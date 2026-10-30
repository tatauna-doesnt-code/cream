from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import traceback

from PySide6 import QtCore, QtGui, QtWidgets as W
import substance_painter as sp
import substance_painter.ui

from . import core, painter, updater, bootstrap
from .columns import ColumnDialog
from .version import VERSION

DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "KR7BatchExporter"
DEFAULT_OUTPUT = str(Path(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.DocumentsLocation))
                     / "Trackmania" / "Skins" / "Models" / "CarSport")


class Progress(W.QDialog):
    def __init__(self, parent, cancel):
        super().__init__(parent)
        self.cancel = cancel
        self.setWindowTitle("CREAM — Batch in progress")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setMinimumWidth(530)
        layout = W.QVBoxLayout(self)
        self.label = W.QLabel("Preparing…")
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.bar = W.QProgressBar()
        layout.addWidget(self.bar)
        self.button = W.QPushButton("Cancel safely")
        self.button.clicked.connect(self.request_cancel)
        layout.addWidget(self.button)
        layout.addWidget(W.QLabel("If Painter is busy, cancellation will wait for the current operation."))

    def request_cancel(self):
        self.cancel.set()
        self.button.setEnabled(False)
        self.label.setText("Cancellation requested. Waiting for a safe stopping point and restoring the project…")

    def reject(self):
        self.request_cancel()

    def closeEvent(self, event):
        self.request_cancel()
        event.ignore()


