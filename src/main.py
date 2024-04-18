import logging
import traceback

from config import SLACK_URL
from exchange_adapter import ExchangeAdapter
from src.model.turtle_model import create_schema_and_tables
from turtle_trader import TurtleTrader
from src.utils.log import init_logging
from slack_bot.notifications import SlackNotifier

_logger = logging.getLogger(__name__)
_notifier = SlackNotifier(url=SLACK_URL, username='main')

tickers = ['LTC']


def trade():
    try:
        _logger.info(f"Starting trade")
        exchange = ExchangeAdapter('binance')
        for i in tickers:
            exchange.market = f"{i}/USDT"
            trader = TurtleTrader(exchange)
            trader.trade()
        return

    except Exception as e:
        _logger.error(f"there was an error with flask app: {str(e)}\n"
                      f"{traceback.format_exc(limit=3)}")
        _notifier.error(f"there was an error with flask app: {str(e)}\n"
                        f"{traceback.format_exc(limit=3)}")


if __name__ == '__main__':
    init_logging()
    create_schema_and_tables()
    trade()
