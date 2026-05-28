# settings.py

import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
#  API / TELEGRAM
# ─────────────────────────────────────────────
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ─────────────────────────────────────────────
#  SYMBOL I INTERWAŁY
# ─────────────────────────────────────────────
SYMBOL = "XRPUSDC"

INTERVAL_4H = "4h"
INTERVAL_1H = "1h"
INTERVAL_1D = "1d"

# Ilość świec — dopasowane do EMA200 i MACD
CANDLES_4H = 300
CANDLES_1H = 300
CANDLES_1D = 300   # min. 250 dla EMA200

# ─────────────────────────────────────────────
#  EMA
# ─────────────────────────────────────────────
EMA_FAST = 50
EMA_SLOW = 200

# ─────────────────────────────────────────────
#  MACD (spójne dla 1H / 4H / 1D)
# ─────────────────────────────────────────────
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# ─────────────────────────────────────────────
#  RSI
# ─────────────────────────────────────────────
RSI_PERIOD = 14

# 4H — filtry trendowe
RSI_OVERBOUGHT_4H = 65
RSI_OVERSOLD_4H = 35

# 1H — momentum
RSI_1H_UP = 55
RSI_1H_DOWN = 45

# ─────────────────────────────────────────────
#  STOCHASTIC
# ─────────────────────────────────────────────
STO_K = 14
STO_D = 3
STO_SMOOTH = 3

# ─────────────────────────────────────────────
#  SL / TP / TRAILING STOP
# ─────────────────────────────────────────────
SL_PERCENT = 0.03        # 3%
TP_PERCENT = 0.08        # 8%
TRAILING_PERCENT = 0.03  # 3%

# ─────────────────────────────────────────────
#  CZĘSTOTLIWOŚĆ SPRAWDZANIA
# ─────────────────────────────────────────────
CHECK_SLEEP_SECONDS = 300  # 5 minut
