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

The gateway is cheap and may scale to zero independently. It reads the desired
model state before forwarding. Only the local `mn start` command changes the
backend to `min_containers=1`.

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

Start and wait for readiness:

```sh
mn start
```

The command dynamically sets:

```text
min_containers=1
max_containers=1
target_concurrency=1
scaledown_window=300
```

Stop:

```sh
mn stop
```

The gateway blocks traffic first, then the command sets:

```text
min_containers=0
max_containers=1
scaledown_window=2
```

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

While stopped:

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

After `mn start`, run:

```sh
.venv/bin/python test_endpoint.py
mn launch hermes
```

Then stop the deployment and confirm in the Modal dashboard that the GPU
container count returns to zero.
