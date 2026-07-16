# Release notes

These are the curated release notes for MN Uncensored. They describe tagged
runtime releases. Documentation on `main` after a tag may explain the deployed
runtime without implying that a new Modal deployment occurred.

## Unreleased — Cost-safety correction

### Safety changes

- `mn start MODEL` now safely arms and wakes one explicit model; it can no
  longer create an indefinite `min_containers=1` warm container.
- Default idle scale-down is five minutes.
- `start`, `auto`, and `wake` require an explicit model.
- Backend and gateway cold-start limits are 30 minutes.
- Release workflows finish with every model hard-stopped.
- Automatic-mode policy failures leave the route fail-closed.

### Incident record

- Added the complete 2026-07-16 Modal cost incident report with the raw
  `$45.9634` pre-credit breakdown and verified container-start timeline.
- Documented that stable auto scale-down worked; unsafe start semantics,
  aggressive pre-v0.3.1 polling, repeated deployments, and the separate legacy
  397B app caused the exposure.
- Modal Workspace hard budget is now a mandatory prerequisite for more GPU
  testing.

## v0.3.1 — Reliable cold-start waiting

Released 2026-07-16.

### Fixed

- Replaced five-second cold-start polling with exponential health-check
  backoff.
- Health probes now wait 30, 60, 120, and 240 seconds, capped at five minutes.
- Prevented long 35B starts from accumulating a queue of redundant Modal GPU
  invocations.

### Runtime status

- Catalog: `mn/god`, `mn/code`, and `mn/fast`.
- Lifecycle: independent request-triggered start and ten-minute idle shutdown.
- Context: 131,072 tokens on every route.
- Output ceiling: 16,384 tokens.
- Release verification: streaming completion and forced tool call on every
  model.

## v0.3.0 — Three-model catalog

Released 2026-07-16.

### Added

- `mn/god`: Huihui Qwen3.6 35B A3B Abliterated on one H200.
- `mn/code`: YuYu Ornith 35B Abliterated on one H200.
- `mn/fast`: Huihui Qwythos 9B Abliterated on one L40S.
- Independent lifecycle records and Modal applications for every route.
- Model selection in the CLI, Hermes, Pi, OpenCode, and endpoint tests.
- Strict public model routing and legacy alias migration.
- 131,072-token context and 16,384-token output ceiling.
- Persistent Hugging Face, vLLM, and FlashInfer caches.
- Exact model revision, attribution, compatibility, and license record.
- Apache-2.0 repository license.

### Changed

- Replaced the impractical single 397B prototype direction with an affordable
  35B/35B/9B evaluation catalog.
- Disabled Qwen thinking by default so standard clients receive normal
  `content`; direct clients can opt in.
- Aligned the vLLM tool parser with each pinned chat template.
- Persisted the selected catalog profile inside each Modal image.
- Added one retry for transient Modal recreate-rollover timeouts.

### Verified

- `/v1/models` returns exactly the three public MN IDs.
- Every model passed an ordinary streaming completion.
- Every model passed a forced function/tool call.
- Hard-stop isolation was tested per model.

## v0.2.0 — Automatic lifecycle

Released 2026-07-16.

### Added

- API-triggered cold starts through the shared gateway.
- Automatic mode with a ten-minute idle GPU shutdown.
- Authenticated `/wake` route.
- Hermes custom provider with long cold-start timeouts.
- Explicit hard stop for running and pending model containers.

### Fixed and changed

- The gateway recognizes Modal’s empty cold-start 503 response and waits for
  the backend instead of returning it directly to clients.
- Compressed upstream streaming chunks are decoded before forwarding.
- vLLM uses the pinned model snapshot and reproducible lifecycle configuration.
- Automatic mode no longer creates a permanently pending server.
- Recovery deployments require a clean worktree and verified signed HEAD.
- Stop transitions fail closed before a backend rollover.

## v0.1.0 — Initial control plane

Released 2026-07-16.

### Added

- Minimal `mn` interactive menu and CLI.
- Start, stop, status, API, token, and agent-launch commands.
- Hermes, Pi, and OpenCode launchers.
- Modal FastAPI gateway with an OpenAI-compatible `/v1/models` route and
  transparent `/v1/*` proxy.
- Bearer API authentication with named token creation and revocation.
- macOS Keychain storage for the owner token.
- SHA-256 digest-only token storage in Modal.
- Private Modal backend authentication through a separate proxy credential.
- Secret scanning and signed deployment/release workflow.

### Security boundary

- The endpoint URL is not treated as an access control.
- Plaintext owner and backend credentials do not belong in Git.
- A stopped lifecycle fails closed rather than being silently woken.
