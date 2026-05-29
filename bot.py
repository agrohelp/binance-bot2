# bot.py
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
from strategy.strategy_4h import check_signal
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
                ts = entry * (1 - TRAILING_PERCENT)

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
                logger.info(f"BUY @ {entry}, SL={sl}, TP={tp}, TS={ts}")

            # Obsługa otwartej pozycji
            pos_dict = state["position"]
            if pos_dict is not None:
                pos = Position.from_dict(pos_dict)

                new_ts = price * (1 - TRAILING_PERCENT)
                if new_ts > pos.ts:
                    pos.ts = new_ts
                    state["position"] = pos.to_dict()
                    save_state(state)
                    send_trailing_update(new_ts)
                    logger.info(f"Trailing stop update: {new_ts}")

                if price <= pos.sl:
                    send_sl_alert(price)
                    logger.info(f"SL hit @ {price}")
                    state["position"] = None
                    save_state(state)

                elif price >= pos.tp:
                    send_tp_alert(price)
                    logger.info(f"TP hit @ {price}")
                    state["position"] = None
                    save_state(state)

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
