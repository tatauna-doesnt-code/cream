"""Painter capabilities, kept independent of Qt for startup and testing."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Capabilities:
    version: tuple

    @property
    def version_text(self):
        return '.'.join(map(str, self.version[:3]))

    @property
    def export(self):
        return self.version >= (9, 0, 0)

    @property
    def customization(self):
        return self.version >= (10, 0, 0)

    @property
    def qt6(self):
        return self.version >= (10, 1, 0)

    @property
    def warning(self):
        if not self.export:
            return ('CREAM requires Painter 9.0.0 or later. Export and skin customization '
                    'are disabled on this version.')
        if not self.customization:
            return ('Export-only mode: Painter ' + self.version_text + ' does not provide the layer-editing API. '
                    'Changing text on the car, changing skin colors, Painter previews and restoring '
                    'customization are disabled. Names and colors can still style ZIP filenames. '
                    'Texture export, DDS conversion and ZIP packaging remain available. '
                    'Use Painter 10.1.2 or later for the full, more stable experience.')
        if self.version < (10, 1, 2):
            return ('Painter ' + self.version_text + ' supports customization, but older builds have '
                    'layer-stack API issues. Upgrade to at least Painter 10.1.2 for a more stable '
                    'experience, especially with effects on group layers.')
        return ''


def current():
    import substance_painter.application as application
    return Capabilities(tuple(application.version_info()[:3]))


def texture_set_name(texture_set):
    """name() became the name property in Painter 11.0."""
    name = texture_set.name
    return str(name() if callable(name) else name)
