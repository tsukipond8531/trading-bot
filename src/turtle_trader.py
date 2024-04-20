import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd
import pandas.io.sql as sqlio
from database_tools.adapters.postgresql import PostgresqlAdapter
from retrying import retry
from slack_bot.notifications import SlackNotifier
from sqlalchemy import func
from sqlalchemy.exc import OperationalError, TimeoutError

from config import (TRADE_RISK_ALLOCATION,
                    MAX_ONE_ASSET_RISK_ALLOCATION,
                    STOP_LOSS_ATR_MULTIPL,
                    ATR_PERIOD,
                    TURTLE_ENTRY_DAYS,
                    TURTLE_EXIT_DAYS,
                    OHLC_HISTORY_W_BUFFER_DAYS,
                    PYRAMIDING_LIMIT,
                    AGGRESSIVE_PYRAMID_ATR_PRICE_RATIO_LIMIT,
                    SLACK_URL)
from exchange_adapter import ExchangeAdapter
from src.model import trader_database
from src.model.turtle_model import Order
from src.schemas.turtle_schema import OrderSchema

_logger = logging.getLogger(__name__)
_notifier = SlackNotifier(SLACK_URL, __name__, __name__)


class AssetAllocationOverRiskLimit(Exception):
    """ Asset trades exceeds risk limit"""


def generate_trade_id():
    return str(uuid.uuid4().fields[-1])[:8]


def retry_if_sqlalchemy_transient_error(exception):
    """Determine if the exception is a transient SQLAlchemy error."""
    return isinstance(exception, (OperationalError, TimeoutError))


@dataclass
class LastOpenedPosition:
    id: str
    agg_trade_id: str
    action: str
    price: float
    cost: float
    stop_loss_price: float
    atr: float
    free_balance: float
    pl: float

    def is_long(self):
        return self.action == 'long'

    def get_atr_price_ratio(self):
        return self.atr / self.price

    def get_atr_for_pyramid(self):
        # lower atr for entry to half for pyramid trade
        # if atr/price ration is lower than 2% (less volatile market)
        atr_ratio = self.get_atr_price_ratio()
        if atr_ratio < AGGRESSIVE_PYRAMID_ATR_PRICE_RATIO_LIMIT:
            return self.atr * 0.5
        return self.atr


@dataclass
class CurrMarketConditions:
    timeframe: int
    O: float
    H: float
    L: float
    C: float
    V: float
    datetime: str
    ATR: float
    d20_High: float
    d20_Low: float
    d10_High: float
    d10_Low: float
    Long_Entry: bool
    Short_Entry: bool
    Long_Exit: bool
    Short_Exit: bool

    def log_current_market_conditions(self):
        _logger.info(f'\nLONG ENTRY cond: {self.Long_Entry}\n'
                     f'LONG EXIT cond: {self.Long_Exit}\n'
                     f'SHORT ENTRY cond: {self.Short_Entry}\n'
                     f'SHORT EXIT cond: {self.Short_Exit}')


def calculate_atr(df, period=ATR_PERIOD):
    """
    Calculate the Average True Range (ATR) for given OHLCV DataFrame.

    Parameters:
    - df: pandas DataFrame with columns 'H', 'L', and 'C'.
    - period: the period over which to calculate the ATR.

    Returns:
    - A pandas Series representing the ATR.
    """
    # Calculate true ranges
    df['High-Low'] = df['H'] - df['L']
    df['High-PrevClose'] = abs(df['H'] - df['C'].shift(1))
    df['Low-PrevClose'] = abs(df['L'] - df['C'].shift(1))

    # Find the max of the true ranges
    df['TrueRange'] = df[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)

    # Calculate the ATR
    df['ATR'] = df['TrueRange'].rolling(window=period, min_periods=1).mean()

    # Clean up the DataFrame by removing the intermediate columns
    df.drop(['High-Low', 'High-PrevClose', 'Low-PrevClose', 'TrueRange'], axis=1, inplace=True)

    return df


