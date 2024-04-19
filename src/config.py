import os

BINANCE_API_KEY_TEST = os.environ.get('BINANCE_API_KEY_TEST')
BINANCE_API_SECRET_TEST = os.environ.get('BINANCE_API_SECRET_TEST')
BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY')
BINANCE_API_SECRET = os.environ.get('BINANCE_API_SECRET')

KUCOIN_API_KEY = os.environ.get('KUCOIN_API_KEY')
KUCOIN_API_SECRET = os.environ.get('KUCOIN_API_SECRET')
KUCOIN_PASS = os.environ.get('KUCOIN_PASS')

LEVERAGE = os.environ.get('LEVERAGE', 1)

# exchanges
BINANCE_CONFIG_TEST = {
    'apiKey': BINANCE_API_KEY_TEST,
    'secret': BINANCE_API_SECRET_TEST,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'leverage': LEVERAGE
    }
}

BINANCE_CONFIG_PROD = {
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'leverage': LEVERAGE
    }
}

KUCOIN_CONFIG_PROD = {
    'apiKey': KUCOIN_API_KEY,
    'secret': KUCOIN_API_SECRET,
    'password': KUCOIN_PASS,
    'enableRateLimit': True,
    'options': {
        'leverage': LEVERAGE
    }
}

SLACK_URL = os.environ.get("SLACK_URL")
APP_SETTINGS = os.environ.get("APP_SETTINGS", "DevConfig")
TRADED_TICKERS = os.environ.get("TRADED_TICKERS", "BTC,ETH,SOL,DOGE").split(',')


class Config:
    DEBUG = False
    DEVELOPMENT = True
    USE_SANDBOX = True
    EXCHANGES = {
        'binance': BINANCE_CONFIG_TEST
    }


class DevConfig(Config):
    pass


class ProdConfig(Config):
    DEBUG = False
    DEVELOPMENT = False
    USE_SANDBOX = False
    EXCHANGES = {
        'binance': BINANCE_CONFIG_PROD,
        'kucoinfutures': KUCOIN_CONFIG_PROD
    }


app_config = eval(APP_SETTINGS)
