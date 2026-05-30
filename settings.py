import os
from dotenv import load_dotenv

# Wczytaj zmienne z pliku .env
load_dotenv()

# ─────────────────────────────────────────────
# TRYB PRACY BOTA
# ─────────────────────────────────────────────
# SPOT_MODE = True → tylko LONG (BUY + EXIT)
# SPOT_MODE = False → long + short (BUY + SELL)
SPOT_MODE = True

# W trybie debug bot drukuje pełne dane diagnostyczne
DEBUG = True

# ─────────────────────────────────────────────
# SYMBOL / INTERWAŁY
# ─────────────────────────────────────────────

# SYMBOL = "XRPUSDC"
SYMBOL = "BTCUSDT"

INTERVAL_4H = "4h"
CANDLES_4H = 300

# ─────────────────────────────────────────────
# EMA
# ─────────────────────────────────────────────

EMA_FAST = 50
EMA_SLOW = 200

# ─────────────────────────────────────────────
# MACD
# ─────────────────────────────────────────────

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# ─────────────────────────────────────────────
# RSI
# ─────────────────────────────────────────────

RSI_PERIOD = 14
RSI_OVERBOUGHT_4H = 70
RSI_OVERSOLD_4H = 30

# ─────────────────────────────────────────────
# STOCH
# ─────────────────────────────────────────────

STO_K = 14
STO_D = 3
STO_SMOOTH = 3

# ─────────────────────────────────────────────
# RISK MANAGEMENT
# ─────────────────────────────────────────────

SL_PERCENT = 0.02
TP_PERCENT = 0.04
TRAILING_PERCENT = 0.01

# ─────────────────────────────────────────────
# GŁÓWNA PĘTLA
# ─────────────────────────────────────────────

CHECK_SLEEP_SECONDS = 10

# ─────────────────────────────────────────────
# TELEGRAM — pobierane z .env
# ─────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Multi-user: lista ID z .env
raw_ids = os.getenv("TELEGRAM_CHAT_IDS", "")
TELEGRAM_CHAT_IDS = [x.strip() for x in raw_ids.split(",") if x.strip()]

# przyszłe wsparcie dla wielu odbiorców (v2.3.4)
# TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "")

if TELEGRAM_BOT_TOKEN is None or TELEGRAM_CHAT_IDS is None:
    raise ValueError("Brakuje TELEGRAM_BOT_TOKEN lub TELEGRAM_CHAT_ID w pliku .env")

# ─────────────────────────────────────────────
# ALERT STATUS CO X MINUT
# ─────────────────────────────────────────────

STATUS_ALERT_ENABLED = True
STATUS_ALERT_INTERVAL = 60  # w minutach
