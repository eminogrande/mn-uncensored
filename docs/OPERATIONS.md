# Operations

## Components

```text
Hermes / Pi / OpenCode / Cursor / friends
                  |
        Bearer sk-mn-* token
                  |
      MN CPU gateway (Modal Function)
                  |
       Modal-Key + Modal-Secret
                  |
  vLLM Server: 1 container, 2 x H200
```

The gateway is cheap and may scale to zero independently. In the recommended
`auto` state, the first authenticated model request triggers the GPU cold start,
waits through Modal's temporary 503 responses, and then retries the original
request. The backend shuts down after 10 idle minutes.

The vLLM server exposes a 65,536-token context. Hermes 0.18.2 enforces a
64,000-token minimum for known custom models, so the gateway and Hermes provider
must never advertise a larger context than the backend actually serves.

The backend normally sets `LOCAL_SNAPSHOT=true` and opens the pinned path in
`hf-model-cache` directly. Set it to `false` only to populate a new cache; a Hub
repository may contain irrelevant card/assets files that are intentionally not
needed at inference time.

## Initial setup

```sh
uv sync
.venv/bin/modal setup
./scripts/install-macos.sh
```

Create `deployment.env` from `deployment.env.example` if the model deployment
settings need to be changed. This file is ignored by Git.

Create the backend proxy secret from the existing Keychain values:

```sh
./scripts/sync-modal-secret.sh
```

Bootstrap the gateway from a clean, committed tree:

```sh
PYTHONPATH="$PWD/src" .venv/bin/modal deploy modal_gateway.py --tag v0.1.0
```

After the first deployment, copy the printed gateway URL into:

- `config/mn.json`
- `config/pi-agent/models.json`

Commit that non-secret URL, reinstall the editable CLI, test the endpoint, then
create the first signed tag and GitHub release. Subsequent deployments use the
release script below because the Modal URL remains stable.

Create the owner token:

```sh
mn token create owner
```

## Normal operation

Enable automatic operation:

```sh
mn auto
```

The deployed static definition uses:

```text
min_containers=0
max_containers=1
scaledown_window=600
```

Hermes, Pi, and OpenCode launchers call the authenticated `/wake` endpoint
before opening the agent:

```sh
mn launch hermes
```

The Hermes launcher persists only non-secret provider metadata in the existing
Hermes config. It passes `MN_API_TOKEN` and the 45-minute cold-start timeouts in
the child process environment.

For a temporarily permanent warm replica, start and wait for readiness:

```sh
mn start
```

The command dynamically sets:

```text
min_containers=1
max_containers=1
scaledown_window=300
```

Hard stop:

```sh
mn stop
```

The gateway becomes fail-closed first, then `mn stop` performs a Modal
`rollover --strategy recreate`. This replaces containers from the same immutable
deployment version and restores its static `min_containers=0` configuration
without uploading local source.

`mn auto` normally changes only the control state. Modal then performs native
zero-to-one scaling on the next authenticated request and shuts down after 600
idle seconds.

If the backend app was permanently stopped outside the normal flow, recovery
requires a source deploy. The CLI refuses that recovery unless the Git tree is
clean and HEAD has a verified signature, and records the short commit in the
Modal deployment tag. Source changes still require a new signed GitHub release.

Check state:

```sh
mn status
```

## Deployments and releases

Every deployment must start from a clean, committed working tree. Use:

```sh
./scripts/deploy-release.sh gateway vX.Y.Z
./scripts/deploy-release.sh backend vX.Y.Z
```

The script:

1. verifies the tree is clean;
2. verifies global SSH commit and tag signing;
3. runs tests and the secret scan;
4. deploys the selected Modal app;
5. creates a signed annotated tag;
6. pushes the branch and tag;
7. creates a GitHub release.

Deploying the backend resets dynamic autoscaler overrides to the static source
configuration (`min_containers=0`). The backend therefore remains stopped after
a deployment until `mn start` is run.

## Verification

While hard-stopped:

```sh
curl -i "$MN_GATEWAY_URL/v1/models" \
  -H "Authorization: Bearer $MN_API_TOKEN"

curl -i "$MN_GATEWAY_URL/v1/chat/completions" \
  -H "Authorization: Bearer $MN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"anything","messages":[]}'
```

The model list should return 200. A completion should return a structured 503
with code `model_stopped` and must not start a GPU.

In auto mode, the first completion is held by the gateway while the backend
starts, then retried. The gateway and Hermes timeouts are 45 minutes, which is
above the observed roughly 20-minute cached cold start.

After `mn start`, run:

```sh
.venv/bin/python test_endpoint.py
mn launch hermes
```

Then stop the deployment and confirm in the Modal dashboard that the GPU
container count returns to zero.
