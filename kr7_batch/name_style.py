"""Compact WYSIWYG editor for filename-compatible Trackmania text styles."""
from dataclasses import replace
from pathlib import Path

from .qt import QtCore, QtGui, QtWidgets as W, exec_dialog

from . import tm_text

STYLE_PROPERTY = int(QtGui.QTextFormat.UserProperty) + 71
_font_ids = []


def game_font():
    if not _font_ids:
        for path in (Path(__file__).parent / "fonts").glob("Montserrat-*.ttf"):
            # Loading bytes avoids Windows holding font files open during future updates.
            identifier = QtGui.QFontDatabase.addApplicationFontFromData(QtCore.QByteArray(path.read_bytes()))
            if identifier >= 0:
                _font_ids.append(identifier)
    return QtGui.QFont("Montserrat", 12)


def style_from_format(fmt):
    data = fmt.property(STYLE_PROPERTY)
    return tm_text.Style(**data) if isinstance(data, dict) else tm_text.DEFAULT


def text_format(style, colors):
    fmt = QtGui.QTextCharFormat()
    if hasattr(fmt, 'setFontFamilies'):
        fmt.setFontFamilies(["Montserrat"])
    else:
        fmt.setFontFamily('Montserrat')
    fmt.setProperty(STYLE_PROPERTY, dict(style.__dict__))
    fmt.setFontWeight(QtGui.QFont.Bold if style.bold else QtGui.QFont.Normal)
    fmt.setFontItalic(style.italic)
    fmt.setFontCapitalization(QtGui.QFont.AllUppercase if style.uppercase else QtGui.QFont.MixedCase)
    font = fmt.font()
    font.setStretch({"normal": 100, "narrow": 65, "wide": 140}[style.width])
    fmt.setFont(font)
    color = colors.get(style.color) if style.color in ("primary", "secondary") else style.color
    fmt.setForeground(QtGui.QColor(tm_text.expand_color(color) if color else "#EEEEEE"))
    return fmt


class StyledLine(W.QTextEdit):
    style_requested = QtCore.Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.setFont(game_font())
        self.document().setDefaultFont(game_font())
        self.setLineWrapMode(W.QTextEdit.NoWrap)
        self.setFixedHeight(56)
        self.setStyleSheet("QTextEdit { background: #242424; color: #eeeeee; border: 1px solid #666; padding: 4px; }")

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            return
        if not self.isReadOnly():
            for sequence, field in ((QtGui.QKeySequence.Bold, "bold"), (QtGui.QKeySequence.Italic, "italic")):
                if event.matches(sequence):
                    self.style_requested.emit(field)
                    return
            if event.matches(QtGui.QKeySequence.Underline):
                return  # Trackmania has no standalone underline text-style code.
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        self.insertPlainText(source.text().replace("\r", " ").replace("\n", " ").replace("\t", " "))

    def paintEvent(self, event):
        super().paintEvent(event)
        # QTextDocument has no per-run drop shadow. Paint a shadow-only copy,
        # then draw the foreground/selection again so the shadow remains behind it.
        runs = document_runs(self.document())
        if not any(style.shadow for _, style in runs):
            return
        shadow = self.document().clone()
        cursor = QtGui.QTextCursor(shadow)
        position = 0
        for text, style in runs:
            cursor.setPosition(position)
            position += len(text.encode("utf-16-le")) // 2
            cursor.setPosition(position, QtGui.QTextCursor.KeepAnchor)
            fmt = QtGui.QTextCharFormat()
            fmt.setForeground(QtGui.QColor(0, 0, 0, 210) if style.shadow else QtGui.QColor("transparent"))
            cursor.mergeCharFormat(fmt)
        painter = QtGui.QPainter(self.viewport())
        painter.translate(-self.horizontalScrollBar().value(), -self.verticalScrollBar().value())
        painter.translate(1.5, 1.5)
        shadow.drawContents(painter)
        painter.translate(-1.5, -1.5)
        context = QtGui.QAbstractTextDocumentLayout.PaintContext()
        current = self.textCursor()
        if current.hasSelection():
            selection = QtGui.QAbstractTextDocumentLayout.Selection()
            selection.cursor = current
            selection.format.setBackground(self.palette().highlight())
            selection.format.setForeground(self.palette().highlightedText())
            context.selections = [selection]
        if self.hasFocus() and not self.isReadOnly():
            context.cursorPosition = current.position()
        self.document().documentLayout().draw(painter, context)
        painter.end()


def document_runs(document):
    runs = []
    block = document.begin()
    while block.isValid():
        iterator = block.begin()
        while not iterator.atEnd():
            fragment = iterator.fragment()
            if fragment.isValid():
                runs.append((fragment.text(), style_from_format(fragment.charFormat())))
            iterator += 1
        block = block.next()
    return runs


