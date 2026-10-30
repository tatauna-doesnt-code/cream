# Local development without commits

CREAM runs inside Painter, not as a standalone desktop application. You can edit
any local source checkout or GitHub Code → Download ZIP; commits, pushes and releases
are not needed to test changes. The repository is private until publication, so
downloading the initial checkout currently requires repository access.

## One-time setup

1. Get the current repository source, preserving its directory structure. Use main's
   source checkout rather than an older installer ZIP that predates Dev.cmd.
2. Close Painter and run Instalar.cmd from that source folder to install a copy.
3. Open Painter and enable Python → kr7_batch. Open a test project.

## Edit → stage → reload

1. Edit files in the source checkout using any editor.
2. Save them and run **Dev.cmd** from the checkout. While Painter is running, it
   locates Painter's bundled Python, so a separate Python installation is unnecessary.
3. In CREAM, open **Settings → Check for updates**. It checks the locally staged
   build before contacting GitHub; no online release or version bump is required.
4. Click **Apply and reopen CREAM** for reloadable Python changes. If the loader,
   bootstrap, updater, fonts, executable or other resources changed, save your
   project and restart Painter instead, as instructed.
5. Repeat after each edit. No Git operations occur in this loop.

Prefer a terminal? With Python 3.10+:

```powershell
python scripts/dev.py
# Custom installed location:
python scripts/dev.py --target 'C:\path\to\Painter\python\plugins\kr7_batch'
```

To select an interpreter explicitly:

```powershell
powershell -File scripts/dev.ps1 -Python 'C:\path\to\python.exe'
```

The target is the **installed copy**, never the checkout. Editing checkout files
alone does not change Painter's already-loaded modules. This workflow stages a
validated package and applies it through CREAM's transactional updater; it uses no
junctions or symlinks and never replaces the source checkout.

## Safety and recovery

Python syntax and package hashes are checked before staging. An existing downloaded
release is not replaced without an explicit --replace-pending (or -ReplacePending)
option. Repeated builds from the same checkout may replace their own local marker;
superseded stage directories are retained to avoid races with Painter.

Finish background updates/batches and restore any preview before applying a build.
Existing busy/autosave, worker and recovery guards apply. Loaded rows and current UI
state survive eligible reloads. Import failures roll back installed files/modules;
fix the checkout and stage a new build. Restart Painter if required by the recovery
message. Installations are backed up under python/cream-backups.

Keep development builds separate from production projects. This does not provide
a standalone model preview or simulate Painter's native APIs outside Painter.

## Tests and release builds

```powershell
python -m pip install Pillow
python -m unittest discover -s tests -p 'test_*.py'
python scripts/build_release.py
```

The first commands run outside Painter; Qt integration scripts under scripts/check_*
use Painter's SDK Python with the Qt platform environment configured as documented
in their source. A local build includes uncommitted/untracked source files from the
packaged directories: review the package before distributing it.

Builds are stored in dist/CREAM-plugin.zip; stage/recovery data uses the current
user's local CREAM data directory (legacy name KR7BatchExporter). Local source paths
are recorded only in that user's staging marker, not as shared package defaults.
