# indicators/rsi.py
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    try:
        if series is None or len(series) < period + 1:
            logger.warning(
                f"RSI: za mało danych (len={len(series) if series is not None else 0})"
            )
            return pd.Series([float("nan")] * (len(series) if series is not None else 1))

        delta = series.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        rs = avg_gain / avg_loss.replace(0, float("nan"))
        rsi_val = 100 - (100 / (1 + rs))

        return rsi_val

    except Exception as e:
        logger.error(f"RSI error: {e}")
        return pd.Series([float("nan")] * (len(series) if series is not None else 1))
