# ABLITERATED.cloud website-v0.4.1

WebMCP registration fix for the Agent-Ready edge release.

## Fixed

- Register the public read-only `get_site_summary`, `list_models` and
  `read_public_documentation` tools with `navigator.modelContext` when a
  supporting browser or scanner exposes WebMCP.
- Keep the static `/.well-known/webmcp.json` manifest and the live document
  registration aligned.
- Preserve ordinary browser behavior through progressive enhancement; the
  registration adds no third-party dependency and makes no inference request.

## Verification

- 62 repository tests pass.
- The local Agent-Ready verification passes.
- The Cloudflare Worker dry-run succeeds.
- No Modal application is imported and no GPU is started.
