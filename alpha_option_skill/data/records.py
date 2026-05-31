"""Normalized records stored by the local Alpha data layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class EquityQuote:
    source: str
    symbol: str
    observed_at: str = field(default_factory=utc_now_iso)
    bid: float | None = None
    ask: float | None = None
    last: float | None = None
    volume: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OptionContract:
    source: str
    contract_code: str
    underlying: str
    observed_at: str = field(default_factory=utc_now_iso)
    expiration_date: str | None = None
    strike_price: float | None = None
    option_type: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OptionQuote:
    source: str
    contract_code: str
    underlying: str | None = None
    observed_at: str = field(default_factory=utc_now_iso)
    bid: float | None = None
    ask: float | None = None
    last: float | None = None
    volume: float | None = None
    open_interest: float | None = None
    implied_volatility: float | None = None
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DataSyncResult:
    source: str
    ok: bool
    equity_quotes: int = 0
    option_contracts: int = 0
    option_quotes: int = 0
    message: str = ""
