"""Run with Painter's SDK Python and QT_QPA_PLATFORM=offscreen."""
import json
import os
from pathlib import Path
import sys
import tempfile
import types
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Adobe keeps Qt/Shiboken DLLs next to Painter rather than the embedded interpreter.
_dll_path = Path(sys.executable).resolve().parents[2]
_dll_handle = os.add_dll_directory(str(_dll_path)) if os.name == "nt" else None
from PySide6 import QtWidgets as W
from kr7_batch.columns import ColumnDialog, column_letter

app = W.QApplication.instance() or W.QApplication([])
table = [["Nickname", "Color", "Color"], ["Joseph", "#AABBCC", "#DDEEFF"]]
dialog = ColumnDialog(table)
assert not dialog.import_button.isEnabled()
dialog.combos["nome_player"].setCurrentIndex(1)
dialog.combos["cor_1"].setCurrentIndex(2)
dialog.combos["cor_2"].setCurrentIndex(3)
assert dialog.import_button.isEnabled()
dialog.accept_mapping()
assert dialog.result() == W.QDialog.Accepted
assert dialog.rows[0]["colors"] == ["#AABBCC", "#DDEEFF", None]
profile = {"headers": table[0], "mapping": dialog.mapping}
restored = ColumnDialog(table, profile)
assert restored.selection() == dialog.mapping
changed = ColumnDialog([["Other name", "Color", "Color"]], profile)
assert not changed.import_button.isEnabled()
invalid = ColumnDialog([["nome_player", "cor_1"], ["Joseph", "invalid"]])
invalid.accept_mapping()
assert invalid.result() != W.QDialog.Accepted and "#RRGGBB" in invalid.message.text()
assert column_letter(26) == "AA"

# Exercise the actual Window load/save/cancel paths without opening a Painter project.
sp = types.ModuleType("substance_painter")
sp.__path__ = []
sp.ui = types.ModuleType("substance_painter.ui")
sp.ui.get_main_window = lambda: None
sys.modules["substance_painter"] = sp
sys.modules["substance_painter.ui"] = sp.ui
sys.modules["kr7_batch.painter"] = types.ModuleType("kr7_batch.painter")
from kr7_batch import ui

with tempfile.TemporaryDirectory() as folder, patch.object(ui, "DATA", Path(folder)):
    path = Path(folder) / "input.csv"
    path.write_text("Nickname;Color;Color\nJoseph;#AABBCC;#DDEEFF\n", encoding="utf-8")
    window = ui.Window(auto_update=False)
    window.fields["sheet"].setText(str(path))
    def accept_import(self):
        for field, index in {"nome_player": 1, "cor_1": 2, "cor_2": 3}.items():
            self.combos[field].setCurrentIndex(index)
        self.accept_mapping()
        return self.result()
    with patch.object(ColumnDialog, "exec", accept_import):
        window.load_sheet()
    assert window.rows[0]["colors"] == ["#AABBCC", "#DDEEFF", None]
    assert window.backers.item(0, 2).text() == "Joseph"
    assert json.loads((Path(folder) / "settings.json").read_text())["column_profile"] == profile
    second = ui.Window(auto_update=False)
    assert second.column_profile == profile
    with patch.object(ColumnDialog, "exec", return_value=W.QDialog.Rejected):
        window.load_sheet()
    assert window.rows[0]["name"] == "Joseph"
    for item in (window, second):
        item.stop_updater()
        item.pool.shutdown(wait=True)
print("Passed: Qt mapping, defaults, invalid values, header changes, Window import, settings, cancellation.")
