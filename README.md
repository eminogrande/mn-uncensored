# ABLITERATED.cloud website

This directory contains the dependency-free static landing page deployed with
GitHub Pages.

## Goals

- high PageSpeed performance without a build framework;
- complete semantic content in the initial HTML response;
- responsive and accessible design;
- exact model, status, price, and licensing transparency;
- agent-readable Markdown, `llms.txt`, OpenAPI, authentication, skill, robots,
  sitemap, and security resources;
- no analytics, advertising, external fonts, cookies, secrets, inference API
  calls, health polling, or Modal wake requests.

## Local preview

```sh
python3 -m http.server 4173 --directory website
```

Open:

```text
http://127.0.0.1:4173/
```

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

## Later custom domain

The intended domain is:

```text
https://abliterated.cloud/
```

Before switching:

1. verify `abliterated.cloud` in the owner's GitHub Pages settings;
2. set the repository Pages custom domain;
3. replace Porkbun parking records with GitHub Pages DNS records;
4. wait for certificate provisioning and enable HTTPS;
5. update canonical, Open Graph, sitemap, security, OpenAPI, skill, and LLM
   URLs from the temporary GitHub Pages URL to `https://abliterated.cloud/`;
6. test redirects, Search Console, PageSpeed Insights, Rich Results, and
   isitagentready.com.

A custom domain is required for root-level `/robots.txt`, `/.well-known/*`,
and the strongest agent-readiness result. GitHub project Pages serves the
temporary site below `/mn-uncensored/`.

## Agent-readiness limit on plain GitHub Pages

Static GitHub Pages can publish discoverability files but cannot vary the
homepage response on `Accept: text/markdown` or add arbitrary HTTP response
headers. A future Cloudflare layer in front of `abliterated.cloud` can provide:

- real Markdown content negotiation;
- `Link` discovery headers;
- `Content-Signal` headers;
- DNS-AID;
- Web Bot Auth.

The repository already publishes explicit Markdown alternatives so agents do
not need to scrape the visual page.

The static site also publishes truthful discovery resources at the paths used
by current agent tooling:

- `/.well-known/api-catalog`
- `/.well-known/agent-skills/index.json`
- `/.well-known/skills/index.json` for legacy clients
- `/auth.md`
- `/openapi.json`

These resources resolve at the origin root after `abliterated.cloud` becomes
the Pages custom domain. The temporary project Pages URL cannot control the
root of `eminogrande.github.io`, which is why origin-based scanners cannot
award the final root-level checks there.

The extensionless API catalog follows RFC 9727's Linkset JSON structure.
GitHub Pages may serve extensionless files with a generic media type; the
future custom-domain edge layer should explicitly return
`application/linkset+json`.

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
