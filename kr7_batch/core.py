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
import subprocess
import threading
import unicodedata
import uuid
import zipfile
import xml.etree.ElementTree as ET

MAPS = {"B": "BC1_UNORM", "R": "BC5_UNORM", "I": "BC3_UNORM",
        "N": "BC5_UNORM", "CoatR": "BC4_UNORM", "DirtMask": "BC4_UNORM", "AO": "BC1_UNORM"}
HEADERS = ["ativo", "id", "nome_player", "nome_arquivo", "cor_1", "cor_2", "cor_3"]
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


class Cancelled(Exception):
    pass


def check_cancel(cancel):
    if cancel.is_set():
        raise Cancelled("Cancelado pelo usuário.")


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
                    raise ValueError(f"XLSX: substitua a fórmula da célula {cell.attrib['r']} por um valor.")
                col = 0
                for letter in re.match(r"[A-Z]+", cell.attrib["r"])[0]:
                    col = col * 26 + ord(letter) - 64
                if col > 100:
                    raise ValueError("Use uma planilha simples com as colunas do modelo.")
                kind = cell.attrib.get("t", "")
                value = cell.findtext("m:v", "", NS)
                if kind == "s":
                    value = strings[int(value)]
                elif kind == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iterfind(".//m:t", NS))
                elif kind == "e":
                    raise ValueError(f"Erro de Excel na célula {cell.attrib['r']}.")
                values[col - 1] = value
            rows.append([values.get(i, "") for i in range(max(values, default=-1) + 1)])
        return rows


def read_rows(path):
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
        raise ValueError("Selecione CSV UTF-8 ou XLSX.")
    if not table:
        raise ValueError("Planilha vazia.")
    headers = [h.strip().lower() for h in table[0]]
    if "nome_player" not in headers or len(headers) != len(set(headers)):
        raise ValueError("Cabeçalhos inválidos: nome_player é obrigatório; colunas não podem se repetir.")
    rows, warnings, ids = [], [], set()
    for number, cells in enumerate(table[1:], 2):
        if not any(str(v).strip() for v in cells):
            continue
        record = dict(zip(headers, cells))
        active = record.get("ativo", "sim").strip().casefold()
        if active in ("não", "nao", "no", "false", "0", "n"):
            continue
        if active not in ("", "sim", "yes", "true", "1", "s"):
            raise ValueError(f"Linha {number}: ativo deve ser sim ou não.")
        name = unicodedata.normalize("NFC", record.get("nome_player", ""))
        if not name.strip() or any(unicodedata.category(c) == "Cc" for c in name):
            raise ValueError(f"Linha {number}: nome vazio ou com caracteres de controle.")
        if re.search(r"\$(?:[0-9a-fA-F]{3}|[oswniztlgmhpuOSWNIZTLGMHPU])", name):
            raise ValueError(f"Linha {number}: remova os códigos de formatação do Trackmania.")
        if len(name) > 20:
            warnings.append(f"Linha {number}: nome cortado para {name[:20]!r}.")
        name = name[:20]
        colors = []
        for index in range(1, 4):
            color = record.get(f"cor_{index}", "").strip()
            if color and not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                raise ValueError(f"Linha {number}: cor_{index} deve ser #RRGGBB ou vazia.")
            colors.append(color.upper() or None)
        identifier = record.get("id", "").strip() or str(number)
        if identifier in ids:
            raise ValueError(f"Linha {number}: id repetido ({identifier}). Nomes podem repetir; IDs devem ser únicos.")
        ids.add(identifier)
        filename = record.get("nome_arquivo", "").strip() or name
        clean = safe_stem(filename)
        if clean != filename:
            warnings.append(f"Linha {number}: nome de arquivo adaptado para {clean!r}.")
        rows.append({"line": number, "id": identifier, "name": name, "stem": clean, "colors": colors})
    if not rows:
        raise ValueError("Nenhuma linha ativa na planilha.")
    return rows, warnings


