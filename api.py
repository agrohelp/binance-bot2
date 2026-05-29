# api.py

import time
import pandas as pd
import requests
from utils.logger import get_logger

logger = get_logger(__name__)

BINANCE_URL = "https://api.binance.com/api/v3/klines"


def get_klines(symbol: str, interval: str, limit: int) -> pd.DataFrame:
    """
    Pobiera świece z Binance Spot.
    Zwraca DataFrame z kolumnami:
    open, high, low, close, volume, open_time, close_time
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }

    for attempt in range(5):
        try:
            r = requests.get(BINANCE_URL, params=params, timeout=5)

            if r.status_code == 429:
                logger.warning("Binance 429 — rate limit, retry…")
                time.sleep(2 + attempt)
                continue

            if r.status_code != 200:
                logger.error(f"Binance HTTP {r.status_code}: {r.text}")
                time.sleep(1 + attempt)
                continue

            data = r.json()

            if not isinstance(data, list) or len(data) == 0:
                logger.error("Binance zwrócił pustą listę świec")
                return None

            df = pd.DataFrame(data, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "number_of_trades",
                "taker_buy_base", "taker_buy_quote", "ignore"
            ])

            # konwersje
            df["open"] = df["open"].astype(float)
            df["high"] = df["high"].astype(float)
            df["low"] = df["low"].astype(float)
            df["close"] = df["close"].astype(float)
            df["volume"] = df["volume"].astype(float)

            return df[["open_time", "open", "high", "low", "close", "volume", "close_time"]]

        except Exception as e:
            logger.error(f"get_klines error: {e}")
            time.sleep(1 + attempt)

    logger.error("get_klines: wszystkie próby nieudane")
    return None
