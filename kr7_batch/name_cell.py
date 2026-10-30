"""Inline per-backer player-name editor and icon-only reset control."""
from .qt import QtCore, QtGui, QtWidgets as W


class PlayerNameDelegate(W.QStyledItemDelegate):
    def paint(self, painter, option, index):
        option = W.QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        option.text = ""  # The inline editor paints the name; avoid drawing it twice.
        style = option.widget.style() if option.widget is not None else W.QApplication.style()
        style.drawControl(W.QStyle.CE_ItemViewItem, option, painter, option.widget)


class PlayerNameCell(W.QWidget):
    changed = QtCore.Signal(str)
    reset_requested = QtCore.Signal()
    focused = QtCore.Signal()

    def __init__(self, name, original, parent=None):
        super().__init__(parent)
        self.original = original
        self.allowed = True
        self.selected = False
        self.invalid = ""
        layout = W.QHBoxLayout(self)
        layout.setContentsMargins(5, 4, 5, 4)
        layout.setSpacing(4)
        self.editor = W.QLineEdit(name)
        self.editor.setAccessibleName("Player name")
        self.editor.setMinimumWidth(120)
        self.editor.installEventFilter(self)
        self.editor.setFixedHeight(26)
        self.editor.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        self.reset = W.QToolButton()
        self.reset.setIcon(self.style().standardIcon(W.QStyle.SP_BrowserReload))
        self.reset.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.reset.setAccessibleName("Reset player name")
        self.reset.setToolTip("Reset to spreadsheet value: " + original)
        self.reset.setAutoRaise(True)
        self.reset.setFixedSize(26, 26)
        self.reset.clicked.connect(self.reset_requested)
        layout.addWidget(self.reset, 0, QtCore.Qt.AlignVCenter)
        layout.addWidget(self.editor, 1, QtCore.Qt.AlignVCenter)
        self.editor.textChanged.connect(self.changed)
        self.refresh_appearance()

    def eventFilter(self, watched, event):
        if watched is self.editor and event.type() == QtCore.QEvent.FocusIn:
            self.focused.emit()
        return super().eventFilter(watched, event)

    def set_text(self, text):
        blocker = QtCore.QSignalBlocker(self.editor)
        self.editor.setText(text)
        del blocker
        self.refresh_appearance()

    def set_allowed(self, allowed):
        self.allowed = allowed
        self.editor.setReadOnly(not allowed)
        self.refresh_appearance()

    def set_selected(self, selected):
        self.selected = selected
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Text, self.palette().color(
            QtGui.QPalette.HighlightedText if selected else QtGui.QPalette.Text))
        self.editor.setPalette(palette)

    def refresh_appearance(self):
        changed = self.editor.text() != self.original
        font = self.editor.font()
        font.setBold(changed)
        font.setItalic(changed)
        self.editor.setFont(font)
        self.reset.setEnabled(self.allowed and changed)
        self.editor.setToolTip(self.invalid or (
            "Edit the player name for this session. Up to 20 characters."
            if self.allowed else "Finish the batch and restore the preview before editing names."))
        self.editor.setStyleSheet("QLineEdit { min-height: 0; background: #202225; color: #eee; border: " +
                                 ("1px solid #d66" if self.invalid else "1px solid #62666a") +
                                 "; border-radius: 3px; padding: 0 5px; } QLineEdit:focus { border-color: #7db5d8; }")
