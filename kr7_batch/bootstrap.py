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
        raise ValueError("O pacote não é uma atualização CREAM válida.")
    files = manifest.get("files", {})
    required = {"kr7_batch/__init__.py", "kr7_batch/bootstrap.py", "kr7_batch/updater.py",
                "kr7_batch/version.py", "kr7_batch/core.py", "kr7_batch/painter.py", "kr7_batch/ui.py",
                "kr7_batch/bin/texconv.exe"}
    if not isinstance(files, dict) or not required.issubset(files):
        raise ValueError("O pacote CREAM está incompleto.")
    if len({name.casefold() for name in files}) != len(files):
        raise ValueError("Arquivos duplicados no manifesto.")
    for name, digest in files.items():
        safe_relative(name)
        path = root / name
        if path.is_symlink() or not path.is_file() or sha256(path) != digest:
            raise ValueError("A integridade do pacote falhou: " + name)
    actual = {p.relative_to(root).as_posix() for p in (root / "kr7_batch").rglob("*") if p.is_file()}
    expected = {name for name in files if name.startswith("kr7_batch/")}
    if actual != expected:
        raise ValueError("Arquivos inesperados no plugin da atualização.")
    return manifest


def safe_relative(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or "\\" in name or ":" in name
            or any(part in ("..", ".", "") or part.endswith((".", " ")) for part in name.split("/"))):
        raise ValueError("Caminho inválido no pacote de atualização.")
    if any(part.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *("COM" + str(i) for i in range(1, 10)), *("LPT" + str(i) for i in range(1, 10))} for part in path.parts):
        raise ValueError("Nome de arquivo reservado pelo Windows.")
    return path


def apply_pending(target, data_dir=DATA):
    """Validate, stage on the same volume, swap directories, and roll back on error."""
    target = Path(target).resolve()
    marker = pending_path(target, data_dir)
    if not marker.exists():
        return None
    pending = json.loads(marker.read_text(encoding="utf-8"))
    if pending.get("target") != str(target) or target.name != "kr7_batch":
        raise ValueError("Destino da atualização não corresponde a este plugin.")
    updates = (Path(data_dir) / "updates").resolve()
    stage = (updates / pending["stage"]).resolve()
    if stage.parent != updates or stage.is_symlink():
        raise ValueError("Pasta de atualização inválida.")
    manifest = read_manifest(stage)
    if manifest["version"] != pending["version"] or sha256(stage / "manifest.json") != pending["manifest_sha256"]:
        raise ValueError("O manifesto da atualização mudou após o download.")
    next_dir = target.parent / (".cream-next-" + uuid.uuid4().hex)
    backup_root = target.parent.parent / "cream-backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    backup = backup_root / ("kr7_batch-" + uuid.uuid4().hex)
    moved_old = False
    try:
        shutil.copytree(stage / "kr7_batch", next_dir)
        for name, digest in manifest["files"].items():
            if name.startswith("kr7_batch/") and sha256(next_dir / name[len("kr7_batch/"):]) != digest:
                raise ValueError("Cópia da atualização falhou na verificação.")
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
        return {"version": manifest["version"], "backup": str(backup)}
    finally:
        if next_dir.exists():
            shutil.rmtree(next_dir)
        # A complete old copy is intentionally retained after successful activation.
