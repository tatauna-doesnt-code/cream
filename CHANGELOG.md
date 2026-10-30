# Changes

## 1.6.0

- Edit Player name directly in each loaded row. Manually changed names appear bold
  italic with an icon-only refresh button to restore the original spreadsheet value.
- Use edited names in previews, text layers, ZIP patterns and report fingerprints.
  Update ZIP-name fallbacks while preserving explicitly supplied ZIP names.
- Apply the same Unicode, 20-character and formatting-code validation as spreadsheet
  imports. Invalid edits block preview/export; editing is locked during batches/previews.
- Preserve session edits and their original reset values across CREAM-only updates.
  The source spreadsheet is never modified. Reloading a spreadsheet starts a new baseline.
- Scan the output directory once per filename-preview refresh instead of once per row.

## 1.5.0

- Add an optional TM styling helper next to the ZIP name pattern, off by default.
  Edit selected text visually with bold, italic, uppercase, shadow, normal/narrow/wide
  widths, default color, full reset and literal-dollar controls. Raw codes remain editable.
- Add a strict 3-digit RGB picker with channel sliders and per-backer primary/secondary
  skin-color choices. Dynamic colors use {primary}/{secondary} tokens and are quantized
  to Trackmania's 12-bit text palette independently for every exported ZIP.
- Preview the selected backer's styled filename with local fonts. Use a single original
  project color for blank spreadsheet colors; reject ambiguous or unavailable defaults.
- Keep styling limited to filenames, preserve helper preferences across reloads, and avoid
  splitting $RGB/style codes when limiting filename length.

## 1.4.0

- Configure ZIP filenames with {name}, {player}, {id} and {row}, with a live example
  and per-row destination preview. Automatically append .zip and retain collision suffixes.
- Preserve KR7 - {name} for existing settings; default new installations to {name}.
  Remove the hardcoded Windows username from the default output folder.
- Validate patterns and Windows filenames before editing the Painter project. Naming
  affects only ZIP filenames, never the text applied to the skin.
- Include custom patterns in resume checks and retain the pattern across CREAM reloads.
- Eligible for CREAM-only reload when upgrading from 1.3.0.

## 1.3.0

- Use English throughout the plugin UI, column selection, validation, progress,
  recovery, updater messages and manual installer. Existing spreadsheets remain compatible.
- Add release restart metadata with an independent check of installed file hashes.
  Python-only changes can restart CREAM; loader, updater, native and unknown component
  changes, unsupported metadata and explicit restart requests require Painter restart.
- Apply eligible updates from the UI without restarting Painter, using a deferred
  reload with worker shutdown, fresh Python modules, backup and rollback on import failure.
- Preserve loaded rows, checked backers, selected row, settings and log across reloads.
  Block applying during exports, background tasks, previews, recovery or Painter activity.
- Upgrade the legacy startup loader after the initial install. Updating from 1.2.x
  requires one Painter restart; subsequent compatible releases can reload CREAM alone.

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
