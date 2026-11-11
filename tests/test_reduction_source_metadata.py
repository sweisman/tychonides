import copy
import unittest

from src.catalog import normalize_quantity
from src.date_claims import project_date_claims
from src.public_checkpoint import public_assertion


class ReductionSourceMetadataTests(unittest.TestCase):
    def test_parallax_included_label_preserves_the_coordinate_without_a_second_correction(self):
        row = self.row(
            "ecliptic_latitude",
            {"degree": "0", "arcminute": "24", "arcsecond": "40"},
            subject="Mars",
            role="reduction",
            direction="north",
            source_coordinate_state="parallax_included_as_stated",
            flags=["historical_parallax_not_detection"],
        )
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Reviewed included-parallax label must export: " + str(error))
        self.assertEqual(out["normalized"]["magnitude"], "1480")
        self.assertEqual(out["normalized"]["signed_magnitude"], "1480")
        self.assertEqual(out["source_coordinate_state"], "parallax_included_as_stated")
        self.assertNotIn("source_parallax_operation", out)
        for change in (
            {"role": "recorded_coordinate"},
            {"quantity": "declination"},
            {"subject": "Jupiter"},
            {"reference": "Earth"},
            {"flags": []},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_latitude_complement_is_a_calculation_angle_not_a_planet_latitude(self):
        row = self.row(
            "calculation_angle",
            {"degree": "89", "arcminute": "46", "arcsecond": "10"},
            subject="Mars",
            role="calculation_intermediate",
            argument_name="latitude_complement",
        )
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Reviewed latitude complement must export: " + str(error))
        self.assertEqual(out["quantity"], "calculation_angle")
        self.assertEqual(out["argument_name"], "latitude_complement")
        self.assertEqual(out["normalized"]["magnitude"], "323170")
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        for change in (
            {"quantity": "ecliptic_latitude"},
            {"role": "recorded_coordinate"},
            {"subject": "Jupiter"},
            {"direction": "north"},
            {"reference": "Earth"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_adopted_ra_can_prefer_a_stellar_route_without_inventing_a_weight(self):
        row = self.row(
            "right_ascension",
            {"degree": "351", "arcminute": "5", "arcsecond": "0"},
            subject="Mars",
            role="adopted_value",
            source_reduction_method="adoption",
            source_reduction_references=[],
            source_adoption_preference="bright star of Aries",
            flags=["historical_adoption_algorithm_unstated"],
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_adoption_preference"), "bright star of Aries")
        self.assertIsNone(out["reference"])
        self.assertEqual(out["source_reduction_references"], [])
        self.assertEqual(out["normalized"]["magnitude"], "1263900")
        self.assertNotIn("weight", out)
        for change in (
            {"role": "recorded_reading"},
            {"role": "historical_input"},
            {"quantity": "angular_separation"},
            {"source_adoption_preference": "private name"},
            {"source_adoption_preference": None},
            {"source_reduction_method": "meridian_altitude"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_right_ascension_route_keeps_comparison_star_separate_from_coordinate_origin(self):
        row = self.row(
            "right_ascension",
            {"degree": "346", "arcminute": "42", "arcsecond": "50"},
            subject="Mars",
            source_reduction_method="comparison_directions",
            source_reduction_references=["Vulture"],
        )
        result = public_assertion(row)
        self.assertEqual(result.get("source_reduction_references"), ["Vulture"])
        self.assertEqual(result["normalized"]["magnitude"], "1248170")
        self.assertIsNone(result["reference"])
        for change in ({"role": "historical_input"}, {"quantity": "angular_separation"}):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def row(self, quantity="ecliptic_latitude", components=None, **kwargs):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=280,
            quantity=quantity,
            role="reduction",
            subject="Jupiter",
            reference=None,
            direction=None,
            flags=[],
            components=components or {"degree": "0", "arcminute": "18", "arcsecond": "0"},
        )
        row.update(kwargs)
        row["normalized"] = normalize_quantity(row)
        return row

    def test_observation_date_and_reduction_target_keep_separate_source_roles(self):
        contexts = [
            dict(
                id="context-v12-" + char * 20,
                volume=12,
                kind="recorded_date",
                value=dict(year=1593, month=6, day=day),
                calendar=None,
                day_origin=None,
                source_date_role=role,
            )
            for char, day, role in [("a", 25, "observation_label"), ("b", 29, "calculation_target")]
        ]
        result = project_date_claims(
            contexts, [dict(id="a", volume=12, context_ids=[c["id"] for c in contexts])], []
        )
        self.assertEqual(
            [(c["day"], c.get("source_date_role")) for c in result["date_claims"]],
            [(25, "observation_label"), (29, "calculation_target")],
        )
        self.assertTrue(
            all(
                c["absolute_timestamp"] is None and c["day_origin"] is None
                for c in result["date_claims"]
            )
        )
        bad = copy.deepcopy(contexts)
        bad[0]["source_date_role"] = "private narrative"
        with self.assertRaises(ValueError):
            project_date_claims(bad, [], [])

    def test_midnight_source_label_keeps_twelve_hours_without_becoming_a_clock(self):
        row = self.row(
            "calculation_epoch",
            {"hour": "12", "minute": "0"},
            role="calculation_epoch",
            subject="calculation epoch",
            time_reference="source_midnight_label",
        )
        out = public_assertion(row)
        self.assertEqual(out["time_reference"], "source_midnight_label")
        self.assertEqual(out["normalized"]["magnitude"], "43200")
        self.assertNotIn("absolute_timestamp", out)
        for change in (
            {"quantity": "recorded_clock"},
            {"role": "recorded_reading"},
            {
                "normalized": normalize_quantity(
                    dict(quantity="calculation_epoch", components={"hour": "0"})
                )
            },
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_refraction_free_coordinate_does_not_assert_parallax_was_removed(self):
        row = self.row(source_coordinate_state="free_of_refraction")
        out = public_assertion(row)
        self.assertEqual(out["source_coordinate_state"], "free_of_refraction")
        self.assertIsNone(out["direction"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        bad = copy.deepcopy(row)
        bad["quantity"] = "altitude"
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_apparent_coordinate_keeps_its_source_label_without_implying_refraction(self):
        row = self.row(
            "ecliptic_latitude",
            {"degree": "6", "arcminute": "6"},
            subject="Mars",
            source_coordinate_state="apparent",
            direction="south",
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_coordinate_state"), "apparent")
        self.assertEqual(out["normalized"]["signed_magnitude"], "-21960")
        self.assertNotIn("refraction_correction", out)
        for change in ({"quantity": "declination"}, {"role": "recorded_reading"}):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_after_midnight_calculation_keeps_relative_time_without_a_timestamp(self):
        row = self.row(
            "calculation_epoch",
            {"hour": "1/3"},
            role="calculation_epoch",
            subject="calculation epoch",
            time_reference="source_after_midnight_label",
        )
        out = public_assertion(row)
        self.assertEqual(out["time_reference"], "source_after_midnight_label")
        self.assertEqual(out["normalized"]["magnitude"], "1200")
        self.assertNotIn("absolute_timestamp", out)
        for change in (
            {"quantity": "recorded_clock"},
            {"quantity": "transit_clock"},
            {"role": "recorded_reading"},
            {"role": "reduction"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_capricorn_reference_coordinate_keeps_its_own_subject(self):
        row = self.row(
            "declination",
            {"degree": "15", "arcminute": "57 1/2"},
            subject="lower horn of Capricorn",
            role="historical_input",
            direction="south",
        )
        out = public_assertion(row)
        self.assertEqual(out["subject"], "lower horn of Capricorn")
        self.assertEqual(out["normalized"]["signed_magnitude"], "-57450")

    def test_water_star_equatorial_indication_keeps_angular_units_and_no_clock(self):
        row = self.row(
            "meridian_distance",
            {"degree": "4", "arcminute": "31"},
            subject="first star in outpouring of water",
            reference="meridian",
            role="calibration",
            flags=[
                "direction_unstated",
                "observing_clock_unstated",
                "reference_star_modern_id_unresolved",
            ],
        )
        out = public_assertion(row)
        self.assertEqual(out["subject"], "first star in outpouring of water")
        self.assertEqual(out["normalized"]["unit"], "arcsecond")
        self.assertEqual(out["normalized"]["magnitude"], "16260")
        self.assertIsNone(out["event_id"])
        self.assertIsNone(out["direction"])

    def test_parallax_addition_retains_ra_context_without_claiming_a_detection(self):
        row = self.row(
            "parallax_angle",
            {"arcsecond": "15"},
            subject="Mars",
            reference="Earth",
            role="historical_correction",
            source_parallax_context="right_ascension_collection",
            source_parallax_operation="add",
            flags=["historical_parallax_not_detection"],
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_parallax_context"), "right_ascension_collection")
        self.assertEqual(out.get("source_parallax_operation"), "add")
        self.assertEqual(out["normalized"]["magnitude"], "15")
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        for change in (
            {"quantity": "clock_correction"},
            {"role": "recorded_reading"},
            {"source_parallax_context": "ecliptic_longitude"},
            {"source_parallax_operation": "subtract"},
            {"source_parallax_operation": None},
            {"reference": None},
            {"flags": []},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
        for missing in ("source_parallax_context", "source_parallax_operation"):
            bad = copy.deepcopy(row)
            del bad[missing]
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_ecliptic_parallax_instructions_keep_the_coordinate_and_printed_operation(self):
        for quantity, components, operation, magnitude in (
            ("longitude_correction", {"arcminute": "1"}, "add", "60"),
            ("latitude_correction", {"arcminute": "1", "arcsecond": "45"}, "subtract", "105"),
        ):
            row = self.row(
                quantity,
                components,
                subject="Mars",
                reference="Earth",
                role="historical_correction",
                source_parallax_context="ecliptic_coordinate_reduction",
                source_parallax_operation=operation,
                flags=["historical_parallax_not_detection"],
            )
            try:
                out = public_assertion(row)
            except ValueError as error:
                self.fail("Reviewed ecliptic parallax instruction must export: " + str(error))
            self.assertEqual(out["quantity"], quantity)
            self.assertEqual(out["normalized"]["magnitude"], magnitude)
            self.assertEqual(out["source_parallax_operation"], operation)
            self.assertEqual(out["source_parallax_context"], "ecliptic_coordinate_reduction")
            self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_ecliptic_parallax_instruction_cannot_become_a_measurement_or_signed_position(self):
        row = self.row(
            "latitude_correction",
            {"arcminute": "1", "arcsecond": "45"},
            subject="Mars",
            reference="Earth",
            role="historical_correction",
            source_parallax_context="ecliptic_coordinate_reduction",
            source_parallax_operation="subtract",
            flags=["historical_parallax_not_detection"],
        )
        for change in (
            {"role": "recorded_coordinate"},
            {"quantity": "ecliptic_latitude"},
            {"quantity": "parallax_angle"},
            {"reference": None},
            {"subject": "Jupiter"},
            {"direction": "south"},
            {"source_parallax_operation": "multiply"},
            {"flags": []},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_longitude_of_greatest_latitude_is_a_parameter_not_a_planet_position(self):
        row = self.row(
            "ecliptic_longitude",
            {"degree": "18"},
            subject="Mars",
            role="historical_input",
            zodiac_sign="Aquarius",
            source_parameter_kind="longitude_of_greatest_latitude",
            flags=["not_an_additional_raw_reading"],
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_parameter_kind"), "longitude_of_greatest_latitude")
        self.assertEqual(out["normalized"]["zodiac_longitude_degrees"], "318")
        for change in (
            {"role": "recorded_coordinate"},
            {"role": "historical_prediction"},
            {"quantity": "ecliptic_latitude"},
            {"source_parameter_kind": "planet_position"},
            {"subject": "Sun"},
            {"flags": []},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_coordinate_reduction_from_mars_is_not_a_new_raw_separation(self):
        row = self.row(
            "ecliptic_longitude",
            {"degree": "17", "arcminute": "23", "arcsecond": "35"},
            source_reduction_method="comparison_directions",
            source_reduction_references=["Mars"],
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_reduction_references"), ["Mars"])
        self.assertEqual(out.get("source_reduction_method"), "comparison_directions")
        self.assertEqual(out["quantity"], "ecliptic_longitude")
        self.assertIsNone(out["reference"])
        for change in (
            {"role": "recorded_reading"},
            {"source_reduction_references": ["private name"]},
            {"source_reduction_method": "private process"},
            {"source_reduction_references": ["Mars", "Mars"]},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_latitude_weight_is_a_dimensionless_ratio_without_a_fictitious_body(self):
        row = self.row(
            "correction_ratio",
            {"ratio": "1/3"},
            role="historical_correction",
            correction_ratio_kind="latitude_difference_weight",
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "1/3")
        self.assertEqual(out["normalized"]["unit"], "ratio")
        self.assertIsNone(out["reference"])
        self.assertEqual(out["correction_ratio_kind"], "latitude_difference_weight")
        for change in ({"reference": "Sun"}, {"role": "recorded_reading"}):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
