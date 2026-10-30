"""Cursor-following explanations, including controls Qt disables during a preview."""
from PySide6 import QtCore, QtGui, QtWidgets as W


class PreviewHelp(QtCore.QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.targets = {}
        self.tip = W.QLabel(window, QtCore.Qt.ToolTip)
        self.tip.setWordWrap(True)
        self.tip.setMaximumWidth(340)
        self.tip.setStyleSheet("background: #202225; color: #eeeeee; border: 1px solid #666; padding: 10px;")
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(80)
        self.timer.timeout.connect(self.follow)

    def update(self, targets, active):
        self.targets = targets
        if active:
            self.timer.start()
        else:
            self.timer.stop()
            self.tip.hide()

    def follow(self):
        position = QtGui.QCursor.pos()
        target = W.QApplication.widgetAt(position)
        while target is not None and target not in self.targets:
            target = target.parentWidget()
        if target is None or not self.window.isVisible():
            self.tip.hide()
            return
        self.tip.setText(self.targets[target] + " is locked while a preview is applied. Click Restore original beside Preview to use it.")
        self.tip.adjustSize()
        screen = W.QApplication.screenAt(position)
        point = position + QtCore.QPoint(16, 22)
        if screen:
            bounds = screen.availableGeometry()
            point.setX(min(point.x(), bounds.right() - self.tip.width()))
            point.setY(min(point.y(), bounds.bottom() - self.tip.height()))
        self.tip.move(point)
        self.tip.show()
