"""Regression coverage for native public meridian table formats."""

from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.catalog_release import write_catalogue
from src.numeric_integrity import validate_conversion
from src.online_catalogs import cds_records, jpl_records, run, usno_records


def fixed_line(size, values):
    line = [" "] * size
    for start, text in values:
        line[start : start + len(text)] = text
    return "".join(line)


class MeridianTablesTests(unittest.TestCase):
    def test_acquisition_rejects_an_unprotected_workspace_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "protected working storage"):
                run(Path(directory) / "public", Path(directory) / "base")
            self.assertFalse((Path(directory) / "public").exists())

    def test_complete_bundle_and_resume_use_shared_verified_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base, workspace = root / "base", root / "acquisition"
            write_catalogue(base, [], [], [], [], [], [], [], [], [], {})
            path = root / "sun.txt"
            path.write_text(self.jpl(), encoding="ascii")
            tables = [("jpl-wash6a", path, jpl_records, "wash6a", "https://example.org/sun")]
            with (
                patch("src.online_catalogs.input_tables", return_value=tables),
                patch("src.import_collection.WORK_ROOT", root),
            ):
                first = run(workspace, base, repeat=True)
                self.assertEqual(first["combined_quantities"], 3)
                self.assertEqual(first["combined_groups"], 1)
                self.assertTrue(first["repeated_outputs_identical"])
                with patch(
                    "src.online_catalogs.write_catalogue", side_effect=AssertionError("rebuilt")
                ):
                    self.assertEqual(run(workspace, base), first)

    def jpl(self, target="010", station="7866"):
        return fixed_line(
            80,
            [
                (0, "P" + target),
                (4, "244000050000"),
                (21, station),
                (28, "1"),
                (33, "151137363"),
                (42, "0"),
                (50, "-00105060"),
                (59, "0"),
            ],
        )

    def test_jpl_sun_and_satellite_identities_and_exact_sign(self):
        rows = list(jpl_records(self.jpl(), "wash6a"))
        self.assertEqual({r["subject"] for r in rows}, {"Sun"})
        dec = next(r for r in rows if r["quantity"] == "declination")
        self.assertEqual(Fraction(dec["derived_normalization"]["magnitude"]), -Fraction(3253, 5))
        moon = list(jpl_records(self.jpl("606", "999 "), "bordeaux"))
        self.assertEqual(moon[0]["subject"], "Titan")
        self.assertEqual(moon[0]["original_target_code"], "606")

    def test_la_palma_native_station_is_not_replaced_by_documentation_code(self):
        rows = list(jpl_records(self.jpl("503", "9501"), "lapalma"))
        self.assertEqual(rows[0]["observatory_telescope_code"], "9501")
        with self.assertRaisesRegex(ValueError, "station"):
            list(jpl_records(self.jpl("503", "9001"), "lapalma"))

    def test_unrecognized_jpl_target_or_record_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "target"):
            list(jpl_records(self.jpl("799"), "wash6a"))
        with self.assertRaisesRegex(ValueError, "non-record"):
            list(jpl_records("unexpected data", "wash6a"))

    def test_usno_other_target_preserves_incomplete_coordinate(self):
        line = 'Amphitrite 07 57 12.722 +30 13       2447162.07136     E     7"'
        rows = list(usno_records(line, "w2"))
        self.assertEqual({r["subject"] for r in rows}, {"Amphitrite"})
        dec = next(r for r in rows if r["quantity"] == "declination")
        self.assertIn("incomplete_coordinate", dec["flags"])
        self.assertNotIn("derived_normalization", dec)
        self.assertEqual(dec["site"], "Black Birch")
        self.assertEqual(dec["clamp_code"], "E")

    def test_carlsberg_geographos_and_separated_negative_zero_sign(self):
        line = fixed_line(
            83,
            [
                (1, "9001620"),
                (12, "1620"),
                (18, "Geographos"),
                (32, "2448647.663371"),
                (46, "*"),
                (50, "11  1 36.045"),
                (64, "- 0 37 21.13"),
                (78, " 4.92"),
            ],
        )
        rows = list(cds_records(line, "carlsberg"))
        dec = next(r for r in rows if r["quantity"] == "declination")
        self.assertEqual(dec["subject"], "(1620) Geographos")
        self.assertEqual(dec["coordinate_origin"], "topocentric")
        self.assertEqual(dec["time_scale"], "TT")
        self.assertEqual(dec["literal"], "- 0 37 21.13")
        self.assertEqual(dec["derived_normalization"]["magnitude"], "-224113/100")
        self.assertEqual(dec["corrections"][0]["status"], "not_applied")
        self.assertIn("source_internal_error_above_0.75_arcsecond", dec["flags"])
        for row in rows:
            self.assertEqual(validate_conversion(row), row.get("derived_normalization"))

    def test_tokyo_applied_phase_corrections_and_residuals_stay_separate(self):
        line = "MARS           1  2446455.415120  1986  1 24    15 31 37.363  -0.032 -0.017   -18 10 50.60  -0.09 +0.06    +1.79  +0.59"
        rows = {r["quantity"]: r for r in cds_records(line, "tokyo")}
        self.assertEqual(len(rows), 9)
        phase = rows["phase_correction_ra"]
        self.assertEqual(phase["normalized"]["magnitude"], "-17/1000")
        self.assertEqual(phase["unit"], "second_of_time")
        self.assertEqual(phase["correction_status"], "applied_as_published")
        self.assertEqual(rows["observed_minus_computed_dec"]["normalized"]["magnitude"], "-9/100")
        self.assertEqual(rows["right_ascension"]["subject"], "Mars")


if __name__ == "__main__":
    unittest.main()
