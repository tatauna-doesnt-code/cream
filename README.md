<p align="center">
  <img src="docs/assets/cream-logo.png" width="240" alt="cream — CREAM logo in Righteous">
</p>

**Color Replacement & Export Automation Manager**

## TL;DR

CREAM turns your Painter project into a **Trackmania 2020 skin ZIP**, handling DDS conversion, ZIP packaging and in-game filename styling. Batch export is optional.

1. [Download](https://github.com/tatauna-doesnt-code/cream/releases) **CREAM-plugin.zip**, extract it, close Painter and run **Install.cmd**.
2. Reopen Painter, enable **Python → CREAM**, open your project and click the **c** icon in the Plugins toolbar.
3. In CREAM, choose an output folder in **Settings**, select a template, textures and resolutions in **Textures**, and set the **Skin ZIPfile name**.
4. Click **Export current skin**. Use **Batch** only when you need multiple skins.

**Beta 1.13.0 · Windows · Painter 8.1.2+**

[Download](https://github.com/tatauna-doesnt-code/cream/releases) · [Report a bug](https://github.com/tatauna-doesnt-code/cream/issues) · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md)

## Features

- Select an installed export template and discover the actual texture sets and outputs of the open project, with resolution controls per set and per texture.
- Convert to the DDS formats Trackmania expects, package the selected textures into a ZIP. Optionally reuse a base ZIP to preserve its other files.
- Name ZIPs with configurable patterns and an optional **Trackmania WYSIWYG editor**: bold, italic, uppercase, shadow, widths and three-digit text colors.
- On compatible versions, change player-name font fills and up to three Base Colors. Font layout and other layer channels stay as you set them in Painter.
- Export batches with safe cancellation, reports, resume and original-value recovery.

No separate Python, Excel, image library or DDS converter installation is needed to use CREAM.

## Export templates and texture overrides

CREAM looks for one installed **TM2020** export template. If it cannot find an unambiguous match, choose a template in **Textures**. The dropdown identifies duplicate template names by their resource URL. Click Refresh after editing a template in Painter. No preset is installed or overwritten by CREAM.

Only the current project's texture sets are listed. Each template output has an export checkbox, a suffix input, BC1/BC3/BC4/BC5 compression and a resolution control. CREAM preserves the template's channel packing and normal convention. Unknown suffixes default to **BC3** to preserve alpha and display a warning; choose the required format before exporting.

The first suffix/compression edit asks for confirmation. Overrides become **_bold italic_**, with a restore icon for each value; the Textures tab gains an asterisk. Yellow icons explain unknown suffixes or combinations that differ from the TM2020 reference table. These are advisories, so intentional custom formats can export. Unsafe filenames and duplicate destinations are blocked.

Open **TM2020 textures reference table** in Textures or Help for the suffix/content/compression table. Overrides and selections are saved by project, template URL, texture set and output identity; edits are retained through CREAM reloads.

**Painter 8.1.2–9.x:** library templates are discovered through the older resource API. CREAM predicts output names and temporarily exports the full template for each selected output/resolution, then packages only your selections. This can be slower. The newer API for inspecting template channel definitions is available from Painter 10. Pre-8.3 builds use the host Qt application version because Adobe introduced the application-version API in 8.3. Unknown host versions fail closed with an explanation. See [Adobe’s Python API changelog](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/api/changelog) for the version/API boundaries. Projects with UDIMs, material layering or template output subfolders remain unsupported.

The 8.1.2–9.x paths are tested with real Qt5 and simulated Painter APIs, including real DDS/ZIP processing. Native installations still need beta testing; documentation support is not a claim that every old build has been tested.

## Painter compatibility

CREAM checks the **actual application version**, including on Steam. Unsupported controls stay visible, grayed out, with an explanation. Opening CREAM on a version older than **10.1.2** shows a warning.

| Painter version | Mode | What to expect |
| --- | --- | --- |
| Below 8.1.2 | Unsupported | Export and customization are disabled. |
| **8.1.2–9.1.x** | Export only | Export the existing project, convert to DDS, build ZIPs and style their names. Changing names/colors on the car and customization previews/restoration are disabled. |
| **10.0.0–10.1.1** | Full features, with a warning | Customization is available. Upgrade to at least **10.1.2** for a more stable layer-stack API experience. |
| **10.1.2–11.x** | Full features | Compatibility adapters handle Qt bindings and the older texture-set naming API. |
| **12.x** | Full features | **12.1.3** is the version used for native SDK checks. |

Older-version paths have automated compatibility checks, but still need real-project beta testing inside those Painter releases. This table describes feature availability, not a claim that every build has been tested.

| Feature | 8.1.2–9.x | 10.0.0–10.1.1 | 10.1.2+ |
| --- | :---: | :---: | :---: |
| Texture selection, resolutions and export | ✓ | ✓ | ✓ |
| DDS conversion and base-ZIP packaging | ✓ | ✓ | ✓ |
| Filename patterns and TM styling editor | ✓ | ✓ | ✓ |
| Manual entries, CSV/XLSX import and column mapping | ✓ | ✓ | ✓ |
| Logs, reports, cancellation, resume and updates | ✓ | ✓ | ✓ |
| Change `PLAYER_NAME` font fills | — | ✓* | ✓ |
| Change `PLAYER_COLOR1–3` Base Colors | — | ✓* | ✓ |
| Preview and restore customization | — | ✓* | ✓ |
| Read original layer colors for filename tokens | — | ✓* | ✓ |

\* Available with the stability warning. Adobe introduced layer editing and font APIs in [Painter 10.0](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/release-notes/old-versions/version-10-0), and switched to PySide6 in [10.1](https://adobedocs.github.io/painter-python-api/guides/qt6-migration/).

In export-only mode, names and the first two colors are **filename data**. They do not change the car. Color tokens need explicit entry values because layer-color lookup is unavailable in this mode.

## Installation

1. Download **CREAM-plugin.zip** from [Releases](https://github.com/tatauna-doesnt-code/cream/releases).
2. Extract the whole ZIP. Save your work and close Painter.
3. Run **Install.cmd**. Administrator access is not required. The installer backs up an existing installation. CREAM uses your installed templates and does not install or replace export presets.
4. Open Painter and enable **Python → cream**. That is the plugin's package name.
5. Click **CREAM** in Painter's Plugins toolbar, or open **Window → CREAM**. Enabling the plugin adds these launchers; it does not open the window automatically.

CREAM does **not** open its window automatically when Painter starts. Enabling the plugin adds its menu entry; open it when you need it.

For manual installation, copy `cream` into Painter's `python/plugins` folder; no preset installation is required. Painter’s plugins are under your Windows Documents folder, inside `Adobe/Adobe Substance 3D Painter`. Keep the bundled converter and fonts in the plugin folder.

### Upgrading from an older package name

For this migration, download the release ZIP, close Painter and run **Install.cmd** once. Older versions cannot apply the renamed package through their built-in updater. Enable **Python → cream** after installation.

The installer identifies previous CREAM installations by their repository identity, moves them outside Painter's plugins folder into `cream-backups`, and installs one copy under `cream`. It copies settings, protected GitHub access and recovery records into `%LOCALAPPDATA%/CREAM` without overwriting newer values. Previous data stays intact; pending updates are not carried over. Future updates use the new package normally.

## First export

1. Open a saved Painter project and prepare the textures you want to export.
2. In **CREAM's Settings tab**, select the output folder. A base ZIP is optional and can be selected in **CREAM's Batch tab**. For in-game uploads, use **CarSport directly**; uploads from subfolders can fail. The base ZIP's files must be at its root.
3. In **1 Textures**, choose maps and resolutions. Without a base ZIP, only selected textures are included. With a base ZIP, unselected files are preserved.
4. In **2 Skin ZIPfile name**, edit the plain default name `skin` in the styling editor. Trackmania styling is enabled by default; no style is applied until you choose one.
5. Click **Export current skin**. CREAM checks the configuration, exports the textures, converts to DDS and packages the ZIP.

**You don't need a batch entry.** Leave Batch empty to export the open project exactly as it is, without changing names or colors on the car. No specially named layers are required.

Existing output ZIPs are preserved. Duplicate names receive numeric suffixes.

## Customizing the car

**Requires Painter 10.0.0+.** Adding batch entries automatically enables customization. With no entries, CREAM exports the project as-is.

- **Names:** use Font resources in mask Fill effects named `PLAYER_NAME`. CREAM changes only Text. Set the font, size, placement and alignment in Painter.
- **Colors:** use Fill layers named `PLAYER_COLOR1`, `PLAYER_COLOR2` and optionally `PLAYER_COLOR3`. Base Color must be an independent uniform color. Only that channel changes. Existing anchor points can reuse those colors elsewhere.
- **Optional targets:** color-only projects don't need a name fill. Projects without customization targets can still be exported.
- **Glass:** can be exported, but is excluded from name and color changes.

Colors use `#RRGGBB`; blank fields keep the project original. Names preserve case, normalize to NFC and are limited to 20 characters. TM formatting codes belong in ZIP filenames, not the text printed on the car.

Use **Preview highlighted skin** to check a variation in Painter, then **Restore original**. Other actions explain why they are locked while a preview is active.

## Batch exports

Batch is optional. Add entries when you need several versions of the same project. Once the list contains entries, CREAM exports **only checked entries**. Selecting none does not fall back to a current-project export.

**Clear batch…** removes the entries after confirmation and returns to exporting the current project. **Clear selection** only unchecks them. The filename tab becomes **Skin ZIPfile names** when there is more than one entry.

Use **Add skin…**, **Edit skin…** and **Remove** to manage entries. Names are editable directly in the list. Overrides become **_bold italic_**; the refresh icon resets the original entry.

For larger batches, **Import CSV / XLSX…** appends spreadsheet rows. The first row must contain headers. Match your columns in the import dialog:

| Field | Required | Format |
| --- | --- | --- |
| Player name | Yes | Text, up to 20 characters |
| Colors 1–3 | No | `#RRGGBB` |
| ZIP name | No | Separate filename value; otherwise player name |
| Row ID | No | Your own identifier |
| Export / active | No | Which entries to select |

XLSX reads the **first worksheet**, regardless of its name. Formula cells are rejected. Source spreadsheets are never modified.

Manual and mixed lists are saved locally. Spreadsheet-only lists must be imported again after restarting Painter. A CREAM-only reload preserves the current list and editor state.

## ZIP filenames and TM styling

Single exports use a literal filename, initially `skin`. Variables and per-player text colors are available only when Batch contains entries. For example, `Event - {name}` adds a shared prefix.

| Token | Value |
| --- | --- |
| `{name}` | ZIP-name value, or player name if none is provided |
| `{player}` | Player name |
| `{id}` / `{row}` | Entry ID / source row number |
| `{primary}` / `{secondary}` | Colors 1 / 2, converted to three-digit TM text colors |

The editor supports bold, italic, uppercase, shadow, normal/narrow/wide text and **three-digit** colors, including each entry's primary/secondary color. Montserrat previews approximate game rendering.

TM styling is **on by default** each new session. Turning the helper off hides the editor; it doesn't remove codes already in the pattern.

## Texture formats

| Map | DDS compression |
| --- | --- |
| Base Color `_B` / Ambient Occlusion `_AO` | BC1 / DXT1 |
| Roughness + Metallic `_R` / Normals `_N` | BC5 / BC5U |
| Emissive `_I` | BC3 / DXT5 |
| Coat Roughness `_CoatR` / Dirt Mask `_DirtMask` | BC4 / BC4U |

The selected template controls the normal convention; CREAM does not flip channels. DDS files have no additional mipmaps. Wheels keep **1:4 proportions**; other sets use square 1024, 2048 or 4096 outputs.

Painter 8.1.2–9.x uses the chosen library template directly and temporarily exports all of its maps for each selection. Painter 10+ reads individual output definitions. No bundled preset is required.

UDIM and material layering are not supported by this beta.

## Cancellation, recovery and updates

**Cancel safely** waits for the current operation. Completed ZIPs remain available; partial ZIPs aren't published. Customization runs restore original values. Export-only runs don't edit layers or create customization recovery records. No per-player SPP is saved; temporary textures are cleaned up after processing.

To resume, choose **Resume a previous batch…** and a JSON report from `_CREAM_reports` in the output folder. Matching successful entries whose ZIPs still exist are unchecked. Review the remaining selection and export again. The project, settings and customization mode must match.

After an interrupted customization run, use **Logs → Restore original / recover project** with the original project open. Restoring layer values requires Painter 10.0+.

Updates are in **CREAM's Settings tab**. Check, download and follow the apply/restart instructions. Some Python changes only need CREAM to reopen; loader or resource changes need a Painter restart. **This compatibility update requires one Painter restart.**

Public releases need no token. While the repository is private, testers need access and a fine-grained GitHub token with **Contents: Read-only** for this repository. CREAM asks when needed and protects the saved credential with Windows encryption.

## Local development

No commits or online releases are needed to test changes:

1. Clone the repository or download its source ZIP, then install once with **Install.cmd**.
2. Open Painter and CREAM. Edit the source and run **Dev.cmd**.
3. In **CREAM's Settings tab → Check for updates**, apply the local build or restart Painter when requested.

See [the development guide](docs/development.md). To run core tests and build a package with a separate Python installation:

```sh
python -m pip install Pillow
python -m unittest discover -s tests -p "test_*.py"
python scripts/build_release.py
```

Qt integration checks also exercise the interface and batch controller with Painter API stubs. Native Painter testing remains necessary for real project behavior on each supported version.

## Contributing and support

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). For bugs, include your Painter version, reproduction steps and relevant Logs. A small reproducible example helps a lot. Keep private spreadsheets, tokens and personal paths out of public reports.

Report security issues privately as described in [SECURITY.md](SECURITY.md).

## License

CREAM's original code is **GPL-3.0-only**. You can modify and redistribute it under GPLv3, including corresponding source and notices. It comes without warranty. See [LICENSE](LICENSE).

Microsoft texconv uses MIT; Montserrat and the Righteous logo font use the SIL Open Font License. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