class TextColorDialog(W.QDialog):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Trackmania text color")
        self.choice = None
        self.colors = colors
        layout = W.QVBoxLayout(self)
        layout.addWidget(W.QLabel("Text colors use exactly three hex digits ($RGB)."))
        self.hex = W.QLineEdit("FFF")
        self.hex.setPlaceholderText("F80")
        self.hex.setToolTip("Exactly 3 digits. Six-digit HEX colors are not accepted.")
        form = W.QFormLayout()
        form.addRow("RGB", self.hex)
        layout.addLayout(form)
        self.sliders = []
        for index, channel in enumerate(("Red", "Green", "Blue")):
            slider = W.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 15)
            slider.setValue(15)
            slider.valueChanged.connect(self.slider_changed)
            self.sliders.append(slider)
            form.addRow(channel + " (0–F)", slider)
        self.swatch = W.QLabel("#FFFFFF · $FFF")
        self.swatch.setMinimumHeight(38)
        self.swatch.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.swatch)
        self.error = W.QLabel()
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        self.apply = W.QPushButton("Apply text color")
        self.apply.clicked.connect(self.apply_literal)
        layout.addWidget(self.apply)
        for key, title in (("primary", "Use skin primary color"), ("secondary", "Use skin secondary color")):
            code = colors.get(key)
            button = W.QPushButton(title + (" · $" + code if code else " · per backer"))
            if code:
                swatch = QtGui.QPixmap(16, 16)
                swatch.fill(QtGui.QColor(tm_text.expand_color(code)))
                button.setIcon(QtGui.QIcon(swatch))
            button.setToolTip("Uses color " + ("1" if key == "primary" else "2") + " for each backer, rounded to Trackmania's 3-digit palette.")
            button.clicked.connect(lambda checked=False, value=key: self.choose(value))
            layout.addWidget(button)
        default = W.QPushButton("Use default text color ($g)")
        default.clicked.connect(lambda: self.choose(""))
        layout.addWidget(default)
        cancel = W.QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel)
        self.hex.textChanged.connect(self.hex_changed)
        self.hex_changed()

    def slider_changed(self):
        self.hex.setText("".join(format(slider.value(), "X") for slider in self.sliders))

    def hex_changed(self):
        try:
            value = tm_text.color3(self.hex.text())
        except ValueError as exc:
            self.apply.setEnabled(False)
            self.error.setText(str(exc))
            return
        self.apply.setEnabled(True)
        self.error.clear()
        for slider, value_char in zip(self.sliders, value):
            blocker = QtCore.QSignalBlocker(slider)
            slider.setValue(int(value_char, 16))
            del blocker
        expanded = tm_text.expand_color(value)
        self.swatch.setText(expanded + " · $" + value)
        # Contrast only affects this UI swatch, not the chosen TM text color.
        light = sum(int(c, 16) for c in value) > 22
        self.swatch.setStyleSheet("background: " + expanded + "; color: " + ("black" if light else "white") + ";")

    def choose(self, choice):
        self.choice = choice
        self.accept()

    def apply_literal(self):
        try:
            self.choose(tm_text.color3(self.hex.text()))
        except ValueError as exc:
            self.error.setText(str(exc))


