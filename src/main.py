import logging
import sys
import traceback

from jnd_utils.log import init_logging
from slack_bot.notifications import SlackNotifier

from config import SLACK_URL, TRADED_TICKERS
from exchange_adapter import ExchangeAdapter
from turtle_trader import TurtleTrader

_logger = logging.getLogger(__name__)
_notifier = SlackNotifier(url=SLACK_URL, username='main')


def trade():
    try:
        _logger.info(f"Initialising Turtle trader, tickers: {TRADED_TICKERS}")
        exchange = ExchangeAdapter('binance')
        for ticker in TRADED_TICKERS:
            _logger.info(f"\n\n============== Starting trade ==============")
            _logger.info(f"working on {ticker}")
            exchange.market = f"{ticker}/USDT"
            trader = TurtleTrader(exchange)
            trader.trade()

    except Exception as e:
        _logger.error(f"there was an error with trading-bot: {str(e)}\n"
                      f"{traceback.format_exc(limit=3)}")
        _notifier.error(f"there was an error with trading-bot: {str(e)}\n"
                        f"{traceback.format_exc(limit=3)}")
        sys.exit(1)


if __name__ == '__main__':
    init_logging()
    trade()
