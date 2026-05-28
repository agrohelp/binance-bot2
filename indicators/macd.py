import pandas as pd

def macd(series: pd.Series, fast=12, slow=26, signal=9):
    """
    Moving Average Convergence Divergence (MACD)
    - zgodne z TradingView / Binance
    - szybka implementacja oparta o pandas.ewm
    """

    # EMA szybka i wolna
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()

    # Linia MACD
    macd_line = ema_fast - ema_slow

    # Linia sygnału
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    # Histogram
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram
