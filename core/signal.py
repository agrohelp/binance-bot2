from dataclasses import dataclass


@dataclass
class Signal:
    side: str   # "BUY" lub "SELL"
    price: float
