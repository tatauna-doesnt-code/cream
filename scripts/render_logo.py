"""Render the supplied Bornie wordmark once; no font file ships in the plugin."""
import os
from pathlib import Path
import sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', r'D:\Adobe\Adobe Substance 3D Painter\PlugIns\platforms')
handle = os.add_dll_directory(str(Path(sys.executable).resolve().parents[2]))
from PySide6 import QtCore, QtGui, QtWidgets

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
identifier = QtGui.QFontDatabase.addApplicationFontFromData(QtCore.QByteArray(Path(sys.argv[1]).read_bytes()))
families = QtGui.QFontDatabase.applicationFontFamilies(identifier)
assert families, 'Could not load the supplied font'
font = QtGui.QFont(families[0])
font.setPointSizeF(28)
path = QtGui.QPainterPath()
path.addText(0, 0, font, 'Cream')
bounds = path.boundingRect().adjusted(-2, -2, 2, 2)
scale = 3
picture = QtGui.QImage(int(bounds.width() * scale + 1), int(bounds.height() * scale + 1), QtGui.QImage.Format_ARGB32_Premultiplied)
picture.fill(QtCore.Qt.transparent)
painter = QtGui.QPainter(picture)
painter.setRenderHint(QtGui.QPainter.Antialiasing)
painter.scale(scale, scale)
painter.translate(-bounds.left(), -bounds.top())
painter.fillPath(path, QtGui.QColor('#eeeeee'))
painter.end()
destination = Path(__file__).resolve().parents[1] / 'kr7_batch/assets/cream-logo.png'
destination.parent.mkdir(parents=True, exist_ok=True)
assert picture.save(str(destination))
print(f'Rendered Cream in {families[0]} at 28 pt (3x).')
