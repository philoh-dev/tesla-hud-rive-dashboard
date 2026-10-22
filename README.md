# Tesla HUD Rive Dashboard

Rive dashboards for [DashPilot](https://github.com/softwiredtech/dashpilot),
using Tesla telemetry from [DashKit](https://github.com/softwiredtech/dashkit-firmware).
Includes ready-to-use `.riv` files, source code and vehicle artwork.

## Use a dashboard

1. Choose your model and paint in **[dashboard/](dashboard/)**.
2. Open its `.riv` file on GitHub and select **Download raw file**.
3. Load the file through DashPilot's Rive-dashboard support and connect your
   compatible DashKit setup for live telemetry.

Fonts and images are embedded; no separate asset download is needed.

| Vehicle | Available paints |
| --- | --- |
| Model Y Juniper | Stealth Grey, White Multi-Coat, Diamond Black, Marine Blue, Quicksilver, Ultra Red |
| Model Y Legacy | Deep Blue Metallic, Pearl White Multi-Coat, Midnight Silver Metallic |
| Model 3 Highland | Stealth Grey, Pearl White Multi-Coat, Marine Blue, Diamond Black, Ultra Red, Quicksilver |

Start with the [Model Y Juniper Stealth Grey dashboard](dashboard/model-y-juniper-stealth-grey.riv).
A [generic dashboard](dashboard/generic-vehicle.riv) is also available.
These options describe the artwork, not DashKit hardware compatibility.

## Features

- Speed, speed limit, cruise set speed, gear and odometer.
- Car and phone batteries, power consumption and recuperation.
- Animated road, assist lanes, turn signals and blind-spot warnings.
- Separate Park/Drive views, light/dark themes and responsive layout.
- Juniper: curved lane projection and angle-specific vehicle views.

[Preview images](docs/images/) use demo telemetry. Device fit and safe areas
are controlled by the host; see [validation status](VALIDATION.md) for known limitations.

## Develop

Requires **Python 3** and **Rive CLI 1.6.0**. Put the CLI on `PATH`, set
`RIVE_CLI` to its executable, or place it in `.tooling/` as `rive` / `rive.exe`.

```sh
python3 -m unittest discover
python3 build.py --vehicle model-y-juniper-stealth-grey
```

Run `python3 build.py` to build all designs, or `python3 build.py --universal`
for the dashboard selected by the host's `vehicleDesign` property.
Exports go to `dashboard/`; intermediate files go to ignored `build/`.
Builds use committed compact assets and enforce a 5 MB limit per export.
No image-processing dependencies are needed for normal builds.

- [Development guide](docs/DEVELOPMENT.md): setup, telemetry bindings, previews and runtime checks.
- [Asset guide](assets/README.md): vehicle sources, shared artwork and paint variants.
- [GitHub Actions](.github/workflows/dashboard.yml): tests, builds and downloadable artifacts.

## Credits

See [CREDITS.md](CREDITS.md) for artwork provenance and
[Inter's SIL Open Font License](fonts/Inter-OFL.txt) for font licensing.
