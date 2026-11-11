import copy
import unittest

from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class IncompleteClockAndQualityAttributionTests(unittest.TestCase):
    def test_unitless_clock_drift_preserves_unknown_scale(self):
        row = dict(
            id="assertion-v11-" + "a" * 20,
            volume=11,
            printed_page=332,
            subject="observing clock",
            reference=None,
            quantity="clock_drift",
            role="calibration",
            direction=None,
            components={},
            flags=[
                "source_notation_unresolved",
                "clock_runs_fast",
                "clock_drift_not_applied_to_times",
            ],
        )
        row["normalized"] = normalize_quantity(row)
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["status"], "unsupported")
        self.assertEqual(out["normalized"]["unit"], "second_of_time")
        self.assertIsNone(out["normalized"]["magnitude"])
        for change in (
            {"subject": "Mars"},
            {"role": "recorded_reading"},
            {"reference": "Sun"},
            {"direction": "east"},
            {"components": {"minute": "7 1/2"}},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_missing_clock_denominator_keeps_time_unit_without_zero_filling(self):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=288,
            subject="observing clock",
            reference=None,
            quantity="recorded_clock",
            role="recorded_clock",
            flags=["absolute_time_unestablished"],
            normalized=normalize_quantity(dict(quantity="recorded_clock", incomplete=True)),
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["unit"], "second_of_time")
        self.assertEqual(out["normalized"]["status"], "incomplete")
        self.assertTrue(
            all(
                out["normalized"][key] is None
                for key in ("magnitude", "magnitude_degrees", "signed_magnitude")
            )
        )
        bad = copy.deepcopy(row)
        bad["normalized"]["magnitude"] = "0"
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_later_hand_qualifies_quality_note_without_reattributing_measurement(self):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=288,
            subject="mouth of Pegasus",
            reference="outermost star in wing of Pegasus",
            quantity="angular_separation",
            role="calibration",
            flags=[
                "not_certain_enough",
                "source_quality_note_present",
                "source_quality_note_later_hand",
            ],
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components=dict(degree="36", arcminute="42"))
            ),
        )
        out = public_assertion(row)
        self.assertIn("source_quality_note_later_hand", out["flags"])
        self.assertEqual(out["normalized"]["magnitude"], "132120")
        self.assertNotIn("observer_names", out)
        for change in (
            {"role": "recorded_reading"},
            {"quantity": "declination"},
            {"flags": ["source_quality_note_later_hand"]},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
