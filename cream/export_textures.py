"""Project/template-driven texture controls, with explicit Trackmania overrides."""
from pathlib import Path
from .qt import QtCore, QtGui, QtWidgets as W
from . import core, painter, template_export, compatibility
from .controls import InstantInfo, set_chevron, CenteredCheckDelegate
from .texture_sets import add_resolutions, SetCheckBox, LABELS

REFERENCE = '<table cellspacing="0" cellpadding="7" border="1"><tr><th>Suffix</th><th>Contents</th><th>DDS</th></tr>' + ''.join(
    '<tr><td>_' + suffix + '</td><td>' + LABELS[suffix].split(' (_')[0] + '</td><td>' + compression.split('_')[0] + '</td></tr>'
    for suffix, compression in core.MAPS.items()) + '</table>'
MISSING = 'The usual Trackmania export template (TM2020) could not be located. Pick an installed export template to populate the textures.'


def warning_icon(text=''):
    label = InstantInfo()
    label.setPixmap(label.style().standardIcon(W.QStyle.SP_MessageBoxWarning).pixmap(16, 16))
    label.setFixedSize(22, 32)
    label.setAlignment(QtCore.Qt.AlignCenter)
    label.setToolTip(text)
    return label


class Override(W.QWidget):
    changed = QtCore.Signal()
    def __init__(self, value, owner, choices=None):
        super().__init__()
        self.original = value
        self.owner = owner
        layout = W.QHBoxLayout(self)
        layout.setContentsMargins(2, 4, 2, 4)
        layout.setSpacing(3)
        self.reset = W.QToolButton()
        self.reset.setIcon(self.style().standardIcon(W.QStyle.SP_BrowserReload))
        self.reset.setToolTip('Restore template default: ' + value)
        self.reset.setAccessibleName('Restore template default')
        self.reset.setFixedSize(32, 32)
        self.input = W.QComboBox() if choices else W.QLineEdit(value)
        self.input.setFixedHeight(32)
        if choices:
            self.input.addItems(choices)
            self.input.setCurrentText(value)
            self.input.activated.connect(self.edited)
        else:
            self.input.setMaxLength(100)
            self.input.textEdited.connect(self.edited)
        self.alert = warning_icon()
        layout.addWidget(self.reset)
        layout.addWidget(self.input, 1)
        layout.addWidget(self.alert)
        self.reset.clicked.connect(lambda: self.set_value(self.original))
        self.refresh()

    def value(self):
        return self.input.currentText() if isinstance(self.input, W.QComboBox) else self.input.text()

    def set_value(self, value):
        if isinstance(self.input, W.QComboBox):
            self.input.setCurrentText(value)
        else:
            self.input.setText(value)
        self.refresh()
        self.changed.emit()

    def edited(self, *args):
        if not self.owner.confirm_override():
            self.set_value(getattr(self, 'previous', self.original))
            return
        self.refresh()
        self.changed.emit()

    def refresh(self):
        self.previous = self.value()
        modified = self.value() != self.original
        font = self.input.font()
        font.setBold(modified)
        font.setItalic(modified)
        self.input.setFont(font)
        self.reset.setEnabled(modified)

    def warn(self, reason):
        self.alert.setToolTip(reason)
        self.alert.setVisible(bool(reason))


