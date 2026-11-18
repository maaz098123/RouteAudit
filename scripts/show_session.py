"""
Shows every turn of ONE conversation, in order.

Run it from inside the routeaudit/ folder:
    python scripts/show_session.py test-5191bc43
"""

import sqlite3
import sys

if len(sys.argv) < 2:
    raise SystemExit("Usage: python scripts/show_session.py <session_id>")

session_id = sys.argv[1]  # the session ID you type after the script name

conn = sqlite3.connect("routeaudit.db")
rows = conn.execute(
    """
    SELECT id, model_used, prompt_tokens, cached_tokens, cost_usd
    FROM calls
    WHERE session_id = ?   -- only this conversation
    ORDER BY id ASC        -- oldest first, so turns are in order
    """,
    (session_id,),
).fetchall()

if not rows:
    print(f"No calls found for session '{session_id}'.")

for turn, r in enumerate(rows, start=1):
    print(f"Turn {turn} | call #{r[0]} | {r[1]} | prompt {r[2]} | cached {r[3]} | ${r[4]}")