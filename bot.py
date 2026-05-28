# bot.py

import time
import sys
import json
import os

from settings import (
    SYMBOL,
    CHECK_SLEEP_SECONDS,
    SL_PERCENT,
    TP_PERCENT,
    TRAILING_PERCENT,
)

from strategy.strategy_4h import check_signal

from alert import (
    send_buy_alert,
    send_sell_alert,
    send_sl_alert,
    send_tp_alert,
    send_trailing_update,
    send_trailing_hit,
)

STATE_FILE = "state.json"


# ──────────────────────────────
#  STAN BOTA (persistencja)
# ──────────────────────────────

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(
    last_trend_signal,
    position_side,
    entry_price,
    sl_level,
    tp_level,
    trailing_stop,
):
    state = {
        "last_trend_signal": last_trend_signal,
        "position_side": position_side,
        "entry_price": entry_price,
        "sl_level": sl_level,
        "tp_level": tp_level,
        "trailing_stop": trailing_stop,
    }
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"[WARN] Nie mogę zapisać stanu: {e}")


# ──────────────────────────────
#  GŁÓWNA PĘTLA BOTA
# ──────────────────────────────

def main():
    print("🚀 Start Bot 4H — EMA+MACD+RSI+STOCH (1H/4H/1D)")
    print(f"💰 Symbol: {SYMBOL}")
    print("──────────────────────────────")

    # wczytanie stanu
    state = load_state()

    last_trend_signal = state.get("last_trend_signal", None)  # BUY / SELL / None
    position_side = state.get("position_side", None)          # "LONG" / None
    entry_price = state.get("entry_price", None)
    sl_level = state.get("sl_level", None)
    tp_level = state.get("tp_level", None)
    trailing_stop = state.get("trailing_stop", None)

    # sanity cast (JSON → float / None)
    def _to_float_or_none(v):
        return float(v) if v is not None else None

    entry_price = _to_float_or_none(entry_price)
    sl_level = _to_float_or_none(sl_level)
    tp_level = _to_float_or_none(tp_level)
    trailing_stop = _to_float_or_none(trailing_stop)

    while True:
        try:
            # prosta odporność: retry na check_signal
            for attempt in range(3):
                try:
                    signal, price = check_signal()
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    print(f"[WARN] check_signal error (attempt {attempt+1}/3): {e}")
                    time.sleep(2)
            else:
                # nie powinno się zdarzyć
                continue

            print(f"🕒 4H | Cena: {price} | Sygnał: {signal}")

            # ──────────────────────────────
            #  1) Nowy sygnał trendowy
            # ──────────────────────────────
            if signal and signal != last_trend_signal:
                if signal == "BUY":
                    # otwieramy tylko LONG (bez shortów)
                    send_buy_alert(SYMBOL, price)
                    position_side = "LONG"
                    entry_price = float(price)
                    sl_level = entry_price * (1 - SL_PERCENT)
                    tp_level = entry_price * (1 + TP_PERCENT)
                    trailing_stop = entry_price * (1 - TRAILING_PERCENT)
                    print(
                        f"➡️ Ustawiam SL={sl_level:.6f}, "
                        f"TP={tp_level:.6f}, TS={trailing_stop:.6f}"
                    )

                elif signal == "SELL":
                    # zamykamy wirtualną pozycję, jeśli była
                    send_sell_alert(SYMBOL, price)
                    position_side = None
                    entry_price = None
                    sl_level = None
                    tp_level = None
                    trailing_stop = None

                last_trend_signal = signal

                # zapis stanu po zmianie trendu / pozycji
                save_state(
                    last_trend_signal,
                    position_side,
                    entry_price,
                    sl_level,
                    tp_level,
                    trailing_stop,
                )

            # ──────────────────────────────
            #  2) SL / TP / Trailing stop
            # ──────────────────────────────
            if position_side == "LONG" and entry_price is not None:
                # SL
                if sl_level is not None and price <= sl_level:
                    print(f"🛑 SL trafiony @ {price}")
                    send_sl_alert(SYMBOL, price, sl_level)
                    position_side = None
                    entry_price = None
                    sl_level = None
                    tp_level = None
                    trailing_stop = None

                    save_state(
                        last_trend_signal,
                        position_side,
                        entry_price,
                        sl_level,
                        tp_level,
                        trailing_stop,
                    )

                # TP
                elif tp_level is not None and price >= tp_level:
                    print(f"🎯 TP trafiony @ {price}")
                    send_tp_alert(SYMBOL, price, tp_level)
                    position_side = None
                    entry_price = None
                    sl_level = None
                    tp_level = None
                    trailing_stop = None

                    save_state(
                        last_trend_signal,
                        position_side,
                        entry_price,
                        sl_level,
                        tp_level,
                        trailing_stop,
                    )

                else:
                    # TRAILING STOP — aktualizacja (tylko gdy cena rośnie)
                    if trailing_stop is not None and price > entry_price:
                        new_ts = price * (1 - TRAILING_PERCENT)
                        if new_ts > trailing_stop:
                            trailing_stop = new_ts
                            print(f"🔄 TS update: {trailing_stop:.6f}")
                            send_trailing_update(SYMBOL, trailing_stop)

                            save_state(
                                last_trend_signal,
                                position_side,
                                entry_price,
                                sl_level,
                                tp_level,
                                trailing_stop,
                            )

                    # TRAILING STOP — trafiony
                    if trailing_stop is not None and price <= trailing_stop:
                        print(f"🛑 TS trafiony @ {price}")
                        send_trailing_hit(SYMBOL, price, trailing_stop)
                        position_side = None
                        entry_price = None
                        sl_level = None
                        tp_level = None
                        trailing_stop = None

                        save_state(
                            last_trend_signal,
                            position_side,
                            entry_price,
                            sl_level,
                            tp_level,
                            trailing_stop,
                        )

        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(CHECK_SLEEP_SECONDS)


if __name__ == "__main__":
    from tests import (
        test_internet,
        test_env,
        test_telegram,
        test_binance,
        test_candles,
        test_indicators,
        test_strategy_simulation,
        test_alert,
        test_buy,
        test_sell,
        test_sl,
        test_tp,
        test_ts,
        test_all,
    )

    if "--test-internet" in sys.argv:
        test_internet()
    elif "--test-env" in sys.argv:
        test_env()
    elif "--test-telegram" in sys.argv:
        test_telegram()
    elif "--test-binance" in sys.argv:
        test_binance()
    elif "--test-candles" in sys.argv:
        test_candles()
    elif "--test-indicators" in sys.argv:
        test_indicators()
    elif "--test-strategy" in sys.argv:
        test_strategy_simulation()
    elif "--test-alert" in sys.argv:
        test_alert()
    elif "--test-buy" in sys.argv:
        test_buy()
    elif "--test-sell" in sys.argv:
        test_sell()
    elif "--test-sl" in sys.argv:
        test_sl()
    elif "--test-tp" in sys.argv:
        test_tp()
    elif "--test-ts" in sys.argv:
        test_ts()
    elif "--test-all" in sys.argv:
        test_all()
    else:
        main()