class Window(W.QDialog):
    def __init__(self, auto_update=True, reload_callback=None):
        super().__init__(sp.ui.get_main_window())
        self.setWindowTitle("CREAM — " + VERSION)
        self.resize(1040, 820)
        self.rows = []
        self.column_profile = None
        self.reload_callback = reload_callback
        self.saved = None
        self.runner = None
        self.future = None
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="KR7-files")
        self.cancel = threading.Event()
        self.progress = None
        self.report = None
        self.report_path = None
        self._stepping = False
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.tick)
        DATA.mkdir(parents=True, exist_ok=True)
        layout = W.QVBoxLayout(self)
        title = W.QLabel("CREAM • Color Replacement & Export Automation Manager")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin: 4px 0 8px 0;")
        layout.addWidget(title)
        self.fields = {}
        form = W.QFormLayout()
        layout.addLayout(form)
        self.field(form, "sheet", "CSV / XLSX spreadsheet", "", "Spreadsheets (*.csv *.xlsx)")
        self.field(form, "base", "Base ZIP", "", "Skin (*.zip)")
        self.field(form, "output", "ZIP output folder", DEFAULT_OUTPUT, None)
        self.field(form, "converter", "DDS converter", str(Path(__file__).parent / "bin" / "texconv.exe"), "Converter (texconv.exe)")
        self.fields["name_pattern"] = W.QLineEdit(core.DEFAULT_NAME_PATTERN)
        self.fields["name_pattern"].setPlaceholderText("Event - {name}")
        self.fields["name_pattern"].setMaxLength(200)
        self.fields["name_pattern"].setToolTip(
            "{name}: ZIP-name column (or player name). {player}: printed name. {id}: row ID. {row}: spreadsheet row. ZIP extension is added automatically.")
        form.addRow("ZIP name pattern", self.fields["name_pattern"])
        self.name_preview = W.QLabel()
        self.name_preview.setWordWrap(True)
        form.addRow("Filename preview", self.name_preview)
        self.tabs = W.QTabWidget()
        layout.addWidget(self.tabs, 1)
        page = W.QWidget()
        box = W.QVBoxLayout(page)
        toolbar = W.QHBoxLayout()
        box.addLayout(toolbar)
        for label, callback in [("Load spreadsheet", self.load_sheet), ("Select all", lambda: self.check_rows(True)),
                                ("Deselect all", lambda: self.check_rows(False)), ("Resume from report…", self.resume)]:
            button = W.QPushButton(label)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
        self.backers = W.QTableWidget(0, 8)
        self.backers.setHorizontalHeaderLabels(["Export", "Row / ID", "Player name", "Color 1", "Color 2", "Color 3", "Expected ZIP", "Status"])
        self.backers.setSelectionBehavior(W.QAbstractItemView.SelectRows)
        self.backers.setSelectionMode(W.QAbstractItemView.SingleSelection)
        self.backers.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        self.backers.horizontalHeader().setSectionResizeMode(W.QHeaderView.ResizeToContents)
        self.backers.horizontalHeader().setStretchLastSection(True)
        box.addWidget(self.backers)
        box.addWidget(W.QLabel("Names: up to 20 characters. Blank colors: project original. Duplicate ZIP names receive 2, 3…"))
        upload_note = W.QLabel("To upload in-game, place ZIPs directly in CarSport; uploads may fail from subfolders.")
        upload_note.setWordWrap(True)
        box.addWidget(upload_note)
        self.tabs.addTab(page, "Backers")
        page = W.QWidget()
        box = W.QVBoxLayout(page)
        box.addWidget(W.QLabel("TM2020 preset • DDS without mipmaps • OpenGL normals at export • Glass has no name/color changes"))
        self.maps = W.QTableWidget(0, 5)
        self.maps.setHorizontalHeaderLabels(["Exportar", "Texture set", "Texture", "Output resolution", "DDS"])
        self.maps.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        self.maps.horizontalHeader().setSectionResizeMode(W.QHeaderView.Stretch)
        for texture_set in ("Details", "Glass", "Skin", "Wheels"):
            for suffix, compression in core.MAPS.items():
                index = self.maps.rowCount()
                self.maps.insertRow(index)
                self.maps.setItem(index, 0, self.check_item(False))
                self.maps.setItem(index, 1, W.QTableWidgetItem(texture_set))
                self.maps.setItem(index, 2, W.QTableWidgetItem(suffix))
                sizes = W.QComboBox()
                for size in (1024, 2048, 4096):
                    width, height = core.dimensions(texture_set, size)
                    sizes.addItem(f"{width} × {height}", size)
                sizes.setCurrentIndex(1)
                self.maps.setCellWidget(index, 3, sizes)
                self.maps.setItem(index, 4, W.QTableWidgetItem(compression.replace("_UNORM", "")))
        box.addWidget(self.maps)
        box.addWidget(W.QLabel("Unselected files are preserved from the base ZIP. Missing files remain absent."))
        self.tabs.addTab(page, "Textures")
        self.log = W.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.tabs.addTab(self.log, "Log")
        actions = W.QHBoxLayout()
        layout.addLayout(actions)
        for label, callback in [("Validate configuration", self.validate), ("Preview selected backer", self.preview),
                                ("Restore names and colors", self.restore), ("Export selected backers", self.start)]:
            button = W.QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        self.status = W.QLabel("Select the spreadsheet, base ZIP and textures. Validate before exporting.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.load_settings()
        self.fields["name_pattern"].textChanged.connect(self.naming_changed)
        self.fields["output"].textChanged.connect(self.naming_changed)
        self.naming_changed()
        self.update_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="CREAM-updates")
        self.update_future = None
        self._updates_stopped = False
        self.update_cancel = threading.Event()
        self.available_release = None
        self.update_mode = "check"
        self.update_status = W.QLabel("CREAM " + VERSION)
        self.update_status.setWordWrap(True)
        layout.addWidget(self.update_status)
        update_bar = W.QHBoxLayout()
        layout.addLayout(update_bar)
        self.check_button = W.QPushButton("Check for updates")
        self.access_button = W.QPushButton("Configure private access…")
        self.update_button = W.QPushButton("Download update")
        self.update_button.setEnabled(False)
        for button in (self.check_button, self.access_button, self.update_button):
            update_bar.addWidget(button)
        self.check_button.clicked.connect(self.check_updates)
        self.access_button.clicked.connect(self.configure_access)
        self.update_button.clicked.connect(self.update_clicked)
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.setInterval(200)
        self.update_timer.timeout.connect(self.poll_update)
        if self.reload_callback is None:
            QtCore.QTimer.singleShot(0, self.adopt_reload_support)
        if auto_update:
            QtCore.QTimer.singleShot(1000, self.check_updates)

    def adopt_reload_support(self):
        """Finish a one-time upgrade applied by the pre-1.3 startup loader."""
        import importlib
        import sys
        package = sys.modules[__package__]
        if getattr(package, "_window", None) is not self:
            return
        if not hasattr(package, "request_reload"):
            window, action = package._window, package._action
            try:
                importlib.reload(bootstrap)
                importlib.reload(package)
            finally:
                package._window, package._action = window, action
        self.reload_callback = package.request_reload

    def configure_access(self):
        if self.update_future is not None:
            return
        token, ok = W.QInputDialog.getText(self, "Private GitHub access",
            "Create a GitHub fine-grained personal access token for tatauna-doesnt-code/cream,\n"
            "with Repository permissions → Contents: Read-only.\n"
            "Paste it here. Windows will protect the credential for this user.", W.QLineEdit.Password)
        if ok and token.strip():
            try:
                updater.save_token(token)
                self.check_updates()
            except Exception as exc:
                self.update_status.setText(str(exc))

    def check_updates(self):
        if self._updates_stopped or self.update_future is not None:
            return
        if bootstrap.pending_path(Path(__file__).parent).exists():
            self.show_pending_update()
            return
        self.update_mode = "check"
        self.update_status.setText("Checking for new releases…")
        self.check_button.setEnabled(False)
        self.update_future = self.update_pool.submit(updater.check_latest)
        self.update_timer.start()

    def download_update(self):
        if self.update_future is not None or self.available_release is None:
            return
        if self.runner is not None or self.saved is not None:
            self.update_status.setText("Finish the batch and restore the preview before updating.")
            return
        self.update_mode = "download"
        self.update_cancel.clear()
        self.update_button.setEnabled(False)
        self.check_button.setEnabled(False)
        self.update_status.setText("Downloading and verifying the update…")
        self.update_future = self.update_pool.submit(updater.stage_release,
            self.available_release, Path(__file__).parent, self.update_cancel)
        self.update_timer.start()

    def poll_update(self):
        if self.update_future is None or not self.update_future.done():
            return
        future, self.update_future = self.update_future, None
        self.update_timer.stop()
        self.check_button.setEnabled(True)
        try:
            result = future.result()
            if self.update_mode == "download":
                self.show_pending_update()
            else:
                self.available_release = result
                self.update_button.setText("Download update")
                self.update_button.setEnabled(result is not None)
                self.update_status.setText("New release: " + result["version"] if result else "CREAM " + VERSION + " is up to date.")
        except Exception as exc:
            self.update_status.setText(str(exc))

    def show_pending_update(self):
        try:
            info = bootstrap.pending_info(Path(__file__).parent)
            if info is None:
                return
            can_reload = info["restart"] == "cream" and self.reload_callback is not None
            self.update_button.setText("Apply and reopen CREAM" if can_reload else "Restart Painter required")
            self.update_button.setEnabled(can_reload)
            self.update_status.setText(
                "CREAM " + info["version"] + (" is ready. Apply it without restarting Painter." if can_reload
                else " is ready. Save your work and restart Painter to install.") + " " + info["reason"])
        except Exception as exc:
            self.update_button.setEnabled(False)
            self.update_status.setText(str(exc))

    def update_clicked(self):
        if bootstrap.pending_path(Path(__file__).parent).exists():
            reason = self.reload_block_reason()
            if reason:
                self.update_status.setText(reason)
            elif self.reload_callback is not None:
                self.reload_callback()
        else:
            self.download_update()

    def reload_block_reason(self):
        if self.runner is not None or self._stepping or self.future is not None or self.update_future is not None:
            return "Wait for the current batch or background task to finish before applying the update."
        if self.saved is not None:
            return "Restore names and colors before applying the update."
        if sp.project.is_open():
            if sp.project.is_busy():
                return "Painter is busy. Wait for the current operation to finish."
            if sp.project.file_path() and self.recovery_path().exists():
                return "Restore the pending project recovery before applying the update."
        return ""

    def stop_background_tasks(self):
        self.timer.stop()
        self.stop_updater()
        self.update_pool.shutdown(wait=True, cancel_futures=True)
        self.pool.shutdown(wait=True, cancel_futures=True)

    def capture_reload_state(self):
        return {"rows": self.rows, "loaded_sheet": getattr(self, "loaded_sheet", None),
                "checked": [self.backers.item(i, 0).checkState() == QtCore.Qt.Checked
                            for i in range(self.backers.rowCount())],
                "selected": self.backers.currentRow(), "log": self.log.toPlainText()}

    def restore_reload_state(self, state):
        if not state:
            return
        self.rows = state["rows"]
        self.loaded_sheet = state["loaded_sheet"]
        self.backers.setRowCount(len(self.rows))
        for i, row in enumerate(self.rows):
            self.backers.setItem(i, 0, self.check_item(state["checked"][i]))
            values = [f"{row['line']} / {row['id']}", row["name"],
                      *[c or "Original" for c in row["colors"]], "", "Pending"]
            for column, value in enumerate(values, 1):
                self.backers.setItem(i, column, W.QTableWidgetItem(str(value)))
        self.refresh_destinations()
        if state["selected"] >= 0:
            self.backers.selectRow(state["selected"])
        self.log.setPlainText(state["log"])

    def stop_updater(self):
        self._updates_stopped = True
        self.update_cancel.set()
        self.update_timer.stop()
        self.update_pool.shutdown(wait=False, cancel_futures=True)

    def field(self, form, key, label, value, pattern):
        row = W.QWidget()
        layout = W.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        text = W.QLineEdit(value)
        self.fields[key] = text
        layout.addWidget(text)
        button = W.QPushButton("Browse…")
        button.clicked.connect(lambda: self.browse(key, pattern))
        layout.addWidget(button)
        form.addRow(label, row)

    def browse(self, key, pattern):
        if pattern:
            value, _ = W.QFileDialog.getOpenFileName(self, "Select", self.fields[key].text(), pattern)
        else:
            value = W.QFileDialog.getExistingDirectory(self, "ZIP output folder", self.fields[key].text())
        if value:
            self.fields[key].setText(value)

    def say(self, message):
        self.log.appendPlainText(datetime.now().strftime("%H:%M:%S  ") + message)
        self.status.setText(message)
        if self.progress and not self.cancel.is_set():
            self.progress.label.setText(message)

    def error(self, exc):
        self.say(str(exc))
        self.log.appendPlainText(traceback.format_exc())
        W.QMessageBox.warning(self, "CREAM", str(exc))

    @staticmethod
    def check_item(checked):
        item = W.QTableWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable)
        item.setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
        return item

    def check_rows(self, checked):
        for i in range(self.backers.rowCount()):
            self.backers.item(i, 0).setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)

    def load_sheet(self):
        try:
            if self.runner is not None or self.saved is not None:
                raise ValueError("Finish the batch and restore the preview before loading another spreadsheet.")
            path = Path(self.fields["sheet"].text())
            stamp = path.stat().st_mtime_ns
            table = core.read_table(path)
            dialog = ColumnDialog(table, self.column_profile, self)
            if dialog.exec() != W.QDialog.Accepted:
                return
            if path.stat().st_mtime_ns != stamp:
                raise ValueError("The spreadsheet changed during column selection. Load it again.")
            rows, warnings = dialog.rows, dialog.warnings
            self.column_profile = {"headers": table[0], "mapping": dialog.mapping}
            self.rows = rows
            self.loaded_sheet = (self.fields["sheet"].text(), stamp)
            self.backers.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.backers.setItem(i, 0, self.check_item(True))
                values = [f"{row['line']} / {row['id']}", row["name"], *[c or "Original" for c in row["colors"]], "", "Pending"]
                for column, value in enumerate(values, 1):
                    self.backers.setItem(i, column, W.QTableWidgetItem(str(value)))
            self.refresh_destinations()
            self.backers.selectRow(0)
            for warning in warnings:
                self.say(warning)
            self.say(f"{len(rows)} backers loaded. {len(warnings)} warnings in the Log.")
            self.save_settings()
        except Exception as exc:
            self.error(exc)

    def refresh_destinations(self):
        pattern = core.validate_name_pattern(self.fields["name_pattern"].text())
        occupied = set()
        for i, row in enumerate(self.rows):
            path = core.next_destination(self.fields["output"].text(), core.format_skin_name(pattern, row), occupied)
            self.backers.item(i, 6).setText(path.name)
            if i == 0:
                self.name_preview.setText(path.name)

    def naming_changed(self):
        try:
            pattern = self.fields["name_pattern"].text()
            example = self.rows[0] if self.rows else {"stem": "Joseph", "name": "Joseph", "id": "001", "line": 2}
            self.name_preview.setText(core.format_skin_name(pattern, example) + ".zip")
            self.refresh_destinations()
        except ValueError as exc:
            self.name_preview.setText(str(exc))
            for i in range(self.backers.rowCount()):
                if self.backers.item(i, 6) is not None:
                    self.backers.item(i, 6).setText("Invalid name pattern")

    def selections(self):
        return [{"set": self.maps.item(i, 1).text(), "map": self.maps.item(i, 2).text(),
                 "size": self.maps.cellWidget(i, 3).currentData()}
                for i in range(self.maps.rowCount()) if self.maps.item(i, 0).checkState() == QtCore.Qt.Checked]

    def save_settings(self):
        core.atomic_json(DATA / "settings.json", {"fields": {k: v.text() for k, v in self.fields.items()},
                         "column_profile": self.column_profile,
                         "maps": [{"checked": self.maps.item(i, 0).checkState() == QtCore.Qt.Checked,
                                   "size": self.maps.cellWidget(i, 3).currentData()} for i in range(self.maps.rowCount())]})

    def load_settings(self):
        try:
            settings = json.loads((DATA / "settings.json").read_text(encoding="utf-8"))
            # Before configurable naming every export had this prefix. Preserve it on upgrade.
            self.fields["name_pattern"].setText(settings.get("fields", {}).get("name_pattern", core.LEGACY_NAME_PATTERN))
            self.column_profile = settings.get("column_profile")
            for key, value in settings.get("fields", {}).items():
                if key in self.fields:
                    self.fields[key].setText(value)
            for i, item in enumerate(settings.get("maps", [])[:self.maps.rowCount()]):
                self.maps.item(i, 0).setCheckState(QtCore.Qt.Checked if item["checked"] else QtCore.Qt.Unchecked)
                combo = self.maps.cellWidget(i, 3)
                combo.setCurrentIndex(max(0, combo.findData(item["size"])))
        except (OSError, ValueError, KeyError):
            pass

    def recovery_path(self):
        return DATA / ("recover-" + core.fingerprint(painter.project_path().casefold())[:20] + ".json")

    def capture(self):
        path = self.recovery_path()
        if self.saved is not None or path.exists():
            raise ValueError("A preview or recovery is pending. Use Restore names and colors before continuing.")
        saved = painter.snapshot()
        core.atomic_json(path, saved)  # Must reach disk before editing the project.
        self.saved = saved
        return saved

    def ensure_rows(self):
        if not self.rows:
            raise ValueError("Load the spreadsheet first.")
        sheet = self.fields["sheet"].text()
        if (sheet, Path(sheet).stat().st_mtime_ns) != self.loaded_sheet:
            raise ValueError("The spreadsheet changed. Click Load spreadsheet again.")

    def config_signature(self):
        base = Path(self.fields["base"].text())
        signature = {"project": painter.project_path(), "base": str(base.resolve()),
                                 "base_size": base.stat().st_size, "base_mtime": base.stat().st_mtime_ns,
                                 "maps": self.selections(), "preset": painter.preset_maps(), "normal_invert": False,
                                 "dds_headers": "BC4U_BC5U",
                                 "normal_export": "Normal_OpenGL"}
        pattern = self.fields["name_pattern"].text()
        if pattern != core.LEGACY_NAME_PATTERN:
            signature["zip_name_pattern"] = pattern
        return core.fingerprint(signature)

    def check(self):
        if not painter.ready():
            raise ValueError("Wait for Painter to finish its current operation and open a saved project in painting mode.")
        self.ensure_rows()
        core.validate_name_pattern(self.fields["name_pattern"].text())
        for row in self.rows:
            core.format_skin_name(self.fields["name_pattern"].text(), row)
        if self.saved or self.recovery_path().exists():
            raise ValueError("Restore names and colors before validating or starting a new batch.")
        selections = self.selections()
        if not selections:
            raise ValueError("Select at least one texture in the Textures tab.")
        base = Path(self.fields["base"].text())
        core.inspect_base(base)
        converter = Path(self.fields["converter"].text())
        if not converter.is_file() or converter.name.lower() != "texconv.exe":
            raise ValueError("Select texconv.exe (included in the plugin bin folder).")
        output = Path(self.fields["output"].text())
        if not output.is_absolute():
            raise ValueError("Choose an output folder with an absolute path.")
        output.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=output):
            pass
        saved = painter.snapshot()
        maps = painter.preset_maps()
        painter.preflight_exports(maps, selections, output)
        for i in range(3):
            if any(r["colors"][i] for r in self.rows) and not any(t.get("index") == i for t in saved["targets"]):
                raise ValueError(f"There is color_{i + 1} in the spreadsheet, but no PLAYER_COLOR{i + 1} in the project.")
        self.refresh_destinations()
        self.save_settings()
        return saved, maps

    def validate(self):
        try:
            saved, _ = self.check()
            for target in saved["targets"]:
                self.say("Found: " + " / ".join(map(str, target["location"])))
            self.say(f"Configuration valid: {len(saved['targets'])} targets; {len(self.selections())} textures per backer. Run a test export first.")
        except Exception as exc:
            self.error(exc)

    def preview(self):
        try:
            if not painter.ready():
                raise ValueError("Wait for Painter to become available.")
            self.ensure_rows()
            index = self.backers.currentRow()
            if index < 0:
                raise ValueError("Select a row to preview.")
            saved = self.capture()
            try:
                painter.apply(saved, self.rows[index])
            except Exception:
                painter.apply(saved)
                self.recovery_path().unlink(missing_ok=True)
                self.saved = None
                raise
            self.say("Preview applied. Check the model, then use Restore names and colors. Do not save the preview over your original.")
        except Exception as exc:
            self.error(exc)

    def restore(self):
        try:
            if not painter.ready():
                raise ValueError("Wait for Painter to become available before restoring.")
            path = self.recovery_path()
            saved = self.saved or (json.loads(path.read_text(encoding="utf-8")) if path.exists() else None)
            if saved is None:
                self.say("There is no pending preview or recovery for this project.")
                return
            painter.apply(saved)
            path.unlink(missing_ok=True)
            self.saved = None
            self.say("Original names and colors restored. The plugin did not save the .spp.")
        except Exception as exc:
            self.error(exc)

    def resume(self):
        try:
            self.ensure_rows()
            path, _ = W.QFileDialog.getOpenFileName(self, "Previous report", self.fields["output"].text(), "CREAM report (*.json)")
            if not path:
                return
            report = json.loads(Path(path).read_text(encoding="utf-8"))
            if report["signature"] != self.config_signature():
                raise ValueError("The project, preset, base ZIP, texture selection or export settings differ from this report.")
            done = {r["key"] for r in report["rows"] if r["status"] == "success" and Path(r["output"]).is_file()}
            count = 0
            for i, row in enumerate(self.rows):
                completed = core.fingerprint(row) in done
                self.backers.item(i, 0).setCheckState(QtCore.Qt.Unchecked if completed else QtCore.Qt.Checked)
                self.backers.item(i, 7).setText("Already completed" if completed else "Pending")
                count += completed
            self.say(f"Resume prepared: {count} completed rows deselected. Review and click Export selected backers.")
        except Exception as exc:
            self.error(exc)

    def start(self):
        captured = False
        try:
            _, maps = self.check()
            indices = [i for i in range(len(self.rows)) if self.backers.item(i, 0).checkState() == QtCore.Qt.Checked]
            if not indices:
                raise ValueError("Select at least one backer.")
            saved = self.capture()
            captured = True
            output = Path(self.fields["output"].text())
            report_dir = output / "_KR7_reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            self.report_path = report_dir / (stamp + ".json")
            self.report = {"version": 1, "signature": self.config_signature(), "started": stamp,
                           "project": saved["project"], "status": "running", "rows": []}
            core.atomic_json(self.report_path, self.report)
            self.cancel.clear()
            self.progress = Progress(self, self.cancel)
            self.progress.bar.setRange(0, len(indices))
            self.progress.show()
            self.runner = self.run_batch(indices, saved, maps, self.selections(), self.fields["name_pattern"].text())
            self.timer.start()
        except Exception as exc:
            # capture() may have succeeded before setup failed; no mutation yet.
            if captured and self.saved is not None and self.runner is None:
                try:
                    self.recovery_path().unlink(missing_ok=True)
                    self.saved = None
                except Exception:
                    pass
            self.error(exc)

    def wait_ready(self):
        while not painter.ready():
            if not sp.project.is_open():
                raise RuntimeError("The project was closed. The recovery record was preserved.")
            yield

    def await_file(self, function, *args):
        self.future = self.pool.submit(function, *args)
        while not self.future.done():
            yield
        future, self.future = self.future, None
        return future.result()

    def run_batch(self, indices, saved, maps, selections, name_pattern=None):
        name_pattern = self.fields["name_pattern"].text() if name_pattern is None else name_pattern
        base = Path(self.fields["base"].text())
        output = Path(self.fields["output"].text())
        converter = Path(self.fields["converter"].text())
        try:
            for position, index in enumerate(indices):
                core.check_cancel(self.cancel)
                row = self.rows[index]
                entry = {"key": core.fingerprint(row), "id": row["id"], "line": row["line"],
                         "name": row["name"], "status": "running", "output": ""}
                self.report["rows"].append(entry)
                core.atomic_json(self.report_path, self.report)
                self.backers.item(index, 7).setText("Processing")
                temp = Path(tempfile.mkdtemp(prefix="kr7-", dir=DATA))
                try:
                    yield from self.wait_ready()
                    core.check_cancel(self.cancel)
                    self.say(f"{position + 1}/{len(indices)} — applying {row['name']}")
                    painter.apply(saved, row)
                    yield
                    replacements = {}
                    for selection in selections:
                        yield from self.wait_ready()
                        core.check_cancel(self.cancel)
                        filename = f"{selection['set']}_{selection['map']}"
                        self.say(f"{position + 1}/{len(indices)} — {row['name']}: exporting {filename}")
                        source = painter.export_one(maps, selection, temp)
                        yield
                        core.check_cancel(self.cancel)
                        self.say(f"{row['name']}: converting {filename} to DDS")
                        width, height = core.dimensions(selection["set"], selection["size"])
                        dds = yield from self.await_file(core.convert, converter, source, temp / "dds",
                                                         selection["map"], width, height, self.cancel)
                        replacements[filename + ".dds"] = dds
                        source.unlink(missing_ok=True)
                    core.check_cancel(self.cancel)
                    destination = core.next_destination(output, core.format_skin_name(name_pattern, row))
                    entry["output"] = str(destination)
                    core.atomic_json(self.report_path, self.report)
                    self.say(f"{row['name']}: building and verifying {destination.name}")
                    final = yield from self.await_file(core.build_zip, base, replacements, destination, self.cancel)
                    entry.update(status="success", output=final)
                    # Persist success immediately after publish; then restore the project.
                    core.atomic_json(self.report_path, self.report)
                    self.backers.item(index, 0).setCheckState(QtCore.Qt.Unchecked)
                    self.backers.item(index, 6).setText(Path(final).name)
                    self.backers.item(index, 7).setText("Completed")
                except core.Cancelled:
                    entry["status"] = "cancelled"
                    self.backers.item(index, 7).setText("Cancelled")
                    raise
                except Exception as exc:
                    entry.update(status="failed", error=str(exc))
                    self.backers.item(index, 7).setText("Failed")
                    self.say(f"Failed for {row['name']}: {exc}. See the report.")
                finally:
                    yield from self.wait_ready()
                    painter.apply(saved)
                    core.atomic_json(self.report_path, self.report)
                    shutil.rmtree(temp, ignore_errors=True)
                self.progress.bar.setValue(position + 1)
                yield
            self.report["status"] = "completed_with_errors" if any(r["status"] == "failed" for r in self.report["rows"]) else "completed"
        except core.Cancelled:
            self.report["status"] = "cancelled"
        finally:
            yield from self.wait_ready()
            painter.apply(saved)
            self.recovery_path().unlink(missing_ok=True)
            self.saved = None
            core.atomic_json(self.report_path, self.report)

    def tick(self):
        # Painter exports may run a nested Qt event loop; never re-enter a generator.
        if self._stepping or self.runner is None:
            return
        self._stepping = True
        try:
            next(self.runner)
        except StopIteration:
            self.finish()
        except Exception as exc:
            if self.report:
                self.report.update(status="interrupted", error=str(exc))
                core.atomic_json(self.report_path, self.report)
            self.finish()
            self.error(exc)
        finally:
            self._stepping = False

    def finish(self):
        self.timer.stop()
        self.runner = None
        if self.progress:
            self.progress.hide()
            self.progress.deleteLater()
            self.progress = None
        if self.report:
            successes = sum(r["status"] == "success" for r in self.report["rows"])
            failures = sum(r["status"] == "failed" for r in self.report["rows"])
            cancelled = " Cancelled by the user." if self.report["status"] == "cancelled" else ""
            self.say(f"Batch finished: {successes} ZIPs completed; {failures} failures.{cancelled} Report: {self.report_path}")

    def closeEvent(self, event):
        if self.runner:
            self.cancel.set()
            event.ignore()
        elif self.saved is not None:
            self.restore()
            if self.saved is not None:
                event.ignore()
            else:
                event.accept()
        else:
            self.save_settings()
            event.accept()
