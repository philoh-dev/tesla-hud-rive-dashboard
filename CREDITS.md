# Assets and provenance

Model Y Stealth Grey vehicle PNGs are byte-for-byte copies of T Hud's existing, project-local
generated artwork originally under the firmware's `assets/vehicles/prepared/`.
They are bundled locally; no firmware checkout is required. See
[assets/README.md](assets/README.md) and [assets/manifest.json](assets/manifest.json).
The static Park/Drive endpoint images are unchanged. Abandoned turnaround
atlases, intermediate-angle images and their preparation script were removed;
none of those assets are part of this repository or the dashboard export.

Model 3 Highland Stealth Grey artwork in
`assets/vehicle/model-3-highland-stealth-grey/` was generated with the built-in
image generator from user-supplied front and rear vehicle references, using
the existing Model Y assets only as camera-angle/style references. These are
illustrative renders, not official Tesla assets or dimensionally exact models.
Tesla names and vehicle designs belong to their respective rights holders.
The final prompt specifications are recorded in
`assets/vehicle/model-3-highland-stealth-grey/README.md`.

Model Y Juniper White Multi-Coat artwork in
`assets/vehicle/model-y-juniper-white-multi-coat/` was generated with the built-in
image generator by recoloring the existing Juniper sprites, with user-supplied
white Juniper images as paint references. The same illustrative-render and
trademark caveats apply. Final prompt specifications are recorded in that
directory's `README.md`.

Model Y Juniper Diamond Black artwork in
`assets/vehicle/model-y-juniper-diamond-black/` uses the same built-in
image-generator recoloring workflow, with the user's Diamond Black Juniper
references guiding the paint. It retains the shared Juniper camera/style.
Prompt specifications are recorded in that directory's `README.md`; these
are illustrative renders, not official Tesla artwork.

Model Y Juniper Marine Blue artwork in
`assets/vehicle/model-y-juniper-marine-blue/` was recolored using the built-in
image generator from the existing Juniper sprites, guided by the user's Marine
Blue reference. Prompt specifications are recorded in that directory's
`README.md`. These are illustrative renders, not official Tesla artwork.

Model Y Juniper Quicksilver and Ultra Red artwork in
`assets/vehicle/model-y-juniper-quicksilver/` and
`assets/vehicle/model-y-juniper-ultra-red/` uses the same built-in image-generator
paint-edit workflow. User-supplied references guide paint color; the existing
Juniper sprites guide camera, shape and style. Each directory records its prompt
specifications in `README.md`. These are illustrative renders, not official
Tesla artwork.

Additional Model 3 Highland paint variants (Pearl White Multi-Coat, Marine
Blue, Diamond Black, Ultra Red and Quicksilver) are built-in image-generator
paint edits of the existing Highland sprites. User-supplied references guide
paint only; the existing sprites guide camera, shape and wheels. Each
`assets/vehicle/model-3-highland-<paint>/README.md` records its prompt
specifications. These are illustrative renders, not official Tesla artwork.

Montserrat Light/Bold were copied from the firmware's `assets/fonts/` and redistributed
under the accompanying SIL Open Font License in `fonts/OFL.txt`.

The road-scene Autopilot badge is T Hud's existing project-local geometric
artwork, originally prepared by the firmware's `scripts/prepare_indicator_assets.py`.

Turn signals are original geometric vector paths authored in `generate.py`
(`turn_signal_points`), using a conventional filled arrowhead and rectangular
shaft with lightly rounded corners. The right arrow mirrors the left geometry.
No Tesla-downloaded turn-signal PNGs are bundled or embedded in current exports.

The Rive port does not copy DashPilot's demo artwork. It uses the published
`DashViewModel` property names to interoperate with that host.
