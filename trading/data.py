"""Data sources.

A ``DataSource`` answers one question: *"give me the candles."* Defining it as
an abstract base class lets the engine stay ignorant of whether candles come
from a CSV, a database, or a broker API (Dependency Inversion / Open-Closed).
Add a new source by subclassing ``DataSource`` — nothing else changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

# Canonical column names every source must return, lowest index = oldest.
OHLC_COLUMNS = ["Date", "Open", "High", "Low", "Close"]


class DataSource(ABC):
    """Abstract provider of chronologically-sorted OHLC candles."""

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Return a DataFrame with columns ``OHLC_COLUMNS``, oldest row first."""


class CsvDataSource(DataSource):
    """Load candles from an NSE-style historical CSV.

    The NSE export is newest-first and quotes every field; this class
    normalises it into a clean, chronologically-ascending numeric frame.
    """

    def __init__(self, path: str | Path, date_format: str = "%d %b %Y") -> None:
        self._path = Path(path)
        self._date_format = date_format

    def load(self) -> pd.DataFrame:
        if not self._path.exists():
            raise FileNotFoundError(f"CSV not found: {self._path}")

        df = pd.read_csv(self._path)
        df.columns = [c.strip() for c in df.columns]

        missing = [c for c in OHLC_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        df["Date"] = pd.to_datetime(df["Date"], format=self._date_format)
        for col in ("Open", "High", "Low", "Close"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df[OHLC_COLUMNS].dropna(subset=["Open", "High", "Low", "Close"])
        return df.sort_values("Date").reset_index(drop=True)
