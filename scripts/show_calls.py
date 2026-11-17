"""
Shows the last 10 calls saved by the proxy.

Run it from inside the routeaudit/ folder:
    python scripts/show_calls.py
"""

import sqlite3

conn = sqlite3.connect("routeaudit.db")
rows = conn.execute(
    """
    SELECT id, timestamp, model_used, status_code, duration_ms,
           prompt_tokens, completion_tokens, cached_tokens, reasoning_tokens, cost_usd
    FROM calls
    ORDER BY id DESC
    LIMIT 10
    """
).fetchall()

if not rows:
    print("No calls saved yet. Run scripts/test_call.py first.")

for r in rows:
    print(
        f"#{r[0]} {r[1][:19]} | {r[2]} | status {r[3]} | {r[4]} ms | "
        f"prompt {r[5]} / completion {r[6]} / cached {r[7]} / reasoning {r[8]} | ${r[9]}"
    )