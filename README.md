# CREAM

**Color Replacement & Export Automation Manager**

Windows plugin for Adobe Substance 3D Painter: customize player names and colors
from CSV/XLSX, export TM2020 textures, convert to DDS and build one ZIP per backer.

See [LEIA-ME.md](LEIA-ME.md) for installation and usage (in English).
Tested against the Painter 12.1.3 SDK; API minimum 11.0 is not validated on that version.

## Updates

Open **Updates** in the top-right corner for version checks, downloads and private
access. The header changes to **Update available** or **Update ready** when applicable.

The header now reads **Check for updates…**. The update dialog requests a read-only
GitHub token only if a private-repository access check fails. Startup checks never
open credential prompts. **Help** at the top-right of the page navigation contains
the project setup guide and feature FAQ. Filename previews use bundled Montserrat
fonts (regular, bold, italic and bold italic), distributed under their included SIL
Open Font License. Upgrading to 1.9.0 requires a Painter restart for these new resources.

Install manually once with `Instalar.cmd`, with Painter closed. For private updates,
configure a GitHub fine-grained token limited to `tatauna-doesnt-code/cream`, with
Contents: Read-only. Windows protects the token for the current user.

Check for updates downloads and verifies the release asset SHA-256 and its manifest.
The package declares an update protocol and restart mode. CREAM also compares file
hashes against the installation; the declaration alone cannot authorize reloading.

- Pure Python module changes: **Apply and reopen CREAM**.
- Changed loader, bootstrap, updater, non-Python files, unsupported metadata, or an
  explicit full restart: **Restart Painter required**.
- Active batch, preview, recovery, background task or busy Painter: wait or restore first.

Eligible updates close the old UI, stop workers, swap directories and load fresh
Python modules. Loaded rows, checked backers, settings and log are restored. Import
failures restore the old files/modules and require a Painter restart to retry.
Previous installations are retained under `python/cream-backups`.
The initial upgrade from 1.2.x requires one Painter restart.

## Spreadsheet and textures

The main workflow is **1 Setup → 2 Skins → 3 Textures**. Setup contains source files,
the output folder and collapsible Painter-project instructions. Loading a spreadsheet
opens column mapping and then the skin list. Select rows, optionally preview one,
and choose maps. **Export N skins** validates before starting; a separate configuration
check is available. Missing prerequisites are explained beside the export counts.
An active preview shows **Restore original** above every page. Recovery after a crash
is also available in **Activity**. ZIP naming/styling has its own optional **ZIP names**
page; updates no longer occupy the export workspace.

Select columns for name, three colors, ID, ZIP name and active flag. Only name is
required. Original template headers and existing CSV values remain supported.
Names are limited to 20 Unicode code points after NFC normalization. Colors are sRGB
`#RRGGBB`; omitted colors use the original project color.

The Textures tab groups Details, Glass, Skin and Wheels into collapsed accordions.
Use the arrow/name to expand a set, its checkbox to select or clear all seven textures,
and its Resolution control to apply a size to every texture in that set. Partial checks
indicate a subset of selected textures. Each texture keeps its own checkbox and size
override; the set control shows Mixed when sizes differ. Changing the set resolution
replaces all individual sizes, including unchecked textures. Wheels stays at 1:4.
Selections and per-texture sizes from earlier versions are retained.
CREAM always uses its bundled DDS converter; there is no executable-path setting.

Edit **Player name** directly in the loaded table. An override appears **bold italic**;
the refresh-icon button restores the imported spreadsheet name. Names are normalized
and limited to 20 characters using the same rules as imports. Invalid drafts block
preview/export until fixed or reset. Editing is locked during a batch or active preview.

Overrides affect the name printed on the skin and `{player}` in filenames. If the ZIP
name falls back to the player name, `{name}` follows the edit too; an explicitly mapped
ZIP name is preserved. Completed ZIPs are not renamed or overwritten. Row export
checkboxes retain their selection, so select edited rows before exporting again.
Edits are session-only, survive CREAM reloads and never modify the spreadsheet.
Reloading the spreadsheet replaces the edits and resets the baseline.

The **ZIP name pattern** is configurable, with a live preview:

