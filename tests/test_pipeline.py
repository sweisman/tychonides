import unittest
import tempfile
from pathlib import Path
from fractions import Fraction
from src.core import (
    angle,
    compare_records,
    extract_text,
    sample_records,
    quote_angle,
    recorded_clock,
)


class PipelineTests(unittest.TestCase):
    def test_original_clock_forms_and_ambiguous_multiple_clocks(self):
        self.assertEqual(recorded_clock("H.13 26 P.M."), "48360")
        self.assertEqual(recorded_clock("H.6.40 P. M."), "24000")
        self.assertEqual(recorded_clock("H.1 3/4"), "6300")
        self.assertEqual(recorded_clock("H.3 27 1/6"), "12430")
        self.assertEqual(recorded_clock("H.6 M.19 S.30"), "22770")
        self.assertIsNone(recorded_clock("H.6 M.16 H.20"))
        self.assertIsNone(recorded_clock("H.7 Mk57 1/2"))

    def test_read_only_output_guard(self):
        from src.__main__ import guard

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                guard(root / "translation" / "new", root)
            guard(root.parent / "different-output", root)

    def test_comparison_star_hemisphere_does_not_sign_mars(self):
        text = '[QA: PDF p. 58 — running head: "1590", page number "44"]\n### 4 March\n| Time | Distance from scale-pan, south | Declination of Mars |\n|---|---|---|\n| 7^h^ 5^m^ | 20° 5′ | 9° 26′ |\n'
        self.assertIsNone(extract_text(text, "test", {})[0]["arcsec"])

    def test_fractions_and_missing(self):
        self.assertEqual(angle("11° 5⅙′"), Fraction(39910))
        self.assertEqual(angle("0° 0′ 0″"), 0)
        self.assertIsNone(angle(""))
        self.assertIsNone(angle("11° [?]′"))
        self.assertEqual(angle("11° 5¹⁄₁₂′"), Fraction(39905))
        self.assertEqual(angle("11° 5′ 30″"), 39930)

    def test_pafko_quote_is_separate_from_converted_cells(self):
        quote = "Afc. R. [MS] 107o 56' Declin. 26o 36' B."
        self.assertEqual(quote_angle(quote), 95760)
        self.assertNotEqual(quote_angle(quote), 26 * 3600 + 56 * 60)
        self.assertEqual(quote_angle("Decl. [MS] M. 20 50 1/6"), 75010)
        self.assertEqual(quote_angle("declinatio [MS] 3 grad. 29 2/3 Min. bis."), 12580)
        self.assertEqual(quote_angle("Declinatio [MS] 1g 21' B"), 4860)

    def test_south_and_apparatus(self):
        text = '[QA: PDF p. 58 — running head: "1590", page number "44"]\n### 4 March\n| Time | Declination of Mars, south |\n|---|---|\n| 7^h^ 5⅚^m^ | 9° 26′ |\n| | 9° 26½′ |\n\n¹ Correct declination of Mars to 9° 27′.\n'
        rows = extract_text(text, "test.md", {})
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["arcsec"], "-33960")
        self.assertEqual(rows[0]["date"], "1590-03-04")
        self.assertEqual(rows[1]["time_key"], rows[0]["time_key"])

    def test_matching_never_uses_value(self):
        p = {"id": "p1", "page": 44, "date": "1590-03-04", "arcsec": "100", "time_key": None}
        candidates = [dict(p, id="a", arcsec="200"), dict(p, id="b")]
        self.assertEqual(compare_records([p], candidates)[0]["status"], "ambiguous")
        self.assertEqual(compare_records([p], candidates[:1])[0]["status"], "disagreement")
        self.assertEqual(
            compare_records([p], [dict(p, id="a", arcsec=None)])[0]["status"], "unresolved"
        )

    def test_date_inheritance_and_no_zero_filling(self):
        state = {}
        extract_text('[QA: PDF p. 58 — "1590", page number "44"]\n### 4 March\n', "a", state)
        rows = extract_text(
            '[QA: PDF p. 59 — "1590", page number "45"]\n| Time | Declination of Mars |\n|---|---|\n| | 9° 26′ |\n',
            "b",
            state,
        )
        self.assertEqual(rows[0]["date"], "1590-03-04")
        self.assertIsNone(rows[0]["arcsec"])  # no hemisphere established

    def test_stratified_sample(self):
        rows = [{"id": str(i), "date": f"{1590 + i % 6}-01-01", "page": i} for i in range(100)]
        chosen = sample_records(rows, 50)
        self.assertEqual(len(chosen), 50)
        self.assertEqual(chosen, sample_records(rows, 50))
        self.assertEqual(len({r["date"][:4] for r in chosen}), 6)

    def test_alternative_page_head_and_parallel_column(self):
        text = '[QA: p. 359 opening. Running head: "1594" (centre) "345" (right)]\n### 4 March\n| Hours, minutes | Declination of Mars, south | |\n|---|---|---|\n| 7^h^ 5^m^ | 9° 26′ | 9° 27′ |\n'
        rows = extract_text(text, "test.md", {})
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["page"], 345)
        self.assertEqual(rows[0]["date"], "1594-03-04")
        self.assertEqual(rows[0]["time_key"], "25500")
        self.assertIn("column_role_unresolved", rows[1]["flags"])

    def test_shared_candidate_is_not_two_matches(self):
        p = {"id": "p1", "page": 44, "date": "1590-03-04", "arcsec": "100", "time_key": None}
        results = compare_records([p, dict(p, id="p2")], [dict(p, id="a")])
        self.assertEqual([r["status"] for r in results], ["ambiguous", "ambiguous"])


if __name__ == "__main__":
    unittest.main()
