# api.py

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import pandas as pd
import time
from settings import BINANCE_API_KEY, BINANCE_API_SECRET

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)


def get_client():
    return client


def get_klines(symbol: str, interval: str, limit: int = 300, retries: int = 3) -> pd.DataFrame:
    """
    Stabilne pobieranie klines z Binance z retry/backoff.
    """

    for attempt in range(retries):
        try:
            raw = client.get_klines(symbol=symbol, interval=interval, limit=limit)
            break

        except (BinanceAPIException, BinanceRequestException) as e:
            if attempt == retries - 1:
                raise e
            time.sleep(1 + attempt * 2)  # backoff

    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "num_trades", "taker_base", "taker_quote", "ignore"
    ])

    # konwersja typów
    float_cols = ["open", "high", "low", "close", "volume"]
    df[float_cols] = df[float_cols].astype(float)

    # timestamp → datetime
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

    return df
