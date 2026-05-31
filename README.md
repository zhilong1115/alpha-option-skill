# alpha-option-skill

Alpha options trading skill research, trade planning, and broker connector scaffolding.

## Broker Status

- Moomoo: primary options connector. The first implementation supports account, positions, option chain, option quote, order list, and single-leg option order submission through the official Moomoo OpenAPI SDK. Dry-run order planning works without installing the SDK.
- Robinhood MCP: tracked as a future connector, but current official Trading MCP support is long-equities only. Options chain and options order methods intentionally raise `UnsupportedOperation`.

## Safety Defaults

- `OptionOrder.dry_run` defaults to `True`.
- Dry-run Moomoo orders never import the SDK, connect to OpenD, unlock trading, or submit live orders.
- Live Moomoo orders require `dry_run=False`, the optional `moomoo-api` SDK, a running Moomoo OpenD process, and any live-trading unlock flow outside this connector.
- Multi-leg option orders are not marked supported until we confirm an atomic spread-order API.

## Development

```bash
python3 -m unittest discover -s tests
```

Optional Moomoo SDK install:

```bash
python3 -m pip install -e ".[moomoo]"
```

The official PyPI package is `moomoo-api`; it imports as `moomoo` in Python.

Default OpenD connection values:

- host: `127.0.0.1`
- port: `11111`
- trade env: `SIMULATE`

## CLI

Run from the repo:

```bash
python3.11 -m alpha_option_skill --broker moomoo --env real positions
python3.11 -m alpha_option_skill --broker moomoo --env real account
python3.11 -m alpha_option_skill --broker moomoo --env real orders
python3.11 -m alpha_option_skill --broker moomoo option-quote US.AAPL240621C200000
python3.11 -m alpha_option_skill --broker moomoo option-chain US.AAPL
```

Dry-run option order planning:

```bash
python3.11 -m alpha_option_skill --broker moomoo place-option-order \
  --symbol AAPL \
  --contract-code US.AAPL240621C200000 \
  --side BUY \
  --qty 1 \
  --limit 1.25
```

Non-dry-run real orders require both `--no-dry-run` and `--confirm-live-order`.

```bash
python3.11 -m alpha_option_skill --broker moomoo --env real place-option-order \
  --symbol AAPL \
  --contract-code US.AAPL240621C200000 \
  --side BUY \
  --qty 1 \
  --limit 1.25 \
  --no-dry-run \
  --confirm-live-order
```
