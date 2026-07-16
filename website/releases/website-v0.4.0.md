# ABLITERATED.cloud website-v0.4.0

A quieter, clearer landing page and the first complete Agent-Ready edge layer.

## Changed

- Rebuilt the landing page around larger type, more whitespace, flat borders
  and fewer decorative interface elements.
- Replaced raw repository slugs as headings with readable factual model names.
- Kept every complete Hugging Face `owner/repository` path directly below the
  heading with a direct upstream link.
- Moved internal `mn/*` route identifiers to the final technical row labeled
  `API model ID`.
- Simplified the page to: explanation, three steps, four models, one API
  example, transparency notes, FAQ and access request.
- Rewrote model descriptions for non-technical readers while preserving
  license, parameter, context, hardware, status and price details.

## Agent readiness

- Added the Cloudflare Worker edge layer used for the final custom domain.
- Added Markdown negotiation, discovery `Link` headers, `Content-Signal`,
  explicit MIME types and CORS for public machine-readable resources.
- Added OAuth protected-resource discovery, an A2A agent card, MCP server card,
  Agent Skills, WebMCP and HTTP-message-signature discovery.
- Added a real read-only MCP endpoint for the public service summary and exact
  model catalog.
- Added a local verification command covering every application-controlled
  `isitagentready.com` surface.

## Verification

- 61 repository tests pass.
- The Cloudflare Worker dry-run succeeds with 51 static assets.
- The local Agent-Ready verification passes.
- The homepage returns discovery `Link` and `Content-Signal` headers.
- `Accept: text/markdown` returns Markdown.
- `/.well-known/api-catalog` returns `application/linkset+json`.
- No model deployment is invoked and no GPU is started.

## Remaining external step

`abliterated.cloud` still uses Porkbun nameservers. A public 100% score requires
moving the final hostname to an active Cloudflare zone, enabling DNSSEC,
configuring DNS-AID, deploying the Worker and scanning that exact hostname.