| Pattern | Example |
|---|---|
| `{name}` | `Joseph.zip` |
| `My Event - {name}` | `My Event - Joseph.zip` |
| `{player} - {id}` | `Joseph - 001.zip` |
| `Skin {row} - {name}` | `Skin 2 - Joseph.zip` |

`{name}` uses the mapped ZIP-name column, falling back to the player name. `{player}`
always uses the name printed on the skin; `{id}` and `{row}` are the row ID and spreadsheet
row number. This controls filenames only. The extension is automatic; an optional final
`.zip` in the pattern is accepted. Invalid filename characters in values are replaced,
reserved Windows names are escaped and filenames are limited to 100 characters before
collision suffixes. Folders, unknown tokens and Python format modifiers are rejected.
Existing settings retain `KR7 - {name}`; new installations use `{name}` and default to
the current user's Documents/Trackmania/Skins/Models/CarSport. Saved folders are preserved.

### Trackmania styling helper

Enable **Use Trackmania text styling** on the **ZIP names** page to show a compact WYSIWYG editor
and styled preview for the selected backer. It is off by default. Select a portion of
the pattern and use bold, italic, uppercase, shadow, width, color or reset controls;
with no selection, the style applies to subsequent typing. Ctrl+B/Ctrl+I are supported.
The raw field remains available. Turning the helper off hides it without removing codes.
Only ZIP filenames are styled; the name printed on the car remains unchanged.

**Text color…** accepts exactly three hex digits, e.g. `F80`, and offers 0–F RGB sliders,
default text color, and **Use skin primary/secondary color**. Six-digit text colors are
rejected. Primary/secondary refer to spreadsheet colors 1/2 for each row. For example:

`{primary}My Event$g - {secondary}{name}$z`

These tokens resolve to `$RGB` codes independently for every backer, rounding each
8-bit sRGB channel to the nearest 4-bit channel. Blank spreadsheet colors use the
original project color, converted to sRGB. If the original differs across texture sets
at this palette precision, or is unavailable, select an explicit spreadsheet color.
Project defaults refresh on validation and when opening the color picker.

Filename-compatible styling codes: `$o` bold, `$i` italic, `$t` uppercase, `$s` shadow,
`$w` wide, `$n` narrow, `$m` normal width, `$g` default color, `$z` reset, and `$$` dollar.
Reference: https://doc.maniaplanet.com/client/text-formatting
The helper does not emit hyperlinks or scope delimiters; these are not filename styling
controls, and scope delimiters contain characters prohibited in Windows filenames.
The styled preview uses local fonts; in-game font metrics can differ. The actual raw
filename is always displayed. Pattern/filename limits include control codes, which are
not split when truncating generated filenames.

Normals are generated as Normal_OpenGL before conversion. Green is preserved.
The output DDS identifiers are DXT1 (B/AO), DXT5 (I), BC5U (R/N) and BC4U
(CoatR/DirtMask). ATI aliases are relabeled without changing compressed pixels.
Copy ZIPs directly into CarSport for upload; subfolders can cause C-AA-00-03.

## Development

Run `python -m unittest discover -s tests -p "test_*.py"` (Pillow for real DDS tests).
Run `scripts/check_columns_ui.py` and `scripts/check_runtime_reload.py` with Painter's
SDK Python and Qt platform configured for offscreen testing.
`scripts/check_name_style.py` checks the real WYSIWYG editor and strict RGB picker.
`scripts/check_texture_sets.py` checks the texture accordions and legacy settings migration.
Run `python scripts/build_release.py` to create `dist/CREAM-plugin.zip`.

Set `VERSION` and `UPDATE_RESTART` in `kr7_batch/version.py` for each release.
The manifest uses `update: {protocol: 1, restart: "cream"|"painter", min_reload_protocol: 1}`.
Use `painter` for releases explicitly requiring it. The runtime additionally forces
Painter restart for protected or non-Python changes, including removed files.
Older packages without compatible metadata always require Painter restart.

The GitHub Actions workflow tests, builds and publishes the stable asset on version changes.
The repository is private, without an open-source license. The bundled texconv retains
Microsoft's MIT license in `kr7_batch/bin`.