class Section(W.QWidget):
    changed = QtCore.Signal()
    def __init__(self, name, records, owner):
        super().__init__()
        self.texture_set, self.records = name, records
        self.setObjectName('textureSetCard')
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        layout = W.QVBoxLayout(self)
        layout.setContentsMargins(1, 0, 1, 0)
        layout.setSpacing(0)
        header_widget = W.QWidget()
        header_widget.setObjectName('textureSetHeader')
        header_widget.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        header = W.QHBoxLayout(header_widget)
        header.setContentsMargins(0, 4, 8, 4)
        header.setSpacing(6)
        self.export = SetCheckBox()
        self.export.setTristate(True)
        self.expand = W.QToolButton()
        self.expand.setText(name)
        self.expand.setCheckable(True)
        self.expand.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.expand.setFixedHeight(32)
        self.expand.setMinimumWidth(110)
        self.expand.setStyleSheet('QToolButton { text-align: left; padding: 4px 8px; border: none; background: transparent; font-weight: 600; } QToolButton:hover { background: #424b51; }')
        set_chevron(self.expand)
        self.summary = W.QLabel()
        self.resolution = W.QComboBox()
        self.resolution.setFixedHeight(32)
        self.resolution.addItem('Mixed', None)
        self.resolution.model().item(0).setEnabled(False)
        add_resolutions(self.resolution, name)
        self.resolution.setCurrentIndex(self.resolution.findData(2048))
        self.check_cell = W.QWidget()
        self.check_cell.setFixedSize(40, 40)
        check_layout = W.QHBoxLayout(self.check_cell)
        check_layout.setContentsMargins(0, 0, 0, 0)
        self.export.setFixedSize(18, 18)
        check_layout.addWidget(self.export, 0, QtCore.Qt.AlignCenter)
        header.addWidget(self.check_cell)
        header.addWidget(self.expand, 0, QtCore.Qt.AlignLeft)
        header.addWidget(self.summary, 0, QtCore.Qt.AlignLeft)
        header.addStretch(1)
        self.resolution.setFixedWidth(140)
        self.resolution.setAccessibleName(name + ' resolution for all textures')
        header.addWidget(self.resolution)
        layout.addWidget(header_widget)
        self.table = W.QTableWidget(len(records), 5)
        self.table.setHorizontalHeaderLabels(['', 'Output', 'Suffix', 'DDS', 'Resolution'])
        self.table.verticalHeader().hide()
        self.table.setItemDelegateForColumn(0, CenteredCheckDelegate(self.table))
        self.table.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(W.QAbstractItemView.NoSelection)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.horizontalHeader().setSectionResizeMode(W.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, W.QHeaderView.Fixed)
        self.table.horizontalHeader().setMinimumSectionSize(20)
        self.table.setColumnWidth(0, 40)
        self.table.horizontalHeader().setSectionResizeMode(1, W.QHeaderView.Stretch)
        self.table.setStyleSheet('QTableWidget { border: none; border-top: 1px solid #494c50; background: #222426; } QHeaderView::section { background: #292b2e; color: #cccccc; border: none; border-bottom: 1px solid #44474a; padding: 4px; }')
        for column, width in ((2, 210), (3, 180), (4, 140)):
            self.table.horizontalHeader().setSectionResizeMode(column, W.QHeaderView.Interactive)
            self.table.setColumnWidth(column, width)
        self.table.setHorizontalScrollMode(W.QAbstractItemView.ScrollPerPixel)
        self.suffixes, self.compressions, self.sizes = [], [], []
        for index, record in enumerate(records):
            item = W.QTableWidgetItem()
            item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.table.setItem(index, 0, item)
            output = W.QTableWidgetItem(record['source'])
            output.setToolTip('Original template output: ' + record['source'])
            self.table.setItem(index, 1, output)
            suffix = Override(record['suffix'], owner)
            suffix.input.setAccessibleName(name + ' ' + record['source'] + ' suffix')
            suffix.input.setToolTip('Filename suffix after the final underscore; omit the separator. Example: B produces _B.dds.')
            compression = Override(record['compression'], owner, ['BC1', 'BC3', 'BC4', 'BC5'])
            compression.input.setAccessibleName(name + ' ' + record['source'] + ' DDS compression')
            self.suffixes.append(suffix)
            self.compressions.append(compression)
            size = W.QComboBox()
            size.setFixedHeight(32)
            add_resolutions(size, name)
            size.setCurrentIndex(size.findData(2048))
            self.sizes.append(size)
            for column, widget in ((2, suffix), (3, compression), (4, size)):
                if column == 4:
                    cell = W.QWidget()
                    cell_layout = W.QHBoxLayout(cell)
                    cell_layout.setContentsMargins(2, 4, 2, 4)
                    cell_layout.addWidget(widget, 1, QtCore.Qt.AlignVCenter)
                    self.table.setCellWidget(index, column, cell)
                else:
                    self.table.setCellWidget(index, column, widget)
            suffix.changed.connect(self.update)
            compression.changed.connect(self.update)
            size.currentIndexChanged.connect(self.update)
        self.table.setFixedHeight(min(400, self.table.horizontalHeader().sizeHint().height() + len(records) * 40 + 2))
        self.body = self.table
        layout.addWidget(self.table)
        self.table.hide()
        self.expand.toggled.connect(self.set_expanded)
        self.export.stateChanged.connect(self.toggle_all)
        self.resolution.activated.connect(self.apply_resolution)
        self.table.itemChanged.connect(self.update)
        self.update()

    def set_expanded(self, expanded):
        self.table.setVisible(expanded)
        set_chevron(self.expand, expanded)

    def toggle_all(self, *args):
        checked = self.export.checkState() == QtCore.Qt.Checked
        blocker = QtCore.QSignalBlocker(self.table)
        for i in range(len(self.records)):
            self.table.item(i, 0).setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
        del blocker
        self.update()

    def apply_resolution(self, *args):
        size = self.resolution.currentData()
        for widget in self.sizes:
            blocker = QtCore.QSignalBlocker(widget)
            widget.setCurrentIndex(widget.findData(size))
            del blocker
        self.update()

    def update(self, *args):
        count = sum(self.table.item(i, 0).checkState() == QtCore.Qt.Checked for i in range(len(self.records)))
        blocker = QtCore.QSignalBlocker(self.export)
        self.export.setCheckState(QtCore.Qt.Unchecked if count == 0 else QtCore.Qt.Checked if count == len(self.records) else QtCore.Qt.PartiallyChecked)
        del blocker
        self.summary.setText(f'{count} / {len(self.records)} selected')
        values = {size.currentData() for size in self.sizes}
        blocker = QtCore.QSignalBlocker(self.resolution)
        self.resolution.setCurrentIndex(self.resolution.findData(next(iter(values))) if len(values) == 1 else 0)
        del blocker
        for suffix, compression in zip(self.suffixes, self.compressions):
            expected = core.MAPS.get(suffix.value())
            reason = ('Unknown Trackmania suffix. Check the TM2020 reference table.' if expected is None else
                      'Trackmania expects ' + expected.split('_')[0] + ' for _' + suffix.value() + '.' if compression.value() != expected.split('_')[0] else '')
            suffix.warn(reason)
            compression.warn(reason)
        self.changed.emit()

    def state(self):
        return [dict(id=r['id'], checked=self.table.item(i, 0).checkState() == QtCore.Qt.Checked,
                     suffix=self.suffixes[i].value(), compression=self.compressions[i].value(), size=self.sizes[i].currentData())
                for i, r in enumerate(self.records)]

    def restore(self, state):
        for i, record in enumerate(self.records):
            saved = next((r for r in state if r.get('id') == record['id']), None)
            if not saved:
                continue
            self.suffixes[i].set_value(saved.get('suffix', record['suffix']))
            compression = saved.get('compression', record['compression'])
            if compression in ('BC1', 'BC3', 'BC4', 'BC5'):
                self.compressions[i].set_value(compression)
            size = self.sizes[i].findData(saved.get('size', 2048))
            self.sizes[i].setCurrentIndex(max(0, size))
            self.table.item(i, 0).setCheckState(QtCore.Qt.Checked if saved.get('checked') else QtCore.Qt.Unchecked)
        self.update()

    def selections(self):
        return [dict(record, set=self.texture_set, map=record['id'], suffix=self.suffixes[i].value(),
                     compression=self.compressions[i].value(), size=self.sizes[i].currentData())
                for i, record in enumerate(self.records) if self.table.item(i, 0).checkState() == QtCore.Qt.Checked]


