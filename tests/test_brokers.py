import unittest

from alpha_option_skill.brokers import (
    MoomooOptionsBroker,
    OptionOrder,
    RobinhoodMcpBroker,
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


class RobinhoodMcpBrokerTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
