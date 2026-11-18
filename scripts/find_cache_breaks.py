import sqlite3
import sys

session_id = sys.argv[1]
conn = sqlite3.connect("routeaudit.db")
turns = conn.execute(
    "SELECT model_used, cached_tokens FROM calls WHERE session_id = ? ORDER BY id ASC",
    (session_id,),
).fetchall()

for i in range(1, len(turns)):          # start at turn 2, compare with the turn before
    prev_model, prev_cached = turns[i - 1]
    model, cached = turns[i]
    prev_cached = prev_cached or 0      # treat empty as 0
    cached = cached or 0

    # TODO 1: write the if-condition: model different AND cached lower
    if prev_model != model and cached < prev_cached:
        tokens_lost = prev_cached - cached
        print(f"CACHE BREAK at turn {i + 1}: {prev_model} -> {model}, lost {tokens_lost} cached tokens")