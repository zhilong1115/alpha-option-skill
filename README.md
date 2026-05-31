# alpha-option-skill

Alpha options trading skill research, trade planning, and broker connector scaffolding.

## Broker Status

- Moomoo: primary options connector. The first implementation supports account, positions, option chain, option quote, order list, and single-leg option order submission through the official Moomoo OpenAPI SDK. Dry-run order planning works without installing the SDK.
- Robinhood MCP: tracked as a future connector, but current official Trading MCP support is long-equities only. Options chain and options order methods intentionally raise `UnsupportedOperation`.

## Safety Defaults

- `OptionOrder.dry_run` defaults to `True`.
- Dry-run Moomoo orders never import the SDK, connect to OpenD, unlock trading, or submit live orders.
- Live Moomoo orders require `dry_run=False`, the optional `moomoo` SDK, a running Moomoo OpenD process, and any live-trading unlock flow outside this connector.
- Multi-leg option orders are not marked supported until we confirm an atomic spread-order API.

## Development

```bash
python3 -m unittest discover -s tests
```

Optional Moomoo SDK install:

```bash
python3 -m pip install -e ".[moomoo]"
```

Default OpenD connection values:

- host: `127.0.0.1`
- port: `11111`
- trade env: `SIMULATE`
