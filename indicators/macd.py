# indicators/macda.py
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> pd.DataFrame:
    try:
        if series is None or len(series) < slow + signal:
            logger.warning(
                f"MACD: za mało danych (len={len(series) if series is not None else 0})"
            )
            nan_series = pd.Series([float("nan")] * (len(series) if series is not None else 1))
            return pd.DataFrame({
                "macd": nan_series,
                "signal": nan_series,
                "hist": nan_series
            })

        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        hist = macd_line - signal_line

        return pd.DataFrame({
            "macd": macd_line,
            "signal": signal_line,
            "hist": hist
        })

    except Exception as e:
        logger.error(f"MACD error: {e}")
        nan_series = pd.Series([float("nan")] * (len(series) if series is not None else 1))
        return pd.DataFrame({
            "macd": nan_series,
            "signal": nan_series,
            "hist": nan_series
        })

