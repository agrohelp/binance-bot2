import pandas as pd
import numpy as np

def stochastic(df, k_period=14, d_period=3, smooth=3):
    """
    Stochastic Oscillator (K%D)
    - zgodne z TradingView
    - odporne na dzielenie przez zero
    - smooth = wygładzenie K (SMA)
    """

    low_min = df["low"].rolling(k_period).min()
    high_max = df["high"].rolling(k_period).max()

    # ochrona przed dzieleniem przez zero
    range_ = (high_max - low_min).replace(0, np.nan)

    # %K surowe
    k_raw = 100 * (df["close"] - low_min) / range_

    # wygładzenie K (SMA)
    k_smooth = k_raw.rolling(smooth).mean()

    # linia %D (SMA z K)
    d = k_smooth.rolling(d_period).mean()

    return k_smooth, d
