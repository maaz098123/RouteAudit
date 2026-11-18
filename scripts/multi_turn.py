"""
RouteAudit - Day 3: multi-turn cache test.

Sends a 4-turn conversation through the proxy, all with the same session ID.
Each turn re-sends the whole conversation so far (that's how chat APIs work),
so the shared beginning should get CACHED from turn 2 onwards.

Watch cached_tokens turn by turn:
  - it should go UP on turns 2, 3, 4  -> cache working
  - if it drops back to 0 on a turn  -> cache break (e.g. the router switched model)

Run it (proxy running in another terminal):
    python scripts/multi_turn.py
"""

import uuid

import httpx

PROXY_URL = "http://localhost:8001/v1/chat/completions"

# Put the same model you used in test_call.py here.
MODEL = "dots-studio/dots-3-note-preview:free"

# Providers only cache long prompts (OpenAI: 1024+ tokens), so we start the
# conversation with a long system prompt. ~1500 tokens of repeated text.
LONG_SYSTEM_PROMPT = (
    "You are a helpful assistant for a small online bookshop. "
    "Answer briefly, in one or two sentences. "
    + "Store policy: orders ship within two business days, returns are accepted "
      "within thirty days with a receipt, and gift wrapping is free on request. " * 60
)

QUESTIONS = [
    "How long does shipping take?",
    "Can I return a book after three weeks?",
    "Is gift wrapping extra?",
    "Summarise the three policies in one line.",
]

session_id = f"test-{uuid.uuid4().hex[:8]}"
headers = {"x-session-id": session_id}
messages = [{"role": "system", "content": LONG_SYSTEM_PROMPT}]

print(f"Session: {session_id}\n")

for turn, question in enumerate(QUESTIONS, start=1):
    messages.append({"role": "user", "content": question})
     
    if turn <= 2:
        model = MODEL
    else:
        model = "nvidia/nemotron-3.5-lightning:free"
    response = httpx.post(
        PROXY_URL,
        json={"model": model, "messages": messages},
        headers=headers,
        timeout=120,
    )
    data = response.json()

    if response.status_code != 200:
        print(f"Turn {turn}: error {response.status_code}: {data}")
        break

    answer = data["choices"][0]["message"]["content"]
    usage = data.get("usage") or {}
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens")

    print(
        f"Turn {turn} | model {data.get('model')} | "
        f"prompt {usage.get('prompt_tokens')} | cached {cached}"
    )
    print(f"   Q: {question}")
    print(f"   A: {answer.strip()[:120]}\n")

    # Add the answer to the conversation so the next turn includes it.
    messages.append({"role": "assistant", "content": answer})

print(f"Done. Look at this session in the database with session_id = '{session_id}'")


