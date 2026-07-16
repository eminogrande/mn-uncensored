# ABLITERATED.cloud website releases

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
