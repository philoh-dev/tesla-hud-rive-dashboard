# Assets and provenance

Model Y vehicle PNGs are byte-for-byte copies of T Hud's existing, project-local
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

Montserrat Light/Bold were copied from the firmware's `assets/fonts/` and redistributed
under the accompanying SIL Open Font License in `fonts/OFL.txt`.

The road-scene Autopilot badge is T Hud's existing project-local geometric
artwork, originally prepared by the firmware's `scripts/prepare_indicator_assets.py`.

The two turn-arrow PNGs are copied from the existing Tesla-owner-manual-derived
prepared indicators. Their original source attribution and rights notice are
in [assets/README.md](assets/README.md): rights remain with Tesla, Inc.; they are
not covered by the project's license. Their reuse here does **not** establish
permission for redistribution in an MIT-licensed contest entry. Obtain suitable
permission or replace them with original artwork before contest submission.

The Rive port does not copy DashPilot's demo artwork. It uses the published
`DashViewModel` property names to interoperate with that host.
