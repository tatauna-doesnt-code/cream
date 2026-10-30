import copy
import unittest

from cream import core


class PlayerNameEditTests(unittest.TestCase):
    def setUp(self):
        self.row = {'name': 'Joseph', 'stem': 'Joseph', 'id': 'one', 'line': 2,
                    'colors': ['#FF8800', None, None]}

    def test_edit_updates_default_zip_name_and_reset_restores_exact_row(self):
        original = core.name_originals([self.row])[0]
        before = copy.deepcopy(self.row)
        edited, warnings = core.edited_player_name(self.row, original, 'Bompi')
        self.assertEqual(edited['name'], 'Bompi')
        self.assertEqual(edited['stem'], 'Bompi')
        self.assertEqual(warnings, [])
        self.assertEqual(self.row, before)
        self.assertEqual(edited['id'], before['id'])
        self.assertEqual(edited['colors'], before['colors'])
        self.assertNotEqual(core.fingerprint(edited), core.fingerprint(before))
        reset, _ = core.edited_player_name(edited, original, original['name'])
        self.assertEqual(reset, before)

    def test_explicit_zip_name_is_kept_even_if_it_matches_original_player(self):
        table = [['Player', 'ZIP'], ['Joseph', 'Joseph']]
        original = core.name_originals([self.row], table, 1)[0]
        edited, _ = core.edited_player_name(self.row, original, 'Bompi')
        self.assertEqual(edited['stem'], 'Joseph')
        self.assertEqual(core.format_skin_name('{name} - {player}', edited), 'Joseph - Bompi')
        original = core.name_originals([self.row], [['Player', 'ZIP'], ['Joseph', '']], 1)[0]
        self.assertEqual(core.edited_player_name(self.row, original, 'Bompi')[0]['stem'], 'Bompi')

    def test_manual_names_use_the_same_validation_and_unicode_limit(self):
        original = core.name_originals([self.row])[0]
        for invalid in ('', '  ', 'A\nB', '$oPlayer', '$F80Player'):
            with self.subTest(name=invalid), self.assertRaises(ValueError):
                core.edited_player_name(self.row, original, invalid)
        edited, warnings = core.edited_player_name(self.row, original, '😀' * 21)
        self.assertEqual(edited['name'], '😀' * 20)
        self.assertEqual(len(warnings), 1)
        edited, _ = core.edited_player_name(self.row, original, 'Jose\u0301ph')
        self.assertEqual(edited['name'], 'Joséph')

