"""Market data source adapters for moomoo and Polygon."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable

from alpha_option_skill.brokers import BrokerError, MoomooOptionsBroker
from alpha_option_skill.data.records import (
    DataSyncResult,
    EquityQuote,
    OptionContract,
    OptionQuote,
    utc_now_iso,
)
from alpha_option_skill.data.store import AlphaDataStore


def _first_present(row: dict[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        value = row.get(name)
        if value not in (None, "", "N/A"):
            return value
    return None


def _to_float(value: Any) -> float | None:
    if value in (None, "", "N/A"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _rows(value: Any) -> list[dict[str, Any]]:
    if hasattr(value, "to_dict"):
        return list(value.to_dict(orient="records"))
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


class MoomooDataSource:
    name = "moomoo"

    def __init__(self, broker: MoomooOptionsBroker) -> None:
        self.broker = broker

    def sync(
        self,
        store: AlphaDataStore,
        symbols: list[str],
        option_contracts: list[str],
        include_option_chains: bool = False,
    ) -> DataSyncResult:
        equity_records: list[EquityQuote] = []
        option_quotes: list[OptionQuote] = []
        option_contract_records: list[OptionContract] = []

        for symbol in symbols:
            snapshot = self._snapshot(symbol)
            equity_records.extend(self._equity_quotes(symbol, snapshot))
            if include_option_chains:
                chain = self.broker.option_chain(symbol)
                option_contract_records.extend(self._option_contracts(symbol, chain))

        for contract in option_contracts:
            snapshot = self.broker.option_quote(contract)
            option_quotes.extend(self._option_quotes(contract, snapshot))

        eq_count = store.insert_equity_quotes(equity_records)
        contract_count = store.insert_option_contracts(option_contract_records)
        opt_count = store.insert_option_quotes(option_quotes)
        return DataSyncResult(
            source=self.name,
            ok=True,
            equity_quotes=eq_count,
            option_contracts=contract_count,
            option_quotes=opt_count,
            message="moomoo sync complete",
        )

    def _snapshot(self, symbol: str) -> Any:
        with self.broker.quote_context() as ctx:
            ret, data = ctx.get_market_snapshot([symbol])
            return self.broker._call_ok(ret, data, "equity snapshot query")

    def _equity_quotes(self, symbol: str, snapshot: Any) -> list[EquityQuote]:
        observed_at = utc_now_iso()
        records: list[EquityQuote] = []
        for row in _rows(snapshot):
            records.append(
                EquityQuote(
                    source=self.name,
                    symbol=str(_first_present(row, ["code", "symbol"]) or symbol),
                    observed_at=observed_at,
                    bid=_to_float(_first_present(row, ["bid_price", "bid"])),
                    ask=_to_float(_first_present(row, ["ask_price", "ask"])),
                    last=_to_float(_first_present(row, ["last_price", "nominal_price", "price"])),
                    volume=_to_float(_first_present(row, ["volume"])),
                    raw=row,
                )
            )
        return records

    def _option_contracts(self, symbol: str, chain: Any) -> list[OptionContract]:
        observed_at = utc_now_iso()
        records: list[OptionContract] = []
        for row in _rows(chain):
            contract_code = _first_present(row, ["code", "contract_code", "symbol"])
            if not contract_code:
                continue
            records.append(
                OptionContract(
                    source=self.name,
                    contract_code=str(contract_code),
                    underlying=symbol,
                    observed_at=observed_at,
                    expiration_date=_first_present(row, ["expiration_date", "expiry", "exp_date"]),
                    strike_price=_to_float(_first_present(row, ["strike_price", "strike"])),
                    option_type=_first_present(row, ["option_type", "type"]),
                    raw=row,
                )
            )
        return records

    def _option_quotes(self, contract: str, snapshot: Any) -> list[OptionQuote]:
        observed_at = utc_now_iso()
        records: list[OptionQuote] = []
        for row in _rows(snapshot):
            records.append(
                OptionQuote(
                    source=self.name,
                    contract_code=str(_first_present(row, ["code", "contract_code"]) or contract),
                    underlying=_first_present(row, ["stock_owner", "underlying", "underlying_symbol"]),
                    observed_at=observed_at,
                    bid=_to_float(_first_present(row, ["bid_price", "bid"])),
                    ask=_to_float(_first_present(row, ["ask_price", "ask"])),
                    last=_to_float(_first_present(row, ["last_price", "nominal_price", "price"])),
                    volume=_to_float(_first_present(row, ["volume"])),
                    open_interest=_to_float(_first_present(row, ["open_interest"])),
                    implied_volatility=_to_float(_first_present(row, ["implied_volatility", "iv"])),
                    delta=_to_float(_first_present(row, ["delta"])),
                    gamma=_to_float(_first_present(row, ["gamma"])),
                    theta=_to_float(_first_present(row, ["theta"])),
                    vega=_to_float(_first_present(row, ["vega"])),
                    raw=row,
                )
            )
        return records


@dataclass(frozen=True)
class PolygonConfig:
    api_key: str | None = None
    base_url: str = "https://api.polygon.io"

    @classmethod
    def from_env(cls) -> "PolygonConfig":
        return cls(api_key=os.getenv("POLYGON_API_KEY"))


class PolygonDataSource:
    name = "polygon"

    def __init__(self, config: PolygonConfig | None = None) -> None:
        self.config = config or PolygonConfig.from_env()

    def sync(
        self,
        store: AlphaDataStore,
        symbols: list[str],
        option_contracts: list[str],
        include_option_chains: bool = False,
    ) -> DataSyncResult:
        if not self.config.api_key:
            return DataSyncResult(
                source=self.name,
                ok=False,
                message="POLYGON_API_KEY is not set; skipped polygon sync",
            )

        equity_records = [self._equity_snapshot(symbol) for symbol in symbols]
        option_records = [self._option_snapshot(contract) for contract in option_contracts]
        eq_count = store.insert_equity_quotes([row for row in equity_records if row])
        opt_count = store.insert_option_quotes([row for row in option_records if row])
        return DataSyncResult(
            source=self.name,
            ok=True,
            equity_quotes=eq_count,
            option_quotes=opt_count,
            message="polygon sync complete",
        )

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = {"apiKey": self.config.api_key, **(params or {})}
        url = f"{self.config.base_url}{path}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise BrokerError(f"polygon request failed: {exc}") from exc

    def _equity_snapshot(self, symbol: str) -> EquityQuote | None:
        ticker_symbol = self._ticker_symbol(symbol)
        data = self._get_json(f"/v2/snapshot/locale/us/markets/stocks/tickers/{ticker_symbol}")
        ticker = data.get("ticker") or {}
        last_trade = ticker.get("lastTrade") or {}
        last_quote = ticker.get("lastQuote") or {}
        day = ticker.get("day") or {}
        return EquityQuote(
            source=self.name,
            symbol=ticker_symbol,
            bid=_to_float(last_quote.get("p")),
            ask=_to_float(last_quote.get("P")),
            last=_to_float(last_trade.get("p") or day.get("c")),
            volume=_to_float(day.get("v")),
            raw=data,
        )

    def _option_snapshot(self, contract: str) -> OptionQuote | None:
        underlying = self._option_underlying(contract)
        path_contract = urllib.parse.quote(contract, safe="")
        data = self._get_json(f"/v3/snapshot/options/{underlying}/{path_contract}")
        result = data.get("results") or {}
        details = result.get("details") or {}
        greeks = result.get("greeks") or {}
        last_quote = result.get("last_quote") or {}
        last_trade = result.get("last_trade") or {}
        return OptionQuote(
            source=self.name,
            contract_code=contract,
            underlying=details.get("underlying_ticker"),
            bid=_to_float(last_quote.get("bid")),
            ask=_to_float(last_quote.get("ask")),
            last=_to_float(last_trade.get("price")),
            open_interest=_to_float(result.get("open_interest")),
            implied_volatility=_to_float(result.get("implied_volatility")),
            delta=_to_float(greeks.get("delta")),
            gamma=_to_float(greeks.get("gamma")),
            theta=_to_float(greeks.get("theta")),
            vega=_to_float(greeks.get("vega")),
            raw=data,
        )

    def _ticker_symbol(self, symbol: str) -> str:
        return symbol.split(".")[-1].upper()

    def _option_underlying(self, contract: str) -> str:
        ticker = contract[2:] if contract.startswith("O:") else contract
        chars = []
        for char in ticker:
            if char.isdigit():
                break
            chars.append(char)
        if not chars:
            raise BrokerError(f"cannot infer Polygon option underlying from contract: {contract}")
        return "".join(chars).upper()
