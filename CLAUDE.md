# CLAUDE.md

Guidance for working in this repository. This is a learning project for
backtesting trading strategies on NSE (Indian market) historical data.

## What this project is

A small, extensible backtesting toolkit. Given historical OHLC candles and a
strategy, it simulates trades bar by bar and reports performance (trade log,
equity curve, open position, drawdown).

The reference strategy is a **7-day Donchian breakout** with a fixed 5%
take-profit and no stop loss:
- **Buy** when the current close is above the highest High of the previous 7 candles.
- **Sell** when profit reaches 5% (modeled as a limit fill at `entry * 1.05`).
- Only **one open position** at a time.

## Environment & commands

Python is managed with **uv**. `uv` lives at `C:\Users\ganes\.local\bin`
(added to PATH for new terminals). Dependencies are pinned in `uv.lock`.

```powershell
uv sync                              # recreate the environment from the lock
uv run python backtest.py            # run the default backtest
uv run python backtest.py "data.csv" # run against a different CSV
uv run pytest -q                     # run the test suite
uv add <pkg>                         # add a runtime dependency
uv add --dev <pkg>                   # add a dev dependency
```

Do **not** call `pip` directly or use a globally-installed Python — always go
through `uv run` so the locked environment is used.

## Architecture

Code lives in the `trading/` package. The design follows SOLID/DRY so new
strategies, data sources, sizing rules, and reports can be added **without
modifying existing files**. `backtest.py` is only a thin composition root.

```
trading/
├── config.py      # BacktestConfig — account-level settings (value object)
├── models.py      # Bar, Trade, Position, OpenTrade, BacktestResult (data only)
├── data.py        # DataSource (ABC) + CsvDataSource
├── strategies.py  # Strategy (ABC) + DonchianBreakoutStrategy
├── sizing.py      # PositionSizer (ABC) + AllInSizer / FixedFractionSizer
├── engine.py      # Backtester — the simulation loop
└── reporting.py   # Reporter (ABC) + Console / CSV / Plot reporters
backtest.py        # composition root (wires concrete classes together)
tests/             # pytest suite
```

### How the SOLID principles map to the code

- **Single Responsibility** — each module owns exactly one concern: loading
  data, deciding trades, sizing, simulating, or reporting. `models.py` holds
  data with no behaviour beyond derived read-only metrics.
- **Open-Closed** — add a new strategy/data source/sizer/reporter by
  subclassing the relevant ABC. The `Backtester` never changes.
- **Liskov** — the engine uses any `Strategy`/`PositionSizer`
  interchangeably through their abstract interface.
- **Interface Segregation** — interfaces are minimal (`Strategy` has
  `entry_price`/`exit_price`; `PositionSizer` has one method).
- **Dependency Inversion** — `Backtester` depends on the abstractions
  (`Strategy`, `PositionSizer`, and DataFrames from a `DataSource`), never on
  concrete implementations. Concretes are injected in `backtest.py`.

### Key contracts

- **DataSource.load()** returns a DataFrame with columns
  `Date, Open, High, Low, Close`, sorted **oldest-first**. (The NSE CSV is
  newest-first and quoted; `CsvDataSource` normalises it.)
- **Strategy.entry_price(data, i)** → price to buy at, or `None`.
  **Strategy.exit_price(data, i, position)** → price to sell at, or `None`.
  Strategies must use only bars `0..i` — **never look at future bars**
  (avoid look-ahead bias).
- **BacktestResult** exposes all metrics as properties (`total_return_pct`,
  `max_drawdown_pct`, `win_rate_pct`, ...) so reporters never recompute them.

## How to extend

**Add a new strategy** — create a subclass in `trading/strategies.py`:

```python
class MyStrategy(Strategy):
    @property
    def name(self) -> str: ...
    def describe(self) -> str: ...
    def entry_price(self, data, index): ...        # -> float | None
    def exit_price(self, data, index, position): ... # -> float | None
```

Then use it in `backtest.py`: `strategy = MyStrategy(...)`. Nothing else changes.

**Add a stop loss / trailing exit** — put the logic in a strategy's
`exit_price` (it already receives the open `position` and full history).

**Add a new data source** (DB, API) — subclass `DataSource` and implement
`load()` to return the canonical DataFrame.

**Add a new output** (JSON, HTML) — subclass `Reporter` and implement
`report(result)`; append an instance to the `reporters` list in `backtest.py`.

## Conventions

- Python 3.14+, full type hints, `from __future__ import annotations`.
- Prefer `@dataclass(frozen=True)` for value objects; validate in
  `__post_init__` / `__init__`.
- Abstract base classes (`abc.ABC`) for every extension point.
- Every new behaviour needs a test in `tests/` using small hand-built series
  whose expected numbers can be verified by hand.
- Keep `backtest.py` a thin composition root — no business logic there.

## Modeling assumptions (document any change to these)

- Entry fills at the signal bar's **close**.
- Take-profit is a **limit order** filled at exactly `entry * (1 + take_profit)`
  on the first later bar whose High reaches the target.
- Position sizing is **all-in** (`equity / price`) by default.
- No commissions, slippage, or fees are modeled.
- After a take-profit exit, the engine may **re-enter on the same bar** if the
  entry condition holds again.

## Data

`NSE_NIFTY 50_Historical_PR_01012026to12072026.csv` — NIFTY 50 daily candles,
Jan–Jul 2026, newest-first, quoted fields, date format `%d %b %Y`.
Outputs `equity_curve.csv` and `equity_curve.png` are generated artifacts.
