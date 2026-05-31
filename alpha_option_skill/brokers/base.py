"""Shared broker connector types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


class BrokerError(RuntimeError):
    """Base exception for broker connector failures."""


class BrokerDependencyError(BrokerError):
    """Raised when an optional broker SDK is not installed."""


class UnsupportedOperation(BrokerError):
    """Raised when a broker cannot support the requested action."""


OrderSide = Literal["BUY", "SELL"]


@dataclass(frozen=True)
class BrokerCapabilities:
    options_chain: bool = False
    options_quotes: bool = False
    options_orders: bool = False
    equity_orders: bool = False
    paper_trading: bool = False
    multi_leg_options: bool = False


@dataclass(frozen=True)
class OptionOrder:
    symbol: str
    contract_code: str
    side: OrderSide
    quantity: int
    limit_price: float
    dry_run: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.limit_price <= 0:
            raise ValueError("limit_price must be positive")


@dataclass(frozen=True)
class StockOrder:
    symbol: str
    side: OrderSide
    quantity: int
    limit_price: float
    dry_run: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.limit_price <= 0:
            raise ValueError("limit_price must be positive")


@dataclass(frozen=True)
class OrderResult:
    broker: str
    dry_run: bool
    accepted: bool
    message: str
    order_id: str | None = None
    raw: Any | None = None


class Broker(Protocol):
    @property
    def capabilities(self) -> BrokerCapabilities:
        ...

    def account(self) -> Any:
        ...

    def positions(self) -> Any:
        ...

    def option_chain(self, symbol: str, **kwargs: Any) -> Any:
        ...

    def option_quote(self, contract_code: str) -> Any:
        ...

    def orders(self, **kwargs: Any) -> Any:
        ...

    def place_option_order(self, order: OptionOrder) -> OrderResult:
        ...

    def place_stock_order(self, order: StockOrder) -> OrderResult:
        ...
