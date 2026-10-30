from pathlib import Path
import tempfile
import unittest

from kr7_batch import core


class NamingTests(unittest.TestCase):
    def setUp(self):
        self.row = {'name': 'Joseph', 'stem': 'Joseph VIP', 'id': 'backer-7', 'line': 12}

    def test_patterns_and_zip_column_override(self):
        cases = {'{name}': 'Joseph VIP', 'Event - {name}': 'Event - Joseph VIP',
                 '{player} - {id} - {row}': 'Joseph - backer-7 - 12',
                 '$o$w$iEvent - {name}.zip': '$o$w$iEvent - Joseph VIP',
                 '{name}.ZIP': 'Joseph VIP', 'Same skin': 'Same skin', '{{Event}} - {player}': '{Event} - Joseph'}
        for pattern, result in cases.items():
            with self.subTest(pattern=pattern):
                self.assertEqual(core.format_skin_name(pattern, self.row), result)
        self.assertEqual(self.row['name'], 'Joseph')

    def test_unknown_unsafe_or_broken_patterns_fail(self):
        for pattern in ('', ' ', '{unknown}', '{name', '{name!r}', '{name:>20}', '{name.upper}',
                        '{name[0]}', '{}', '../{name}', 'C:\\{name}', 'Event/{name}',
                        'Event:{name}', 'a\n{name}', 'x' * 201, '.zip'):
            with self.subTest(pattern=pattern), self.assertRaises(ValueError):
                core.format_skin_name(pattern, self.row)

    def test_values_are_sanitized_and_not_reinterpreted(self):
        row = dict(self.row, id='../CON:Bad*', name='A/B', stem='{id}')
        self.assertEqual(core.format_skin_name('{id}', row), '.._CON_Bad_')
        self.assertEqual(core.format_skin_name('{player}', row), 'A_B')
        self.assertEqual(core.format_skin_name('{name}', row), '{id}')
        for pattern in ('CON', 'nul.txt', 'LPT1', 'aux'):
            self.assertTrue(core.format_skin_name(pattern, self.row).startswith('_'))
        self.assertEqual(len(core.format_skin_name('a' * 200, self.row)), 100)

    def test_generic_names_and_case_insensitive_collisions(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / 'JOSEPH.zip').write_bytes(b'existing')
            occupied = set()
            self.assertEqual(core.next_destination(folder, 'Joseph', occupied).name, 'Joseph 2.zip')
            self.assertEqual(core.next_destination(folder, 'Joseph', occupied).name, 'Joseph 3.zip')
            self.assertEqual(core.next_destination(folder, 'Event - Joseph', occupied).name, 'Event - Joseph.zip')
