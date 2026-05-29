# backtest/engine.py

from core.signal import Signal

class BacktestEngine:

    def __init__(self, df, strategy_func, logger):
        self.df = df
        self.strategy = strategy_func
        self.logger = logger

        self.balance = 1000.0
        self.position = None
        self.entry_price = None
        self.history = []  # <── NOWE

    def run(self):
        for i in range(50, len(self.df)):
            window = self.df.iloc[:i].copy()
            last = window.iloc[-1]

            signal = self.strategy(df_override=window)

            if isinstance(signal, Signal):

                if signal.side == "BUY" and self.position is None:
                    self.position = "LONG"
                    self.entry_price = last["close"]

                    self.history.append([
                        last["open_time"], "BUY", self.entry_price, "", self.balance
                    ])

                elif signal.side == "SELL" and self.position == "LONG":
                    exit_price = last["close"]
                    profit = exit_price - self.entry_price
                    self.balance += profit

                    self.history.append([
                        last["open_time"], "SELL", exit_price, profit, self.balance
                    ])

                    self.position = None
                    self.entry_price = None

        return {
            "final_balance": self.balance,
            "history": self.history,
            "num_trades": len(self.history),
        }
