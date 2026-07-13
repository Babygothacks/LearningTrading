"""Plain data containers used across the package.

These classes hold data and derived read-only metrics only — they contain no
I/O and no trading logic. Keeping them behaviour-free (Single Responsibility)
means every other module can depend on them without coupling to how data is
loaded, how strategies decide, or how results are displayed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from trading.config import BacktestConfig


@dataclass(frozen=True)
class Bar:
    """A single OHLC candle (one trading period)."""

    date: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class Trade:
    """A completed round-trip (entry followed by exit)."""

    entry_date: datetime
    entry_price: float
    exit_date: datetime
    exit_price: float
    shares: float
    pnl: float
    return_pct: float
    bars_held: int


@dataclass(frozen=True)
class Position:
    """A currently-held position while the simulation is running."""

    entry_index: int
    entry_date: datetime
    entry_price: float
    shares: float


@dataclass(frozen=True)
class OpenTrade:
    """A position still held when the data ended (unrealised)."""

    entry_date: datetime
    entry_price: float
    shares: float
    last_close: float

    @property
    def unrealized_pnl(self) -> float:
        return (self.last_close - self.entry_price) * self.shares

    @property
    def unrealized_return_pct(self) -> float:
        return (self.last_close / self.entry_price - 1.0) * 100.0


@dataclass(frozen=True)
class BacktestResult:
    """Everything produced by a run, plus derived performance metrics.

    Metrics are computed on demand as properties so reporting code never has to
    recompute them (DRY) and there is a single source of truth for each figure.
    """

    config: BacktestConfig
    strategy_description: str
    data: pd.DataFrame
    trades: list[Trade]
    equity_curve: pd.DataFrame  # columns: date, equity
    open_trade: OpenTrade | None = field(default=None)

    @property
    def total_trades(self) -> int:
        return len(self.trades)

    @property
    def winning_trades(self) -> int:
        return sum(1 for t in self.trades if t.pnl > 0)

    @property
    def win_rate_pct(self) -> float:
        if not self.trades:
            return 0.0
        return self.winning_trades / self.total_trades * 100.0

    @property
    def realized_pnl(self) -> float:
        return sum(t.pnl for t in self.trades)

    @property
    def avg_bars_held(self) -> float:
        if not self.trades:
            return 0.0
        return sum(t.bars_held for t in self.trades) / self.total_trades

    @property
    def final_equity(self) -> float:
        return float(self.equity_curve["equity"].iloc[-1])

    @property
    def total_return_pct(self) -> float:
        return (self.final_equity / self.config.initial_equity - 1.0) * 100.0

    @property
    def max_drawdown_pct(self) -> float:
        equity = self.equity_curve["equity"]
        peak = equity.cummax()
        return float(((equity - peak) / peak).min() * 100.0)
