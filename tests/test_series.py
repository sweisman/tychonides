import importlib
import unittest


class SeriesTests(unittest.TestCase):
    def parse(self, text):
        try:
            m = importlib.import_module("src.series")
        except ModuleNotFoundError:
            self.fail("Reviewed separation-series parser is not implemented")
        return m.parse_separation_row(text)

    def test_original_row_survives_inline_erratum(self):
        r = self.parse(
            "- H.2 24 — 3 2⅔ [recte: for 2⅔ read 3²⁄₈ — Corrigenda, p. 430] — I — Alt. of Mars [Alt. Mars] 47 50"
        )
        self.assertEqual(r["clock"]["components"], {"hour": "2", "minute": "24"})
        self.assertEqual(r["separation"]["source_expression"], "3 2⅔")
        self.assertEqual(r["separation"]["components"], {"degree": "3", "arcminute": "2⅔"})
        self.assertEqual(r["altitude"]["source_expression"], "47 50")
        self.assertEqual(r["ordinal"], 1)
        self.assertEqual(r["ordinal_original"], "I")

    def test_one_component_altitude_preserves_degree_precision(self):
        r = self.parse("- 6 41 — 2 47⅚ — III — 13")
        self.assertEqual(r["altitude"]["components"], {"degree": "13"})
        self.assertEqual(r["clock"]["source_expression"], "6 41")
        self.assertEqual(r["ordinal"], 3)

    def test_unsupported_or_missing_fields_cannot_be_silently_skipped(self):
        for text in (
            "- 6 41 — ? — III",
            "- 6 41 — 2 47 — unlabeled",
            "- 6 41 — 2 47 — I — 13 and 14",
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.parse(text)
        r = self.parse("- 3 4 — 4 31 — IIII")
        self.assertEqual(r["ordinal"], 4)
        self.assertIsNone(r["altitude"])


if __name__ == "__main__":
    unittest.main()
