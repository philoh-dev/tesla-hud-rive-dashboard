# Bundled dashboard assets

These files are committed so this repository builds independently of T Hud's
firmware checkout. `manifest.json` records the SHA-256 values of the active
PNG assets, two fonts and font license.
`generate.py` references their actual repository-relative paths.

- Vehicle images in `vehicle/model-y-juniper-stealth-grey/`: project-local
  generated graphite crossover artwork. The
  `park.png` uses an elevated front three-quarter angle; `drive.png` uses
  the rear-elevated angle.
- Vehicle images in `vehicle/model-3-highland-stealth-grey/`: generated Highland
  sedan artwork from user-supplied references, with the same two camera roles.
- Blind-spot vehicles: shared directly under `assets/` for every ego vehicle
  design. Adjacent grey/red cars are exact mirrored pairs.
- Autopilot badge: project-local geometric artwork, not an enlarged manual
  bitmap. The blue badge is `#0071ff` with a white steering-wheel symbol.
- Fonts: Montserrat Light/Bold; see the bundled `fonts/OFL.txt`.

## Third-party turn signals

The turn-signal art was derived from Tesla's public owner's manuals. Copyright
and trademarks remain with Tesla, Inc.; these indicators are not covered by
the project's code license. The right arrow is a horizontal mirror of the left.
Prepared arrows were recolored bright green (`#35d774`) while retaining alpha.

Original left-arrow asset: `GUID-4B939373-7C8C-43B5-8577-087BC99AB167-online-en-US.png`.
Original public source pages:

- https://www.tesla.com/ownersmanual/modelx/en_pr/GUID-29A7E205-A689-41D1-B69C-3AE821CB70E7.html
- https://www.tesla.com/ownersmanual/models/en_us/GUID-1C209641-AA23-47AC-B0D1-3FE3779CF222.html

Bundling these files does not establish permission for redistribution in an
MIT-licensed contest entry. Obtain permission or replace them with original
artwork before submission. See `CREDITS.md` for further provenance.
