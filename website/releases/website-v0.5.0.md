# ABLITERATED.cloud website-v0.5.0

A cleaner, brighter ABLITERATED.cloud landing page with an independently
implemented developer-product layout and an animated point-cloud brain.

## Changed

- Narrow the content grid, flatten the visual hierarchy, shorten section
  spacing, and use compact mono typography for navigation and technical data.
- Replace the two-column photographic hero with one focused message, Signal
  and model actions, and a wide abstract brain visualization.
- Add a visible **Star on GitHub** action in the desktop header and preserve
  both GitHub and Signal destinations in mobile navigation.
- Keep all four human-readable model names, exact linked Hugging Face
  repositories, API identifiers, prices, status, hardware, context, licensing,
  commercial caveats, FAQs and client-integration guidance unchanged.

## Animation, accessibility and performance

- Generate the brain locally with a deterministic Canvas point cloud and no
  Three.js, CDN, external font, analytics or API request.
- Pause rendering when the visual is offscreen or the tab is hidden, throttle
  active animation to roughly 30 frames per second, and cap pixel density at 2.
- Respect `prefers-reduced-motion` with a static frame and retain the optimized
  owner-supplied AVIF as the no-JavaScript fallback.
- Remove the old hero-image preload from the critical rendering path.

## Verification

- 63 repository tests pass.
- The secret scan passes.
- JavaScript syntax and the repository diff pass validation.
- The Cloudflare Worker deployment dry-run succeeds.
- No Modal application is imported and no GPU is started.
