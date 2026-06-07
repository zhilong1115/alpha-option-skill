# alpha-option-skill

Alpha options trading skill research, trade planning, and broker connector scaffolding.

AI agents should read [`SKILL.md`](SKILL.md) for the operational workflow,
authentication routing, privacy requirements, and live-order safety rules.
Codex-compatible agents can discover it through `AGENTS.md`; Claude Code can
discover it through `CLAUDE.md`.

## Broker Status

- Moomoo: primary options connector. The first implementation supports account, positions, option chain, option quote, order list, and single-leg option order submission through the official Moomoo OpenAPI SDK. Dry-run order planning works without installing the SDK.
- Robinhood MCP: supports the official Agentic Trading MCP path for account, positions, orders, and stock order submission. Current public MCP support is long-equities only; options chain and options order methods intentionally raise `UnsupportedOperation`.
- Robinhood account access is rolling out. If the OAuth page shows `Coming soon: Agentic trading`, the account is not enabled yet and live MCP reads/orders cannot run until Robinhood grants access.

## Safety Defaults

- `OptionOrder.dry_run` defaults to `True`.
- Dry-run Moomoo orders never import the SDK, connect to OpenD, unlock trading, or submit live orders.
- Live Moomoo orders require `dry_run=False`, the optional `moomoo-api` SDK, a running Moomoo OpenD process, and any live-trading unlock flow outside this connector.
- Robinhood orders go through the official MCP endpoint and require OAuth through `mcporter`; dry-run stock orders do not call MCP.
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

Robinhood MCP auth:

```bash
mcporter auth https://agent.robinhood.com/mcp/trading
```

Default OpenD connection values:

- host: `127.0.0.1`
- port: `11111`
- account: `paper` maps to Moomoo `SIMULATE`; `live` maps to Moomoo `REAL`
- currency: `USD` by default; use `--currency HKD` when an HKD view is needed

## Data Layer

The local data layer is a lightweight SQLite store for Alpha's market snapshots,
option snapshots, sync history, and future strategy audit trail. It is not meant
to copy an entire vendor warehouse. It stores the data Alpha actually used, so
future decisions can be audited and compared across data sources.

Default data sources:

- `moomoo`: primary broker/data source through local OpenD.
- `polygon`: secondary market-data source. Set `POLYGON_API_KEY` to enable live
  Polygon sync; without a key the source is recorded as skipped instead of
  breaking the command.

Initialize the local database:

```bash
alpha data init --db alpha.db
```

Check counts:

```bash
alpha data status --db alpha.db
```

Sync both configured sources:

```bash
alpha data --broker moomoo --account live sync \
  --db alpha.db \
  --sources moomoo,polygon \
  --symbols US.AAPL,US.NVDA \
  --contracts US.AAPL240621C200000
```

For a first pass, keep this as a light local fact store:

- stock snapshots in `equity_quotes`
- option contract metadata in `option_contracts`
- option snapshots/Greeks in `option_quotes`
- sync audit rows in `sync_runs`

## CLI

Run from the repo:

```bash
alpha positions --broker moomoo --account live
alpha account --broker moomoo --account live
alpha orders --broker moomoo --account live
alpha quote --broker moomoo --type option --contract US.AAPL240621C200000
alpha chain --broker moomoo --type option --symbol US.AAPL
```

`--account` chooses the broker account environment. Use `--account paper` for Moomoo paper trading, and `--account live` for the live account.

Dry-run option order planning:

```bash
alpha order --broker moomoo --account paper \
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
alpha order --broker moomoo --account paper \
  --type option \
  --submit \
  --symbol AAPL \
  --contract US.AAPL240621C200000 \
  --side buy \
  --qty 1 \
  --limit 1.25
```

Submitted live orders use `--account live --submit`.

```bash
alpha order --broker moomoo --account live \
  --type option \
  --submit \
  --symbol AAPL \
  --contract US.AAPL240621C200000 \
  --side buy \
  --qty 1 \
  --limit 1.25
```

Robinhood stock dry-run:

```bash
alpha order --broker robinhood \
  --type stock \
  --dry-run \
  --symbol AAPL \
  --side buy \
  --qty 1 \
  --limit 200
```

Robinhood live account reads and stock submit:

```bash
alpha account --broker robinhood --account live
alpha account --broker robinhood --account live --account-number ACCOUNT_NUMBER
alpha positions --broker robinhood --account live --account-number ACCOUNT_NUMBER
alpha orders --broker robinhood --account live --account-number ACCOUNT_NUMBER
alpha order --broker robinhood --account live \
  --account-number ACCOUNT_NUMBER \
  --type stock \
  --submit \
  --symbol AAPL \
  --side buy \
  --qty 1 \
  --limit 200
```
