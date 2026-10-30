"""Task-focused layout for CREAM; export behavior lives in ui.Window."""
from PySide6 import QtCore, QtWidgets as W

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
        QTabBar::tab { padding: 10px 18px; }
        QLineEdit { min-height: 26px; }
        QToolButton { min-height: 24px; }
        QWidget#workspaceCard { background: #292b2e; border: 1px solid #494c50; border-radius: 5px; }
        QTabWidget::pane { border: none; }
        QTableWidget { background: #222426; alternate-background-color: #2b2d30;
            color: #eeeeee; border: 1px solid #494c50; selection-background-color: #365568; selection-color: white; }
        QTableWidget::item { color: #eeeeee; }
        QTableWidget::item:alternate { background: #2b2d30; }
        QTableWidget::item:selected { background: #365568; color: white; }
        QWidget#previewBanner { background: #263c49; border: 1px solid #537184; border-radius: 4px; }
        QFrame#actionPanel { background: #242629; border: 1px solid #494c50; border-radius: 4px; }
        QWidget#textureSetCard { background: #222426; border: 1px solid #494c50; border-radius: 4px; }
    """)
    header = W.QHBoxLayout()
    title = note("CREAM")
    title.setStyleSheet("font-size: 23px; font-weight: 600;")
    title.setToolTip("Color Replacement & Export Automation Manager")
    header.addWidget(title)
    subtitle = note("Trackmania skin exporter")
    subtitle.setWordWrap(False)
    header.addWidget(subtitle)
    header.addStretch()
    w.updates_link = button("Updates · " + VERSION, lambda: w.updates_dialog.show())
    header.addWidget(w.updates_link)
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
    layout.addWidget(w.tabs, 1)
    w.fields = {}
    w.setup_page, setup = page(w, "1  Setup", "Choose your source files",
        "Start with an open Painter project. Each spreadsheet row becomes one personalized skin ZIP.")
    files = W.QFormLayout()
    files.setVerticalSpacing(12)
    files.setFormAlignment(QtCore.Qt.AlignTop)
    files.setFieldGrowthPolicy(W.QFormLayout.AllNonFixedFieldsGrow)
    setup.addLayout(files)
    w.field(files, "sheet", "Spreadsheet", "", "Spreadsheets (*.csv *.xlsx)")
    files.addRow("", note("CSV or XLSX with player names and optional hex colors. You’ll match the columns when loading."))
    w.load_button = button("Load spreadsheet…", w.load_sheet, True)
    w.load_button.setMaximumWidth(220)
    files.addRow("", w.load_button)
    w.field(files, "base", "Base skin ZIP", "", "Skin (*.zip)")
    files.addRow("", note("A working skin to copy. Only the textures you select will be replaced."))
    w.field(files, "output", "Save ZIPs to", default_output, None)
    files.addRow("", note("For in-game uploads, use the CarSport folder directly; subfolders may fail."))
    project_help = W.QToolButton()
    project_help.setText("How to prepare the Painter project")
    project_help.setCheckable(True)
    project_help.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
    project_help.setArrowType(QtCore.Qt.RightArrow)
    setup.addWidget(project_help, 0, QtCore.Qt.AlignLeft)
    requirements = note("Use PLAYER_NAME for the font fill effects in your masks. Name your color fill layers "
        "PLAYER_COLOR1, PLAYER_COLOR2 and PLAYER_COLOR3 as needed. CREAM changes only their Base Color; "
        "blank spreadsheet colors keep the original. Glass is excluded from name and color changes. "
        "Use Check configuration to verify the project before exporting.")
    setup.addWidget(requirements)
    requirements.hide()
    project_help.toggled.connect(requirements.setVisible)
    project_help.toggled.connect(lambda expanded: project_help.setArrowType(QtCore.Qt.DownArrow if expanded else QtCore.Qt.RightArrow))
    setup.addStretch()
    w.setup_hint = note("Next: load your spreadsheet and match its columns.")
    setup.addWidget(w.setup_hint)

    w.skins_page, skins = page(w, "2  Skins", "Choose the skins to export",
        "Check rows to include in the batch. Click a row to preview that skin in Painter.")
    tools = W.QHBoxLayout()
    tools.addWidget(button("Select all", lambda: w.check_rows(True)))
    tools.addWidget(button("Clear selection", lambda: w.check_rows(False)))
    w.skin_count = note("No skins loaded")
    tools.addWidget(w.skin_count)
    tools.addStretch()
    w.resume_button = button("Resume a previous batch…", w.resume)
    tools.addWidget(w.resume_button)
    resume_info = W.QToolButton()
    resume_info.setIcon(w.style().standardIcon(W.QStyle.SP_MessageBoxInformation))
    resume_info.setAccessibleName("How resuming a batch works")
    resume_info.setToolTip("Choose a JSON report from the output folder’s _KR7_reports directory. CREAM checks that the project and export settings match, then unchecks successfully exported rows whose ZIPs still exist. Failed or unfinished rows stay checked. Review the selection and click Export to continue.")
    resume_info.clicked.connect(lambda: W.QToolTip.showText(resume_info.mapToGlobal(resume_info.rect().bottomLeft()), resume_info.toolTip(), resume_info))
    tools.addWidget(resume_info)
    skins.addLayout(tools)
    w.empty_state = W.QWidget()
    empty = W.QVBoxLayout(w.empty_state)
    empty.addStretch()
    message = note("No skins yet\nLoad a spreadsheet in Setup to see your players and colors here.")
    message.setAlignment(QtCore.Qt.AlignCenter)
    empty.addWidget(message)
    empty.addWidget(button("Go to Setup", lambda: w.tabs.setCurrentWidget(w.setup_page)))
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
    w.backers.verticalHeader().setDefaultSectionSize(34)
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

    w.textures_page, textures = page(w, "3  Textures", "Choose which textures to replace",
        "Check a set to include all its textures, or expand it to choose individual maps. Everything else stays as it is in the base ZIP.")
    w.texture_sets = TextureSets()
    textures.addWidget(w.texture_sets, 1)
    textures.addWidget(note("Set resolution applies to every map in that set. Expand a set to override individual resolutions."))
    technical = note("Trackmania 2020 · DDS compression is automatic · Wheels keep a 1:4 aspect ratio")
    technical.setToolTip("DDS without mipmaps. OpenGL normals exported directly. Glass receives no player-name or color changes. Missing, unselected files remain absent.")
    textures.addWidget(technical)

    w.naming_page, naming = page(w, "4  ZIP names", "Name the exported files",
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
    w.status = note("Start in Setup: choose a spreadsheet and base skin ZIP.")
    w.status.setMaximumHeight(48)
    actions.addWidget(w.status, 1)
    w.validate_button = button("Check configuration", w.validate)
    actions.addWidget(w.validate_button)
    w.export_button = button("Export skins", w.start, True)
    w.export_button.setToolTip("Checks configuration, exports the selected skins, then restores the original project.")
    actions.addWidget(w.export_button)
    action_layout.addLayout(actions)
    layout.addWidget(action_panel)

    w.updates_dialog = W.QDialog(w)
    w.updates_dialog.setWindowTitle("CREAM — Updates")
    w.updates_dialog.setMinimumWidth(500)
    w.updates_layout = W.QVBoxLayout(w.updates_dialog)
    w.updates_layout.addWidget(note("CREAM " + VERSION + "\nUpdates are checked automatically when CREAM opens."))
    from .preview_help import PreviewHelp
    w.preview_help = PreviewHelp(w)
    return layout
