# Model Y Juniper â€” Marine Blue

Updated with the built-in image generator using the current Model Y Juniper
Stealth Grey images as the geometry, camera and styling templates. The previous
marine-blue images supply paint color only. Stealth Grey assets are unchanged.

## Final prompt specifications

- `park.png`: Recolor only the Stealth Grey template's painted body panels,
  pillars and mirror caps to marine-blue. Preserve its elevated front-left
  three-quarter view, body proportions, multispoke wheels, tires, dark glass
  roof, black trim, thin front light bar, reflections and panel details.
- `drive.png`: Apply the same paint to the current Stealth Grey rear template.
  Preserve its centered elevated camera, zero yaw and symmetry, smooth dark
  roof reflections, proportions, mirrors, wheels and black trim. Keep the
  bumper without a plate-holder outline and the thin red running-light strip;
  the center and outer brake segments remain unlit. Do not copy the older
  paint reference's higher camera or brighter brake lamps.

Both prompts require one whole isolated car with both mirrors, genuine
transparent alpha, a small transparent margin, no clipping, no floor, ground
shadow, environment, labels or watermark. Generated silhouettes are fitted
without stretching to the Stealth Grey template's occupied bounds and canvas:
410 × 307 pixels for Park and 111 × 124 pixels for Drive.

All Juniper dashboards share the Stealth Grey blind-spot sprites through the
source asset mapping. Source PNG changes do not rebuild compiled `.riv` files.
These are illustrative dashboard sprites, not official Tesla artwork.
