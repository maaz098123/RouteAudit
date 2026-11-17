"""
Sends one chat request through YOUR proxy (not directly to the router).
If Day 1 works, you'll see the model's answer printed.

Run it (while the proxy is running in another terminal):
    python scripts/test_call.py
"""

import httpx

PROXY_URL = "http://localhost:8001/v1/chat/completions"

payload = {
    # A free model on OpenRouter. Change it if this one is unavailable.
    "model": "dots-studio/dots-3-note-preview:free",
    "messages": [{"role": "user", "content": "Say hello in exactly five words."}],
}

response = httpx.post(PROXY_URL, json=payload, timeout=60)

print("Status:", response.status_code)
data = response.json()

if response.status_code == 200:
    print("Model used:", data.get("model"))
    print("Answer:", data["choices"][0]["message"]["content"])
    print("Tokens:", data.get("usage"))
else:
    print("Error from router:", data)