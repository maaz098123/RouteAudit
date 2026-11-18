import sqlite3
import sys
from pricing import get_price

session_id = sys.argv[1]
conn = sqlite3.connect("routeaudit.db")
turns = conn.execute(
    "SELECT model_used, cached_tokens FROM calls WHERE session_id = ? ORDER BY id ASC",
    (session_id,),
).fetchall()

for i in range(1, len(turns)):
    prev_model, prev_cached = turns[i - 1]
    model, cached = turns[i]
    prev_cached = prev_cached or 0
    cached = cached or 0

    if prev_model != model and cached < prev_cached:
        tokens_lost = prev_cached - cached
        price = get_price(model)
        extra_cost = tokens_lost * (price["prompt"] - price["cache_read"])
        print(f"CACHE BREAK at turn {i + 1}: {prev_model} -> {model}, lost {tokens_lost} cached tokens ≈ ${extra_cost:.6f} extra")
        