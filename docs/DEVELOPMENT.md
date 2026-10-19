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

The build generates `scene.rml`, verifies it, compiles the dashboard and checks
the 5,000,000-byte limit. The distributable is
`dashboard/model-y-juniper-stealth-grey.riv`; intermediate files stay under
ignored `build/`. The export embeds fonts and images and contains no runtime
scripts. No Rive login is required for these unsigned local builds.

The internal artboard is currently named `Newhaven` (see `rive.yaml`). Its
1800 × 1080 dimensions are authoring coordinates, not a fixed output resolution.
DashPilot's normalized 1080-unit height preserves artwork size while Layout fit
reflows the width. Main/status regions use a 4:1 height split. Speed, power and
battery stay left; speed limit and gear stay right; road, blind-spot vehicles
and Autopilot remain center-relative. Contain/Cover scale or crop the canvas
instead of reflowing it.

## Actual renderer checks

Requires Pillow and a working graphics context:

```sh
python3 validate_states.py
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
`docs/images/model-y-juniper-stealth-grey/` are actual Rive renders with fixed
demo telemetry, not in-car captures or conceptual mockups. Driving previews
show 130 km/h, a 130 km/h speed limit, left turn intent and both occupied blind
spots. Dark mode shows Autopilot active; light mode shows neutral lanes.

## Data bindings

The host binds `DashViewModel`; the dashboard itself does not connect to BLE or
decode CAN frames. Speed and speed limit arrive in the selected display units.
Road animation converts mph to physical km/h internally.

- `gear`: 0 unknown, 1 P, 2 R, 3 N, 4 D.
- `leftBlinker` / `rightBlinker`: 0 off, 1 dark phase, 2 bright phase.
- Blind-spot vehicles are grey for occupancy and red for matching turn intent,
  including the blink's dark phase.
- `adasOn`: blue road lines and Autopilot badge.
- `powerLevel`: signed normalized power/recuperation percentage supplied by
  the host. Battery percentage uses floor rounding of usable energy.
- `darkMode`: live theme selection, default dark. `darkModeBackgroundGray` is
  exposed for compatibility but deliberately ignored to keep OLED black.
- `dataSourceType`: source identity, not a BLE connection-health indicator.

Dark mode uses `#000000`; light mode uses `#ffffff`. Light-mode neutral lanes,
the sign face, power track and empty battery interior use `#ecf0f1`. Current
speed, power fill, gear and battery percentage use `#2d3436`. Recuperation and
battery charge stay green. Autopilot lanes stay blue in both themes.

Park/Drive car views switch instantly. Park hides road and speed/power
instruments. Stopped D/R show perspective direction cues, with the closer
Reverse cue larger. On departure, the cue travels 40 native pixels and fades
from 30% opacity over 0.4 seconds, resetting when stopped. The static Park car
does not rotate or animate.

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
