# settings.py
import os
from dotenv import load_dotenv

# Wczytaj zmienne z pliku .env
load_dotenv()

# W trybie produkcyjnym bot ma być czysty, lekki, nie spamować logów.
# W trybie debug chcesz widzieć wszystko: EMA, MACD, RSI, STOCH,
# powody odrzucenia sygnału.
DEBUG = True # włącza/wyłącza DEBUGI w kodzie


# ─────────────────────────────────────────────
# SYMBOL / INTERWAŁY
# ─────────────────────────────────────────────

SYMBOL = "XRPUSDC"

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
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
