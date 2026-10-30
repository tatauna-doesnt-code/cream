"""Test the real Qt name-style editor without importing Painter."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_dll = os.add_dll_directory(str(Path(sys.executable).resolve().parents[2]))
from PySide6 import QtGui, QtWidgets as W
from kr7_batch import tm_text
from kr7_batch.name_style import NameStyleHelper, TextColorDialog, document_runs, style_from_format

app = W.QApplication.instance() or W.QApplication([])
QtGui.QFontDatabase.addApplicationFont(r'C:\Windows\Fonts\segoeui.ttf')
app.setFont(QtGui.QFont('Segoe UI', 10))
helper = NameStyleHelper()
helper.resize(1000, 320)
emitted = []
helper.pattern_changed.connect(emitted.append)
raw = '$oKR7 - {name}$z'
helper.set_source(raw)
assert helper.editor.toPlainText() == 'KR7 - {name}'
assert not emitted and helper.source == raw
cursor = helper.editor.textCursor()
cursor.setPosition(0)
cursor.setPosition(3, QtGui.QTextCursor.KeepAnchor)
helper.editor.setTextCursor(cursor)
helper.change_style(italic=True)
assert emitted and '$i' in emitted[-1]
runs = tm_text.parse(emitted[-1], template=True)
assert runs[0][0] == 'KR7' and runs[0][1].bold and runs[0][1].italic
assert runs[1][1].bold and not runs[1][1].italic
helper.change_style(color='primary', shadow=True, width='wide')
assert '{primary}' in emitted[-1]
helper.set_preview('$F80KR7$g - $08FJoseph.zip', {'primary': 'F80', 'secondary': '08F'})
assert helper.preview.toPlainText() == 'KR7 - Joseph.zip'
assert document_runs(helper.preview.document())[0][1].color == 'F80'
helper.show()
app.processEvents()  # Exercises the per-run shadow paint path.
helper.grab().save(str(ROOT / 'dist/name-style-editor.png'))
helper.change_style(reset=True)
assert document_runs(helper.editor.document())[0][1] == tm_text.DEFAULT

# A partial selection spanning differently styled runs retains unrelated formatting.
helper.set_source('$oA$iB$zC')
cursor = helper.editor.textCursor()
cursor.setPosition(0)
cursor.setPosition(2, QtGui.QTextCursor.KeepAnchor)
helper.editor.setTextCursor(cursor)
helper.change_style(uppercase=True)
styled = tm_text.parse(emitted[-1], template=True)
assert styled[0][1].bold and styled[0][1].uppercase and not styled[0][1].italic
assert styled[1][1].bold and styled[1][1].uppercase and styled[1][1].italic

helper.set_source('X')
cursor = helper.editor.textCursor()
cursor.movePosition(QtGui.QTextCursor.End)
helper.editor.setTextCursor(cursor)
helper.editor.insertPlainText('$')
assert emitted[-1] == 'X$$'
helper.set_source('$oX$z')
helper.editor.insertPlainText('Y')
assert tm_text.parse(emitted[-1])[-1] == ('Y', tm_text.DEFAULT)
helper.set_source('Type')
cursor = helper.editor.textCursor()
cursor.movePosition(QtGui.QTextCursor.End)
helper.editor.setTextCursor(cursor)
helper.toggles['bold'].click()
helper.editor.insertPlainText(' bold')
assert tm_text.parse(emitted[-1])[-1][1].bold
helper.set_source('X' * 200)
helper.editor.selectAll()
helper.change_style(shadow=True)
assert helper.source == 'X' * 200 and document_runs(helper.editor.document())[0][1] == tm_text.DEFAULT
assert '200-character' in helper.message.text()
helper.set_source('😀{name}')
cursor = helper.editor.textCursor()
cursor.setPosition(2)
cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)
helper.editor.setTextCursor(cursor)
helper.change_style(italic=True)
assert tm_text.parse(emitted[-1])[0][0] == '😀'

dialog = TextColorDialog({'primary': 'F80', 'secondary': '08F'})
dialog.hex.setText('FF8800')
assert not dialog.apply.isEnabled()
dialog.hex.setText('f80')
assert dialog.apply.isEnabled() and dialog.sliders[1].value() == 8
dialog.apply_literal()
assert dialog.choice == 'F80'
dialog = TextColorDialog({'primary': 'F80', 'secondary': '08F'})
next(b for b in dialog.findChildren(W.QPushButton) if b.text().startswith('Use skin secondary')).click()
assert dialog.choice == 'secondary'
helper.hide()
print('Passed: WYSIWYG selection/editing, mixed styles, shadow paint, dynamic colors, dollar escaping, emoji positions and strict 3-digit picker.')
