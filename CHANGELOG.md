# Changelog

All notable changes to MN Uncensored are documented here.

## [Unreleased]

### Fixed

- Changed `mn start MODEL` from an indefinite `min_containers=1` warm mode to a
  fail-safe automatic route plus one explicit wake.
- Reapply `min_containers=0`, `max_containers=1`, and the tracked idle window
  whenever automatic mode is armed; failures leave the route hard-stopped.
- Reduced backend and gateway cold-start timeouts from 90/45 minutes to
  30 minutes.

### Security

- Reduced the idle shutdown window from ten to five minutes and reject tracked
  values above 300 seconds.
- Require an explicit model for `start`, `auto`, and `wake`.
- Leave every model hard-stopped after release smoke tests instead of restoring
  all routes to wakeable automatic mode.
- Added regression tests that forbid a normal warm-container floor.

### Documentation

- Added a full post-incident report for the 2026-07-16 Modal GPU cost event,
  including the `$45.9634` pre-credit breakdown, verified timeline, root
  causes, limitations, containment, and safe operating procedure.
- Rewrote start/stop guidance around hard-stop by default, one explicit model,
  five-minute idle scale-down, actual billing inspection, and the mandatory
  Modal Workspace budget.
- Expanded the README into a complete architecture and operations guide with
  Mermaid diagrams for routing, cold starts, lifecycle state, token security,
  cloud storage, capacity, and the future resale stack.
- Documented the original 397B direction, the 35B/35B/9B catalog decision,
  provider comparison, current official price calculations, multi-user
  capacity, client-specific setup, troubleshooting, and commercial gaps.
- Added curated historical release notes for every published version.
- Replaced the stale release-command example with a neutral version example.

### Changed

- Future GitHub releases now use the matching curated `CHANGELOG.md` section
  instead of publishing only automatically generated commit links.

### Added

- Added a tested release-note extractor that fails if the requested version is
  missing or empty.

## [0.3.1] - 2026-07-16

### Fixed

- Replaced five-second cold-start polling with exponential backoff so long
  Modal starts do not accumulate redundant pending GPU invocations.

## [0.3.0] - 2026-07-16

### Added

- Three independently autoscaling catalog models: `mn/god`, `mn/code`, and
  `mn/fast`.
- Strict model routing, per-model lifecycle records, and isolated wake/status
  endpoints.
- Model selection for Hermes, Pi, OpenCode, CLI controls, and endpoint tests.
- Pinned model/license record with the documented Qwen3.6 compatibility
  fallback.
- Apache-2.0 project license.
- Request-side 16,384-token output enforcement.

### Changed

- Replaced the single 397B backend with two 35B H200 profiles and one 9B L40S
  profile.
- Increased the advertised and served context from 65,536 to 131,072 tokens.
- Made hard stop and automatic mode operate per backend without affecting the
  other catalog models.
- Updated the release workflow to deploy all three backends and the shared
  gateway under one signed release.
- Persisted and shared FlashInfer CUDA kernels across scale-to-zero cold
  starts.
- Disabled Qwen thinking by default for clients that consume only the standard
  OpenAI `content` field; requests can explicitly opt back in.
- Aligned every catalog model with the XML tool-call format declared by its
  pinned Hugging Face chat template.
- Persisted the selected catalog profile inside each Modal image so runtime
  imports cannot fall back to the default model.
- Retry a transient Modal recreate-rollover timeout once while keeping the
  affected route fail-closed.

### Security

- Backend destinations and model aliases are resolved only from the tracked
  catalog.
- Unknown or malformed model IDs and excessive output requests fail before an
  upstream client is created.
- Expanded Docker-context exclusions for environment files and local agent
  credentials.

## [0.2.0] - 2026-07-16

### Added

- API-triggered cold starts with gateway-side waiting through Modal 503s.
- Ten-minute idle GPU shutdown through `mn auto`.
- Authenticated `/wake` endpoint used automatically by agent launchers.
- Named Hermes custom provider with remote-endpoint timeout hardening.
- 65,536-token backend context required by Hermes Agent.
- Immediate termination of running or pending model containers on hard stop.

### Changed

- Automatic mode is now the recommended default; manual warm and hard-stop
  modes remain available.
- vLLM opens the pinned local Hugging Face snapshot directly in offline mode.
- Entering auto mode from a stopped state no longer creates a Pending server.
- Hard stop resets the immutable deployment with a recreate rollover.
- Auto mode normally changes only control state; recovery deploys require a
  clean, verified signed HEAD.
- Gateway streaming decodes compressed upstream chunks before forwarding.

### Security

- Cold-start polling rechecks hard-stop state before every probe and retry.
- Application-level 503 responses are no longer mistaken for Modal cold starts.

## [0.1.0] - 2026-07-16

### Added

- Minimal `mn` menu and start, stop, status, API, token, and launch commands.
- First-class Hermes Agent launcher using its custom OpenAI-compatible provider.
- Launchers for Pi and OpenCode.
- Lightweight Modal FastAPI gateway with standard Bearer authentication.
- Multiple named API tokens with revocation and digest-only remote storage.
- Clipboard-only retrieval for the Keychain-backed owner token.
- Explicit gateway state that prevents stopped clients from waking the GPU.
- OpenAI-compatible `/v1/models` and transparent `/v1/*` proxying.
- Local gateway and token security tests.
- Signed deployment and release workflow.

### Changed

- Pi now uses the shared MN gateway instead of Modal proxy headers.
- The model server is controlled through dynamic Modal autoscaler settings.

### Security

- Agent credentials, sessions, environment files, and runtime state are ignored.
- The owner token is stored in the macOS Keychain.
- Modal backend credentials are isolated in a Modal Secret.
- Gateway docs and permissive cross-origin access are disabled.