def turtle_trading_signals_adjusted(df):
    """
    Identify Turtle Trading entry and exit signals for both long and short positions, adjusting for early rows.

    Parameters:
    - df: pandas DataFrame with at least 'High' and 'Low' columns.

    Adds columns to df:
    - 'd20_High': Highest high over the previous 20 days, adjusting for early rows.
    - 'd20_Low': Lowest low over the previous 20 days, adjusting for early rows.
    - 'd10_High': Highest high over the previous 10 days, adjusting for early rows.
    - 'd10_Low': Lowest low over the previous 10 days, adjusting for early rows.
    - 'Long_Entry': Signal for entering a long position.
    - 'Long_Exit': Signal for exiting a long position.
    - 'Short_Entry': Signal for entering a short position.
    - 'Short_Exit': Signal for exiting a short position.
    """
    df['datetime'] = pd.to_datetime(df['timeframe'], unit='ms')
    # Calculate rolling max/min for the required windows with min_periods=1
    df['d20_High'] = df['H'].rolling(window=TURTLE_ENTRY_DAYS, min_periods=1).max()
    df['d20_Low'] = df['L'].rolling(window=TURTLE_ENTRY_DAYS, min_periods=1).min()
    df['d10_High'] = df['H'].rolling(window=TURTLE_EXIT_DAYS, min_periods=1).max()
    df['d10_Low'] = df['L'].rolling(window=TURTLE_EXIT_DAYS, min_periods=1).min()

    # Entry signals
    df['Long_Entry'] = df['H'] > df['d20_High'].shift(1)
    df['Short_Entry'] = df['L'] < df['d20_Low'].shift(1)

    # Exit signals
    df['Long_Exit'] = df['L'] < df['d10_Low'].shift(1)
    df['Short_Exit'] = df['H'] > df['d10_High'].shift(1)

    return df


