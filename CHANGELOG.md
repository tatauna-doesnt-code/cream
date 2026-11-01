# Changes

## 1.11.2 beta

- Make the base ZIP optional for current-project and batch exports. Without one, package only the selected textures.
- Move the optional base ZIP picker to Batch, with a clear control and explanation. Invalid explicit selections show an actionable error.
- Allow validation, report signatures and export startup without a base ZIP.

## 1.11.1 beta

- Infer customization from batch entries; remove the manual customization toggle.
- Default to an unstyled literal `skin` with the WYSIWYG editor enabled. Restrict filename variables and player text-color tokens to batches.
- Center export checkboxes and the in-game preview, shrink accordion chevrons, align the text toolbar and standardize square icon controls.
- Show batch-resume help instantly, add an Open Help action to configuration errors, and improve Help-tab spacing.
- Display CREAM in the Python menu while preserving its lowercase package identity.

## 1.11.0 beta

- Rename the Python package to `cream`, installer to `Install.cmd` / `Install.ps1`, and local data directory to `CREAM`. Update development scripts, tests and manifests.
- Remove the redundant translated README and obsolete sample CSV; the README explains spreadsheet columns.
- Add installation migration with backups and rollback, keeping settings, protected access, recovery records and existing presets. This rename requires one manual installation; older updaters cannot apply the new package name.

- Make current-project export the default: an empty Batch list exports one ZIP without changing any layers.
- Open Textures first, followed by Skin ZIPfile Name. Batch is a separate optional area; the filename tab becomes plural for multiple entries.
- Resolve `{name}` to the project filename for single exports, with the same TM styling, duplicate protection, DDS conversion and safe cancellation as batch exports.
- Split the Batch toolbar into entry management and selection rows. Add Clear batch with confirmation; selecting no entries never triggers an unintended single export.
- Standardize action buttons, single-line inputs and resolution controls at 32 px, including inline player-name reset controls.
- Update the menu entry, Help and README to explain both workflows.
- Add Qt5/Qt6 integration coverage for empty-list exports, untouched layers, cancellation cleanup and returning from batch to single export.


## 1.10.0 beta

- Add Painter 9.x export-only mode with DDS conversion, ZIP packaging and TM filename styling.
- Detect Painter capabilities, gray out unsupported customization controls, and explain the limitations at launch.
- Warn on Painter versions below 10.1.2; adapt PySide2/PySide6 and pre-11 texture-set names.
- Use installed export presets directly when the older API cannot read map definitions; explicitly export OpenGL normals.
- Make car customization optional, including on newer Painter versions. Color-only projects no longer need a font fill.
- Register a Window-menu action at Painter startup and open CREAM only when requested.
- Rewrite the README with installation, usage, development instructions, a Righteous logo and a compatibility matrix.
- Requires one Painter restart because the startup loader changed. Older Painter releases still need native beta testing.

## Local development tooling (included in 1.10.0)

- Add Dev.cmd and a Python CLI to stage uncommitted source builds for the existing
  transactional reload flow, without GitHub, commits or version bumps.
- Locate Painter's bundled Python automatically and honor redirected Documents paths.
- Validate source syntax, preserve downloaded pending updates by default, and use
  the actual Painter process ID so protected changes really require a restart.
- Document contributor setup and include the launcher in future release packages.

## 1.9.5

- License CREAM's original code under GPL-3.0-only and include license/source/build
  instructions and third-party notices in the release archive.
- Replace the Bornie bitmap with the unmodified OFL-licensed Righteous font. Render
  the lowercase “cream” wordmark as live 28-point text centered in Help.
- Remove the former bitmap and its renderer from the current source/package.
- Add read-only pull-request CI, pinned GitHub Actions, Dependabot action updates,
  and a public-repository CodeQL workflow.
- Add issue forms, contribution/security reporting policies, publication audit,
  and a reviewable repository administration plan/helper. Live settings require
  separate administration access; private-plan restrictions still apply.
- Public releases check anonymously first, even when an old private-access token
  is saved. Repository visibility is not changed by this release.
- Requires a Painter restart for the new font and removed logo resource.

## 1.9.4

