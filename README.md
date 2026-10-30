# CREAM

**Color Replacement & Export Automation Manager**

Windows plugin for Adobe Substance 3D Painter: customize player names and colors
from CSV/XLSX, export TM2020 textures, convert to DDS and build one ZIP per backer.

See [LEIA-ME.md](LEIA-ME.md) for installation and usage (in English).
Tested against the Painter 12.1.3 SDK; API minimum 11.0 is not validated on that version.

## Updates

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

Select columns for name, three colors, ID, ZIP name and active flag. Only name is
required. Original template headers and existing CSV values remain supported.
Names are limited to 20 Unicode code points after NFC normalization. Colors are sRGB
`#RRGGBB`; omitted colors use the original project color.

Normals are generated as Normal_OpenGL before conversion. Green is preserved.
The output DDS identifiers are DXT1 (B/AO), DXT5 (I), BC5U (R/N) and BC4U
(CoatR/DirtMask). ATI aliases are relabeled without changing compressed pixels.
Copy ZIPs directly into CarSport for upload; subfolders can cause C-AA-00-03.

## Development

Run `python -m unittest discover -s tests -p "test_*.py"` (Pillow for real DDS tests).
Run `scripts/check_columns_ui.py` and `scripts/check_runtime_reload.py` with Painter's
SDK Python and Qt platform configured for offscreen testing.
Run `python scripts/build_release.py` to create `dist/CREAM-plugin.zip`.

Set `VERSION` and `UPDATE_RESTART` in `kr7_batch/version.py` for each release.
The manifest uses `update: {protocol: 1, restart: "cream"|"painter", min_reload_protocol: 1}`.
Use `painter` for releases explicitly requiring it. The runtime additionally forces
Painter restart for protected or non-Python changes, including removed files.
Older packages without compatible metadata always require Painter restart.

The GitHub Actions workflow tests, builds and publishes the stable asset on version changes.
The repository is private, without an open-source license. The bundled texconv retains
Microsoft's MIT license in `kr7_batch/bin`.
