"""In-product setup guide and feature FAQ."""
from PySide6 import QtCore, QtGui, QtWidgets as W
from pathlib import Path


FAQ = [
    ("How do I prepare the Painter project?", """
    <h3>1. Start with your finished base skin</h3><p>Open the project in Painter and keep a working skin ZIP as your base.
    Supported texture sets are <b>Details, Glass, Skin and Wheels</b>. Glass is exported if selected,
    but excluded from player name and color edits.</p>
    <h3>2. Prepare the player-name fills</h3><p>In the appropriate layer masks, add fill effects using a <b>Font</b> resource.
    Name each effect <code>PLAYER_NAME</code>. CREAM replaces the font's Text parameter in every matching effect.
    Choose your font, size, alignment and placement in Painter; CREAM keeps those settings.</p>
    <h3>3. Prepare the color layers</h3><p>Use fill layers named <code>PLAYER_COLOR1</code>,
    <code>PLAYER_COLOR2</code> and optionally <code>PLAYER_COLOR3</code>. Their Base Color must be a uniform color.
    Only Base Color changes. Use anchor points to reuse these colors elsewhere in the skin.</p>
    <h3>4. Verify a small export</h3><p>Load the spreadsheet in <b>1 Setup</b>, match the columns, select a player in
    <b>2 Skins</b> and choose maps in <b>3 Textures</b>. Use <b>Check configuration</b>, preview the player,
    then <b>Restore original</b>. Export a test skin and check it in Trackmania before running the full batch.</p>"""),
    ("What spreadsheet do I need?", "<p>Use CSV or XLSX with column headers in the first row. Match any column names when loading. Only the player name is required; colors 1–3, row ID, ZIP name and active flag are optional. Colors use <code>#RRGGBB</code>. Blank or unmapped colors keep the project originals. XLSX uses the Backers sheet, or the first sheet; formulas are rejected.</p>"),
    ("Can I edit a player's name without changing the spreadsheet?", "<p>Yes. Edit the input in the Player name column. Overrides are <b><i>bold italic</i></b>; the refresh icon resets the imported name. Names preserve case and are truncated to 20 characters. Trackmania styling codes are not accepted for the text printed on the car. Edits last for this session and survive CREAM reloads. Reloading the spreadsheet resets them.</p>"),
    ("Does the final ZIP filename support TM styling?", "<p>Yes. In <b>3 ZIP names</b>, enable <b>Use Trackmania text styling</b>. Select text and apply bold, italic, uppercase, shadow, width or color. Text colors require exactly <b>three hex digits</b>, such as <code>$F80</code>. You can also edit raw codes. The Montserrat preview approximates in-game rendering; italic is shown normally in the editor. Styling affects ZIP names only.</p>"),
    ("How can I use each player's chosen color in the ZIP filename?", "<p>Open <b>Text color…</b> in the styling helper and choose <b>Use skin primary color</b> or <b>Use skin secondary color</b>. These insert <code>{primary}</code> or <code>{secondary}</code>, resolved independently from spreadsheet colors 1 and 2 for each skin. Example: <code>{primary}Event - {name}$z</code>. Skin colors are rounded to Trackmania's three-digit palette. Blank colors use the original project color; differing originals across sets must be resolved before export.</p>"),
    ("How do filename patterns and duplicate names work?", "<p>Use <code>{name}</code> for the ZIP-name column or player fallback, <code>{player}</code> for the printed player name, <code>{id}</code> for row ID and <code>{row}</code> for spreadsheet row. Add a prefix such as <code>Event - {name}</code>. The .zip extension is automatic. Duplicate or existing names receive 2, 3…; existing ZIPs are preserved. An explicit ZIP-name column is independent of manual player-name edits.</p>"),
    ("Which textures and resolutions can I export?", "<p>Check a set to select every map, or expand it to select maps individually. Set resolution applies to all maps in the set; individual overrides are supported and show as Mixed. Sizes are 1024, 2048 or 4096; Wheels keeps a 1:4 ratio. Compression is automatic for Trackmania 2020. OpenGL normals are exported directly, without a later green-channel inversion.</p>"),
    ("What happens to textures in the base ZIP?", "<p>Selected maps replace their matching files. Unselected files are copied from the base ZIP, and missing unselected maps remain absent. The base ZIP should contain its files at the root. CREAM uses its bundled DDS converter and keeps only the final ZIPs and batch reports after successful cleanup.</p>"),
    ("Why are some controls locked during a preview?", "<p>A preview temporarily changes names and colors in your open project. Editing names, importing, resuming and exporting are locked to protect the original state. Hover a locked control for an explanation. Click <b>Restore original</b> beside Preview or in the banner to continue. Do not save the preview over your base project. After a crash, use <b>Logs → Restore original / recover project</b>.</p>"),
    ("Can I cancel or resume a batch?", "<p>Use <b>Cancel safely</b>. CREAM waits for the current operation, restores the original project and keeps completed ZIPs. To resume, load the same spreadsheet and settings, then choose <b>Resume a previous batch…</b> and a JSON report from <code>_CREAM_reports</code> inside the output folder. Successful rows whose ZIPs still exist are unchecked; review the remaining selection and export again. A report must match the project and export configuration.</p>"),
    ("Where do I put skins for Trackmania uploads?", "<p>Save or copy ZIPs directly into <code>Documents/Trackmania/Skins/Models/CarSport</code>. Uploads from subfolders can fail even when the skin previews correctly. Check your ZIP size against the game's upload limit.</p>"),
    ("How do updates and GitHub access work?", "<p>Click <b>Settings</b> and use <b>Check for updates</b>. If the repository is private, CREAM asks for a fine-grained GitHub token with <b>Contents: Read-only</b> access to the CREAM repository when needed. Windows protects the saved token for your user. Public releases require no token. Download the release, then follow the Apply/restart instruction. Active previews and batches must finish before applying updates.</p>"),
]


