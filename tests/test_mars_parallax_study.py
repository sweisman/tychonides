"""The 1587 Mars parallax tables regenerate from their committed inputs."""

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


class MarsParallaxSelectionTests(unittest.TestCase):
    @unittest.skipUnless(CATALOG, "set TYCHONIDES_CATALOG to the unpacked catalog to run")
    def test_input_files_match_the_catalog(self):
        import mars_parallax_select as selection

        with closing(sqlite3.connect(f"file:{CATALOG}?mode=ro", uri=True)) as db:
            selected, excluded = selection.select(db)
        with tempfile.TemporaryDirectory() as scratch:
            for name, fields, rows in (
                ("mars-parallax-readings.csv", selection.FIELDS, selected),
                ("mars-parallax-excluded.csv", selection.EXCLUDED_FIELDS, excluded),
            ):
                selection.write(Path(scratch) / name, fields, rows)
                self.assertEqual(table(Path(scratch) / name), table(EXAMPLES / name), name)

    def test_every_selected_clock_has_a_printed_origin(self):
        with (EXAMPLES / "mars-parallax-readings.csv").open(encoding="utf-8", newline="") as source:
            rows = list(csv.DictReader(source))
        self.assertTrue(rows)
        for row in rows:
            self.assertIn(row["clock_origin"], ("noon", "midnight"))
            self.assertTrue(row["origin_basis"])


@unittest.skipUnless(importlib.util.find_spec("numpy"), "the study scripts need NumPy")
class MarsParallaxStudyTests(unittest.TestCase):
    def test_published_tables_regenerate_from_committed_inputs(self):
        import mars_parallax_1587 as study

        with tempfile.TemporaryDirectory() as scratch:
            study.write_tables(Path(scratch))
            produced = sorted(path.name for path in Path(scratch).iterdir())
            self.assertEqual(
                produced, sorted(path.name for path in FIGURES.glob("mars-parallax-1587-*.csv"))
            )
            for name in produced:
                self.assertEqual(table(Path(scratch) / name), table(FIGURES / name), name)

    def test_cached_ephemeris_covers_exactly_the_instants_the_study_uses(self):
        import mars_parallax_1587 as study

        cached = [row[0] for row in table(EXAMPLES / "mars-parallax-ephemeris.csv")[1:]]
        self.assertEqual(cached, study.instants())

    def test_hours_after_midnight_belong_to_the_night_of_the_labeled_date(self):
        import mars_parallax_1587 as study

        evening = {"julian_date": "1587-02-23", "clock_origin": "noon", "clock_seconds": "28800"}
        morning = {"julian_date": "1587-02-23", "clock_origin": "midnight", "clock_seconds": "3600"}
        hours = (study.instant(morning) - study.instant(evening)) * 24
        self.assertAlmostEqual(hours, 5, places=2)
        self.assertEqual(study.session(evening), "evening")
        self.assertEqual(study.session(morning), "near the meridian")

    def test_wing_stars_have_the_declinations_the_log_gives_them(self):
        import mars_parallax_1587 as study
        import numpy as np

        sky, jd = study.Sky(), float(study.instants()[0])
        for hip, degrees, minutes in (("60129", 1, 39), ("61941", 0, 51)):
            direction = study.precession(jd) @ study.star_direction(sky.stars[hip], jd)
            declination = float(np.rad2deg(np.arcsin(direction[2])))
            self.assertAlmostEqual(declination, degrees + minutes / 60, delta=3 / 60)

    def test_the_pole_stands_at_the_latitude_and_refraction_lifts_by_its_own_amount(self):
        import mars_parallax_1587 as study
        import numpy as np
        from refraction_tables import STANDARD, bennett

        jd = float(study.instants()[0])
        pole = np.array([0.0, 0.0, 1.0])
        self.assertAlmostEqual(study.altitude(pole, jd), np.rad2deg(study.LATITUDE), places=9)
        seen = study.altitude(study.lifted(pole, jd, STANDARD), jd)
        self.assertAlmostEqual(
            (seen - study.altitude(pole, jd)) * 3600, float(bennett(seen, *STANDARD)), places=3
        )
        self.assertEqual(study.tycho_table()(25.0), 0.0)

    def test_the_fit_recovers_a_parallax_put_into_the_distances(self):
        import mars_parallax_1587 as study

        sky, rows = study.Sky(), study.read("mars-parallax-readings.csv")
        for row in rows:
            row["separation_arcseconds_exact"] = repr(
                sky.distance(study.instant(row), row["hip"], 150.0)
            )
        parallax, _, _ = study.implied(study.evaluate(sky, rows))
        self.assertAlmostEqual(parallax, 150, delta=0.5)

    def test_computed_meridian_altitude_matches_the_log(self):
        import mars_parallax_1587 as study

        # The log gives Mars 39° 40¾′ on the meridian on March 10 (Opera Omnia XI p. 186).
        records = study.evaluate(study.Sky(), study.read("mars-parallax-readings.csv"))
        near = [
            record["mars_altitude"]
            for record in records
            if record["key"] == ("1587-03-10", "near the meridian")
        ]
        self.assertAlmostEqual(max(near), 39 + 40.75 / 60, delta=2 / 60)


if __name__ == "__main__":
    unittest.main()
