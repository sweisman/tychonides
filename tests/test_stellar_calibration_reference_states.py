import unittest
from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class StellarCalibrationReferenceStatesTests(unittest.TestCase):
    def test_tabular_altitude_argument_does_not_become_an_observed_star_altitude(self):
        row = dict(
            id="assertion-v11-" + "c" * 20,
            volume=11,
            printed_page=84,
            quantity="altitude",
            components=dict(degree="1"),
            subject="Spica refraction table",
            reference=None,
            direction=None,
            role="historical_input",
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Source table argument must remain separately identified: " + str(error))
        self.assertEqual(out["normalized"]["magnitude"], "3600")
        self.assertEqual(out["role"], "historical_input")
        self.assertEqual(out["subject"], "Spica refraction table")

    def test_equatorial_refraction_components_keep_their_axes_and_historical_roles(self):
        for axis, value in (("declination", "1320"), ("right_ascension", "420")):
            row = dict(
                id="assertion-v11-" + "a" * 20,
                volume=11,
                printed_page=84,
                quantity="refraction_angle",
                components=dict(arcminute="22" if axis == "declination" else "7", arcsecond="0"),
                subject="Spica",
                reference=None,
                direction=None,
                role="historical_correction",
                source_component_label=axis,
                flags=["not_an_additional_raw_reading"],
            )
            row["normalized"] = normalize_quantity(row)
            try:
                out = public_assertion(row)
            except ValueError as error:
                self.fail("Equatorial refraction component must retain its axis: " + str(error))
            self.assertEqual(out["source_component_label"], axis)
            self.assertEqual(out["normalized"]["magnitude"], value)
            self.assertIsNone(out["normalized"]["signed_magnitude"])
            for change in (
                dict(role="recorded_reading"),
                dict(quantity="angular_separation"),
                dict(flags=[]),
            ):
                with self.subTest(axis=axis, change=change), self.assertRaises(ValueError):
                    public_assertion({**row, **change})

    def test_adopted_true_spica_declination_is_separate_from_an_observation(self):
        row = dict(
            id="assertion-v11-" + "b" * 20,
            volume=11,
            printed_page=84,
            quantity="declination",
            components=dict(degree="8", arcminute="57 1/2"),
            subject="Spica",
            reference=None,
            direction="south",
            role="adopted_value",
            source_coordinate_state="true",
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Adopted true Spica input must retain its state: " + str(error))
        self.assertEqual(out["normalized"]["signed_magnitude"], "-32250")
        self.assertEqual(out["source_coordinate_state"], "true")
        for change in (dict(role="recorded_coordinate"), dict(flags=[])):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion({**row, **change})

    def test_expected_true_stellar_declination_is_not_a_raw_observation(self):
        row = dict(
            id="assertion-v12-" + "b" * 20,
            volume=12,
            printed_page=348,
            quantity="declination",
            components=dict(degree="25", arcminute="25"),
            subject="heart of Scorpio",
            reference=None,
            direction=None,
            role="expected_calibration",
            source_coordinate_state="true",
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Expected stellar reference must retain its true label: " + str(error))
        self.assertEqual(out["source_coordinate_state"], "true")
        self.assertEqual(out["normalized"]["magnitude"], "91500")
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        for change in (dict(role="recorded_coordinate"), dict(flags=[]), dict(subject="Mars")):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion({**row, **change})

    def test_true_stellar_separation_retains_reduction_state_and_endpoints(self):
        row = dict(
            id="assertion-v12-" + "c" * 20,
            volume=12,
            printed_page=348,
            quantity="angular_separation",
            components=dict(degree="45", arcminute="56 1/6"),
            subject="Spica",
            reference="heart of Scorpio",
            direction=None,
            role="reduction",
            source_coordinate_state="true",
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("True stellar separation must retain its reduction state: " + str(error))
        self.assertEqual(out["source_coordinate_state"], "true")
        self.assertEqual(out["normalized"]["magnitude"], "165370")
        self.assertEqual(out["reference"], "heart of Scorpio")
        for change in (dict(role="recorded_reading"), dict(flags=[]), dict(reference="Mars")):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion({**row, **change})


if __name__ == "__main__":
    unittest.main()
