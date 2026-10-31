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
from PySide6 import QtGui, QtWidgets as W
sp = types.ModuleType('substance_painter')
sp.__path__ = []
sp.application = types.ModuleType('substance_painter.application')
sp.application.version_info = lambda: (12, 1, 3)
sys.modules['substance_painter'] = sp
sys.modules['substance_painter.application'] = sp.application
from cream.columns import ColumnDialog, column_letter

app = W.QApplication.instance() or W.QApplication([])
QtGui.QFontDatabase.addApplicationFont(r'C:\Windows\Fonts\segoeui.ttf')
app.setFont(QtGui.QFont('Segoe UI', 9))
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
sp.application = types.ModuleType('substance_painter.application')
sp.application.version_info = lambda: (12, 1, 3)
sys.modules['substance_painter.application'] = sp.application
sys.modules["cream.painter"] = types.ModuleType("cream.painter")
from cream import ui
ui.painter.ready = lambda: False

with tempfile.TemporaryDirectory() as folder, patch.object(ui, "DATA", Path(folder)):
    path = Path(folder) / "input.csv"
    path.write_text("Nickname;Color;Color\nJoseph;#AABBCC;#DDEEFF\n", encoding="utf-8")
    window = ui.Window(auto_update=False)
    assert 'converter' not in window.fields
    assert window.fields["name_pattern"].text() == "skin"
    assert window.styling_enabled.isChecked()
    window.fields["name_pattern"].setText("{name}")
    window.fields["sheet"].setText(str(path))
    window.fields["output"].setText(str(Path(folder) / 'skins'))
    original_sheet = path.read_bytes()
    def accept_import(self):
        for field, index in {"nome_player": 1, "cor_1": 2, "cor_2": 3}.items():
            self.combos[field].setCurrentIndex(index)
        self.accept_mapping()
        return self.result()
    with patch.object(ColumnDialog, "exec", accept_import):
        window.load_sheet()
    assert window.rows[0]["colors"] == ["#AABBCC", "#DDEEFF", None]
    assert window.backers.item(0, 2).text() == "Joseph"
    cell = window.name_cells[0]
    assert not cell.reset.isEnabled() and not cell.reset.icon().isNull() and not cell.reset.text()
    cell.editor.setText("Bompi")
    assert window.rows[0]['name'] == 'Bompi' and window.rows[0]['stem'] == 'Bompi'
    assert cell.editor.font().bold() and cell.editor.font().italic() and cell.reset.isEnabled()
    assert window.backers.item(0, 6).text() == 'Bompi.zip'
    cell.editor.setText('')
    try:
        window.ensure_rows()
        raise AssertionError('Invalid edited name was accepted')
    except ValueError:
        pass
    assert window.invalid_names and 'invalid player name' in window.reload_block_reason()
    cell.reset.click()
    assert window.rows[0]['name'] == 'Joseph' and not window.invalid_names
    assert not cell.editor.font().bold() and not cell.editor.font().italic() and not cell.reset.isEnabled()
    window.saved = {}
    window.sync_name_editing()
    assert cell.editor.isReadOnly() and not cell.reset.isEnabled()
    cell.editor.setText('Blocked change')
    assert window.rows[0]['name'] == 'Joseph' and cell.editor.text() == 'Joseph'
    window.saved = None
    window.sync_name_editing()
    assert not cell.editor.isReadOnly()
    assert path.read_bytes() == original_sheet
    window.styling_enabled.setChecked(True)
    assert not window.name_style.isHidden()
    window.fields["name_pattern"].setText("{primary}{name}$g - {secondary}Event")
    assert window.name_preview.text() == "$ABCJoseph$g - $DEFEvent.zip"
    assert window.name_style.preview.toPlainText() == "Joseph - Event.zip"
    raw = window.fields["name_pattern"].text()
    window.styling_enabled.setChecked(False)
    assert window.fields["name_pattern"].text() == raw
    window.fields["name_pattern"].setText("Community - {name} - {id}")
    assert window.backers.item(0, 6).text() == "Community - Joseph - 2.zip"
    assert window.name_preview.text() == window.backers.item(0, 6).text()
    window.fields["name_pattern"].setText("{unknown}")
    assert window.backers.item(0, 6).text() == "Invalid name pattern"
    window.fields["name_pattern"].setText("Community - {name}")
    wheels = window.texture_sets.groups['Wheels']
    wheels.export.click()
    wheels.resolution.setCurrentIndex(wheels.resolution.findData(4096))
    wheels.sizes[1].setCurrentIndex(wheels.sizes[1].findData(2048))
    window.save_settings()
    base = Path(folder) / "base.zip"
    base.write_bytes(b"signature fixture")
    window.fields["base"].setText(str(base))
    with patch.object(ui.painter, "project_path", return_value="project.spp", create=True), \
            patch.object(ui.painter, "preset_maps", return_value=[], create=True):
        custom_signature = window.config_signature()
        window.fields["name_pattern"].setText("CUP - {name}")
        legacy_signature = window.config_signature()
        assert custom_signature != legacy_signature
        expected_legacy = ui.core.fingerprint({"project": "project.spp", "base": str(base.resolve()),
            "base_size": base.stat().st_size, "base_mtime": base.stat().st_mtime_ns,
            "maps": window.selections(), "preset": [], "normal_invert": False,
            "dds_headers": "BC4U_BC5U", "normal_export": "Normal_OpenGL", "zip_name_pattern": "CUP - {name}"})
        assert legacy_signature == expected_legacy
    window.fields["name_pattern"].setText("Community - {name}")
    window.save_settings()
    assert json.loads((Path(folder) / "settings.json").read_text())["column_profile"] == profile
    second = ui.Window(auto_update=False)
    assert second.column_profile == profile
    assert second.fields["name_pattern"].text() == "skin"
    assert second.texture_sets.settings() == window.texture_sets.settings()
    with patch.object(ColumnDialog, "exec", return_value=W.QDialog.Rejected):
        window.load_sheet()
    assert window.rows[0]["name"] == "Joseph"
    window.name_cells[0].editor.setText('Bompi')
    window.show()
    app.processEvents()
    app.processEvents()
    window.grab().save(str(Path(__file__).resolve().parents[1] / 'dist/ui-manual-player-name.png'))
    window.name_cells[0].reset.click()
    settings = json.loads((Path(folder) / "settings.json").read_text())
    settings["fields"].pop("name_pattern")
    settings['fields']['converter'] = 'C:/obsolete/custom/texconv.exe'
    settings['tm_styling'] = True
    (Path(folder) / "settings.json").write_text(json.dumps(settings))
    legacy = ui.Window(auto_update=False)
    assert legacy.fields["name_pattern"].text() == "skin"
    assert legacy.styling_enabled.isChecked()
    assert 'converter' not in legacy.fields and ui.CONVERTER == Path(ui.__file__).parent / 'bin/texconv.exe'
    for item in (window, second, legacy):
        item.stop_updater()
        item.pool.shutdown(wait=True)
print("Passed: Qt mapping, defaults, invalid values, header changes, Window import, settings, cancellation.")
