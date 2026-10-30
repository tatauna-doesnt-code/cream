"""Direct name/color entry using the same validation as spreadsheet imports."""
from PySide6 import QtCore, QtGui, QtWidgets as W
from . import core


class SkinDialog(W.QDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent)
        self.setWindowTitle("Edit skin" if row else "Add skin")
        self.setMinimumWidth(430)
        layout = W.QVBoxLayout(self)
        layout.addWidget(W.QLabel("Enter a player name and up to three skin colors.\nLeave a color blank to keep the project original."))
        form = W.QFormLayout()
        layout.addLayout(form)
        self.name = W.QLineEdit(row['name'] if row else '')
        self.name.setAccessibleName("Player name")
        form.addRow("Player name", self.name)
        self.colors = []
        for i in range(3):
            container = W.QWidget()
            line = W.QHBoxLayout(container)
            line.setContentsMargins(0, 0, 0, 0)
            value = W.QLineEdit((row['colors'][i] or '') if row else '')
            value.setPlaceholderText("Project original · #RRGGBB")
            value.setAccessibleName(f"Color {i+1}")
            choose = W.QPushButton("Choose…")
            choose.setAutoDefault(False)
            choose.clicked.connect(lambda checked=False, field=value: self.pick(field))
            line.addWidget(value, 1)
            line.addWidget(choose)
            form.addRow(f"Color {i+1}", container)
            self.colors.append(value)
        self.message = W.QLabel()
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        buttons = W.QDialogButtonBox(W.QDialogButtonBox.Save | W.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_data)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.name.setFocus()

    def pick(self, field):
        color = W.QColorDialog.getColor(QtGui.QColor(field.text() or '#FFFFFF'), self, 'Choose skin color')
        if color.isValid():
            field.setText(color.name().upper())

    def accept_data(self):
        try:
            rows, warnings = core.rows_from_table([
                ['nome_player', 'cor_1', 'cor_2', 'cor_3'],
                [self.name.text(), *[field.text() for field in self.colors]]])
            self.row = rows[0]
            if warnings:
                self.name.setText(self.row['name'])
            self.accept()
        except ValueError as exc:
            self.message.setText(str(exc))
