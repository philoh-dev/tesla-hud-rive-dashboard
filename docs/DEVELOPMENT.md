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
process every entry in `generate.VEHICLES`. Vehicle selection changes only
the Park/Drive image paths; all bindings, layout and blind-spot assets are
shared. Both scripts restore canonical Model Y `scene.rml` in a `finally`
block, so build order does not change the committed default source.

Highland paint variants use the same flags with IDs
`model-3-highland-pearl-white-multi-coat`, `model-3-highland-marine-blue`,
`model-3-highland-diamond-black`, `model-3-highland-ultra-red` and
`model-3-highland-quicksilver`.

The internal artboard is currently named `Newhaven` (see `rive.yaml`). Its
1800 × 1080 dimensions are authoring coordinates, not a fixed output resolution.
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

- `gear`: 0 unknown, 1 P, 2 R, 3 N, 4 D.
- `leftBlinker` / `rightBlinker`: 0 off, 1 dark phase, 2 bright phase.
- Blind-spot vehicles are grey for occupancy and red for matching turn intent,
  including the blink's dark phase.
- `adasOn` (Boolean): blue road lines and Autopilot badge. Both use the flat
  Boolean → string → number converter from DashPilot's reference dashboard,
  without wrapping it in another group or an identity formula. Runtime checks
  cover initial off/on, engagement, disengagement and re-engagement in both themes.
  This verifies rendering when the host supplies the flag, not live CAN delivery.
- `accSetSpeed` (Number): cruise set speed in the host's selected display units,
  shown immediately left of the speed-limit sign with a blue MAX caption when
  positive and either `adasOn` or `selfdriveActive` (Boolean) is true. Unknown,
  zero and negative values are hidden; the speed-limit sign remains independent.
  Its value uses Inter Regular, matching current speed. Labels use Inter Medium;
  speed-limit digits and the MAX caption use Inter SemiBold.
  Explicit Boolean state-machine transitions implement the OR condition; a
  separate numeric binding gates unknown set speeds without combining Boolean
  values inside a formula.
- `powerLevel`: signed normalized power/recuperation percentage supplied by
  the host. Battery percentage uses floor rounding of usable energy.
- `darkMode`: live theme selection, default dark. `darkModeBackgroundGray` is
  exposed for compatibility but deliberately ignored to keep OLED black.
- `dataSourceType`: source identity, not a BLE connection-health indicator.
- `phoneBattery` (Number): phone charge percentage, clamped to 0–100 and
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
  Separate metric/imperial branches and 1–4-group text runs avoid scripts and
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
`generate.py`, not PNG assets. Their 32 × 36 native-pixel outline has a
9-pixel-long, 14-pixel-thick shaft and a larger 23 × 36 arrowhead (previously 17 × 30).
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
