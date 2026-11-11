import unittest

from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class PublicTimeReferenceTests(unittest.TestCase):
    def test_meridian_offset_remains_time_with_a_separate_reference(self):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=149,
            quantity="meridian_time_difference",
            role="historical_input",
            subject="observing clock",
            reference=None,
            components={"minute": "12"},
            time_reference="between_site_meridians",
        )
        row["normalized"] = normalize_quantity(row)
        self.assertEqual(row["normalized"]["magnitude"], "720")
        self.assertEqual(row["normalized"]["unit"], "second_of_time")
        result = public_assertion(row)
        self.assertEqual(result.get("time_reference"), "between_site_meridians")
        row["time_reference"] = "unreviewed narrative"
        with self.assertRaises(ValueError):
            public_assertion(row)
        row["time_reference"] = "between_site_meridians"
        row["quantity"] = "angular_separation"
        row["reference"] = "Vulture"
        with self.assertRaises(ValueError):
            public_assertion(row)
