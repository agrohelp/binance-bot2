# backtest/export.py

import csv
import os

def export_backtest_to_csv(results, path="backtest_results.csv"):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "side", "price", "profit", "balance"])

        for row in results["history"]:
            writer.writerow(row)
