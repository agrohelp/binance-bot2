# backtest/loader.py

import pandas as pd

def load_csv(path: str):
    """
    Wczytuje dane OHLCV z pliku CSV.
    Wymagane kolumny: open_time, open, high, low, close, volume
    """
    df = pd.read_csv(path)

    required = ["open_time", "open", "high", "low", "close", "volume"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Brak kolumny w CSV: {col}")

    return df
