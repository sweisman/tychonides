import copy
import unittest

from src.catalog import normalize_quantity, compile_catalogue
import hashlib
from src.public_checkpoint import public_assertion
from src.date_claims import public_date_claim


class OccultationUnitTests(unittest.TestCase):
    def test_wrong_physical_table_column_is_rejected_before_import(self):
        text = "| First result 118125 | |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        a = dict(
            key="result",
            line=1,
            span_id="s",
            source_expression="118125",
            column=2,
            quantity="source_scalar",
            role="calculation_intermediate",
            subject="Moon calculation",
            reference=None,
            direction=None,
            components={"scalar": "118125"},
            source_parameter_kind="arithmetic_intermediate",
            flags=["not_an_additional_raw_reading"],
            unit_basis="Native source integer",
        )
        b = dict(
            id="review",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip().encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=24),
            assertions=[a],
            span_decisions=[dict(span_id="s", decision="include", reason="Printed result")],
        )
        span = dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=1)
        with self.assertRaises(ValueError):
            compile_catalogue([b], {10: text}, [span])

    def row(self, quantity, components, **extra):
        row = dict(
            id="assertion-v10-" + "a" * 20,
            volume=10,
            printed_page=24,
            quantity=quantity,
            components=components,
            role="historical_input",
            subject="Moon calculation",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        row.update(extra)
        row["normalized"] = normalize_quantity(row)
        return row

    def test_native_sine_and_intermediate_are_not_angles_or_automatically_rescaled(self):
        sine = self.row(
            "source_scalar",
            {"scalar": "97127"},
            source_parameter_kind="scaled_sine",
            source_scalar_scale="100000",
        )
        try:
            out = public_assertion(sine)
        except ValueError as error:
            self.fail(f"Native scaled sine needs its stated scale: {error}")
        self.assertEqual(out["normalized"]["magnitude"], "97127")
        self.assertEqual(out["normalized"]["unit"], "source_scalar")
        self.assertEqual(out["source_scalar_scale"], "100000")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        product = self.row(
            "source_scalar",
            {"scalar": "8242900000"},
            role="calculation_intermediate",
            source_parameter_kind="arithmetic_intermediate",
        )
        self.assertEqual(public_assertion(product)["normalized"]["magnitude"], "8242900000")
        for change in (
            {"source_scalar_scale": "0"},
            {"source_scalar_scale": "90000"},
            {"role": "recorded_reading"},
            {"direction": "north"},
        ):
            bad = copy.deepcopy(sine)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_model_lengths_keep_native_parts_and_allow_lengths_above_reference(self):
        row = self.row(
            "source_scalar",
            {"scalar": "10997"},
            subject="Mars calculation",
            role="calculation_intermediate",
            source_parameter_kind="model_length",
            source_scalar_scale="10000",
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "10997")
        self.assertEqual(out["normalized"]["unit"], "source_scalar")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        self.assertEqual(out["source_parameter_kind"], "model_length")
        self.assertEqual(out["source_scalar_scale"], "10000")
        self.assertEqual(
            public_assertion(dict(row, subject="Moon calculation"))["normalized"]["magnitude"],
            "10997",
        )
        for changes in (
            {"source_scalar_scale": "0"},
            {"source_scalar_scale": None},
            {"source_scalar_scale": "10000/1"},
            {"subject": "comet calculation"},
            {"role": "recorded_reading"},
            {"direction": "north"},
            {"reference": "Earth"},
            {"flags": []},
        ):
            bad = copy.deepcopy(row)
            bad.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                public_assertion(bad)
        for value in ("0", "-1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                bad = self.row(
                    "source_scalar",
                    {"scalar": value},
                    subject="Mars calculation",
                    source_parameter_kind="model_length",
                    source_scalar_scale="10000",
                )
                public_assertion(bad)

    def test_lunar_reference_fractions_keep_their_distinct_bases(self):
        for kind, value, relation in (
            ("lunar_illuminated_portion", "1/3", "separation_as_stated"),
            ("lunar_semidiameter", "2/3", "latitude_offset_as_stated"),
            ("lunar_reference_unstated", "1/3", "latitude_offset_as_stated"),
            ("lunar_illuminated_portion", "1", "greater_than_reference_fraction"),
        ):
            row = self.row(
                "source_fraction",
                {"fraction": value},
                role="recorded_reading",
                subject="Moon centre",
                reference="Aldebaran",
                source_fraction_kind=kind,
                comparison_relation=relation,
                flags=["source_visual_estimate", "geometry_interpretation_unestablished"],
            )
            if relation == "greater_than_reference_fraction":
                row["flags"].append("source_lower_bound")
            try:
                out = public_assertion(row)
            except ValueError as error:
                self.fail(f"Native lunar fraction must retain its reference: {error}")
            self.assertEqual(out["normalized"]["magnitude"], value)
            self.assertEqual(out["normalized"]["unit"], "source_fraction")
            self.assertEqual(out["source_fraction_kind"], kind)
            self.assertIsNone(out["normalized"]["magnitude_degrees"])
            bad = copy.deepcopy(row)
            bad["subject"] = "Mars"
            with self.assertRaises(ValueError):
                public_assertion(bad)

    def test_hourly_motion_has_an_hour_rate_unit(self):
        row = self.row(
            "angular_hourly_motion", {"arcminute": "30"}, role="reduction", subject="Moon"
        )
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail(f"An hourly motion must remain a rate: {error}")
        self.assertEqual(out["normalized"]["magnitude"], "1800")
        self.assertEqual(out["normalized"]["unit"], "arcsecond_per_source_hour")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        bad = copy.deepcopy(row)
        bad["quantity"] = "angular_daily_motion"
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_parallax_free_lunar_distance_keeps_its_reduced_state(self):
        row = self.row(
            "angular_separation",
            {"degree": "12", "arcminute": "5"},
            role="reduction",
            subject="Moon",
            reference="Aldebaran",
            source_coordinate_state="free_of_parallax",
            flags=["not_an_additional_raw_reading", "limb_or_instrument_setting_unresolved"],
        )
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail(f"Source-corrected distance must keep its state: {error}")
        self.assertEqual(out["source_coordinate_state"], "free_of_parallax")
        self.assertEqual(out["normalized"]["magnitude"], "43500")
        for change in ({"role": "recorded_reading"}, {"subject": "Mars"}, {"reference": None}):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_following_day_retains_the_named_anchor_without_inventing_a_day_number(self):
        context = dict(
            id="context-v10-" + "a" * 20,
            volume=10,
            kind="recorded_date",
            value=dict(year=1570, month=1, day=None, day_rule="following_named_day", anchor_day=16),
            calendar=None,
            day_origin=None,
            source_date_role="observation_label",
        )
        try:
            out = public_date_claim(context)
        except ValueError as error:
            self.fail(f"Relative observing day needs its recorded anchor: {error}")
        self.assertIsNone(out["day"])
        self.assertEqual(out["day_rule"], "following_named_day")
        self.assertEqual(out["anchor_day"], 16)
        self.assertIsNone(out["absolute_timestamp"])
        bad = copy.deepcopy(context)
        bad["value"]["day"] = 17
        with self.assertRaises(ValueError):
            public_date_claim(bad)


if __name__ == "__main__":
    unittest.main()
