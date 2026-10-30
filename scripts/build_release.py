"""Build the package consumed by the installer and private GitHub updater."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cream.version import VERSION, UPDATE_RESTART


def build():
    files = [p for folder in ('cream', 'preset', 'scripts', 'tests', 'docs', '.github') for p in (ROOT / folder).rglob('*')
             if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    files += [ROOT / p for p in ('Install.cmd', 'Install.ps1', 'Dev.cmd', 
                                'LICENSE', 'THIRD_PARTY_NOTICES.md', 'CONTRIBUTING.md', 'SECURITY.md')]
    # Releases include their corresponding source, build instructions and license.
    files += [ROOT / p for p in ('README.md', 'CHANGELOG.md')]
    manifest = {'schema': 1, 'product': 'CREAM', 'module': 'cream', 'version': VERSION,
                'update': {'protocol': 1, 'restart': UPDATE_RESTART, 'min_reload_protocol': 1},
                'files': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    destination = ROOT / 'dist' / 'CREAM-plugin.zip'
    destination.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr('manifest.json', json.dumps(manifest, indent=2))
    print(destination)
    return destination


if __name__ == '__main__':
    build()
