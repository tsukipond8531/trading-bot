import logging
import traceback

from slack_bot.notifications import SlackNotifier

from config import SLACK_URL, TRADED_TICKERS
from exchange_adapter import ExchangeAdapter
from jnd_utils.log import init_logging
from turtle_trader import TurtleTrader

_logger = logging.getLogger(__name__)
_notifier = SlackNotifier(url=SLACK_URL, username='main')


def trade():
    try:
        _logger.info(f"Starting trade")
        exchange = ExchangeAdapter('binance')
        for i in TRADED_TICKERS:
            print(f"working on {i}")
            # exchange.market = f"{i}/USDT"
            # trader = TurtleTrader(exchange)
            # trader.trade()
        return

    except Exception as e:
        _logger.error(f"there was an error with trading-bot: {str(e)}\n"
                      f"{traceback.format_exc(limit=3)}")
        _notifier.error(f"there was an error with trading-bot: {str(e)}\n"
                        f"{traceback.format_exc(limit=3)}")


if __name__ == '__main__':
    init_logging()
    trade()
