# MN Uncensored

MN Uncensored is a minimal three-model catalog with one authenticated,
OpenAI-compatible API:

| Model | Purpose | Modal GPU | Base active cost |
| --- | --- | --- | ---: |
| `mn/god` | Qwen3.6 35B A3B abliterated general agent | 1 x H200 | about $4.54/hour |
| `mn/code` | Ornith 35B abliterated coding agent | 1 x H200 | about $4.54/hour |
| `mn/fast` | Qwythos 9B abliterated fast/cheap agent | 1 x L40S | about $1.95/hour |

Each model has its own private vLLM backend and independent scale-to-zero
lifecycle. The lightweight gateway and Bearer tokens are shared, so Hermes,
Pi, OpenCode, Cursor, and other OpenAI-compatible applications use the same
base URL.

## Install and enable automatic mode

```sh
./scripts/install-macos.sh
mn auto
mn status
```

`mn auto` enables wake-on-request for all three models without keeping a GPU
warm. An authenticated request starts only the selected model. Ten minutes
after its last backend request, that model scales back to zero.

Manual controls are model-aware:

```sh
mn start code     # keep mn/code warm
mn stop fast      # hard-stop only mn/fast
mn stop           # hard-stop all models
mn auto god       # restore automatic mode for one model
mn wake fast      # explicitly wake one model
```

The first start downloads the pinned weights into the shared Modal volume.
Later cold starts reuse that cache.

## Launch coding agents

The default is `mn/god`:

```sh
mn launch hermes
mn launch pi
mn launch opencode
```

Select another catalog model by placing `--model` before the tool name:

```sh
mn launch --model code hermes --yolo
mn launch --model fast pi
mn launch --model code opencode
```

The launcher reads the owner token from the macOS Keychain, wakes only the
selected backend, and passes the token only to the child process.

All catalog models expose a real 131,072-token context and a 16,384-token output
ceiling. Hermes therefore receives more than its required 64K context without
the old 33K workaround.

## API tokens

Create the local owner token once:

```sh
mn token create owner
```

The owner token is stored in the macOS login Keychain. Named friend tokens can
be created and revoked independently:

```sh
mn token copy owner
mn token create alice
mn token list
mn token revoke alice
```

`mn token copy owner` writes the token directly to the clipboard. The gateway
stores only SHA-256 token digests, never plaintext tokens.

## Standard OpenAI API

Show the connection values:

```sh
mn api
```

Current base URL:

```text
https://eminhenri--mn-uncensored-api-api.modal.run/v1
```

Example:

```sh
curl "https://eminhenri--mn-uncensored-api-api.modal.run/v1/chat/completions" \
  -H "Authorization: Bearer $MN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mn/code",
    "messages": [{"role": "user", "content": "Say hello briefly."}],
    "max_tokens": 80
  }'
```

The authenticated `/v1/models` endpoint lists `mn/god`, `mn/code`, and
`mn/fast` without waking a GPU. Unknown model IDs are rejected before an
upstream connection is created. During the v0.3 migration, the old
`nuri/ornith-397b-abliterated` ID resolves to the default `mn/god` route so an
old client does not accidentally wake two backends.

## Cost and capacity

Modal publishes base prices of approximately $4.54/hour for an H200 and
$1.95/hour for an L40S. All three models running simultaneously are therefore
about $11.03/hour of base GPU compute, plus the small gateway and any regional
or ancillary charges.

Each backend is capped at:

- one GPU container;
- the configured GPU count;
- one vLLM generation sequence;
- 16,384 output tokens per request;
- ten billable idle minutes before scale-to-zero.

Multiple users share each model replica. Requests to different models can run
and become billable simultaneously. Scale-to-zero is not a workspace spending
limit.

## Security and release boundary

The repository and endpoint addresses may be public; the service is not public
access. Every model, status, and wake request requires a valid Bearer token.
The private Modal backends additionally require Modal proxy credentials.

Never commit:

- `.env`, `.env.*`, or `deployment.env`;
- Modal, Hugging Face, or MN plaintext tokens;
- Pi authentication, settings, or session files;
- local `.mn/` state.

This remains a private evaluation deployment, not a production resale
platform. Before selling public access, add quotas, per-token model
permissions, metering, billing reconciliation, abuse controls, terms, privacy
controls, and legal review.

See:

- [Operations](docs/OPERATIONS.md)
- [Model pins, licenses, and compatibility exception](docs/MODELS.md)
- [Security boundary](SECURITY.md)
- [Apache-2.0 project license](LICENSE)

## Model accuracy note

The configured model artifacts and full Hugging Face revisions are pinned in
`config/mn.json`. Benchmark results from a base model or another abliterated
checkpoint must not be presented as results of the deployed MN artifact.

In particular, the originally selected WWTCyber Qwen3.6 checkpoint is not
compatible with vLLM 0.21's registered architectures. `mn/god` therefore uses
the pinned Huihui Qwen3.6 fallback documented in
[docs/MODELS.md](docs/MODELS.md).
