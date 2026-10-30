# CREAM beta 1.10.0

**Color Replacement & Export Automation Manager** personalizes Trackmania 2020 skin
names/colors in Painter, exports DDS textures and packages one ZIP per skin.

## Requirements and beta compatibility

**Windows and Adobe Substance 3D Painter 9.0.0 or later.** Painter 9.x exports existing
textures to DDS/ZIP and supports TM filename styling; car name/color customization is
disabled. Painter 10.0+ enables customization, with a warning below 10.1.2. Older
releases still need native beta testing; 12.1.3 is the SDK-check baseline. No separate
Python, Excel, Pillow or DDS converter installation is required. See README.md for
the full compatibility table and updated instructions.

This beta supports TM2020 texture sets Details, Glass, Skin and Wheels, without
UDIM or material layering. It is not an exporter for arbitrary games. Test a small
export in-game before processing large batches. Include Painter version, reproduction
steps and relevant Logs when reporting issues.

## Installation

1. Download **CREAM-plugin.zip** from Releases, rather than GitHub's Source code ZIP.
2. Extract the entire ZIP, save your project and close Painter.
3. Run **Instalar.cmd** without administrator rights. The installer uses Windows'
   Documents folder, backs up an existing installation and preserves an existing preset.
4. Open Painter and enable **Python > kr7_batch**. This legacy internal folder name
   remains for update compatibility; the application is CREAM.
5. Open **Window > CREAM — Batch Exporter**. CREAM does not open automatically with Painter.

Keep the extracted package together. Its texconv converter and fonts are bundled.
The package ships no developer-specific source/output paths.

## First export

1. Open a saved project. Use mask Font fill effects named `PLAYER_NAME`, and uniform
   Base Color fill layers `PLAYER_COLOR1`, `PLAYER_COLOR2`, optionally `PLAYER_COLOR3`.
   CREAM changes text/Base Color only. Set font, size, alignment and projection in Painter.
2. In **Settings**, select the base skin ZIP and output folder. Use CarSport directly
   for in-game uploads; subfolders can fail. The base ZIP's files must be at its root.
3. In **1 Skins**, click **Add skin…** and enter a name and up to three colors using
   pickers or `#RRGGBB`. Blank colors keep the project original. Use **Edit skin…** to
   change a highlighted entry and **Remove** to remove it.
4. Optionally use **Import CSV / XLSX…** at the list's top right. Match your columns;
   imports append to existing entries. Only player name is required. XLSX reads the
   Backers sheet or first sheet; formulas are rejected.
5. Choose maps/resolutions in **2 Textures**, then optional naming in **3 ZIP names**.
6. Check configuration, preview a highlighted skin, then **Restore original**. Export
   a test skin and inspect it in Trackmania. Help contains the full setup guide and FAQ.

Manual and mixed lists are saved locally. Spreadsheet-only lists must be reloaded
when restarting Painter. CREAM-only reloads preserve the loaded list and editor state.
Source spreadsheets are never modified. Inline name overrides are bold italic; refresh
restores the original entry. Names preserve case, normalize to NFC and truncate to
20 characters. TM styling codes cannot be used for the text printed on the car.

## Textures and ZIP names

Per-set controls select all maps and apply a common resolution; individual overrides
remain possible. Wheels keeps 1:4 proportions. Unselected files remain from the base ZIP.
Glass receives no name/color edits. DDS compression is automatic: B/AO BC1, R/N BC5U,
I BC3, CoatR/DirtMask BC4U. Normals export as OpenGL without another green-channel flip.

Filename tokens: `{name}`, `{player}`, `{id}`, `{row}`, `{primary}`, `{secondary}`.
Duplicate/existing ZIP names receive numeric suffixes. Existing files are preserved.
The optional TM helper supports bold, italic, uppercase, shadow, widths and three-digit
text colors, including each player's primary/secondary color. It starts off each new
session. Hiding the helper preserves codes already in the filename pattern. Montserrat
previews approximate game rendering. The default ZIP pattern is `{name}`.

## Safe batches and updates

Use **Cancel safely** to finish the current operation and restore original values.
Completed ZIPs remain valid. Resume using a JSON report in `_CREAM_reports`; successful
matching rows whose ZIPs still exist are unchecked. Settings and project must match.
After interruption, use **Logs > Restore original / recover project**. No per-skin SPP
is saved. Temporary textures are cleaned up after processing.

Update controls are directly in **Settings**. Check, download and follow Apply/restart
instructions. Python-only updates can reopen CREAM; loader/resource changes require
Painter restart. Restore previews and finish batches before applying updates.

For public releases, updates work without a GitHub account or token. CREAM checks
anonymously first, even if an old private-access token is saved. If the repository
is private, testers need repository access and a fine-grained token limited to
`tatauna-doesnt-code/cream` with **Contents: Read-only**. Windows protects the saved
credential. Startup checks never open credential prompts.

## Development and components

Run `python -m unittest discover -s tests -p 'test_*.py'`, then
`python scripts/build_release.py`. Qt integration scripts require Painter's SDK runtime.
CREAM original code is **GPL-3.0-only**; see [LICENSE](LICENSE). You may modify and
redistribute it under GPLv3, including its source and required notices. It comes
without warranty. Microsoft texconv retains its MIT license; Montserrat and the
Righteous logo font retain their SIL Open Font Licenses. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The logo is live lowercase `cream`
in Righteous at 28 pt; the rest of the product uses CREAM. Bornie is not bundled.

See [CONTRIBUTING.md](CONTRIBUTING.md) for pull requests and
[SECURITY.md](SECURITY.md) for private vulnerability reporting. Do not post tokens,
real backer spreadsheets or private paths in issues. The publication audit and
remaining administration steps are in [docs/publication-audit.md](docs/publication-audit.md)
and [docs/github-settings-plan.md](docs/github-settings-plan.md).

## Local development without commits

Get the current main source checkout (or GitHub Code → Download ZIP), install it
once with Painter closed using Instalar.cmd, then reopen Painter. Edit the local
checkout and run **Dev.cmd**. In CREAM, use **Settings → Check for updates**, then
**Apply and reopen CREAM** to load that local build. The check sees the staged local
package first; no commit, push, GitHub release or version bump is needed.

Dev.cmd finds the running Painter's bundled Python. Alternatively use
`python scripts/dev.py` with Python 3.10+, and `--target` for a custom installation.
Python-only edits can reload CREAM; loader/updater/resource changes require a Painter
restart. Existing preview/batch/autosave and rollback safeguards remain in effect.
CREAM itself still runs inside Painter.

See [docs/development.md](docs/development.md) for the full workflow and recovery notes.

## Development and components

Run `python -m unittest discover -s tests -p 'test_*.py'`, then
`python scripts/build_release.py`. Qt integration scripts require Painter's SDK runtime.
CREAM original code is **GPL-3.0-only**; see [LICENSE](LICENSE). You may modify and
redistribute it under GPLv3, including its source and required notices. It comes
without warranty. Microsoft texconv retains its MIT license; Montserrat and the
Righteous logo font retain their SIL Open Font Licenses. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The logo is live lowercase `cream`
in Righteous at 28 pt; the rest of the product uses CREAM. Bornie is not bundled.

See [CONTRIBUTING.md](CONTRIBUTING.md) for pull requests and
[SECURITY.md](SECURITY.md) for private vulnerability reporting. Do not post tokens,
real backer spreadsheets or private paths in issues. The publication audit and
remaining administration steps are in [docs/publication-audit.md](docs/publication-audit.md)
and [docs/github-settings-plan.md](docs/github-settings-plan.md).
