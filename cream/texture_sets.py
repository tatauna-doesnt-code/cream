"""Collapsible texture-set export controls, independent of the Painter API."""
from .qt import QtCore, QtWidgets as W

from . import core
from .controls import set_chevron, CenteredCheckDelegate

TEXTURE_SETS = ("Details", "Glass", "Skin", "Wheels")
LABELS = {"B": "Base color (_B)", "R": "Roughness / Metallic (_R)", "I": "Emissive (_I)",
          "N": "Normals (_N)", "CoatR": "Coat roughness (_CoatR)",
          "DirtMask": "Dirt mask (_DirtMask)", "AO": "Ambient occlusion (_AO)"}


def add_resolutions(combo, texture_set):
    for size in (1024, 2048, 4096):
        width, height = core.dimensions(texture_set, size)
        combo.addItem(f"{width} × {height}", size)


class SetCheckBox(W.QCheckBox):
    def nextCheckState(self):
        # Partial means some children are selected. One click always selects the rest.
        self.setCheckState(QtCore.Qt.Unchecked if self.checkState() == QtCore.Qt.Checked else QtCore.Qt.Checked)


class TextureSetSection(W.QWidget):
    changed = QtCore.Signal()

    def __init__(self, texture_set, parent=None):
        super().__init__(parent)
        self.setObjectName("textureSetCard")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.texture_set = texture_set
        self.suffixes = list(core.MAPS)
        layout = W.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = W.QWidget()
        header_layout = W.QHBoxLayout(header)
        header_layout.setContentsMargins(6, 10, 6, 10)
        self.export = SetCheckBox()
        self.export.setTristate(True)
        self.export.setAccessibleName("Export " + texture_set + " texture set")
        self.export.setToolTip("Select or clear every texture in this set. A partial check means only some are selected.")
        header_layout.addWidget(self.export)
        self.expand = W.QToolButton()
        self.expand.setText(texture_set)
        self.expand.setCheckable(True)
        self.expand.setAutoRaise(True)
        self.expand.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        set_chevron(self.expand)
        self.expand.setAccessibleName("Expand " + texture_set + " textures")
        font = self.expand.font()
        font.setBold(True)
        self.expand.setFont(font)
        self.expand.setSizePolicy(W.QSizePolicy.Expanding, W.QSizePolicy.Preferred)
        self.expand.setStyleSheet("text-align: left; padding: 4px;")
        header_layout.addWidget(self.expand, 1)
        self.summary = W.QLabel()
        header_layout.addWidget(self.summary)
        header_layout.addSpacing(12)
        header_layout.addWidget(W.QLabel("Resolution"))
        self.resolution = W.QComboBox()
        self.resolution.addItem("Mixed", None)
        self.resolution.model().item(0).setEnabled(False)
        add_resolutions(self.resolution, texture_set)
        self.resolution.setCurrentIndex(self.resolution.findData(2048))
        self.resolution.setMinimumWidth(132)
        self.resolution.setAccessibleName(texture_set + " resolution for all textures")
        self.resolution.setToolTip("Applies to every texture in this set, including unchecked textures. Mixed indicates individual overrides.")
        header_layout.addWidget(self.resolution)
        layout.addWidget(header)
        self.body = W.QWidget()
        body_layout = W.QVBoxLayout(self.body)
        body_layout.setContentsMargins(26, 2, 6, 8)
        self.table = W.QTableWidget(len(self.suffixes), 3)
        self.table.setHorizontalHeaderLabels(["Export", "Texture", "Resolution"])
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setItemDelegateForColumn(0, CenteredCheckDelegate(self.table))
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(W.QAbstractItemView.NoSelection)
        self.table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setSectionResizeMode(0, W.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, W.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, W.QHeaderView.ResizeToContents)
        self.sizes = []
        for index, suffix in enumerate(self.suffixes):
            item = W.QTableWidgetItem()
            item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.table.setItem(index, 0, item)
            label = W.QTableWidgetItem(LABELS[suffix])
            label.setToolTip("DDS: " + core.MAPS[suffix].replace("_UNORM", "") + " / " + core.DDS_FOURCC[core.MAPS[suffix]].decode())
            self.table.setItem(index, 1, label)
            combo = W.QComboBox()
            add_resolutions(combo, texture_set)
            combo.setCurrentIndex(combo.findData(2048))
            combo.setAccessibleName(texture_set + " " + suffix + " resolution")
            self.sizes.append(combo)
            self.table.setCellWidget(index, 2, combo)
            combo.currentIndexChanged.connect(self.child_changed)
        self.table.verticalHeader().setDefaultSectionSize(36)
        for combo in self.sizes:
            combo.setFixedHeight(32)
        self.resolution.setFixedHeight(32)
        self.expand.setFixedHeight(32)
        self.table.setFixedHeight(self.table.horizontalHeader().sizeHint().height()
                                  + sum(self.table.rowHeight(i) for i in range(self.table.rowCount()))
                                  + self.table.frameWidth() * 2 + 2)
        body_layout.addWidget(self.table)
        layout.addWidget(self.body)
        self.body.hide()
        self.expand.toggled.connect(self.set_expanded)
        self.export.stateChanged.connect(self.toggle_all)
        self.table.itemChanged.connect(self.child_changed)
        self.resolution.currentIndexChanged.connect(self.apply_resolution)
        self.sync_header()

    def set_expanded(self, expanded):
        self.body.setVisible(expanded)
        set_chevron(self.expand, expanded)
        self.expand.setAccessibleName(("Collapse " if expanded else "Expand ") + self.texture_set + " textures")

    def toggle_all(self, *args):
        checked = self.export.checkState() == QtCore.Qt.Checked
        blocker = QtCore.QSignalBlocker(self.table)
        for index in range(self.table.rowCount()):
            self.table.item(index, 0).setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
        del blocker
        self.child_changed()

    def apply_resolution(self, *args):
        size = self.resolution.currentData()
        if size is None:
            return
        for combo in self.sizes:
            blocker = QtCore.QSignalBlocker(combo)
            combo.setCurrentIndex(combo.findData(size))
            del blocker
        self.child_changed()

    def sync_header(self):
        count = sum(self.table.item(i, 0).checkState() == QtCore.Qt.Checked for i in range(self.table.rowCount()))
        blocker = QtCore.QSignalBlocker(self.export)
        self.export.setCheckState(QtCore.Qt.Unchecked if count == 0 else QtCore.Qt.Checked
                                  if count == self.table.rowCount() else QtCore.Qt.PartiallyChecked)
        del blocker
        self.summary.setText(f"{count} / {self.table.rowCount()} selected")
        sizes = {combo.currentData() for combo in self.sizes}
        blocker = QtCore.QSignalBlocker(self.resolution)
        self.resolution.setCurrentIndex(self.resolution.findData(next(iter(sizes))) if len(sizes) == 1 else 0)
        del blocker

    def child_changed(self, *args):
        self.sync_header()
        self.changed.emit()

    def selections(self):
        return [{"set": self.texture_set, "map": suffix, "size": self.sizes[i].currentData()}
                for i, suffix in enumerate(self.suffixes)
                if self.table.item(i, 0).checkState() == QtCore.Qt.Checked]

    def settings(self):
        return [{"checked": self.table.item(i, 0).checkState() == QtCore.Qt.Checked,
                 "size": self.sizes[i].currentData()} for i in range(self.table.rowCount())]

    def restore_settings(self, settings):
        blocker = QtCore.QSignalBlocker(self.table)
        for i, item in enumerate(settings[:self.table.rowCount()]):
            if not isinstance(item, dict):
                continue
            self.table.item(i, 0).setCheckState(QtCore.Qt.Checked if item.get("checked") else QtCore.Qt.Unchecked)
            combo = self.sizes[i]
            size_blocker = QtCore.QSignalBlocker(combo)
            index = combo.findData(item.get("size"))
            combo.setCurrentIndex(index if index >= 0 else combo.findData(2048))
            del size_blocker
        del blocker
        self.sync_header()


class TextureSets(W.QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(W.QFrame.NoFrame)
        self.setStyleSheet('QScrollArea { background: transparent; }')
        self.viewport().setAutoFillBackground(False)
        content = W.QWidget()
        content.setAutoFillBackground(False)
        layout = W.QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.groups = {}
        for name in TEXTURE_SETS:
            section = TextureSetSection(name)
            self.groups[name] = section
            layout.addWidget(section)
        layout.addStretch()
        self.setWidget(content)

    def selections(self):
        return [item for section in self.groups.values() for item in section.selections()]

    def settings(self):
        # Preserve the pre-accordion settings shape and ordering for existing users.
        return [item for section in self.groups.values() for item in section.settings()]

    def restore_settings(self, settings):
        if not isinstance(settings, list):
            return
        count = len(core.MAPS)
        for i, section in enumerate(self.groups.values()):
            section.restore_settings(settings[i * count:(i + 1) * count])
