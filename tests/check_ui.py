import os
from pathlib import Path
import sys
import types
import tempfile
import threading
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = r'D:\Adobe\Adobe Substance 3D Painter\PlugIns\platforms'
dll = os.add_dll_directory(r'D:\Adobe\Adobe Substance 3D Painter')
from PySide6 import QtWidgets as W, QtGui
print('Qt imported', flush=True)
app = W.QApplication([])
QtGui.QFontDatabase.addApplicationFont(r'C:\Windows\Fonts\segoeui.ttf')
app.setFont(QtGui.QFont('Segoe UI', 9))
print('Application ready', flush=True)
main = W.QMainWindow()
sp = types.ModuleType('substance_painter')
sp.__path__ = []
sys.modules['substance_painter'] = sp
for name in ['ui', 'project', 'layerstack', 'textureset', 'colormanagement', 'source', 'export']:
    module = types.ModuleType('substance_painter.' + name)
    setattr(sp, name, module)
    sys.modules[module.__name__] = module
sp.ui.get_main_window = lambda: main
sys.path.insert(0, str(ROOT))
from kr7_batch import ui
print('Module ready', flush=True)
with tempfile.TemporaryDirectory() as temp:
    ui.DATA = Path(temp)
    window = ui.Window(auto_update=False)
    print('Window ready', flush=True)
    window.show()
    app.processEvents()
    window.grab().save(str(ROOT / 'dist/ui-backers.png'))
    window.tabs.setCurrentIndex(1)
    app.processEvents()
    window.grab().save(str(ROOT / 'dist/ui-textures.png'))
    assert window.maps.rowCount() == 28
    assert window.maps.cellWidget(21, 3).currentText() == '512 × 2048'
    # Exercise the real Qt controller + external converter + ZIP publisher, with only
    # Painter's native calls simulated. No user's project is opened or modified.
    from kr7_batch import core, painter
    base = Path(temp) / 'base.zip'
    with zipfile.ZipFile(base, 'w') as z:
        z.writestr('Details_R.dds', b'preserved base data')
    window.fields['base'].setText(str(base))
    window.fields['converter'].setText(str(ROOT / 'kr7_batch/bin/texconv.exe'))
    state = {'name': None, 'color': None, 'waits': 0}
    painter.project_path = lambda: str(Path(temp) / 'project.spp')
    painter.snapshot = lambda: {'project': painter.project_path(), 'targets': []}
    def ready():
        state['waits'] += 1
        return state['waits'] > 3
    painter.ready = ready
    sp.project.is_open = lambda: True
    def apply(saved, row=None):
        state['name'] = row['name'] if row else None
        state['color'] = row['colors'][0] if row else None
    painter.apply = apply
    def export_one(maps, selection, directory):
        im = QtGui.QImage(1024, 1024, QtGui.QImage.Format_RGBA8888)
        im.fill(QtGui.QColor(state['color']))
        path = Path(directory) / 'Skin_B.png'
        assert im.save(str(path))
        return path
    painter.export_one = export_one
    def run(cancel_second=False, styled=False, edited=False):
        output = Path(temp) / ('edited' if edited else 'styled' if styled else 'cancelled' if cancel_second else 'completed')
        output.mkdir()
        window.fields['output'].setText(str(output))
        window.fields['name_pattern'].setText('{primary}Community - {name}$z' if styled else 'Community - {name}')
        window.rows = [{'id':str(i), 'line':i+2, 'name':'Joseph', 'stem':'Joseph',
                        'colors':[color, None, None]} for i, color in enumerate(['#FF0000', '#00FF00'])]
        window.backers.setRowCount(2)
        for i in range(2):
            for col in range(8):
                window.backers.setItem(i,col,window.check_item(True) if col == 0 else W.QTableWidgetItem(''))
        if edited:
            window.name_originals = core.name_originals(window.rows)
            window.install_name_cells()
            window.name_cells[0].editor.setText('Bompi')
        window.saved = {'project':painter.project_path(), 'targets':[]}
        core.atomic_json(window.recovery_path(), window.saved)
        window.report = {'rows':[], 'status':'running'}
        window.report_path = output / 'report.json'
        window.cancel.clear()
        window.progress = ui.Progress(window, window.cancel)
        generator = window.run_batch([0,1],window.saved,[],[{'set':'Skin','map':'B','size':1024}])
        deadline = time.monotonic() + 30
        while True:
            if cancel_second and state['color'] == '#00FF00':
                window.cancel.set()
            try:
                next(generator)
            except StopIteration:
                break
            assert time.monotonic() < deadline, 'Controller did not finish'
            time.sleep(0.005)
        assert state['name'] is None
        assert window.saved is None
        assert not window.recovery_path().exists()
        first = 'Community - Bompi.zip' if edited else '$F00Community - Joseph$z.zip' if styled else 'Community - Joseph.zip'
        second = 'Community - Joseph.zip' if edited else '$0F0Community - Joseph$z.zip' if styled else 'Community - Joseph 2.zip'
        assert (output/first).is_file()
        if cancel_second:
            assert not (output/second).exists()
            assert window.report['status'] == 'cancelled'
        else:
            assert (output/second).is_file()
            assert window.report['status'] == 'completed'
            with zipfile.ZipFile(output/first) as a, zipfile.ZipFile(output/second) as b:
                assert a.read('Skin_B.dds') != b.read('Skin_B.dds')
                assert a.read('Details_R.dds') == b'preserved base data'
        assert not list(output.glob('*.partial'))
        window.progress.deleteLater()
        window.progress = None
    run()
    run(cancel_second=True)
    run(styled=True)
    run(edited=True)
    window.styling_enabled.setChecked(True)
    window.backers.selectRow(0)
    window.fields['name_pattern'].setText('$o{primary}Community - {name}$z')
    window.tabs.setCurrentIndex(0)
    app.processEvents()
    app.processEvents()  # Allow the expanded helper's layout request to settle.
    assert window.name_style.geometry().bottom() < window.tabs.geometry().top()
    window.grab().save(str(ROOT / 'dist/ui-name-styling.png'))
    print('Controller integration: busy wait, two same-name different-color ZIPs, cancellation on second backer, original restore verified.', flush=True)
    window.pool.shutdown()
    window.hide()
print('Qt UI instantiated and rendered with Painter Python 3.13 / PySide6; 28 map controls verified.')