def safe_stem(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip().rstrip(". ")
    if not name:
        raise ValueError("O nome do arquivo ficou vazio após remover caracteres inválidos.")
    return name[:100].rstrip(". ")


def next_destination(folder, stem, occupied=None):
    occupied = occupied if occupied is not None else set()
    existing = {p.name.casefold() for p in Path(folder).glob("*")} if Path(folder).exists() else set()
    for index in range(1, 1000000):
        suffix = "" if index == 1 else f" {index}"
        name = f"KR7 - {stem}{suffix}.zip"
        if name.casefold() not in existing | occupied:
            occupied.add(name.casefold())
            return Path(folder) / name
    raise ValueError("Não foi possível reservar um nome de ZIP.")


def dimensions(texture_set, size):
    if size not in (1024, 2048, 4096):
        raise ValueError("Resolução inválida.")
    return (size // 4, size) if texture_set == "Wheels" else (size, size)


def inspect_base(path):
    with zipfile.ZipFile(path) as archive:
        names = []
        for item in archive.infolist():
            if item.is_dir():
                continue
            if item.filename != PurePosixPath(item.filename).name or "\\" in item.filename:
                raise ValueError("O ZIP base deve conter arquivos diretamente na raiz, sem subpastas.")
            names.append(item.filename.casefold())
        if len(names) != len(set(names)):
            raise ValueError("O ZIP base contém entradas duplicadas.")
        if not names:
            raise ValueError("O ZIP base está vazio.")
        return names


def validate_dds(path, suffix, width, height):
    with Path(path).open("rb") as handle:
        header = handle.read(148)
    if len(header) < 128 or header[:4] != b"DDS ":
        raise ValueError(f"DDS inválido: {path}")
    actual_h, actual_w = struct.unpack_from("<II", header, 12)
    mips = struct.unpack_from("<I", header, 28)[0]
    fourcc = header[84:88]
    expected = {"BC1_UNORM": (b"DXT1",), "BC3_UNORM": (b"DXT5",),
                "BC4_UNORM": (b"BC4U", b"ATI1"), "BC5_UNORM": (b"BC5U", b"ATI2")}[MAPS[suffix]]
    if (actual_w, actual_h) != (width, height) or mips not in (0, 1) or fourcc not in expected:
        raise ValueError(f"DDS fora da configuração: {Path(path).name}: {actual_w}×{actual_h}, {fourcc!r}, mips={mips}")
    block_bytes = 8 if suffix in ("B", "AO", "CoatR", "DirtMask") else 16
    expected_bytes = 128 + ((width + 3) // 4) * ((height + 3) // 4) * block_bytes
    if Path(path).stat().st_size != expected_bytes:
        raise ValueError(f"Tamanho DDS incorreto ou arquivo incompleto: {path}")


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
                    raise Cancelled("Conversão cancelada.")
        if process.returncode:
            raise RuntimeError(data.decode("utf-8", errors="replace")[-4000:])
        check_cancel(cancel)
        candidates = [p for p in output.iterdir() if p.stem.casefold() == Path(source).stem.casefold() and p.suffix.lower() == ".dds"]
        if len(candidates) != 1:
            raise RuntimeError("O conversor não produziu o DDS esperado.")
        validate_dds(candidates[0], suffix, width, height)
        if suffix == "N":
            invert_bc5_green(candidates[0], cancel)
            validate_dds(candidates[0], suffix, width, height)
        return candidates[0]
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def _index_table(mapping):
    return tuple(sum(mapping[(value >> bit) & 7] << bit for bit in (0, 3, 6, 9))
                 for value in range(4096))


_BC4_EIGHT = _index_table((1, 0, 7, 6, 5, 4, 3, 2))
_BC4_SIX = _index_table((1, 0, 5, 4, 3, 2, 7, 6))


def invert_bc5_green(path, cancel):
    """Invert green AFTER DDS generation, without decompressing/recompressing BC5.

    BC5 stores red then green as independent 8-byte BC4 UNORM blocks. Reflect and
    swap the green endpoints, and remap all sixteen 3-bit indices. Both BC4 modes
    are preserved. Red blocks and the DDS header remain bit-for-bit identical.
    GPU integer interpolation can differ by one LSB when rounding complements.
    """
    path = Path(path)
    data = bytearray(path.read_bytes())
    if len(data) < 128 or data[:4] != b"DDS " or data[84:88] not in (b"BC5U", b"ATI2"):
        raise ValueError("A inversão pós-conversão requer DDS BC5 UNORM com cabeçalho legado.")
    height, width = struct.unpack_from("<II", data, 12)
    mips = struct.unpack_from("<I", data, 28)[0]
    if mips not in (0, 1) or len(data) != 128 + ((width + 3) // 4) * ((height + 3) // 4) * 16:
        raise ValueError("DDS BC5 incompleto ou com mipmaps não suportados.")
    temporary = path.with_name(path.name + ".green-" + uuid.uuid4().hex + ".tmp")
    try:
        for offset in range(136, len(data), 16):
            if (offset - 136) % 65536 == 0:
                check_cancel(cancel)
            high, low = data[offset], data[offset + 1]
            table = _BC4_EIGHT if high > low else _BC4_SIX
            indices = int.from_bytes(data[offset + 2:offset + 8], "little")
            mapped = (table[indices & 4095] | (table[(indices >> 12) & 4095] << 12)
                      | (table[(indices >> 24) & 4095] << 24) | (table[indices >> 36] << 36))
            data[offset:offset + 2] = bytes((255 - low, 255 - high))
            data[offset + 2:offset + 8] = mapped.to_bytes(6, "little")
        check_cancel(cancel)
        with temporary.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        check_cancel(cancel)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build_zip(base, replacements, destination, cancel):
    """Never modify base or an existing final. Publish with a no-clobber rename on Windows."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / (".kr7-" + uuid.uuid4().hex + ".partial")
    replacement_names = {name.casefold() for name in replacements}
    if len(replacement_names) != len(replacements):
        raise ValueError("Texturas de saída duplicadas.")
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
