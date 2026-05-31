import unittest

from alpha_option_skill.cli import build_parser, run_command
from alpha_option_skill.brokers import (
    MoomooConfig,
    MoomooOptionsBroker,
    OptionOrder,
    RobinhoodMcpBroker,
    StockOrder,
    UnsupportedOperation,
)


class MoomooOptionsBrokerTests(unittest.TestCase):
    def test_dry_run_order_does_not_require_sdk(self) -> None:
        broker = MoomooOptionsBroker()
        result = broker.place_option_order(
            OptionOrder(
                symbol="AAPL",
                contract_code="US.AAPL240621C200000",
                side="BUY",
                quantity=1,
                limit_price=1.25,
            )
        )

        self.assertTrue(result.accepted)
        self.assertTrue(result.dry_run)
        self.assertIn("DRY RUN", result.message)
        self.assertEqual(result.broker, "moomoo")

    def test_capabilities(self) -> None:
        caps = MoomooOptionsBroker().capabilities

        self.assertTrue(caps.options_chain)
        self.assertTrue(caps.options_quotes)
        self.assertTrue(caps.options_orders)
        self.assertTrue(caps.paper_trading)
        self.assertFalse(caps.multi_leg_options)

    def test_default_market_is_us(self) -> None:
        self.assertEqual(MoomooConfig().market, "US")


class CliTests(unittest.TestCase):
    def test_dry_run_order_command_does_not_require_sdk(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "order",
                "--broker",
                "moomoo",
                "--type",
                "option",
                "--dry-run",
                "--symbol",
                "AAPL",
                "--contract",
                "US.AAPL240621C200000",
                "--side",
                "buy",
                "--qty",
                "1",
                "--limit",
                "1.25",
            ]
        )

        result = run_command(args)

        self.assertTrue(result.dry_run)
        self.assertTrue(result.accepted)

    def test_order_requires_dry_run_or_submit(self) -> None:
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "order",
                    "--broker",
                    "moomoo",
                    "--type",
                    "option",
                    "--symbol",
                    "AAPL",
                    "--contract",
                    "US.AAPL240621C200000",
                    "--side",
                    "buy",
                    "--qty",
                    "1",
                    "--limit",
                    "1.25",
                ]
            )

    def test_option_order_requires_contract(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "order",
                "--type",
                "option",
                "--dry-run",
                "--symbol",
                "AAPL",
                "--side",
                "buy",
                "--qty",
                "1",
                "--limit",
                "1.25",
            ]
        )

        with self.assertRaises(SystemExit):
            run_command(args)

    def test_stock_orders_are_not_implemented(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "order",
                "--type",
                "stock",
                "--dry-run",
                "--symbol",
                "AAPL",
                "--side",
                "buy",
                "--qty",
                "1",
                "--limit",
                "200",
            ]
        )

        with self.assertRaises(UnsupportedOperation):
            run_command(args)


class RobinhoodMcpBrokerTests(unittest.TestCase):
    def test_stock_dry_run_does_not_require_mcp(self) -> None:
        broker = RobinhoodMcpBroker()
        result = broker.place_stock_order(
            StockOrder(
                symbol="AAPL",
                side="BUY",
                quantity=1,
                limit_price=200,
            )
        )

        self.assertTrue(result.accepted)
        self.assertTrue(result.dry_run)
        self.assertEqual(result.broker, "robinhood")

    def test_options_are_not_supported(self) -> None:
        broker = RobinhoodMcpBroker()

        with self.assertRaises(UnsupportedOperation):
            broker.place_option_order(
                OptionOrder(
                    symbol="AAPL",
                    contract_code="AAPL 240621C200",
                    side="BUY",
                    quantity=1,
                    limit_price=1.25,
                )
            )

    def test_capabilities(self) -> None:
        caps = RobinhoodMcpBroker().capabilities

        self.assertFalse(caps.options_orders)
        self.assertFalse(caps.options_chain)
        self.assertTrue(caps.equity_orders)

    def test_cli_supports_robinhood_stock_dry_run(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "order",
                "--broker",
                "robinhood",
                "--type",
                "stock",
                "--dry-run",
                "--symbol",
                "AAPL",
                "--side",
                "buy",
                "--qty",
                "1",
                "--limit",
                "200",
            ]
        )

        result = run_command(args)

        self.assertTrue(result.accepted)
        self.assertTrue(result.dry_run)

    def test_robinhood_submit_requires_live_account(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "order",
                "--broker",
                "robinhood",
                "--type",
                "stock",
                "--submit",
                "--symbol",
                "AAPL",
                "--side",
                "buy",
                "--qty",
                "1",
                "--limit",
                "200",
            ]
        )

        with self.assertRaises(UnsupportedOperation):
            run_command(args)


if __name__ == "__main__":
    unittest.main()
