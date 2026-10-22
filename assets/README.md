# Bundled dashboard assets

These files are committed so this repository builds independently of T Hud's
firmware checkout. `manifest.json` records the SHA-256 values of the active
PNG assets, three active Inter fonts and their font license.
`generate.py` references their actual repository-relative paths.

Drive artwork now follows the approved, slightly lower rear camera, retaining
each vehicle design and paint. Park artwork retains its existing view. Shared
blind-spot cars follow the refined Juniper camera elevation.
See [Drive camera and prompt specifications](DRIVE-ANGLE.md).

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
- All five additional Juniper paints use deterministic paint-only recolors of
  the approved Stealth Grey Park, rear chase and intermediate steering assets.
  `recolor_juniper.py` preserves every alpha pixel and canvas dimension; shared
  paint masks protect glass, lamps, tires and trim. Stealth Grey PNGs are unchanged.
  Full sources are in each paint directory and compact derivatives are in
  `optimized/model-y-juniper-*/`. Older `drive.png` files remain reference artwork;
  active dashboards use `drive-chase.png` plus the intermediate steering pose.
- Juniper blind-spot vehicles share Stealth Grey's projected grey/red sprites
  and the narrower/wider angle variants. Warning artwork tints every surface red,
  including glass and tires, with darker/lighter red for contrast. Right-side
  cars mirror the inner-flank view. Other vehicle families retain their original
  shared blind-spot assets.
- Autopilot badge: project-local geometric artwork, not an enlarged manual
  bitmap. The blue badge is `#0071ff` with a white steering-wheel symbol.
- Fonts: Inter Regular/Medium/SemiBold; see `fonts/Inter-OFL.txt`.

## Original vector turn signals

`generate.py` draws a conventional seven-vertex filled arrow from independently
authored coordinates, with lightly rounded corners. The right arrow mirrors
the left. Both retain green `#35d774` and the existing off/dim/bright bindings.
These paths are embedded as vectors in each `.riv`; no turn-signal PNGs or
Tesla-downloaded indicator artwork are bundled. See `CREDITS.md`.