class TurtleTrader:

    def __init__(self,
                 exchange: ExchangeAdapter,
                 db: PostgresqlAdapter = None,
                 testing_file_path: bool = False
                 ):
        self._exchange = exchange
        self._database = trader_database if not db else db

        self.opened_positions = None
        self.last_opened_position: LastOpenedPosition = None
        self.curr_market_conditions: CurrMarketConditions = None

        self.get_opened_positions()
        self.get_curr_market_conditions(testing_file_path)

    @property
    def n_of_opened_positions(self):
        return len(self.opened_positions) if self.opened_positions is not None else None

    @property
    def opened_positions_ids(self):
        if self.opened_positions is not None:
            return self.opened_positions['id'].to_list()
        return None

    @retry(retry_on_exception=retry_if_sqlalchemy_transient_error,
           stop_max_attempt_number=5,
           wait_exponential_multiplier=2000)
    def get_opened_positions(self):
        _logger.info('Getting opened positions')
        with self._database.get_session() as session:
            df = sqlio.read_sql(
                session.query(
                    Order.id,
                    Order.agg_trade_id,
                    Order.action,
                    Order.price,
                    Order.cost,
                    Order.stop_loss_price,
                    Order.atr,
                    Order.free_balance,
                    Order.pl
                ).filter(
                    Order.position_status == 'opened',
                    Order.symbol == self._exchange.market_futures
                ).order_by(
                    Order.timestamp
                ).statement,
                session.bind
            )

        if df.empty:
            _logger.info('No opened positions')
            self.opened_positions = None
            self.last_opened_position = None
        else:
            _logger.info(f'There are opened positions')
            self.opened_positions = df
            last_opened_position = df.iloc[-1].to_dict()
            self.last_opened_position = LastOpenedPosition(**last_opened_position)

    @retry(retry_on_exception=retry_if_sqlalchemy_transient_error,
           stop_max_attempt_number=5,
           wait_exponential_multiplier=2000)
    def get_pl(self):
        _logger.info('Getting positions summary')
        with self._database.get_session() as session:
            # Query for the sum of P&L for opened positions with the specific symbol
            asset_pl = session.query(
                func.sum(Order.pl).label('filtered_total_pl')
            ).filter(
                Order.symbol == self._exchange.market_futures
            ).scalar()

            # Query for the sum of P&L for all positions
            total_pl = session.query(
                func.sum(Order.pl).label('total_pl')
            ).scalar()

            # If there are no records matching the filters, set the values to 0.0
            asset_pl = 0.0 if asset_pl is None else float(asset_pl)
            total_pl = 0.0 if total_pl is None else float(total_pl)

        return asset_pl, total_pl

    def log_total_pl(self):
        asset_pl, total_pl = self.get_pl()
        _logger.info(f'{self._exchange.market} P/L = {asset_pl} | Total P/L = {total_pl}')
        _notifier.info(f'{self._exchange.market} P/L = {asset_pl} | Total P/L = {total_pl}')

    def calculate_pl(self, close_order: OrderSchema):
        if self.last_opened_position.is_long():
            total_cost = self.opened_positions.cost.sum()
            total_revenue = close_order.cost
        else:
            total_cost = close_order.cost
            total_revenue = self.opened_positions.cost.sum()

        pl = total_revenue - total_cost
        pl_percent = (pl / total_cost) * 100

        return round(pl, 2), round(pl_percent, 2)

    def get_curr_market_conditions(self, testing_file_path: str = None):
        n_days_ago = datetime.now() - timedelta(days=OHLC_HISTORY_W_BUFFER_DAYS)
        since_timestamp_ms = int(n_days_ago.timestamp() * 1000)

        if testing_file_path:
            ohlc = pd.read_csv(testing_file_path)
        else:
            ohlc = self._exchange.fetch_ohlc(since=since_timestamp_ms)

        ohlc = calculate_atr(ohlc, period=ATR_PERIOD)
        ohlc = turtle_trading_signals_adjusted(ohlc)

        curr_market_con = ohlc.iloc[-1].to_dict()
        self.curr_market_conditions = CurrMarketConditions(**curr_market_con)
        self.curr_market_conditions.log_current_market_conditions()

    def create_agg_trade_id(self):
        if self.last_opened_position is None:
            return generate_trade_id()
        else:
            return self.last_opened_position.agg_trade_id

    def get_stop_loss_price(self, action, atr2):
        # save stop-loss price
        if action == 'long':  # long
            return self.curr_market_conditions.C - atr2
        elif action == 'short':  # short
            return self.curr_market_conditions.C + atr2
        else:
            return

    def recalc_limited_free_entry_balance(self, free_balance, total_balance):
        if self.last_opened_position:
            # This is to ensure that the pyramid position is not larger than the last position
            # (checking the free balance at the time of the last position).
            # In the case of trading several assets.
            last_pos_free_balance = self.last_opened_position.free_balance
            if free_balance > last_pos_free_balance:
                _logger.info('Balance is greater than last position free balance '
                             '-> setting balance to last open position free balance')
                free_balance = last_pos_free_balance

            actual_asset_allocation = self.opened_positions.cost.sum() / total_balance
            if actual_asset_allocation > MAX_ONE_ASSET_RISK_ALLOCATION:
                _logger.warning(f'This trade would excess max capital allocation into one asset')
                raise AssetAllocationOverRiskLimit

            return free_balance
        else:
            return free_balance

    @retry(retry_on_exception=retry_if_sqlalchemy_transient_error,
           stop_max_attempt_number=5,
           wait_exponential_multiplier=2000)
    def update_closed_orders(self):
        _logger.info('Updating closed orders in db')
        with self._database.get_session() as session:
            session.query(Order).filter(Order.id.in_(self.opened_positions_ids)).update(
                {"position_status": "closed"},
                synchronize_session=False  # Use 'fetch' if objects are being used in the session
            )
            session.commit()
        _logger.info('Closed orders successfully updated')

    @retry(retry_on_exception=retry_if_sqlalchemy_transient_error,
           stop_max_attempt_number=5,
           wait_exponential_multiplier=2000)
    def commit_order_to_db(self, order_object: OrderSchema):
        with self._database.get_session() as session:
            session.add(order_object)
            session.commit()
        _logger.info('Order successfully saved')

    def save_order(self, order, action, position_status='opened'):
        _logger.info('Saving order to db')
        self._exchange.fetch_balance()

        order_object = OrderSchema().load(order)
        order_object.atr = self.curr_market_conditions.ATR
        order_object.action = action
        order_object.free_balance = self._exchange.free_balance
        order_object.total_balance = self._exchange.total_balance
        order_object.position_status = position_status
        order_object.agg_trade_id = self.create_agg_trade_id()
        # stop loss atr
        atr2 = STOP_LOSS_ATR_MULTIPL * order_object.atr
        order_object.stop_loss_price = self.get_stop_loss_price(action, atr2)

        if action == 'close':
            order_object.closed_positions = self.opened_positions_ids
            order_object.pl, order_object.pl_percent = self.calculate_pl(order_object)

        self.commit_order_to_db(order_object)

    def entry_position(self, action):
        self._exchange.fetch_balance()
        free_balance = self._exchange.free_balance
        total_balance = self._exchange.total_balance

        free_balance = self.recalc_limited_free_entry_balance(free_balance, total_balance)

        trade_risk_cap = free_balance * TRADE_RISK_ALLOCATION
        amount = trade_risk_cap / (STOP_LOSS_ATR_MULTIPL * self.curr_market_conditions.ATR)

        _logger.info(f'Creating {action} order. Amount: {amount}')
        order = self._exchange.order(action, amount)

        if order:
            self.save_order(order, action, free_balance)

    def exit_position(self):
        action = 'close'
        order = self._exchange.order(action)
        if order:
            self.save_order(order, action, position_status='closed')
            self.update_closed_orders()
            self.log_total_pl()

    def process_opened_position(self):
        _logger.info('Processing opened positions')

        curr_mar_cond = self.curr_market_conditions
        last_stop_loss = self.last_opened_position.stop_loss_price

        # set trigger price for pyramid trade
        pyramid_atr = self.last_opened_position.get_atr_for_pyramid()
        long_pyramid_price = self.last_opened_position.price + pyramid_atr
        short_pyramid_price = self.last_opened_position.price - pyramid_atr

        # check if number of pyramid trade is over limit
        pyramid_stop = self.n_of_opened_positions > PYRAMIDING_LIMIT

        if self.last_opened_position.is_long():
            # exit position
            if curr_mar_cond.Long_Exit:
                _logger.info('Exiting long position/s')
                self.exit_position()
            # add to position -> pyramiding
            elif curr_mar_cond.C >= long_pyramid_price and not pyramid_stop:
                _logger.info(f'Adding to long position -> pyramid')
                self.entry_position('long')
            # exit position -> stop loss
            elif curr_mar_cond.C <= last_stop_loss:
                _logger.info('Initiating long stop-loss')
                self.exit_position()
            else:
                _logger.info('Staying in position '
                             '-> no condition for opened position is met')
        else:
            # exit position
            if curr_mar_cond.Short_Exit:
                _logger.info('Exiting short position/s')
                self.exit_position()
            # add to position -> pyramiding
            elif curr_mar_cond.C <= short_pyramid_price and not pyramid_stop:
                _logger.info(f'Adding to short position -> pyramid')
                self.entry_position('short')
            # exit position -> stop loss
            elif curr_mar_cond.C >= last_stop_loss:
                _logger.info('Initiating short stop-loss')
                self.exit_position()
            else:
                _logger.info('Staying in position '
                             '-> no condition for opened position is met')

    def trade(self):
        if self.opened_positions is None:
            curr_cond = self.curr_market_conditions
            # entry long
            if curr_cond.Long_Entry and not curr_cond.Long_Exit:  # safety
                _logger.info('Long cond is met -> entering long position')
                self.entry_position('long')
            # entry short
            elif curr_cond.Short_Entry and not curr_cond.Short_Exit:  # safety
                _logger.info('Short cond is met -> entering short position')
                self.entry_position('short')
            # do nothing
            else:
                _logger.info('No opened positions and no condition is met for entry -> SKIPPING')
        # work with opened position
        else:
            self.process_opened_position()
