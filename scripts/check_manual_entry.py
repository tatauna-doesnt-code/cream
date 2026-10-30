"""Exercise manual/mixed lists, validation and persistence without a Painter project."""
import runpy
from pathlib import Path
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
context = runpy.run_path(str(ROOT / 'scripts/check_columns_ui.py'))
W, ui, app = (context[key] for key in ('W', 'ui', 'app'))
from cream.manual_entry import SkinDialog
from cream.columns import ColumnDialog

with tempfile.TemporaryDirectory() as folder, patch.object(ui, 'DATA', Path(folder)):
    window = ui.Window(auto_update=False)
    def enter(dialog):
        dialog.name.setText('Tester')
        dialog.colors[0].setText('#aabbcc')
        dialog.accept_data()
        return dialog.result()
    with patch.object(SkinDialog, 'exec', enter):
        window.add_skin()
        window.add_skin()
    assert len(window.rows) == 2 and window.rows[0]['colors'] == ['#AABBCC', None, None]
    assert len({r['id'] for r in window.rows}) == 2
    window.ensure_rows()  # No spreadsheet is needed.
    invalid = SkinDialog(window)
    invalid.name.setText('Valid')
    invalid.colors[0].setText('wrong')
    invalid.accept_data()
    assert invalid.result() != W.QDialog.Accepted and '#RRGGBB' in invalid.message.text()
    def edit(dialog):
        dialog.name.setText('Edited')
        dialog.colors[1].setText('#FF0088')
        dialog.accept_data()
        return dialog.result()
    window.backers.selectRow(0)
    with patch.object(SkinDialog, 'exec', edit):
        window.edit_skin()
    assert window.rows[0]['name'] == 'Edited' and window.rows[0]['colors'][1] == '#FF0088'
    path = Path(folder) / 'import.csv'
    path.write_text('nome_player;cor_1\nImported;#112233\n', encoding='utf-8')
    window.fields['sheet'].setText(str(path))
    def accept(dialog):
        dialog.accept_mapping()
        return dialog.result()
    with patch.object(ColumnDialog, 'exec', accept):
        window.load_sheet(append=True)
    assert [r['name'] for r in window.rows] == ['Edited', 'Tester', 'Imported']
    assert window.loaded_sheet is None
    window.ensure_rows()
    window.backers.selectRow(1)
    window.remove_skin()
    assert [r['name'] for r in window.rows] == ['Edited', 'Imported']
    reopened = ui.Window(auto_update=False)
    assert reopened.rows == window.rows
    assert reopened.name_originals == window.name_originals
    assert not reopened.styling_enabled.isChecked()
    reopened.ensure_rows()
    window.saved = {'project': 'test'}
    with patch.object(SkinDialog, 'exec') as dialog:
        window.add_skin()
        window.edit_skin()
        window.remove_skin()
        dialog.assert_not_called()
    window.saved = None
    for item in (window, reopened):
        item.stop_background_tasks()
        item.hide()
print('Passed: manual add/edit/remove, color validation, mixed import, unique IDs, persistence, no-sheet export readiness and preview guards.')
