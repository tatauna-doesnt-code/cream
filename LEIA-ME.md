# CREAM 1.6.0

Color Replacement & Export Automation Manager for Adobe Substance 3D Painter on Windows.
The filename is retained for installer compatibility; these instructions are in English.

## Install

1. Extract the entire ZIP to a folder.
2. Save your work and close Painter.
3. Run **Instalar.cmd**. Administrator access is not required.
4. Open Painter and enable **Python > kr7_batch**.
5. Reopen the window with **Window > CREAM — Batch Exporter**.

The installer backs up an existing installation and preserves an existing TM2020 preset.
The texconv converter is included; Python, Pillow and Excel are not required to use CREAM.

## Prepare the project

Open a saved .spp project. CREAM never saves one project per backer.
Use mask Fill effects named PLAYER_NAME with a Font in Grayscale. Every matching
name outside Glass is updated. Use Fill Layers PLAYER_COLOR1, PLAYER_COLOR2 and/or
PLAYER_COLOR3 with an independent uniform Base Color. Other layer properties,
anchors, text colors, font sizes and projection settings are preserved.

Texture sets: Details, Glass, Skin and Wheels, without UDIM or material layering.
Glass can be exported but never receives personalized names or colors.
The TM2020 export preset must have outputs $textureSet_B, _R, _I, _N, _CoatR,
_DirtMask and _AO, as needed for the selected textures.

## Spreadsheet

Use UTF-8 CSV (comma, semicolon or tab) or XLSX. The first row contains headers.
For XLSX, CREAM reads the Backers sheet or the first sheet; formulas are rejected.
Click Load spreadsheet, select a column for each field and confirm the sample.
Header names/order are unrestricted. Repeated headers are identified by column letter.
CREAM remembers the last mapping for identical headers and recognizes the original template.

| Field | Content or default when not mapped |
|---|---|
| Player name | Required; case preserved, limited to 20 characters |
| Color 1/2/3 | #RRGGBB; blank or unmapped uses the project original |
| Row ID | Unique identifier; defaults to the spreadsheet row number |
| ZIP name | Defaults to the player name |
| Export / active | yes/no, true/false or 1/0; blank/unmapped exports all rows |

Original template keys ativo, id, nome_player, nome_arquivo, cor_1, cor_2, cor_3 and
Portuguese sim/não values remain compatible. A column can supply multiple fields.
Names longer than 20 Unicode code points after NFC normalization are truncated with
a warning. Empty names, control characters and common Trackmania formatting codes
are rejected. Duplicate names are allowed; explicit IDs must be unique.
ZIP collisions receive suffixes: KR7 - Joseph.zip, KR7 - Joseph 2.zip, etc.
Existing ZIPs are never overwritten. Invalid filename characters are replaced with _.

### Edit a player name manually

Edit the **Player name** field directly in the loaded table. A changed name appears
bold italic. Click its refresh icon to restore the imported spreadsheet value.
The same 20-character, Unicode and formatting-code validation applies to manual edits.
Invalid edits must be fixed or reset before preview/export. Names are read-only while
a batch or preview is active; restore the preview before editing.

Edits are used for the skin text, `{player}` and any ZIP name derived from the player
name. An explicit ZIP-name column remains unchanged. Select the desired rows before
exporting again; existing ZIPs are preserved. Edits survive CREAM reloads within the
current session but do not modify the source spreadsheet. Reloading the spreadsheet
starts again with its imported values.

## Export

1. Load and map the spreadsheet.
2. Select the base ZIP, output folder and ZIP name pattern. Check the filename preview.
3. Select textures and individual resolutions in Textures.
4. Validate configuration.
5. Preview a selected backer, inspect the model, then Restore names and colors.
6. Export one or two backers and check them in Trackmania before running the full batch.

Copy completed ZIPs directly into Trackmania/Skins/Models/CarSport for in-game upload.
Uploads from subfolders such as KR7BACKERS can fail with C-AA-00-03 despite a working preview.
The output folder preference is retained; CREAM does not automatically copy into CarSport.

The base ZIP must contain files directly at its root. Selected outputs replace matching
files; all others are preserved. Settings apply to every selected backer.

### ZIP name pattern

