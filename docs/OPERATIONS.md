# Operations

## Architecture

```text
Hermes / Pi / OpenCode / Cursor / friends
                  |
        Bearer sk-mn-* token
                  |
      MN CPU gateway (Modal Function)
          /          |          \
     mn/god       mn/code      mn/fast
     H200           H200         L40S
```

The gateway selects a backend only from the tracked catalog. Each backend is a
separate Modal application with `min_containers=0`, `max_containers=1`, and a
600-second scale-down window.

An authenticated request in `auto` mode triggers only the requested model,
waits through Modal's empty cold-start 503, and retries the original request
once the selected backend is healthy. Application-level 503 responses with a
body are returned without retrying.

## Initial setup

```sh
uv sync
.venv/bin/modal setup
./scripts/install-macos.sh
./scripts/sync-modal-secret.sh
```

The macOS Keychain must contain:

```text
mn-uncensored-owner-token
uncensored-modal-key
uncensored-modal-secret
```

The gateway receives the Modal proxy credentials through the Modal Secret
`nuri-backend-proxy`. Hugging Face and MN plaintext tokens must never be added
to the tracked catalog.

## Catalog configuration

`config/mn.json` is the single tracked catalog. Every model contains:

- public MN ID and display name;
- exact Hugging Face repository and 40-character revision;
- independent Modal app and backend URL;
- GPU/count and cost estimate;
- context/output limits;
- vLLM reasoning and tool parsers;
- lifecycle and cache behavior.

`modal_vllm.py` selects one profile through `MN_MODEL=god|code|fast`. This
allows the same reproducible source to deploy three separate Modal apps.

Model weights, vLLM compilation artifacts, and FlashInfer CUDA kernels remain
in persistent Modal volumes. The first MoE cold start can spend several
minutes compiling Hopper kernels; later starts and compatible catalog models
reuse the shared `flashinfer-kernel-cache`.

## Normal operation

Enable all three scale-to-zero routes:

```sh
mn auto
```

Operate one model:

```sh
mn start code
mn status code
mn wake code
mn auto code
mn stop code
```

Operate or inspect the full catalog:

```sh
mn status
mn api
mn stop
```

Manual `start` changes only the selected Modal Server to:

```text
min_containers=1
max_containers=1
scaledown_window=300
```

`mn auto <model>` performs a recreate rollover when returning from a manual
warm state, restoring the immutable static `min_containers=0` definition.

`mn stop <model>` marks that route fail-closed before its recreate rollover.
Requests to other catalog models remain unaffected.

If a backend app was stopped outside the normal flow, `mn auto` and `mn start`
may perform a recovery deployment. Recovery requires a clean Git tree and a
verified signed HEAD commit.

## Agent launchers

```sh
mn launch hermes
mn launch --model code hermes --yolo
mn launch --model fast pi
mn launch --model code opencode
```

The selected model ID, 131,072 context, 16,384 output ceiling, endpoint, and
non-secret provider metadata are configured automatically. The owner token is
read from the Keychain and passed in the child process environment.

## Deployments and releases

Every deployment must start from a clean, signed commit:

```sh
./scripts/deploy-release.sh catalog v0.3.0
```

The `catalog` target:

1. verifies Git signing configuration;
2. runs the full test suite and secret scan;
3. deploys `god`, `code`, and `fast` as separate Modal apps;
4. deploys the shared gateway;
5. creates a signed annotated tag;
6. pushes the branch and tag;
7. creates the GitHub release.

Do not reuse a version tag. If a deployment fails before tagging, correct the
cause and rerun from the same clean signed commit. If it fails after a partial
catalog deployment, the old gateway remains authoritative until the gateway
target succeeds.

Only a full catalog deployment creates a release. The script enables automatic
mode, validates `/v1/models`, runs a real streaming completion and forced tool
call against each backend, hard-stops each tested GPU, then restores automatic
mode. A failed smoke test triggers a best-effort hard stop and no tag or GitHub
release is created.

## Verification

List models without waking a GPU:

```sh
curl "$MN_GATEWAY_URL/v1/models" \
  -H "Authorization: Bearer $MN_API_TOKEN"
```

Expected IDs:

```text
mn/god
mn/code
mn/fast
```

Test each selected model:

```sh
.venv/bin/python test_endpoint.py god
.venv/bin/python test_endpoint.py code
.venv/bin/python test_endpoint.py fast
```

Agent/tool smoke tests should include:

- ordinary completion;
- streaming completion;
- one tool call with arguments;
- context metadata from `/v1/models`;
- hard-stop isolation;
- ten-minute scale-to-zero observation.

After testing:

```sh
mn auto
```

Then verify in Modal that no GPU container remains after the idle window.

## Cost gate

Base estimates:

```text
mn/god   1 x H200  ~$4.54/hour
mn/code  1 x H200  ~$4.54/hour
mn/fast  1 x L40S  ~$1.95/hour
all                    ~$11.03/hour
```

Cold starts, inference, and each model's ten-minute idle window are billable.
The one-container limit applies per model, not across the workspace. Configure
a Modal budget before sharing tokens beyond controlled testing.
