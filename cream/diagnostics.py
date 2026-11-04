"""Read-only, explicitly requested template discovery reports. No uploads."""
from collections import Counter
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path
import json
import sys

from . import compatibility, template_export
from .version import VERSION

BUILD = 'local-test-8'


def attempt(callback):
    try:
        return callback()
    except Exception as exc:
        return {'error': type(exc).__name__ + ': ' + str(exc)}


def enum_name(value):
    return str(getattr(value, 'name', value))


def folder_report(location):
    """Inspect only this directory and standard preset subdirectories, never recurse."""
    path = Path(location)
    result = {'path': str(path), 'exists': path.exists(), 'is_directory': path.is_dir()}
    if not path.is_dir():
        return result
    folders = []
    for relative in ('', 'export-presets', 'assets/export-presets', 'shelf/export-presets'):
        directory = path / relative
        if not directory.is_dir():
            continue
        def listing():
            # Bound enumeration, including on a mapped drive with many unrelated files.
            names = [p.name for p in islice(directory.iterdir(), 1001)]
            return {'entries_scanned': min(len(names), 1000), 'truncated': len(names) > 1000,
                    'preset_filenames': sorted(n for n in names[:1000] if n.lower().endswith('.spexp'))}
        folders.append({'path': str(directory), 'listing': attempt(listing)})
    result['folders'] = folders
    return result


def collect(extra_folder='', window=None):
    import substance_painter as sp
    import substance_painter.resource
    resource = sp.resource
    report = {'schema': 1, 'build': BUILD, 'cream_version': VERSION,
              'created_utc': datetime.now(timezone.utc).isoformat(),
              'painter_version': attempt(lambda: compatibility.current().version_text),
              'python_version': sys.version, 'python_executable': sys.executable,
              'notes': 'Read-only. Includes library paths and resource identifiers, not project contents or credentials.',
              'available_api': {name: hasattr(sp.export, name) for name in (
                  'list_resource_export_presets', 'list_predefined_export_presets')},
              'resource_types': attempt(lambda: [enum_name(v) for v in resource.Type]),
              'resource_usages': attempt(lambda: [enum_name(v) for v in resource.Usage]),
              'cream_discovery': attempt(template_export.templates)}
    report['project_state'] = {name: attempt(lambda n=name: getattr(sp.project, n)())
        for name in ('is_open', 'is_in_edition_state', 'is_busy')}
    if window is not None:
        textures = window.texture_sets
        report['template_ui'] = {
            'reload_status': textures.reload_status, 'problem': textures.problem,
            'catalog_loaded': textures.catalog_loaded, 'catalog_count': len(textures.catalog),
            'dropdown_count': textures.template.count(), 'selected_url': textures.template.currentData(),
            'texture_sets_loaded': list(textures.groups), 'loading': textures._loading,
            'export_active': window.runner is not None, 'preview_active': window.saved is not None}

    def libraries():
        entries = []
        for shelf in resource.Shelves.all():
            path = attempt(shelf.path)
            entries.append({'name': attempt(shelf.name), 'path': path,
                'is_crawling': attempt(shelf.is_crawling),
                'folder': attempt(lambda p=path: folder_report(p)) if isinstance(path, str) else None})
        return entries
    report['libraries'] = attempt(libraries)

    def resources():
        found = resource.search('')
        types, usages, errors = Counter(), Counter(), Counter()
        candidates, unknown = [], []
        for item in found:
            kind = attempt(lambda: enum_name(item.type()))
            uses = attempt(lambda: [enum_name(u) for u in item.usages()])
            identifier = attempt(lambda: item.identifier().url())
            type_key = kind if isinstance(kind, str) else kind['error']
            types[type_key] += 1
            if isinstance(uses, list):
                usages.update(uses)
            else:
                errors[uses['error']] += 1
            entry = {'identifier': identifier, 'type': kind, 'usages': uses}
            text = str(identifier).lower()
            if ('export' in type_key.lower() or
                    (isinstance(uses, list) and any('export' in u.lower() for u in uses)) or
                    'tm2020' in text or 'ltw2023' in text):
                if len(candidates) < 300:
                    candidates.append(entry)
            if isinstance(kind, dict) and len(unknown) < 30:
                unknown.append(entry)
        return {'total': len(found), 'type_counts': dict(types), 'usage_counts': dict(usages),
                'usage_errors': dict(errors), 'export_candidates_first_300': candidates,
                'unknown_type_samples_first_30': unknown}
    report['resource_scan'] = attempt(resources)
    if extra_folder.strip():
        report['extra_template_folder'] = attempt(lambda: folder_report(extra_folder.strip()))
    return report


def add_controls(window, layout):
    from .qt import QtWidgets as W
    heading = W.QLabel('Template diagnostics · local test build')
    heading.setStyleSheet('font-size: 17px; font-weight: 600;')
    layout.addWidget(heading)
    explanation = W.QLabel('Save a report if export templates are missing. It includes library paths and resource names. '
                           'Nothing is uploaded or changed in Painter. You can review the JSON before sharing it.')
    explanation.setWordWrap(True)
    layout.addWidget(explanation)
    row = W.QHBoxLayout()
    window.diagnostics_folder = W.QLineEdit()
    window.diagnostics_folder.setPlaceholderText('Optional: paste the folder containing your export template')
    window.diagnostics_folder.setFixedHeight(32)
    from .qt import QtCore
    row.addWidget(window.diagnostics_folder, 1, QtCore.Qt.AlignVCenter)
    window.diagnostics_button = W.QPushButton('Save template diagnostic report…')
    window.diagnostics_button.setFixedHeight(32)
    window.diagnostics_button.setAutoDefault(False)
    row.addWidget(window.diagnostics_button, 0, QtCore.Qt.AlignVCenter)
    layout.addLayout(row)

    def save():
        filename, _ = W.QFileDialog.getSaveFileName(window, 'Save CREAM template diagnostic report',
            'CREAM-template-diagnostics.json', 'JSON report (*.json)')
        if not filename:
            return
        try:
            report = collect(window.diagnostics_folder.text(), window)
            Path(filename).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        except Exception as exc:
            W.QMessageBox.warning(window, 'CREAM diagnostics', 'Could not save the report: ' + str(exc))
            return
        W.QMessageBox.information(window, 'CREAM diagnostics',
            'Report saved. Send this JSON file back for investigation.\n\n' + filename)
    window.diagnostics_button.clicked.connect(save)