Use a pattern such as `{name}`, `My Event - {name}` or `{player} - {id}`.
`{name}` uses the ZIP-name column (or the player name if not mapped); `{player}` uses
the printed name, `{id}` the row ID, and `{row}` the spreadsheet row number.
The .zip extension is automatic. Duplicate filenames receive numeric suffixes.
The pattern changes only ZIP filenames, never the text printed on the skin.
Patterns cannot contain folders or invalid filename characters. Values are sanitized
and the resulting name is limited to 100 characters, with reserved Windows names escaped.

Existing settings keep `KR7 - {name}`. New installations start with `{name}` and the
current user's Documents/Trackmania/Skins/Models/CarSport folder. Saved output folders
are preserved. Naming preferences survive CREAM reloads. Changing the pattern prevents
resuming a report created with a different naming configuration.

### Trackmania name styling

Turn on **TM styling helper** next to ZIP name pattern. It is off by default and shows
an editable styled pattern plus the selected backer's in-game-name preview. Select text
and use the toolbar, or choose a style and type. Bold, italic, uppercase, shadow,
normal/narrow/wide width, default color, full reset and literal dollar are available.
Ctrl+B and Ctrl+I also work. The preview uses local fonts, so exact metrics can differ
from Trackmania. The raw pattern and actual ZIP filename remain visible.

**Text color…** accepts exactly three hexadecimal digits such as F80, not FF8800.
Channel sliders use values 0–F. Inside this picker, choose **Use skin primary color**
or **Use skin secondary color** to use color 1 or 2 independently for each backer.
The pattern tokens are `{primary}` and `{secondary}`; each becomes a `$RGB` color code.
Example: `{primary}My Event$g - {secondary}{name}$z`.

Skin colors are rounded from 6-digit sRGB to Trackmania's 3-digit text palette. For blank
spreadsheet colors, the project original is used. If originals differ across texture
sets at this palette precision, supply a spreadsheet color instead of relying on defaults.
The helper changes ZIP-name styling only. Turning it off keeps the existing raw codes.

| Texture | Compression / DDS identifier |
|---|---|
| B, AO | BC1 / DXT1; opaque alpha |
| R, N | BC5 / BC5U |
| I | BC3 / DXT5; RGB and alpha preserved |
| CoatR, DirtMask | BC4 / BC4U |

No extra mipmaps. Normals use Normal_OpenGL at Painter export, with no later green flip.
ATI1/ATI2 aliases from texconv are changed to BC4U/BC5U without recompressing pixels.
Details/Glass/Skin: square 1024, 2048 or 4096. Wheels: 256x1024, 512x2048 or 1024x4096.
8-bit PNG intermediates are deleted after DDS conversion; per-backer temporary folders
in %LOCALAPPDATA%/KR7BatchExporter are removed after processing.

## Cancel and recover

Cancel safely waits for a safe stopping point, restores original names/colors and preserves
finished ZIPs. Painter exports/autosave can delay a cancellation request. Conversion can
be terminated. A ZIP is written as .partial, checked for CRC and published only when complete.
An abrupt process exit can leave temporary files. The recovery record is written before
project edits. Restore names and colors after a crash before starting another batch.

Reports are stored in _KR7_reports. Load the same spreadsheet/settings and use Resume from
report to deselect confirmed completed rows. Reports across changed export pipelines cannot
be resumed. CREAM cannot detect arbitrary manual material edits; check the project first.

## Update

Configure private access using a GitHub fine-grained token for tatauna-doesnt-code/cream,
with Contents: Read-only. Do not share the token; Windows encrypts it for the current user.
Check for updates, then Download update. CREAM verifies hashes and chooses the required restart:

- Apply and reopen CREAM: eligible Python-only updates; loaded rows and settings are preserved.
- Restart Painter required: loader/updater/native or other non-Python changes, an explicit
  restart request, or unsupported/missing package metadata.

Stop the batch, restore any preview/recovery, and wait for Painter/background tasks before
applying. If importing an update fails, CREAM restores the previous version and asks for a
Painter restart. Previous versions are retained in python/cream-backups. No internet is
required for normal exports. Updating from 1.2.x requires one Painter restart to install
this reload mechanism; compatible future updates can restart only CREAM.
