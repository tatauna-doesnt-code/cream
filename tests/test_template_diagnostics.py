from enum import Enum
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


class TemplateDiagnosticsTests(unittest.TestCase):
    def test_report_captures_unknown_types_export_usages_and_library_paths(self):
        class Kind(Enum):
            PRESET = 'preset'
            EXPORT = 'export'
        class Usage(Enum):
            EXPORT = 'export'

        def unknown():
            raise ValueError("'vectorial' is not a valid Type")

        sp = types.ModuleType('substance_painter')
        sp.__path__ = []
        sp.export = types.SimpleNamespace()
        resource = types.ModuleType('substance_painter.resource')
        sp.resource = resource
        resource.Type, resource.Usage = Kind, Usage
        resource.search = lambda query: [
            types.SimpleNamespace(type=unknown, usages=lambda: [],
                identifier=lambda: types.SimpleNamespace(url=lambda: 'resource://test/vector')),
            types.SimpleNamespace(type=lambda: Kind.PRESET, usages=lambda: [Usage.EXPORT],
                identifier=lambda: types.SimpleNamespace(url=lambda: 'resource://test/TM2020'))]
        spec = importlib.util.spec_from_file_location('cream._diagnostics_test',
            Path(__file__).resolve().parents[1] / 'cream' / 'diagnostics.py')
        module = importlib.util.module_from_spec(spec)
        with tempfile.TemporaryDirectory() as folder, patch.dict(sys.modules,
                {'substance_painter': sp, 'substance_painter.resource': resource}):
            spec.loader.exec_module(module)
            root = Path(folder)
            (root / 'export-presets').mkdir()
            (root / 'export-presets' / 'TM2020.spexp').write_bytes(b'not read')
            (root / 'private.txt').write_text('must not appear in report')
            shelf = types.SimpleNamespace(name=lambda: 'user', path=lambda: folder, is_crawling=lambda: False)
            resource.Shelves = types.SimpleNamespace(all=lambda: [shelf])
            with patch.object(module.compatibility, 'current', return_value=types.SimpleNamespace(version_text='9.1.2')), \
                 patch.object(module.template_export, 'templates', return_value=[]):
                report = module.collect(folder)
            self.assertEqual(report['painter_version'], '9.1.2')
            self.assertEqual(report['cream_discovery'], [])
            scan = report['resource_scan']
            self.assertEqual(scan['total'], 2)
            self.assertEqual(scan['usage_counts'], {'EXPORT': 1})
            self.assertEqual(len(scan['unknown_type_samples_first_30']), 1)
            self.assertEqual(scan['export_candidates_first_300'][0]['type'], 'PRESET')
            serialized = json.dumps(report)
            self.assertIn('TM2020.spexp', serialized)
            self.assertNotIn('must not appear', serialized)
            self.assertNotIn('private.txt', serialized)
            # An unavailable mapped drive is recorded rather than aborting collection.
            self.assertFalse(module.folder_report(root / 'missing')['exists'])
            resource.search = lambda query: (_ for _ in ()).throw(RuntimeError('Library unavailable'))
            with patch.object(module.compatibility, 'current', return_value=types.SimpleNamespace(version_text='9.1.2')), \
                 patch.object(module.template_export, 'templates', side_effect=ValueError('discovery failed')):
                failed = module.collect()
            self.assertIn('Library unavailable', failed['resource_scan']['error'])
            self.assertIn('discovery failed', failed['cream_discovery']['error'])
