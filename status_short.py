from strategy.strategy_4h import (
    get_trend_1h,
    get_trend_1d,
    get_buy_diagnostics,
    get_sell_diagnostics,
    _get_last_context,
)

def get_short_status():
    df, last, prev, price = _get_last_context()
    if df is None:
        return "Brak danych 4H."

    trend_1h = get_trend_1h()
    trend_1d = get_trend_1d()
    buy_diag = get_buy_diagnostics()
    sell_diag = get_sell_diagnostics()

    buy_ok = all(v == "OK" for v in buy_diag.values())
    sell_ok = all(v == "OK" for v in sell_diag.values())

    msg = ""

    msg += f"📊 *BTCUSDT — status 4H*\n"
    msg += f"Cena: {price}\n\n"

    msg += "⏱ *TREND 1H*\n"
    msg += f"• trend: {trend_1h['trend']}\n"
    msg += f"• momentum: {trend_1h['momentum']}\n"
    msg += f"• rsi_trend: {trend_1h['rsi_trend']}\n\n"

    msg += "📅 *TREND 1D*\n"
    msg += f"• trend: {trend_1d['trend']}\n"
    msg += f"• big_trend: {trend_1d['big_trend']}\n\n"

    msg += "🟢 BUY możliwy: " + ("TAK" if buy_ok else "NIE") + "\n"
    msg += "🔴 SELL możliwy: " + ("TAK" if sell_ok else "NIE") + "\n"

    return msg
