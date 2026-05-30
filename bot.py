# bot.py — v2.3.3 (SPOT MODE, ATR PRO, last_closed history)

import time
import json
import os
from typing import Optional, Dict, Any, TypedDict

from utils.logger import get_logger
from settings import (
    CHECK_SLEEP_SECONDS,
    SL_PERCENT,
    TP_PERCENT,
    TRAILING_PERCENT,
    STATUS_ALERT_ENABLED,
    STATUS_ALERT_INTERVAL,
    SPOT_MODE,
)
from strategy.strategy_4h import check_signal, get_atr_4h
from core.signal import Signal
from core.position import Position
from alert import (
    send_buy_alert,
    send_sell_alert,
    send_sl_alert,
    send_tp_alert,
    send_trailing_update,
    send_trailing_hit,
    send_status_alert,
)
from status_short import get_short_status

logger = get_logger(__name__)

# ATR PRO — mnożnik trailing stopu
ATR_MULTIPLIER = 2.5


class StateDict(TypedDict):
    position: Optional[Dict[str, Any]]
    last_closed: Optional[Dict[str, Any]]


STATE_FILE = "state.json"


def load_state() -> StateDict:
    if not os.path.exists(STATE_FILE):
        logger.info("Brak state.json — tworzę nowy stan.")
        return {"position": None, "last_closed": None}

    try:
        with open(STATE_FILE, "r") as f:
            data: Dict[str, Any] = json.load(f)

        pos_data = data.get("position")
        last_closed = data.get("last_closed")

        if pos_data is not None:
            pos = Position.from_dict(pos_data)
            pos_dict = pos.to_dict()
        else:
            pos_dict = None

        return {
            "position": pos_dict,
            "last_closed": last_closed,
        }

    except Exception as e:
        logger.error(f"Błąd wczytywania state.json: {e}")
        return {"position": None, "last_closed": None}


def save_state(state: StateDict) -> None:
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
        logger.info("Zapisano state.json")
    except Exception as e:
        logger.error(f"Błąd zapisu state.json: {e}")


# ─────────────────────────────────────────────
# ATR PRO — dopieszczony dynamiczny trailing stop
# ─────────────────────────────────────────────
def compute_trailing_stop(
    price: float,
    atr: float | None,
    entry: float,
    sl: float,
    current_ts: float,
) -> float:
    """
    ATR PRO:
    - używa ATR EMA
    - ma minimalny i maksymalny próg
    - TS nigdy nie spada
    - TS nigdy nie jest poniżej SL
    - TS nigdy nie jest powyżej ceny
    """

    # fallback gdy brak ATR
    if atr is None:
        ts = price * (1 - TRAILING_PERCENT)
        return max(ts, current_ts, sl)

    # minimalny ATR (żeby TS nie był za ciasny)
    min_atr = price * 0.0001
    if atr < min_atr:
        atr = min_atr

    # maksymalny ATR (żeby nie było spike’ów)
    max_atr = price * 0.2
    if atr > max_atr:
        atr = max_atr

    # ATR PRO TS
    ts = price - atr * ATR_MULTIPLIER

    # TS nie może spaść
    ts = max(ts, current_ts)

    # TS nie może być poniżej SL
    ts = max(ts, sl)

    # TS nie może być powyżej ceny
    if ts > price:
        ts = price * 0.999

    return ts


