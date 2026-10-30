from dataclasses import replace
import unittest

from kr7_batch import core, tm_text


class TMTextTests(unittest.TestCase):
    def test_manual_colors_are_exactly_three_digits(self):
        self.assertEqual(tm_text.color3('#f80'), 'F80')
        self.assertEqual(tm_text.expand_color('F80'), '#FF8800')
        for invalid in ('FF8800', '#FF8800', 'F', 'FFFF', 'G00', '$F80', 'RGBA'):
            with self.subTest(color=invalid), self.assertRaises(ValueError):
                tm_text.color3(invalid)

    def test_skin_colors_are_quantized_to_12_bits(self):
        self.assertEqual(tm_text.from_hex6('#FF8800'), 'F80')
        self.assertEqual(tm_text.from_hex6('#0088FF'), '08F')
        self.assertEqual(tm_text.from_hex6('#123456'), '135')
        self.assertEqual(tm_text.from_hex6('#FFFFFF'), 'FFF')

    def test_all_style_codes_toggles_and_resets(self):
        runs = tm_text.parse('$o$i$t$s$w$f80A$o$i$t$s$nB$m$gC$zD')
        self.assertEqual(runs[0], ('A', tm_text.Style(True, True, True, True, 'wide', 'F80')))
        self.assertEqual(runs[1], ('B', tm_text.Style(width='narrow', color='F80')))
        self.assertEqual(runs[2], ('C', tm_text.DEFAULT))
        self.assertEqual(runs[3], ('D', tm_text.DEFAULT))

    def test_literal_dollar_unknown_codes_and_three_digit_parsing(self):
        runs = tm_text.parse('$$o $q $ff0000')
        self.assertEqual(''.join(text for text, _ in runs), '$o $q 000')
        self.assertEqual(runs[-1][1].color, 'FF0')

    def test_serialization_preserves_mixed_styles_and_dollars(self):
        raw = '$oA$iB$wC$gD$z$$E$nF$mG$tH$tI$sJ$sK'
        def visible_styles(runs):
            return [(char, style) for text, style in runs for char in text]
        self.assertEqual(visible_styles(tm_text.parse(raw)),
                         visible_styles(tm_text.parse(tm_text.serialize(tm_text.parse(raw)))))

    def test_dynamic_colors_only_have_meaning_in_templates(self):
        runs = tm_text.parse('{primary}{name}$g - {secondary}Event', template=True)
        self.assertEqual(runs[0], ('{name}', replace(tm_text.DEFAULT, color='primary')))
        self.assertEqual(tm_text.serialize(runs), '{primary}{name}$z - {secondary}Event')
        self.assertEqual(tm_text.parse('{primary}'), [('{primary}', tm_text.DEFAULT)])
        self.assertEqual(''.join(t for t, _ in tm_text.parse('{{primary}}', template=True)), '{{primary}}')

    def test_dynamic_filename_colors_and_original_fallback(self):
        row = {'stem': 'Joseph', 'name': 'Joseph', 'id': '1', 'line': 2, 'colors': ['#FF8800', '#0088FF', None]}
        self.assertEqual(core.format_skin_name('{primary}{name}$g - {secondary}Event', row), '$F80Joseph$g - $08FEvent')
        row['colors'] = [None, None, None]
        self.assertEqual(core.format_skin_name('{primary}{name}', row, ['#123456', None]), '$135Joseph')
        with self.assertRaisesRegex(ValueError, 'secondary'):
            core.format_skin_name('{secondary}{name}', row)
        self.assertEqual(core.name_color_fields('{{primary}} - {name}'), set())

    def test_filename_truncation_does_not_split_format_tokens(self):
        self.assertEqual(core.safe_stem('a' * 98 + '$F80X'), 'a' * 98)
        self.assertEqual(core.safe_stem('a' * 99 + '$oX'), 'a' * 99)
        self.assertEqual(core.safe_stem('a' * 99 + '$$X'), 'a' * 99)

