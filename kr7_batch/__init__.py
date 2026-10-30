# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 tatauna-doesnt-code and contributors
"""CREAM Skin Batch Exporter — Substance 3D Painter 12.1 / Python plugin.

Free software under GNU GPL version 3; see LICENSE. Distributed without warranty.
"""
_window = None
_action = None
_reload_scheduled = False


def start_plugin(apply_update=True):
    global _window, _action
    from pathlib import Path
    from . import bootstrap
    import sys
    if _window is None and apply_update:
        try:
            applied = bootstrap.apply_pending(Path(__file__).parent)
            if applied:
                for name in list(sys.modules):
                    if name.startswith(__name__ + ".") and name != __name__ + ".bootstrap":
                        del sys.modules[name]
                        globals().pop(name.rsplit('.', 1)[-1], None)
        except Exception as exc:
            print("CREAM: update not applied; previous version retained:", exc)
    from PySide6.QtGui import QAction
    import substance_painter.ui as ui
    from .ui import Window
    if _window is not None:
        _window.show()
        return
    _window = Window(reload_callback=request_reload)
    _action = QAction("CREAM — Batch Exporter", ui.get_main_window())
    _action.triggered.connect(_window.show)
    ui.add_action(ui.ApplicationMenu.Window, _action)
    _window.show()


def request_reload():
    """Leave the old button's signal stack before replacing its Python module."""
    global _reload_scheduled
    from PySide6.QtCore import QTimer
    if _reload_scheduled or _window is None:
        return
    reason = _window.reload_block_reason()
    if reason:
        _window.update_status.setText(reason)
        return
    _reload_scheduled = True
    QTimer.singleShot(0, _reload_now)


def _reload_now():
    global _window, _action, _reload_scheduled
    import importlib
    from pathlib import Path
    import sys
    import substance_painter.ui as ui
    from . import bootstrap
    target = Path(__file__).parent
    old = _window
    applied = None
    stopped = False
    modules = {}
    state = None
    try:
        if old is None:
            return
        reason = old.reload_block_reason()
        if reason:
            raise RuntimeError(reason)
        info = bootstrap.pending_info(target)
        if info is None or info["restart"] != "cream":
            raise RuntimeError("This update requires a Painter restart.")
        old.save_settings()
        state = old.capture_reload_state()
        old.stop_background_tasks()
        stopped = True
        old.hide()
        if _action is not None:
            ui.delete_ui_element(_action)
            _action = None
        applied = bootstrap.apply_pending(target, cream_only=True)
        modules = {name: module for name, module in list(sys.modules.items())
                   if name.startswith(__name__ + ".") and name != __name__ + ".bootstrap"}
        for name in modules:
            sys.modules.pop(name, None)
            globals().pop(name.rsplit(".", 1)[-1], None)
        importlib.invalidate_caches()
        _window = None
        start_plugin()
        _window.restore_reload_state(state)
        _window.update_status.setText("CREAM updated. Painter did not need to restart.")
        ui.delete_ui_element(old)
    except Exception as exc:
        if applied:
            try:
                bootstrap.rollback_applied(target, applied)
                for name in list(sys.modules):
                    if name.startswith(__name__ + ".") and name != __name__ + ".bootstrap":
                        sys.modules.pop(name, None)
                        globals().pop(name.rsplit(".", 1)[-1], None)
                sys.modules.update(modules)
                for name, module in modules.items():
                    if name.count(".") == __name__.count(".") + 1:
                        globals()[name.rsplit(".", 1)[-1]] = module
            except Exception as rollback_error:
                print("CREAM: rollback failed; restart Painter:", rollback_error)
                _window = old
                old.update_status.setText("Update recovery failed. Save your work and restart Painter. " + str(rollback_error))
                old.setEnabled(False)
                old.show()
                return
        if stopped:
            if _window is not None and _window is not old:
                _window.stop_background_tasks()
                ui.delete_ui_element(_window)
            _window = None
            start_plugin(apply_update=False)
            _window.restore_reload_state(state)
            ui.delete_ui_element(old)
        if _window is not None:
            _window.update_status.setText("Update not applied. Restart Painter to retry. " + str(exc))
    finally:
        _reload_scheduled = False


def close_plugin():
    global _window, _action
    import substance_painter.ui as ui
    if _window is not None:
        if _window.runner is not None:
            _window.cancel.set()
            raise RuntimeError("CREAM: cancellation requested; wait for the batch to finish before disabling the plugin.")
        if _window.saved is not None:
            _window.restore()
            if _window.saved is not None:
                raise RuntimeError("CREAM: restore the project before disabling the plugin.")
        _window.stop_background_tasks()
        ui.delete_ui_element(_window)
        _window = None
    if _action is not None:
        ui.delete_ui_element(_action)
        _action = None
