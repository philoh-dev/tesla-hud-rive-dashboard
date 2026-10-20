# Rive validation — 20 October 2026

Status: **not fully passing**. Local CLI rendering only; no Android/iOS device
validation or device-FPS claim.

## Passing

- Rive CLI 1.6.0 verification and compilation, no warnings/errors.
- 35 standard-library regression tests (including matching car/phone battery
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
- Cruise set speed and MAX caption next to the speed limit: either `adasOn` or
  `selfdriveActive` enables it, zero/unknown set speed hides it, and live set-speed
  changes redraw the value. Native renderer checks cover both themes and assist
  handoff with one flag remaining true. Visibility uses explicit Boolean state
  transitions after a combined formula failed the off-state renderer test.
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
python3 validate_road.py
```

Runtime scripts require Pillow and a working graphics context. Fixture-only
controls and diagnostic readouts are never included in the production `.riv`.