def add_help(window):
    scroll = W.QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(W.QFrame.NoFrame)
    content = W.QWidget()
    content.setObjectName("workspaceCard")
    content.setAttribute(QtCore.Qt.WA_StyledBackground, True)
    layout = W.QVBoxLayout(content)
    layout.setContentsMargins(18, 18, 18, 18)
    window.cream_logo = W.QLabel()
    font_path = Path(__file__).parent / 'fonts/righteous/Righteous-Regular.ttf'
    app = W.QApplication.instance()
    identifier = app.property('creamRighteousFontId')
    if identifier is None and font_path.is_file():
        identifier = QtGui.QFontDatabase.addApplicationFontFromData(QtCore.QByteArray(font_path.read_bytes()))
        app.setProperty('creamRighteousFontId', identifier)
    if identifier is not None and identifier >= 0:
        family = QtGui.QFontDatabase.applicationFontFamilies(identifier)[0]
        window.cream_logo.setText('cream')
        window.cream_logo.setFont(QtGui.QFont(family, 28))
        window.cream_logo.setStyleSheet('font-family: "Righteous"; font-size: 28pt; font-weight: normal;')
        window.cream_logo.setAccessibleName('CREAM logo')
    else:
        window.cream_logo.setText('CREAM')
        fallback = window.cream_logo.font()
        fallback.setPointSize(28)
        window.cream_logo.setFont(fallback)
    window.cream_logo.setAlignment(QtCore.Qt.AlignCenter)
    window.cream_logo.setContentsMargins(0, 8, 0, 16)
    layout.addWidget(window.cream_logo)
    title = W.QLabel("Getting started with CREAM")
    title.setStyleSheet("font-size: 18px; font-weight: 600;")
    layout.addWidget(title)
    intro = FAQ[0][1]
    intro = intro.replace('Load the spreadsheet in <b>1 Setup</b>, match the columns, select a player in\n    <b>2 Skins</b> and choose maps in <b>3 Textures</b>.', 'In <b>Settings</b>, choose your base ZIP and output folder. In <b>1 Skins</b>, use <b>Add skin</b> to enter a name and colors, or <b>Import CSV / XLSX</b> to append a spreadsheet. Choose maps in <b>2 Textures</b> and set filenames in <b>3 ZIP names</b>.')
    intro = '<p>CREAM creates personalized Trackmania 2020 skin ZIPs from your open Painter project. Start with one skin, then build a batch when you are ready.</p>' + intro
    intro = intro.replace('<code>', '<b><span style="color: #a9d7f5; font-family: Consolas;">').replace('</code>', '</span></b>')
    guide = W.QLabel(intro)
    guide.setWordWrap(True)
    guide.setTextFormat(QtCore.Qt.RichText)
    guide.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
    layout.addWidget(guide)
    faq_heading = W.QLabel('Frequently asked questions')
    faq_heading.setStyleSheet('font-size: 17px; font-weight: 600; padding-top: 16px;')
    layout.addWidget(faq_heading)
    entries = [('What does CREAM mean?', '<p><b>Color Replacement &amp; Export Automation Manager.</b> CREAM automates player names, skin colors, texture exports, DDS conversion and final ZIP packaging.</p>'),
        ('Can I enter data without a spreadsheet?', '<p>Yes. In <b>1 Skins</b>, click <b>Add skin</b>, enter a name and up to three colors, then Save. Use <b>Edit skin</b> to change a highlighted entry or <b>Remove</b> to delete it. Blank colors keep the project original. Manual lists are saved locally. Import CSV / XLSX appends spreadsheet rows without replacing the current list.</p>')]
    for question, answer in entries + FAQ[1:]:
        toggle = W.QToolButton()
        toggle.setText(question)
        toggle.setCheckable(True)
        toggle.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        toggle.setArrowType(QtCore.Qt.RightArrow)
        toggle.setSizePolicy(W.QSizePolicy.Expanding, W.QSizePolicy.Preferred)
        toggle.setStyleSheet("text-align: left; padding: 8px; background: #222426; border: 1px solid #494c50;")
        import re
        answer = re.sub(r"<code>(.*?)</code>", r'<b><span style="color: #a9d7f5; font-family: Consolas;">\1</span></b>', answer)
        body = W.QLabel(answer)
        body.setWordWrap(True)
        body.setTextFormat(QtCore.Qt.RichText)
        body.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        body.setStyleSheet("padding: 8px 16px; color: #eee;")
        body.hide()
        toggle.toggled.connect(body.setVisible)
        toggle.toggled.connect(lambda opened, t=toggle: t.setArrowType(QtCore.Qt.DownArrow if opened else QtCore.Qt.RightArrow))
        layout.addWidget(toggle)
        layout.addWidget(body)
    layout.addStretch()
    scroll.setWidget(content)
    window.help_page = scroll
    index = window.tabs.addTab(scroll, "Help")
    window.tabs.tabBar().setTabVisible(index, False)
    window.help_link = W.QToolButton()
    window.help_link.setText("Help")
    window.help_link.setIcon(window.style().standardIcon(W.QStyle.SP_MessageBoxQuestion))
    window.help_link.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
    window.help_link.setCheckable(True)
    window.help_link.setFixedHeight(38)
    window.help_link.setStyleSheet("QToolButton { padding: 4px 16px; background: #222426; border: 1px solid #494c50; border-bottom: none; border-radius: 0; } QToolButton:checked { background: #292b2e; border-top: 2px solid #6ca8cf; }")
    window.help_link.clicked.connect(lambda: window.tabs.setCurrentWidget(scroll))
    window.tabs.currentChanged.connect(lambda current: window.help_link.setChecked(current == index))
    corner = W.QWidget()
    links = W.QHBoxLayout(corner)
    links.setContentsMargins(0, 0, 0, 0)
    links.setSpacing(0)
    window.settings_link = W.QToolButton()
    window.settings_link.setText('Settings')
    window.settings_link.setCheckable(True)
    window.settings_link.setFixedHeight(38)
    window.settings_link.setStyleSheet(window.help_link.styleSheet())
    settings_index = window.tabs.indexOf(window.settings_page)
    window.tabs.tabBar().setTabVisible(settings_index, False)
    window.settings_link.clicked.connect(lambda: window.tabs.setCurrentWidget(window.settings_page))
    window.tabs.currentChanged.connect(lambda current: window.settings_link.setChecked(current == settings_index))
    links.addWidget(window.settings_link)
    links.addWidget(window.help_link)
    window.tabs.setCornerWidget(corner, QtCore.Qt.TopRightCorner)
