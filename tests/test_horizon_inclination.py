import copy
import unittest

from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class HorizonInclinationTests(unittest.TestCase):
    def fixture(self):
        row = dict(
            id="assertion-v12-" + "c" * 20,
            volume=12,
            printed_page=225,
            quantity="horizon_inclination",
            role="historical_input",
            subject="Mars",
            reference="Mercury",
            direction=None,
            components={"degree": "50"},
            flags=["source_approximate"],
        )
        row["normalized"] = normalize_quantity(row)
        return row

    def test_approximate_horizon_inclination_is_an_angular_input_with_both_bodies(self):
        row = self.fixture()
        out = public_assertion(row)
        self.assertEqual(
            (out["normalized"]["magnitude"], out["normalized"]["unit"]), ("180000", "arcsecond")
        )
        self.assertEqual((out["subject"], out["reference"]), ("Mars", "Mercury"))
        self.assertIn("source_approximate", out["flags"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        self.assertIsNone(out["event_id"])

    def test_missing_endpoints_orientation_and_time_units_are_not_horizon_inclinations(self):
        row = self.fixture()
        for update in (
            dict(reference=None),
            dict(reference="Mars"),
            dict(direction="north"),
            dict(role="recorded_clock"),
        ):
            wrong = copy.deepcopy(row)
            wrong.update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                public_assertion(wrong)
        wrong = copy.deepcopy(row)
        wrong["normalized"]["unit"] = "second_of_time"
        with self.assertRaises(ValueError):
            public_assertion(wrong)
