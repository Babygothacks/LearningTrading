"""Unit tests for the backtesting engine and strategy.

These use small hand-built price series so every expected number can be
reasoned about by hand — that is what makes the design's correctness testable.
"""

from __future__ import annotations

import pandas as pd
import pytest

from trading import (
    AllInSizer,
    Backtester,
    BacktestConfig,
    DonchianBreakoutStrategy,
)


def _frame(closes, highs=None):
    """Build an OHLC frame from a list of closes (highs default to closes)."""
    highs = highs if highs is not None else closes
    dates = pd.date_range("2026-01-01", periods=len(closes), freq="D")
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": closes,
            "High": highs,
            "Low": closes,
            "Close": closes,
        }
    )


def test_no_entry_before_enough_history():
    strat = DonchianBreakoutStrategy(lookback=7, take_profit=0.05)
    # Fewer bars than lookback -> never enough prior data to trigger.
    result = Backtester(strat).run(_frame([100, 101, 102]))
    assert result.total_trades == 0
    assert result.open_trade is None


def test_breakout_opens_a_position():
    strat = DonchianBreakoutStrategy(lookback=3, take_profit=0.05)
    # First 3 bars flat at 100, then a breakout to 110 on bar index 3.
    closes = [100, 100, 100, 110, 110]
    result = Backtester(strat).run(_frame(closes))
    assert result.open_trade is not None
    assert result.open_trade.entry_price == 110


def test_take_profit_closes_at_target():
    strat = DonchianBreakoutStrategy(lookback=3, take_profit=0.05)
    # Breakout at 100 (bar 3); later bar's High reaches the +5% target (105).
    # Final close (100) is below the prior 3-bar high (101) so it does NOT
    # re-enter after the exit -> the run ends flat.
    closes = [90, 90, 90, 100, 101, 100]
    highs = [90, 90, 90, 100, 101, 106]  # bar 5 high 106 >= 105 target
    result = Backtester(strat).run(_frame(closes, highs))
    assert result.total_trades == 1
    trade = result.trades[0]
    assert trade.exit_price == pytest.approx(105.0)
    assert trade.return_pct == pytest.approx(5.0)
    assert result.open_trade is None


def test_only_one_position_at_a_time():
    strat = DonchianBreakoutStrategy(lookback=2, take_profit=0.05)
    # Continuous new highs would trigger repeatedly, but we hold just one.
    closes = [100, 101, 102, 103, 104, 105]
    result = Backtester(strat).run(_frame(closes))
    # Never hits +5% target, so it enters once and stays open.
    assert result.total_trades == 0
    assert result.open_trade is not None
    assert result.open_trade.entry_price == 102  # first breakout bar


def test_equity_curve_has_one_point_per_bar():
    strat = DonchianBreakoutStrategy(lookback=3, take_profit=0.05)
    closes = [100, 100, 100, 110, 110]
    result = Backtester(strat, BacktestConfig(initial_equity=50_000)).run(_frame(closes))
    assert len(result.equity_curve) == len(closes)
    # Flat until the first entry -> equity unchanged on early bars.
    assert result.equity_curve["equity"].iloc[0] == pytest.approx(50_000)


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        BacktestConfig(initial_equity=0)


def test_invalid_strategy_params_rejected():
    with pytest.raises(ValueError):
        DonchianBreakoutStrategy(lookback=0)
    with pytest.raises(ValueError):
        DonchianBreakoutStrategy(take_profit=0)