class NameStyleHelper(W.QWidget):
    pattern_changed = QtCore.Signal(str)
    color_requested = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source = None
        self.colors = {}
        self.syncing = False
        layout = W.QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 4)
        tools = W.QHBoxLayout()
        self.toggles = {}
        for title, key, code in (("B", "bold", "$o"), ("I", "italic", "$i"),
                                 ("ABC", "uppercase", "$t"), ("Shadow", "shadow", "$s")):
            button = W.QToolButton()
            button.setText(title)
            font = button.font()
            font.setBold(key == "bold")
            font.setItalic(key == "italic")
            button.setFont(font)
            button.setCheckable(True)
            button.setToolTip(key.capitalize() + " (" + code + ")")
            button.setFocusPolicy(QtCore.Qt.NoFocus)
            button.clicked.connect(lambda checked=False, field=key: self.change_style(**{field: checked}))
            tools.addWidget(button)
            self.toggles[key] = button
        self.width_combo = W.QComboBox()
        for label, value in (("Normal ($m)", "normal"), ("Narrow ($n)", "narrow"), ("Wide ($w)", "wide")):
            self.width_combo.addItem(label, value)
        self.width_combo.activated.connect(lambda: self.change_style(width=self.width_combo.currentData()))
        tools.addWidget(self.width_combo)
        color = W.QPushButton("Text color…")
        color.setFocusPolicy(QtCore.Qt.NoFocus)
        color.clicked.connect(self.pick_color)
        tools.addWidget(color)
        reset = W.QPushButton("Reset style ($z)")
        reset.setFocusPolicy(QtCore.Qt.NoFocus)
        reset.clicked.connect(lambda: self.change_style(reset=True))
        tools.addWidget(reset)
        dollar = W.QPushButton("$")
        dollar.setToolTip("Insert a literal dollar ($$ in the filename)")
        dollar.setFocusPolicy(QtCore.Qt.NoFocus)
        dollar.clicked.connect(lambda: self.editor.insertPlainText("$"))
        tools.addWidget(dollar)
        tools.addStretch()
        layout.addLayout(tools)
        self.editor = StyledLine()
        self.editor.setAccessibleName("Styled ZIP name pattern")
        layout.addWidget(self.editor)
        self.message = W.QLabel()
        self.message.setWordWrap(True)
        self.message.hide()
        layout.addWidget(self.message)
        instruction = W.QLabel("Select text to style it, or choose a style and type. Name tokens are resolved in the preview below.")
        instruction.setWordWrap(True)
        layout.addWidget(instruction)
        self.preview = StyledLine()
        preview_font = game_font()
        preview_font.setPointSize(24)
        self.preview.setFont(preview_font)
        self.preview.document().setDefaultFont(preview_font)
        self.preview.setFixedHeight(84)
        self.preview.setReadOnly(True)
        self.preview.setAccessibleName("Trackmania filename preview")
        layout.addWidget(self.preview)
        caption = W.QLabel("In-game name preview · Font metrics are approximate. Styling changes the ZIP name only.")
        caption.setWordWrap(True)
        layout.addWidget(caption)
        self.editor.textChanged.connect(self.edited)
        self.editor.currentCharFormatChanged.connect(self.sync_toolbar)
        self.editor.style_requested.connect(lambda field: self.change_style(**{
            field: not getattr(style_from_format(self.editor.currentCharFormat()), field)}))
        layout.setSizeConstraint(W.QLayout.SetMinimumSize)

    def fill(self, widget, source):
        blocker = QtCore.QSignalBlocker(widget)
        cursor = QtGui.QTextCursor(widget.document())
        cursor.select(QtGui.QTextCursor.Document)
        cursor.removeSelectedText()
        for text, style in tm_text.parse(source, template=widget is self.editor, final=True):
            if text:
                fmt = text_format(style, self.colors)
                if widget is self.preview:
                    fmt.setFontPointSize(24)
                cursor.insertText(text, fmt)
        if widget is self.editor:
            widget.setTextCursor(cursor)
            widget.setCurrentCharFormat(text_format(style, self.colors))
        widget.document().clearUndoRedoStacks()
        del blocker

    def set_source(self, source):
        if source == self.source:
            return
        self.source = source
        self.message.clear()
        self.message.hide()
        self.syncing = True
        self.fill(self.editor, source)
        self.syncing = False
        self.sync_toolbar()

    def set_preview(self, name, colors):
        changed = self.colors != colors
        self.colors = colors
        self.fill(self.preview, name)
        if not changed:
            return
        # Refresh dynamic swatches while retaining the editor's selection and undo stack.
        blocker = QtCore.QSignalBlocker(self.editor)
        current = self.editor.textCursor()
        typing_style = style_from_format(self.editor.currentCharFormat())
        cursor = QtGui.QTextCursor(self.editor.document())
        position = 0
        for text, style in document_runs(self.editor.document()):
            cursor.setPosition(position)
            position += len(text.encode("utf-16-le")) // 2
            cursor.setPosition(position, QtGui.QTextCursor.KeepAnchor)
            cursor.mergeCharFormat(text_format(style, colors))
        self.editor.setTextCursor(current)
        if not current.hasSelection():
            self.editor.setCurrentCharFormat(text_format(typing_style, colors))
        del blocker

    def sync_toolbar(self, *args):
        if self.syncing:
            return
        style = style_from_format(self.editor.currentCharFormat())
        for key, button in self.toggles.items():
            button.setChecked(getattr(style, key))
        blocker = QtCore.QSignalBlocker(self.width_combo)
        self.width_combo.setCurrentIndex(self.width_combo.findData(style.width))
        del blocker

    def change_style(self, reset=False, **values):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            # Snapshot fragment boundaries; formatting may merge fragments during the edit.
            spans, position = [], 0
            for text, style in document_runs(self.editor.document()):
                length = len(text.encode("utf-16-le")) // 2
                if position < end and position + length > start:
                    spans.append((max(position, start), min(position + length, end),
                                  tm_text.DEFAULT if reset else replace(style, **values)))
                position += length
            cursor.beginEditBlock()
            for begin, finish, style in spans:
                part = QtGui.QTextCursor(self.editor.document())
                part.setPosition(begin)
                part.setPosition(finish, QtGui.QTextCursor.KeepAnchor)
                part.setCharFormat(text_format(style, self.colors))
            cursor.endEditBlock()
        else:
            style = style_from_format(self.editor.currentCharFormat())
            self.editor.setCurrentCharFormat(text_format(tm_text.DEFAULT if reset else replace(style, **values), self.colors))
        self.editor.setFocus()
        self.sync_toolbar()

    def pick_color(self):
        self.color_requested.emit()
        dialog = TextColorDialog(self.colors, self)
        if exec_dialog(dialog) == W.QDialog.Accepted:
            self.change_style(color=dialog.choice)

    def edited(self):
        if self.syncing:
            return
        runs = document_runs(self.editor.document())
        source = tm_text.serialize(runs)
        if runs and runs[-1][1] != tm_text.DEFAULT:
            source += "$z"
        if len(source) > 200:
            self.syncing = True
            self.editor.undo()
            self.syncing = False
            self.message.setText("This styling exceeds the 200-character pattern limit. Simplify the formatting.")
            self.message.show()
            return
        self.message.clear()
        self.message.hide()
        self.source = source
        self.pattern_changed.emit(source)
