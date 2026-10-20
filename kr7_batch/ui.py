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
from .version import VERSION

DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "KR7BatchExporter"
DEFAULT_OUTPUT = r"C:\Users\lucas\Documents\Trackmania\Skins\Models\CarSport\KR7BACKERS"


class Progress(W.QDialog):
    def __init__(self, parent, cancel):
        super().__init__(parent)
        self.cancel = cancel
        self.setWindowTitle("KR7 — batch em andamento")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setMinimumWidth(530)
        layout = W.QVBoxLayout(self)
        self.label = W.QLabel("Preparando…")
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.bar = W.QProgressBar()
        layout.addWidget(self.bar)
        self.button = W.QPushButton("Cancelar com segurança")
        self.button.clicked.connect(self.request_cancel)
        layout.addWidget(self.button)
        layout.addWidget(W.QLabel("Se o Painter estiver ocupado, a parada aguardará a operação atual."))

    def request_cancel(self):
        self.cancel.set()
        self.button.setEnabled(False)
        self.label.setText("Cancelamento solicitado. Aguardando uma etapa segura e restaurando o projeto…")

    def reject(self):
        self.request_cancel()

    def closeEvent(self, event):
        self.request_cancel()
        event.ignore()


class Window(W.QDialog):
    def __init__(self, auto_update=True):
        super().__init__(sp.ui.get_main_window())
        self.setWindowTitle("CREAM — " + VERSION)
        self.resize(1040, 820)
        self.rows = []
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
        self.field(form, "sheet", "Planilha CSV / XLSX", "", "Planilhas (*.csv *.xlsx)")
        self.field(form, "base", "ZIP base", "", "Skin (*.zip)")
        self.field(form, "output", "Pasta dos ZIPs", DEFAULT_OUTPUT, None)
        self.field(form, "converter", "Conversor DDS", str(Path(__file__).parent / "bin" / "texconv.exe"), "Conversor (texconv.exe)")
        self.tabs = W.QTabWidget()
        layout.addWidget(self.tabs, 1)
        page = W.QWidget()
        box = W.QVBoxLayout(page)
        toolbar = W.QHBoxLayout()
        box.addLayout(toolbar)
        for label, callback in [("Carregar planilha", self.load_sheet), ("Marcar todos", lambda: self.check_rows(True)),
                                ("Desmarcar todos", lambda: self.check_rows(False)), ("Retomar de relatório…", self.resume)]:
            button = W.QPushButton(label)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
        self.backers = W.QTableWidget(0, 8)
        self.backers.setHorizontalHeaderLabels(["Gerar", "Linha / ID", "Nome na skin", "Cor 1", "Cor 2", "Cor 3", "ZIP previsto", "Estado"])
        self.backers.setSelectionBehavior(W.QAbstractItemView.SelectRows)
        self.backers.setSelectionMode(W.QAbstractItemView.SingleSelection)
        self.backers.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        self.backers.horizontalHeader().setSectionResizeMode(W.QHeaderView.ResizeToContents)
        self.backers.horizontalHeader().setStretchLastSection(True)
        box.addWidget(self.backers)
        box.addWidget(W.QLabel("Nomes: até 20 caracteres. Cores vazias: original do projeto. Repetidos recebem 2, 3… no ZIP."))
        self.tabs.addTab(page, "Backers")
        page = W.QWidget()
        box = W.QVBoxLayout(page)
        box.addWidget(W.QLabel("Preset TM2020 • DDS sem mipmaps • normals OpenGL na exportação • Glass não recebe nomes/cores"))
        self.maps = W.QTableWidget(0, 5)
        self.maps.setHorizontalHeaderLabels(["Exportar", "Texture set", "Textura", "Resolução final", "DDS"])
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
        box.addWidget(W.QLabel("Arquivos não selecionados são preservados no ZIP base. Arquivos ausentes continuam ausentes."))
        self.tabs.addTab(page, "Texturas")
        self.log = W.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.tabs.addTab(self.log, "Registro")
        actions = W.QHBoxLayout()
        layout.addLayout(actions)
        for label, callback in [("Validar configuração", self.validate), ("Prévia do backer selecionado", self.preview),
                                ("Restaurar nomes e cores", self.restore), ("Exportar backers marcados", self.start)]:
            button = W.QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        self.status = W.QLabel("Selecione a planilha, o ZIP base e as texturas. Valide antes de exportar.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.load_settings()
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
        self.check_button = W.QPushButton("Verificar atualizações")
        self.access_button = W.QPushButton("Configurar acesso privado…")
        self.update_button = W.QPushButton("Atualizar CREAM")
        self.update_button.setEnabled(False)
        for button in (self.check_button, self.access_button, self.update_button):
            update_bar.addWidget(button)
        self.check_button.clicked.connect(self.check_updates)
        self.access_button.clicked.connect(self.configure_access)
        self.update_button.clicked.connect(self.download_update)
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.setInterval(200)
        self.update_timer.timeout.connect(self.poll_update)
        if auto_update:
            QtCore.QTimer.singleShot(1000, self.check_updates)

    def configure_access(self):
        if self.update_future is not None:
            return
        token, ok = W.QInputDialog.getText(self, "Acesso ao GitHub privado",
            "Crie um fine-grained personal access token no GitHub para tatauna-doesnt-code/cream,\n"
            "com Repository permissions → Contents: Read-only.\n"
            "Cole aqui. O Windows protegerá a credencial neste usuário.", W.QLineEdit.Password)
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
            self.update_status.setText("Atualização preparada. Reinicie o Painter para instalar.")
            self.update_button.setEnabled(False)
            return
        self.update_mode = "check"
        self.update_status.setText("Consultando novas versões…")
        self.check_button.setEnabled(False)
        self.update_future = self.update_pool.submit(updater.check_latest)
        self.update_timer.start()

    def download_update(self):
        if self.update_future is not None or self.available_release is None:
            return
        if self.runner is not None or self.saved is not None:
            self.update_status.setText("Encerre o lote e restaure a prévia antes de atualizar.")
            return
        self.update_mode = "download"
        self.update_cancel.clear()
        self.update_button.setEnabled(False)
        self.check_button.setEnabled(False)
        self.update_status.setText("Baixando e verificando atualização…")
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
                self.update_status.setText("CREAM " + result + " preparado. Salve seu trabalho e reinicie o Painter para instalar.")
            else:
                self.available_release = result
                self.update_button.setEnabled(result is not None)
                self.update_status.setText("Nova versão: " + result["version"] if result else "CREAM " + VERSION + " está atualizado.")
        except Exception as exc:
            self.update_status.setText(str(exc))

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
        button = W.QPushButton("Escolher…")
        button.clicked.connect(lambda: self.browse(key, pattern))
        layout.addWidget(button)
        form.addRow(label, row)

    def browse(self, key, pattern):
        if pattern:
            value, _ = W.QFileDialog.getOpenFileName(self, "Selecionar", self.fields[key].text(), pattern)
        else:
            value = W.QFileDialog.getExistingDirectory(self, "Pasta dos ZIPs", self.fields[key].text())
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
        W.QMessageBox.warning(self, "KR7", str(exc))

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
            rows, warnings = core.read_rows(self.fields["sheet"].text())
            self.rows = rows
            self.loaded_sheet = (self.fields["sheet"].text(), Path(self.fields["sheet"].text()).stat().st_mtime_ns)
            self.backers.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self.backers.setItem(i, 0, self.check_item(True))
                values = [f"{row['line']} / {row['id']}", row["name"], *[c or "Original" for c in row["colors"]], "", "Pendente"]
                for column, value in enumerate(values, 1):
                    self.backers.setItem(i, column, W.QTableWidgetItem(str(value)))
            self.refresh_destinations()
            self.backers.selectRow(0)
            for warning in warnings:
                self.say(warning)
            self.say(f"{len(rows)} backers carregados. {len(warnings)} avisos no Registro.")
            self.save_settings()
        except Exception as exc:
            self.error(exc)

    def refresh_destinations(self):
        occupied = set()
        for i, row in enumerate(self.rows):
            path = core.next_destination(self.fields["output"].text(), row["stem"], occupied)
            self.backers.item(i, 6).setText(path.name)

    def selections(self):
        return [{"set": self.maps.item(i, 1).text(), "map": self.maps.item(i, 2).text(),
                 "size": self.maps.cellWidget(i, 3).currentData()}
                for i in range(self.maps.rowCount()) if self.maps.item(i, 0).checkState() == QtCore.Qt.Checked]

    def save_settings(self):
        core.atomic_json(DATA / "settings.json", {"fields": {k: v.text() for k, v in self.fields.items()},
                         "maps": [{"checked": self.maps.item(i, 0).checkState() == QtCore.Qt.Checked,
                                   "size": self.maps.cellWidget(i, 3).currentData()} for i in range(self.maps.rowCount())]})

    def load_settings(self):
        try:
            settings = json.loads((DATA / "settings.json").read_text(encoding="utf-8"))
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
            raise ValueError("Há uma prévia ou recuperação pendente. Use Restaurar nomes e cores antes de continuar.")
        saved = painter.snapshot()
        core.atomic_json(path, saved)  # Must reach disk before editing the project.
        self.saved = saved
        return saved

    def ensure_rows(self):
        if not self.rows:
            raise ValueError("Carregue a planilha primeiro.")
        sheet = self.fields["sheet"].text()
        if (sheet, Path(sheet).stat().st_mtime_ns) != self.loaded_sheet:
            raise ValueError("A planilha mudou. Clique Carregar planilha novamente.")

    def config_signature(self):
        base = Path(self.fields["base"].text())
        return core.fingerprint({"project": painter.project_path(), "base": str(base.resolve()),
                                 "base_size": base.stat().st_size, "base_mtime": base.stat().st_mtime_ns,
                                 "maps": self.selections(), "preset": painter.preset_maps(), "normal_invert": False,
                                 "normal_export": "Normal_OpenGL"})

    def check(self):
        if not painter.ready():
            raise ValueError("Aguarde o Painter terminar a operação atual e abra um projeto salvo no modo de pintura.")
        self.ensure_rows()
        if self.saved or self.recovery_path().exists():
            raise ValueError("Restaure os nomes e cores antes de validar/iniciar um novo lote.")
        selections = self.selections()
        if not selections:
            raise ValueError("Marque pelo menos uma textura na aba Texturas.")
        base = Path(self.fields["base"].text())
        core.inspect_base(base)
        converter = Path(self.fields["converter"].text())
        if not converter.is_file() or converter.name.lower() != "texconv.exe":
            raise ValueError("Selecione texconv.exe (incluído na pasta bin do plugin).")
        output = Path(self.fields["output"].text())
        if not output.is_absolute():
            raise ValueError("Escolha uma pasta de destino com caminho absoluto.")
        output.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=output):
            pass
        saved = painter.snapshot()
        maps = painter.preset_maps()
        painter.preflight_exports(maps, selections, output)
        for i in range(3):
            if any(r["colors"][i] for r in self.rows) and not any(t.get("index") == i for t in saved["targets"]):
                raise ValueError(f"Há cor_{i + 1} na planilha, mas nenhum PLAYER_COLOR{i + 1} no projeto.")
        self.refresh_destinations()
        self.save_settings()
        return saved, maps

    def validate(self):
        try:
            saved, _ = self.check()
            for target in saved["targets"]:
                self.say("Encontrado: " + " / ".join(map(str, target["location"])))
            self.say(f"Configuração válida: {len(saved['targets'])} alvos; {len(self.selections())} texturas por backer. Faça primeiro um export de teste.")
        except Exception as exc:
            self.error(exc)

    def preview(self):
        try:
            if not painter.ready():
                raise ValueError("Aguarde o Painter ficar disponível.")
            self.ensure_rows()
            index = self.backers.currentRow()
            if index < 0:
                raise ValueError("Selecione uma linha para prévia.")
            saved = self.capture()
            try:
                painter.apply(saved, self.rows[index])
            except Exception:
                painter.apply(saved)
                self.recovery_path().unlink(missing_ok=True)
                self.saved = None
                raise
            self.say("Prévia aplicada. Confira no modelo; depois use Restaurar nomes e cores. Não salve a prévia sobre seu original.")
        except Exception as exc:
            self.error(exc)

    def restore(self):
        try:
            if not painter.ready():
                raise ValueError("Aguarde o Painter ficar disponível para restaurar.")
            path = self.recovery_path()
            saved = self.saved or (json.loads(path.read_text(encoding="utf-8")) if path.exists() else None)
            if saved is None:
                self.say("Não há prévia ou recuperação pendente neste projeto.")
                return
            painter.apply(saved)
            path.unlink(missing_ok=True)
            self.saved = None
            self.say("Nomes e cores originais restaurados. O plugin não salvou o .spp.")
        except Exception as exc:
            self.error(exc)

    def resume(self):
        try:
            self.ensure_rows()
            path, _ = W.QFileDialog.getOpenFileName(self, "Relatório anterior", self.fields["output"].text(), "Relatório KR7 (*.json)")
            if not path:
                return
            report = json.loads(Path(path).read_text(encoding="utf-8"))
            if report["signature"] != self.config_signature():
                raise ValueError("O projeto, preset, ZIP base ou seleção de texturas difere desse relatório.")
            done = {r["key"] for r in report["rows"] if r["status"] == "success" and Path(r["output"]).is_file()}
            count = 0
            for i, row in enumerate(self.rows):
                completed = core.fingerprint(row) in done
                self.backers.item(i, 0).setCheckState(QtCore.Qt.Unchecked if completed else QtCore.Qt.Checked)
                self.backers.item(i, 7).setText("Já concluído" if completed else "Pendente")
                count += completed
            self.say(f"Retomada preparada: {count} linhas concluídas desmarcadas. Confira e clique Exportar.")
        except Exception as exc:
            self.error(exc)

    def start(self):
        captured = False
        try:
            _, maps = self.check()
            indices = [i for i in range(len(self.rows)) if self.backers.item(i, 0).checkState() == QtCore.Qt.Checked]
            if not indices:
                raise ValueError("Marque ao menos um backer.")
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
            self.runner = self.run_batch(indices, saved, maps, self.selections())
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
                raise RuntimeError("O projeto foi fechado. Registro de recuperação preservado.")
            yield

    def await_file(self, function, *args):
        self.future = self.pool.submit(function, *args)
        while not self.future.done():
            yield
        future, self.future = self.future, None
        return future.result()

    def run_batch(self, indices, saved, maps, selections):
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
                self.backers.item(index, 7).setText("Processando")
                temp = Path(tempfile.mkdtemp(prefix="kr7-", dir=DATA))
                try:
                    yield from self.wait_ready()
                    core.check_cancel(self.cancel)
                    self.say(f"{position + 1}/{len(indices)} — aplicando {row['name']}")
                    painter.apply(saved, row)
                    yield
                    replacements = {}
                    for selection in selections:
                        yield from self.wait_ready()
                        core.check_cancel(self.cancel)
                        filename = f"{selection['set']}_{selection['map']}"
                        self.say(f"{position + 1}/{len(indices)} — {row['name']}: exportando {filename}")
                        source = painter.export_one(maps, selection, temp)
                        yield
                        core.check_cancel(self.cancel)
                        self.say(f"{row['name']}: convertendo {filename} para DDS")
                        width, height = core.dimensions(selection["set"], selection["size"])
                        dds = yield from self.await_file(core.convert, converter, source, temp / "dds",
                                                         selection["map"], width, height, self.cancel)
                        replacements[filename + ".dds"] = dds
                        source.unlink(missing_ok=True)
                    core.check_cancel(self.cancel)
                    destination = core.next_destination(output, row["stem"])
                    entry["output"] = str(destination)
                    core.atomic_json(self.report_path, self.report)
                    self.say(f"{row['name']}: montando e verificando {destination.name}")
                    final = yield from self.await_file(core.build_zip, base, replacements, destination, self.cancel)
                    entry.update(status="success", output=final)
                    # Persist success immediately after publish; then restore the project.
                    core.atomic_json(self.report_path, self.report)
                    self.backers.item(index, 0).setCheckState(QtCore.Qt.Unchecked)
                    self.backers.item(index, 6).setText(Path(final).name)
                    self.backers.item(index, 7).setText("Concluído")
                except core.Cancelled:
                    entry["status"] = "cancelled"
                    self.backers.item(index, 7).setText("Cancelado")
                    raise
                except Exception as exc:
                    entry.update(status="failed", error=str(exc))
                    self.backers.item(index, 7).setText("Falhou")
                    self.say(f"Falha em {row['name']}: {exc}. Veja o relatório.")
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
            cancelled = " Cancelado pelo usuário." if self.report["status"] == "cancelled" else ""
            self.say(f"Lote encerrado: {successes} ZIPs concluídos; {failures} falhas.{cancelled} Relatório: {self.report_path}")

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
