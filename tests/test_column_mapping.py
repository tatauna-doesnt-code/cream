import csv
from pathlib import Path
import tempfile
import unittest

from kr7_batch import core


class ColumnMappingTests(unittest.TestCase):
    def test_custom_csv_headers_and_reordered_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "backers.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.writer(handle, delimiter=";")
                writer.writerows([
                    ["Discord", "Accent", "Player nickname", "Main color", "Export?", "ZIP", "Key"],
                    ["ignored", "#ffaa00", "Jóséph", "#00ffAA", "yes", "Custom ZIP", "backer-1"],
                    ["ignored", "INVALID", "Skipped", "INVALID", "no", "", "backer-1"],
                ])
            rows, warnings = core.read_rows(path, {
                "nome_player": 2, "cor_1": 3, "cor_2": 1, "ativo": 4, "nome_arquivo": 5, "id": 6})
            self.assertEqual(warnings, [])
            self.assertEqual(rows, [{"line": 2, "id": "backer-1", "name": "Jóséph",
                                     "stem": "Custom ZIP", "colors": ["#00FFAA", "#FFAA00", None]}])

    def test_duplicate_and_blank_headers_use_positions(self):
        table = [["Name", "Color", "Color", ""], ["Joseph", "INVALID", "#123456", "extra"]]
        rows, _ = core.rows_from_table(table, {"nome_player": 0, "cor_1": 2})
        self.assertEqual(rows[0]["colors"], ["#123456", None, None])

    def test_omitted_columns_and_short_rows_keep_defaults(self):
        rows, _ = core.rows_from_table([["Nickname", "Color"], ["Joseph"]],
                                      {"nome_player": 0, "cor_1": 1})
        self.assertEqual(rows[0], {"line": 2, "id": "2", "name": "Joseph", "stem": "Joseph",
                                   "colors": [None, None, None]})

    def test_missing_or_invalid_name_column_fails(self):
        for mapping in ({}, {"nome_player": -1}, {"nome_player": 1}, {"nome_player": "0"},
                        {"nome_player": True}, {"nome_player": 0, "unknown": 0}):
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                core.rows_from_table([["Nickname"], ["Joseph"]], mapping)

    def test_suggestions_are_unique_and_case_insensitive(self):
        self.assertEqual(core.suggest_columns([" Nome_Player ", "COR_1", "cor_2", "cor_2"]),
                         dict(zip(core.HEADERS, [None, None, 0, None, 1, None, None])))

    def test_mapped_values_still_validate(self):
        for name, color in [("", "#123456"), ("Player", "bad"), ("$oPlayer", "")]:
            with self.subTest(name=name, color=color), self.assertRaises(ValueError):
                core.rows_from_table([["Nickname", "Paint"], [name, color]],
                                     {"nome_player": 0, "cor_2": 1})

    def test_xlsx_can_map_custom_header(self):
        # The XLSX reader is unchanged; the same column positions feed the parser.
        import zipfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.xlsx"
            ns = core.NS["m"]
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("xl/workbook.xml", f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Backers" r:id="rId1"/></sheets></workbook>')
                archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
                archive.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="{ns}"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Nickname</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>Joseph</t></is></c></row></sheetData></worksheet>')
            self.assertEqual(core.read_rows(path, {"nome_player": 0})[0][0]["name"], "Joseph")