class ExportTextures(W.QWidget):
    changed = QtCore.Signal()
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.groups, self.catalog = {}, []
        self.project, self.loaded_url = None, None
        self.catalog_loaded = False
        self.reload_status = 'Not loaded yet'
        self.waiting_for_project = False
        self.pending = None
        self.acknowledged = False
        self.problem = MISSING
        self._loading = False
        layout = W.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        selector = W.QHBoxLayout()
        selector.addWidget(W.QLabel('Export template'))
        self.template = W.QComboBox()
        self.template.addItem('Loading export templates…', None)
        self.template.setFixedHeight(32)
        self.template.setMinimumWidth(240)
        selector.addWidget(self.template, 1)
        self.alert = warning_icon(MISSING)
        selector.addWidget(self.alert)
        self.refresh = W.QPushButton('Refresh')
        self.refresh.setFixedHeight(32)
        self.refresh.clicked.connect(lambda: self.reload(force=True))
        selector.addWidget(self.refresh)
        layout.addLayout(selector)
        self.notice = W.QLabel()
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        self.reference_toggle = W.QPushButton('TM2020 textures reference table')
        self.reference_toggle.setCheckable(True)
        self.reference_toggle.setCursor(QtCore.Qt.PointingHandCursor)
        self.reference_toggle.setStyleSheet('QPushButton { border: none; background: transparent; text-decoration: underline; color: #a9d7f5; text-align: left; padding: 0; } QPushButton:hover { color: white; }')
        layout.addWidget(self.reference_toggle, 0, QtCore.Qt.AlignLeft)
        self.reference = W.QLabel(REFERENCE)
        self.reference.setTextFormat(QtCore.Qt.RichText)
        self.reference.hide()
        self.reference_toggle.toggled.connect(self.reference.setVisible)
        layout.addWidget(self.reference)
        self.scroll = W.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(W.QFrame.NoFrame)
        layout.addWidget(self.scroll, 1)
        self.template.activated.connect(lambda: self.load_outputs())
        self.tab_index = window.tabs.indexOf(window.textures_page)
        window.tabs.setTabText(self.tab_index, '1 TEXTURES')
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.reload)
        self.timer.start()
        self.update_status()

    def confirm_override(self):
        if self.acknowledged:
            return True
        answer = W.QMessageBox.warning(self, 'Change texture output settings?',
            'Changing texture suffixes or DDS compression can prevent Trackmania from recognizing textures or make them render incorrectly. Only change these settings if you know the required format. See the TM2020 reference table.',
            W.QMessageBox.Ok | W.QMessageBox.Cancel, W.QMessageBox.Cancel)
        if answer == W.QMessageBox.Ok:
            self.acknowledged = True
            return True
        return False

    def reload(self, force=False):
        if self._loading or self.window.runner is not None or self.window.saved is not None:
            self.reload_status = 'Paused: loading, export or preview active'
            return
        try:
            # Listing library templates does not need an editable project. Older
            # hosts can report not-ready while still exposing all preset files.
            if force or not self.catalog_loaded:
                self.reload_status = 'Reading template catalog'
                self.catalog = template_export.templates()
                self.populate_templates(self.template.currentData())
                self.catalog_loaded = True
            if not painter.ready():
                self.waiting_for_project = True
                self.reload_status = 'Waiting for Painter project readiness'
                self.problem = ('Templates are listed, but texture outputs are waiting for Painter. '
                    'Open a saved project and finish any active import, export or processing, then click Refresh.')
                self.update_status()
                return
            project = painter.project_path()
            names = tuple(compatibility.texture_set_name(s) for s in template_export.texture_sets())
            identity = (project, names)
            if not force and identity == self.project and not self.waiting_for_project:
                return
            self.waiting_for_project = False
            saved = self.settings()
            self.project = identity
            desired = self.template.currentData()
            state = self.pending or saved
            if state.get('project') == project:
                desired = state.get('template') or desired
            self.populate_templates(desired)
            self.reload_status = 'Reading selected template outputs'
            self.load_outputs(state)
            self.reload_status = self.problem or 'Template and texture outputs loaded'
        except Exception as exc:
            self.problem = 'Cannot read project/templates: ' + str(exc)
            self.reload_status = self.problem
            self.clear_groups()
            self.update_status()

    def populate_templates(self, desired=None):
        blocker = QtCore.QSignalBlocker(self.template)
        self.template.clear()
        self.template.addItem('Choose an export template…' if self.catalog else 'No library export templates found', None)
        counts = {p['name']: sum(q['name'] == p['name'] for q in self.catalog) for p in self.catalog}
        for descriptor in self.catalog:
            label = descriptor['name'] + (' · ' + descriptor['url'] if counts[descriptor['name']] > 1 else '')
            self.template.addItem(label, descriptor['url'])
        if not desired:
            matches = [p for p in self.catalog if p['name'].casefold() == 'tm2020']
            if len(matches) == 1:
                desired = matches[0]['url']
        self.template.setCurrentIndex(max(0, self.template.findData(desired)))
        del blocker

    def clear_groups(self):
        self.groups = {}
        content = W.QWidget()
        self.rows_layout = W.QVBoxLayout(content)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(0)
        self.scroll.setWidget(content)

    def load_outputs(self, state=None):
        self._loading = True
        try:
            if state is None:
                state = self.settings()
            self.clear_groups()
            if not painter.ready():
                self.problem = ('Texture outputs are waiting for Painter. Open a saved project and finish '
                    'any active import, export or processing, then click Refresh.')
                return
            if self.project is None:
                self.project = (painter.project_path(), tuple(
                    compatibility.texture_set_name(s) for s in template_export.texture_sets()))
            descriptor = next((p for p in self.catalog if p['url'] == self.template.currentData()), None)
            self.loaded_url = self.template.currentData()
            if descriptor is None:
                self.problem = MISSING
                return
            records = template_export.discover(descriptor, Path(self.window.fields['output'].text() or '.').resolve())
            self.problem = ''
            for name, outputs in records.items():
                section = Section(name, outputs, self)
                if not self.groups:
                    section.setStyleSheet('QWidget#textureSetCard { border-top: 1px solid #555b60; }')
                    section.layout().setContentsMargins(1, 1, 1, 0)
                self.groups[name] = section
                self.rows_layout.addWidget(section)
                section.changed.connect(self.update_status)
                if state.get('project') == self.project[0] and state.get('template') == descriptor['url']:
                    section.restore(state.get('sets', {}).get(name, []))
            self.rows_layout.addStretch()
            self.pending = None
        except Exception as exc:
            self.clear_groups()
            self.problem = 'Cannot read the selected template: ' + str(exc) + '. Choose a template compatible with this Painter version, then Refresh.'
        finally:
            self._loading = False
            self.update_status()

    def update_status(self, *args):
        modified, warnings = False, []
        for section in self.groups.values():
            for suffix, compression in zip(section.suffixes, section.compressions):
                modified |= suffix.value() != suffix.original or compression.value() != compression.original
                if suffix.alert.toolTip():
                    warnings.append(suffix.alert.toolTip())
        problem = self.problem or ('Some suffix/compression values differ from the TM2020 reference table. Review the yellow icons before exporting.' if warnings else '')
        self.alert.setToolTip(problem)
        self.alert.setVisible(bool(problem))
        tabs = self.window.tabs
        index = tabs.indexOf(self.window.textures_page)
        tabs.tabBar().modified_index = index if modified else -1
        tabs.setTabText(index, '1 TEXTURES' + ('*' if modified else ''))
        tabs.setTabIcon(index, self.style().standardIcon(W.QStyle.SP_MessageBoxWarning) if problem else QtGui.QIcon())
        tabs.setTabToolTip(index, problem or ('Texture defaults were manually changed. Use the restore icons to reset them.' if modified else ''))
        tabs.tabBar().updateGeometry()
        tabs.tabBar().update()
        self.notice.setText(problem or ('This Painter version exports all template outputs temporarily for each selected texture/resolution, then keeps only your selections. Only library templates can be listed on this older API. Template channels and normal convention are preserved.' if self.selected_template().get('kind') == 'legacy' else 'Template channels and normal convention are preserved. Override suffixes and DDS compression only when necessary.'))
        self.changed.emit()

    def selected_template(self):
        return next((p for p in self.catalog if p['url'] == self.template.currentData()), {})

    def export_plan(self):
        if self.problem:
            raise ValueError(self.problem)
        if not self.selected_template():
            raise ValueError(MISSING)
        return {'template': self.selected_template()}

    def selections(self):
        return [item for section in self.groups.values() for item in section.selections()]

    def settings(self):
        return {'schema': 2, 'project': self.project[0] if self.project else None,
                'template': self.loaded_url, 'acknowledged': self.acknowledged,
                'sets': {name: section.state() for name, section in self.groups.items()}}

    def restore_settings(self, state):
        if isinstance(state, dict):
            self.pending = state
            self.acknowledged = bool(state.get('acknowledged'))
        self.reload(force=True)
