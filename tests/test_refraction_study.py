"""The refraction table study regenerates from its committed inputs."""

import csv
import importlib.util
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIGURES = ROOT / "docs/figures"
CATALOG = os.environ.get("TYCHONIDES_CATALOG")
sys.path.insert(0, str(EXAMPLES))


def table(path):
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.reader(source))


class RefractionSelectionTests(unittest.TestCase):
    @unittest.skipUnless(CATALOG, "set TYCHONIDES_CATALOG to the unpacked catalog to run")
    def test_selection_files_match_the_catalog(self):
        import refraction_select

        with closing(sqlite3.connect(f"file:{CATALOG}?mode=ro", uri=True)) as db:
            kept, left_out = refraction_select.select(db)
        with tempfile.TemporaryDirectory() as scratch:
            files = {
                "refraction-tables.csv": (refraction_select.FIELDS, kept),
                "refraction-tables-excluded.csv": (refraction_select.EXCLUDED_FIELDS, left_out),
            }
            for name, (fields, rows) in files.items():
                refraction_select.write(Path(scratch) / name, fields, rows)
                self.assertEqual(table(Path(scratch) / name), table(EXAMPLES / name), name)


@unittest.skipUnless(importlib.util.find_spec("numpy"), "the study scripts need NumPy")
class RefractionStudyTests(unittest.TestCase):
    def test_published_tables_regenerate_from_committed_inputs(self):
        import refraction_tables

        with tempfile.TemporaryDirectory() as scratch:
            refraction_tables.write_tables(Path(scratch))
            produced = sorted(path.name for path in Path(scratch).iterdir())
            self.assertEqual(
                produced, sorted(path.name for path in FIGURES.glob("refraction-tables-*.csv"))
            )
            for name in produced:
                self.assertEqual(table(Path(scratch) / name), table(FIGURES / name), name)

    def test_modern_formula_at_known_altitudes(self):
        import refraction_tables

        # Bennett's formula gives about 34.5 arcminutes at the horizon and 1 at 45 degrees.
        self.assertAlmostEqual(float(refraction_tables.bennett(0)) / 60, 34.48, places=2)
        self.assertAlmostEqual(float(refraction_tables.bennett(45)) / 60, 0.995, places=3)
        cold = float(refraction_tables.bennett(10, 1010, -10))
        self.assertAlmostEqual(cold / float(refraction_tables.bennett(10)), 283 / 263)

    def test_tycho_solar_parallax_is_three_arcminutes(self):
        import refraction_tables

        horizontal = refraction_tables.ARCSECONDS / refraction_tables.TYCHO_SOLAR_DISTANCE
        self.assertAlmostEqual(horizontal, 180, delta=0.02)
        self.assertAlmostEqual(float(refraction_tables.altitude_parallax(60, 180)), 90)


if __name__ == "__main__":
    unittest.main()
