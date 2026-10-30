"""Exercise actual accordion controls without Painter imports."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_dll = os.add_dll_directory(str(Path(sys.executable).resolve().parents[2]))
from PySide6 import QtCore, QtGui, QtWidgets as W
import types
sp = types.ModuleType('substance_painter')
sp.__path__ = []
sp.application = types.ModuleType('substance_painter.application')
sp.application.version_info = lambda: (12, 1, 3)
sys.modules['substance_painter'] = sp
sys.modules['substance_painter.application'] = sp.application
from cream.texture_sets import TextureSets, TEXTURE_SETS

app = W.QApplication.instance() or W.QApplication([])
QtGui.QFontDatabase.addApplicationFont(r'C:\Windows\Fonts\segoeui.ttf')
app.setFont(QtGui.QFont('Segoe UI', 9))
control = TextureSets()
assert list(control.groups) == list(TEXTURE_SETS)
assert not control.selections()
assert len(control.settings()) == 28
assert all(section.body.isHidden() and not section.expand.isChecked() for section in control.groups.values())
skin = control.groups['Skin']
assert skin.table.columnCount() == 3
assert [skin.table.horizontalHeaderItem(i).text() for i in range(3)] == ['Export', 'Texture', 'Resolution']
skin.export.click()
assert len(skin.selections()) == 7 and skin.export.checkState() == QtCore.Qt.Checked
assert skin.body.isHidden()  # Selecting a set does not force it open.
skin.table.item(0, 0).setCheckState(QtCore.Qt.Unchecked)
assert len(skin.selections()) == 6 and skin.export.checkState() == QtCore.Qt.PartiallyChecked
skin.export.click()
assert len(skin.selections()) == 7
skin.export.click()
assert not skin.selections()
skin.table.item(1, 0).setCheckState(QtCore.Qt.Checked)
assert control.selections() == [{'set': 'Skin', 'map': 'R', 'size': 2048}]
skin.resolution.setCurrentIndex(skin.resolution.findData(4096))
assert all(combo.currentData() == 4096 for combo in skin.sizes)
assert control.selections() == [{'set': 'Skin', 'map': 'R', 'size': 4096}]
skin.sizes[1].setCurrentIndex(skin.sizes[1].findData(1024))
assert skin.resolution.currentText() == 'Mixed' and skin.resolution.currentData() is None
assert skin.sizes[0].currentData() == 4096
skin.resolution.setCurrentIndex(skin.resolution.findData(2048))
assert all(combo.currentData() == 2048 for combo in skin.sizes)
skin.expand.click()
assert not skin.body.isHidden()
skin.expand.click()
assert skin.body.isHidden()
wheels = control.groups['Wheels']
assert wheels.resolution.currentText() == '512 × 2048'
wheels.resolution.setCurrentIndex(wheels.resolution.findData(4096))
assert all(combo.currentText() == '1024 × 4096' for combo in wheels.sizes)
wheels.sizes[0].setCurrentIndex(wheels.sizes[0].findData(1024))
assert wheels.sizes[0].currentText() == '256 × 1024' and wheels.resolution.currentText() == 'Mixed'
wheels.export.click()
saved = control.settings()
restored = TextureSets()
restored.restore_settings(saved)
assert restored.settings() == saved and restored.selections() == control.selections()
assert all(section.body.isHidden() for section in restored.groups.values())
# Legacy flat arrays migrate without changing row order, flags or individual resolutions.
legacy = [{'checked': i % 2 == 0, 'size': (1024, 2048, 4096)[i % 3]} for i in range(28)]
restored.restore_settings(legacy)
assert restored.settings() == legacy
control.resize(800, 620)
control.show()
app.processEvents()
control.grab().save(str(ROOT / 'dist/texture-accordions-closed.png'))
skin.expand.click()
wheels.expand.click()
control.resize(800, 800)
app.processEvents()
app.processEvents()
control.grab().save(str(ROOT / 'dist/texture-accordions-open.png'))
control.hide()
print('Passed: collapsed defaults, tri-state selection, all/individual resolutions, Mixed, Wheels aspect ratio, settings and legacy migration.')
