# Development

Run commands from this standalone repository's root. No parent firmware
repository is needed; all active images and fonts are bundled.

## Build

Requires Python 3 and official Rive CLI **1.6.0**. Set `RIVE_CLI` to a custom
executable, or place it at `.tooling/rive` (`.exe` on Windows), or on PATH.

```sh
python3 build.py
python3 -m unittest discover -s . -p 'test_*.py'
```

The build generates and verifies each vehicle scene, compiles all supported
dashboards and checks the 5,000,000-byte limit per export. Distributables are
`dashboard/<vehicle-design>.riv`; intermediate files stay under
ignored `build/`. The export embeds fonts and images and contains no runtime
scripts. No Rive login is required for these unsigned local builds.

Use `--vehicle model-3-highland-stealth-grey` with `build.py` or
`render_previews.py` to select one design. Use
`--vehicle model-y-juniper-white-multi-coat` for the white Juniper or
`--vehicle model-y-juniper-diamond-black` for Diamond Black, or
`--vehicle model-y-juniper-marine-blue` for Marine Blue. Quicksilver and Ultra Red
use `--vehicle model-y-juniper-quicksilver` and
`--vehicle model-y-juniper-ultra-red`. Without a flag, both scripts
process every entry in `generate.VEHICLES`. All Model Y Juniper paints use the Stealth Grey template layout, road
geometry, road playback bindings and mirrored blind-spot sprites, retaining
their own Park/Drive artwork. Other vehicle families retain their existing
layout and shared blind-spot assets. Both scripts restore canonical Model Y `scene.rml` in a `finally`
block, so build order does not change the committed default source.

The pre-Juniper Model Y in Deep Blue Metallic uses
`--vehicle model-y-legacy-deep-blue-metallic`. Its Park and Drive artwork is
separate from Juniper artwork; layout, telemetry and blind-spot vehicles remain
shared.

Highland paint variants use the same flags with IDs
`model-3-highland-pearl-white-multi-coat`, `model-3-highland-marine-blue`,
`model-3-highland-diamond-black`, `model-3-highland-ultra-red` and
`model-3-highland-quicksilver`.

The internal artboard is currently named `Newhaven` (see `rive.yaml`). Its
1800 Ã— 1080 dimensions are authoring coordinates, not a fixed output resolution.
DashPilot's normalized 1080-unit height preserves artwork size while Layout fit
reflows the width. Main/status regions use a 4:1 height split. Speed, power and
battery stay left; speed limit and gear stay right; road, blind-spot vehicles
and Autopilot remain center-relative. Contain/Cover scale or crop the canvas
instead of reflowing it.

Current speed and its muted unit are styled runs in the same text line, with
one thin space between them. This replaces the old digit-count positioning
formula and keeps km/h or mph directly beside the rendered digits. The numeric
font remains Inter Regular 110; the inline unit compensates for line fitting
to preserve the approved visible size.
Current speed and the speed-limit sign are optically centered at approximately
y=181 in the 1080-unit artboard. The set-speed value and MAX caption are treated
as one block, with that whole block centered vertically on the speed-limit sign.
Their different font sizes require different text-box offsets; aligning the
boxes alone does not align the visible content.

## Actual renderer checks

Requires Pillow and a working graphics context:

```sh
python3 validate_states.py
python3 validate_assist.py
python3 validate_batteries.py
python3 validate_layout.py
python3 validate_theme.py
python3 validate_departure.py
python3 validate_steering.py
python3 validate_road.py
```

Fixtures and diagnostic controls live only under ignored `build/`; they are not
shipped in the dashboard. See [VALIDATION.md](../VALIDATION.md) for the unresolved
km/h-versus-mph road-playback comparison and limits of current testing.

## README images

Regenerate the committed screenshots from the current Rive source:

```sh
python3 render_previews.py
```

This requires the Rive CLI and a graphics context. Outputs under
`docs/images/<vehicle-design>/` are actual Rive renders with fixed
demo telemetry, not in-car captures or conceptual mockups. Driving previews
show 130 km/h, a 130 km/h speed limit, left turn intent and both occupied blind
spots. Dark mode shows Autopilot active; light mode shows neutral lanes.
All three states show the current footer: 51% car battery, `123.456km`
odometer and 78% phone battery beside the gear. Both battery percentages use
the same 18-pixel Inter Medium typography.

## Data bindings

The host binds `DashViewModel`; the dashboard itself does not connect to BLE or
decode CAN frames. Speed and speed limit arrive in the selected display units.
Road animation converts mph to physical km/h internally.

