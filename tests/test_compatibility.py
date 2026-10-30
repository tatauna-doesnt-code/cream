import ast
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from kr7_batch.compatibility import Capabilities, texture_set_name

ROOT = Path(__file__).resolve().parents[1]


class CompatibilityTests(unittest.TestCase):
    def test_version_boundaries_and_warnings(self):
        for version, export, customization, qt6, warn in [
            ((8, 3, 1), False, False, False, True),
            ((9, 0, 0), True, False, False, True),
            ((9, 1, 2), True, False, False, True),
            ((10, 0, 0), True, True, False, True),
            ((10, 1, 0), True, True, True, True),
            ((10, 1, 1), True, True, True, True),
            ((10, 1, 2), True, True, True, False),
            ((11, 0, 0), True, True, True, False),
            ((12, 1, 3), True, True, True, False),
        ]:
            with self.subTest(version=version):
                caps = Capabilities(version)
                self.assertEqual((caps.export, caps.customization, caps.qt6, bool(caps.warning)),
                                 (export, customization, qt6, warn))
        self.assertIn('changing skin colors', Capabilities((9, 0, 0)).warning)
        self.assertIn('10.1.2', Capabilities((10, 0, 0)).warning)

    def test_texture_set_names_before_and_after_painter_11(self):
        self.assertEqual(texture_set_name(types.SimpleNamespace(name=lambda: 'Skin')), 'Skin')
        self.assertEqual(texture_set_name(types.SimpleNamespace(name='Skin')), 'Skin')

    def test_binding_selection_never_imports_another_qt_major(self):
        for version, binding, action_module in [((9, 0, 0), 'PySide2', 'QtWidgets'),
                                                ((10, 0, 0), 'PySide2', 'QtWidgets'),
                                                ((10, 1, 0), 'PySide6', 'QtGui')]:
            fake = types.ModuleType(binding)
            for name in ('QtCore', 'QtGui', 'QtWidgets'):
                setattr(fake, name, types.SimpleNamespace(QAction=object()))
            spec = importlib.util.spec_from_file_location('kr7_batch._qt_test', ROOT / 'kr7_batch/qt.py')
            module = importlib.util.module_from_spec(spec)
            with patch('kr7_batch.compatibility.current', return_value=Capabilities(version)), \
                 patch.dict(sys.modules, {binding: fake}):
                spec.loader.exec_module(module)
            self.assertIs(module.QAction, getattr(fake, action_module).QAction)

    def test_runtime_and_development_code_parse_as_python_39(self):
        for folder in ('kr7_batch', 'scripts'):
            for path in (ROOT / folder).glob('*.py'):
                with self.subTest(path=path.name):
                    ast.parse(path.read_text(encoding='utf-8'), feature_version=(3, 9))
