"""Small Righteous monogram, rendered sharply for standard and high-DPI displays."""
from pathlib import Path
from .qt import QtCore, QtGui, QtWidgets


def make_icon():
    app = QtWidgets.QApplication.instance()
    font_id = app.property('creamRighteousFontId')
    if font_id is None:
        data = (Path(__file__).parent / 'fonts/righteous/Righteous-Regular.ttf').read_bytes()
        font_id = QtGui.QFontDatabase.addApplicationFontFromData(QtCore.QByteArray(data))
        app.setProperty('creamRighteousFontId', font_id)
    families = QtGui.QFontDatabase.applicationFontFamilies(font_id)
    font = QtGui.QFont(families[0] if families else 'Arial')
    font.setPixelSize(24)
    glyph = QtGui.QPainterPath()
    glyph.addText(0, 0, font, 'c')
    bounds = glyph.boundingRect()
    icon = QtGui.QIcon()
    for ratio in (1, 2, 3):
        pixmap = QtGui.QPixmap(20 * ratio, 20 * ratio)
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.translate(10, 10)
        scale = min(16 / bounds.width(), 16 / bounds.height())
        painter.scale(scale, scale)
        painter.translate(-bounds.center())
        painter.fillPath(glyph, QtGui.QColor('#eeeeee'))
        painter.end()
        icon.addPixmap(pixmap)
    return icon
