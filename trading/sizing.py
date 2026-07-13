"""Position sizing.

How *much* to buy is a decision independent of *when* to buy. Isolating it
behind ``PositionSizer`` lets you swap "all-in" for fixed-fraction, fixed-cash,
or volatility-based sizing without touching the strategy or the engine
(Single Responsibility + Open-Closed).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class PositionSizer(ABC):
    """Decides how many shares/units to buy given available equity."""

    @abstractmethod
    def size(self, equity: float, price: float) -> float:
        """Return the quantity to buy for ``equity`` cash at ``price``."""


class AllInSizer(PositionSizer):
    """Commit the entire account to each position (equity / price)."""

    def size(self, equity: float, price: float) -> float:
        if price <= 0:
            raise ValueError("price must be positive")
        return equity / price


class FixedFractionSizer(PositionSizer):
    """Commit a fixed fraction of equity to each position."""

    def __init__(self, fraction: float = 1.0) -> None:
        if not 0 < fraction <= 1:
            raise ValueError("fraction must be in (0, 1]")
        self._fraction = fraction

    def size(self, equity: float, price: float) -> float:
        if price <= 0:
            raise ValueError("price must be positive")
        return (equity * self._fraction) / price
