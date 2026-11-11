import copy, hashlib, unittest
from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion, validate_links


class SummaryRevisionTests(unittest.TestCase):
    def row(self, q, parts, **extra):
        row = dict(
            id="assertion-v12-" + "2" * 20,
            volume=12,
            printed_page=309,
            quantity=q,
            components=parts,
            subject="Mars",
            reference=None,
            direction=None,
            role="historical_input",
            flags=["not_an_additional_raw_reading"],
        )
        row.update(extra)
        row["normalized"] = normalize_quantity(row)
        return row

    def test_reported_original_minute_component_is_not_a_complete_angle(self):
        text = "1° 43′¹\n40\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        base = dict(
            span_id="s",
            subject="Mars",
            reference=None,
            unit_basis="Marked minute-component variant",
        )
        parent = dict(
            base,
            key="parent",
            line=1,
            quantity="ecliptic_latitude",
            role="historical_input",
            direction="north",
            source_expression="1° 43′¹",
            source_note_marker_original="¹",
            components={"degree": "1", "arcminute": "43"},
            flags=["not_an_additional_raw_reading"],
        )
        note = dict(
            base,
            key="original-minute",
            line=2,
            quantity="angle_component",
            role="editorial_variant",
            direction=None,
            source_expression="40",
            components={"arcminute": "40"},
            annotation_of_key="parent",
            flags=[
                "source_annotation_variant",
                "not_a_complete_angle",
                "not_an_additional_raw_reading",
            ],
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=2)
        batch = dict(
            id="minute-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=309),
            span_decisions=[
                dict(span_id="s", decision="include", reason="Source component revision")
            ],
            assertions=[parent, note],
            events=[],
        )
        try:
            rows = [
                public_assertion(a)
                for a in compile_catalogue([batch], {12: text}, [span])["assertions"]
            ]
            validate_links(rows, [])
        except ValueError as error:
            self.fail("Reported minute component must compile and export: " + str(error))
        out = next(a for a in rows if a["quantity"] == "angle_component")
        self.assertEqual(out["normalized"]["magnitude"], "40")
        self.assertEqual(out["normalized"]["unit"], "source_angle_component")
        self.assertEqual(out["normalized"]["least_component_unit"], "arcminute")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])

    def test_computed_minus_observed_sign_and_missing_magnitude_are_preserved(self):
        parent = self.row(
            "latitude_difference",
            None,
            role="calculation_intermediate",
            incomplete=True,
            source_comparison_sign="plus",
            comparison_relation="computed_minus_observed",
        )
        try:
            out = public_assertion(parent)
        except ValueError as error:
            self.fail("Sign without magnitude must remain incomplete: " + str(error))
        self.assertEqual(out["normalized"]["status"], "incomplete")
        self.assertIsNone(out["normalized"]["magnitude"])
        self.assertEqual(out["comparison_relation"], "computed_minus_observed")
        variant = self.row(
            "latitude_difference",
            {"arcminute": "3"},
            id="assertion-v12-" + "3" * 20,
            role="editorial_variant",
            source_comparison_sign="plus",
            comparison_relation="computed_minus_observed",
            annotation_of_id=parent["id"],
        )
        try:
            original = public_assertion(variant)
            validate_links([out, original], [])
        except ValueError as error:
            self.fail("Reported earlier residual must retain sign and link: " + str(error))
        self.assertEqual(original["normalized"]["magnitude"], "180")
        bad = copy.deepcopy(variant)
        bad["annotation_of_id"] = None
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_radius_only_and_possible_parallax_shortfall_are_scoped_to_summary(self):
        row = self.row(
            "ecliptic_latitude",
            {"degree": "1", "arcminute": "40"},
            direction="north",
            source_instrument_label="Radius",
            source_instrument_qualifier="only",
            source_coordinate_state="parallax_possibly_insufficient_as_stated",
            flags=[
                "not_an_additional_raw_reading",
                "not_certain_enough",
                "source_quality_note_present",
                "historical_parallax_not_detection",
            ],
        )
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Source instrument and parallax qualification must export: " + str(error))
        self.assertEqual(out["source_instrument_label"], "Radius")
        self.assertEqual(out["source_instrument_qualifier"], "only")
        self.assertNotIn("correction_value", out)
        bad = copy.deepcopy(row)
        bad["role"] = "recorded_coordinate"
        with self.assertRaises(ValueError):
            public_assertion(bad)
        scalar = self.row(
            "source_scalar",
            {"scalar": "3"},
            subject="Mars calculation",
            source_parameter_kind="unlabelled_table_value",
        )
        self.assertEqual(public_assertion(scalar)["normalized"]["unit"], "source_scalar")
