import unittest

from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion, unlinked_recorded_mars_declinations


class VenusComparisonTests(unittest.TestCase):
    def row(self):
        row = dict(
            id="assertion-v12-" + "b" * 20,
            volume=12,
            printed_page=153,
            quantity="angular_separation",
            role="recorded_reading",
            subject="Venus",
            reference="Mars",
            components={"degree": "48", "arcminute": "23"},
        )
        row["normalized"] = normalize_quantity(row)
        return row

    def test_both_venus_mars_endpoint_orders_and_venus_predictions_are_retained(self):
        row = self.row()
        out = public_assertion(row)
        self.assertEqual((out["subject"], out["reference"]), ("Venus", "Mars"))
        self.assertEqual(out["normalized"]["magnitude"], "174180")
        row.update(subject="Mars", reference="Venus")
        self.assertEqual(public_assertion(row)["reference"], "Venus")
        row.update(
            subject="Venus",
            reference=None,
            quantity="ecliptic_longitude",
            role="historical_prediction",
            model_name="Copernicus",
        )
        row["normalized"] = normalize_quantity(row)
        self.assertEqual(public_assertion(row)["model_name"], "Copernicus")
        row["model_name"] = "Alphonsine"
        self.assertEqual(public_assertion(row)["subject"], "Venus")
        row.update(role="reduction", quantity="longitude_difference", reference="mean Sun")
        del row["model_name"]
        row["normalized"] = normalize_quantity(row)
        self.assertEqual(public_assertion(row)["reference"], "mean Sun")
        row["subject"] = "private endpoint"
        with self.assertRaises(ValueError):
            public_assertion(row)

    def test_venus_does_not_enter_mars_declination_or_mars_only_comparison_counts(self):
        row = self.row()
        row.update(quantity="declination", reference=None, role="recorded_coordinate")
        row["normalized"] = normalize_quantity(row)
        out = public_assertion(row)
        self.assertEqual(unlinked_recorded_mars_declinations([out]), [])
        row.update(
            role="historical_comparison",
            model_name="Copernicus",
            quantity="clock_elapsed_time",
            components={"hour": "3"},
            comparison_relation="earlier_than_author",
            lower_bound_inclusive=True,
            flags=["source_lower_bound"],
        )
        row["normalized"] = normalize_quantity(row)
        with self.assertRaises(ValueError):
            public_assertion(row)
        row.update(
            role="editorial_addition",
            model_name="Alphonsine",
            quantity="ecliptic_latitude",
            components={"degree": "5", "arcminute": "4"},
            flags=["source_editorial_computation"],
            editorial_component_units=["arcminute"],
        )
        row["normalized"] = normalize_quantity(row)
        with self.assertRaises(ValueError):
            public_assertion(row)
