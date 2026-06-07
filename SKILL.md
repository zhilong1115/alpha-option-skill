---
name: alpha-options-trading
description: "Research US stocks and options, query Moomoo or Robinhood accounts, inspect positions and orders, sync market data, plan trades, and submit supported orders through the alpha CLI."
---

# Alpha options trading

Use this repository's `alpha` CLI for broker and market-data work. Run commands
from the repository root. Read [references/authentication.md](references/authentication.md)
when setup, login, OAuth, account discovery, or connectivity is involved.

## Start

1. Check installation: `alpha --help` or `python3 -m alpha_option_skill --help`.
2. Install locally if needed: `python3 -m pip install -e ".[moomoo]"`.
3. Confirm the requested broker and whether the user means paper or live.
4. Establish authentication using the reference guide.
5. Run account and position reads before analysis or order preparation.

Never place a live order merely because authentication works. Present the exact
broker, account environment, symbol or contract, side, quantity, order type, and
price, then obtain explicit user confirmation immediately before `--submit`.
Authentication, general trading authorization, or an earlier confirmation is
not confirmation for a new live order.

## Read-only operations

Moomoo defaults to USD:

```bash
alpha account --broker moomoo --account live
alpha positions --broker moomoo --account live
alpha orders --broker moomoo --account live
alpha quote --broker moomoo --type option --contract CONTRACT_CODE
alpha chain --broker moomoo --type option --symbol US.AAPL
```

Robinhood:

```bash
alpha account --broker robinhood --account live
alpha account --broker robinhood --account live --account-number ACCOUNT_NUMBER
alpha positions --broker robinhood --account live --account-number ACCOUNT_NUMBER
alpha orders --broker robinhood --account live --account-number ACCOUNT_NUMBER
```

The first Robinhood account command lists available accounts. Select an
`agentic_allowed=true` account for MCP trading. If multiple accounts are
eligible or the user has not identified one, show sanitized choices and ask.
Do not persist an account number in tracked files.

## Market data

```bash
alpha data init --db alpha.db
alpha data status --db alpha.db
alpha data --broker moomoo --account live sync \
  --db alpha.db \
  --sources moomoo,polygon \
  --symbols US.AAPL,US.NVDA \
  --contracts CONTRACT_CODE
```

`alpha.db` is local and ignored by Git. Polygon is optional and reads
`POLYGON_API_KEY` from the environment.

## Orders

Always dry-run first:

```bash
alpha order --broker moomoo --account paper \
  --type option --dry-run \
  --symbol AAPL --contract CONTRACT_CODE \
  --side buy --qty 1 --limit 1.25

alpha order --broker robinhood \
  --type stock --dry-run \
  --symbol AAPL --side buy --qty 1 --limit 200
```

After presenting the dry-run and receiving explicit confirmation, submit with
the same reviewed values:

```bash
alpha order --broker moomoo --account live \
  --type option --submit \
  --symbol AAPL --contract CONTRACT_CODE \
  --side buy --qty 1 --limit 1.25

alpha order --broker robinhood --account live \
  --account-number ACCOUNT_NUMBER \
  --type stock --submit \
  --symbol AAPL --side buy --qty 1 --limit 200
```

Current limits:

- Moomoo: single-leg option orders; no atomic multi-leg spreads.
- Robinhood MCP: equity orders only through this CLI; no option orders.
- Never imply unsupported functionality succeeded.

## Privacy

- Never commit account numbers, balances, positions, order history, OAuth data,
  API keys, credentials, local databases, or generated account reports.
- Keep secrets in broker apps, MCP credential storage, or environment variables.
- Before every push, inspect `git diff --cached` and scan tracked content for
  credentials and personal data.
- Report financial values to the user, but redact account numbers unless the
  user specifically needs to distinguish accounts.
- Do not print tokens or credential-file contents while diagnosing auth.

## Verification

After code changes:

```bash
python3 -m unittest discover -s tests
git diff --check
```

For broker checks, prefer read-only account and position calls. State clearly
which calls were live reads and whether any order was submitted.
