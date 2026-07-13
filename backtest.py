"""Entry point: wire the components together and run one backtest.

This file is deliberately thin. All logic lives in the reusable ``trading``
package; here we only *compose* concrete implementations. Swapping the
strategy, data source, sizer, or reporters is a one-line change each.

Run:
    uv run python backtest.py
    # or, with a custom CSV:
    uv run python backtest.py "path/to/data.csv"
"""

from __future__ import annotations

import sys
from pathlib import Path

from trading import (
    AllInSizer,
    Backtester,
    BacktestConfig,
    ConsoleReporter,
    CsvDataSource,
    DonchianBreakoutStrategy,
    EquityCurveExporter,
    EquityCurvePlotter,
)

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = PROJECT_DIR / "NSE_NIFTY 50_Historical_PR_01012026to12072026.csv"


def main(csv_path: str | Path = DEFAULT_CSV) -> None:
    # --- compose the pieces (each is independently swappable) ---
    data_source = CsvDataSource(csv_path)
    strategy = DonchianBreakoutStrategy(lookback=7, take_profit=0.05)
    backtester = Backtester(
        strategy=strategy,
        config=BacktestConfig(initial_equity=100_000.0),
        sizer=AllInSizer(),
    )
    reporters = [
        ConsoleReporter(),
        EquityCurveExporter(PROJECT_DIR / "equity_curve.csv"),
        EquityCurvePlotter(
            PROJECT_DIR / "equity_curve.png",
            title=f"Equity Curve - NIFTY 50 {strategy.name}",
        ),
    ]

    # --- run and report ---
    result = backtester.run(data_source.load())
    for reporter in reporters:
        reporter.report(result)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    main(path)
