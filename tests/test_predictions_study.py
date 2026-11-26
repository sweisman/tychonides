"""The printed-predictions tables regenerate from their committed inputs."""

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


class PredictionSelectionTests(unittest.TestCase):
    def test_a_longitude_without_a_sign_keeps_its_value_within_the_sign(self):
        import predictions_select

        signed = predictions_select.value(
            "ecliptic_longitude", "arcsecond", None, {"zodiac_longitude_degrees": "247/2"}
        )
        self.assertEqual(signed, ("247/2", "printed sign", ""))
        bare = predictions_select.value(
            "ecliptic_longitude", "arcsecond", None, {"magnitude_degrees": "77/6"}
        )
        self.assertEqual(bare, ("77/6", "within the sign", "no printed zodiac sign"))

    def test_a_latitude_needs_a_printed_direction(self):
        import predictions_select

        north = predictions_select.value("ecliptic_latitude", "arcsecond", "5400", {})
        self.assertEqual(north, ("3/2", "printed direction", ""))
        open_direction = predictions_select.value("ecliptic_latitude", "arcsecond", None, {})
        self.assertEqual(open_direction, ("", "", "no printed latitude direction"))

    @unittest.skipUnless(CATALOG, "set TYCHONIDES_CATALOG to the unpacked catalog to run")
    def test_input_files_match_the_catalog(self):
        import predictions_select

        with closing(sqlite3.connect(f"file:{CATALOG}?mode=ro", uri=True)) as db:
            predictions, references, excluded = predictions_select.select(db)
        self.assertEqual((len(predictions), len(references), len(excluded)), (485, 340, 284))
        files = {
            "printed-predictions.csv": (predictions_select.PREDICTION_FIELDS, predictions),
            "printed-predictions-references.csv": (predictions_select.REFERENCE_FIELDS, references),
            "printed-predictions-excluded.csv": (predictions_select.EXCLUDED_FIELDS, excluded),
        }
        with tempfile.TemporaryDirectory() as scratch:
            for name, (fields, rows) in files.items():
                predictions_select.write(Path(scratch) / name, fields, rows)
                self.assertEqual(table(Path(scratch) / name), table(EXAMPLES / name), name)


@unittest.skipUnless(importlib.util.find_spec("numpy"), "the study scripts need NumPy")
class PredictionStudyTests(unittest.TestCase):
    def test_published_tables_regenerate_from_committed_inputs(self):
        import printed_predictions

        with tempfile.TemporaryDirectory() as scratch:
            printed_predictions.write_tables(Path(scratch))
            produced = sorted(path.name for path in Path(scratch).iterdir())
            self.assertEqual(
                produced, sorted(path.name for path in FIGURES.glob("printed-predictions-*.csv"))
            )
            for name in produced:
                self.assertEqual(table(Path(scratch) / name), table(FIGURES / name), name)

    def test_cached_ephemeris_covers_exactly_the_instants_the_study_uses(self):
        import printed_predictions

        cached = {
            (row[0], row[1]) for row in table(EXAMPLES / "printed-predictions-ephemeris.csv")[1:]
        }
        wanted = {
            (body, jd) for body, epochs in printed_predictions.instants().items() for jd in epochs
        }
        self.assertEqual(cached, wanted)

    def test_differences_wrap_and_respect_a_missing_sign(self):
        import printed_predictions

        self.assertAlmostEqual(printed_predictions.gap(359.5, 0.5, "printed sign"), -1.0)
        # 12° within a sign against 342°, which is 12° of Pisces.
        self.assertAlmostEqual(printed_predictions.gap(12.5, 342.0, "within the sign"), 0.5)
        self.assertAlmostEqual(printed_predictions.mean_angle([359.0, 1.0], [0.5, 0.5]), 360.0)

    def test_the_moon_is_compared_only_with_a_printed_hour(self):
        import printed_predictions

        rows = [row for row in printed_predictions.compare() if row["body"] == "Moon"]
        self.assertTrue(rows)
        for row in rows:
            timed = row["de441_time_basis"] == "printed hours"
            self.assertEqual(bool(row["prediction_minus_de441_arcmin"]), timed, row["id"])
            self.assertEqual(bool(row["prediction_minus_log_arcmin"]), timed, row["id"])

    def test_a_calculation_hour_is_used_only_when_its_label_places_it(self):
        import printed_predictions

        item = {"julian_date": "1595-09-30", "daypart": "", "epoch_seconds": "14400"}
        noon = printed_predictions.mm.jd_ut(date(1595, 9, 30), 12.0)
        self.assertAlmostEqual(printed_predictions.calculation_instant(item) - noon, 4 / 24)
        # "4h A.M." can be a clock hour or four hours before noon.
        marked = {**item, "daypart": "before_noon"}
        self.assertIsNone(printed_predictions.calculation_instant(marked))
        self.assertIsNone(printed_predictions.calculation_instant({**item, "epoch_seconds": ""}))
        used = [
            row
            for row in printed_predictions.compare()
            if row["de441_time_basis"] == "calculation hour"
        ]
        self.assertEqual(len(used), 63)


if __name__ == "__main__":
    unittest.main()
