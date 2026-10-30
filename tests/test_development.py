import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from cream import bootstrap, core
from scripts.build_release import build
from scripts import dev


class DevelopmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = build()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.target = self.root / 'plugins/cream'
        shutil.copytree(dev.ROOT / 'cream', self.target, ignore=shutil.ignore_patterns('__pycache__'))
        self.data = self.root / 'data'

    def tearDown(self):
        self.temp.cleanup()

    def stage(self, **kwargs):
        return dev.stage_local(self.target, self.data, archive=self.archive,
                               painter_process_id=os.getpid(), **kwargs)

    def test_local_stage_has_no_network_and_preserves_installed_code(self):
        original = (self.target / 'ui.py').read_bytes()
        (self.target / 'ui.py').write_bytes(original + b'\n# previous installed copy\n')
        with patch('urllib.request.build_opener', side_effect=AssertionError('No network allowed')):
            result = self.stage()
        self.assertEqual(result['restart'], 'cream')
        self.assertTrue((self.target / 'ui.py').read_bytes().endswith(b'# previous installed copy\n'))
        info = bootstrap.pending_info(self.target, self.data)
        self.assertTrue(info['pending']['local'])
        self.assertEqual(info['pending']['source'], str(dev.ROOT))
        self.assertEqual(info['pending']['process_id'], os.getpid())
        bootstrap.apply_pending(self.target, self.data, cream_only=True)
        self.assertEqual((self.target / 'ui.py').read_bytes(), original)

    def test_loader_change_really_requires_new_painter_process(self):
        with (self.target / '__init__.py').open('a') as handle:
            handle.write('\n# installed loader differs\n')
        self.assertEqual(self.stage()['restart'], 'painter')
        with self.assertRaisesRegex(RuntimeError, 'Restart'):
            bootstrap.apply_pending(self.target, self.data)

    def test_remote_pending_is_not_overwritten_implicitly(self):
        self.stage()
        marker = bootstrap.pending_path(self.target, self.data)
        value = json.loads(marker.read_text())
        value.pop('local')
        core.atomic_json(marker, value)
        before = marker.read_bytes()
        with self.assertRaisesRegex(ValueError, 'Another update'):
            self.stage()
        self.assertEqual(marker.read_bytes(), before)
        self.stage(replace_pending=True)

    def test_repeat_local_stage_and_invalid_target(self):
        first = self.stage()
        stage = bootstrap.pending_info(self.target, self.data)['stage']
        self.stage()
        self.assertTrue(Path(stage).is_dir())
        self.assertTrue(Path(first['marker']).samefile(bootstrap.pending_path(self.target, self.data)))
        with self.assertRaisesRegex(ValueError, 'source checkout'):
            dev.stage_local(dev.ROOT / 'cream', self.data, archive=self.archive)

    def test_source_syntax_is_checked(self):
        source = self.root / 'source/cream'
        source.mkdir(parents=True)
        (source / 'broken.py').write_text('if :\n')
        with self.assertRaises(SyntaxError):
            dev.validate_sources(source.parent)
