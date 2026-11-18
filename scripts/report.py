"""
RouteAudit - one-screen report across the whole database.

Checks every session for cache breaks (using Maaz's rule) and prints totals,
plus a breakdown of which model switches caused the most waste.

Run it from inside the routeaudit/ folder:
    python scripts/report.py
"""

import sqlite3
from collections import defaultdict

from pricing import get_price

DB_PATH = "routeaudit.db"


def find_cache_breaks(turns):
    """
    turns = list of (model_used, cached_tokens) for one session, oldest first.
    Returns a list of breaks: (turn_number, prev_model, model, tokens_lost, extra_cost).

    Rule (written by Maaz): the model is different from the previous turn
    AND cached tokens dropped -> cache break.
    """
    breaks = []
    for i in range(1, len(turns)):
        prev_model, prev_cached = turns[i - 1]
        model, cached = turns[i]
        prev_cached = prev_cached or 0
        cached = cached or 0

        if prev_model != model and cached < prev_cached:
            tokens_lost = prev_cached - cached
            price = get_price(model)
            extra_cost = tokens_lost * (price["prompt"] - price["cache_read"])
            breaks.append((i + 1, prev_model, model, tokens_lost, extra_cost))
    return breaks


def main():
    conn = sqlite3.connect(DB_PATH)

    # --- Overall numbers -------------------------------------------------------
    total_calls, failed_calls, total_cost = conn.execute(
        """
        SELECT COUNT(*),
               SUM(CASE WHEN status_code != 200 THEN 1 ELSE 0 END),
               SUM(COALESCE(cost_usd, 0))
        FROM calls
        """
    ).fetchone()

    # Usage sanity check: reasoning tokens are part of completion tokens,
    # so reasoning > completion is impossible -> the reported numbers don't add up.
    impossible = conn.execute(
        "SELECT COUNT(*) FROM calls WHERE reasoning_tokens > completion_tokens"
    ).fetchone()[0]

    if not total_calls:
        print("No calls in the database yet. Run scripts/test_call.py or multi_turn.py first.")
        return

    session_ids = [
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT session_id FROM calls WHERE session_id IS NOT NULL"
        )
    ]

    # --- Cache breaks across every session ------------------------------------
    sessions_with_breaks = 0
    total_breaks = 0
    total_tokens_lost = 0
    total_extra_cost = 0.0
    by_switch = defaultdict(lambda: {"count": 0, "tokens": 0, "cost": 0.0})

    for session_id in session_ids:
        turns = conn.execute(
            """
            SELECT model_used, cached_tokens FROM calls
            WHERE session_id = ? AND status_code = 200
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()

        breaks = find_cache_breaks(turns)
        if breaks:
            sessions_with_breaks += 1
        for _turn, prev_model, model, tokens_lost, extra_cost in breaks:
            total_breaks += 1
            total_tokens_lost += tokens_lost
            total_extra_cost += extra_cost
            switch = by_switch[(prev_model, model)]
            switch["count"] += 1
            switch["tokens"] += tokens_lost
            switch["cost"] += extra_cost

    # --- Print the report ------------------------------------------------------
    line = "=" * 64
    print(line)
    print("  ROUTEAUDIT REPORT")
    print(line)
    print(f"  Calls logged            {total_calls}")
    print(f"  Failed calls            {failed_calls or 0}")
    print(f"  Impossible usage rows   {impossible}   (reasoning > completion)")
    print(f"  Reported spend          ${total_cost or 0:.6f}")
    print(f"  Conversations           {len(session_ids)}")
    print()
    print("  CACHE BREAKS")
    print(f"  Sessions with a break   {sessions_with_breaks} of {len(session_ids)}")
    print(f"  Total cache breaks      {total_breaks}")
    print(f"  Cached tokens lost      {total_tokens_lost}")
    print(f"  Extra cost              ${total_extra_cost:.6f}")

    if by_switch:
        print()
        print("  WORST MODEL SWITCHES (by extra cost)")
        ranked = sorted(by_switch.items(), key=lambda item: item[1]["cost"], reverse=True)
        for (prev_model, model), s in ranked:
            print(f"  {prev_model} -> {model}")
            print(f"      {s['count']} break(s), {s['tokens']} tokens lost, ${s['cost']:.6f} extra")
    print(line)


if __name__ == "__main__":
    main()