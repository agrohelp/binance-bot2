# alert.py — v2.3.3 (SPOT/FUTURES explicit alerts)

import requests
import time
from utils.logger import get_logger
from settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SPOT_MODE

logger = get_logger(__name__)

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def send_message(text: str, retries: int = 3) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        msg = "[ALERT] Brak konfiguracji Telegram — drukuję lokalnie:\n" + text
        logger.warning(msg)
        print(msg)
        return

    for attempt in range(retries):
        try:
            response = requests.get(
                TELEGRAM_URL,
                params={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": text,
                    "parse_mode": "HTML",
                },
                timeout=5,
            )

            if response.status_code == 429:
                retry_after = response.json().get("retry_after", 5)
                logger.warning(f"Telegram 429 — retry after {retry_after}s")
                time.sleep(retry_after)
                continue

            if response.status_code != 200:
                logger.warning(
                    f"Telegram HTTP {response.status_code}: {response.text}"
                )
                time.sleep(1 + attempt * 2)
                continue

            return

        except Exception as e:
            logger.warning(
                f"Telegram error: {e} (attempt {attempt+1}/{retries})"
            )
            time.sleep(1 + attempt * 2)

    logger.error("Nie udało się wysłać alertu do Telegrama")
    print("[ERROR] Nie udało się wysłać alertu do Telegrama:")
    print(text)


# ─────────────────────────────────────────────
# ALERTY HANDLOWE — SPOT/FUTURES explicit
# ─────────────────────────────────────────────

def send_buy_alert(price: float) -> None:
    if SPOT_MODE:
        text = (
            "📈 <b>WEJŚCIE LONG (SPOT)</b>\n"
            f"Cena: <b>{price}</b>"
        )
    else:
        text = (
            "📈 <b>BUY (LONG)</b>\n"
            f"Cena: <b>{price}</b>"
        )
    send_message(text)


def send_sell_alert(price: float) -> None:
    if SPOT_MODE:
        text = (
            "📉 <b>WYJŚCIE Z LONG (SPOT)</b>\n"
            f"Cena: <b>{price}</b>"
        )
    else:
        text = (
            "📉 <b>SELL (SHORT)</b>\n"
            f"Cena: <b>{price}</b>"
        )
    send_message(text)


def send_sl_alert(price: float) -> None:
    prefix = "(SPOT)" if SPOT_MODE else "(FUTURES)"
    send_message(f"🛑 <b>STOP LOSS {prefix}</b>\nCena: <b>{price}</b>")


def send_tp_alert(price: float) -> None:
    prefix = "(SPOT)" if SPOT_MODE else "(FUTURES)"
    send_message(f"🎯 <b>TAKE PROFIT {prefix}</b>\nCena: <b>{price}</b>")


def send_trailing_update(new_ts: float) -> None:
    prefix = "(SPOT)" if SPOT_MODE else "(FUTURES)"
    send_message(
        f"🔄 <b>Trailing stop update {prefix}</b>\nNowy TS: <b>{new_ts}</b>"
    )


def send_trailing_hit(price: float) -> None:
    prefix = "(SPOT)" if SPOT_MODE else "(FUTURES)"
    send_message(
        f"🛑 <b>TRAILING STOP {prefix}</b>\nCena: <b>{price}</b>"
    )


# ─────────────────────────────────────────────
# ALERT STATUSOWY
# ─────────────────────────────────────────────

def send_status_alert(msg: str) -> None:
    mode = "SPOT" if SPOT_MODE else "FUTURES"
    send_message(f"⏱️ <b>Alert statusowy ({mode})</b>\n\n{msg}")
