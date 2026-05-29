# backtest/run_backtest.py

import sys
from utils.logger import get_logger
from backtest.loader import load_csv
from backtest.engine import BacktestEngine
from backtest.export import export_backtest_to_csv
from strategy.strategy_4h import check_signal

logger = get_logger("BACKTEST")


def run_backtest(csv_path):
    logger.info(f"Ładuję dane z CSV: {csv_path}")

    try:
        df = load_csv(csv_path)
    except Exception as e:
        logger.error(f"Nie mogę wczytać CSV: {e}")
        return

    engine = BacktestEngine(
        df=df,
        strategy_func=lambda df_override: check_signal(df_override=df_override),
        logger=logger
    )

    logger.info("Start backtestu...")
    result = engine.run()

    export_backtest_to_csv(result, "results/backtest_results.csv")

    logger.info("=== BACKTEST WYNIKI ===")
    logger.info(f"Final balance: {result['final_balance']}")
    logger.info(f"Liczba transakcji: {result['num_trades']}")
    logger.info("Wyniki zapisane do results/backtest_results.csv")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Użycie: python run_backtest.py <plik.csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    run_backtest(csv_path)
