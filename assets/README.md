# Bundled dashboard assets

These files are committed so this repository builds independently of T Hud's
firmware checkout. `manifest.json` records the SHA-256 values of the active
PNG assets, three active Inter fonts and their font license.
`generate.py` references their actual repository-relative paths.

- Vehicle images in `vehicle/model-y-juniper-stealth-grey/`: project-local
  generated graphite crossover artwork. The
  `park.png` uses an elevated front three-quarter angle; `drive.png` uses
  the rear-elevated angle.
- Vehicle images in `vehicle/model-3-highland-stealth-grey/`: generated Highland
  sedan artwork from user-supplied references, with the same two camera roles.
- Vehicle images in `vehicle/model-y-legacy-deep-blue-metallic/`: dedicated
  generated pre-Juniper Model Y artwork based on user-supplied front/rear
  references, with Deep Blue Metallic paint, silver wheels and the original
  separate lamp clusters. Existing Juniper sprites guide camera and style only.
- Additional Highland directories `vehicle/model-3-highland-<paint>/` contain
  Pearl White Multi-Coat, Marine Blue, Diamond Black, Ultra Red and Quicksilver
  paint edits of those same Park/Drive views. Shared wheels, camera roles and
  dashboard layout are retained; each directory documents its prompt specifications.
- Vehicle images in `vehicle/model-y-legacy-pearl-white-multi-coat/`: generated
  Pearl White paint edits of the Legacy Park/Drive sprites, guided by the user's
  reference. Camera roles, silver wheels and shared blind-spot assets are retained.
- Vehicle images in `vehicle/model-y-legacy-midnight-silver-metallic/`: generated
  Midnight Silver Metallic paint edits of the Legacy Park/Drive sprites, guided
  by the user's reference and retaining the enlarged Legacy Drive scale.
- Vehicle images in `vehicle/model-y-juniper-white-multi-coat/`: generated white
  paint variants of the Juniper sprites, guided by user-supplied paint references.
- Vehicle images in `vehicle/model-y-juniper-diamond-black/`: generated Diamond
  Black paint variants of the Juniper sprites, guided by user-supplied references.
- Vehicle images in `vehicle/model-y-juniper-marine-blue/`: generated Marine Blue
  paint variants of the Juniper sprites, guided by the user's paint reference.
- Vehicle images in `vehicle/model-y-juniper-quicksilver/` and
  `vehicle/model-y-juniper-ultra-red/`: generated Quicksilver and Ultra Red paint
  variants, guided by the user's paint references.
- Blind-spot vehicles: shared directly under `assets/` for every ego vehicle
  design. Adjacent grey/red cars are exact mirrored pairs.
- Autopilot badge: project-local geometric artwork, not an enlarged manual
  bitmap. The blue badge is `#0071ff` with a white steering-wheel symbol.
- Fonts: Inter Regular/Medium/SemiBold; see `fonts/Inter-OFL.txt`.

## Original vector turn signals

`generate.py` draws a conventional seven-vertex filled arrow from independently
authored coordinates, with lightly rounded corners. The right arrow mirrors
the left. Both retain green `#35d774` and the existing off/dim/bright bindings.
These paths are embedded as vectors in each `.riv`; no turn-signal PNGs or
Tesla-downloaded indicator artwork are bundled. See `CREDITS.md`.
