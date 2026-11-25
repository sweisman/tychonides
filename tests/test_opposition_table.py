"""The opposition table comparison regenerates from its committed inputs."""

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIGURES = ROOT / "docs/figures"
sys.path.insert(0, str(EXAMPLES))


def table(path):
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.reader(source))


@unittest.skipUnless(importlib.util.find_spec("numpy"), "the study scripts need NumPy")
class OppositionTableTests(unittest.TestCase):
    def test_published_table_regenerates_from_the_cached_positions(self):
        import mars_opposition_table

        name = "mars-opposition-table.csv"
        with tempfile.TemporaryDirectory() as scratch:
            mars_opposition_table.write_tables(Path(scratch))
            produced, committed = table(Path(scratch) / name), table(FIGURES / name)
        self.assertEqual(len(produced), len(committed))
        for made, kept in zip(produced, committed, strict=True):
            for new, old in zip(made, kept, strict=True):
                try:
                    difference = abs(float(new) - float(old))
                except ValueError:
                    self.assertEqual(new, old)
                    continue
                # Allow a change in the last printed place and nothing more.
                places = len(old.partition(".")[2])
                self.assertLessEqual(difference, 1.5 * 10**-places, f"{old} became {new}")

    def test_cache_holds_exactly_the_instants_the_script_uses(self):
        import mars_opposition_table

        cached = {
            (row[0], row[1]) for row in table(EXAMPLES / "mars-opposition-table-ephemeris.csv")[1:]
        }
        wanted = {
            (number, jd)
            for number, epochs in mars_opposition_table.instants().items()
            for jd in epochs
        }
        self.assertEqual(cached, wanted)

    def test_every_row_has_one_opposition_near_its_instant(self):
        import mars_opposition_table

        rows = mars_opposition_table.reproduce()
        self.assertEqual(len(rows), 14)
        for row in rows:
            self.assertLess(abs(float(row["de441_opposition_offset_hours"])), 4, row)
            self.assertLess(abs(float(row["tabulated_minus_de441_longitude_arcmin"])), 4, row)
            unexplained = float(row["implied_sun_minus_de441_sun_arcmin"]) - float(
                row["solar_equation_excess_arcmin"]
            )
            self.assertLess(abs(unexplained), 3, row)

    def test_the_solar_equation_excess_is_about_seven_arcminutes(self):
        import mars_opposition_table

        self.assertAlmostEqual(mars_opposition_table.EQUATION_EXCESS * 60, 6.8, places=1)


if __name__ == "__main__":
    unittest.main()
