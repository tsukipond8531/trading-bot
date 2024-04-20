import logging
import traceback

import ccxt
import pandas as pd
from retrying import retry
from slack_bot.notifications import SlackNotifier

from config import SLACK_URL, LEVERAGE
from exchange_factory import ExchangeFactory
from src.utils.utils import round

_notifier = SlackNotifier(url=SLACK_URL, username='Exchange adapter')
_logger = logging.getLogger(__name__)

POSITIONS_MAPPING = {
    'long': 'buy',
    'short': 'sell'
}


class NotEnoughBalanceException(Exception):
    """Balance is really low"""


def retry_if_network_error(exception):
    """Return True if we should retry (in this case when it's a NetworkError), False otherwise"""
    return isinstance(exception, (ccxt.NetworkError, ccxt.ExchangeError))


class ExchangeAdapter(ExchangeFactory):
    params = {'leverage': LEVERAGE}

    def __init__(self, exchange_id, market: str = None, collateral: str = 'USDT'):
        super().__init__(exchange_id)
        self._market = market
        self._collateral = collateral
        self.market_futures = f"{self._market}:{self._collateral}"
        self._open_position = None
        self.balance = None

    @property
    def free_balance(self):
        return round(self.balance['free'][self._collateral], 1)

    @property
    def total_balance(self):
        return round(self.balance['total'][self._collateral], 1)

    @property
    def market(self) -> str:
        return self._market

    @market.setter
    def market(self, name) -> None:
        _logger.info(f"Setting market to {name}")
        self._market = name
        self.market_futures = f"{self._market}:{self._collateral}"

    @retry(retry_on_exception=retry_if_network_error,
           stop_max_attempt_number=5,
           wait_exponential_multiplier=1500)
    def fetch_ohlc(self, since, timeframe: str = '1d'):
        candles = self._exchange.fetchOHLCV(self._market, timeframe=timeframe, since=since)
        candles_df = pd.DataFrame(candles, columns=['timeframe', 'O', 'H', 'L', 'C', 'V'])
        candles_df['datetime'] = pd.to_datetime(candles_df['timeframe'], unit='ms')
        return candles_df

    @retry(retry_on_exception=retry_if_network_error,
           stop_max_attempt_number=5,
           wait_exponential_multiplier=1500)
    def fetch_balance(self, min_balance=50):
        _logger.info(f"getting balance")
        balance = self._exchange.fetch_balance()
        self.balance = balance

        if self.free_balance < min_balance:
            _logger.error(f"balance: {balance}$ is under minimal balance: {min_balance}$")
            raise NotEnoughBalanceException

    @retry(retry_on_exception=retry_if_network_error,
           stop_max_attempt_number=5,
           wait_exponential_multiplier=1500)
    def close_price(self):
        _logger.info(f"getting close price")
        return self._exchange.fetch_ticker(symbol=self.market_futures)['close']

    @retry(retry_on_exception=retry_if_network_error,
           stop_max_attempt_number=5,
           wait_exponential_multiplier=1500)
    def opened_position(self):
        _logger.info(f"getting open positions")

        if self._exchange_id == 'binance':
            open_positions = self._exchange.fetch_account_positions(
                symbols=[self._market]
            )
        else:
            open_positions = self._exchange.fetchPositions(
                symbols=[self.market_futures]
            )

        if open_positions:
            open_position = open_positions[0]
            self._open_position = open_position

    @property
    def open_position_amount(self):
        return self._open_position['contracts']

    @property
    def open_position_side(self):
        if self._open_position:
            return POSITIONS_MAPPING.get(self._open_position['side'])
        return

    @property
    def open_position_equity(self):
        return self._open_position['initialMargin'] + self._open_position['unrealizedPnl']

    def assert_side(self, side):
        assert side != self.open_position_side, (
            f"There's already "
            f"opened position with"
            f" the same side: {self.open_position_side},"
            f"\n{self._open_position}"
        )

    @retry(retry_on_exception=retry_if_network_error,
           stop_max_attempt_number=5,
           wait_exponential_multiplier=1500)
    def enter_position(self, side, amount):
        _logger.info(f"entering {str.upper(side)} position")

        try:
            # self.opened_position()
            # self.assert_side(side)
            #
            # if self.open_position_side:
            #     _logger.info(f"There is already one open position")
            #     self.close_position()

            _logger.info(f"creating order: {side}, "
                         f"amount: {amount}, "
                         f"params: {self.params}")
            order = self._exchange.create_order(
                symbol=self.market_futures,
                type='market',
                side=side,
                amount=amount,
                params=self.params
            )

            _notifier.info(f"order {str.upper(side)} | amount: {amount}")
            return order

        except (ccxt.NetworkError, ccxt.ExchangeError) as e:
            msg = (f"{self._exchange.id} enter_position failed "
                   f"due to a Network or Exchange error: {e}")
            _logger.error(msg)
            raise

        except AssertionError as e:
            msg = f"{self._exchange.id} enter_position failed due to assert error: {e}"
            _logger.error(msg)
            _notifier.error(msg)
            raise

        except Exception as e:
            msg = f"{self._exchange.id} close_position failed with: {traceback.format_exc()}"
            _logger.error(msg)
            raise

    @retry(retry_on_exception=retry_if_network_error,
           stop_max_attempt_number=5,
           wait_exponential_multiplier=1000)
    def close_position(self):
        _logger.info(f"closing position")

        params = {'reduceOnly': True}
        try:
            self.opened_position()

            if not self.open_position_side:
                _logger.warning(f"no open position to close: {self.open_position_side}")
                _notifier.warning(f"no open position to close: {self.open_position_side}")
                return {"msg": "Nothing to close"}

            side = 'buy' if self.open_position_side == 'sell' else 'sell'

            _logger.info(f"creating order: {side}, "
                         f"amount: {self.open_position_amount}, "
                         f"params: {params}")
            order = self._exchange.create_order(
                symbol=self.market_futures,
                type='market',
                side=side,
                amount=self.open_position_amount,
                params=params
            )

            _notifier.info(f"order CLOSE {str.upper(side)}")
            return order

        except (ccxt.NetworkError, ccxt.ExchangeError) as e:
            msg = (f"{self._exchange.id} close_position failed "
                   f"due to a Network or Exchange error: {e}")
            _logger.error(msg)
            raise

        except Exception as e:
            msg = f"{self._exchange.id} close_position failed with: {traceback.format_exc()}"
            _logger.error(msg)
            raise

    def order(self, action_key, amount: float = 0):
        _actions = {
            'long': {'action': self.enter_position, 'side': 'buy'},
            'short': {'action': self.enter_position, 'side': 'sell'},
            'close': {'action': self.close_position}
        }

        position = _actions.get(action_key)
        position_order = position['action']
        side = position.get('side', None)

        if side:
            return position_order(side, amount)
        return position_order()
