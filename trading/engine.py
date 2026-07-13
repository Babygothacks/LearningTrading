"""The backtesting engine.

``Backtester`` owns the simulation loop and account bookkeeping only. It never
decides *when* to trade (that is the strategy), *how much* to trade (the
sizer), or *how* to load data (the data source). It depends on those
abstractions, so any concrete implementation composes cleanly (Dependency
Inversion). This is what makes the whole system reusable and easy to extend.
"""

from __future__ import annotations

import pandas as pd

from trading.config import BacktestConfig
from trading.models import BacktestResult, OpenTrade, Position, Trade
from trading.sizing import AllInSizer, PositionSizer
from trading.strategies import Strategy


class Backtester:
    """Runs a :class:`Strategy` over historical candles bar by bar.

    Args:
        strategy: entry/exit decision logic.
        config: account-level settings (defaults to :class:`BacktestConfig`).
        sizer: position sizing rule (defaults to :class:`AllInSizer`).
    """

    def __init__(
        self,
        strategy: Strategy,
        config: BacktestConfig | None = None,
        sizer: PositionSizer | None = None,
    ) -> None:
        self._strategy = strategy
        self._config = config or BacktestConfig()
        self._sizer = sizer or AllInSizer()

    def run(self, data: pd.DataFrame) -> BacktestResult:
        """Execute the backtest and return a fully-populated result."""
        cash = self._config.initial_equity
        position: Position | None = None
        closed: list[Trade] = []
        equity_points: list[dict] = []

        for index in range(len(data)):
            bar = data.iloc[index]
            date, close = bar["Date"], float(bar["Close"])

            # 1. Manage an open position first (exit before considering entry).
            if position is not None:
                exit_price = self._strategy.exit_price(data, index, position)
                if exit_price is not None:
                    cash += self._realize(position, exit_price)
                    closed.append(self._make_trade(position, date, exit_price, index))
                    position = None

            # 2. Consider a new entry only when flat (one position at a time).
            if position is None:
                entry_price = self._strategy.entry_price(data, index)
                if entry_price is not None:
                    shares = self._sizer.size(cash, entry_price)
                    position = Position(
                        entry_index=index,
                        entry_date=date,
                        entry_price=entry_price,
                        shares=shares,
                    )

            # 3. Mark the account to market after this bar.
            equity_points.append({"date": date, "equity": self._mark_to_market(cash, position, close)})

        return BacktestResult(
            config=self._config,
            strategy_description=self._strategy.describe(),
            data=data,
            trades=closed,
            equity_curve=pd.DataFrame(equity_points),
            open_trade=self._make_open_trade(position, data),
        )

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _realize(position: Position, exit_price: float) -> float:
        """Cash change from closing ``position`` at ``exit_price``."""
        return (exit_price - position.entry_price) * position.shares

    @staticmethod
    def _make_trade(
        position: Position, exit_date, exit_price: float, exit_index: int
    ) -> Trade:
        pnl = (exit_price - position.entry_price) * position.shares
        return Trade(
            entry_date=position.entry_date,
            entry_price=position.entry_price,
            exit_date=exit_date,
            exit_price=exit_price,
            shares=position.shares,
            pnl=pnl,
            return_pct=(exit_price / position.entry_price - 1.0) * 100.0,
            bars_held=exit_index - position.entry_index,
        )

    @staticmethod
    def _mark_to_market(cash: float, position: Position | None, close: float) -> float:
        if position is None:
            return cash
        return cash + (close - position.entry_price) * position.shares

    @staticmethod
    def _make_open_trade(position: Position | None, data: pd.DataFrame) -> OpenTrade | None:
        if position is None:
            return None
        return OpenTrade(
            entry_date=position.entry_date,
            entry_price=position.entry_price,
            shares=position.shares,
            last_close=float(data["Close"].iloc[-1]),
        )
