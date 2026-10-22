# Approved Drive camera

Drive sprites follow the approved, slightly lower elevated rear camera from
the Model Y Juniper Stealth Grey preview. This is an illustrative approximately
five-degree adjustment, not a measured 3D rotation.

The built-in image-generation tool was used for each vehicle/paint variant.
The initial rollout changed only Drive artwork. Later refinements to the shared
blind-spot cars are described below; Park artwork keeps its existing view.
PNG canvas dimensions are retained, including the larger Legacy canvases,
except Marine Blue Highland: its old landscape canvas is normalized to the
105 Ã— 126 portrait canvas used by the other Highland colors.

## Prompt specifications

- Juniper paints: use the approved lower-camera Juniper as edit target and the
  existing paint-specific sprite as paint reference only. Preserve the approved
  camera, roof/glass footprint, body proportions, mirrors, black trim and
  full-width red rear lamp. Change only the paint.
- Highland and Legacy: use each existing sprite as vehicle/paint identity
  target and the approved Juniper as camera-orientation reference only. Match
  its elevated rear perspective without copying Juniper bodywork or lamps.
  Retain the Highland sedan body and separate C-shaped rear lamps, and the
  Legacy SUV body and separate original rear-lamp clusters.
- All: straight rear view, zero yaw/roll and symmetry. Roof/glass stays dominant
  with slightly more rear hatch/bumper visible. Whole car and both mirrors on
  genuine transparent alpha; no floor, ground shadow, scenery, text or watermark.

Generated artwork is mechanically framed and resized to sprite dimensions.
Checksums are recorded in `manifest.json`. Source PNG updates do not change
already-compiled `.riv` exports; compilation is a separate step.

## Detail corrections

The three Legacy paint variants received a roof-only correction: smooth dark
panoramic glass with broad, subtle reflections, no repeated curved bands,
corrugations or fake roof ribs. Camera, bodywork, paint and lamps are retained.

The six Highland colors received a lettering-only correction, restoring the
five evenly spaced metallic letters `T E S L A` across the trunk between the
rear lamps. The approved camera, body, paint and separate lamps are retained.
Both corrections use the built-in image generator with transparent alpha and
the same mechanically framed sprite dimensions.

## Juniper Stealth Grey reference refinement

The Stealth Grey Drive sprite was refined with the built-in image generator
using the user's photo of the vehicle shown in Tesla software. The approved
rear camera sits between the earlier overhead sprite and the first low rear
preview. Its glass roof has smooth reflections; the bumper has no plate-holder
outline. The center and outer brake segments are unlit while the thin red
running-light strip remains visible.

Final paint prompt: preserve the approved camera, geometry, glass, bumper and
lamp state; match the painted body panels to the original Stealth Grey sprite's
dark graphite metallic tone, including the pillars, mirrors and rear deck.
The approved result is cropped to its transparent silhouette and fitted without
stretching inside the existing 111 Ã— 124 pixel canvas.

## Matching blind-spot camera

The built-in image generator adjusted the grey neighboring car to the refined
Juniper camera elevation, preserving the generic vehicle design and slight
inward lane perspective. The red warning variant uses the same view with red
body paint and dark burgundy glazing. The final prompt preserves geometry,
camera, framing, lamp shapes and transparency while changing only that warning
color treatment. Both variants share one crop and are fitted without stretching
inside 117 Ã— 140 pixel canvases. The right-lane PNGs are exact horizontal mirrors
of their left-lane counterparts.

## All Juniper paints aligned to the current Stealth Grey template

White Multi-Coat, Diamond Black, Marine Blue, Quicksilver and Ultra Red Park
and Drive PNGs were regenerated from the current Stealth Grey view templates,
using their previous images only as paint references. Both cameras, dark glass,
wheels and body geometry follow Stealth Grey. Drive views retain its smooth
roof, bumper without a plate-holder outline, thin red running-light strip and
unlit center/outer brake segments. Each generated silhouette is fitted without
stretching into the corresponding Stealth Grey alpha bounds on a 410 × 307
Park canvas or 111 × 124 Drive canvas. The built-in image generator supplied
transparent alpha; mechanical framing preserves it. Stealth Grey PNGs and all
compiled `.riv` exports are unchanged. Paint-specific READMEs record the final
prompt set.
