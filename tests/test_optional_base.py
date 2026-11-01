from pathlib import Path
import tempfile
import threading
import unittest
import zipfile
from cream import core


class OptionalBaseTests(unittest.TestCase):
    def test_no_base_packages_only_exports_and_preserves_existing_zip(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'Skin_B.dds'
            source.write_bytes(b'exported texture')
            output = root / 'skin.zip'
            core.build_zip(None, {'Skin_B.dds': source}, output, threading.Event())
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.namelist(), ['Skin_B.dds'])
                self.assertEqual(archive.read('Skin_B.dds'), source.read_bytes())
            original = output.read_bytes()
            with self.assertRaises(FileExistsError):
                core.build_zip(None, {'Skin_B.dds': source}, output, threading.Event())
            self.assertEqual(output.read_bytes(), original)
            self.assertFalse(list(root.glob('*.partial')))

    def test_no_base_cancel_never_publishes_partial_zip(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'Skin_B.dds'
            source.write_bytes(b'texture')
            cancel = threading.Event()
            cancel.set()
            with self.assertRaises(core.Cancelled):
                core.build_zip(None, {'Skin_B.dds': source}, root / 'skin.zip', cancel)
            self.assertFalse((root / 'skin.zip').exists())
            self.assertFalse(list(root.glob('*.partial')))

    def test_explicit_invalid_base_explains_how_to_clear_it(self):
        with tempfile.TemporaryDirectory() as folder:
            for path in (Path(folder), Path(folder) / 'missing.zip'):
                with self.assertRaisesRegex(ValueError, 'Batch, or clear the field'):
                    core.inspect_base(path)
