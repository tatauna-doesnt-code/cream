"""Column selection UI; independent of the Painter API."""
from PySide6 import QtCore, QtWidgets as W

from . import core


FIELDS = [
    ("nome_player", "Player name *", "Select a column"),
    ("cor_1", "Color 1 — PLAYER_COLOR1", "Project original"),
    ("cor_2", "Color 2 — PLAYER_COLOR2", "Project original"),
    ("cor_3", "Color 3 — PLAYER_COLOR3", "Project original"),
    ("id", "Row ID", "Row number"),
    ("nome_arquivo", "ZIP name", "Use player name"),
    ("ativo", "Export / active", "All rows"),
]


def column_letter(index):
    label = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        label = chr(65 + remainder) + label
    return label


class ColumnDialog(W.QDialog):
    def __init__(self, table, saved=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CREAM — Spreadsheet columns")
        self.resize(850, 650)
        self.table = table
        self.mapping = None
        headers = table[0]
        layout = W.QVBoxLayout(self)
        description = W.QLabel(
            "Choose a column for each field. The first spreadsheet row contains the headers.\n"
            "Only the name is required. Colors must be #RRGGBB; blank cells use the project original.")
        description.setWordWrap(True)
        layout.addWidget(description)
        form = W.QFormLayout()
        layout.addLayout(form)
        self.combos = {}
        initial = core.suggest_columns(headers)
        if saved and saved.get("headers") == headers:
            initial = saved.get("mapping", initial)
        for field, label, empty in FIELDS:
            combo = W.QComboBox()
            combo.addItem("— " + empty + " —", None)
            for index, header in enumerate(headers):
                combo.addItem(f"{column_letter(index)} — {header or '(no header)'}", index)
            selected = initial.get(field)
            combo.setCurrentIndex(max(0, combo.findData(selected)))
            combo.currentIndexChanged.connect(self.validate_selection)
            form.addRow(label, combo)
            self.combos[field] = combo
        layout.addWidget(W.QLabel("Spreadsheet preview (up to 5 rows):"))
        samples = table[1:6]
        self.preview = W.QTableWidget(len(samples), len(headers))
        self.preview.setHorizontalHeaderLabels(
            [f"{column_letter(i)} — {h or '(no header)'}" for i, h in enumerate(headers)])
        self.preview.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        for row, cells in enumerate(samples):
            for column in range(len(headers)):
                self.preview.setItem(row, column, W.QTableWidgetItem(str(cells[column]) if column < len(cells) else ""))
        self.preview.horizontalHeader().setSectionResizeMode(W.QHeaderView.ResizeToContents)
        layout.addWidget(self.preview, 1)
        self.message = W.QLabel()
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        self.buttons = W.QDialogButtonBox()
        self.import_button = self.buttons.addButton("Load backers", W.QDialogButtonBox.AcceptRole)
        self.buttons.addButton("Cancel", W.QDialogButtonBox.RejectRole)
        self.buttons.accepted.connect(self.accept_mapping)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.validate_selection()

    def selection(self):
        return {field: combo.currentData() for field, combo in self.combos.items()}

    def validate_selection(self):
        # Signals may fire while the form is being constructed.
        if not hasattr(self, "buttons"):
            return
        valid = self.combos["nome_player"].currentData() is not None
        self.import_button.setEnabled(valid)
        self.message.setText("" if valid else "Select the player name column to continue.")

    def accept_mapping(self):
        try:
            mapping = core.validate_columns(self.table[0], self.selection())
            self.rows, self.warnings = core.rows_from_table(self.table, mapping)
        except ValueError as exc:
            self.message.setText(str(exc))
            return
        self.mapping = mapping
        super().accept()
