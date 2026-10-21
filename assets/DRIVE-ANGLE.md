# Approved Drive camera

Drive sprites follow the approved, slightly lower elevated rear camera from
the Model Y Juniper Stealth Grey preview. This is an illustrative approximately
five-degree adjustment, not a measured 3D rotation.

The built-in image-generation tool was used for each vehicle/paint variant.
Only Drive artwork changed; Park artwork and shared blind-spot cars did not.
PNG canvas dimensions are retained, including the larger Legacy canvases,
except Marine Blue Highland: its old landscape canvas is normalized to the
105 × 126 portrait canvas used by the other Highland colors.

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
