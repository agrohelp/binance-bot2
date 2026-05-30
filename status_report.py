"""
status_report.py
----------------
Moduł odpowiedzialny za:
- wysyłanie cyklicznych raportów na Telegram (interwał z settings.py)
- wysyłanie alertów, gdy zmieniają się warunki rynkowe (trend 1H/1D, momentum, RSI trend, BUY/SELL diagnostyka)
- formatowanie raportu z emoji

Plik umieszczamy w katalogu głównym projektu, obok bot.py.
"""

import time
import requests
from settings import (
    TELEGRAM_STATUS_INTERVAL_MINUTES,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from strategy.strategy_4h import (
    get_debug_report,
    get_state_snapshot,
)

# przechowuje poprzedni stan rynku
last_snapshot = None


def send_telegram_message(text: str):
    """Wysyła wiadomość na Telegram."""
    if TELEGRAM_BOT_TOKEN is None or TELEGRAM_CHAT_ID is None:
        print("Brak TELEGRAM_BOT_TOKEN lub TELEGRAM_CHAT_ID — sprawdź .env")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")


def start_status_loop():
    """Główna pętla wysyłająca raporty i alerty zmian."""
    global last_snapshot

    last_sent = 0
    interval = TELEGRAM_STATUS_INTERVAL_MINUTES * 60

    while True:
        now = time.time()

        # pobierz aktualny stan rynku
        snapshot = get_state_snapshot()

        # pierwszy snapshot
        if last_snapshot is None:
            last_snapshot = snapshot

        # wykrywanie zmian
        if snapshot != last_snapshot:
            send_telegram_message(
                "⚠️ *Zmiana warunków rynkowych!* ⚠️\n\n" + get_debug_report()
            )
            last_snapshot = snapshot

        # raport interwałowy
        if now - last_sent >= interval:
            send_telegram_message(get_debug_report())
            last_sent = now

        time.sleep(5)
