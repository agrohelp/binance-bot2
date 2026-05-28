# alert.py

import requests
import time
from settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def send_message(text, retries=3):
    """
    Stabilne wysyłanie wiadomości do Telegrama z retry/backoff.
    Nie blokuje bota przy chwilowych problemach sieciowych.
    """

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[ALERT] Brak konfiguracji Telegram")
        print(text)
        return

    for attempt in range(retries):
        try:
            requests.get(
                TELEGRAM_URL,
                params={"chat_id": TELEGRAM_CHAT_ID, "text": text},
                timeout=5,
            )
            return
        except Exception as e:
            print(f"[WARN] Telegram error: {e} (attempt {attempt+1}/{retries})")
            time.sleep(1 + attempt * 2)  # backoff

    print("[ERROR] Nie udało się wysłać alertu do Telegrama:")
    print(text)


# ─────────────────────────────────────────────
#  ALERTY TRENDOWE
# ─────────────────────────────────────────────

def send_buy_alert(symbol, price):
    send_message(f"📈 BUY 4H\n{symbol}\nCena: {price}")


def send_sell_alert(symbol, price):
    send_message(f"📉 SELL 4H\n{symbol}\nCena: {price}")


# ─────────────────────────────────────────────
#  ALERTY SL / TP
# ─────────────────────────────────────────────

def send_sl_alert(symbol, price, level):
    send_message(
        f"🛑 STOP LOSS\n"
        f"{symbol}\n"
        f"Cena: {price}\n"
        f"SL poziom: {level}"
    )


def send_tp_alert(symbol, price, level):
    send_message(
        f"🎯 TAKE PROFIT\n"
        f"{symbol}\n"
        f"Cena: {price}\n"
        f"TP poziom: {level}"
    )


# ─────────────────────────────────────────────
#  ALERTY TRAILING STOP
# ─────────────────────────────────────────────

def send_trailing_update(symbol, new_level):
    send_message(
        f"🔄 Trailing stop przesunięty\n"
        f"{symbol}\n"
        f"Nowy poziom TS: {new_level}"
    )


def send_trailing_hit(symbol, price, level):
    send_message(
        f"🛑 TRAILING STOP\n"
        f"{symbol}\n"
        f"Cena: {price}\n"
        f"TS poziom: {level}"
    )