- `egoSteeringAngle` (Number): steering-wheel degrees, negative left and
  positive right. The road ignores the central Â±2Â°, reaches its bounded bend
  at Â±90Â°, and smooths changes over 0.12 seconds with a native Rive converter.
  Distant lane markings follow a quadratic curve; the near road, ego car,
  blind-spot vehicles and instruments stay anchored. This is a steering-based
  illustration, not detected road geometry or a predicted driving path.
  Private `_roadPhase` and `_roadBend` fields are maintained by the animation;
  the host must not write them. A single phase clock moves every dash along
  the curve at the existing speed-dependent rate, without smoothing speed.
  All thirteen vehicle exports include this shared implementation. Native
  steering checks use the default Model Y Juniper Stealth Grey artwork;
  per-vehicle tests verify that only the selected Park/Drive assets differ.
  Documentation images remain unchanged; phone validation is separate.
- `gear`: 0 unknown, 1 P, 2 R, 3 N, 4 D.
- `leftBlinker` / `rightBlinker`: 0 off, 1 dark phase, 2 bright phase.
- Blind-spot vehicles are grey for occupancy and red for matching turn intent,
  including the blink's dark phase.
- `adasOn` (Boolean): blue road lines and Autopilot badge. Both use the flat
  Boolean â†’ string â†’ number converter from DashPilot's reference dashboard,
  without wrapping it in another group or an identity formula. Runtime checks
  cover initial off/on, engagement, disengagement and re-engagement in both themes.
  This verifies rendering when the host supplies the flag, not live CAN delivery.
- `accSetSpeed` (Number): cruise set speed in the host's selected display units,
  shown immediately left of the speed-limit sign whenever positive, independently
  of `adasOn` and `selfdriveActive`. Unknown,
  zero and negative values are hidden; the speed-limit sign remains independent.
  Its value uses Inter Regular, matching current speed. Labels use Inter Medium;
  speed-limit digits and the MAX caption use Inter SemiBold.
  Like DashPilot's `dash_demo.riv`, a direct native range mapper clamps the value
  to 0â€“1 for opacity, without a formula or visibility state-machine transitions.
  `adasOn` changes only the MAX caption color: blue when true, muted when false.
  Checks include rendering with both assist flags off and with an idle-only state
  machine, without any assist visibility transitions.
- `powerLevel`: signed normalized power/recuperation percentage supplied by
  the host. Battery percentage uses floor rounding of usable energy.
- `darkMode`: live theme selection, default dark. `darkModeBackgroundGray` is
  exposed for compatibility but deliberately ignored to keep OLED black.
- `dataSourceType`: source identity, not a BLE connection-health indicator.
- `phoneBattery` (Number): phone charge percentage, clamped to 0â€“100 and
  floored for display. Zero is valid; negative/unavailable values hide the
  entire phone widget. `showPhoneBattery` (Boolean) independently controls
  its visibility using a flat Boolean binding. The car widget retains
  `showCarBattery` and usable-energy calculation. Car battery has no separate
  car icon; the phone widget uses an original vector phone outline. Car battery stays left; phone
  battery is right-anchored immediately left of the gear.
  Both battery percentages and percent signs use Inter Medium at 18 native pixels.
  The power/recuperation rail has not moved.
- `odometer` (Number) and `showOdometer` (Boolean): a whole-kilometre reading
  immediately after the car battery percentage, e.g. `123.456km`. Dot separators
  group every three digits; subsequent groups are zero-padded (`1.000.005km`).
  The inline km suffix has lower contrast in both themes. Negative/unavailable
  values hide the reading. The host's imperial odometer is converted back using
  its `0.621371` factor before flooring; this readout deliberately remains km.
  Separate metric/imperial branches and 1â€“4-group text runs avoid scripts and
  provide live visibility/format changes without a host-side formatted string.

### Android system-theme limitation

