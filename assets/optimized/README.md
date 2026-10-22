# Compact export assets

These derivatives are embedded by `optimize_export.py` during `build.py`.
The original artwork and full Inter fonts remain unchanged in their source paths.
The canonical `scene.rml` continues to reference those originals.

- `drive-chase.png`: Lanczos downsample from 1312x1199 to 640x585, preserving
  transparency. Export image scale compensates for both dimensions, keeping
  the displayed size, center and tire baseline unchanged. At the 1800x1080
  design viewport, this is still over twice the displayed ego body resolution.
- Inter fonts: subsets retain Latin-1, general punctuation and spaces
  (including the thin space), minus and replacement characters. They cover
  dashboard labels, numeric telemetry, units and gear letters. Font outlines,
  metrics and layout behavior are preserved. See `fonts/Inter-OFL.txt` for the
  original SIL Open Font License; font license/name records are retained.
- `manifest.json`: SHA-256 and sizes of the compact derivatives.

To regenerate, install Pillow and `fonttools==4.67.0` and run
`python prepare_compact_assets.py`. Normal dashboard builds need neither package:
the compact assets are committed alongside their full-resolution sources.

The MYJ SG export shrank from 4,404,728 to 2,697,844 bytes (38.7%). No vehicle
pose, animation, view-model contract or lane geometry was removed.
