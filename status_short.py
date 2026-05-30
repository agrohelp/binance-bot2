from settings import SPOT_MODE, SYMBOL
from strategy.strategy_4h import (
    get_trend_1h,
    get_trend_1d,
    get_buy_diagnostics,
    get_sell_diagnostics,
    _get_last_context,
)
import json
import os
from settings import SPOT_MODE
print(f"[DEBUG] SPOT_MODE widziany przez status_short.py = {SPOT_MODE}")


STATE_FILE = "state.json"


def _load_state():
    if not os.path.exists(STATE_FILE):
        return {"position": None, "last_closed": None}

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"position": None, "last_closed": None}


def get_short_status() -> str:
    df, last, prev, price = _get_last_context()
    if df is None:
        return "Brak danych 4H."

    trend_1h = get_trend_1h()
    trend_1d = get_trend_1d()
    buy_diag = get_buy_diagnostics()
    sell_diag = get_sell_diagnostics()

    buy_ok = all(v == "OK" for v in buy_diag.values())
    sell_ok = all(v == "OK" for v in sell_diag.values())

    state = _load_state()
    pos = state.get("position")
    last_closed = state.get("last_closed")

    # ─────────────────────────────────────────────
    # Format pozycji
    # ─────────────────────────────────────────────
    if pos is None:
        pos_text = "BRAK"
        pos_details = ""
    else:
        pos_text = pos.get("side", "LONG")
        pos_details = (
            f"• Entry: {pos.get('entry')}\n"
            f"• SL: {pos.get('sl')}\n"
            f"• TP: {pos.get('tp')}\n"
            f"• TS: {pos.get('ts')}\n"
        )

    # ─────────────────────────────────────────────
    # Format historii ostatniej pozycji
    # ─────────────────────────────────────────────
    if last_closed:
        last_details = (
            f"🕒 *Ostatnia pozycja:*\n"
            f"• Zamknięta: {last_closed.get('time')}\n"
            f"• Powód: {last_closed.get('reason')}\n"
            f"• Cena wyjścia: {last_closed.get('exit_price')}\n"
            f"• Entry: {last_closed.get('entry')}\n"
            f"• SL: {last_closed.get('sl')}\n"
            f"• TP: {last_closed.get('tp')}\n"
            f"• TS: {last_closed.get('ts')}\n\n"
        )
    else:
        last_details = ""

    # ─────────────────────────────────────────────
    # Budowa wiadomości
    # ─────────────────────────────────────────────
    msg = ""

    msg += f"📊 *{SYMBOL} — status 4H*\n"
    msg += f"Cena: {price}\n\n"

    msg += "⏱️ *TREND 1H*\n"
    msg += f"• trend: {trend_1h['trend']}\n"
    msg += f"• momentum: {trend_1h['momentum']}\n"
    msg += f"• rsi_trend: {trend_1h['rsi_trend']}\n\n"

    msg += "📅 *TREND 1D*\n"
    msg += f"• trend: {trend_1d['trend']}\n"
    msg += f"• big_trend: {trend_1d['big_trend']}\n\n"

    # Pozycja
    if SPOT_MODE:
        msg += f"🔵 *Pozycja (SPOT):* {pos_text}\n"
    else:
        msg += f"🔵 *Pozycja:* {pos_text}\n"

    if pos_details:
        msg += pos_details + "\n"

    # Historia
    if last_details:
        msg += last_details

    # BUY/SELL logic
    if SPOT_MODE:
        msg += "🟢 Wejście możliwe: " + ("TAK" if buy_ok else "NIE") + "\n"
        msg += "🔴 Wyjście możliwe: " + ("TAK" if sell_ok else "NIE") + "\n"
    else:
        msg += "🟢 BUY możliwy: " + ("TAK" if buy_ok else "NIE") + "\n"
        msg += "🔴 SELL możliwy: " + ("TAK" if sell_ok else "NIE") + "\n"

    return msg
