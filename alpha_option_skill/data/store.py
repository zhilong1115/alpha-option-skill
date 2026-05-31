"""SQLite-backed local store for Alpha market/account snapshots."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from alpha_option_skill.data.records import (
    DataSyncResult,
    EquityQuote,
    OptionContract,
    OptionQuote,
)
from alpha_option_skill.data.schema import SCHEMA_SQL


class AlphaDataStore:
    def __init__(self, path: str | Path = "alpha.db") -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.executemany(
                "INSERT OR IGNORE INTO data_sources(name, kind) VALUES (?, ?)",
                [("moomoo", "broker"), ("polygon", "market_data")],
            )

    def insert_equity_quotes(self, records: Iterable[EquityQuote]) -> int:
        rows = list(records)
        if not rows:
            return 0
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT INTO equity_quotes
                (source, symbol, observed_at, bid, ask, last, volume, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row.source,
                        row.symbol,
                        row.observed_at,
                        row.bid,
                        row.ask,
                        row.last,
                        row.volume,
                        json.dumps(row.raw, sort_keys=True, default=str),
                    )
                    for row in rows
                ],
            )
        return len(rows)

    def insert_option_contracts(self, records: Iterable[OptionContract]) -> int:
        rows = list(records)
        if not rows:
            return 0
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO option_contracts
                (source, contract_code, underlying, observed_at, expiration_date,
                 strike_price, option_type, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row.source,
                        row.contract_code,
                        row.underlying,
                        row.observed_at,
                        row.expiration_date,
                        row.strike_price,
                        row.option_type,
                        json.dumps(row.raw, sort_keys=True, default=str),
                    )
                    for row in rows
                ],
            )
        return len(rows)

    def insert_option_quotes(self, records: Iterable[OptionQuote]) -> int:
        rows = list(records)
        if not rows:
            return 0
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT INTO option_quotes
                (source, contract_code, underlying, observed_at, bid, ask, last, volume,
                 open_interest, implied_volatility, delta, gamma, theta, vega, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row.source,
                        row.contract_code,
                        row.underlying,
                        row.observed_at,
                        row.bid,
                        row.ask,
                        row.last,
                        row.volume,
                        row.open_interest,
                        row.implied_volatility,
                        row.delta,
                        row.gamma,
                        row.theta,
                        row.vega,
                        json.dumps(row.raw, sort_keys=True, default=str),
                    )
                    for row in rows
                ],
            )
        return len(rows)

    def record_sync_result(self, result: DataSyncResult) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sync_runs
                (source, ok, message, equity_quotes, option_contracts, option_quotes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result.source,
                    1 if result.ok else 0,
                    result.message,
                    result.equity_quotes,
                    result.option_contracts,
                    result.option_quotes,
                ),
            )

    def table_count(self, table: str) -> int:
        allowed = {"equity_quotes", "option_contracts", "option_quotes", "sync_runs"}
        if table not in allowed:
            raise ValueError(f"unsupported table: {table}")
        with self.connect() as conn:
            return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
