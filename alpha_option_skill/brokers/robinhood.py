"""Robinhood Trading MCP placeholder.

Robinhood's current official Trading MCP supports long equities, not options.
This connector documents that boundary so the options skill does not silently
route option orders to an unsupported broker.
"""

from __future__ import annotations

from typing import Any

from alpha_option_skill.brokers.base import (
    BrokerCapabilities,
    OptionOrder,
    OrderResult,
    UnsupportedOperation,
)


class RobinhoodMcpBroker:
    name = "robinhood_mcp"

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

    def account(self) -> Any:
        raise UnsupportedOperation("Robinhood MCP account wiring is not implemented yet.")

    def positions(self) -> Any:
        raise UnsupportedOperation("Robinhood MCP positions wiring is not implemented yet.")

    def option_chain(self, symbol: str, **kwargs: Any) -> Any:
        raise UnsupportedOperation(
            "Robinhood Trading MCP currently supports long equities only, not options."
        )

    def option_quote(self, contract_code: str) -> Any:
        raise UnsupportedOperation(
            "Robinhood Trading MCP currently supports long equities only, not options."
        )

    def orders(self, **kwargs: Any) -> Any:
        raise UnsupportedOperation("Robinhood MCP order history wiring is not implemented yet.")

    def place_option_order(self, order: OptionOrder) -> OrderResult:
        raise UnsupportedOperation(
            "Robinhood Trading MCP currently supports long equities only, not options."
        )
