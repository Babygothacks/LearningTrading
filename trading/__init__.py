"""Reusable, extensible backtesting toolkit.

Public API — import the pieces you need:

    from trading import (
        BacktestConfig,
        CsvDataSource,
        DonchianBreakoutStrategy,
        AllInSizer,
        Backtester,
        ConsoleReporter,
        EquityCurvePlotter,
    )

The package is organised by responsibility (SOLID):

- ``config``      : configuration value objects
- ``models``      : plain data containers (no behaviour)
- ``data``        : where candles come from
- ``strategies``  : entry / exit decision logic
- ``sizing``      : how large a position to take
- ``engine``      : the simulation loop
- ``reporting``   : how results are presented / persisted
"""

from trading.config import BacktestConfig
from trading.data import CsvDataSource, DataSource
from trading.engine import Backtester
from trading.models import Bar, BacktestResult, OpenTrade, Trade
from trading.reporting import (
    ConsoleReporter,
    EquityCurveExporter,
    EquityCurvePlotter,
    Reporter,
)
from trading.sizing import AllInSizer, PositionSizer
from trading.strategies import DonchianBreakoutStrategy, Strategy

__all__ = [
    "BacktestConfig",
    "DataSource",
    "CsvDataSource",
    "Bar",
    "Trade",
    "OpenTrade",
    "BacktestResult",
    "Strategy",
    "DonchianBreakoutStrategy",
    "PositionSizer",
    "AllInSizer",
    "Backtester",
    "Reporter",
    "ConsoleReporter",
    "EquityCurveExporter",
    "EquityCurvePlotter",
]
