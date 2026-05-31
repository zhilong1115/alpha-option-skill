"""SQLite schema for the local Alpha data store."""

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS data_sources (
    name TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS equity_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    bid REAL,
    ask REAL,
    last REAL,
    volume REAL,
    raw_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_equity_quotes_symbol_time
ON equity_quotes(symbol, observed_at DESC);

CREATE TABLE IF NOT EXISTS option_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    contract_code TEXT NOT NULL,
    underlying TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    expiration_date TEXT,
    strike_price REAL,
    option_type TEXT,
    raw_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_option_contracts_unique
ON option_contracts(source, contract_code, observed_at);

CREATE TABLE IF NOT EXISTS option_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    contract_code TEXT NOT NULL,
    underlying TEXT,
    observed_at TEXT NOT NULL,
    bid REAL,
    ask REAL,
    last REAL,
    volume REAL,
    open_interest REAL,
    implied_volatility REAL,
    delta REAL,
    gamma REAL,
    theta REAL,
    vega REAL,
    raw_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_option_quotes_contract_time
ON option_quotes(contract_code, observed_at DESC);

CREATE TABLE IF NOT EXISTS sync_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    ok INTEGER NOT NULL,
    message TEXT NOT NULL,
    equity_quotes INTEGER NOT NULL DEFAULT 0,
    option_contracts INTEGER NOT NULL DEFAULT 0,
    option_quotes INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_quality_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    severity TEXT NOT NULL,
    source TEXT NOT NULL,
    symbol TEXT,
    message TEXT NOT NULL,
    raw_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""
