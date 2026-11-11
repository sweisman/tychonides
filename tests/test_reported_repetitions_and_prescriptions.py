import copy
import unittest

from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class ReportedRepetitionAndPrescriptionTests(unittest.TestCase):
    def row(self, **extra):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=287,
            subject="Mars",
            reference="lower horn of Capricorn",
            quantity="angular_separation",
            role="recorded_reading",
            flags=[],
        )
        row.update(extra)
        row["normalized"] = normalize_quantity(
            dict(quantity=row["quantity"], components=dict(degree="46", arcminute="2"))
        )
        return row

    def test_reported_twice_qualifies_one_value_without_creating_a_clock(self):
        row = self.row(
            source_repeat_count=2,
            source_repetition_label="bis",
            flags=["source_repetition_note_present"],
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_repeat_count"), 2)
        self.assertEqual(out.get("source_repetition_label"), "bis")
        self.assertEqual(out["normalized"]["magnitude"], "165720")
        self.assertIsNone(out["event_id"])
        for change in (
            {"source_repeat_count": True},
            {"source_repeat_count": 3},
            {"flags": []},
            {"source_repetition_label": "private text"},
            {"role": "adopted_value"},
            {"quantity": "declination"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_prescribed_meridian_reduction_is_not_a_completed_correction(self):
        row = self.row(
            role="adopted_value",
            flags=["source_future_meridian_reduction", "not_an_additional_raw_reading"],
        )
        out = public_assertion(row)
        self.assertIn("source_future_meridian_reduction", out["flags"])
        self.assertEqual(out["normalized"]["magnitude"], "165720")
        self.assertIsNone(out["event_id"])
        for change in (
            {"role": "recorded_reading"},
            {"quantity": "clock_correction"},
            {"quantity": "altitude"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
