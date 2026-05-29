# indicators/stoch.py
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)


def stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3
) -> pd.DataFrame:
    try:
        if (
            high is None or low is None or close is None
            or len(high) < k_period
            or len(low) < k_period
            or len(close) < k_period
        ):
            logger.warning(
                f"STOCH: za mało danych (len={len(close) if close is not None else 0})"
            )
            nan_series = pd.Series([float("nan")] * (len(close) if close is not None else 1))
            return pd.DataFrame({
                "k": nan_series,
                "d": nan_series
            })

        lowest_low = low.rolling(k_period).min()
        highest_high = high.rolling(k_period).max()

        k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, float("nan"))
        d = k.rolling(d_period).mean()

        return pd.DataFrame({
            "k": k,
            "d": d
        })

    except Exception as e:
        logger.error(f"STOCH error: {e}")
        nan_series = pd.Series([float("nan")] * (len(close) if close is not None else 1))
        return pd.DataFrame({
            "k": nan_series,
            "d": nan_series
        })
