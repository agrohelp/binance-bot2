# core/sanity.py

import numpy as np

def sanity_check_candles(df, logger, tf_name="4H"):
    """
    Zwraca True jeśli świece są OK.
    Zwraca False jeśli wykryto błąd.
    """

    # 1) Za mało świec
    if df is None or len(df) < 20:
        logger.warning(f"{tf_name}: Za mało świec do sanity-check")
        return False

    # 2) NaN w danych OHLC
    if df[["open", "high", "low", "close"]].isna().any().any():
        logger.error(f"{tf_name}: NaN w świecach OHLC — odrzucam dane")
        return False

    # 3) Cena <= 0
    if (df["close"] <= 0).any():
        logger.error(f"{tf_name}: Wykryto świecę z ceną <= 0 — odrzucam dane")
        return False

    # 4) Skoki cen > 10% w jedną świecę
    close = df["close"].values
    pct = np.abs(np.diff(close) / close[:-1])

    if (pct > 0.10).any():
        logger.warning(f"{tf_name}: Wykryto skok ceny > 10% — możliwe błędne dane")
        return False

    # 5) High < Low (błąd Binance)
    if (df["high"] < df["low"]).any():
        logger.error(f"{tf_name}: High < Low — błędne dane świec")
        return False

    # 6) Timestamp sanity (rosnący)
    if not df["open_time"].is_monotonic_increasing:
        logger.error(f"{tf_name}: Timestamps nie rosną — odrzucam dane")
        return False

    return True
