"""Real Qt5/Qt6 + texconv + ZIP integration; Painter's native calls are simulated.

Run with Python 3.9/PySide2 for 9.0.0 and 10.0.0, or Painter SDK/PySide6
for 10.1.1, 10.1.2, 11.0.0 and 12.1.3. Never touches a user's project.
"""
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import types
from unittest.mock import patch
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
version = tuple(map(int, (sys.argv[1] if len(sys.argv) > 1 else '12.1.3').split('.')))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
if version >= (10, 1, 0):
    dll = os.add_dll_directory(str(Path(sys.executable).resolve().parents[2]))
    from PySide6 import QtWidgets as W
else:
    from PySide2 import QtWidgets as W

sp = types.ModuleType('substance_painter')
sp.__path__ = []
sys.modules['substance_painter'] = sp
modules = ['application', 'ui', 'project', 'textureset', 'export', 'resource']
if version >= (10, 0, 0):
    modules += ['source', 'colormanagement', 'layerstack']
for name in modules:
    module = types.ModuleType('substance_painter.' + name)
    setattr(sp, name, module)
    sys.modules[module.__name__] = module
sp.application.version_info = lambda: version
sp.ui.get_main_window = lambda: None
sp.ui.ApplicationMenu = types.SimpleNamespace(Window=1)
sp.ui.add_action = lambda *args: None
sp.ui.delete_ui_element = lambda obj: obj.deleteLater()
sp.project.is_open = lambda: True
sp.project.is_busy = lambda: False
sp.project.is_in_edition_state = lambda: True
stack = types.SimpleNamespace(name=lambda: '')
sp.textureset.all_texture_sets = lambda: [types.SimpleNamespace(
    name='Skin' if version >= (11, 0, 0) else lambda: 'Skin', all_stacks=lambda: [stack])]
preset_id = types.SimpleNamespace(name='TM2020', url=lambda: 'resource://test/TM2020')
sp.resource.Type = types.SimpleNamespace(EXPORT=1)
sp.resource.search = lambda query: [types.SimpleNamespace(identifier=lambda: preset_id, type=lambda: 1)]
if version >= (10, 0, 0):
    sp.layerstack.get_root_layer_nodes = lambda s: []
    sp.export.list_resource_export_presets = lambda: [types.SimpleNamespace(
        resource_id=preset_id, list_output_maps=lambda: [{'fileName': '$textureSet_B', 'channels': []}])]


def paths(config):
    name = config['exportList'][0]['rootPath']
    output = (config['exportPresets'][0]['maps'][0]['fileName'] if 'exportPresets' in config else
              config['exportList'][0]['filter']['outputMaps'][0].replace('$textureSet', name))
    return {(name, ''): [str(Path(config['exportPath']) / (output + '.png'))]}


def png(path, width, height):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    data = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>2I5B', width, height, 8, 2, 0, 0, 0))
    data += chunk(b'IDAT', zlib.compress((b'\0' + b'\xa0\xb0\xc0' * width) * height))
    Path(path).write_bytes(data + chunk(b'IEND', b''))


def export(config):
    output = paths(config)
    size = config['exportParameters'][0]['parameters']['sizeLog2']
    png(next(iter(output.values()))[0], 2 ** size[0], 2 ** size[1])
    return types.SimpleNamespace(status='success', textures=output)


sp.export.ExportStatus = types.SimpleNamespace(Success='success')
sp.export.list_project_textures = paths
sp.export.export_project_textures = export
app = W.QApplication.instance() or W.QApplication([])
from cream.qt import QtGui
app.setStyle('Fusion')
palette = QtGui.QPalette()
for role, value in [('Window', '#303030'), ('WindowText', '#eeeeee'), ('Base', '#222426'),
                    ('AlternateBase', '#2b2d30'), ('Text', '#eeeeee'), ('Button', '#393939'),
                    ('ButtonText', '#eeeeee'), ('Highlight', '#365568'), ('HighlightedText', '#ffffff')]:
    palette.setColor(getattr(QtGui.QPalette, role), QtGui.QColor(value))
app.setPalette(palette)
from cream import ui, painter, bootstrap, compatibility
from cream.manual_entry import SkinDialog
import cream as plugin

