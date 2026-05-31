import unittest
from tempfile import TemporaryDirectory

from alpha_option_skill.cli import build_parser, run_command
from alpha_option_skill.brokers import (
    MoomooConfig,
    MoomooOptionsBroker,
    OptionOrder,
    RobinhoodMcpBroker,
    StockOrder,
    UnsupportedOperation,
)
from alpha_option_skill.data.records import EquityQuote, OptionQuote
from alpha_option_skill.data.sources import PolygonDataSource
from alpha_option_skill.data.store import AlphaDataStore


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


class DataLayerTests(unittest.TestCase):
    def test_store_initializes_and_records_quotes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = AlphaDataStore(f"{temp_dir}/alpha.db")
            store.init()

            equity_count = store.insert_equity_quotes(
                [
                    EquityQuote(
                        source="test",
                        symbol="US.AAPL",
                        bid=199.9,
                        ask=200.1,
                        last=200.0,
                        volume=1000,
                    )
                ]
            )
            option_count = store.insert_option_quotes(
                [
                    OptionQuote(
                        source="test",
                        contract_code="US.AAPL240621C200000",
                        underlying="US.AAPL",
                        bid=1.2,
                        ask=1.3,
                        implied_volatility=0.35,
                        delta=0.42,
                    )
                ]
            )

            self.assertEqual(equity_count, 1)
            self.assertEqual(option_count, 1)
            self.assertEqual(store.table_count("equity_quotes"), 1)
            self.assertEqual(store.table_count("option_quotes"), 1)

    def test_polygon_sync_skips_without_api_key(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = AlphaDataStore(f"{temp_dir}/alpha.db")
            store.init()

            result = PolygonDataSource().sync(store, ["AAPL"], [])

            self.assertFalse(result.ok)
            self.assertIn("POLYGON_API_KEY", result.message)

    def test_polygon_normalizes_us_symbols(self) -> None:
        source = PolygonDataSource()

        self.assertEqual(source._ticker_symbol("US.AAPL"), "AAPL")
        self.assertEqual(source._option_underlying("O:AAPL260717C00410000"), "AAPL")

    def test_cli_data_init_and_status(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/alpha.db"
            parser = build_parser()

            init_args = parser.parse_args(["data", "init", "--db", db_path])
            init_result = run_command(init_args)

            status_args = parser.parse_args(["data", "status", "--db", db_path])
            status_result = run_command(status_args)

            self.assertEqual(init_result["status"], "initialized")
            self.assertEqual(status_result["equity_quotes"], 0)
            self.assertEqual(status_result["option_quotes"], 0)


if __name__ == "__main__":
    unittest.main()
