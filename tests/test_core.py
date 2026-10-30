import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cream import core
from PIL import Image

TEXCONV = Path(__file__).resolve().parents[1] / 'cream/bin/texconv.exe'


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def sheet(self, rows, delimiter=';'):
        path = self.root / 'input.csv'
        with path.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(core.HEADERS)
            writer.writerows(rows)
        return path

    def test_unicode_colors_truncation_duplicates(self):
        path = self.sheet([['sim','1','Jóséph ABCDEFGHIJKLMNOPQRSTUVWXYZ','','#00ffAA','',''],
                           ['sim','2','Joseph','','','#FF0000',''],['sim','3','Joseph','','#00FF00','','']])
        rows, warnings = core.read_rows(path)
        self.assertEqual(len(rows[0]['name']), 20)
        self.assertEqual(rows[0]['colors'], ['#00FFAA', None, None])
        occupied = set()
        self.assertEqual(core.next_destination(self.root, core.format_skin_name('CUP - {name}', rows[1]), occupied).name, 'CUP - Joseph.zip')
        self.assertEqual(core.next_destination(self.root, core.format_skin_name('CUP - {name}', rows[2]), occupied).name, 'CUP - Joseph 2.zip')
        self.assertEqual(len(warnings), 1)

    def test_invalid_color_or_formatting_fails(self):
        for name, color in [('Player','#GG0011'), ('$oPlayer','#FFFFFF')]:
            with self.assertRaises(ValueError):
                core.read_rows(self.sheet([['sim','1',name,'',color,'','']]))

    def test_inactive_and_duplicate_ids(self):
        path = self.sheet([['não','1','Player','','INVALID','',''], ['sim','2','Player','','','','']])
        self.assertEqual(len(core.read_rows(path)[0]), 1)
        with self.assertRaises(ValueError):
            core.read_rows(self.sheet([['sim','1','A','','','',''], ['sim','1','B','','','','']]))

    def test_filename_collision_windows_rules(self):
        (self.root / 'CUP - JOSEPH.zip').write_bytes(b'existing')
        self.assertEqual(core.next_destination(self.root, 'CUP - Joseph').name, 'CUP - Joseph 2.zip')
        self.assertEqual(core.safe_stem('A/B:*? '), 'A_B___')

    def test_zip_replace_preserve_and_no_clobber(self):
        base = self.root / 'base.zip'
        with zipfile.ZipFile(base, 'w') as z:
            z.writestr('Skin_B.dds', b'old')
            z.writestr('Details_N.dds', b'unchanged')
        before = base.read_bytes()
        replacement = self.root / 'new.dds'
        replacement.write_bytes(b'new color')
        final = self.root / 'final.zip'
        core.build_zip(base, {'skin_b.dds': replacement}, final, threading.Event())
        with zipfile.ZipFile(final) as z:
            self.assertEqual(len(z.namelist()), 2)
            self.assertEqual(z.read('skin_b.dds'), b'new color')
            self.assertEqual(z.read('Details_N.dds'), b'unchanged')
        final_before = final.read_bytes()
        with self.assertRaises(FileExistsError):
            core.build_zip(base, {}, final, threading.Event())
        self.assertEqual(final.read_bytes(), final_before)
        self.assertEqual(base.read_bytes(), before)
        self.assertFalse(list(self.root.glob('*.partial')))

    def test_cancel_mid_zip_does_not_publish(self):
        base = self.root / 'base.zip'
        with zipfile.ZipFile(base, 'w') as z:
            z.writestr('Skin_B.dds', b'A' * (5 * 1024 * 1024))
        class CancelAfterChecks:
            count = 0
            def is_set(self):
                self.count += 1
                return self.count > 3
        final = self.root / 'final.zip'
        with self.assertRaises(core.Cancelled):
            core.build_zip(base, {}, final, CancelAfterChecks())
        self.assertFalse(final.exists())
        self.assertFalse(list(self.root.glob('*.partial')))

    def test_xlsx_inline_shared_and_formulas(self):
        path = self.root / 'input.xlsx'
        main = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('xl/workbook.xml', f'<workbook xmlns="{main}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Backers" r:id="rId1"/></sheets></workbook>')
            z.writestr('xl/_rels/workbook.xml.rels', '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            z.writestr('xl/sharedStrings.xml', f'<sst xmlns="{main}"><si><t>nome_player</t></si></sst>')
            z.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{main}"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>Álvaro</t></is></c></row></sheetData></worksheet>')
        self.assertEqual(core.read_rows(path)[0][0]['name'], 'Álvaro')
        bad = self.root / 'formula.xlsx'
        with zipfile.ZipFile(path) as src, zipfile.ZipFile(bad, 'w') as dst:
            for name in src.namelist():
                data = src.read(name)
                if name.endswith('sheet1.xml'):
                    data = data.replace(b'<is>', b'<f>1+1</f><is>')
                dst.writestr(name, data)
        with self.assertRaisesRegex(ValueError, 'formula'):
            core.read_rows(bad)

    def test_real_dds_all_formats_and_wheels(self):
        image = self.root / 'Skin.png'
        Image.new('RGBA', (16, 64), (128, 64, 192, 128)).save(image)
        for suffix in core.MAPS:
            with self.subTest(suffix=suffix):
                output = self.root / suffix
                result = core.convert(TEXCONV, image, output, suffix, 16, 64, threading.Event())
                core.validate_dds(result, suffix, 16, 64)
                self.assertEqual(result.read_bytes()[84:88],
                                 {'B': b'DXT1', 'R': b'BC5U', 'I': b'DXT5', 'N': b'BC5U',
                                  'CoatR': b'BC4U', 'DirtMask': b'BC4U', 'AO': b'DXT1'}[suffix])
        self.assertEqual(core.dimensions('Wheels', 2048), (512, 2048))
        self.assertEqual(core.dimensions('Skin', 2048), (2048, 2048))

    def test_header_normalization_preserves_payload_and_is_idempotent(self):
        source = self.root / 'Skin.png'
        Image.new('RGB', (16, 16), (128, 64, 192)).save(source)
        for suffix, alias, expected in [('CoatR', b'ATI1', b'BC4U'), ('R', b'ATI2', b'BC5U')]:
            output = self.root / suffix
            output.mkdir()
            subprocess.run(core.conversion_args(TEXCONV, source, output, suffix), check=True, capture_output=True)
            path = output / 'Skin.dds'
            original = path.read_bytes()
            self.assertEqual(original[84:88], alias)
            with self.assertRaises(ValueError):
                core.validate_dds(path, suffix, 16, 16)
            core.normalize_dds_header(path, suffix)
            patched = path.read_bytes()
            self.assertEqual(patched, original[:84] + expected + original[88:])
            core.normalize_dds_header(path, suffix)
            self.assertEqual(path.read_bytes(), patched)
            core.validate_dds(path, suffix, 16, 16)

    def test_header_normalization_rejects_incompatible_formats(self):
        for fourcc in (b'BC4S', b'BC5S', b'DX10', b'DXT1', b'ATI1'):
            path = self.root / 'wrong.dds'
            data = b'DDS ' + bytes(80) + fourcc + bytes(48)
            path.write_bytes(data)
            with self.assertRaises(ValueError):
                core.normalize_dds_header(path, 'R')
            self.assertEqual(path.read_bytes(), data)

    def test_real_normal_green_preserved(self):
        source = self.root / 'Skin_N.png'
        Image.new('RGB', (4, 4), (128, 64, 255)).save(source)
        dds = core.convert(TEXCONV, source, self.root / 'compressed', 'N', 4, 4, threading.Event())
        decoded = self.root / 'decoded'
        decoded.mkdir()
        subprocess.run([str(TEXCONV), '-nologo', '-y', '-ft', 'png', '-f', 'R8G8B8A8_UNORM', '-o', str(decoded), str(dds)], check=True, capture_output=True)
        pixel = Image.open(decoded / 'Skin_N.png').getpixel((0, 0))
        self.assertLessEqual(abs(pixel[0] - 128), 2)
        self.assertLessEqual(abs(pixel[1] - 64), 2)

    def test_real_emissive_rgb_survives_zero_alpha(self):
        source = self.root / 'Skin_I.png'
        Image.new('RGBA', (4, 4), (200, 100, 50, 0)).save(source)
        dds = core.convert(TEXCONV, source, self.root / 'compressed', 'I', 4, 4, threading.Event())
        decoded = self.root / 'decoded'
        decoded.mkdir()
        subprocess.run([str(TEXCONV), '-nologo', '-y', '-ft', 'png', '-sepalpha', '-f', 'R8G8B8A8_UNORM', '-o', str(decoded), str(dds)], check=True, capture_output=True)
        pixel = Image.open(decoded / 'Skin_I.png').getpixel((0, 0))
        self.assertGreater(pixel[0], 185)
        self.assertEqual(pixel[3], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
