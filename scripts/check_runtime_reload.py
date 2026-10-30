"""Exercise real Qt window/module swaps with Painter API stubs in an isolated copy."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
import types
import uuid

ROOT = Path(__file__).resolve().parents[1]
_dll_handle = os.add_dll_directory(str(Path(sys.executable).resolve().parents[2]))
from PySide6 import QtCore, QtWidgets as W

app = W.QApplication.instance() or W.QApplication([])
runpy.run_path(str(ROOT / 'tests/test_painter_adapter.py'), run_name='painter_stubs')
sp = sys.modules['substance_painter']
sp.ui = types.ModuleType('substance_painter.ui')
main = W.QMainWindow()
sp.ui.get_main_window = lambda: main
sp.ui.ApplicationMenu = types.SimpleNamespace(Window=1)
sp.ui.add_action = lambda menu, action: None
sp.ui.delete_ui_element = lambda item: item.deleteLater()
sys.modules['substance_painter.ui'] = sp.ui
sp.project.is_open = lambda: False

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    os.environ['LOCALAPPDATA'] = str(root / 'local')
    target = root / 'plugins/kr7_batch'
    shutil.copytree(ROOT / 'kr7_batch', target, ignore=shutil.ignore_patterns('__pycache__'))
    for name in list(sys.modules):
        if name == 'kr7_batch' or name.startswith('kr7_batch.'):
            del sys.modules[name]
    sys.path.insert(0, str(target.parent))
    import kr7_batch as plugin
    from kr7_batch import bootstrap
    plugin.start_plugin()
    old = plugin._window
    old.fields['output'].setText(str(root / 'skins'))
    old.fields['name_pattern'].setText('Community - {name}')
    old.styling_enabled.setChecked(True)
    old.maps.item(0, 0).setCheckState(QtCore.Qt.Checked)
    old.restore_reload_state({'rows': [{'line': 2, 'id': '1', 'name': 'Joseph', 'stem': 'Joseph',
                                      'colors': ['#AABBCC', None, None]}],
                             'loaded_sheet': ('input.csv', 10), 'checked': [False], 'selected': 0, 'log': 'Keep this log'})
    old.name_cells[0].editor.setText('Bompi')
    def stage(broken=False):
        stage = bootstrap.DATA / 'updates' / uuid.uuid4().hex
        shutil.copytree(target, stage / 'kr7_batch', ignore=shutil.ignore_patterns('__pycache__'))
        ui = stage / 'kr7_batch/ui.py'
        if broken:
            ui.write_text("raise RuntimeError('simulated UI import failure')\n", encoding='utf-8')
        else:
            path = stage / 'kr7_batch/version.py'
            from kr7_batch.version import VERSION
            path.write_text(path.read_text().replace('VERSION = "' + VERSION + '"', 'VERSION = "99.0.0"'), encoding='utf-8')
        manifest = {'schema': 1, 'product': 'CREAM', 'module': 'kr7_batch', 'version': '99.0.0',
                    'update': {'protocol': 1, 'restart': 'cream', 'min_reload_protocol': 1},
                    'files': {p.relative_to(stage).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in stage.rglob('*') if p.is_file()}}
        (stage / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        marker = bootstrap.pending_path(target)
        marker.write_text(json.dumps({'target': str(target.resolve()), 'stage': stage.name,
            'version': '99.0.0', 'process_id': os.getpid(),
            'manifest_sha256': bootstrap.sha256(stage / 'manifest.json')}), encoding='utf-8')
    stage()
    old.show_pending_update()
    assert old.update_button.text() == 'Apply and reopen CREAM' and old.update_button.isEnabled()
    for field, value in [('saved', {}), ('runner', object()), ('future', object()), ('update_future', object())]:
        setattr(old, field, value)
        plugin.request_reload()
        assert not plugin._reload_scheduled
        setattr(old, field, None)
    sp.project.is_open = lambda: True
    sp.project.is_busy = lambda: True
    assert 'busy' in old.reload_block_reason()
    sp.project.is_open = lambda: False
    old_module = sys.modules['kr7_batch.ui']
    plugin.request_reload()
    app.processEvents()
    current = plugin._window
    assert current is not old and sys.modules['kr7_batch.ui'] is not old_module
    assert '99.0.0' in current.windowTitle()
    assert current.fields['name_pattern'].text() == 'Community - {name}'
    assert current.styling_enabled.isChecked() and not current.name_style.isHidden()
    assert current.backers.item(0, 6).text() == 'Community - Bompi.zip'
    assert current.rows[0]['name'] == 'Bompi'
    assert current.name_cells[0].editor.font().bold() and current.name_cells[0].editor.font().italic()
    assert current.name_originals[0]['name'] == 'Joseph'
    assert current.backers.item(0, 0).checkState() == QtCore.Qt.Unchecked
    assert current.maps.item(0, 0).checkState() == QtCore.Qt.Checked
    assert current.log.toPlainText() == 'Keep this log'
    assert not bootstrap.pending_path(target).exists()
    stage(broken=True)
    plugin.request_reload()
    app.processEvents()
    restored = plugin._window
    assert restored is not current and '99.0.0' in restored.windowTitle()
    assert restored.rows[0]['name'] == 'Bompi'
    restored.name_cells[0].reset.click()
    assert restored.rows[0]['name'] == 'Joseph' and restored.rows[0]['stem'] == 'Joseph'
    assert 'simulated UI import failure' in restored.update_status.text()
    assert bootstrap.pending_info(target)['restart'] == 'painter'
    restored.show_pending_update()
    assert restored.update_button.text() == 'Restart Painter required' and not restored.update_button.isEnabled()
    action = plugin._action
    del plugin.request_reload  # Simulate the root module left behind by the 1.2 startup loader.
    restored.reload_callback = None
    restored.adopt_reload_support()
    assert plugin._window is restored and plugin._action is action
    assert restored.reload_callback == plugin.request_reload
    plugin.close_plugin()
    # Release module references before TemporaryDirectory removes the test copy.
    for name in list(sys.modules):
        if name == 'kr7_batch' or name.startswith('kr7_batch.'):
            del sys.modules[name]
print('Passed: deferred Qt reload, fresh modules, state preservation, active-job/preview/autosave guards, import-failure rollback, legacy loader upgrade.')
