"""The Kassel and Uraniborg comparison regenerates from its committed inputs."""

import csv
import importlib.util
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


def records(path):
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


@unittest.skipUnless(importlib.util.find_spec("numpy"), "the study scripts need NumPy")
class KasselSelectionTests(unittest.TestCase):
    @unittest.skipUnless(CATALOG, "set TYCHONIDES_CATALOG to the unpacked catalog to run")
    def test_input_files_match_the_catalog(self):
        import mars_kassel_select as selection

        with closing(sqlite3.connect(f"file:{CATALOG}?mode=ro", uri=True)) as db:
            selected, excluded = selection.select(db)
        with tempfile.TemporaryDirectory() as scratch:
            for name, fields, rows in (
                ("mars-kassel-readings.csv", selection.FIELDS, selected),
                ("mars-kassel-excluded.csv", selection.EXCLUDED_FIELDS, excluded),
            ):
                selection.write(Path(scratch) / name, fields, rows)
                self.assertEqual(table(Path(scratch) / name), table(EXAMPLES / name), name)

    def test_the_sun_is_down_at_an_evening_hour_and_up_at_an_afternoon_one(self):
        import mars_kassel_select as selection

        self.assertTrue(selection.sun_is_up("Kassel", date(1593, 8, 22), 2 * 3600))
        self.assertFalse(selection.sun_is_up("Kassel", date(1593, 8, 22), 9 * 3600))
        # In December the Sun has set at Uraniborg well before six.
        self.assertFalse(selection.sun_is_up("Uraniborg", date(1593, 12, 29), 5 * 3600 + 1320))

    def test_an_evening_hour_is_counted_from_noon(self):
        import mars_kassel_select as selection

        placed = selection.placed("Kassel", date(1593, 8, 21), "after_noon", "32400", True)
        self.assertEqual(placed, (32400, "counted from noon", ""))

    def test_an_hour_in_daylight_has_passed_twelve_when_its_entry_has_an_evening_hour(self):
        import mars_kassel_select as selection

        day = date(1593, 8, 21)
        seconds, basis, reason = selection.placed("Uraniborg", day, "before_midnight", "600", True)
        self.assertEqual((seconds, reason), (43800, ""))
        self.assertIn("past twelve", basis)
        seconds, _, reason = selection.placed("Uraniborg", day, "before_midnight", "600", False)
        self.assertIsNone(seconds)
        self.assertIn("no evening hour", reason)

    def test_a_morning_hour_belongs_to_the_night_before_and_an_hour_before_noon_is_open(self):
        import mars_kassel_select as selection

        day = date(1595, 10, 27)
        seconds, basis, _ = selection.placed("Uraniborg", day, "morning", "24540", False)
        self.assertEqual(seconds, 24540 - 43200)
        self.assertIn("morning", basis)
        self.assertEqual(selection.night(day, seconds), date(1595, 10, 26))
        self.assertEqual(selection.night(day, 43800), day)
        seconds, _, reason = selection.placed("Kassel", day, "before_noon", "10800", True)
        self.assertIsNone(seconds)
        self.assertIn("day is open", reason)
        self.assertEqual(selection.placed("Kassel", day, "", "", True)[2], "no exact printed clock")

    def test_every_selected_reading_has_a_partner_at_the_other_site_that_night(self):
        rows = records(EXAMPLES / "mars-kassel-readings.csv")
        self.assertTrue(rows)
        sites = {}
        for row in rows:
            sites.setdefault((row["night"], row["hip"]), set()).add(row["site"])
        self.assertEqual(set(map(frozenset, sites.values())), {frozenset({"Kassel", "Uraniborg"})})


