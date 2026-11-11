import unittest
from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class ReducedDeclinationStateTests(unittest.TestCase):
    def test_apparent_declination_input_retains_explicit_reduction_label(self):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=348,
            quantity="declination",
            components=dict(degree="19", arcminute="1"),
            subject="Mars",
            reference=None,
            direction="south",
            role="historical_input",
            source_coordinate_state="apparent",
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Explicit apparent adopted declination must retain its state: " + str(error))
        self.assertEqual(out["source_coordinate_state"], "apparent")
        self.assertEqual(out["normalized"]["signed_magnitude"], "-68460")
        with self.assertRaises(ValueError):
            public_assertion({**row, "role": "recorded_coordinate"})

    def test_true_declination_input_retains_state_without_becoming_raw(self):
        row = dict(
            id="assertion-v12-" + "9" * 20,
            volume=12,
            printed_page=347,
            quantity="declination",
            components=dict(degree="17", arcminute="5"),
            subject="Mars",
            reference=None,
            direction="south",
            role="historical_input",
            source_coordinate_state="true",
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail(
                "Explicit true declination must retain its reduced input state: " + str(error)
            )
        self.assertEqual(out["source_coordinate_state"], "true")
        self.assertEqual(out["normalized"]["magnitude"], "61500")
        self.assertEqual(out["normalized"]["signed_magnitude"], "-61500")
        for changes in (
            dict(role="recorded_coordinate"),
            dict(flags=[]),
            dict(subject="Spica"),
            dict(source_coordinate_state="parallax_included_as_stated"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                public_assertion({**row, **changes})


if __name__ == "__main__":
    unittest.main()
