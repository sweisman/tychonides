import unittest

from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class HistoricalDailyMotionTests(unittest.TestCase):
    def test_joint_motion_is_not_assigned_as_each_planets_individual_rate(self):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=280,
            quantity="angular_daily_motion",
            subject="Jupiter",
            reference="simple Sun",
            role="historical_input",
            components={"degree": "1", "arcminute": "7", "arcsecond": "8"},
            flags=["source_joint_motion_unallocated"],
        )
        row["normalized"] = normalize_quantity(row)
        result = public_assertion(row)
        self.assertEqual(result["normalized"]["magnitude"], "4028")
        self.assertEqual(result["normalized"]["unit"], "arcsecond_per_source_day")
        self.assertEqual(result["reference"], "simple Sun")
        self.assertIn("source_joint_motion_unallocated", result["flags"])
        for quantity, role, reference in [
            ("longitude_difference", "historical_input", "simple Sun"),
            ("angular_daily_motion", "recorded_reading", "simple Sun"),
            ("angular_daily_motion", "historical_input", None),
        ]:
            bad = dict(row, quantity=quantity, role=role, reference=reference)
            bad["normalized"] = normalize_quantity(bad)
            with (
                self.subTest(quantity=quantity, role=role, reference=reference),
                self.assertRaises(ValueError),
            ):
                public_assertion(bad)

    def test_day_component_is_elapsed_duration_not_calendar_day(self):
        row = dict(
            quantity="clock_elapsed_time", components={"day": "3", "hour": "23", "minute": "30"}
        )
        self.assertEqual(normalize_quantity(row)["magnitude"], "343800")
        row["quantity"] = "calculation_epoch"
        with self.assertRaises(ValueError):
            normalize_quantity(row)

    def test_daily_motion_stays_a_rate_in_public_data(self):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=150,
            quantity="angular_daily_motion",
            subject="Mars",
            reference=None,
            role="historical_input",
            components={"arcminute": "18", "arcsecond": "13"},
        )
        norm = normalize_quantity(row)
        self.assertEqual(norm["magnitude"], "1093")
        self.assertEqual(norm["unit"], "arcsecond_per_source_day")
        self.assertIsNone(norm["magnitude_degrees"])
        row["normalized"] = norm
        self.assertEqual(public_assertion(row)["normalized"]["unit"], "arcsecond_per_source_day")
        row["normalized"] = dict(norm, unit="arcsecond")
        with self.assertRaises(ValueError):
            public_assertion(row)
