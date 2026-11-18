"""
RouteAudit - model prices from OpenRouter's public models list (no API key needed).

Prices come back as strings in USD *per token*, e.g. "0.0000004" = $0.40 per 1M tokens.

Try it:
    python scripts/pricing.py openai/gpt-4.1-mini
"""

import sys

import httpx

MODELS_URL = "https://openrouter.ai/api/v1/models"

_prices = None  # filled on first use, so we only download the list once per run


def _load_prices():
    global _prices
    if _prices is None:
        response = httpx.get(MODELS_URL, timeout=30)
        response.raise_for_status()
        _prices = {m["id"]: m.get("pricing") or {} for m in response.json()["data"]}
    return _prices


def get_price(model_id: str) -> dict:
    """
    Returns {"prompt": ..., "completion": ..., "cache_read": ...} as floats (USD per token).

    Free models cost $0, which makes every cost $0. So for a ":free" model we also
    return the price of its paid version (if OpenRouter has one), as "what it would
    cost a paying customer". If nothing is found, all prices are 0.0.
    """
    prices = _load_prices()

    pricing = prices.get(model_id, {})
    if model_id.endswith(":free"):
        paid_id = model_id.removesuffix(":free")
        if paid_id in prices:
            pricing = prices[paid_id]

    def to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    prompt = to_float(pricing.get("prompt"))
    cache_read = pricing.get("input_cache_read")
    return {
        "prompt": prompt,
        "completion": to_float(pricing.get("completion")),
        # If a model publishes no cache price, assume no discount (cache read = full price).
        "cache_read": to_float(cache_read) if cache_read is not None else prompt,
    }


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "openai/gpt-4.1-mini"
    p = get_price(model)
    print(model)
    for name, per_token in p.items():
        print(f"  {name:<11} ${per_token * 1_000_000:.4f} per 1M tokens")