# ─────────────────────────────────────────────
# GŁÓWNA PĘTLA BOTA
# ─────────────────────────────────────────────
def main() -> None:
    logger.info(f"Bot startuje… (SPOT_MODE={SPOT_MODE})")
    state: StateDict = load_state()

    last_status_alert = 0.0

    while True:
        try:
            signal = check_signal()

            if not isinstance(signal, Signal):
                logger.info("Brak sygnału — czekam…")

                if STATUS_ALERT_ENABLED:
                    now = time.time()
                    if now - last_status_alert >= STATUS_ALERT_INTERVAL * 60:
                        try:
                            msg = get_short_status()
                            send_status_alert(msg)
                            logger.info("Wysłano cykliczny alert statusowy.")
                        except Exception as e:
                            logger.error(f"Błąd wysyłania alertu statusowego: {e}")
                        last_status_alert = now

                time.sleep(CHECK_SLEEP_SECONDS)
                continue

            price: float = signal.price if signal.price is not None else 0.0

            # BUY — wejście LONG (SPOT/FUTURES)
            if signal.side == "BUY" and state["position"] is None:
                entry = price
                sl = entry * (1 - SL_PERCENT)
                tp = entry * (1 + TP_PERCENT)

                atr = get_atr_4h()
                ts = compute_trailing_stop(
                    price=entry,
                    atr=atr,
                    entry=entry,
                    sl=sl,
                    current_ts=sl,
                )

                pos = Position(
                    side="LONG",
                    entry=entry,
                    sl=sl,
                    tp=tp,
                    ts=ts,
                )

                state["position"] = pos.to_dict()
                # nie kasujemy last_closed przy nowej pozycji — historia zostaje
                save_state(state)

                send_buy_alert(entry)
                logger.info(
                    f"BUY @ {entry}, SL={sl}, TP={tp}, TS={ts} (ATR PRO)"
                )

            # Obsługa otwartej pozycji
            pos_dict = state["position"]
            if pos_dict is not None:
                pos = Position.from_dict(pos_dict)

                atr = get_atr_4h()
                new_ts = compute_trailing_stop(
                    price=price,
                    atr=atr,
                    entry=pos.entry,
                    sl=pos.sl,
                    current_ts=pos.ts,
                )

                if new_ts > pos.ts:
                    pos.ts = new_ts
                    state["position"] = pos.to_dict()
                    save_state(state)
                    send_trailing_update(new_ts)
                    logger.info(f"ATR PRO TS update: {new_ts}")

                # SL
                if price <= pos.sl:
                    send_sl_alert(price)
                    send_sell_alert(price)
                    logger.info(f"SL hit @ {price}")

                    state["last_closed"] = {
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "reason": "STOP LOSS",
                        "exit_price": price,
                        "entry": pos.entry,
                        "sl": pos.sl,
                        "tp": pos.tp,
                        "ts": pos.ts,
                    }
                    state["position"] = None
                    save_state(state)

                # TP
                elif price >= pos.tp:
                    send_tp_alert(price)
                    send_sell_alert(price)
                    logger.info(f"TP hit @ {price}")

                    state["last_closed"] = {
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "reason": "TAKE PROFIT",
                        "exit_price": price,
                        "entry": pos.entry,
                        "sl": pos.sl,
                        "tp": pos.tp,
                        "ts": pos.ts,
                    }
                    state["position"] = None
                    save_state(state)

                # TS
                elif price <= pos.ts:
                    send_trailing_hit(price)
                    send_sell_alert(price)
                    logger.info(f"TS hit @ {price}")

                    state["last_closed"] = {
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "reason": "TRAILING STOP",
                        "exit_price": price,
                        "entry": pos.entry,
                        "sl": pos.sl,
                        "tp": pos.tp,
                        "ts": pos.ts,
                    }
                    state["position"] = None
                    save_state(state)

            if STATUS_ALERT_ENABLED:
                now = time.time()
                if now - last_status_alert >= STATUS_ALERT_INTERVAL * 60:
                    try:
                        msg = get_short_status()
                        send_status_alert(msg)
                        logger.info("Wysłano cykliczny alert statusowy.")
                    except Exception as e:
                        logger.error(f"Błąd wysyłania alertu statusowego: {e}")
                    last_status_alert = now

            time.sleep(CHECK_SLEEP_SECONDS)

        except KeyboardInterrupt:
            logger.info("Przerwano ręcznie (CTRL+C). Kończę pracę bota.")
            break
        except Exception as e:
            logger.error(f"Błąd głównej pętli: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
