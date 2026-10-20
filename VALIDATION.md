# Rive validation — 20 October 2026

Status: **not fully passing**. Local CLI rendering only; no Android/iOS device
validation or device-FPS claim.

## Steering curve — all vehicle exports

All thirteen vehicle `.riv` files under `dashboard/` have been built with the
same steering implementation as the initial Model Y Juniper Stealth Grey test
export. Every export passes CLI verification and compilation and remains below
the 5 MB limit. The steering rollout did not modify existing vehicle artwork or
committed screenshots. The standard-library suite passes all 41 tests, including the check
that vehicle variants differ only in their selected Park/Drive image assets.

`validate_steering.py` passes in the native renderer: negative/positive steering,
increasing and bounded bend, ±2° dead zone, actual live smoothing and return to
straight, direction reversal, moving/stopped dashes, unchanged nearby road/car
and footer, both themes and assist states, hidden Park road, and landscape
phone widths of 2340 and 2520 at normalized height 1080. A live 60° step reaches
normalized bend 0.0915 / 0.2746 / 0.6591 after 1 / 3 / 12 frames, confirming the
0.12-second interpolation rather than an instantaneous jump.

Park/gear states, live assist/cruise, exact theme colors/live changes and departure
cues were rerun and pass. The road's stopped, moving and proportional-speed
assertions pass, but the existing equivalent km/h-versus-mph comparison still
fails. The native steering checks used the default Model Y Juniper Stealth Grey
design; they were not separately repeated for each artwork variant. No
Android/iOS steering or performance validation is claimed.

## Model Y Legacy Deep Blue Metallic

Added a separate vehicle design with dedicated pre-Juniper Park and Drive
sprites generated from the user's two references. Asset checksums, RGBA PNG
format and shared sprite dimensions are covered by the regression suite.
The remaining twelve vehicle exports were not rebuilt for this asset-only
addition; the new export verifies and compiles at 1,287,484 bytes.

Dark Drive, light Drive and dark Park documentation captures were rendered and
visually checked. The Legacy artwork retains separate headlights/rear lamp
clusters and silver wheels; generic blind-spot cars, layout, theme, telemetry
and steering-responsive road are shared. This brings vehicle documentation
coverage to 39 captures across 13 designs. No additional phone or performance
validation is implied, and the existing unresolved issues below remain.

## Passing

- Rive CLI 1.6.0 verification and compilation, no warnings/errors.
- Optical alignment measured in the approved 1800×1080 dark preview at 130:
  the complete set-speed value + MAX block and the speed-limit sign each have
  a visible vertical center of 181 px. Current speed retains its 180.5 px
  glyph center (approximately 181 px), position, size and tight inline unit.
- 41 standard-library regression tests (including the separate Legacy model,
  RGBA sprite dimensions, signed/clamped steering,
  native smoothing and phase-clock bindings, near-road anchoring, optical speed-readout alignment,
  inline speed-unit spacing,
  matching car/phone battery
  typography, grouped odometer bindings,
  absence of a car-identification icon,
  car/phone battery widgets,
  unchanged power-rail position, cruise host fields/visibility
  conditions and approved Inter font weights, flat Autopilot Boolean bindings,
  shorter turn-signal shafts/larger arrowheads, all Highland paint registrations,
  original mirrored vector
  turn signals and off/dim/bright states, per-vehicle asset selection,
  unchanged shared layout/bindings, rejection of unknown vehicles, the standalone checksum
  manifest, named design-export path, Linux CI library setup and four installer
  safety checks).
- Model Y Juniper Stealth Grey, White Multi-Coat, Diamond Black, Marine Blue,
  Quicksilver and Ultra Red, plus Model 3 Highland Stealth Grey, Pearl White
  Multi-Coat, Marine Blue, Diamond Black, Ultra Red and Quicksilver exports
  verify and build under the 5 MB
  limit. Highland and all added Juniper paint variants' Park, dark Drive and
  light Drive previews were
  rendered and visually checked; the runtime checks listed below predate
  these asset-only variants and were not all rerun for them.
- All twelve exports built with original vector turn signals. Refreshed all
  README captures; visually checked the bright left arrow and dim-left/bright-right
  combination in the real renderer. Retired bitmap indicators are no longer embedded.
- Cruise set speed and MAX caption next to the speed limit: a direct native
  range-mapper binding shows positive `accSetSpeed`, independently of assist flags.
  Zero/negative speeds hide it; live updates redraw the value. `adasOn` changes
  only the caption color. Native checks cover both themes, assist on/off/handoff,
  and operation with an idle-only state machine, matching `dash_demo.riv`'s direct
  visibility approach. This replaces the previous assist visibility transitions.
  Turn-signal shafts are 14 pixels thick while staying 9 pixels long.
- The five additional Highland colors each have Park, dark Drive and light
  Drive captures. Park and light Drive captures were visually checked for
  layout/vehicle identity; no new Android/iOS or performance validation is implied.
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

- Battery widget runtime checks pass for 0%, 78%, 100% and unknown phone
  battery, live phone charge changes, hide/show settings and independence from
  the car battery in both themes. Phone battery now shares the gear's right-edge
  anchor; car battery stays left without a separate car icon or reserved icon gap.
  Theme-color and left/right/center anchor
  checks rerun at 1440, 1800 and 2340 widths after adding the icons/widgets.
- Odometer runtime checks pass for live thousand/million boundaries, show/hide,
  muted km suffix and imperial-to-km conversion. These and the runtime theme/layout
  checks passed before increasing the phone percentage from 16 to 18 pixels.
  The matching battery typography is covered by regression tests and rebuilt
  exports. On 20 October, all 36 documentation captures (12 vehicles × dark
  Drive, light Drive and dark Park) were regenerated from the current source,
  including the matching battery typography, right-side phone widget and
  `123.456km` odometer. Documentation image links and capture coverage were
  checked; this screenshot refresh does not resolve the runtime issues below.

## Unresolved

Automatic Android phone-theme following is a host integration issue, not fixed
by the font update. The inspected upstream Android `ConnectionViewModel` loads
`darkMode` from a saved app preference; the dashboard settings UI hides controls
not declared by the selected dashboard manifest. The `.riv` cannot read the
phone's system theme itself. Actual-renderer checks pass for initial dark/light
values and live `darkMode` switching, including Inter typography. No Android
app was modified; a host update is required to resolve system night mode and
forward it. See `docs/DEVELOPMENT.md` for the inspected upstream source links.

The reported missing Autopilot badge and blue lanes in the DashPilot phone app
could not be reproduced in the CLI: both the previous binding and the simplified
binding pass local live-update checks. Both visuals now use the same flat
Boolean → string → number converter as the official DashPilot Rive example,
removing nested groups and an identity formula from the engagement path.
`validate_assist.py` checks initial off/on, off→on, on→off and repeated toggling
for the badge and nested road lanes in dark and light mode. Reimporting the new
export and confirming live phone operation is still required; this change is
not evidence that the phone receives `adasOn=true` from its data source.

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
python3 validate_assist.py
python3 validate_batteries.py
python3 validate_layout.py
python3 validate_theme.py
python3 validate_departure.py
python3 validate_steering.py
python3 validate_road.py
```

Runtime scripts require Pillow and a working graphics context. Fixture-only
controls and diagnostic readouts are never included in the production `.riv`.
