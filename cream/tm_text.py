"""Trackmania text styles, independent of Qt/Painter.

Reference: https://doc.maniaplanet.com/client/text-formatting
Width reset $m and repeated style toggles follow the ManiaPlanet text conventions.
Only text styling is emitted; links and scope delimiters are not filename controls.
"""
from dataclasses import dataclass, replace
import re


@dataclass(frozen=True)
class Style:
    bold: bool = False
    italic: bool = False
    uppercase: bool = False
    shadow: bool = False
    width: str = "normal"
    color: str = ""  # Empty = default, RGB = literal, primary/secondary = per-row color.


DEFAULT = Style()
TOGGLES = {"o": "bold", "i": "italic", "t": "uppercase", "s": "shadow"}
WIDTHS = {"m": "normal", "n": "narrow", "w": "wide"}


def color3(value):
    """Validate manual input strictly: exactly three hex digits, optional # prefix."""
    value = value.strip().removeprefix("#")
    if not re.fullmatch(r"[0-9a-fA-F]{3}", value):
        raise ValueError("Enter exactly 3 hexadecimal digits, such as F80. Trackmania does not use 6-digit text colors.")
    return value.upper()


def from_hex6(value):
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError("A skin color must be #RRGGBB.")
    return "".join(format(round(int(value[i:i + 2], 16) / 17), "X") for i in (1, 3, 5))


def expand_color(value):
    return "#" + "".join(c * 2 for c in color3(value))


def parse(text, template=False, final=False):
    """Return (text, Style) runs. Unknown codes remain literal; $$ is escaped first."""
    runs, buffer, style, index = [], [], DEFAULT, 0
    def flush():
        if buffer:
            runs.append(("".join(buffer), style))
            buffer.clear()
    while index < len(text):
        if template and text[index:index + 2] in ("{{", "}}"):
            buffer.append(text[index:index + 2])
            index += 2
            continue
        dynamic = next((key for key in ("primary", "secondary")
                        if template and text.startswith("{" + key + "}", index)), None)
        if dynamic:
            flush()
            style = replace(style, color=dynamic)
            index += len(dynamic) + 2
            continue
        if text.startswith("$$", index):
            buffer.append("$")
            index += 2
            continue
        if text[index] == "$" and index + 1 < len(text):
            code = text[index + 1].lower()
            rgb = text[index + 1:index + 4]
            if len(rgb) == 3 and re.fullmatch(r"[0-9a-fA-F]{3}", rgb):
                flush()
                style = replace(style, color=rgb.upper())
                index += 4
                continue
            if code in TOGGLES or code in WIDTHS or code in ("g", "z"):
                flush()
                if code in TOGGLES:
                    key = TOGGLES[code]
                    style = replace(style, **{key: not getattr(style, key)})
                elif code in WIDTHS:
                    style = replace(style, width=WIDTHS[code])
                else:
                    style = DEFAULT if code == "z" else replace(style, color="")
                index += 2
                continue
        buffer.append(text[index])
        index += 1
    flush()
    if final:
        runs.append(("", style))
    return runs


def transition(previous, current):
    if previous == current:
        return ""
    if current == DEFAULT:
        return "$z"
    output = ""
    for code, field in TOGGLES.items():
        if getattr(previous, field) != getattr(current, field):
            output += "$" + code
    if previous.width != current.width:
        output += "$" + {v: k for k, v in WIDTHS.items()}[current.width]
    if previous.color != current.color:
        output += ("{" + current.color + "}" if current.color in ("primary", "secondary")
                   else "$" + color3(current.color) if current.color else "$g")
    return output


def serialize(runs):
    previous, output = DEFAULT, []
    for text, style in runs:
        if not text:
            continue
        output.append(transition(previous, style))
        output.append(text.replace("$", "$$"))
        previous = style
    return "".join(output)


def truncate(text, limit):
    """Do not split a $RGB, style code, or escaped dollar at the filename limit."""
    index = 0
    while index < len(text) and index < limit:
        size = 1
        if text[index] == "$" and index + 1 < len(text):
            if re.fullmatch(r"[0-9a-fA-F]{3}", text[index + 1:index + 4]):
                size = 4
            elif text[index + 1].lower() in set(TOGGLES) | set(WIDTHS) | {"g", "z", "$"}:
                size = 2
        if index + size > limit:
            break
        index += size
    return text[:index]
