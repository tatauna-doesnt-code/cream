import io
import os
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kr7_batch import bootstrap, core, updater
from scripts.build_release import build
from kr7_batch.version import VERSION


class UpdateTests(unittest.TestCase):
    def test_versions(self):
        self.assertGreater(updater.version_tuple('v1.10.0'), updater.version_tuple('1.9.0'))
        with self.assertRaises(ValueError):
            updater.version_tuple('v1.2.3-beta')

    def test_traversal_rejected(self):
        for name in ('../evil', '/evil', 'kr7_batch/../../evil', 'C:/evil', 'a\\b', 'a/CON.py', 'a./b'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                bootstrap.safe_relative(name)

    def test_private_check(self):
        release = {'tag_name': 'v1.2.0', 'assets': [{'name': 'CREAM-plugin.zip', 'state': 'uploaded',
                   'digest': 'sha256:' + 'a'*64, 'id': 123, 'size': 100}]}
        with patch.object(updater, '_request', return_value=io.BytesIO(json.dumps(release).encode())):
            self.assertEqual(updater.check_latest(token='test')['version'], '1.2.0')
        with patch.object(updater, '_request', return_value=io.BytesIO(json.dumps(release).encode())):
            self.assertIsNone(updater.check_latest(current='1.2.0', token='test'))

    @unittest.skipUnless(os.environ.get('CREAM_TEST_DPAPI') == '1', 'Enable in a normal Windows user session; sandbox has no DPAPI profile')
    def test_dpapi(self):
        with tempfile.TemporaryDirectory() as directory:
            updater.save_token('test-token-not-a-credential', directory)
            self.assertNotIn(b'test-token', updater.token_path(directory).read_bytes())
            self.assertEqual(updater.load_token(directory), 'test-token-not-a-credential')

    def test_stage_apply_and_rollback(self):
        archive = build()
        payload = archive.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root/'plugins'/'kr7_batch'
            target.mkdir(parents=True)
            (target/'__init__.py').write_text('original')
            data = root/'data'
            release = {'id': 1, 'version': VERSION, 'size': len(payload), 'sha256': bootstrap.sha256(archive)}
            with patch.object(updater, '_request', return_value=io.BytesIO(payload)):
                updater.stage_release(release, target, threading.Event(), data, token='test')
            self.assertEqual((target/'__init__.py').read_text(), 'original')
            original_rename = bootstrap.os.rename
            def fail_swap(source, destination):
                if Path(source).name.startswith('.cream-next-'):
                    raise OSError('simulated locked file')
                original_rename(source, destination)
            with patch.object(bootstrap.os, 'rename', side_effect=fail_swap), self.assertRaises(OSError):
                bootstrap.apply_pending(target, data)
            self.assertEqual((target/'__init__.py').read_text(), 'original')
            result = bootstrap.apply_pending(target, data)
            self.assertEqual(result['version'], VERSION)
            self.assertEqual((Path(result['backup'])/'__init__.py').read_text(), 'original')
            self.assertFalse(bootstrap.pending_path(target, data).exists())

    def test_modified_package_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            updater.extract_verified(build(), directory)
            (Path(directory)/'kr7_batch/core.py').write_text('tampered')
            with self.assertRaises(ValueError):
                bootstrap.read_manifest(directory)

    def test_redirect_removes_token(self):
        import urllib.request
        req = urllib.request.Request('https://api.github.com/repos/tatauna-doesnt-code/cream/releases/assets/1', headers={'Authorization': 'Bearer test'})
        result = updater._GitHubRedirect().redirect_request(req, None, 302, '', {}, 'https://release-assets.githubusercontent.com/asset')
        self.assertIsNone(result.get_header('Authorization'))
        with self.assertRaises(RuntimeError):
            updater._GitHubRedirect().redirect_request(req, None, 302, '', {}, 'https://example.org/asset')


if __name__ == '__main__':
    unittest.main()
