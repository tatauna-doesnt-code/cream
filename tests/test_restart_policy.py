import json
from pathlib import Path
import shutil
import tempfile
import unittest

from kr7_batch import bootstrap, core


class RestartPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.target = self.root / 'plugins' / 'kr7_batch'
        self.target.mkdir(parents=True)
        for name in ('__init__.py', 'bootstrap.py', 'updater.py', 'ui.py', 'core.py', 'version.py', 'painter.py', 'bin/texconv.exe'):
            path = self.target / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b'original')
        self.data = self.root / 'data'
        self.stage = self.data / 'updates' / 'test'
        shutil.copytree(self.target, self.stage / 'kr7_batch')

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self, **policy):
        return {'schema': 1, 'product': 'CREAM', 'module': 'kr7_batch', 'version': '9.0.0',
                'update': dict(protocol=1, restart='cream', min_reload_protocol=1, **policy),
                'files': {p.relative_to(self.stage).as_posix(): bootstrap.sha256(p)
                          for p in self.stage.rglob('*') if p.is_file() and p.name != 'manifest.json'}}

    def stage_marker(self, manifest):
        core.atomic_json(self.stage / 'manifest.json', manifest)
        core.atomic_json(bootstrap.pending_path(self.target, self.data), {
            'target': str(self.target.resolve()), 'stage': 'test', 'version': '9.0.0',
            'process_id': bootstrap.os.getpid(), 'manifest_sha256': bootstrap.sha256(self.stage / 'manifest.json')})

    def test_python_changes_allow_reload(self):
        (self.stage / 'kr7_batch/ui.py').write_bytes(b'new UI')
        m = self.manifest()
        self.assertEqual(bootstrap.restart_requirement(self.target, m)[0], 'cream')
        self.stage_marker(m)
        result = bootstrap.apply_pending(self.target, self.data, cream_only=True)
        self.assertEqual((self.target / 'ui.py').read_bytes(), b'new UI')
        bootstrap.rollback_applied(self.target, result, self.data)
        self.assertEqual((self.target / 'ui.py').read_bytes(), b'original')
        self.assertEqual(bootstrap.pending_info(self.target, self.data)['restart'], 'painter')
        with self.assertRaisesRegex(RuntimeError, 'Restart'):
            bootstrap.apply_pending(self.target, self.data, cream_only=True)

    def test_loader_native_and_unknown_files_override_declaration(self):
        for name in ('__init__.py', 'bootstrap.py', 'updater.py', 'bin/texconv.exe', 'native.pyd', 'config.json'):
            with self.subTest(name=name):
                path = self.stage / 'kr7_batch' / name
                previous = path.read_bytes() if path.exists() else None
                path.write_bytes(b'changed')
                self.assertEqual(bootstrap.restart_requirement(self.target, self.manifest())[0], 'painter')
                if previous is None:
                    path.unlink()
                else:
                    path.write_bytes(previous)

    def test_removed_files_are_classified(self):
        (self.stage / 'kr7_batch/bootstrap.py').unlink()
        self.assertEqual(bootstrap.restart_requirement(self.target, self.manifest())[0], 'painter')

    def test_missing_unknown_or_explicit_restart_policy_is_conservative(self):
        for policy in (None, {}, {'protocol': 99}, {'protocol': 1, 'restart': 'cream', 'min_reload_protocol': 2},
                       {'protocol': 1, 'restart': 'painter', 'min_reload_protocol': 1}):
            with self.subTest(policy=policy):
                m = self.manifest()
                m['update'] = policy
                self.assertEqual(bootstrap.restart_requirement(self.target, m)[0], 'painter')

    def test_restart_required_cannot_be_bypassed_by_disabling_plugin(self):
        (self.stage / 'kr7_batch/updater.py').write_bytes(b'new updater')
        self.stage_marker(self.manifest())
        with self.assertRaisesRegex(RuntimeError, 'Restart Substance'):
            bootstrap.apply_pending(self.target, self.data)
        self.assertEqual((self.target / 'updater.py').read_bytes(), b'original')
        marker = bootstrap.pending_path(self.target, self.data)
        pending = json.loads(marker.read_text())
        pending['process_id'] = -1
        core.atomic_json(marker, pending)
        bootstrap.apply_pending(self.target, self.data)
        self.assertEqual((self.target / 'updater.py').read_bytes(), b'new updater')

    def test_tampering_after_staging_is_rejected(self):
        self.stage_marker(self.manifest())
        (self.stage / 'kr7_batch/core.py').write_bytes(b'tampered')
        with self.assertRaises(ValueError):
            bootstrap.pending_info(self.target, self.data)
