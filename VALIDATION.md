# Rive validation — 19 October 2026

Status: **not fully passing**. Local CLI rendering only; no Android/iOS device
validation or device-FPS claim.

## Passing

- Rive CLI 1.6.0 verification and compilation, no warnings/errors.
- 24 standard-library regression tests (including per-vehicle asset selection,
  unchanged shared layout/bindings, rejection of unknown vehicles, the standalone checksum
  manifest, named design-export path, Linux CI library setup and four installer
  safety checks).
- Both Model Y Juniper and Model 3 Highland exports verify and build under
  the 5 MB limit. Highland Park, dark Drive and light Drive previews were
  rendered and visually checked; the runtime checks listed below predate
  this asset-only variant and were not all rerun for Highland.
- Runtime Park/Drive switching, R/N ego image, rapid return, hidden Park road
  and speed/power instruments. The comparison now excludes direction arrows,
  which intentionally differ between stopped D, R and N.
- Left/right/center anchors at 1440, 1800 and 2340 × 1080 in Park and Drive.
- Exact dark/light background, speed, road, sign face, power-track/fill, gear,
  battery label/interior/green charge colors; assist blue and live theme changes.
- Forward/reverse departure travel, decreasing opacity, disappearance after
  24 frames at 60 Hz, stopping/reset, repeated speed updates, no entrance flash
  when already moving, no cue in N/unknown, and both themes.
- Road stopped at zero speed, visible movement and proportional-speed capture
  comparison before the mph assertion.

## Unresolved

`python3 validate_road.py` fails the equivalent physical-distance comparison
between 43.2 km/h and 43.2 / 1.609344 mph. The formula itself evaluates to the
same rate, but rendered lane positions differ. This persisted when telemetry
defaults were seeded together rather than supplied through sequential CLI data
writes. Do not assume this is only capture startup or only a test issue.

The failing captures are under `build/road-validation/` (`moving-later.png` and
`mph.png`). The assertion is retained. The later Neutral assertion is not
reached by that run. Native runtime reverse motion and exact wrap continuity
have not been independently signed off; the unit tests check the direction
formula and authored geometry, not native device playback.

Speculative playback-start and converter-input changes did not resolve the
failure and were reverted; this validation has not introduced a road fix.

## Reproduce

```sh
python3 build.py
python3 -m unittest discover -s . -p 'test_*.py'
python3 validate_states.py
python3 validate_layout.py
python3 validate_theme.py
python3 validate_departure.py
python3 validate_road.py
```

Runtime scripts require Pillow and a working graphics context. Fixture-only
controls and diagnostic readouts are never included in the production `.riv`.
