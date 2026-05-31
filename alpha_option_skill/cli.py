"""Command line interface for broker checks and option orders."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import logging
from dataclasses import asdict, is_dataclass
from typing import Any, Sequence

from alpha_option_skill.brokers import (
    MoomooConfig,
    MoomooOptionsBroker,
    OptionOrder,
    UnsupportedOperation,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alpha")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--broker", default="moomoo", choices=["moomoo"])
    common.add_argument("--account", default="paper", choices=["paper", "live"])
    common.add_argument("--host", default="127.0.0.1")
    common.add_argument("--port", type=int, default=11111)
    common.add_argument("--market", default="US")
    common.add_argument("--security-firm")
    common.add_argument("--format", default="table", choices=["table", "json"])
    common.add_argument("--verbose", action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("account", parents=[common])
    subparsers.add_parser("positions", parents=[common])
    subparsers.add_parser("orders", parents=[common])

    quote = subparsers.add_parser("quote", parents=[common])
    quote.add_argument("--type", default="option", choices=["option"])
    quote.add_argument("--contract", required=True)

    chain = subparsers.add_parser("chain", parents=[common])
    chain.add_argument("--type", default="option", choices=["option"])
    chain.add_argument("--symbol", required=True)

    order = subparsers.add_parser("order", parents=[common])
    order.add_argument("--type", required=True, choices=["option", "stock"])
    order.add_argument("--symbol", required=True)
    order.add_argument("--contract")
    order.add_argument("--side", required=True, choices=["buy", "sell"])
    order.add_argument("--qty", required=True, type=int)
    order.add_argument("--limit", required=True, type=float)
    execution = order.add_mutually_exclusive_group(required=True)
    execution.add_argument("--dry-run", action="store_true", help="Only print the order plan.")
    execution.add_argument("--submit", action="store_true", help="Submit the order to the selected account.")

    return parser


def broker_from_args(args: argparse.Namespace) -> MoomooOptionsBroker:
    trade_env = "SIMULATE" if args.account == "paper" else "REAL"
    config = MoomooConfig(
        host=args.host,
        port=args.port,
        market=args.market.upper(),
        trade_env=trade_env,
        security_firm=args.security_firm,
    )
    return MoomooOptionsBroker(config)


def to_builtin(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "to_dict"):
        return value.to_dict(orient="records")
    if isinstance(value, dict):
        return {key: to_builtin(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(item) for item in value]
    return value


def print_json(value: Any) -> None:
    print(json.dumps(to_builtin(value), indent=2, sort_keys=True, default=str))


def preferred_columns(value: Any) -> list[str]:
    if not hasattr(value, "columns"):
        return []

    candidates = [
        "code",
        "stock_name",
        "name",
        "qty",
        "can_sell_qty",
        "position_side",
        "cost_price",
        "average_cost",
        "market_val",
        "nominal_price",
        "last_price",
        "bid_price",
        "ask_price",
        "pl_val",
        "pl_ratio",
        "unrealized_pl",
        "currency",
        "order_id",
        "order_status",
        "trd_side",
        "price",
        "dealt_qty",
        "create_time",
        "strike_price",
        "expiration_date",
        "option_type",
        "volume",
        "open_interest",
        "implied_volatility",
        "delta",
        "gamma",
        "theta",
        "vega",
    ]
    return [column for column in candidates if column in value.columns]


def print_table(value: Any) -> None:
    if hasattr(value, "empty") and hasattr(value, "to_string"):
        if value.empty:
            print("No rows.")
        else:
            columns = preferred_columns(value)
            printable = value[columns] if columns else value
            print(printable.to_string(index=False))
        return

    if is_dataclass(value):
        print_json(value)
        return

    if isinstance(value, dict):
        for key, item in value.items():
            print(f"{key}: {item}")
        return

    print(value)


def emit(value: Any, output_format: str) -> None:
    if output_format == "json":
        print_json(value)
    else:
        print_table(value)


def run_command(args: argparse.Namespace) -> Any:
    broker = broker_from_args(args)

    if args.command == "account":
        return broker.account()
    if args.command == "positions":
        return broker.positions()
    if args.command == "orders":
        return broker.orders()
    if args.command == "quote":
        return broker.option_quote(args.contract)
    if args.command == "chain":
        return broker.option_chain(args.symbol)
    if args.command == "order":
        if args.type == "stock":
            raise UnsupportedOperation("stock orders are not implemented yet")
        if not args.contract:
            raise SystemExit("--contract is required for option orders")
        dry_run = args.dry_run
        order = OptionOrder(
            symbol=args.symbol,
            contract_code=args.contract,
            side=args.side.upper(),
            quantity=args.qty,
            limit_price=args.limit,
            dry_run=dry_run,
        )
        return broker.place_option_order(order)
    raise SystemExit(f"Unsupported command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    logging.getLogger().setLevel(logging.ERROR)
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.verbose:
        result = run_command(args)
    else:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = run_command(args)
    emit(result, args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