@unittest.skipUnless(importlib.util.find_spec("numpy"), "the study scripts need NumPy")
class KasselStudyTests(unittest.TestCase):
    def test_published_tables_regenerate_from_committed_inputs(self):
        import mars_kassel as study

        with tempfile.TemporaryDirectory() as scratch:
            study.write_tables(Path(scratch))
            produced = sorted(path.name for path in Path(scratch).iterdir())
            self.assertEqual(
                produced, sorted(path.name for path in FIGURES.glob("mars-kassel-*.csv"))
            )
            for name in produced:
                self.assertEqual(table(Path(scratch) / name), table(FIGURES / name), name)

    def test_cached_ephemeris_covers_exactly_the_instants_the_study_uses(self):
        import mars_kassel as study

        cached = [row[0] for row in table(EXAMPLES / "mars-kassel-ephemeris.csv")[1:]]
        self.assertEqual(cached, study.instants())

    def test_the_same_clock_hour_comes_later_at_kassel_than_at_uraniborg(self):
        import mars_kassel as study

        row = {"julian_date": "1593-08-21", "seconds_from_noon": "32400"}
        kassel = study.instant(row | {"site": "Kassel"})
        uraniborg = study.instant(row | {"site": "Uraniborg"})
        # Kassel lies 3.2 degrees west of Uraniborg, and a degree is four minutes of time.
        self.assertAlmostEqual((kassel - uraniborg) * 1440, (12.6967 - 9.5) * 4, places=1)
        later = study.instant(row | {"site": "Kassel"}, minutes=30)
        # The equation of time moves by a fraction of a second in half an hour.
        self.assertAlmostEqual((later - kassel) * 1440, 30, places=1)

    def test_the_pole_stands_at_the_latitude_of_each_site(self):
        import mars_kassel as study
        import numpy as np

        pole = np.array([0.0, 0.0, 1.0])
        for site, degrees in (("Kassel", 51 + 19 / 60), ("Uraniborg", 55 + 54.47 / 60)):
            height = study.altitude(pole, study.zenith(site, 2303000.5))
            self.assertAlmostEqual(height, degrees, places=2)

    def test_a_pair_reports_what_is_left_after_the_computed_change(self):
        import mars_kassel as study

        def record(site, observed, computed):
            return {
                "site": site,
                "night": "1593-08-21",
                "hip": "9884",
                "observed": observed,
                "computed": computed,
                "hours": 9.0,
                "mars_altitude": 20.0,
            }

        both = [
            record("Kassel", 3600.0, 3480.0),
            record("Kassel", 3660.0, 3480.0),
            record("Uraniborg", 3540.0, 3500.0),
        ]
        (pair,) = study.pairs(both)
        self.assertAlmostEqual(pair["raw"], 90.0)
        self.assertAlmostEqual(pair["change"], -20.0)
        self.assertAlmostEqual(pair["left"], 110.0)
        self.assertAlmostEqual(pair["Kassel"]["left"], 150.0)
        self.assertAlmostEqual(pair["Uraniborg"]["left"], 40.0)
        self.assertEqual(study.pairs(both[:2]), [])

    def test_a_reading_whose_printed_altitude_contradicts_its_hour_has_its_clock_in_question(self):
        import mars_kassel as study

        def record(recorded, computed):
            return {"recorded_altitude": recorded, "mars_altitude": computed}

        self.assertTrue(study.clock_in_question(record(44.7, 29.7)))
        self.assertFalse(study.clock_in_question(record(22.0, 19.1)))
        self.assertFalse(study.clock_in_question(record(None, 19.1)))

    def test_the_third_star_of_aries_stands_where_the_kassel_book_prints_it(self):
        import mars_kassel as study
        import numpy as np
        from mars_parallax_1587 import of_date, star_direction
        from solar_theory import mean_elements

        # Observationes Hassiacae p. 65 gives it Taurus 2° 7′ 44″ and 9° 54′ 12″ north.
        sky, jd = study.Sky(), float(study.instants()[0])
        x, y, z = of_date(star_direction(sky.stars["9884"], jd), jd)
        tilt = np.deg2rad(mean_elements(jd)[2])
        latitude = np.rad2deg(np.arcsin(z * np.cos(tilt) - y * np.sin(tilt)))
        longitude = np.rad2deg(np.arctan2(y * np.cos(tilt) + z * np.sin(tilt), x)) % 360
        self.assertAlmostEqual(latitude, 9 + 54.2 / 60, delta=5 / 60)
        self.assertAlmostEqual(longitude, 32 + 7.73 / 60, delta=15 / 60)


if __name__ == "__main__":
    unittest.main()
