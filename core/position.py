from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class Position:
    side: str   # "LONG" / "SHORT" (na razie używamy tylko LONG)
    entry: float
    sl: float
    tp: float
    ts: float   # trailing stop

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Position":
        return cls(
            side=str(data["side"]),
            entry=float(data["entry"]),
            sl=float(data["sl"]),
            tp=float(data["tp"]),
            ts=float(data["ts"]),
        )
