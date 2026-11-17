"""
RouteAudit - Day 2: the database.

Every call that goes through the proxy is saved as one row in the "calls" table,
in a single file called routeaudit.db. Column design by Maaz.
"""

import sqlite3

DB_PATH = "routeaudit.db"

CREATE_CALLS_TABLE = """
CREATE TABLE IF NOT EXISTS calls (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp          TEXT NOT NULL,      -- when the call happened, e.g. 2026-11-17T14:19:00
    router             TEXT NOT NULL,      -- "openrouter", "tokenless", ...
    session_id         TEXT,               -- groups the turns of one conversation
    caller_id          TEXT,               -- which app/user sent it
    requested_model    TEXT,               -- what the app asked for, e.g. openrouter/auto
    model_used         TEXT,               -- what the router actually picked
    status_code        INTEGER,            -- 200, 404, 429, ...
    duration_ms        INTEGER,            -- how long the call took
    prompt_tokens      INTEGER,
    completion_tokens  INTEGER,
    cached_tokens      INTEGER,            -- cache-break detector watches this
    reasoning_tokens   INTEGER,            -- hidden "thinking" tokens
    cost_usd           REAL,               -- REAL, so $0.0015 isn't saved as 0
    prompt_hash        TEXT,               -- fingerprint of the question, to detect retries
    request_body       TEXT,               -- full JSON sent (for shadow sampling later)
    response_body      TEXT,               -- full JSON received
    error_message      TEXT                -- why it failed, if it did
);
"""


def init_db():
    """Create the database file and the calls table if they don't exist yet."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(CREATE_CALLS_TABLE)


def save_call(row: dict):
    """
    Save one call. `row` is a dict whose keys are column names, e.g.
    {"timestamp": "...", "router": "openrouter", "model_used": "...", ...}
    Columns you leave out are stored as empty (NULL).
    """
    columns = ", ".join(row.keys())
    placeholders = ", ".join("?" for _ in row)   # "?" keeps it safe from SQL injection
    sql = f"INSERT INTO calls ({columns}) VALUES ({placeholders})"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(sql, list(row.values()))