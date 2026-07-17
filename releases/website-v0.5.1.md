# ABLITERATED.cloud website-v0.5.1

A simpler, more readable typography system inspired by Routstr's mono-first
presentation.

## Changed

- Use one Geist Mono-compatible local font stack for the complete page.
- Remove the separate sans-serif body and heading stack.
- Raise every fixed UI font size to at least 17 px, including navigation,
  buttons, labels, status lines, exact repository names, model facts, code,
  annotations and footer content.
- Give the header, controls, technical fact column and mobile brain annotation
  enough space for the larger text.

The page still uses no external font request or third-party runtime asset.

## Verification

- 64 repository tests pass.
- The typography regression test enforces the 17 px minimum and single stack.
- The secret scan passes.
- The local Agent-Ready verification passes.
- The Cloudflare Worker deployment dry-run succeeds.
- No Modal application is imported and no GPU is started.
