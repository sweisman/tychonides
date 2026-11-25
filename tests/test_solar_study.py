"""The solar-theory tables regenerate from their committed inputs."""

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


class SolarSelectionTests(unittest.TestCase):
    @unittest.skipUnless(CATALOG, "set TYCHONIDES_CATALOG to the unpacked catalog to run")
    def test_input_file_matches_the_catalog(self):
        import solar_select

        with closing(sqlite3.connect(f"file:{CATALOG}?mode=ro", uri=True)) as db:
            rows = solar_select.select(db)
        self.assertEqual(len(rows), 10 + len(solar_select.ITEMS))
        with tempfile.TemporaryDirectory() as scratch:
            name = "solar-theory-inputs.csv"
            solar_select.write(Path(scratch) / name, solar_select.FIELDS, rows)
            self.assertEqual(table(Path(scratch) / name), table(EXAMPLES / name))


@unittest.skipUnless(importlib.util.find_spec("numpy"), "the study scripts need NumPy")
class SolarStudyTests(unittest.TestCase):
    def test_published_tables_regenerate_from_committed_inputs(self):
        import solar_theory

        with tempfile.TemporaryDirectory() as scratch:
            solar_theory.write_tables(Path(scratch))
            produced = sorted(path.name for path in Path(scratch).iterdir())
            self.assertEqual(
                produced, sorted(path.name for path in FIGURES.glob("solar-theory-*.csv"))
            )
            for name in produced:
                self.assertEqual(table(Path(scratch) / name), table(FIGURES / name), name)

    def test_cached_ephemeris_covers_exactly_the_instants_the_study_uses(self):
        import solar_theory

        cached = [row[0] for row in table(EXAMPLES / "solar-theory-ephemeris.csv")[1:]]
        self.assertEqual(cached, solar_theory.instants())

    def test_the_construction_recovers_a_known_eccentric(self):
        import numpy as np
        import solar_theory

        # A Sun moving uniformly on a circle whose center lies 0.03 from the Earth toward 100°.
        year, apogee, eccentricity = 365.25, np.deg2rad(100), 0.03

        def elapsed(longitude):
            seen = np.deg2rad(longitude) - apogee
            return (seen + np.arcsin(eccentricity * np.sin(seen))) * year / (2 * np.pi)

        half = elapsed(180) - elapsed(0)
        for place, interval in (
            ("15 Taurus", elapsed(45) - elapsed(0)),
            ("15 Leo", elapsed(180) - elapsed(135)),
        ):
            found = solar_theory.construction(year, half, place, interval)
            self.assertAlmostEqual(found[0], 100, places=6)
            self.assertAlmostEqual(found[1], 0.03, places=9)

    def test_printed_hours_count_from_apparent_noon(self):
        import solar_theory

        row = {"julian_date": "1588-03-09", "value_exact": "74700"}
        mean = solar_theory.printed_instant(row, apparent=False)
        # In March a sundial runs behind a clock, so the apparent hour falls later in mean time.
        self.assertAlmostEqual((solar_theory.printed_instant(row) - mean) * 1440, 7.7, places=1)

    def test_an_exact_reduction_returns_the_true_longitude(self):
        import numpy as np
        import solar_theory

        _, items = solar_theory.inputs()
        reduction = solar_theory.Reduction(items, 23.5)
        # With no refraction or parallax on either side, the true pole altitude and the true
        # obliquity, the reduction is an identity.
        reduction.seen = lambda altitude: altitude
        reduction.correction = lambda altitude: 0.0
        reduction.pole = solar_theory.SITE_LATITUDE
        reduction.obliquity = np.deg2rad(23.5)
        for longitude in (0.0, 45.0, 135.0, 180.0):
            self.assertAlmostEqual(reduction.true_place(longitude), longitude, places=9)


if __name__ == "__main__":
    unittest.main()
