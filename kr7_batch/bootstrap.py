"""Small, standard-library-only updater bootstrap; runs before importing Painter UI."""
import hashlib
import importlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import uuid

DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "KR7BatchExporter"
MAX_UNPACKED = 150 * 1024 * 1024
RELOAD_PROTOCOL = 1
RESTART_FILES = {"__init__.py", "bootstrap.py", "updater.py"}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pending_path(target, data_dir=DATA):
    key = hashlib.sha256(str(Path(target).resolve()).casefold().encode()).hexdigest()[:20]
    return Path(data_dir) / ("update-" + key + ".json")


def read_manifest(root):
    root = Path(root).resolve()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("product") != "CREAM" or manifest.get("schema") != 1 or manifest.get("module") != "kr7_batch":
        raise ValueError("This is not a valid CREAM update package.")
    files = manifest.get("files", {})
    required = {"kr7_batch/__init__.py", "kr7_batch/bootstrap.py", "kr7_batch/updater.py",
                "kr7_batch/version.py", "kr7_batch/core.py", "kr7_batch/painter.py", "kr7_batch/ui.py",
                "kr7_batch/bin/texconv.exe"}
    if not isinstance(files, dict) or not required.issubset(files):
        raise ValueError("The CREAM package is incomplete.")
    if len({name.casefold() for name in files}) != len(files):
        raise ValueError("Duplicate files in the manifest.")
    for name, digest in files.items():
        safe_relative(name)
        path = root / name
        if path.is_symlink() or not path.is_file() or sha256(path) != digest:
            raise ValueError("Package integrity check failed: " + name)
    actual = {p.relative_to(root).as_posix() for p in (root / "kr7_batch").rglob("*") if p.is_file()}
    expected = {name for name in files if name.startswith("kr7_batch/")}
    if actual != expected:
        raise ValueError("Unexpected files in the update plugin.")
    return manifest


def safe_relative(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or "\\" in name or ":" in name
            or any(part in ("..", ".", "") or part.endswith((".", " ")) for part in name.split("/"))):
        raise ValueError("Invalid path in the update package.")
    if any(part.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *("COM" + str(i) for i in range(1, 10)), *("LPT" + str(i) for i in range(1, 10))} for part in path.parts):
        raise ValueError("Reserved Windows filename.")
    return path


def restart_requirement(target, manifest):
    """A release declaration is necessary but never overrides changed loader/native files."""
    policy = manifest.get("update", {})
    if (not isinstance(policy, dict) or policy.get("protocol") != RELOAD_PROTOCOL
            or policy.get("restart") not in ("cream", "painter")
            or type(policy.get("min_reload_protocol")) is not int
            or not 1 <= policy["min_reload_protocol"] <= RELOAD_PROTOCOL):
        return "painter", "This package has no compatible CREAM reload policy."
    if policy["restart"] == "painter":
        return "painter", "This release requires a Painter restart."
    target = Path(target)
    old = {p.relative_to(target).as_posix(): sha256(p) for p in target.rglob("*")
           if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    new = {name[len("kr7_batch/"):]: digest for name, digest in manifest["files"].items()
           if name.startswith("kr7_batch/")}
    for name in sorted(old.keys() | new.keys()):
        if old.get(name) == new.get(name):
            continue
        if name in RESTART_FILES or Path(name).suffix != ".py":
            return "painter", "The loader, updater, or a non-Python component has changed: " + name
    return "cream", "Only reloadable Python modules have changed."


def pending_info(target, data_dir=DATA):
    """Revalidate the staged package before displaying or executing its restart policy."""
    target = Path(target).resolve()
    marker = pending_path(target, data_dir)
    if not marker.exists():
        return None
    pending = json.loads(marker.read_text(encoding="utf-8"))
    if pending.get("target") != str(target) or target.name != "kr7_batch":
        raise ValueError("The update target does not match this plugin.")
    updates = (Path(data_dir) / "updates").resolve()
    stage = (updates / pending["stage"]).resolve()
    if stage.parent != updates or stage.is_symlink():
        raise ValueError("Invalid update directory.")
    manifest = read_manifest(stage)
    if manifest["version"] != pending["version"] or sha256(stage / "manifest.json") != pending["manifest_sha256"]:
        raise ValueError("The update manifest changed after download.")
    restart, reason = restart_requirement(target, manifest)
    if pending.get("force_painter"):
        restart, reason = "painter", "Reload failed previously. Restart Painter to apply this update."
    return {"version": manifest["version"], "restart": restart, "reason": reason,
            "manifest": manifest, "pending": pending, "stage": str(stage)}


def apply_pending(target, data_dir=DATA, cream_only=False):
    """Validate, stage on the same volume, swap directories, and roll back on error."""
    target = Path(target).resolve()
    info = pending_info(target, data_dir)
    if info is None:
        return None
    pending, manifest, stage = info["pending"], info["manifest"], Path(info["stage"])
    if info["restart"] == "painter" and (cream_only or pending.get("process_id") == os.getpid()):
        raise RuntimeError("Restart Substance 3D Painter to apply this update. " + info["reason"])
    marker = pending_path(target, data_dir)
    next_dir = target.parent / (".cream-next-" + uuid.uuid4().hex)
    backup_root = target.parent.parent / "cream-backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    backup = backup_root / ("kr7_batch-" + uuid.uuid4().hex)
    moved_old = False
    try:
        shutil.copytree(stage / "kr7_batch", next_dir)
        for name, digest in manifest["files"].items():
            if name.startswith("kr7_batch/") and sha256(next_dir / name[len("kr7_batch/"):]) != digest:
                raise ValueError("Update copy verification failed.")
        os.rename(target, backup)
        moved_old = True
        try:
            os.rename(next_dir, target)
        except Exception:
            os.rename(backup, target)
            moved_old = False
            raise
        marker.unlink()
        importlib.invalidate_caches()
        return {"version": manifest["version"], "backup": str(backup), "pending": pending}
    finally:
        if next_dir.exists():
            shutil.rmtree(next_dir)
        # A complete old copy is intentionally retained after successful activation.


def rollback_applied(target, applied, data_dir=DATA):
    """Restore the old files if importing the new Python UI fails."""
    target = Path(target).resolve()
    backup = Path(applied["backup"]).resolve()
    if backup.parent != (target.parent.parent / "cream-backups").resolve() or not backup.is_dir():
        raise ValueError("The update backup is unavailable.")
    failed = backup.parent / ("failed-" + uuid.uuid4().hex)
    os.rename(target, failed)
    try:
        os.rename(backup, target)
    except Exception:
        os.rename(failed, target)
        raise
    pending = dict(applied["pending"], force_painter=True, process_id=os.getpid())
    marker = pending_path(target, data_dir)
    temp = marker.with_suffix(".tmp")
    temp.write_text(json.dumps(pending), encoding="utf-8")
    os.replace(temp, marker)
    importlib.invalidate_caches()
