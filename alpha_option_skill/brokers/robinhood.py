"""Robinhood Agentic Trading MCP connector.

The official Robinhood Agentic Trading MCP currently targets a dedicated
Agentic Account and long-equity trading. Options are intentionally rejected so
the options skill does not silently route unsupported orders.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any

from alpha_option_skill.brokers.base import (
    BrokerCapabilities,
    BrokerDependencyError,
    BrokerError,
    OptionOrder,
    OrderResult,
    StockOrder,
    UnsupportedOperation,
)


DEFAULT_MCP_URL = "https://agent.robinhood.com/mcp/trading"


@dataclass(frozen=True)
class RobinhoodMcpConfig:
    server_url: str = DEFAULT_MCP_URL
    account_tool: str = "get_account"
    positions_tool: str = "get_positions"
    orders_tool: str = "get_orders"
    order_tool: str = "place_order"
    timeout_ms: int = 30000

    @classmethod
    def from_env(cls, server_url: str | None = None) -> "RobinhoodMcpConfig":
        return cls(
            server_url=server_url or os.getenv("ALPHA_ROBINHOOD_MCP_URL", DEFAULT_MCP_URL),
            account_tool=os.getenv("ALPHA_ROBINHOOD_ACCOUNT_TOOL", "get_account"),
            positions_tool=os.getenv("ALPHA_ROBINHOOD_POSITIONS_TOOL", "get_positions"),
            orders_tool=os.getenv("ALPHA_ROBINHOOD_ORDERS_TOOL", "get_orders"),
            order_tool=os.getenv("ALPHA_ROBINHOOD_ORDER_TOOL", "place_order"),
            timeout_ms=int(os.getenv("ALPHA_ROBINHOOD_MCP_TIMEOUT_MS", "30000")),
        )


class RobinhoodMcpBroker:
    name = "robinhood"

    def __init__(self, config: RobinhoodMcpConfig | None = None) -> None:
        self.config = config or RobinhoodMcpConfig.from_env()

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            options_chain=False,
            options_quotes=False,
            options_orders=False,
            equity_orders=True,
            paper_trading=False,
            multi_leg_options=False,
        )

    def _selector(self, tool: str) -> str:
        return f"{self.config.server_url}.{tool}"

    def _call_mcp(self, tool: str, args: dict[str, Any] | None = None) -> Any:
        payload = args or {}
        command = [
            "mcporter",
            "call",
            self._selector(tool),
            "--args",
            json.dumps(payload),
            "--output",
            "json",
            "--timeout",
            str(self.config.timeout_ms),
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                text=True,
                capture_output=True,
                timeout=self.config.timeout_ms / 1000,
            )
        except FileNotFoundError as exc:
            raise BrokerDependencyError("mcporter is required for Robinhood MCP. Install mcporter first.") from exc
        except subprocess.TimeoutExpired as exc:
            raise BrokerError(
                f"Robinhood MCP tool '{tool}' timed out. "
                f"Authorize Robinhood MCP first: mcporter auth {self.config.server_url}"
            ) from exc

        if completed.returncode != 0:
            details = (completed.stderr or completed.stdout).strip()
            auth_hint = (
                f"Authorize Robinhood MCP first: mcporter auth {self.config.server_url}"
                if "OAuth" in details or "authorization" in details.lower() or "auth" in details.lower()
                else ""
            )
            message = f"Robinhood MCP tool '{tool}' failed"
            if details:
                message = f"{message}: {details}"
            if auth_hint:
                message = f"{message}\n{auth_hint}"
            raise BrokerError(message)

        output = completed.stdout.strip()
        if not output:
            return {}
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output

    def account(self) -> Any:
        return self._call_mcp(self.config.account_tool)

    def positions(self) -> Any:
        return self._call_mcp(self.config.positions_tool)

    def option_chain(self, symbol: str, **kwargs: Any) -> Any:
        raise UnsupportedOperation(
            "Robinhood Trading MCP currently supports long equities only, not options."
        )

    def option_quote(self, contract_code: str) -> Any:
        raise UnsupportedOperation(
            "Robinhood Trading MCP currently supports long equities only, not options."
        )

    def orders(self, **kwargs: Any) -> Any:
        return self._call_mcp(self.config.orders_tool, kwargs)

    def place_option_order(self, order: OptionOrder) -> OrderResult:
        raise UnsupportedOperation(
            "Robinhood Trading MCP currently supports long equities only, not options."
        )

    def place_stock_order(self, order: StockOrder) -> OrderResult:
        if order.dry_run:
            return OrderResult(
                broker=self.name,
                dry_run=True,
                accepted=True,
                message=(
                    f"DRY RUN: {order.side} {order.quantity} {order.symbol} "
                    f"@ limit {order.limit_price:.2f}"
                ),
                raw={"order": order},
            )

        result = self._call_mcp(
            self.config.order_tool,
            {
                "symbol": order.symbol,
                "side": order.side.lower(),
                "quantity": order.quantity,
                "order_type": "limit",
                "limit_price": order.limit_price,
                **order.metadata,
            },
        )
        order_id = None
        if isinstance(result, dict):
            order_id = result.get("order_id") or result.get("id")

        return OrderResult(
            broker=self.name,
            dry_run=False,
            accepted=True,
            order_id=str(order_id) if order_id else None,
            message="Stock order submitted to Robinhood MCP.",
            raw=result,
        )
