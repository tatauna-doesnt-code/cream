import importlib.util
from pathlib import Path
import sys
import tempfile
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
            # Real LTW report: search returns no exports, but both registered
            # starter_assets and user libraries contain readable .spexp files.
            with tempfile.TemporaryDirectory(prefix='cream library ') as directory:
                root = Path(directory)
                for context in ('starter_assets', 'your_assets'):
                    (root / context / 'export-presets').mkdir(parents=True)
                (root / 'starter_assets/export-presets/PBR Metallic Roughness.spexp').write_bytes(b'not parsed')
                (root / 'your_assets/export-presets/TM2020.spexp').write_bytes(b'not parsed')
                (root / 'your_assets/export-presets/TM.spexp').write_bytes(b'not parsed')
                (root / 'your_assets/export-presets/ignore.txt').write_bytes(b'not a template')
                resource.Shelves = types.SimpleNamespace(all=lambda: [
                    types.SimpleNamespace(name=lambda c=c: c, path=lambda c=c: str(root / c))
                    for c in ('starter_assets', 'your_assets')])
                resource.ResourceID = lambda context, name: types.SimpleNamespace(name=name,
                    url=lambda: 'resource://' + context + '/' + name)
                resource.search = lambda query: [types.SimpleNamespace(type=unknown)]
                found = module.templates()
                self.assertEqual([p['name'] for p in found], ['PBR Metallic Roughness', 'TM', 'TM2020'])
                self.assertEqual(found[2]['url'], 'resource://your_assets/TM2020')
                resource.search = lambda query: [types.SimpleNamespace(type=lambda: 'export', identifier=lambda:
                    types.SimpleNamespace(name='TM2020', url=lambda: 'resource://your_assets/TM2020?version=test.spexp'))]
                self.assertEqual(len(module.templates()), 3)
                self.assertEqual(module.templates()[2]['url'], 'resource://your_assets/TM2020?version=test.spexp')
            # Genuine library failures still surface instead of becoming an empty picker.
            resource.search = lambda query: (_ for _ in ()).throw(RuntimeError('Library unavailable'))
            with self.assertRaisesRegex(RuntimeError, 'Library unavailable'):
                module.templates()
