import logging
import traceback

import ccxt
from retrying import retry

from config import app_config, SLACK_URL
from slack_bot.notifications import SlackNotifier

_notifier = SlackNotifier(url=SLACK_URL, username='Exchange factory')
_logger = logging.getLogger(__name__)


def retry_if_network_error(exception):
    """Return True if we should retry (in this case when it's an IOError), False otherwise"""
    return isinstance(exception, ccxt.NetworkError)


class ExchangeFactory:

    def __init__(self, exchange_id: str):
        self._exchange_id = exchange_id
        self._exchange = self._create_exchange_object()

    @retry(retry_on_exception=retry_if_network_error, stop_max_attempt_number=7, wait_fixed=10_000)
    def _create_exchange_object(self) -> ccxt.Exchange:
        try:
            _logger.info(f"crating exchange object")
            _exchange_class = getattr(ccxt, self._exchange_id)
            _exchange = _exchange_class(app_config.EXCHANGES[self._exchange_id])
            if app_config.USE_SANDBOX:
                _logger.info(f"using SANDBOX")
                _exchange.set_sandbox_mode(True)
            return _exchange

        except ccxt.NetworkError as e:
            msg = f"""{self._exchange.id} creating exchange object 
                    failed due to a network error: {e}"""
            _logger.error(msg)
            _notifier.error(msg)

        except ccxt.ExchangeError as e:
            msg = f"""{self._exchange.id} creating exchange object 
                    failed due to a exchange error: {e}"""
            _logger.error(msg)
            _notifier.error(msg)

        except Exception as e:
            msg = f"""{self._exchange.id} creating exchange object
                  failed with: {traceback.format_exc()}"""
            _logger.error(msg)
            _notifier.error(msg)

    def load_exchange(self) -> ccxt.Exchange.__module__:
        _logger.info(f"loading markets")
        try:
            self._exchange.load_markets()
            _logger.info("markets loaded")

        except ccxt.NetworkError as e:
            msg = f"""{self._exchange.id} loading markets 
                    failed due to a network error: {e}"""
            _logger.error(msg)
            _notifier.error(msg)

        except ccxt.ExchangeError as e:
            msg = f"""{self._exchange.id} loading markets 
                    failed due to a exchange error: {e}"""
            _logger.error(msg)
            _notifier.error(msg)

        except Exception as e:
            msg = f"""{self._exchange.id} loading markets 
                  failed with: {traceback.format_exc()}"""
            _logger.error(msg)
            _notifier.error(msg)
        return self._exchange
