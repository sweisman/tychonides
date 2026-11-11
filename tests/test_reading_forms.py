import unittest
from src.core import extract_text, compare_records

HEAD = '[QA: PDF p. 58 — running head: "1590", page number "44"]\n### 4 March\n'


class ReadingFormTests(unittest.TestCase):
    def test_declination_label_inside_blank_horizontal_column(self):
        text = (
            HEAD
            + """| Hours, minutes | Distance of Mars | | Star |
|---|---|---|---|
| 6^h^ 16^m^ 20^s^ | Mars crossed the meridian | | |
| | | Declination 6° 47½′ | |
| | | 6° 48′ | |
"""
        )
        rows = extract_text(text, "test", {})
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["24450", "24480"])
        self.assertEqual(rows[1]["time_key"], "22580")

    def test_inline_continuation_reading_and_untimed_reduction(self):
        text = (
            HEAD
            + """Mars was observed.
| Time | Reading | Value |
|---|---|---|
| 6^h^ 48^m^ | Declination 1° 31′ north | |
| | 1° 31¼′ doubtful | |

From this comes the declination of Mars, 1° 34½′.
"""
        )
        rows = extract_text(text, "test", {})
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["5460", "5475", "5670"])
        self.assertEqual(rows[-1]["role"], "derived")
        self.assertIsNone(rows[-1]["time_key"])

    def test_mars_section_supplies_target_for_later_days(self):
        text = "[Running header: 1585 382]\n## Observations of Mars\n### 7 January\nDeclination 15 35 [Decl. eius 15 35]\n"
        rows = extract_text(text, "test", {"volume": 10})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["magnitude_arcsec"], "56100")

    def test_multiple_label_value_pairs_do_not_share_a_label(self):
        text = (
            HEAD
            + """| Time | Reading | Value | Reading | Value |
|---|---|---|---|---|
| 6^h^ 31^m^ | Distance of Mars from Spica | 31° 26′ | Declination of Mars | 3° 16½′ |
| 6^h^ 36^m^ | | 31° 27′ | | 3° 16′ |
"""
        )
        rows = extract_text(text, "test", {})
        self.assertEqual([r["value_original"] for r in rows], ["3° 16½′", "3° 16′"])

    def test_inline_declination_does_not_capture_following_altitude(self):
        text = (
            HEAD
            + """| Time | Reading | Value |
|---|---|---|
| 9^h^ 1^m^ | Declination of Mars 7° 35′, altitude | 40° 25′ |
"""
        )
        rows = extract_text(text, "test", {})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["magnitude_arcsec"], "27300")

    def test_prose_reading_comes_from_book_not_latin_repetition(self):
        text = HEAD + "- Declination of ♂ B. [Decl. ♂ B.] — 17 31 0\n"
        rows = extract_text(text, "test", {})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["magnitude_arcsec"], "63060")

    def test_derived_quote_can_be_confirmed_but_keeps_its_role(self):
        p = dict(
            id="p",
            volume=12,
            page=44,
            date="1590-03-04",
            time_key=None,
            quote="9 26",
            quote_magnitude_arcsec="33960",
            arcsec="33960",
        )
        r = dict(
            id="r",
            volume=12,
            page=44,
            date="1590-03-04",
            time_key=None,
            magnitude_arcsec="33960",
            arcsec=None,
            role="derived",
            flags=["derived_or_editorial"],
        )
        result = compare_records([p], [r])[0]
        self.assertEqual(result["status"], "magnitude_agreement")
        self.assertEqual(result["source_role"], "derived")


if __name__ == "__main__":
    unittest.main()