The Rive file can only follow the host's `darkMode` Boolean; it cannot read
Android's system setting. In the inspected DashPilot Android main source,
`ConnectionViewModel` loads `darkMode` from `PREF_DARK_MODE`, not Android's
`uiMode`. `SettingsScreen` only displays its Dark mode control when the selected
dashboard manifest declares that setting, which can leave imported dashboards
without a visible control. Fixing automatic phone-theme following requires a
DashPilot host change (observe system night-mode changes and publish the resolved
Boolean through DisplaySettings/DashViewModel), not another `.riv` property.
See the upstream [settings implementation](https://github.com/softwiredtech/dashpilot/blob/main/dashpilot-android/app/src/main/java/com/softwiredtech/dashpilot/ui/SettingsScreen.kt)
and [display-settings loading](https://github.com/softwiredtech/dashpilot/blob/main/dashpilot-android/app/src/main/java/com/softwiredtech/dashpilot/viewmodel/ConnectionViewModel.kt).

Dark mode uses `#000000`; light mode uses `#ffffff`. Light-mode neutral lanes,
the sign face, power track and empty battery interior use `#ecf0f1`. Current
speed, power fill, gear and battery percentage use `#2d3436`. Recuperation and
battery charge stay green. Autopilot lanes stay blue in both themes.

Park/Drive car views switch instantly. Park hides road and speed/power
instruments. Stopped D/R show perspective direction cues, with the closer
Reverse cue larger. On departure, the cue travels 40 native pixels and fades
from 30% opacity over 0.4 seconds, resetting when stopped. The static Park car
does not rotate or animate.

Turn signals are original vector paths generated by `turn_signal_points` in
`generate.py`, not PNG assets. Their 32 Ã— 36 native-pixel outline has a
9-pixel-long, 14-pixel-thick shaft and a larger 23 Ã— 36 arrowhead (previously 17 Ã— 30).
They retain mirrored geometry and existing off/50%-opacity/100%-opacity bindings.

## GitHub Actions

[Dashboard CI](../.github/workflows/dashboard.yml) runs on pushes, pull requests
and manual dispatch with an `ubuntu-24.04` x86_64 runner and read-only token.
It runs regression tests before regeneration, installs the pinned CLI and its
EGL/GLES, X11/Wayland, C++ and zlib runtime libraries, verifies/builds the RML,
checks export size and uploads the dashboard, source and checksum for 30 days.

CLI archive SHA-256 verification is implemented in
[ci/install_rive_cli.py](../ci/install_rive_cli.py). There is no publishing,
login, remote creation or automatic commit. Portable CI does not run the GPU
checks and does not clear known runtime failures or certify phone performance.

### MYJ SG reviewed road projection

`python build.py --vehicle model-y-juniper-stealth-grey` includes the reviewed low-angle road and adjacent vehicles through `myj_projection.py`. Adjacent vehicles stay at fixed projected depth, closer to the inner boundaries; detection changes only fade opacity over eight frames. The road keeps its speed and steering bindings. Other designs retain their existing geometry. Sprite contact metrics are baked from the approved alpha silhouette, keeping builds stdlib-only.

### Curved road and angle-specific vehicle views

MYJ SG projects a smooth ground-space arc before drawing the lanes:
`x(d) = bend * (heading*d + 0.5*acceleration*d*d/(1+max(0,d)/depthScale))`.
The acceleration coefficient is 0.0024. The horizon shifts in the turn direction,
up to 20% of the native canvas width. Inner and outer boundaries and adjacent
vehicle anchors use the same path and unit-normal lane offsets. The analytic
slope keeps curvature and heading continuous toward the horizon.

`vehicle_angles.py` selects actual angle-specific sprites after projection;
vehicle images are never rotated or opacity-crossfaded. The approved ego view
is `ego-back-left-middle.png`, mirrored for the opposite turn. Its angle lies
between the straight rear view and the original angled reference. Adjacent
vehicles use narrower/wider inner-flank views. Five additional PNGs and baked
`view-angles/geometry.json` measurements keep builds stdlib-only. Ground shadows
retain their flat-road orientation. The default MYJ SG export is about 4.40 MB.

Build with `python build.py --vehicle model-y-juniper-stealth-grey`.

### Asset-preserving road texture dynamics

`road_dynamics.py` adds speed-scaled sine vibration only to the two MYJ SG blind-spot vehicle bodies, capped at 0.5 output pixels at the 1800x1080 design viewport. The projected depth scale is compensated so the amplitude stays consistent through curves. Frequency is four cycles per 12 m of road travel. Ego body and all contact shadows stay steady. Effects return to baseline at zero speed or outside Drive/Reverse. Typed units conversion matches the existing metric/imperial road clock; all lane dashes share that clock. No vehicle artwork is modified.

### Exclusive angle poses (overlap fix)

`vehicle_angles.py` now puts each vehicle's three views inside a native Solo. A state-machine layer selects a child with a held ID keyframe and zero-duration transitions, guaranteeing only one silhouette is rendered. Angled poses use raw `egoSteeringAngle` only above +50 or below -50 degrees; the inclusive [-50, 50] range selects the straight view. Direct opposite-turn selection is supported. Parent gear/occupancy/warning gates, curved anchors and road-texture vibration are retained. Regression coverage checks mutually exclusive transition conditions, exact steering thresholds and absence of per-pose opacity blending.

Ego angle sprites match the straight rear view's 875-source-pixel opaque body height with uniform scaling, while retaining the same rear tire baseline. This avoids the previous width-only normalization shrinking the angled body vertically.

The MYJ SG ego body and contact shadow sit 20% of the visible ego body height lower (about 45.4 pixels at 1800x1080). Road projection and adjacent vehicle anchors retain their existing calibration via ROAD_CONTACT_Y. Both ego pose variants share this offset.

### Compact export packaging

`build.py` compiles an isolated `build/compact-export` project prepared by
`optimize_export.py`. It embeds committed Inter font subsets and a 640x585 ego
image from `assets/optimized`, while leaving editable source assets and canonical
`scene.rml` intact. Image scale compensation preserves the original displayed
dimensions, position and contact baseline, including the universal dashboard.
The MYJ SG output is 2,697,844 bytes, down 38.7% from 4,404,728 bytes. See
`assets/optimized/README.md` for coverage, licenses and derivative regeneration.
