# Steering angle sprites

Built-in imagegen edits of the existing MYJ SG ego and adjacent car artwork.

Prompt set:
- Ego: preserve the Stealth Grey Juniper identity, 18-degree camera elevation and lighting; change azimuth to approximately 5 degrees from back-left, revealing the left flank; no image roll, flat-picture rotation, scenery or text; transparent background. Mirrored for the opposite turn.
- Adjacent: two equal-scale transparent atlas cells using the same minimalist grey car: rear-right azimuth approximately 19 degrees and 29 degrees at 20-degree elevation, narrower/wider inner flank; keep level wheel contact and zero camera roll.
- Warning: preserve the exact two-cell geometry; recolor all body, glass, wheels, tires, mirrors and underside red, using lighter/darker red for material contrast; preserve transparency.

Technical extraction crops the two atlas cells and downsamples to at most 440 pixels per side. Native Rive preserves road depth, lane offsets and visibility, while selecting one angle-specific image at a time. MYJ SG uses `vehicle_angles.py` to select these views exclusively without car image rotation. `geometry.json` stores the approved silhouette measurements so builds remain stdlib-only. Build the export with `python build.py --vehicle model-y-juniper-stealth-grey`.

Pose selection uses native Rive Solo components and zero-duration transitions. Angled views activate only when egoSteeringAngle > 50 or < -50 degrees; the inclusive [-50, 50] range uses the straight view. Differing silhouettes are never opacity-crossfaded.

The active ego steering sprite is ego-back-left-middle.png; the original ego-back-left.png is retained as a reference. Built-in image generation used both the original angle and drive-chase.png with the prompt: "Create a midpoint rear-left camera angle, with less flank than the existing angled sprite; preserve straight-view pitch, vehicle identity, paint, proportions and transparent background." Height and rear tire baseline normalization remain unchanged.
