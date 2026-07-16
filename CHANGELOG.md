# Changelog

All notable changes to MN Uncensored are documented here.

## [Unreleased]

### Added

- Minimal `mn` menu and start, stop, status, API, token, and launch commands.
- First-class Hermes Agent launcher using its custom OpenAI-compatible provider.
- Launchers for Pi and OpenCode.
- Lightweight Modal FastAPI gateway with standard Bearer authentication.
- Multiple named API tokens with revocation and digest-only remote storage.
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
