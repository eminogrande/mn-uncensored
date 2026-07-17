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
3. prefer `qwythos9` for initial testing;
4. stop it explicitly after the session;
5. inspect the Modal billing report and running containers.

`cebeuq/Ornith-1.0-397B-abliterated-W4A16` is the expensive retained fourth
profile. It uses two H200s and is intentionally blocked with
`deployment_enabled=false`. CLI start, auto, wake, and launch operations would
also require `--allow-expensive`; the source record alone does not deploy or
start it.

The commands below document the intended operating interface after a reviewed
deployment. Preparing or reading this runbook does not create a Modal app.

Safe session:

```sh
mn start qwythos9
# use the API or agent
mn stop qwythos9
mn status qwythos9
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
      abliterated-cloud-api (prepared gateway)
          /                 |                 \
 huihui-qwen3-6-35b-a3b-abliterated | yuyu1015-ornith-1-0-35b-abliterated | huihui-qwythos-9b-claude-mythos-5-1m-abliterated
          H200              |          H200             |          L40S
```

Each enabled backend definition is a separate Modal app with
`min_containers=0`, `max_containers=1`, and a 300-second scale-down window.
The names above are the prepared names; applying them to the Modal dashboard
requires a separate deployment and is intentionally outside this source-only
change.

The source catalog also retains `cebeuq/Ornith-1.0-397B-abliterated-W4A16`, pinned to
[`cebeuq/Ornith-1.0-397B-abliterated-W4A16`](https://huggingface.co/cebeuq/Ornith-1.0-397B-abliterated-W4A16)
at revision `e5651d291be1c65ff1360eee47ab533ab13b3d97`. Its prepared Modal app
name is `cebeuq-ornith-1-0-397b-abliterated-w4a16`, but
`deployment_enabled=false` prevents it from entering the deployable model set.

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

`config/mn.json` is the tracked source catalog and contains all four pinned
profiles, including the budget-gated `cebeuq/Ornith-1.0-397B-abliterated-W4A16` record. A catalog model
contains:

- short CLI key, exact API/Hugging Face ID, aliases, and display name;
- explicit `deployment_enabled` policy;
- exact Hugging Face repository and 40-character revision;
- independent Modal app and backend URL;
- GPU/count and cost estimate;
- context/output limits;
- vLLM reasoning and tool parsers;
- lifecycle and cache behavior.

`Settings.deployed_models` supplies only the three enabled profiles to gateway
and release workflows. The disabled 397B profile remains visible in the source
catalog but must not be deployed. The selected non-secret profile key is also
baked into that model's Modal image so the container resolves the same profile
when it imports the module at runtime.

The fourth route is guarded consistently by source policy, CLI, and release
workflow. A catalog release must fail while `deployment_enabled=false`.
If a future signed budget-approved change enables it, `--allow-expensive`
acknowledges individual lifecycle operations and a full release additionally
requires `MN_RELEASE_ORNITH397=I_ACCEPT_2XH200`.
Its retained serving profile uses `qwen3_xml`, `qwen3` reasoning with thinking
disabled by default, `language_model_only=false`, and
`prefix_caching=false`. These choices reflect the pinned chat template and
conservative reintroduction policy; they still require budgeted text, vision,
and tool-call validation before deployment.

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
mn start ornith35
mn status ornith35
mn wake ornith35
mn auto ornith35
mn stop ornith35
```

`mn start ornith35` is equivalent to safely arming `ornith35` and waking it once. It
does not set a warm-container floor.

Arm a route without starting a GPU:

```sh
mn auto ornith35
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
mn start qwythos9
mn launch --model qwythos9 hermes
mn stop qwythos9

mn start ornith35
mn launch --model ornith35 hermes --yolo
mn launch --model ornith35 opencode
mn stop ornith35
```

The selected model ID, model-specific context/output limits, endpoint, and
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
4. verifies that `ornith397` was explicitly enabled by a signed,
   budget-approved change, then deploys `qwen36`, `ornith35`, `qwythos9`, and
   `ornith397` as separate Modal apps;
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

The `catalog` release deploys and smoke-tests all four routes only after a
signed change sets `ornith397.deployment_enabled=true` and the operator also
provides:

```sh
MN_RELEASE_ORNITH397=I_ACCEPT_2XH200 \
  ./scripts/deploy-release.sh catalog v1.2.3
```

With the tracked policy still false, the release refuses to begin even if the
environment value is present. The operator must confirm the Workspace hard
budget before changing either gate.

## Verification

List models without waking a GPU:

```sh
curl "$MN_GATEWAY_URL/v1/models" \
  -H "Authorization: Bearer $MN_API_TOKEN"
```

Expected IDs for the three enabled prepared profiles:

```text
huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated
YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated
huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated
```

After a future reviewed 397B enablement and successful validation,
`cebeuq/Ornith-1.0-397B-abliterated-W4A16` becomes the fourth exact API ID.
Legacy `mn/*` values are compatibility aliases only.

Test each selected model:

```sh
.venv/bin/python test_endpoint.py qwen36
.venv/bin/python test_endpoint.py ornith35
.venv/bin/python test_endpoint.py qwythos9
.venv/bin/python test_endpoint.py ornith397
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
huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated          1 x H200  $4.5396/hour
YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated          1 x H200  $4.5396/hour
huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated
                                                        1 x L40S  $1.9512/hour
enabled source profiles                                           $11.0304/hour

cebeuq/Ornith-1.0-397B-abliterated-W4A16   2 x H200  $9.0792/hour  disabled
hypothetical all four                                      $20.1096/hour
```

Cold starts, inference, queued work, and each model's five-minute idle window
are billable. Backend startup is capped at 30 minutes, but that cap is not a
substitute for a Workspace budget.
The one-container limit applies per model, not across the workspace. Configure
a Modal Workspace hard budget before any further GPU testing.

Five-minute base GPU tails are approximately `$0.3783` for either one-H200
route, `$0.1626` for
`huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated`, `$0.7566` for
the disabled two-H200 397B profile, `$0.9192` for the three enabled profiles,
and `$1.6758` for a hypothetical all-four deployment. These are risk ceilings,
not evidence of current usage.
