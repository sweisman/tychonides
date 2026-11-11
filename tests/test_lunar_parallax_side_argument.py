import unittest
from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class LunarParallaxSideArgumentTests(unittest.TestCase):
    def test_source_side_retains_printed_arcminutes_without_geometric_reinterpretation(self):
        row = dict(
            id="assertion-v12-" + "d" * 20,
            volume=12,
            printed_page=412,
            quantity="calculation_angle",
            components=dict(arcminute="20"),
            subject="Moon centre",
            reference=None,
            direction=None,
            role="historical_input",
            argument_name="parallax_longitude_side_as_stated",
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Printed lunar calculation side must remain a source argument: " + str(error))
        self.assertEqual(out["normalized"]["magnitude"], "1200")
        self.assertEqual(out["normalized"]["unit"], "arcsecond")
        self.assertEqual(out["argument_name"], "parallax_longitude_side_as_stated")
        for change in (
            dict(role="recorded_reading"),
            dict(subject="Mars"),
            dict(flags=[]),
            dict(quantity="altitude"),
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion({**row, **change})


if __name__ == "__main__":
    unittest.main()