- Center the Bornie “Cream” wordmark at 28 pt at the top of Help. Package rendered
  artwork rather than the font file; other interface text retains CREAM capitalization.
- Remove the shared top-left brand/exporter header from every page.
- Square the adjoining navigation and content corners, including Settings and Help.
- The new logo resource requires a Painter restart for this update.

## 1.9.3

- Present CREAM beta 1.9.3 with manual skin entry as the primary workflow. Add, edit
  and remove entries; choose colors via pickers or hex fields. Save manual/mixed lists locally.
- Move CSV/XLSX import to the list's top right and append imports to the current list.
- Move base/output paths and all update controls into the right-side Settings tab.
- Remove the title-bar em dash and give the in-window CREAM heading a retro serif treatment.
- Make Help's setup guide a formatted introduction; add meaning and direct-entry FAQs.
- Refresh installation/beta documentation and specify Windows/Painter 12.1.3 as the
  supported minimum; older versions remain unverified.

## 1.9.2

- Start the TM styling helper disabled in each new session, even if old preferences
  saved it enabled. Keep its active-session state through CREAM-only reloads.
- Resolve installation from the current user's Windows Documents known folder first,
  supporting redirected/OneDrive Documents. No developer-specific paths ship as defaults.

## 1.9.1

- Double the in-game filename preview from 12 to 24 points and enlarge its viewport.
- Replace event-specific branding, project-operation labels, examples and new report
  names with generic CREAM terminology. New reports use _CREAM_reports; older reports
  can still be selected to resume a matching batch. Keep user-defined filename patterns.
- Preserve legacy module, updater storage and resume-signature identifiers so existing
  installations, credentials, settings and recovery records remain compatible.

## 1.9.0

- Join tab navigation to its content panel; align path controls with consistent backgrounds.
- Show player names as vertically centered inputs with matching reset buttons on the left.
  Add subtle column separators and turn the resume information control into a plain icon.
- Add a top-right Help page with expandable project setup and a feature FAQ.
- Bundle Montserrat regular/bold/italic/bold-italic under the SIL Open Font License for
  filename styling previews. This resource update requires one Painter restart.
- Clarify update navigation and the update dialog. Request private-repository credentials
  contextually after an access failure; automatic startup checks never open a credential prompt.

## 1.8.1

- Use explicit neutral gray table rows and readable text instead of host-theme purple alternation.
- Group pages, texture sets, preview recovery and export controls into bordered dark panels.
- Number ZIP names as step 4 and rename Activity to the unnumbered Logs page.
- Place Restore original beside Preview, retaining the global preview banner.
- Explain preview-locked controls with a cursor-following tooltip, including disabled
  buttons and read-only name editors. Add an information tooltip explaining report-based resume.

## 1.8.0

- Reorganize the workspace into Setup, Skins and Textures, with separate optional ZIP
  naming and Activity pages. Keep filename styling out of the selection workspace.
- Add first-use guidance, project preparation help, an empty state, column-mapping
  explanations, color swatches and live selection/export counts.
- Give Export a clear primary action and explain missing prerequisites. Put preview
  next to the skin list and show a persistent Restore original banner while active.
- Move updates and private access into an Updates dialog, with an available/ready
  indicator in the header. Automatic checks and safe reload behavior remain intact.
- Preserve settings, manual name overrides, texture selections and the current page
  across CREAM reloads. Improve spacing, keyboard labels and compact-window layout.

## 1.7.0

- Remove the DDS converter input and always use the verified bundled texconv.exe.
  Obsolete converter-path preferences are ignored; missing files prompt reinstallation.
- Group Textures into collapsed Details, Glass, Skin and Wheels accordions. Each
  header has a tri-state select-all checkbox and a resolution control for the full set.
- Keep individual texture export flags and resolution overrides. Mixed set resolutions
  are shown explicitly; Wheels retains its 1:4 output dimensions.
- Remove redundant Texture set and DDS columns. Compression details remain in tooltips.
- Preserve the existing flat settings layout, selection order and resume signatures.
  Selections and overrides survive migration and CREAM reloads.

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
- Preserve existing filename patterns; default new installations to {name}.
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
