# core/indicator_sanity.py

import numpy as np

def sanity_check_indicators(last, logger, tf_name="4H"):
    """
    Sprawdza poprawność indykatorów dla ostatniej świecy.
    Zwraca True jeśli OK, False jeśli wykryto błąd.
    """

    checks = {
        "EMA fast > 0": last["ema_fast"] > 0,
        "EMA slow > 0": last["ema_slow"] > 0,
        "RSI w zakresie 0–100": 0 <= last["rsi"] <= 100,
        "MACD nie NaN": not np.isnan(last["macd"]),
        "MACD signal nie NaN": not np.isnan(last["macd_signal"]),
        "STOCH K w zakresie 0–100": 0 <= last["stoch_k"] <= 100,
        "STOCH D w zakresie 0–100": 0 <= last["stoch_d"] <= 100,
        "MACD nie INF": np.isfinite(last["macd"]),
        "RSI nie INF": np.isfinite(last["rsi"]),
        "EMA fast nie INF": np.isfinite(last["ema_fast"]),
        "EMA slow nie INF": np.isfinite(last["ema_slow"]),
    }

    # Logowanie diagnostyczne
    for name, ok in checks.items():
        if not ok:
            logger.error(f"{tf_name}: sanity-check indykatorów FAIL → {name}")
            return False

    return True
