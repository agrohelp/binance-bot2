# alert.py — v2.4 (multi-user + anti-spam + SPOT/FUTURES)

import requests
import time
from utils.logger import get_logger
from settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_IDS, SPOT_MODE

logger = get_logger(__name__)

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# pamiętamy ostatnie message_id dla każdego użytkownika
_last_message_ids = {}


def _delete_previous(chat_id: str):
    """Usuwa poprzedni alert statusowy, jeśli istnieje."""
    if chat_id not in _last_message_ids:
        return

    msg_id = _last_message_ids[chat_id]

    try:
        url = f"{BASE_URL}/deleteMessage"
        requests.get(url, params={"chat_id": chat_id, "message_id": msg_id}, timeout=5)
        logger.info(f"Usunięto poprzedni alert (chat={chat_id}, msg={msg_id})")
    except Exception as e:
        logger.warning(f"Nie udało się usunąć poprzedniego alertu: {e}")


def _send(chat_id: str, text: str, retries: int = 3):
    """Wysyła wiadomość i zapisuje jej message_id."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Brak TELEGRAM_BOT_TOKEN")
        return

    # usuń poprzedni alert
    _delete_previous(chat_id)

    for attempt in range(retries):
        try:
            url = f"{BASE_URL}/sendMessage"
            response = requests.get(
                url,
                params={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
                timeout=5,
            ).json()

            # zapisz ID nowej wiadomości
            if "result" in response and "message_id" in response["result"]:
                _last_message_ids[chat_id] = response["result"]["message_id"]

            return

        except Exception as e:
            logger.warning(f"Telegram error: {e} (attempt {attempt+1}/{retries})")
            time.sleep(1 + attempt * 2)

    logger.error("Nie udało się wysłać alertu Telegram")


def _broadcast(text: str):
    """Wysyła alert do wszystkich użytkowników."""
    for chat_id in TELEGRAM_CHAT_IDS:
        _send(chat_id, text)


# ─────────────────────────────────────────────
# ALERTY HANDLOWE — SPOT/FUTURES
# ─────────────────────────────────────────────

def send_buy_alert(price: float):
    if SPOT_MODE:
        text = f"📈 <b>WEJŚCIE LONG (SPOT)</b>\nCena: <b>{price}</b>"
    else:
        text = f"📈 <b>BUY (LONG)</b>\nCena: <b>{price}</b>"
    _broadcast(text)


def send_sell_alert(price: float):
    if SPOT_MODE:
        text = f"📉 <b>WYJŚCIE Z LONG (SPOT)</b>\nCena: <b>{price}</b>"
    else:
        text = f"📉 <b>SELL (SHORT)</b>\nCena: <b>{price}</b>"
    _broadcast(text)


def send_sl_alert(price: float):
    prefix = "(SPOT)" if SPOT_MODE else "(FUTURES)"
    _broadcast(f"🛑 <b>STOP LOSS {prefix}</b>\nCena: <b>{price}</b>")


def send_tp_alert(price: float):
    prefix = "(SPOT)" if SPOT_MODE else "(FUTURES)"
    _broadcast(f"🎯 <b>TAKE PROFIT {prefix}</b>\nCena: <b>{price}</b>")


def send_trailing_update(new_ts: float):
    prefix = "(SPOT)" if SPOT_MODE else "(FUTURES)"
    _broadcast(f"🔄 <b>Trailing stop update {prefix}</b>\nNowy TS: <b>{new_ts}</b>")


def send_trailing_hit(price: float):
    prefix = "(SPOT)" if SPOT_MODE else "(FUTURES)"
    _broadcast(f"🛑 <b>TRAILING STOP {prefix}</b>\nCena: <b>{price}</b>")


# ─────────────────────────────────────────────
# ALERT STATUSOWY — osobny anti-spam
# ─────────────────────────────────────────────

_last_status_message_ids = {}  # osobne ID tylko dla statusów

def send_status_alert(msg: str):
    mode = "SPOT" if SPOT_MODE else "FUTURES"
    text = f"⏱️ <b>Alert statusowy ({mode})</b>\n\n{msg}"

    for chat_id in TELEGRAM_CHAT_IDS:

        # 1) Usuń poprzedni status tego użytkownika
        if chat_id in _last_status_message_ids:
            try:
                url = f"{BASE_URL}/deleteMessage"
                requests.get(
                    url,
                    params={
                        "chat_id": chat_id,
                        "message_id": _last_status_message_ids[chat_id],
                    },
                    timeout=5,
                )
                logger.info(f"Usunięto poprzedni STATUS (chat={chat_id})")
            except Exception as e:
                logger.warning(f"Nie udało się usunąć statusu: {e}")

        # 2) Wyślij nowy status
        try:
            url = f"{BASE_URL}/sendMessage"
            response = requests.get(
                url,
                params={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
                timeout=5,
            ).json()

            # zapisz ID nowego statusu
            if "result" in response and "message_id" in response["result"]:
                _last_status_message_ids[chat_id] = response["result"]["message_id"]

        except Exception as e:
            logger.error(f"Błąd wysyłania statusu: {e}")
