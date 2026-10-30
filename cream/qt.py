"""Use the Qt binding bundled with Painter; never install a second binding."""
from .compatibility import current

if current().qt6:
    from PySide6 import QtCore, QtGui, QtWidgets
    QAction = QtGui.QAction
else:
    from PySide2 import QtCore, QtGui, QtWidgets
    QAction = QtWidgets.QAction


def exec_dialog(dialog):
    return dialog.exec() if hasattr(dialog, 'exec') else dialog.exec_()
