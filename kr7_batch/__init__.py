"""KR7 Backer Batch Exporter — Substance 3D Painter 12.1 / Python plugin."""
_window = None
_action = None


def start_plugin():
    global _window, _action
    from pathlib import Path
    from . import bootstrap
    import sys
    if _window is None:
        try:
            applied = bootstrap.apply_pending(Path(__file__).parent)
            if applied:
                for name in list(sys.modules):
                    if name.startswith(__name__ + ".") and name != __name__ + ".bootstrap":
                        del sys.modules[name]
                        globals().pop(name.rsplit('.', 1)[-1], None)
        except Exception as exc:
            print("CREAM: atualização não aplicada; versão anterior mantida:", exc)
    from PySide6.QtGui import QAction
    import substance_painter.ui as ui
    from .ui import Window
    if _window is not None:
        _window.show()
        return
    _window = Window()
    _action = QAction("CREAM — Batch Exporter", ui.get_main_window())
    _action.triggered.connect(_window.show)
    ui.add_action(ui.ApplicationMenu.Window, _action)
    _window.show()


def close_plugin():
    global _window, _action
    import substance_painter.ui as ui
    if _window is not None:
        if _window.runner is not None:
            _window.cancel.set()
            raise RuntimeError("KR7: cancelamento solicitado; aguarde o lote encerrar antes de desativar o plugin.")
        if _window.saved is not None:
            _window.restore()
            if _window.saved is not None:
                raise RuntimeError("KR7: restaure o projeto antes de desativar o plugin.")
        _window.stop_updater()
        _window.pool.shutdown(wait=True)
        ui.delete_ui_element(_window)
        _window = None
    if _action is not None:
        ui.delete_ui_element(_action)
        _action = None
