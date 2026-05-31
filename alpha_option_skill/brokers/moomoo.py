"""Moomoo OpenAPI options connector.

The connector imports the optional moomoo SDK lazily. Dry-run order planning
works without the SDK or a running OpenD process.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from alpha_option_skill.brokers.base import (
    BrokerCapabilities,
    BrokerDependencyError,
    BrokerError,
    OptionOrder,
    OrderResult,
)


@dataclass(frozen=True)
class MoomooConfig:
    host: str = "127.0.0.1"
    port: int = 11111
    market: str = "US"
    trade_env: str = "SIMULATE"
    security_firm: str | None = None


class MoomooOptionsBroker:
    name = "moomoo"

    def __init__(self, config: MoomooConfig | None = None) -> None:
        self.config = config or MoomooConfig()

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            options_chain=True,
            options_quotes=True,
            options_orders=True,
            equity_orders=True,
            paper_trading=True,
            multi_leg_options=False,
        )

    def _sdk(self) -> Any:
        try:
            import moomoo  # type: ignore[import-not-found]
        except ImportError as exc:
            raise BrokerDependencyError(
                "moomoo SDK is not installed. Install with: python -m pip install '.[moomoo]'"
            ) from exc
        return moomoo

    def _call_ok(self, ret: Any, data: Any, action: str) -> Any:
        sdk = self._sdk()
        if ret != sdk.RET_OK:
            raise BrokerError(f"moomoo {action} failed: {data}")
        return data

    def quote_context(self) -> Any:
        sdk = self._sdk()
        return sdk.OpenQuoteContext(host=self.config.host, port=self.config.port)

    def trade_context(self) -> Any:
        sdk = self._sdk()
        kwargs: dict[str, Any] = {"host": self.config.host, "port": self.config.port}
        if self.config.security_firm:
            kwargs["security_firm"] = self.config.security_firm
        return sdk.OpenSecTradeContext(**kwargs)

    def account(self) -> Any:
        sdk = self._sdk()
        with self.trade_context() as ctx:
            ret, data = ctx.accinfo_query(trd_env=getattr(sdk.TrdEnv, self.config.trade_env))
            return self._call_ok(ret, data, "account query")

    def positions(self) -> Any:
        sdk = self._sdk()
        with self.trade_context() as ctx:
            ret, data = ctx.position_list_query(trd_env=getattr(sdk.TrdEnv, self.config.trade_env))
            return self._call_ok(ret, data, "positions query")

    def orders(self, **kwargs: Any) -> Any:
        sdk = self._sdk()
        with self.trade_context() as ctx:
            params = {"trd_env": getattr(sdk.TrdEnv, self.config.trade_env), **kwargs}
            ret, data = ctx.order_list_query(**params)
            return self._call_ok(ret, data, "orders query")

    def option_chain(self, symbol: str, **kwargs: Any) -> Any:
        with self.quote_context() as ctx:
            ret, data = ctx.get_option_chain(code=symbol, **kwargs)
            return self._call_ok(ret, data, "option chain query")

    def option_quote(self, contract_code: str) -> Any:
        with self.quote_context() as ctx:
            ret, data = ctx.get_market_snapshot([contract_code])
            return self._call_ok(ret, data, "option quote query")

    def place_option_order(self, order: OptionOrder) -> OrderResult:
        if order.dry_run:
            return OrderResult(
                broker=self.name,
                dry_run=True,
                accepted=True,
                message=(
                    f"DRY RUN: {order.side} {order.quantity} {order.contract_code} "
                    f"@ limit {order.limit_price:.2f}"
                ),
                raw={"order": order},
            )

        sdk = self._sdk()
        side = sdk.TrdSide.BUY if order.side == "BUY" else sdk.TrdSide.SELL
        with self.trade_context() as ctx:
            ret, data = ctx.place_order(
                price=order.limit_price,
                qty=order.quantity,
                code=order.contract_code,
                trd_side=side,
                order_type=sdk.OrderType.NORMAL,
                trd_env=getattr(sdk.TrdEnv, self.config.trade_env),
            )
            result = self._call_ok(ret, data, "place option order")

        order_id = None
        if hasattr(result, "iloc") and "order_id" in result:
            order_id = str(result.iloc[0]["order_id"])
        elif isinstance(result, dict) and "order_id" in result:
            order_id = str(result["order_id"])

        return OrderResult(
            broker=self.name,
            dry_run=False,
            accepted=True,
            order_id=order_id,
            message="Option order submitted to moomoo.",
            raw=result,
        )
