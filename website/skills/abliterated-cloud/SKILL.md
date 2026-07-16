---
name: abliterated-cloud
description: Use ABLITERATED.cloud safely through its token-protected OpenAI-compatible Chat Completions API.
license: Apache-2.0
metadata:
  homepage: https://eminogrande.github.io/mn-uncensored/
  repository: https://github.com/eminogrande/mn-uncensored
---

# ABLITERATED.cloud

Use this skill when a user wants to call an ABLITERATED.cloud model through an OpenAI-compatible client.

## Safety boundary

- Never invent or expose an API token.
- Obtain the token only from the user's existing secret store or environment.
- Never write a token into source code, logs, configuration committed to Git, or a public issue.
- Do not call a hard-stopped route and assume it will wake.
- Do not start, arm, wake, or launch `mn/ornith-397b` without explicit operator cost acknowledgement.
- Do not claim that "abliterated" guarantees zero refusals or correctness.

## Connection

Use the operator-provided base URL ending in `/v1`.

Authenticate with:

```http
Authorization: Bearer sk-mn-...
```

## Models

- `mn/god`
- `mn/code`
- `mn/fast`
- `mn/ornith-397b` after the budgeted four-model release

The legacy ID `nuri/ornith-397b-abliterated` maps to the 397B route after that release.

## Supported contract

Prefer:

- `GET /v1/models`
- `POST /v1/chat/completions`
- streaming
- OpenAI-style `tools` and `tool_choice`

Do not assume full parity with every OpenAI API endpoint.

## Before a call

1. Confirm the desired public model ID.
2. Confirm the route is armed or started.
3. Confirm the user understands cold-start latency.
4. For 397B, confirm the explicit two-H200 cost acknowledgement.
5. Use a conservative `max_tokens` value for the first request.

## After testing

Tell the operator to hard-stop the model instead of relying only on the idle window.
