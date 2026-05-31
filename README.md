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
- account: `paper` maps to Moomoo `SIMULATE`; `live` maps to Moomoo `REAL`

## CLI

Run from the repo:

```bash
python3.11 -m alpha_option_skill positions --broker moomoo --account live
python3.11 -m alpha_option_skill account --broker moomoo --account live
python3.11 -m alpha_option_skill orders --broker moomoo --account live
python3.11 -m alpha_option_skill quote --broker moomoo --type option --contract US.AAPL240621C200000
python3.11 -m alpha_option_skill chain --broker moomoo --type option --symbol US.AAPL
```

`--account` chooses the broker account environment. Use `--account paper` for Moomoo paper trading, and `--account live` for the live account.

Dry-run option order planning:

```bash
python3.11 -m alpha_option_skill order --broker moomoo --account paper \
  --type option \
  --dry-run \
  --symbol AAPL \
  --contract US.AAPL240621C200000 \
  --side buy \
  --qty 1 \
  --limit 1.25
```

Submitted paper orders use `--submit`:

```bash
python3.11 -m alpha_option_skill order --broker moomoo --account paper \
  --type option \
  --submit \
  --symbol AAPL \
  --contract US.AAPL240621C200000 \
  --side buy \
  --qty 1 \
  --limit 1.25
```

Submitted real orders require both `--submit` and `--confirm-live-order`.

```bash
python3.11 -m alpha_option_skill order --broker moomoo --account live \
  --type option \
  --submit \
  --symbol AAPL \
  --contract US.AAPL240621C200000 \
  --side buy \
  --qty 1 \
  --limit 1.25 \
  --confirm-live-order
```
