# ABLITERATED.cloud website-v0.6.0

A more recognizable interactive neural brain and a more explicit description
of the service in the hero.

## Changed

- Change the headline to **“Intelligence, freed: uncensored, private
  abliterated AI.”** with a smaller responsive second line.
- Replace the loose volumetric point cloud with a closed and smoothed lateral
  brain silhouette containing 420 deterministic nodes.
- Preserve a stronger outer contour while keeping the light, connected network
  treatment of the previous graphic.
- Divide the brain into local regions that illuminate their points and lines in
  cyan, magenta, lime, orange or violet under the pointer.
- Add pointer feedback even when reduced-motion mode renders a static frame.

## Performance and accessibility

- No Three.js, CDN, font request, analytics or inference API request is added.
- Animation still pauses offscreen and in hidden tabs, runs at roughly 30 FPS,
  and caps device pixel ratio at 2.
- The interaction is decorative and does not hide information from keyboard or
  assistive-technology users.

## Verification

- 65 repository tests pass.
- The secret scan passes.
- JavaScript syntax and repository diff validation pass.
- The local Agent-Ready verification passes.
- The Cloudflare Worker deployment dry-run succeeds.
- No Modal application is imported and no GPU is started.
