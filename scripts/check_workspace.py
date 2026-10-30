"""Exercise first-use navigation and capture the actual Qt layouts without a project."""
import runpy
from pathlib import Path
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
context = runpy.run_path(str(ROOT / "scripts/check_columns_ui.py"))
W, ui, app = (context[key] for key in ("W", "ui", "app"))
from PySide6 import QtCore, QtGui

app.setStyle("Fusion")
palette = QtGui.QPalette()
for role, color in [("Window", "#303030"), ("WindowText", "#eeeeee"), ("Base", "#242424"),
                    ("AlternateBase", "#2b2b2b"), ("Text", "#eeeeee"), ("Button", "#393939"),
                    ("ButtonText", "#eeeeee"), ("Highlight", "#326b96"), ("HighlightedText", "#ffffff")]:
    palette.setColor(getattr(QtGui.QPalette, role), QtGui.QColor(color))
app.setPalette(palette)

with tempfile.TemporaryDirectory() as folder, patch.object(ui, "DATA", Path(folder)):
    window = ui.Window(auto_update=False)
    window.show()
    app.processEvents()
    assert window.tabs.currentWidget() is window.skins_page
    assert not window.export_button.isEnabled()
    assert not window.preview_button.isEnabled()
    assert window.tabs.indexOf(window.settings_page) == 4
    window.grab().save(str(ROOT / "dist/workspace-01-setup.png"))
    window.tabs.setCurrentWidget(window.skins_page)
    app.processEvents()
    assert window.empty_state.isVisible() and not window.backers.isVisible()
    window.grab().save(str(ROOT / "dist/workspace-02-empty.png"))
    rows = [{"line": i + 2, "id": str(i + 1), "name": name, "stem": name,
             "colors": ["#FFC878", "#8FDFFF", None]} for i, name in enumerate(
                 ["Bompi", "DaBest", "Tevs", "Ice", "p0Sik", "Teak", "karl_jr23"])]
    window.restore_reload_state({"rows": rows, "loaded_sheet": None,
        "checked": [True] * len(rows), "selected": 0, "log": "Ready for validation."})
    window.fields["base"].setText("C:/Skins/Base.zip")
    skin = window.texture_sets.groups["Skin"]
    skin.table.item(0, 0).setCheckState(QtCore.Qt.Checked)
    assert window.export_button.isEnabled()
    assert window.export_button.text() == "Export 7 skins"
    assert not window.empty_state.isVisible()
    window.name_cells[4].editor.setText("p0Sik!")
    app.processEvents()
    window.grab().save(str(ROOT / "dist/workspace-03-skins.png"))
    window.saved = {"project": "test"}
    window.sync_name_editing()
    assert window.preview_banner.isVisible()
    assert window.inline_restore.isEnabled()
    assert window.preview_help.timer.isActive()
    assert window.export_button in window.preview_help.targets
    assert window.name_cells[0].editor in window.preview_help.targets
    window.move(0, 0)
    window.resize(900, 700)
    app.processEvents()
    QtGui.QCursor.setPos(window.export_button.mapToGlobal(window.export_button.rect().center()))
    # Offscreen Qt does not provide native disabled-widget hit testing.
    with patch.object(W.QApplication, 'widgetAt', return_value=window.export_button):
        window.preview_help.follow()
    assert window.preview_help.tip.isVisible()
    assert 'Export is locked' in window.preview_help.tip.text()
    assert 'Restore original' in window.preview_help.tip.text()
    assert not window.export_button.isEnabled() and not window.load_button.isEnabled()
    window.saved = None
    window.sync_name_editing()
    assert not window.preview_banner.isVisible()
    assert not window.inline_restore.isEnabled()
    assert not window.preview_help.timer.isActive()
    assert window.tabs.tabText(2) == '3  ZIP names'
    assert window.tabs.tabText(3) == 'Logs'
    window.tabs.setCurrentWidget(window.textures_page)
    skin.expand.click()
    app.processEvents()
    window.grab().save(str(ROOT / "dist/workspace-04-textures.png"))
    window.tabs.setCurrentWidget(window.naming_page)
    window.styling_enabled.setChecked(True)
    window.fields["name_pattern"].setText("$o{primary}Event - {name}$z")
    app.processEvents()
    window.grab().save(str(ROOT / "dist/workspace-05-names.png"))
    window.resize(900, 700)
    app.processEvents()
    assert window.name_style.geometry().bottom() < window.naming_page.height()
    assert window.export_button.geometry().right() < window.width()
    window.grab().save(str(ROOT / "dist/workspace-06-small.png"))
    window.tabs.setCurrentWidget(window.settings_page)
    app.processEvents()
    assert window.tabs.currentWidget() is window.settings_page
    window.grab().save(str(ROOT / "dist/workspace-07-updates.png"))

    window.help_link.click()
    app.processEvents()
    assert window.tabs.currentWidget() is window.help_page
    assert window.help_link.isChecked()
    questions = window.help_page.findChildren(W.QToolButton)
    questions[0].click()
    app.processEvents()
    window.grab().save(str(ROOT / 'dist/workspace-08-help.png'))
    assert window.name_style.preview.document().defaultFont().family() == 'Montserrat'
    assert window.name_style.preview.document().defaultFont().pointSize() == 24
    assert window.name_style.editor.document().defaultFont().pointSize() == 12
    from concurrent.futures import Future
    for interactive in (False, True):
        window.update_future = Future()
        window.update_future.set_exception(ui.updater.AccessRequired('private'))
        window.update_mode = 'check'
        window.update_interactive = interactive
        with patch.object(window, 'configure_access') as prompt:
            window.poll_update()
            assert prompt.call_count == int(interactive)
        assert not window.access_button.isHidden()
        assert 'private' in window.update_status.text()
    window.stop_background_tasks()
    window.hide()
print("Passed: setup, empty state, selection counts, preview guard, navigation, naming, compact layout and updates dialog.")