with tempfile.TemporaryDirectory() as folder, patch.object(ui, 'DATA', Path(folder)), \
     patch.object(bootstrap, 'DATA', Path(folder)), \
     patch.object(W.QMessageBox, 'warning') as warning:
    sp.project.file_path = lambda: str(Path(folder) / 'test.spp')
    # Enabling registers the action without creating the window or starting updates.
    plugin.start_plugin()
    assert plugin._window is None
    plugin._action.trigger()
    window = plugin._window
    window.stop_updater()
    app.processEvents()
    window.show_compatibility_warning()
    assert warning.call_count == (1 if version < (10, 1, 2) else 0)
    assert window.customize_project.isEnabled() == (version >= (10, 0, 0))
    window.customize_project.setChecked(False)
    assert not window.preview_button.isEnabled()
    if version < (10, 0, 0):
        assert not window.recover_button.isEnabled()
    assert window.compatibility_notice.isHidden() == (version >= (10, 1, 2))
    dialog = SkinDialog(window, customize=False)
    assert dialog.colors[0].isEnabled() and not dialog.colors[2].isEnabled()
    base = Path(folder) / 'base.zip'
    with zipfile.ZipFile(base, 'w') as archive:
        archive.writestr('Details_R.dds', b'unchanged base file')
    window.fields['base'].setText(str(base))
    window.fields['output'].setText(folder)
    # Empty Batch is the primary workflow, even with customization checked on modern hosts.
    assert not window.rows and window.tabs.currentWidget() is window.textures_page
    window.customize_project.setChecked(version >= (10, 0, 0))
    section = window.texture_sets.groups['Skin']
    section.table.item(0, 0).setCheckState(ui.QtCore.Qt.Checked)
    section.sizes[0].setCurrentIndex(section.sizes[0].findData(1024))
    window.fields['name_pattern'].setText('$o$F80{name}$z')
    assert window.name_preview.text() == '$o$F80test$z.zip'
    assert window.export_button.isEnabled() and window.export_button.text() == 'Export current skin'
    assert window.validate_button.isEnabled()
    with patch.object(painter, 'nodes', side_effect=AssertionError('As-is exports must not scan layers')), \
         patch.object(painter, 'apply', side_effect=AssertionError('As-is exports must not apply or restore layers')):
        window.check()
        window.start()
        deadline = time.monotonic() + 30
        while window.runner is not None and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(.01)
        assert window.runner is None and window.report['status'] == 'completed', window.report
        assert window.report['mode'] == 'current_project'
        assert not window.rows and window.backers.rowCount() == 0
        with zipfile.ZipFile(window.report['rows'][0]['output']) as archive:
            assert archive.read('Details_R.dds') == b'unchanged base file'
            assert archive.read('Skin_B.dds')[84:88] == b'DXT1'
        assert window.name_preview.text() == '$o$F80test$z 2.zip'
        assert not list(Path(folder).glob('recover-*.json'))
        assert not list(Path(folder).glob('cream-*'))
        # Cancel the single export after its PNG exists: clean all intermediates, publish nothing.
        window.start()
        window.timer.stop()
        window.tick()
        window.tick()
        window.cancel.set()
        while window.runner is not None and time.monotonic() < deadline:
            window.tick()
            app.processEvents()
            time.sleep(.01)
        assert window.runner is None and window.report['status'] == 'cancelled'
        assert len(list(Path(folder).glob('$o$F80*.zip'))) == 1
        assert not list(Path(folder).glob('cream-*'))
    window.grab().save(str(ROOT / 'dist' / ('single-export-' + '.'.join(map(str, version)) + '.png')))
    window.customize_project.setChecked(False)
    window.restore_reload_state({'rows': [{'id': '1', 'line': 1, 'name': 'Tester', 'stem': 'Tester',
                                          'colors': ['#AABBCC', None, None]}],
                                 'loaded_sheet': None, 'checked': [True], 'selected': 0, 'log': '',
                                 'customize': False})
    original = window.capture_reload_state()
    bulk = dict(original, rows=[dict(original['rows'][0], id=str(i), line=i + 1,
                                    name='Player' + str(i), stem='Player' + str(i)) for i in range(200)],
                name_originals=None, checked=[False] * 200)
    window.restore_reload_state(bulk)
    if version >= (10, 0, 0):
        window.customize_project.setChecked(True)
        window.customize_project.setChecked(False)
    assert all(not window.backers.item(i, 5).flags() & ui.QtCore.Qt.ItemIsEnabled for i in range(200))
    window.restore_reload_state(original)
    section = window.texture_sets.groups['Skin']
    section.table.item(0, 0).setCheckState(ui.QtCore.Qt.Checked)
    section.sizes[0].setCurrentIndex(section.sizes[0].findData(1024))
    window.styling_enabled.setChecked(True)
    window.fields['name_pattern'].setText('$o{primary}{name}$z')
    assert window.name_preview.text() == '$o$ABCTester$z.zip'
    assert window.export_button.isEnabled() and not window.preview_button.isEnabled()
    with patch.object(painter, 'nodes', side_effect=AssertionError('Export-only mode must not touch layers')):
        window.check()
        assert not list(Path(folder).glob('recover-*.json'))
        window.start()
        deadline = time.monotonic() + 30
        while window.runner is not None and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(.01)
        assert window.runner is None
        assert window.report['status'] == 'completed', window.report
        output = Path(window.report['rows'][0]['output'])
        with zipfile.ZipFile(output) as archive:
            assert archive.read('Details_R.dds') == b'unchanged base file'
            assert archive.read('Skin_B.dds')[84:88] == b'DXT1'
        assert not list(Path(folder).glob('recover-*.json'))
        assert not list(Path(folder).glob('cream-*'))
        assert window.saved is None
        # Cancellation still publishes no partial ZIP and needs no layer recovery.
        window.check_rows(True)
        window.start()
        window.cancel.set()
        while window.runner is not None and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(.01)
        assert window.runner is None and window.report['status'] == 'cancelled'
        assert len(list(Path(folder).glob('$o$ABC*.zip'))) == 1
    window.check_rows(False)
    assert not window.export_button.isEnabled()  # A nonempty, unchecked batch never exports as-is.
    with patch.object(W.QMessageBox, 'question', return_value=W.QMessageBox.No):
        window.clear_batch()
        assert window.rows
    with patch.object(W.QMessageBox, 'question', return_value=W.QMessageBox.Yes):
        window.clear_batch()
        assert not window.rows and window.export_button.text() == 'Export current skin'
    assert window.tabs.tabText(1) == '2  Skin ZIPfile name'
    window.grab().save(str(ROOT / 'dist' / ('compatibility-' + '.'.join(map(str, version)) + '.png')))
    plugin.close_plugin()
print('Passed: Painter', version, 'startup, warnings, disabled controls, styling, export, real DDS/ZIP and cancellation.')
