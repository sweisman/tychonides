"""The parallax tables regenerate from their committed inputs."""

import csv
import importlib.util
import math
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIGURES = ROOT / "docs/figures"
CATALOG = os.environ.get("TYCHONIDES_CATALOG")
sys.path.insert(0, str(EXAMPLES))


def table(path):
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.reader(source))


class ParallaxSelectionTests(unittest.TestCase):
    def test_printed_digits_ignore_marks_and_spell_out_fractions(self):
        import parallax_select

        self.assertEqual(parallax_select.digits("51° 35½′"), ["51", "35", "1/2"])
        self.assertEqual(parallax_select.digits("0 3′ 39″"), ["0", "3", "39"])
        self.assertEqual(parallax_select.digits("23° 18 1/12′"), ["23", "18", "1/12"])

    def test_declared_values_are_checked_against_exact_entries(self):
        import parallax_select

        self.assertTrue(parallax_select.agrees("6191/120", "degree", "185730", "arcsecond"))
        self.assertFalse(parallax_select.agrees("619/12", "degree", "185730", "arcsecond"))
        self.assertTrue(parallax_select.agrees("721", "earth_radius", "721", "semidiameter"))

    @unittest.skipUnless(CATALOG, "set TYCHONIDES_CATALOG to the unpacked catalog to run")
    def test_input_files_match_the_catalog(self):
        import parallax_select

        with closing(sqlite3.connect(f"file:{CATALOG}?mode=ro", uri=True)) as db:
            pairs, incomplete, models, odd, resolved = parallax_select.select(db)
        self.assertEqual((len(pairs), incomplete, len(models), len(odd)), (56, 4, 50, 1))
        files = {
            "parallax-venus-pairs.csv": (parallax_select.PAIR_FIELDS, pairs),
            "parallax-riccioli.csv": (parallax_select.RICCIOLI_FIELDS, models),
            "parallax-inputs.csv": (parallax_select.INPUT_FIELDS, resolved),
        }
        with tempfile.TemporaryDirectory() as scratch:
            for name, (fields, rows) in files.items():
                parallax_select.write(Path(scratch) / name, fields, rows)
                self.assertEqual(table(Path(scratch) / name), table(EXAMPLES / name), name)


@unittest.skipUnless(importlib.util.find_spec("numpy"), "the study scripts need NumPy")
class ParallaxStudyTests(unittest.TestCase):
    def assert_tables_close(self, produced, committed, name):
        self.assertEqual(len(produced), len(committed), name)
        for made, kept in zip(produced, committed, strict=True):
            self.assertEqual(len(made), len(kept), name)
            for new, old in zip(made, kept, strict=True):
                try:
                    difference = abs(float(new) - float(old))
                except ValueError:
                    self.assertEqual(new, old, name)
                    continue
                # Allow a change in the last printed place and nothing more.
                places = len(old.partition(".")[2])
                self.assertLessEqual(difference, 1.5 * 10**-places, f"{name}: {old} became {new}")

    def test_published_tables_regenerate_from_committed_inputs(self):
        import planetary_parallax

        with tempfile.TemporaryDirectory() as scratch:
            planetary_parallax.write_tables(Path(scratch))
            produced = sorted(path.name for path in Path(scratch).iterdir())
            self.assertEqual(produced, sorted(path.name for path in FIGURES.glob("parallax-*.csv")))
            for name in produced:
                self.assert_tables_close(table(Path(scratch) / name), table(FIGURES / name), name)

    def test_cached_ephemeris_covers_the_instants_at_the_same_times(self):
        import planetary_parallax

        inputs, pairs = planetary_parallax.load_inputs(), planetary_parallax.load_pairs()
        cached = {row[0]: float(row[2]) for row in table(EXAMPLES / "parallax-ephemeris.csv")[1:]}
        wanted = planetary_parallax.instants(inputs, pairs)
        self.assertEqual(set(cached), {key for key, _, _ in wanted})
        for key, _, epoch in wanted:
            self.assertAlmostEqual(cached[key], epoch, places=5, msg=key)

    def test_dates_and_clocks_become_the_stated_julian_dates(self):
        import planetary_parallax

        noons = [
            planetary_parallax.julian_day_number(day) for _, day, _, _ in planetary_parallax.OUTER
        ]
        self.assertEqual(noons, [2299243, 2300775, 2303081, 2305176])
        offset = planetary_parallax.UT_OFFSET_HOURS
        self.assertAlmostEqual(
            planetary_parallax.local_jd(date(1590, 3, 3), offset), 2301867.0, places=9
        )

    def test_geometry_at_known_values(self):
        import planetary_parallax

        self.assertAlmostEqual(planetary_parallax.altitude_parallax(40, 721), 219.15, places=2)
        # At the horizon and on the equator the share is the sine of the latitude.
        self.assertAlmostEqual(planetary_parallax.projection(0, 0), 0.8281, places=4)
        # On the meridian the whole parallax falls in declination. The exact parallax at a
        # geocentric altitude h and distance n is atan(cos h / (n - sin h)).
        height = math.radians(90 - 55.9078611 + 20)
        exact = math.atan2(math.cos(height), 850 - math.sin(height)) * planetary_parallax.ARCSECONDS
        shift = planetary_parallax.declination_shift(20, math.degrees(height), 850)
        self.assertAlmostEqual(-shift, exact, places=3)


if __name__ == "__main__":
    unittest.main()
