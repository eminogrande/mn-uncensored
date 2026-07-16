# MN Uncensored

MN Uncensored is a minimal control tool for a private, OpenAI-compatible
deployment of `nuri/ornith-397b-abliterated`.

The model runs with vLLM on two Modal H200 GPUs. A separate lightweight API
gateway provides ordinary Bearer tokens, so Hermes, Pi, OpenCode, Cursor, and
other OpenAI-compatible applications all use the same endpoint.

## Everyday use

Install the local CLI once:

```sh
./scripts/install-macos.sh
```

Then use either the live menu:

```sh
mn
```

or direct commands:

```sh
mn start
mn status
mn launch hermes
mn stop
```

`mn start` keeps one model replica warm and waits until it is ready. A cached
cold start currently takes roughly 20 minutes. `mn stop` immediately blocks new
gateway requests and asks Modal to scale the GPU replica to zero.

## Hermes Agent

Hermes is a first-class launcher:

```sh
mn launch hermes
```

The launcher reads the owner token from the macOS Keychain and sets:

- `OPENAI_BASE_URL` to the MN `/v1` endpoint
- `OPENAI_API_KEY` to the owner Bearer token
- provider to Hermes' `custom` OpenAI-compatible provider
- model to `nuri/ornith-397b-abliterated`

Extra Hermes arguments can be appended:

```sh
mn launch hermes --yolo
```

The same model can be opened in the other installed coding agents:

```sh
mn launch pi
mn launch opencode
```

## API tokens

Create the local owner token once:

```sh
mn token create owner
```

The owner token is stored in the macOS login Keychain. Create separate tokens
for friends:

```sh
mn token create alice
mn token create bob
mn token list
mn token revoke alice
```

Friend tokens are displayed once. The gateway stores only SHA-256 token
digests, never plaintext tokens.

## Standard OpenAI API

Show the current connection values:

```sh
mn api
```

Any compatible application uses:

```text
Base URL: https://<gateway>.modal.run/v1
API key:  sk-mn-...
Model:    nuri/ornith-397b-abliterated
```

Example:

```sh
curl "$MN_GATEWAY_URL/v1/chat/completions" \
  -H "Authorization: Bearer $MN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nuri/ornith-397b-abliterated",
    "messages": [{"role": "user", "content": "Say hello briefly."}],
    "max_tokens": 80
  }'
```

For Cursor or another GUI, paste the same base URL and API key into its custom
OpenAI provider settings. The gateway rewrites model aliases to the deployed MN
model, while `/v1/models` reports the canonical model name.

## Cost and capacity

Modal currently lists H200 compute at `$0.001261/second`, or approximately
`$4.54/hour` per GPU. This deployment uses two H200s, so the GPU ceiling is
approximately `$9.08/active hour`, plus a very small CPU gateway cost.

The initial deployment is deliberately capped at:

- one GPU container
- two H200s in that container
- one vLLM sequence at a time

Several people may hold tokens and send requests, but they share that one model
replica. With `--max-num-seqs 1`, only one generation runs at a time and other
requests wait or time out. The hourly GPU price does not increase with the
number of users unless the deployment is changed to allow more GPU replicas.

## Safety boundary

When state is `stopped` or `starting`, the public gateway returns a structured
503 response without forwarding the request. Therefore a forgotten Cursor,
Hermes, or friend token cannot wake the expensive GPU backend.

The private backend still requires Modal's `Modal-Key` and `Modal-Secret`.
Those values live only in the macOS Keychain and the Modal secret
`nuri-backend-proxy`.

Do not commit:

- `.env` or `deployment.env`
- Pi authentication, settings, or session files
- Modal proxy credentials
- Hugging Face tokens
- MN plaintext API tokens

See [OPERATIONS.md](docs/OPERATIONS.md) for deployment and release procedures
and [SECURITY.md](SECURITY.md) for the credential model.

## Model notes

The deployed checkpoint is
`cebeuq/Ornith-1.0-397B-abliterated-W4A16`, pinned to revision
`e5651d291be1c65ff1360eee47ab533ab13b3d97`.

Its aligned parent reports 82.4% on SWE-bench Verified. That score must not be
presented as a benchmark of this modified checkpoint. Benchmark the exact
deployment before making performance claims, and review both the model license
and infrastructure terms before offering paid public access.
