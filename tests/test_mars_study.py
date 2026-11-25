"""The published Mars study regenerates from its committed inputs."""

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


class MarsSelectionTests(unittest.TestCase):
    def test_sexagesimal_places_are_exact(self):
        from mars_select import sexagesimal

        self.assertEqual(str(sexagesimal("0 · 9 6 40")), "82/9")
        self.assertEqual(str(sexagesimal("4 · 8 20 0")), "745/3")
        self.assertEqual(str(sexagesimal("28 8 40")), "2533/90")

    def test_a_month_that_contradicts_the_mean_longitude_column_is_flagged(self):
        import mars_select

        with (EXAMPLES / "mars-oppositions.csv").open(encoding="utf-8", newline="") as source:
            rows = list(csv.DictReader(source))
        for row in rows:
            for field in ("year", "month", "day", "hour", "minute"):
                row[field] = int(row[field])
        printed = {row["number"]: row["month"] for row in rows}
        tenth = next(row for row in rows if row["number"] == "X")
        tenth["month"] = mars_select.MONTHS[tenth["printed_month"][:3].lower()]
        mars_select.check_dates(rows)
        self.assertEqual({row["number"]: row["month"] for row in rows}, printed)
        self.assertEqual(
            [row["number"] for row in rows if row["date_basis"] != "printed date"], ["X"]
        )

    @unittest.skipUnless(CATALOG, "set TYCHONIDES_CATALOG to the unpacked catalog to run")
    def test_selection_files_match_the_catalog(self):
        import mars_select

        names = {
            "mars-oppositions.csv": mars_select.OPPOSITION_FIELDS,
            "mars-observations.csv": mars_select.OBSERVATION_FIELDS,
            "mars-predictions.csv": mars_select.PREDICTION_FIELDS,
            "mars-observations-excluded.csv": mars_select.EXCLUDED_FIELDS,
        }
        with closing(sqlite3.connect(f"file:{CATALOG}?mode=ro", uri=True)) as db:
            results = mars_select.select(db)
        with tempfile.TemporaryDirectory() as scratch:
            for (name, fields), rows in zip(names.items(), results, strict=True):
                mars_select.write(Path(scratch) / name, fields, rows)
                self.assertEqual(table(Path(scratch) / name), table(EXAMPLES / name), name)


@unittest.skipUnless(importlib.util.find_spec("numpy"), "the study scripts need NumPy")
class MarsStudyTests(unittest.TestCase):
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
        import mars_1595

        with tempfile.TemporaryDirectory() as scratch:
            mars_1595.write_tables(Path(scratch))
            produced = sorted(path.name for path in Path(scratch).iterdir())
            self.assertEqual(
                produced, sorted(path.name for path in FIGURES.glob("mars-1595-*.csv"))
            )
            for name in produced:
                self.assert_tables_close(table(Path(scratch) / name), table(FIGURES / name), name)

    def test_heliocentric_and_earth_centered_directions_agree(self):
        # Tolerance fixed in advance: a billionth of a degree of longitude.
        import mars_model
        import numpy as np

        opposition = mars_model.load_oppositions()["VIII"]
        days = np.linspace(-60, 60, 241)
        _, copernican, tychonic, _ = mars_model.models(days, opposition)
        sun = tychonic.guide
        heliocentric = np.angle((tychonic.mars - sun) - (tychonic.earth - sun), deg=True)
        self.assertLess(np.abs(mars_model.wrapped(heliocentric - tychonic.longitude)).max(), 1e-9)
        sun_from_earth = -copernican.earth
        earth_centered = np.angle(sun_from_earth + copernican.mars, deg=True)
        self.assertLess(
            np.abs(mars_model.wrapped(earth_centered - copernican.longitude)).max(), 1e-9
        )

    def test_every_curve_passes_through_the_anchor(self):
        import mars_model

        for opposition in mars_model.load_oppositions().values():
            for track in mars_model.models([0.0], opposition):
                gap = mars_model.wrapped(track.longitude[0] - opposition.longitude)
                self.assertLess(abs(gap), 1e-6, f"{track.key} at opposition {opposition.number}")

    def test_time_conventions(self):
        import mars_model

        self.assertEqual(mars_model.julian_day_number(date(1582, 10, 5)), 2299161)
        self.assertEqual(mars_model.clock("", ""), (12.0, "nominal noon"))
        self.assertEqual(mars_model.clock("", "49200")[0], 12 + 49200 / 3600)
        self.assertEqual(
            mars_model.clock("morning", "12900"), (12900 / 3600, "printed morning hour")
        )
        self.assertEqual(
            mars_model.clock("before_noon", "14400")[1], "nominal noon, hour label open"
        )
        self.assertEqual(mars_model.clock("morning", "46800")[1], "nominal noon, hour label open")


if __name__ == "__main__":
    unittest.main()
