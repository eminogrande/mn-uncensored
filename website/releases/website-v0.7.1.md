# ABLITERATED.cloud website-v0.7.1

This release makes `https://abliterated.cloud/` the canonical production
address of the GitHub Pages website.

## Custom domain

- GitHub Pages is configured with the apex custom domain
  `abliterated.cloud`.
- Porkbun remains the authoritative DNS provider; only the parking records
  were replaced.
- The apex uses GitHub's four official IPv4 and four official IPv6 Pages
  targets.
- `www.abliterated.cloud` points directly to `eminogrande.github.io` and is
  handled by GitHub Pages.
- The repository contains the matching `website/CNAME` deployment artifact.

## Canonical production URLs

- Canonical, Open Graph, Twitter card, Schema.org, sitemap, robots, `llms.txt`,
  and Agent Skill references now use `https://abliterated.cloud/`.
- The old GitHub project URL is no longer advertised as the canonical origin.

## Operational clarity

- The website guide records the exact DNS layout and verification commands.
- GitHub's certificate-provisioning window is documented explicitly.
- The live static GitHub Pages deployment is distinguished from the optional
  prepared Cloudflare Worker; this release does not deploy Cloudflare.

## Safety

This release does not deploy Modal applications, download model weights, wake
an inference endpoint, or start a GPU.

## Verification

- Full Python test suite
- JavaScript syntax validation
- Secret scan
- Local Agent-Ready verification
- JSON and Agent Skill digest validation
- Public DNS and GitHub Pages custom-domain checks
