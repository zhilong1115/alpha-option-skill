"""Command line interface for broker checks and option orders."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import logging
from dataclasses import asdict, is_dataclass
from typing import Any, Sequence

from alpha_option_skill.brokers import MoomooConfig, MoomooOptionsBroker, OptionOrder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alpha-option")
    parser.add_argument("--broker", default="moomoo", choices=["moomoo"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11111)
    parser.add_argument("--market", default="US")
    parser.add_argument("--env", default="simulate", choices=["simulate", "real"])
    parser.add_argument("--security-firm")
    parser.add_argument("--format", default="table", choices=["table", "json"])
    parser.add_argument("--verbose", action="store_true")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("account")
    subparsers.add_parser("positions")
    subparsers.add_parser("orders")

    option_quote = subparsers.add_parser("option-quote")
    option_quote.add_argument("contract_code")

    option_chain = subparsers.add_parser("option-chain")
    option_chain.add_argument("symbol")

    order = subparsers.add_parser("place-option-order")
    order.add_argument("--symbol", required=True)
    order.add_argument("--contract-code", required=True)
    order.add_argument("--side", required=True, choices=["BUY", "SELL"])
    order.add_argument("--qty", required=True, type=int)
    order.add_argument("--limit", required=True, type=float)
    order.add_argument("--no-dry-run", action="store_true")
    order.add_argument(
        "--confirm-live-order",
        action="store_true",
        help="Required with --no-dry-run when --env real.",
    )

    return parser


def broker_from_args(args: argparse.Namespace) -> MoomooOptionsBroker:
    config = MoomooConfig(
        host=args.host,
        port=args.port,
        market=args.market.upper(),
        trade_env=args.env.upper(),
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
    if args.command == "option-quote":
        return broker.option_quote(args.contract_code)
    if args.command == "option-chain":
        return broker.option_chain(args.symbol)
    if args.command == "place-option-order":
        dry_run = not args.no_dry_run
        if args.env == "real" and not dry_run and not args.confirm_live_order:
            raise SystemExit("--confirm-live-order is required for real non-dry-run orders")
        order = OptionOrder(
            symbol=args.symbol,
            contract_code=args.contract_code,
            side=args.side,
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
