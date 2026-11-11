import unittest

from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class CalculationAngleTests(unittest.TestCase):
    def test_lettered_triangle_quantity_keeps_its_geometry_label_without_endpoints(self):
        norm = normalize_quantity(
            dict(quantity="calculation_angle", components={"degree": "31", "arcminute": "25¼"})
        )
        self.assertEqual(norm["magnitude"], "113115")
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=140,
            quantity="calculation_angle",
            role="calculation_intermediate",
            subject="Mars calculation",
            reference=None,
            geometry_label="BAC",
            geometry_column=1,
            flags=["historical_reduction_context"],
            normalized=norm,
        )
        result = public_assertion(row)
        self.assertEqual((result["geometry_label"], result["geometry_column"]), ("BAC", 1))
        self.assertIsNone(result["reference"])
        row["geometry_label"] = "unchecked private label"
        with self.assertRaises(ValueError):
            public_assertion(row)
        row["geometry_label"] = "BAC"
        row["geometry_column"] = 3
        with self.assertRaises(ValueError):
            public_assertion(row)
