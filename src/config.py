import os

ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))
DIR_NAME = os.path.dirname(ROOT_FOLDER)
TRADING_DATA_DIR = os.path.join(DIR_NAME, "trading_data")

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

# turtle strategy
# risks
TRADE_RISK_ALLOCATION = float(os.environ.get('TRADE_RISK_ALLOCATION', 0.02))  # one trade risk capital allocation
MAX_ONE_ASSET_RISK_ALLOCATION = float(os.environ.get(
    'MAX_ONE_ASSET_RISK_ALLOCATION',
    0.5
))  # maximum of capital in one asset traded
STOP_LOSS_ATR_MULTIPL = float(os.environ.get('STOP_LOSS_ATR_MULTIPL', 2))  # multiplication of atr to determine stop-loss

# timeframes
ATR_PERIOD = int(os.environ.get('ATR_PERIOD', 20))  # 20 for slow, 50 for fast
TURTLE_ENTRY_DAYS = int(os.environ.get('TURTLE_ENTRY_DAYS', 20))  # 20 for fast, 50 for slow
TURTLE_EXIT_DAYS = int(os.environ.get('TURTLE_EXIT_DAYS', 10))  # 10 for fast, 20 for slow
# fetch ohlc history with buffer
OHLC_HISTORY_W_BUFFER_DAYS = int(os.environ.get(
    'OHLC_HISTORY_W_BUFFER_DAYS',
    10 + TURTLE_ENTRY_DAYS
))

# pyramiding
PYRAMIDING_LIMIT = int(os.environ.get('PYRAMIDING_LIMIT', 4))  # max pyramid trades (1 init, 3 pyramid)
# atr/price ratio lower than n means less volatile market
AGGRESSIVE_PYRAMID_ATR_PRICE_RATIO_LIMIT = float(os.environ.get(
    'AGGRESSIVE_PYRAMID_ATR_PRICE_RATIO_LIMIT',
    0.02
))


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
