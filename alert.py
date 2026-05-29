# alert.py
import requests
import time
from utils.logger import get_logger
from settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

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


def send_buy_alert(price: float) -> None:
    send_message(f"📈 <b>BUY 4H</b>\nCena: <b>{price}</b>")


def send_sell_alert(price: float) -> None:
    send_message(f"📉 <b>SELL 4H</b>\nCena: <b>{price}</b>")


def send_sl_alert(price: float) -> None:
    send_message(f"🛑 <b>STOP LOSS</b>\nCena: <b>{price}</b>")


def send_tp_alert(price: float) -> None:
    send_message(f"🎯 <b>TAKE PROFIT</b>\nCena: <b>{price}</b>")


def send_trailing_update(new_ts: float) -> None:
    send_message(
        f"🔄 <b>Trailing stop update</b>\nNowy TS: <b>{new_ts}</b>"
    )


def send_trailing_hit(price: float) -> None:
    send_message(
        f"🛑 <b>TRAILING STOP</b>\nCena: <b>{price}</b>"
    )
