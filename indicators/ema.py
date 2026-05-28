import pandas as pd

def ema(series: pd.Series, period: int):
    """
    Exponential Moving Average (EMA)
    - szybka implementacja oparta o pandas.ewm
    - adjust=False → zgodne z tradingview/binance
    """
    return series.ewm(span=period, adjust=False).mean()
