"""Stage an uncommitted working copy for Painter's existing safe reload flow."""
import argparse
import ast
import ctypes
import csv
import io
import json
import os
from pathlib import Path
import shutil
import sys
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cream import bootstrap, core, updater


def default_target():
    documents = Path.home() / 'Documents'
    if os.name == 'nt':
        buffer = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer) == 0:
            documents = Path(buffer.value)
    return documents / 'Adobe/Adobe Substance 3D Painter/python/plugins/cream'


def validate_sources(root=ROOT):
    for path in (Path(root) / 'cream').rglob('*.py'):
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))


def painter_pid():
    if os.name != 'nt':
        return -1
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Adobe Substance 3D Painter.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True, check=True,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    pids = [int(row[1]) for row in csv.reader(io.StringIO(result.stdout))
            if len(row) > 1 and row[0].casefold() == 'adobe substance 3d painter.exe']
    if len(pids) > 1:
        raise ValueError('Multiple Painter processes are running; pass --painter-pid for the instance to update.')
    return pids[0] if pids else -1


def stage_local(target, data_dir=bootstrap.DATA, archive=None, replace_pending=False, painter_process_id=None):
    target, data_dir = Path(target).resolve(), Path(data_dir).resolve()
    if target == (ROOT / 'cream').resolve():
        raise ValueError('Target must be the installed copy, not your source checkout.')
    if target.name != 'cream' or not (target / '__init__.py').is_file():
        raise ValueError('Install CREAM with Install.cmd first, or pass --target for your installed plugin folder.')
    marker = bootstrap.pending_path(target, data_dir)
    if marker.exists() and not replace_pending:
        previous = json.loads(marker.read_text(encoding='utf-8'))
        if not previous.get('local') or previous.get('source') != str(ROOT):
            raise ValueError('Another update is staged. Apply it first, or explicitly use --replace-pending.')
    validate_sources()
    process_id = painter_pid() if painter_process_id is None else painter_process_id
    if archive is None:
        from scripts.build_release import build
        archive = build()
    updates = data_dir / 'updates'
    updates.mkdir(parents=True, exist_ok=True)
    stage = updates / uuid.uuid4().hex
    stage.mkdir()
    committed = False
    try:
        manifest = updater.extract_verified(archive, stage)
        restart, reason = bootstrap.restart_requirement(target, manifest)
        core.atomic_json(marker, {'target': str(target), 'stage': stage.name,
            'version': manifest['version'], 'process_id': process_id,
            'manifest_sha256': bootstrap.sha256(stage / 'manifest.json'),
            'local': True, 'source': str(ROOT)})
        committed = True
        return {'restart': restart, 'reason': reason, 'marker': str(marker)}
    finally:
        if not committed:
            shutil.rmtree(stage, ignore_errors=True)
        # Keep superseded stages: Painter might still be reading an older marker.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, default=default_target())
    parser.add_argument('--replace-pending', action='store_true')
    parser.add_argument('--painter-pid', type=int, help='Running Painter process ID when multiple instances are open')
    args = parser.parse_args()
    result = stage_local(args.target, replace_pending=args.replace_pending, painter_process_id=args.painter_pid)
    print('Local build staged. No Git commit, push or network request was made.')
    print('In CREAM: Settings > Check for updates (detects the local build first).')
    print('Then Apply and reopen CREAM.' if result['restart'] == 'cream' else 'Save your project and restart Painter to apply it.')
    print(result['reason'])


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Local build not staged: ' + str(exc), file=sys.stderr)
        sys.exit(1)
