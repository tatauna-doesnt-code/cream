"""KR7 file operations. No Painter imports; all outputs are transactional."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import string
import subprocess
import threading
import unicodedata
import uuid
import zipfile
import xml.etree.ElementTree as ET

MAPS = {"B": "BC1_UNORM", "R": "BC5_UNORM", "I": "BC3_UNORM",
        "N": "BC5_UNORM", "CoatR": "BC4_UNORM", "DirtMask": "BC4_UNORM", "AO": "BC1_UNORM"}
DDS_FOURCC = {"BC1_UNORM": b"DXT1", "BC3_UNORM": b"DXT5",
              "BC4_UNORM": b"BC4U", "BC5_UNORM": b"BC5U"}
HEADERS = ["ativo", "id", "nome_player", "nome_arquivo", "cor_1", "cor_2", "cor_3"]
DEFAULT_NAME_PATTERN = "{name}"
LEGACY_NAME_PATTERN = "KR7 - {name}"
NAME_FIELDS = {"name", "player", "id", "row"}
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


class Cancelled(Exception):
    pass


def check_cancel(cancel):
    if cancel.is_set():
        raise Cancelled("Cancelled by the user.")


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def read_xlsx(path):
    """Read plain values in Backers (or the first sheet), without dependencies.

    Formula cells are rejected rather than trusting stale cached values.
    """
    with zipfile.ZipFile(path) as book:
        strings = []
        if "xl/sharedStrings.xml" in book.namelist():
            root = ET.fromstring(book.read("xl/sharedStrings.xml"))
            strings = ["".join(t.text or "" for t in si.iterfind(".//m:t", NS)) for si in root]
        workbook = ET.fromstring(book.read("xl/workbook.xml"))
        sheets = list(workbook.find("m:sheets", NS))
        sheet = next((s for s in sheets if s.attrib["name"].casefold() == "backers"), sheets[0])
        rel_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        rels = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        target = next(r.attrib["Target"] for r in rels if r.attrib["Id"] == rel_id)
        target = target.lstrip("/") if target.startswith("/") else "xl/" + target
        root = ET.fromstring(book.read(target))
        rows = []
        for row in root.findall("m:sheetData/m:row", NS):
            values = {}
            for cell in row.findall("m:c", NS):
                if cell.find("m:f", NS) is not None:
                    raise ValueError(f"XLSX: replace the formula in cell {cell.attrib['r']} with a value.")
                col = 0
                for letter in re.match(r"[A-Z]+", cell.attrib["r"])[0]:
                    col = col * 26 + ord(letter) - 64
                if col > 100:
                    raise ValueError("Use a simple spreadsheet with no more than 100 columns.")
                kind = cell.attrib.get("t", "")
                value = cell.findtext("m:v", "", NS)
                if kind == "s":
                    value = strings[int(value)]
                elif kind == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iterfind(".//m:t", NS))
                elif kind == "e":
                    raise ValueError(f"Excel error in cell {cell.attrib['r']}.")
                values[col - 1] = value
            rows.append([values.get(i, "") for i in range(max(values, default=-1) + 1)])
        return rows


def read_table(path):
    """Read a header row and raw cells, without requiring CREAM column names."""
    path = Path(path)
    if path.suffix.lower() == ".xlsx":
        table = read_xlsx(path)
    elif path.suffix.lower() == ".csv":
        content = path.read_text(encoding="utf-8-sig")
        try:
            dialect = csv.Sniffer().sniff(content[:8192], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        table = list(csv.reader(io.StringIO(content), dialect))
    else:
        raise ValueError("Select a UTF-8 CSV or XLSX file.")
    if not table:
        raise ValueError("The spreadsheet is empty.")
    return table


def suggest_columns(headers):
    """Use only unambiguous original headers; other columns need user selection."""
    normalized = [str(h).strip().casefold() for h in headers]
    return {field: normalized.index(field) if normalized.count(field) == 1 else None
            for field in HEADERS}


def validate_columns(headers, mapping):
    unknown = set(mapping) - set(HEADERS)
    if unknown:
        raise ValueError("Unknown import fields: " + ", ".join(sorted(unknown)))
    result = {field: mapping.get(field) for field in HEADERS}
    for field, index in result.items():
        if index is not None and (type(index) is not int or not 0 <= index < len(headers)):
            raise ValueError(f"Invalid column for {field}. Select the columns again.")
    if result["nome_player"] is None:
        raise ValueError("Select the column containing the player name.")
    return result


def read_rows(path, mapping=None):
    return rows_from_table(read_table(path), mapping)


def rows_from_table(table, mapping=None):
    if not table:
        raise ValueError("The spreadsheet is empty.")
    mapping = validate_columns(table[0], suggest_columns(table[0]) if mapping is None else mapping)
    rows, warnings, ids = [], [], set()
    for number, cells in enumerate(table[1:], 2):
        if not any(str(v).strip() for v in cells):
            continue
        record = {field: str(cells[index]) if index is not None and index < len(cells) else ""
                  for field, index in mapping.items()}
        active = record.get("ativo", "sim").strip().casefold()
        if active in ("não", "nao", "no", "false", "0", "n"):
            continue
        if active not in ("", "sim", "yes", "true", "1", "s"):
            raise ValueError(f"Row {number}: active must be yes or no.")
        name = unicodedata.normalize("NFC", record.get("nome_player", ""))
        if not name.strip() or any(unicodedata.category(c) == "Cc" for c in name):
            raise ValueError(f"Row {number}: name is empty or contains control characters.")
        if re.search(r"\$(?:[0-9a-fA-F]{3}|[oswniztlgmhpuOSWNIZTLGMHPU])", name):
            raise ValueError(f"Row {number}: remove Trackmania formatting codes.")
        if len(name) > 20:
            warnings.append(f"Row {number}: name truncated to {name[:20]!r}.")
        name = name[:20]
        colors = []
        for index in range(1, 4):
            color = record.get(f"cor_{index}", "").strip()
            if color and not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                raise ValueError(f"Row {number}: color_{index} must be #RRGGBB or blank.")
            colors.append(color.upper() or None)
        identifier = record.get("id", "").strip() or str(number)
        if identifier in ids:
            raise ValueError(f"Row {number}: duplicate ID ({identifier}). Names may repeat; IDs must be unique.")
        ids.add(identifier)
        filename = record.get("nome_arquivo", "").strip() or name
        clean = safe_stem(filename)
        if clean != filename:
            warnings.append(f"Row {number}: filename adjusted to {clean!r}.")
        rows.append({"line": number, "id": identifier, "name": name, "stem": clean, "colors": colors})
    if not rows:
        raise ValueError("The spreadsheet has no active rows.")
    return rows, warnings


def safe_stem(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip().rstrip(". ")
    if not name:
        raise ValueError("The filename is empty after removing invalid characters.")
    name = name[:100].rstrip(". ")
    reserved = {"CON", "PRN", "AUX", "NUL", *("COM" + str(i) for i in range(1, 10)),
                *("LPT" + str(i) for i in range(1, 10))}
    if name.split(".")[0].upper() in reserved:
        name = "_" + name
    return name[:100].rstrip(". ")


def validate_name_pattern(pattern):
    if not isinstance(pattern, str) or not pattern.strip():
        raise ValueError("Enter a ZIP name pattern, such as {name} or Event - {name}.")
    if len(pattern) > 200:
        raise ValueError("The ZIP name pattern must not exceed 200 characters.")
    try:
        parts = list(string.Formatter().parse(pattern))
    except ValueError as exc:
        raise ValueError("Invalid braces in the ZIP name pattern.") from exc
    for literal, field, spec, conversion in parts:
        if re.search(r'[<>:"/\\|?*\x00-\x1f]', literal):
            raise ValueError("The ZIP name pattern cannot contain folders or invalid filename characters.")
        if field is not None and (field not in NAME_FIELDS or spec or conversion is not None):
            raise ValueError("Use only {name}, {player}, {id} and {row}, without format modifiers.")
    return pattern


def format_skin_name(pattern, row):
    """Produce a safe filename stem. Never alter the name applied to the project."""
    validate_name_pattern(pattern)
    values = {"name": row["stem"], "player": row["name"], "id": row["id"], "row": str(row["line"])}
    name = pattern.format_map(values).strip()
    if name.lower().endswith(".zip"):
        name = name[:-4]
    return safe_stem(name)


def next_destination(folder, stem, occupied=None):
    stem = safe_stem(stem)
    occupied = occupied if occupied is not None else set()
    existing = {p.name.casefold() for p in Path(folder).glob("*")} if Path(folder).exists() else set()
    for index in range(1, 1000000):
        suffix = "" if index == 1 else f" {index}"
        name = f"{stem}{suffix}.zip"
        if name.casefold() not in existing | occupied:
            occupied.add(name.casefold())
            return Path(folder) / name
    raise ValueError("Could not reserve a ZIP filename.")


def dimensions(texture_set, size):
    if size not in (1024, 2048, 4096):
        raise ValueError("Invalid resolution.")
    return (size // 4, size) if texture_set == "Wheels" else (size, size)


def inspect_base(path):
    with zipfile.ZipFile(path) as archive:
        names = []
        for item in archive.infolist():
            if item.is_dir():
                continue
            if item.filename != PurePosixPath(item.filename).name or "\\" in item.filename:
                raise ValueError("The base ZIP must contain files directly at its root, without subfolders.")
            names.append(item.filename.casefold())
        if len(names) != len(set(names)):
            raise ValueError("The base ZIP contains duplicate entries.")
        if not names:
            raise ValueError("The base ZIP is empty.")
        return names


def validate_dds(path, suffix, width, height):
    with Path(path).open("rb") as handle:
        header = handle.read(148)
    if len(header) < 128 or header[:4] != b"DDS ":
        raise ValueError(f"Invalid DDS: {path}")
    actual_h, actual_w = struct.unpack_from("<II", header, 12)
    mips = struct.unpack_from("<I", header, 28)[0]
    fourcc = header[84:88]
    expected = DDS_FOURCC[MAPS[suffix]]
    if (actual_w, actual_h) != (width, height) or mips not in (0, 1) or fourcc != expected:
        raise ValueError(f"DDS does not match the configuration: {Path(path).name}: {actual_w}×{actual_h}, {fourcc!r}, mips={mips}")
    block_bytes = 8 if suffix in ("B", "AO", "CoatR", "DirtMask") else 16
    expected_bytes = 128 + ((width + 3) // 4) * ((height + 3) // 4) * block_bytes
    if Path(path).stat().st_size != expected_bytes:
        raise ValueError(f"Incorrect DDS size or incomplete file: {path}")


def normalize_dds_header(path, suffix):
    """Use the TM2020-compatible unsigned BC4/5 identifiers, without recompression.

    texconv -dx9 writes ATI1/ATI2 for BC4/BC5. The working skin and in-game
    verification require BC4U/BC5U. Only the four FourCC bytes may change.
    Signed formats and DX10 headers are never relabeled.
    """
    expected = DDS_FOURCC[MAPS[suffix]]
    alias = {b"BC4U": b"ATI1", b"BC5U": b"ATI2"}.get(expected)
    with Path(path).open("r+b") as handle:
        header = handle.read(128)
        if len(header) != 128 or header[:4] != b"DDS ":
            raise ValueError(f"Invalid DDS: {path}")
        if header[84:88] == expected:
            return
        if alias is None or header[84:88] != alias:
            raise ValueError(f"Unexpected DDS format: {header[84:88]!r}; expected {expected!r}.")
        handle.seek(84)
        handle.write(expected)


def conversion_args(texconv, source, output, suffix):
    args = [str(texconv), "-nologo", "-y", "-f", MAPS[suffix], "-m", "1", "-dx9",
            "--ignore-srgb", "-sepalpha", "-o", str(output)]
    if suffix in ("B", "AO"):
        args.extend(["--swizzle", "rgb1"])
    args.append(str(source))
    return args


def convert(texconv, source, output, suffix, width, height, cancel):
    check_cancel(cancel)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    # communicate with polling avoids a full pipe deadlock and allows cancellation.
    process = subprocess.Popen(conversion_args(texconv, source, output, suffix),
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        while True:
            try:
                data, _ = process.communicate(timeout=0.2)
                break
            except subprocess.TimeoutExpired:
                if cancel.is_set():
                    process.terminate()
                    try:
                        process.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()
                    raise Cancelled("Conversion cancelled.")
        if process.returncode:
            raise RuntimeError(data.decode("utf-8", errors="replace")[-4000:])
        check_cancel(cancel)
        candidates = [p for p in output.iterdir() if p.stem.casefold() == Path(source).stem.casefold() and p.suffix.lower() == ".dds"]
        if len(candidates) != 1:
            raise RuntimeError("The converter did not produce the expected DDS.")
        normalize_dds_header(candidates[0], suffix)
        validate_dds(candidates[0], suffix, width, height)
        return candidates[0]
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def build_zip(base, replacements, destination, cancel):
    """Never modify base or an existing final. Publish with a no-clobber rename on Windows."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / (".kr7-" + uuid.uuid4().hex + ".partial")
    replacement_names = {name.casefold() for name in replacements}
    if len(replacement_names) != len(replacements):
        raise ValueError("Duplicate output textures.")
    try:
        with zipfile.ZipFile(base) as original, zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as target:
            for entry in original.infolist():
                check_cancel(cancel)
                if entry.is_dir() or entry.filename.casefold() in replacement_names:
                    continue
                with original.open(entry) as src, target.open(entry.filename, "w") as dst:
                    while True:
                        check_cancel(cancel)
                        data = src.read(1024 * 1024)
                        if not data:
                            break
                        dst.write(data)
            for name, path in replacements.items():
                check_cancel(cancel)
                with Path(path).open("rb") as src, target.open(name, "w") as dst:
                    while True:
                        check_cancel(cancel)
                        data = src.read(1024 * 1024)
                        if not data:
                            break
                        dst.write(data)
        with zipfile.ZipFile(temporary) as archive:
            for entry in archive.infolist():
                with archive.open(entry) as handle:
                    while handle.read(1024 * 1024):
                        check_cancel(cancel)
        with temporary.open("r+b") as handle:
            os.fsync(handle.fileno())
        check_cancel(cancel)
        if os.name == "nt":
            os.rename(temporary, destination)  # Windows fails if destination exists.
        else:
            os.link(temporary, destination)  # no-clobber publish for tests on POSIX.
            temporary.unlink()
        return str(destination)
    finally:
        temporary.unlink(missing_ok=True)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
