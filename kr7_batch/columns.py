"""Column selection UI; independent of the Painter API."""
from PySide6 import QtCore, QtWidgets as W

from . import core


FIELDS = [
    ("nome_player", "Nome na skin *", "Selecione uma coluna"),
    ("cor_1", "Cor 1 — PLAYER_COLOR1", "Original do projeto"),
    ("cor_2", "Cor 2 — PLAYER_COLOR2", "Original do projeto"),
    ("cor_3", "Cor 3 — PLAYER_COLOR3", "Original do projeto"),
    ("id", "ID da linha", "Número da linha"),
    ("nome_arquivo", "Nome no ZIP", "Usar nome na skin"),
    ("ativo", "Gerar / ativo", "Todas as linhas"),
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
        self.setWindowTitle("CREAM — Colunas da planilha")
        self.resize(850, 650)
        self.table = table
        self.mapping = None
        headers = table[0]
        layout = W.QVBoxLayout(self)
        description = W.QLabel(
            "Indique onde está cada informação. A primeira linha da planilha contém os cabeçalhos.\n"
            "Somente o nome é obrigatório. Cores devem ser #RRGGBB; células vazias usam o original do projeto.")
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
                combo.addItem(f"{column_letter(index)} — {header or '(sem cabeçalho)'}", index)
            selected = initial.get(field)
            combo.setCurrentIndex(max(0, combo.findData(selected)))
            combo.currentIndexChanged.connect(self.validate_selection)
            form.addRow(label, combo)
            self.combos[field] = combo
        layout.addWidget(W.QLabel("Amostra da planilha (até 5 linhas):"))
        samples = table[1:6]
        self.preview = W.QTableWidget(len(samples), len(headers))
        self.preview.setHorizontalHeaderLabels(
            [f"{column_letter(i)} — {h or '(sem cabeçalho)'}" for i, h in enumerate(headers)])
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
        self.import_button = self.buttons.addButton("Carregar backers", W.QDialogButtonBox.AcceptRole)
        self.buttons.addButton("Cancelar", W.QDialogButtonBox.RejectRole)
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
        self.message.setText("" if valid else "Selecione a coluna do nome para continuar.")

    def accept_mapping(self):
        try:
            mapping = core.validate_columns(self.table[0], self.selection())
            self.rows, self.warnings = core.rows_from_table(self.table, mapping)
        except ValueError as exc:
            self.message.setText(str(exc))
            return
        self.mapping = mapping
        super().accept()
