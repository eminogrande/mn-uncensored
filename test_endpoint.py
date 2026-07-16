from __future__ import annotations

import subprocess

from openai import OpenAI

from mn_uncensored.settings import load_settings


def owner_token() -> str:
    result = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-s",
            "mn-uncensored-owner-token",
            "-w",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


settings = load_settings()
if not settings.api_base_url:
    raise SystemExit("The gateway URL has not been configured.")
client = OpenAI(
    base_url=settings.api_base_url,
    api_key=owner_token(),
    timeout=60 * 60,
    max_retries=0,
)

stream = client.chat.completions.create(
    model=settings.model,
    messages=[
        {
            "role": "user",
            "content": "Reply with one short sentence confirming that you are online.",
        }
    ],
    max_tokens=80,
    stream=True,
)

for chunk in stream:
    text = chunk.choices[0].delta.content
    if text:
        print(text, end="", flush=True)
print()
