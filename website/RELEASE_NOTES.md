# ABLITERATED.cloud website releases

## website-v0.5.0

A brighter, narrower landing page with the clarity of a developer product,
the complete four-model catalog, and a lightweight animated brain.

### Changed

- Rebuilt the hero as one focused column followed by a wide point-cloud brain.
- Tightened the page to a 1040 px content grid, flatter borders, shorter
  sections, compact mono metadata, and large readable sans-serif headings.
- Added a visible **Star on GitHub** action while keeping Signal as the primary
  private-beta access path.
- Preserved every exact Hugging Face repository, model status, context,
  hardware, license, API ID, price, caveat, FAQ and integration detail.

### Performance and accessibility

- Implemented the brain with local Canvas code and no Three.js, CDN, webfont,
  analytics or other runtime dependency.
- Pause animation when it leaves the viewport or the tab is hidden, render at
  no more than roughly 30 frames per second, cap device pixel ratio at 2, and
  show a static frame for reduced-motion users.
- Retained the optimized owner-supplied brain artwork as the no-JavaScript and
  social-card fallback without preloading it on normal visits.

## website-v0.4.1

Fixed WebMCP discovery by registering the three public read-only catalog tools
with `navigator.modelContext` when a supporting browser or scanner exposes it.
The page remains dependency-free and never calls the inference API.

## website-v0.4.0

A quieter, larger-type landing page with readable model names, complete
Hugging Face repository identities, and the Agent-Ready Cloudflare edge layer.

### Changed

- Removed decorative API-window, badge, card and diagram treatments.
- Reorganized the page into a short explanation, three steps, four model rows,
  one API example, transparency notes, FAQ and access request.
- Made readable factual model names the headings, exact Hugging Face
  `owner/repository` paths the linked source field, and `mn/*` values the
  secondary API model IDs.
- Increased body, model, section and FAQ typography and whitespace.

### Agent readiness

- Added Markdown negotiation, discovery headers and exact media types through
  a Cloudflare Worker.
- Added OAuth, A2A, MCP, Agent Skills, WebMCP and HTTP-signature discovery.
- Added a local verifier for all application-controlled scanner requirements.
- Kept GitHub Pages as the public preview until the final domain moves from
  Porkbun DNS to an active Cloudflare zone with DNSSEC and DNS-AID.

## website-v0.3.0

A calmer, more powerful identity centered on “Intelligence, freed.”

### Changed

- Added the owner-supplied brain-and-broken-chains artwork as the responsive
  hero background, with optimized AVIF and WebP variants.
- Replaced the previous hero statement with “Intelligence, freed.” and the
  original prompt line “Ask anything. Think for yourself.”
- Simplified the palette, cards, borders, shadows, gradients, buttons, pricing,
  and closing section for a drier, more minimal interface.
- Added clearer background about why the service exists: exact checkpoint
  identity, reduced refusal behavior, operator-controlled lifecycle, public
  prices, and inspectable source.
- Changed every active access request from WhatsApp to Signal.
- Simplified public pricing to the four ABLITERATED.cloud prices without
  publishing markup or margin mechanics.
- Updated active Markdown, LLM, authentication, OpenAPI, social metadata, and
  discovery-facing documents to match.

### Current prices

- Qwen3.6 35B A3B: $5.45/hour
- Ornith 35B: $5.45/hour
- Qwythos 9B: $2.34/hour
- Ornith 397B W4A16: $10.90/hour

Automated billing is not live yet. The 397B route remains prepared for the next
budgeted runtime release.

## website-v0.2.0

Clearer model identity, free-weight explanation, SEO copy, and transparent
planned pricing.

### Changed

- Replaced shortened marketing names on all model cards with the complete real
  Hugging Face repository names.
- Added source-backed parameter counts, architectures, upstream context,
  licenses, multimodal/reasoning/tool-use metadata, and exact pinned-model
  links.
- Explained the differences between abliterated, uncensored, decensored, and
  the broader informal term jailbroken without promising zero refusals.
- Made the free/paid boundary explicit: weight files are publicly downloadable;
  managed cloud GPU inference costs money.
- Added per-model planned private-beta reference rates calculated as current
  Modal GPU list price multiplied by exactly 1.20.
- Kept the base GPU cost beside every planned rate and disclosed that billing,
  metering, payments, and invoicing are not implemented yet.
- Updated search, Open Graph, Twitter, JSON-LD, Markdown, LLM, FAQ, and social
  image copy.

### Planned reference rates

- `huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated`: $5.44752/hour
- `YuYu1015/YuYu1015-Ornith-1.0-35B-abliterated`: $5.44752/hour
- `huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated`:
  $2.34144/hour
- `cebeuq/Ornith-1.0-397B-abliterated-W4A16`: $10.89504/hour

These are not live customer charges.

## website-v0.1.0

Initial open-source GitHub Pages release.

### Added

- Original responsive ABLITERATED.cloud landing page inspired by the calm
  single-page product rhythm of receive.link without copying its GPL source,
  assets, fonts, icons, or text.
- Exact four-model catalog with Hugging Face links, status, context, hardware,
  and transparent Modal base GPU estimates.
- WhatsApp access requests through `wa.me/13103408213`.
- Dependency-free HTML, CSS, and a small deferred navigation script.
- Open Graph image, favicon, manifest, canonical URL, structured JSON-LD,
  semantic headings, FAQ markup, sitemap, and crawler policy.
- Agent resources: `index.md`, `llms.txt`, `llms-full.txt`, `auth.md`,
  OpenAPI, extensionless API catalog, security contact, and versioned and
  legacy Agent Skill discovery indexes.
- Signed branch-based GitHub Pages deployment isolated from Modal and
  model-release workflows.
- Automated checks for metadata, structured data, internal resources,
  WhatsApp links, secret safety, runtime dependencies, and payload budgets.

### Verified before deployment

- 60 repository tests passed.
- Secret scan passed.
- JSON, XML, YAML, and internal-resource validation passed.
- Desktop and responsive mobile renderings were visually inspected.
- Initial HTML, CSS, JavaScript, logo, and favicon total less than 125 KB.
- No analytics, third-party runtime resources, webfonts, API polling, or Modal
  calls are loaded by the homepage.
- The Pages deployment was built successfully from a signed `gh-pages` commit.
- The custom Actions workflow was removed after GitHub refused to start it due
  to an account billing lock; the verified classic Pages build is used instead.

### Domain

The initial deployment uses
`https://eminogrande.github.io/mn-uncensored/`. The intended later custom
domain is `https://abliterated.cloud/` after GitHub verification, Porkbun DNS
cutover, HTTPS provisioning, canonical URL migration, and live SEO validation.
