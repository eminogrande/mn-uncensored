# Operations

## Cost-safety runbook

The default safe state is hard-stopped:

```sh
mn stop
mn status
```

Before any GPU test:

1. set a Modal Workspace hard budget at
   <https://modal.com/settings/usage>;
2. select exactly one model;
3. prefer `fast` for initial testing;
4. stop it explicitly after the session;
5. inspect the Modal billing report and running containers.

Safe session:

```sh
mn start fast
# use the API or agent
mn stop fast
mn status fast
```

`mn start MODEL` no longer creates a permanent warm container. It enforces
`min_containers=0`, wakes one explicit route, and leaves it with a five-minute
idle shutdown.

The five-minute timer is an idle tail, not a maximum charge. Startup,
compilation, inference, queued requests, retries, and open streams are active
and billable. See
[the 2026-07-16 cost incident](INCIDENT-2026-07-16-MODAL-COST.md).

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
300-second scale-down window.

An authenticated request in `auto` mode triggers only the requested model,
waits through Modal's empty cold-start 503, and retries the original request
once the selected backend is healthy. Application-level 503 responses with a
body are returned without retrying.

After the initial Modal trigger, health checks use exponential backoff: 30,
60, 120, and 240 seconds, capped at five minutes. This avoids creating a large
queue of redundant GPU starts during long cold starts.

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
allows the same reproducible source to deploy three separate Modal apps. The
selected non-secret profile key is also baked into that model's Modal image so
the container resolves the same profile when it imports the module at runtime.

Model weights, vLLM compilation artifacts, and FlashInfer CUDA kernels remain
in persistent Modal volumes. The first MoE cold start can spend several
minutes compiling Hopper kernels; later starts and compatible catalog models
reuse the shared `flashinfer-kernel-cache`.

## Normal operation

Hard-stop every route:

```sh
mn stop
```

Operate one model:

```sh
mn start code
mn status code
mn wake code
mn auto code
mn stop code
```

`mn start code` is equivalent to safely arming `code` and waking it once. It
does not set a warm-container floor.

Arm a route without starting a GPU:

```sh
mn auto code
```

Operate or inspect the full catalog:

```sh
mn status
mn api
mn stop
```

Every normal start and automatic route enforces:

```text
min_containers=0
max_containers=1
scaledown_window=300
```

There is no normal permanent-warm command. If one is ever introduced, it must
be separately named, explicitly confirmed, time-limited, and covered by a hard
budget.

`mn stop <model>` marks that route fail-closed before its recreate rollover.
Requests to other catalog models remain unaffected.
If Modal updates the app but needs longer than its first container-termination
window, MN retries the fail-closed recreate rollover once.

If a backend app was stopped outside the normal flow, `mn auto MODEL` and
`mn start MODEL` may perform a recovery deployment. Recovery requires a clean
Git tree and a verified signed HEAD commit.

## Agent launchers

```sh
mn start fast
mn launch --model fast hermes
mn stop fast

mn start code
mn launch --model code hermes --yolo
mn launch --model code opencode
mn stop code
```

The selected model ID, 131,072 context, 16,384 output ceiling, endpoint, and
non-secret provider metadata are configured automatically. The owner token is
read from the Keychain and passed in the child process environment.

Launchers do not arm a hard-stopped route implicitly. The explicit preceding
`mn start MODEL` is a cost acknowledgement; the explicit following
`mn stop MODEL` is the normal end of a session.

Qwen thinking is disabled by default so OpenAI-compatible clients receive
normal `content` instead of silently dropping a model-specific reasoning field.
Clients can opt in per request with:

```json
{"chat_template_kwargs": {"enable_thinking": true}}
```

## Deployments and releases

Every deployment must start from a clean, signed commit:

```sh
./scripts/deploy-release.sh catalog v1.2.3
```

The `catalog` target:

1. verifies Git signing configuration;
2. runs the full test suite and secret scan;
3. extracts the matching curated section from `CHANGELOG.md`;
4. deploys `god`, `code`, and `fast` as separate Modal apps;
5. deploys the shared gateway;
6. arms, tests, and hard-stops each route individually;
7. creates a signed annotated tag;
8. pushes the branch and tag;
9. creates the GitHub release with those notes.

Before deploying `vX.Y.Z`, move the completed changes out of `Unreleased` into
a non-empty `## [X.Y.Z] - YYYY-MM-DD` section. The release fails instead of
publishing empty or generic notes when that section is missing.

Do not reuse a version tag. If a deployment fails before tagging, correct the
cause and rerun from the same clean signed commit. If it fails after a partial
catalog deployment, the old gateway remains authoritative until the gateway
target succeeds.

Only a full catalog deployment creates a release. The script arms one route,
validates `/v1/models`, runs a real streaming completion and forced tool call,
and hard-stops that route before moving to the next. It finishes with all
models hard-stopped. A failed smoke test triggers a best-effort hard stop and
no tag or GitHub release is created.

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
- five-minute scale-to-zero observation.

After testing:

```sh
mn stop
```

Then verify in Modal that every model app has zero tasks and the container list
is empty.

Billing audit:

```sh
.venv/bin/modal billing report \
  --for today \
  --resolution h \
  --tz local \
  --show-resources
```

The CLI report is before credits and may lag. Usage & Billing and the invoice
remain authoritative.

## Cost gate

Base estimates:

```text
mn/god   1 x H200  ~$4.54/hour
mn/code  1 x H200  ~$4.54/hour
mn/fast  1 x L40S  ~$1.95/hour
all                    ~$11.03/hour
```

Cold starts, inference, queued work, and each model's five-minute idle window
are billable. Backend startup is capped at 30 minutes, but that cap is not a
substitute for a Workspace budget.
The one-container limit applies per model, not across the workspace. Configure
a Modal Workspace hard budget before any further GPU testing.
