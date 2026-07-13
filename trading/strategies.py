"""Trading strategies.

A ``Strategy`` encapsulates *only* the decision logic: given the price history
so far, should we enter, and if we hold, should we exit? It owns its own
parameters. The engine treats every strategy identically through this
interface, so new ideas plug in without engine changes (Open-Closed, Liskov).

Contract:
    * ``entry_price``  -> the price to buy at, or ``None`` for no entry.
    * ``exit_price``   -> the price to sell at, or ``None`` to keep holding.
Both receive the full history and the index of the *current* bar; they must
never look at future bars (no look-ahead bias).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from trading.models import Position


class Strategy(ABC):
    """Abstract entry/exit decision maker."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short human-readable strategy name."""

    @abstractmethod
    def describe(self) -> str:
        """One-line description of the rules and parameters, for reports."""

    @abstractmethod
    def entry_price(self, data: pd.DataFrame, index: int) -> float | None:
        """Price to buy at on bar ``index``, or ``None`` to stay flat."""

    @abstractmethod
    def exit_price(
        self, data: pd.DataFrame, index: int, position: Position
    ) -> float | None:
        """Price to sell an open ``position`` at on bar ``index``, or ``None``."""


class DonchianBreakoutStrategy(Strategy):
    """N-day high breakout with a fixed take-profit and no stop loss.

    Entry: current close breaks above the highest High of the previous
           ``lookback`` bars (an upper Donchian-channel breakout).
    Exit:  a limit take-profit at ``entry * (1 + take_profit)`` — filled on the
           first later bar whose High reaches the target.

    Args:
        lookback: number of prior bars forming the breakout high.
        take_profit: profit target as a fraction (0.05 == 5%).
    """

    def __init__(self, lookback: int = 7, take_profit: float = 0.05) -> None:
        if lookback < 1:
            raise ValueError("lookback must be >= 1")
        if take_profit <= 0:
            raise ValueError("take_profit must be positive")
        self.lookback = lookback
        self.take_profit = take_profit

    @property
    def name(self) -> str:
        return "Donchian Breakout"

    def describe(self) -> str:
        return (
            f"close > highest High of previous {self.lookback} candles; "
            f"take profit {self.take_profit * 100:.0f}% (no stop loss)"
        )

    def entry_price(self, data: pd.DataFrame, index: int) -> float | None:
        if index < self.lookback:
            return None  # not enough history yet
        prior_high = data["High"].iloc[index - self.lookback : index].max()
        close = data["Close"].iloc[index]
        return float(close) if close > prior_high else None

    def exit_price(
        self, data: pd.DataFrame, index: int, position: Position
    ) -> float | None:
        target = position.entry_price * (1.0 + self.take_profit)
        high = data["High"].iloc[index]
        return float(target) if high >= target else None
