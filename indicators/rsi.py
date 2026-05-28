import pandas as pd
import numpy as np

def rsi(series: pd.Series, period: int = 14):
    """
    RSI (Relative Strength Index) — wersja Wildera (RMA)
    - zgodne z TradingView
    - odporne na dzielenie przez zero
    """

    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's RMA (smoothed moving average)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    return rsi
