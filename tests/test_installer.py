"""Run the real PowerShell installer against isolated fixture directories."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.name == 'nt', 'Windows installer')
class InstallerTests(unittest.TestCase):
    def test_install_migration_and_rollback(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([
                'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                str(root / 'scripts/check_installer.ps1'), '-SourceRoot', str(root),
                '-TestRoot', folder], capture_output=True, text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
