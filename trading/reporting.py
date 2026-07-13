"""Reporting and persistence.

Presentation is separated from computation: reporters read a
:class:`BacktestResult` and render it, but never recompute metrics or mutate
the result. Each reporter is one output channel, so adding (say) an HTML or
JSON reporter means writing a new class, not editing existing ones
(Single Responsibility + Open-Closed).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from trading.models import BacktestResult

_LINE = "=" * 70
_THIN = "-" * 70


class Reporter(ABC):
    """Renders a :class:`BacktestResult` to some output channel."""

    @abstractmethod
    def report(self, result: BacktestResult) -> None: ...


class ConsoleReporter(Reporter):
    """Prints a human-readable summary and trade log to stdout."""

    def report(self, result: BacktestResult) -> None:
        for line in self._format(result):
            print(line)

    def _format(self, r: BacktestResult) -> list[str]:
        out: list[str] = [_LINE, "NIFTY 50 BACKTEST REPORT", _LINE]
        out += self._header(r) + [_THIN]
        out += self._trades(r) + [_THIN]
        out += self._open_trade(r) + [_THIN]
        out += self._performance(r) + [_LINE]
        return out

    @staticmethod
    def _header(r: BacktestResult) -> list[str]:
        data = r.data
        return [
            f"Data range      : {data['Date'].iloc[0].date()} -> {data['Date'].iloc[-1].date()}",
            f"Candles         : {len(data)}",
            f"Strategy        : {r.strategy_description}",
            f"Initial equity  : {r.config.initial_equity:,.2f}",
        ]

    @staticmethod
    def _trades(r: BacktestResult) -> list[str]:
        lines = [f"TOTAL CLOSED TRADES : {r.total_trades}"]
        if not r.trades:
            return lines
        lines += [
            f"Winning trades      : {r.winning_trades} ({r.win_rate_pct:.1f}%)",
            f"Realized PnL        : {r.realized_pnl:,.2f}",
            f"Avg bars held       : {r.avg_bars_held:.1f}",
            "",
            "Trade log:",
            f"{'#':>2}  {'Entry':<12}{'EntryPx':>11}  {'Exit':<12}"
            f"{'ExitPx':>11}{'PnL':>12}{'Ret%':>7}{'Bars':>6}",
        ]
        for n, t in enumerate(r.trades, 1):
            lines.append(
                f"{n:>2}  {str(t.entry_date.date()):<12}{t.entry_price:>11.2f}  "
                f"{str(t.exit_date.date()):<12}{t.exit_price:>11.2f}"
                f"{t.pnl:>12.2f}{t.return_pct:>7.2f}{t.bars_held:>6}"
            )
        return lines

    @staticmethod
    def _open_trade(r: BacktestResult) -> list[str]:
        ot = r.open_trade
        if ot is None:
            return ["OPEN TRADE : none (flat at end of data)"]
        return [
            "OPEN TRADE (still holding at end of data):",
            f"  Entry date        : {ot.entry_date.date()}",
            f"  Entry price       : {ot.entry_price:.2f}",
            f"  Last close        : {ot.last_close:.2f}",
            f"  Unrealized PnL    : {ot.unrealized_pnl:,.2f}",
            f"  Unrealized return : {ot.unrealized_return_pct:.2f}%",
        ]

    @staticmethod
    def _performance(r: BacktestResult) -> list[str]:
        return [
            f"Final equity (MTM)  : {r.final_equity:,.2f}",
            f"Total return        : {r.total_return_pct:.2f}%",
            f"Max drawdown        : {r.max_drawdown_pct:.2f}%",
        ]


class EquityCurveExporter(Reporter):
    """Persists the equity curve as a CSV."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def report(self, result: BacktestResult) -> None:
        result.equity_curve.to_csv(self._path, index=False)
        print(f"Equity curve saved  : {self._path}")


class EquityCurvePlotter(Reporter):
    """Renders the equity curve to a PNG (no-op if matplotlib is absent)."""

    def __init__(self, path: str | Path, title: str = "Equity Curve") -> None:
        self._path = Path(path)
        self._title = title

    def report(self, result: BacktestResult) -> None:
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            print("Equity curve plot   : skipped (matplotlib not installed)")
            return

        curve = result.equity_curve
        fig, ax = plt.subplots(figsize=(11, 5))
        ax.plot(curve["date"], curve["equity"], color="#1565c0")
        ax.set_title(self._title)
        ax.set_xlabel("Date")
        ax.set_ylabel("Equity (mark-to-market)")
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(self._path, dpi=120)
        plt.close(fig)
        print(f"Equity curve plot   : {self._path}")
