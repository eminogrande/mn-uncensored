# ABLITERATED.cloud website

This directory contains the dependency-free static landing page. GitHub Pages
remains the public preview. The repository also contains a Cloudflare Worker
edge layer for the final `abliterated.cloud` deployment.

## Goals

- high PageSpeed performance without a build framework;
- complete semantic content in the initial HTML response;
- responsive and accessible design;
- exact model, status, price, and licensing transparency;
- agent-readable Markdown, `llms.txt`, OpenAPI, authentication, skill, robots,
  sitemap, and security resources;
- no analytics, advertising, external fonts, cookies, secrets, inference API
  calls, health polling, or Modal wake requests.

## Typography

The page uses one mono type system throughout. Its local stack begins with
Geist Mono, matching the type direction that inspired the layout, and falls
back to the operating system's native monospace fonts without downloading a
webfont. No fixed interface text is smaller than 17 px.

## Local preview

Use the real edge behavior locally:

```sh
npm install
npm run dev:website
```

Open:

```text
http://127.0.0.1:8788/
```

Then verify the complete local agent surface:

```sh
npm run verify:agent-ready:local
```

## Hero visual

The live hero uses a small, dependency-free Canvas point cloud. It generates a
deterministic abstract brain locally, pauses outside the viewport and when the
tab is hidden, caps rendering density, and becomes static when the visitor
prefers reduced motion. It does not load Three.js or contact a third party.

The owner-supplied brain-and-broken-chains artwork remains stored in optimized
formats for social sharing and the no-JavaScript fallback:

- `assets/hero-brain.avif` is the preferred 142 KB hero image;
- `assets/hero-brain.webp` is the compatibility fallback.

The normal page does not preload either raster image, keeping the critical
render path small.

## Access request

Active private-beta access links use Signal:

```text
https://signal.me/#p/+13103408213
```

Signal does not support the previous WhatsApp-style prefilled message on this
phone link. Visitors are asked in nearby copy to mention ABLITERATED.cloud.

## GitHub Pages

GitHub Pages publishes the root of the `gh-pages` branch. The signed deployment
command is:

```sh
./scripts/deploy-website.sh website-vX.Y.Z
```

The command requires a clean, SSH-signed `main`, runs the complete test suite
and secret scan, creates a signed commit on `gh-pages`, pushes it, and requests
a classic GitHub Pages build. It then creates a signed tag and GitHub release
from `website/releases/website-vX.Y.Z.md`. It never imports the Modal
application, deploys a model, wakes an endpoint, or starts a GPU.

The repository originally included a GitHub Actions Pages workflow. GitHub
refused to start that job because the account was locked for a billing issue,
so Pages now deliberately uses the branch-based deployment that has been
verified to work. This also prevents future `main` pushes from creating a
known-failing Actions run.

Initial URL:

```text
https://eminogrande.github.io/mn-uncensored/
```

## Final custom domain and edge deployment

The intended domain is:

```text
https://abliterated.cloud/
```

`abliterated.cloud` currently uses Porkbun nameservers and parking records.
Cloudflare Workers custom domains require an active Cloudflare zone. Before
the production switch:

1. add `abliterated.cloud` to the intended Cloudflare account;
2. reproduce every existing Porkbun DNS record in Cloudflare;
3. enable DNSSEC and update the Porkbun nameservers to Cloudflare;
4. confirm the zone is active before deploying the Worker;
5. run `npm run deploy:website:production`;
6. configure DNS-AID for the final hostname;
7. run `npm run verify:agent-ready -- https://abliterated.cloud`;
8. verify PageSpeed, Search Console, Rich Results and redirects separately.

A custom domain is required for root-level `/robots.txt`, `/.well-known/*`,
and the strongest agent-readiness result. GitHub project Pages serves the
temporary site below `/mn-uncensored/`.

## Agent-ready edge layer

Static GitHub Pages can publish discoverability files but cannot vary the
homepage response on `Accept: text/markdown` or add arbitrary HTTP response
headers. `website-worker.mjs` now provides:

- real Markdown content negotiation at `/`;
- `Link` and `Content-Signal` headers on every response;
- the correct `application/linkset+json` media type;
- OAuth and protected-resource discovery for public agent metadata;
- A2A, MCP, Agent Skills and WebMCP discovery;
- a real read-only MCP endpoint with `get_site_summary` and `list_models`;
- a public HTTP-signature directory tied to the owner's existing Ed25519
  public signing key.

DNS-AID and the final public score cannot be completed by application code.
They require the final custom hostname, DNSSEC and DNS records. The local gate
tests every application-controlled check before deployment.

The repository already publishes explicit Markdown alternatives so agents do
not need to scrape the visual page.

The site publishes truthful discovery resources at the paths used by current
agent tooling:

- `/.well-known/api-catalog`
- `/.well-known/agent-card.json`
- `/.well-known/agent-skills/index.json`
- `/.well-known/mcp/server-card.json`
- `/.well-known/oauth-authorization-server`
- `/.well-known/oauth-protected-resource`
- `/.well-known/webmcp.json`
- `/.well-known/skills/index.json` for legacy clients
- `/auth.md`
- `/openapi.json`

These resources resolve at the origin root after `abliterated.cloud` becomes
the Pages custom domain. The temporary project Pages URL cannot control the
root of `eminogrande.github.io`, which is why origin-based scanners cannot
award the final root-level checks there.

The extensionless API catalog follows RFC 9727's Linkset JSON structure. The
Worker explicitly serves it as `application/linkset+json`.

## Performance budget

- no third-party runtime requests;
- no framework or package install;
- no render-blocking JavaScript;
- one small deferred script;
- total uncompressed static payload target below 250 KB, excluding the OpenAPI
  and long-form agent text files that are not loaded by the homepage;
- zero layout shift from the logo;
- reduced-motion support;
- mobile-first responsive checks at 390, 768, and 1440 CSS pixels.
