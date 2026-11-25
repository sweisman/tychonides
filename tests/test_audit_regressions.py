from contextlib import closing
from fractions import Fraction
import sqlite3
import unittest

from src.coordinate_staging import parse_coordinate
from src.core import fraction_text, hemisphere, recorded_clock
from src.csv_projection import project_csv, same_cell
from src.normalization import normalize_quantity
from src.numeric_integrity import (
    apply_jpl_coordinate_policy,
    qualify_retained_conversion,
    recompute_conversion,
)


class AuditRegressions(unittest.TestCase):
    def test_jpl_padded_zero_right_ascension_is_a_placeholder_in_the_affected_series(self):
        row = dict(
            source_id="jpl-wash6a",
            unit="hhmmss_millisecond",
            literal=" 00000000",
            derived_normalization={
                "magnitude": "0",
                "unit": "arcsecond",
                "method": "JPL_fixed_width_conversion",
            },
        )
        self.assertEqual(apply_jpl_coordinate_policy(row), ("jpl_zero_placeholder",))
        self.assertNotIn("derived_normalization", row)
        self.assertEqual(recompute_conversion(row, legacy_jpl=True)["magnitude"], "0")

    def test_literal_note_marker_does_not_become_arcseconds(self):
        self.assertEqual(fraction_text("12²"), "12²")
        self.assertIsNone(parse_coordinate("63 3²")["components"])
        self.assertEqual(parse_coordinate("12° 30′ 1/2″")["normalized"]["magnitude"], "90001/2")

    def test_clock_and_altitude_labels_do_not_supply_hemisphere(self):
        self.assertIsNone(hemisphere("Declination at H. 6 M. 30"))
        self.assertIsNone(hemisphere("Alt. Merid. 34 5"))
        self.assertEqual(hemisphere("Declination Bor. H. 5 M. 3"), 1)

    def test_ranges_preserve_valid_endpoints_and_exclude_impossible_points(self):
        self.assertIsNone(recorded_clock("H. 24"))
        self.assertEqual(recorded_clock("H. 23 M. 59 S. 59"), "86399")
        for quantity, parts in (
            ("recorded_clock", {"hour": "24"}),
            ("declination", {"degree": "90", "arcminute": "1"}),
            ("altitude", {"degree": "91"}),
        ):
            with self.subTest(quantity=quantity), self.assertRaisesRegex(ValueError, "range"):
                normalize_quantity(dict(quantity=quantity, components=parts))
        self.assertEqual(
            normalize_quantity(dict(quantity="clock_elapsed_time", components={"hour": "24"}))[
                "magnitude"
            ],
            "86400",
        )
        with self.assertRaisesRegex(ValueError, "range"):
            normalize_quantity(
                dict(quantity="clock_elapsed_time", components={"day": "1", "hour": "24"})
            )
        native = {"literal": "00 59 0", "unit": "sexagesimal_degree"}
        self.assertEqual(recompute_conversion(native)["magnitude"], "3540")
        with self.assertRaises(ValueError):
            recompute_conversion(dict(native, literal="00 60 0"))

    def test_decimal_parity_detects_rounding_exact_values_can_represent(self):
        from src.catalog_release import SCHEMA

        expected = float(Fraction(1, 7))
        with closing(sqlite3.connect(":memory:")) as db:
            db.executescript(SCHEMA)
            db.execute("PRAGMA foreign_keys=OFF")
            db.execute("""
                INSERT INTO quantities
                (id, expression, role, source_id, source_entry_id, original_json,
                 components_json, uncertainty_json, scientific_metadata_json)
                VALUES ('q', '1/7', 'historical_input', 's', '1',
                  '{"quantity":"altitude","subject":"Mars","normalized":{"status":"exact"}}',
                  '{}', '{}', '{}')
            """)
            db.execute("INSERT INTO sources(id,data_json) VALUES ('s','{}')")
            db.execute("""
                INSERT INTO interpretations
                (quantity_id,version,quantity,status,value_exact,normalized_json,components_json,flags_json)
                VALUES ('q',0,'altitude','exact','1/7','{}','{}','[]')
            """)
            self.assertEqual(next(project_csv(db, ("value_decimal",)))["value_decimal"], expected)
        self.assertTrue(same_cell("value_decimal", str(expected), expected))
        self.assertFalse(same_cell("value_decimal", str(round(expected, 6)), expected))

    def test_counted_sign_endpoint_requires_zero_lower_components(self):
        parts = {"sign_count": "5", "degree": "30", "arcminute": "0"}
        row = {"quantity": "calculation_angle", "components": parts}
        self.assertEqual(normalize_quantity(row)["magnitude"], "648000")
        parts["arcminute"] = "1"
        self.assertEqual(normalize_quantity(row)["normalization_issue"], "degree_outside_sign")

    def test_jpl_whole_minute_field_is_a_seconds_placeholder_in_washington_6b_and_6c(self):
        converted = {"unit": "arcsecond", "method": "JPL_fixed_width_conversion"}
        declination = dict(
            source_id="jpl-wash6b",
            unit="signed_ddmmss_centisecond",
            literal=" 11030000",
            derived_normalization=dict(converted, magnitude="39780"),
        )
        self.assertEqual(
            qualify_retained_conversion(declination), ("jpl_zero_seconds_placeholder",)
        )
        self.assertEqual(declination["flags"], ["jpl_zero_seconds_placeholder"])
        self.assertNotIn("derived_normalization", declination)
        right_ascension = dict(
            source_id="jpl-wash6c", unit="hhmmss_millisecond", literal="233500000"
        )
        self.assertEqual(
            apply_jpl_coordinate_policy(right_ascension), ("jpl_zero_seconds_placeholder",)
        )
        self.assertIsNone(recompute_conversion(right_ascension))
        for source_id, unit, literal in (
            ("jpl-wash6a", "hhmmss_millisecond", "233500000"),
            ("jpl-wash6b", "hhmmss_millisecond", "233500010"),
            ("jpl-wash6b", "signed_ddmmss_centisecond", "-11030010"),
        ):
            row = dict(source_id=source_id, unit=unit, literal=literal)
            self.assertEqual(apply_jpl_coordinate_policy(row), ())
            self.assertIsNotNone(recompute_conversion(row))

    def test_jpl_seconds_placeholder_keeps_an_indeterminate_sign(self):
        row = dict(
            source_id="jpl-wash6b",
            unit="signed_ddmmss_centisecond",
            literal=" 00580000",
            flags=["jpl_declination_sign_indeterminate"],
            derived_normalization={
                "magnitude": "3480",
                "unit": "arcsecond",
                "method": "JPL_fixed_width_conversion",
                "sign_indeterminate": True,
            },
        )
        self.assertEqual(
            qualify_retained_conversion(row),
            ("jpl_zero_seconds_placeholder", "jpl_declination_sign_indeterminate"),
        )
        self.assertEqual(
            row["flags"], ["jpl_declination_sign_indeterminate", "jpl_zero_seconds_placeholder"]
        )
        self.assertNotIn("derived_normalization", row)
        self.assertEqual(qualify_retained_conversion(row), tuple(reversed(row["flags"])))

    def test_jpl_seconds_placeholder_rejects_a_fabricated_earlier_value(self):
        row = dict(
            source_id="jpl-wash6c",
            unit="signed_ddmmss_centisecond",
            literal="-16410000",
            derived_normalization={
                "magnitude": "-60061",
                "unit": "arcsecond",
                "method": "JPL_fixed_width_conversion",
            },
        )
        with self.assertRaisesRegex(ValueError, "Derived normalization differs"):
            qualify_retained_conversion(row)
