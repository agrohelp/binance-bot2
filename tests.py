# tests.py — wszystkie testy w jednym miejscu (wersja PRO)

import socket
import traceback
from settings import SYMBOL, INTERVAL_1H, INTERVAL_4H, INTERVAL_1D
from alert import (
    send_message,
    send_buy_alert,
    send_sell_alert,
    send_sl_alert,
    send_tp_alert,
    send_trailing_hit,
)
from api import get_client

client = get_client()


# ─────────────────────────────────────────────
# TEST INTERNETU
# ─────────────────────────────────────────────

def test_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("✔ Internet OK")
    except Exception as e:
        print("❌ Internet ERROR:", e)


# ─────────────────────────────────────────────
# TEST .ENV
# ─────────────────────────────────────────────

def test_env():
    from settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BINANCE_API_KEY, BINANCE_API_SECRET

    errors = False

    if not TELEGRAM_BOT_TOKEN:
        print("❌ Brak TELEGRAM_BOT_TOKEN w .env")
        errors = True
    if not TELEGRAM_CHAT_ID:
        print("❌ Brak TELEGRAM_CHAT_ID w .env")
        errors = True
    if not BINANCE_API_KEY:
        print("❌ Brak BINANCE_API_KEY w .env")
        errors = True
    if not BINANCE_API_SECRET:
        print("❌ Brak BINANCE_API_SECRET w .env")
        errors = True

    if not errors:
        print("✔ .env OK")


# ─────────────────────────────────────────────
# TEST TELEGRAM
# ─────────────────────────────────────────────

def test_telegram():
    try:
        send_message("📡 TEST TELEGRAM — działa OK")
        print("✔ Telegram OK")
    except Exception as e:
        print("❌ Telegram ERROR:", e)


# ─────────────────────────────────────────────
# TEST BINANCE API
# ─────────────────────────────────────────────

def test_binance():
    try:
        price = client.get_symbol_ticker(symbol=SYMBOL)
        print(f"✔ Binance API OK — cena {SYMBOL}: {price['price']}")
    except Exception as e:
        print("❌ Binance API ERROR:", e)
        traceback.print_exc()


# ─────────────────────────────────────────────
# TEST ŚWIEC 1H / 4H / 1D
# ─────────────────────────────────────────────

def test_candles():
    try:
        for interval in [INTERVAL_1H, INTERVAL_4H, INTERVAL_1D]:
            candles = client.get_klines(symbol=SYMBOL, interval=interval, limit=10)
            if len(candles) < 5:
                print(f"❌ Za mało świec ({interval})")
            else:
                print(f"✔ Świece {interval} OK ({len(candles)} świec)")
    except Exception as e:
        print("❌ Candle ERROR:", e)
        traceback.print_exc()


# ─────────────────────────────────────────────
# TEST WSKAŹNIKÓW I STRATEGII
# ─────────────────────────────────────────────

def test_indicators():
    try:
        from strategy.strategy_4h import check_signal
        signal, price = check_signal()
        print("✔ Wskaźniki policzone")
        print("SYGNAŁ:", signal)
        print("CENA:", price)
    except Exception as e:
        print("❌ Indicator ERROR:", e)
        traceback.print_exc()


# ─────────────────────────────────────────────
# SYMULACJA STRATEGII BUY/SELL
# ─────────────────────────────────────────────

def test_strategy_simulation():
    print("▶ Symulacja BUY/SELL…")
    send_buy_alert(SYMBOL, 1.1111)
    send_sell_alert(SYMBOL, 1.2222)
    print("✔ Symulacja strategii wysłana")


# ─────────────────────────────────────────────
# TEST ALERTÓW
# ─────────────────────────────────────────────

def test_alert():
    send_message("🔔 TEST ALERT — bot działa poprawnie")
    print("✔ Test alert wysłany")

def test_buy():
    send_buy_alert(SYMBOL, 1.2345)
    print("✔ Test BUY wysłany")

def test_sell():
    send_sell_alert(SYMBOL, 1.2345)
    print("✔ Test SELL wysłany")

def test_sl():
    send_sl_alert(SYMBOL, 1.2000, 1.2100)
    print("✔ Test SL wysłany")

def test_tp():
    send_tp_alert(SYMBOL, 1.3000, 1.2900)
    print("✔ Test TP wysłany")

def test_ts():
    send_trailing_hit(SYMBOL, 1.2500, 1.2400)
    print("✔ Test Trailing Stop wysłany")


# ─────────────────────────────────────────────
# TEST WSZYSTKIEGO NARAZ
# ─────────────────────────────────────────────

def test_all():
    print("▶ Wysyłam WSZYSTKIE testy…")
    test_internet()
    test_env()
    test_telegram()
    test_binance()
    test_candles()
    test_indicators()
    test_strategy_simulation()
    test_alert()
    test_buy()
    test_sell()
    test_sl()
    test_tp()
    test_ts()
    print("✔ Wszystkie testy zakończone")
