# bot.py — v2.3 (ATR PRO Engine, Dynamic TS, Binance Live)

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
)

logger = get_logger(__name__)

# ATR PRO — mnożnik trailing stopu
ATR_MULTIPLIER = 2.5


class StateDict(TypedDict):
    position: Optional[Dict[str, Any]]


STATE_FILE = "state.json"


def load_state() -> StateDict:
    if not os.path.exists(STATE_FILE):
        logger.info("Brak state.json — tworzę nowy stan.")
        return {"position": None}

    try:
        with open(STATE_FILE, "r") as f:
            data: Dict[str, Any] = json.load(f)

        pos_data = data.get("position")
        if pos_data is not None:
            pos = Position.from_dict(pos_data)
            return {"position": pos.to_dict()}

        return {"position": None}

    except Exception as e:
        logger.error(f"Błąd wczytywania state.json: {e}")
        return {"position": None}


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
    logger.info("Bot startuje…")
    state: StateDict = load_state()

    while True:
        try:
            signal = check_signal()

            if not isinstance(signal, Signal):
                logger.info("Brak sygnału — czekam…")
                time.sleep(CHECK_SLEEP_SECONDS)
                continue

            price: float = signal.price

            # BUY — wejście
            if signal.side == "BUY" and state["position"] is None:
                entry = price
                sl = entry * (1 - SL_PERCENT)
                tp = entry * (1 + TP_PERCENT)

                # ATR PRO — pobranie ATR
                atr = get_atr_4h()
                ts = compute_trailing_stop(
                    price=entry,
                    atr=atr,
                    entry=entry,
                    sl=sl,
                    current_ts=sl,  # start TS = SL
                )

                pos = Position(
                    side="LONG",
                    entry=entry,
                    sl=sl,
                    tp=tp,
                    ts=ts,
                )

                state["position"] = pos.to_dict()
                save_state(state)
                send_buy_alert(entry)

                logger.info(
                    f"BUY @ {entry}, SL={sl}, TP={tp}, TS={ts} (ATR PRO)"
                )

            # Obsługa otwartej pozycji
            pos_dict = state["position"]
            if pos_dict is not None:
                pos = Position.from_dict(pos_dict)

                # ATR PRO — aktualizacja trailing stopu
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
                    logger.info(f"SL hit @ {price}")
                    state["position"] = None
                    save_state(state)

                # TP
                elif price >= pos.tp:
                    send_tp_alert(price)
                    logger.info(f"TP hit @ {price}")
                    state["position"] = None
                    save_state(state)

                # TS
                elif price <= pos.ts:
                    send_trailing_hit(price)
                    logger.info(f"TS hit @ {price}")
                    state["position"] = None
                    save_state(state)

            time.sleep(CHECK_SLEEP_SECONDS)

        except KeyboardInterrupt:
            logger.info("Przerwano ręcznie (CTRL+C). Kończę pracę bota.")
            break
        except Exception as e:
            logger.error(f"Błąd głównej pętli: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
