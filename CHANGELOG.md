# Changelog

All notable changes to MN Uncensored are documented here.

## [Unreleased]

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
