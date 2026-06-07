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
    account_number: str | None = None
    account_tool: str = "get_accounts"
    portfolio_tool: str = "get_portfolio"
    positions_tool: str = "get_equity_positions"
    orders_tool: str = "get_equity_orders"
    order_tool: str = "place_equity_order"
    timeout_ms: int = 30000

    @classmethod
    def from_env(
        cls,
        server_url: str | None = None,
        account_number: str | None = None,
    ) -> "RobinhoodMcpConfig":
        return cls(
            server_url=server_url or os.getenv("ALPHA_ROBINHOOD_MCP_URL", DEFAULT_MCP_URL),
            account_number=account_number or os.getenv("ALPHA_ROBINHOOD_ACCOUNT_NUMBER"),
            account_tool=os.getenv("ALPHA_ROBINHOOD_ACCOUNT_TOOL", "get_accounts"),
            portfolio_tool=os.getenv("ALPHA_ROBINHOOD_PORTFOLIO_TOOL", "get_portfolio"),
            positions_tool=os.getenv("ALPHA_ROBINHOOD_POSITIONS_TOOL", "get_equity_positions"),
            orders_tool=os.getenv("ALPHA_ROBINHOOD_ORDERS_TOOL", "get_equity_orders"),
            order_tool=os.getenv("ALPHA_ROBINHOOD_ORDER_TOOL", "place_equity_order"),
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
            result = json.loads(output)
        except json.JSONDecodeError:
            return output
        if isinstance(result, dict) and result.get("error"):
            raise BrokerError(f"Robinhood MCP tool '{tool}' failed: {result['error']}")
        return result

    def _account_args(self) -> dict[str, str]:
        if not self.config.account_number:
            raise BrokerError(
                "Robinhood account number is required. Pass --account-number or set "
                "ALPHA_ROBINHOOD_ACCOUNT_NUMBER."
            )
        return {"account_number": self.config.account_number}

    def account(self) -> Any:
        if self.config.account_number:
            return self._call_mcp(self.config.portfolio_tool, self._account_args())
        return self._call_mcp(self.config.account_tool)

    def positions(self) -> Any:
        return self._call_mcp(self.config.positions_tool, self._account_args())

    def option_chain(self, symbol: str, **kwargs: Any) -> Any:
        raise UnsupportedOperation(
            "Robinhood Trading MCP currently supports long equities only, not options."
        )

    def option_quote(self, contract_code: str) -> Any:
        raise UnsupportedOperation(
            "Robinhood Trading MCP currently supports long equities only, not options."
        )

    def orders(self, **kwargs: Any) -> Any:
        return self._call_mcp(self.config.orders_tool, {**self._account_args(), **kwargs})

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
                **self._account_args(),
                "symbol": order.symbol,
                "side": order.side.lower(),
                "quantity": str(order.quantity),
                "type": "limit",
                "limit_price": str(order.limit_price),
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
