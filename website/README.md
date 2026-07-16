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

The workflow in `.github/workflows/pages.yml` publishes this directory.
GitHub Pages does not run the Modal deployment or model release scripts.

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
