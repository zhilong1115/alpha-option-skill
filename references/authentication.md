# Authentication and setup

## Moomoo

Requirements:

- Install the optional SDK: `python3 -m pip install -e ".[moomoo]"`.
- Install and launch Moomoo OpenD.
- Log in through Moomoo/OpenD.
- Default endpoint: `127.0.0.1:11111`.

Check the listener without exposing credentials:

```bash
lsof -nP -iTCP:11111 -sTCP:LISTEN
```

Verify with a read:

```bash
alpha account --broker moomoo --account live
```

Use `--account paper` for `SIMULATE` and `--account live` for `REAL`.
Account reporting defaults to USD. Add `--currency HKD` only when requested.

OpenD trading unlock, when required, must happen through the local broker
workflow. Do not store an unlock password in this repository or a command.

## Robinhood MCP

Requirements:

- Install `mcporter`.
- Complete OAuth:

```bash
mcporter auth https://agent.robinhood.com/mcp/trading
```

If browser approval times out, rerun the command when the user is ready.
Never inspect or print `~/.mcporter/credentials.json`.

List accounts:

```bash
alpha account --broker robinhood --account live
```

Use the account whose response has `agentic_allowed=true`. Pass its number only
at runtime:

```bash
alpha account --broker robinhood --account live \
  --account-number ACCOUNT_NUMBER
```

For a private local shell, the number may be supplied through
`ALPHA_ROBINHOOD_ACCOUNT_NUMBER`. Never put the value in Git-tracked files,
examples, tests, logs, reports, or chat messages unless explicitly necessary.

Robinhood OAuth permission does not itself authorize an order. Review the order
and obtain explicit confirmation immediately before each live submission.

## Polygon

Polygon is optional. Export `POLYGON_API_KEY` in the local environment. Never
write the real value into `.env.example`, source code, tests, or documentation.
If absent, Polygon sync is skipped without blocking Moomoo.

## Troubleshooting

- Moomoo connection refused: verify OpenD is running and port `11111` listens.
- Moomoo SDK missing: reinstall with the `moomoo` optional dependency.
- Robinhood OAuth required: rerun `mcporter auth` and complete browser approval.
- Robinhood unknown tool: inspect current tools with
  `mcporter list https://agent.robinhood.com/mcp/trading --schema`.
- Robinhood account rejected: verify the selected account is active and
  `agentic_allowed=true`.
