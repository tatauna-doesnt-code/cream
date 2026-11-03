import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class TemplateDiscoveryTests(unittest.TestCase):
    def test_legacy_unknown_resource_types_do_not_hide_export_templates(self):
        sp = types.ModuleType('substance_painter')
        sp.__path__ = []
        sp.export = types.SimpleNamespace()
        resource = types.ModuleType('substance_painter.resource')
        sp.resource = resource
        resource.Type = types.SimpleNamespace(EXPORT='export')

        def unknown():
            raise ValueError("'vectorial' is not a valid Type")

        def preset(name):
            return types.SimpleNamespace(type=lambda: 'export', identifier=lambda:
                types.SimpleNamespace(name=name, url=lambda: 'resource://test/' + name))

        resource.search = lambda query: [types.SimpleNamespace(type=unknown), preset('TM2020'),
            types.SimpleNamespace(type=lambda: 'texture'), preset('Other'), preset('TM2020')]
        spec = importlib.util.spec_from_file_location('cream._discovery_test',
            Path(__file__).resolve().parents[1] / 'cream' / 'template_export.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'substance_painter': sp, 'substance_painter.resource': resource}):
            spec.loader.exec_module(module)
            self.assertEqual([p['name'] for p in module.templates()], ['Other', 'TM2020'])
            self.assertTrue(all(p['kind'] == 'legacy' for p in module.templates()))
            # Genuine library failures still surface instead of becoming an empty picker.
            resource.search = lambda query: (_ for _ in ()).throw(RuntimeError('Library unavailable'))
            with self.assertRaisesRegex(RuntimeError, 'Library unavailable'):
                module.templates()
