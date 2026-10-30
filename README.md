# CREAM beta 1.9.5

**Color Replacement & Export Automation Manager** personalizes Trackmania 2020 skin
names/colors in Painter, exports DDS textures and packages one ZIP per skin.

## Requirements and beta compatibility

**Windows and Adobe Substance 3D Painter 12.1.3 or later.** 12.1.3 is the supported
minimum and the version used for SDK checks. Earlier versions are unverified; the old
11.0 API estimate was not a tested compatibility guarantee. No separate Python,
Excel, Pillow or DDS converter installation is required.

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
5. Reopen the window via **Window > CREAM — Batch Exporter** if needed.

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
