# indicators/ema.py
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


def ema(series: pd.Series, period: int) -> pd.Series:
    try:
        if series is None or len(series) < period:
            logger.warning(
                f"EMA: za mało danych (len={len(series) if series is not None else 0})"
            )
            return pd.Series([float("nan")] * (len(series) if series is not None else 1))

        if series.isna().any():
            logger.warning("EMA: seria wejściowa zawiera NaN — wynik może być niepoprawny")

        return series.ewm(span=period, adjust=False).mean()

    except Exception as e:
        logger.error(f"EMA error: {e}")
        return pd.Series([float("nan")] * (len(series) if series is not None else 1))
