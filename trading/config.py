"""Configuration value objects.

Configuration is kept separate from behaviour so the same engine can be
driven with different settings without code changes (Dependency Inversion:
the engine depends on this abstraction, not on hard-coded literals).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestConfig:
    """Settings that govern a single backtest run.

    Attributes:
        initial_equity: Starting capital for the simulated account.

    Note:
        Strategy parameters (look-back window, profit target, ...) live on the
        strategy itself, not here. This class only owns account-level concerns.
    """

    initial_equity: float = 100_000.0

    def __post_init__(self) -> None:
        if self.initial_equity <= 0:
            raise ValueError("initial_equity must be positive")
