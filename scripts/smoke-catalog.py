from __future__ import annotations

import argparse
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
parser = argparse.ArgumentParser()
parser.add_argument("model")
args = parser.parse_args()
model = settings.resolve_model(args.model)

client = OpenAI(
    base_url=settings.api_base_url,
    api_key=owner_token(),
    timeout=60 * 60,
    max_retries=0,
)

available = {entry.id for entry in client.models.list().data}
expected = {entry.model for entry in settings.models.values()}
if available != expected:
    raise SystemExit(
        f"Catalog mismatch: expected {sorted(expected)}, received {sorted(available)}"
    )

stream = client.chat.completions.create(
    model=model.model,
    messages=[
        {
            "role": "user",
            "content": "Reply with exactly: MN STREAM OK",
        }
    ],
    max_tokens=64,
    stream=True,
)
stream_text = "".join(
    chunk.choices[0].delta.content or ""
    for chunk in stream
)
if "MN STREAM OK" not in stream_text:
    raise SystemExit(f"{model.model} streaming smoke failed: {stream_text!r}")
print(f"{model.model}: streaming OK")

tool_response = client.chat.completions.create(
    model=model.model,
    messages=[
        {
            "role": "user",
            "content": "Call the mn_echo tool with value set to catalog-ok.",
        }
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "mn_echo",
                "description": "Echo a catalog smoke-test value.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"},
                    },
                    "required": ["value"],
                    "additionalProperties": False,
                },
            },
        }
    ],
    tool_choice={
        "type": "function",
        "function": {"name": "mn_echo"},
    },
    max_tokens=256,
)
tool_calls = tool_response.choices[0].message.tool_calls or []
if not tool_calls or tool_calls[0].function.name != "mn_echo":
    message = tool_response.choices[0].message
    raise SystemExit(
        f"{model.model} tool smoke failed: "
        f"content={message.content!r}, tool_calls={tool_calls!r}"
    )
print(f"{model.model}: tool calling OK")
