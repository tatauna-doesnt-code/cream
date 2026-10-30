# Changes

## 1.2.1

- Write BC4U and BC5U legacy DDS FourCC identifiers after texconv conversion,
  matching the working TM2020 skin. ATI1/ATI2 aliases are replaced without changing
  compressed pixels, dimensions, mipmaps, or channels. Validate canonical identifiers.
- Apply to CoatR/DirtMask (BC4U) and R/N (BC5U). Other formats remain unchanged.
- Invalidate old batch-resume signatures so previous ATI-header outputs are not skipped.
- Note in the UI that ZIPs must be copied directly to CarSport for in-game upload.

## 1.2.0

- Map spreadsheet columns to player name, three colors, ID, ZIP name and active
  flag when loading CSV or XLSX. Preview the first five data rows before import.
- Keep the last mapping for identical headers and suggest the original template
  columns automatically. Optional fields can remain unmapped; existing defaults apply.
- Address columns by position, including repeated or empty header labels.

## 1.1.2

- Request Normal OpenGL from Painter at export time, including with the original
  TM2020 DirectX template. Already-correct OpenGL templates remain unchanged.
- Remove post-export green inversion. DDS conversion preserves the exported green
  channel. Old batch reports cannot be resumed across this pipeline change.
- Document how to configure the saved TM2020 template for manual exports.

## 1.1.1

- Define explicit infinite padding for the inline export preset. Fixes
  “padding algorithm could not be resolved” when validating or exporting maps
  whose resource preset does not provide a padding algorithm.

## 1.1.0

- Invert normal-map green after DDS BC5 conversion.
- Add private GitHub update checks and staged installation with backup.
