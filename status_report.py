# status_report.py — v2.3.2 (diagnostyka, bez wysyłania Telegram)

from strategy.strategy_4h import (
    get_debug_report,
    get_state_snapshot,
)

# przechowuje poprzedni stan rynku
last_snapshot = None


def detect_market_change() -> str | None:
    """
    Sprawdza, czy zmieniły się warunki rynkowe.
    Zwraca tekst raportu jeśli jest zmiana, inaczej None.
    """
    global last_snapshot

    snapshot = get_state_snapshot()

    if last_snapshot is None:
        last_snapshot = snapshot
        return None

    if snapshot != last_snapshot:
        last_snapshot = snapshot
        return "⚠️ *Zmiana warunków rynkowych!* ⚠️\n\n" + get_debug_report()

    return None


def get_full_status() -> str:
    """
    Zwraca pełny raport diagnostyczny 4H.
    """
    return get_debug_report()
