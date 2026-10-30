"""Task-focused layout for CREAM; export behavior lives in ui.Window."""
from PySide6 import QtCore, QtGui, QtWidgets as W

from . import core
from .name_cell import PlayerNameDelegate
from .name_style import NameStyleHelper
from .texture_sets import TextureSets
from .version import VERSION


def note(text):
    label = W.QLabel(text)
    label.setWordWrap(True)
    label.setTextFormat(QtCore.Qt.PlainText)
    return label


def button(text, callback, primary=False):
    control = W.QPushButton(text)
    control.setAutoDefault(False)
    control.setMinimumHeight(30)
    if primary:
        control.setObjectName("primaryAction")
    control.clicked.connect(callback)
    return control


def page(window, tab, title, description):
    content = W.QWidget()
    content.setObjectName("workspaceCard")
    content.setAttribute(QtCore.Qt.WA_StyledBackground, True)
    layout = W.QVBoxLayout(content)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)
    heading = note(title)
    heading.setStyleSheet("font-size: 17px; font-weight: 600;")
    layout.addWidget(heading)
    layout.addWidget(note(description))
    window.tabs.addTab(content, tab)
    return content, layout


def build(window, default_output):
    w = window
    layout = W.QVBoxLayout(w)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(12)
    w.setStyleSheet("""
        QPushButton#primaryAction { background: #326b96; color: white;
            border: 1px solid #568ab1; border-radius: 3px; padding: 6px 18px; font-weight: 600; }
        QPushButton#primaryAction:hover { background: #3c7bab; }
        QPushButton#primaryAction:disabled { background: #41464b; color: #a0a4a8; border-color: #555; }
        QPushButton#primaryAction:focus { border: 2px solid #b8ddfa; }
        QTabBar::tab { padding: 10px 18px; background: #222426; border: 1px solid #494c50; border-bottom: none; }
        QTabBar::tab:selected { background: #292b2e; border-top: 2px solid #6ca8cf; }
        QLineEdit { min-height: 0; background: #202225; color: #eee; border: 1px solid #55595d; border-radius: 3px; padding: 3px 6px; }
        QWidget#pathRow { background: transparent; border: none; }
        QToolButton { min-height: 24px; }
        QWidget#workspaceCard { background: #292b2e; border: 1px solid #494c50; border-radius: 5px; }
        QTabWidget::pane { border: none; margin-top: -1px; }
        QTableWidget { background: #222426; alternate-background-color: #2b2d30;
            color: #eeeeee; border: 1px solid #494c50; selection-background-color: #365568; selection-color: white; }
        QTableWidget::item { color: #eeeeee; }
        QTableWidget::item { border-right: 1px solid #44474a; }
        QTableWidget::item:alternate { background: #2b2d30; }
        QTableWidget::item:selected { background: #365568; color: white; }
        QWidget#previewBanner { background: #263c49; border: 1px solid #537184; border-radius: 4px; }
        QFrame#actionPanel { background: #242629; border: 1px solid #494c50; border-radius: 4px; }
        QWidget#textureSetCard { background: #222426; border: 1px solid #494c50; border-radius: 4px; }
    """)
    header = W.QHBoxLayout()
    title = note("CREAM")
    title.setFont(QtGui.QFont("Georgia", 22, QtGui.QFont.Bold))
    title.setStyleSheet("font-family: Georgia; font-size: 27px; font-weight: bold;")
    title.setToolTip("Color Replacement & Export Automation Manager")
    header.addWidget(title)
    subtitle = note("Trackmania skin exporter")
    subtitle.setWordWrap(False)
    header.addWidget(subtitle)
    header.addStretch()
    layout.addLayout(header)

    # Preview recovery remains reachable from every page.
    w.preview_banner = W.QWidget()
    w.preview_banner.setObjectName("previewBanner")
    w.preview_banner.setAttribute(QtCore.Qt.WA_StyledBackground, True)
    banner = W.QHBoxLayout(w.preview_banner)
    banner.setContentsMargins(12, 8, 12, 8)
    banner.addWidget(note("Preview active in Painter. Restore the original before exporting or editing names."), 1)
    w.restore_button = button("Restore original", w.restore)
    banner.addWidget(w.restore_button)
    layout.addWidget(w.preview_banner)
    w.preview_banner.hide()

    w.tabs = W.QTabWidget()
    w.tabs.setDocumentMode(True)
    w.tabs.tabBar().setDrawBase(False)
    layout.addWidget(w.tabs, 1)
    w.fields = {}
    # Import path is internal state; import itself is available in the skin list.
    w.fields['sheet'] = W.QLineEdit()
    w.skins_page, skins = page(w, "1  Skins", "Choose the skins to export",
        "Check rows to include in the batch. Click a row to preview that skin in Painter.")
    tools = W.QHBoxLayout()
    w.add_button = button("Add skin…", w.add_skin, True)
    tools.addWidget(w.add_button)
    w.edit_button = button("Edit skin…", w.edit_skin)
    tools.addWidget(w.edit_button)
    w.remove_button = button("Remove", w.remove_skin)
    tools.addWidget(w.remove_button)
    tools.addWidget(button("Select all", lambda: w.check_rows(True)))
    tools.addWidget(button("Clear selection", lambda: w.check_rows(False)))
    w.skin_count = note("No skins loaded")
    tools.addWidget(w.skin_count)
    tools.addStretch()
    w.resume_button = button("Resume a previous batch…", w.resume)
    tools.addWidget(w.resume_button)
    resume_info = W.QLabel()
    resume_info.setPixmap(w.style().standardIcon(W.QStyle.SP_MessageBoxInformation).pixmap(16, 16))
    resume_info.setFixedSize(20, 24)
    resume_info.setAlignment(QtCore.Qt.AlignCenter)
    resume_info.setAccessibleName("How resuming a batch works")
    resume_info.setToolTip("Choose a JSON report from the output folder’s _CREAM_reports directory. CREAM checks that the project and export settings match, then unchecks successfully exported rows whose ZIPs still exist. Failed or unfinished rows stay checked. Review the selection and click Export to continue.")
    tools.addWidget(resume_info)
    w.load_button = button("Import CSV / XLSX…", w.import_sheet)
    tools.addWidget(w.load_button)
    skins.addLayout(tools)
    w.empty_state = W.QWidget()
    empty = W.QVBoxLayout(w.empty_state)
    empty.addStretch()
    message = note("Create your first skin\nAdd a player name and colors, or import a spreadsheet for a larger batch.")
    message.setAlignment(QtCore.Qt.AlignCenter)
    empty.addWidget(message)
    empty.addWidget(button("Add your first skin…", w.add_skin, True))
    empty.addStretch()
    skins.addWidget(w.empty_state, 1)
    w.backers = W.QTableWidget(0, 8)
    w.backers.setHorizontalHeaderLabels(["Export", "Row / ID", "Player name", "Color 1", "Color 2", "Color 3", "ZIP filename", "Status"])
    w.backers.verticalHeader().hide()
    w.backers.setShowGrid(False)
    w.backers.setAlternatingRowColors(True)
    w.backers.setSelectionBehavior(W.QAbstractItemView.SelectRows)
    w.backers.setSelectionMode(W.QAbstractItemView.SingleSelection)
    w.backers.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
    w.name_delegate = PlayerNameDelegate(w.backers)
    w.backers.setItemDelegateForColumn(2, w.name_delegate)
    w.backers.horizontalHeaderItem(2).setToolTip("Edit a name directly. Bold italic means changed; the refresh icon resets it.")
    w.backers.selectionModel().selectionChanged.connect(w.sync_name_selection)
    w.backers.horizontalHeader().setSectionResizeMode(W.QHeaderView.ResizeToContents)
    w.backers.horizontalHeader().setSectionResizeMode(6, W.QHeaderView.Stretch)
    w.backers.horizontalHeader().setStretchLastSection(False)
    w.backers.verticalHeader().setDefaultSectionSize(40)
    skins.addWidget(w.backers, 1)
    skins.addWidget(note("Edit names directly (20 characters max). Bold italic = edited; refresh = reset. Blank colors keep the project original."))
    preview = W.QHBoxLayout()
    w.preview_button = button("Preview highlighted skin", w.preview)
    preview.addWidget(w.preview_button)
    w.inline_restore = button("Restore original", w.restore)
    preview.addWidget(w.inline_restore)
    preview.addStretch()
    preview.addWidget(button("Choose textures →", lambda: w.tabs.setCurrentWidget(w.textures_page)))
    skins.addLayout(preview)

    w.textures_page, textures = page(w, "2  Textures", "Choose which textures to replace",
        "Check a set to include all its textures, or expand it to choose individual maps. Everything else stays as it is in the base ZIP.")
    w.texture_sets = TextureSets()
    textures.addWidget(w.texture_sets, 1)
    textures.addWidget(note("Set resolution applies to every map in that set. Expand a set to override individual resolutions."))
    technical = note("Trackmania 2020 · DDS compression is automatic · Wheels keep a 1:4 aspect ratio")
    technical.setToolTip("DDS without mipmaps. OpenGL normals exported directly. Glass receives no player-name or color changes. Missing, unselected files remain absent.")
    textures.addWidget(technical)

    w.naming_page, naming = page(w, "3  ZIP names", "Name the exported files",
        "Optional. By default, each ZIP uses its player name. This changes filenames only, not the names printed on the car.")
    w.fields["name_pattern"] = W.QLineEdit(core.DEFAULT_NAME_PATTERN)
    w.fields["name_pattern"].setMaxLength(200)
    w.fields["name_pattern"].setPlaceholderText("Event - {name}")
    form = W.QFormLayout()
    form.addRow("Filename pattern", w.fields["name_pattern"])
    naming.addLayout(form)
    tokens = W.QHBoxLayout()
    tokens.addWidget(note("Insert:"))
    for token, label in [("name", "ZIP name"), ("player", "Player"), ("id", "ID"), ("row", "Row")]:
        control = button(label, lambda checked=False, t=token: w.fields["name_pattern"].insert("{" + t + "}"))
        control.setToolTip("Insert {" + token + "} at the cursor")
        tokens.addWidget(control)
    tokens.addStretch()
    naming.addLayout(tokens)
    naming.addWidget(note("{name} uses your ZIP-name column, or the player name if none is mapped. Add a prefix such as Event - {name}. Duplicate names receive 2, 3…"))
    naming.addWidget(note("Filename preview · highlighted skin (or sample before loading)"))
    w.name_preview = note("")
    w.name_preview.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
    naming.addWidget(w.name_preview)
    w.styling_enabled = W.QCheckBox("Use Trackmania text styling")
    w.styling_enabled.setToolTip("Optional in-game colors and text styles. Turning this off hides the editor without removing codes.")
    naming.addWidget(w.styling_enabled)
    w.name_style = NameStyleHelper()
    w.name_style.hide()
    w.name_style.pattern_changed.connect(w.fields["name_pattern"].setText)
    w.name_style.color_requested.connect(w.refresh_name_colors)
    w.styling_enabled.toggled.connect(w.toggle_name_helper)
    naming.addWidget(w.name_style)
    naming.addStretch()

    w.log_page, logs = page(w, "Logs", "Logs and troubleshooting", "Validation details, warnings and export results appear here.")
    w.log = W.QPlainTextEdit()
    w.log.setReadOnly(True)
    logs.addWidget(w.log, 1)
    logs.addWidget(button("Restore original / recover project", w.restore))

    action_panel = W.QFrame()
    action_panel.setObjectName("actionPanel")
    action_layout = W.QVBoxLayout(action_panel)
    action_layout.setContentsMargins(12, 10, 12, 10)
    w.summary = note("")
    action_layout.addWidget(w.summary)
    actions = W.QHBoxLayout()
    w.status = note("Add a skin to get started. Choose your base ZIP and output folder in Settings.")
    w.status.setMaximumHeight(48)
    actions.addWidget(w.status, 1)
    w.validate_button = button("Check configuration", w.validate)
    actions.addWidget(w.validate_button)
    w.export_button = button("Export skins", w.start, True)
    w.export_button.setToolTip("Checks configuration, exports the selected skins, then restores the original project.")
    actions.addWidget(w.export_button)
    action_layout.addLayout(actions)
    layout.addWidget(action_panel)

    w.settings_page, settings = page(w, "Settings", "Files and updates",
        "Choose the base skin and where exported ZIPs should be saved.")
    w.setup_page = w.settings_page
    files = W.QFormLayout()
    files.setVerticalSpacing(12)
    settings.addLayout(files)
    w.field(files, 'base', 'Base skin ZIP', '', 'Skin (*.zip)')
    files.addRow('', note('A working skin ZIP. Only selected textures are replaced.'))
    w.field(files, 'output', 'Save ZIPs to', default_output, None)
    files.addRow('', note('Use CarSport directly for in-game uploads; subfolders can fail.'))
    w.setup_hint = note('Add skins, choose textures and export. Settings apply to every selected skin.')
    settings.addWidget(w.setup_hint)
    w.updates_layout = W.QVBoxLayout()
    settings.addLayout(w.updates_layout)
    heading = note('Updates')
    heading.setStyleSheet('font-size: 17px; font-weight: 600;')
    w.updates_layout.addWidget(heading)
    w.updates_layout.addWidget(note('Installed: CREAM beta ' + VERSION + '\nCheck, download, then apply the update. CREAM explains when Painter must restart.'))
    settings.addStretch()
    from .help_page import add_help
    add_help(w)
    from .preview_help import PreviewHelp
    w.preview_help = PreviewHelp(w)
    return layout
