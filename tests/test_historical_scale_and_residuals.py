import copy
import hashlib
import unittest
from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion


class HistoricalScaleTests(unittest.TestCase):
    def row(self, q, parts, **kwargs):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=305,
            quantity=q,
            components=parts,
            role="historical_input",
            subject="Mars",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        row.update(kwargs)
        row["normalized"] = normalize_quantity(row)
        return row

    def test_relative_source_scale_preserves_both_parts_without_a_physical_distance(self):
        text = "9½ of 60\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        source = self.row(
            "source_scale_ratio",
            dict(source_part="9 1/2", reference_scale="60"),
            subject="eccentric centre of Mars",
            reference="Earth",
        )
        source.update(
            key="offset",
            line=1,
            span_id="s",
            source_expression="9½ of 60",
            unit_basis="Explicit source relative scale, not terrestrial radii",
        )
        for key in ("normalized", "id", "volume", "printed_page"):
            source.pop(key)
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        batch = dict(
            id="relative-scale",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=305),
            span_decisions=[
                dict(span_id="s", decision="context", reason="Reviewed relative scale")
            ],
            assertions=[source],
            events=[],
        )
        try:
            compiled = compile_catalogue([batch], {12: text}, [span])
            out = public_assertion(compiled["assertions"][0])
        except ValueError as error:
            self.fail("Reviewed relative scale must compile and export: " + str(error))
        self.assertEqual(out["normalized"]["magnitude"], "19/120")
        self.assertEqual(out["normalized"]["unit"], "ratio")
        self.assertEqual(out["normalized"]["source_scale_part"], "19/2")
        self.assertEqual(out["normalized"]["source_reference_scale"], "60")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        for parts in (
            dict(source_part="9", reference_scale="0"),
            dict(semidiameter="9"),
            dict(source_part="-9", reference_scale="60"),
        ):
            with self.subTest(parts=parts), self.assertRaises(ValueError):
                normalize_quantity(dict(quantity="source_scale_ratio", components=parts))
        bad = copy.deepcopy(compiled["assertions"][0])
        bad["normalized"]["source_reference_scale"] = "120"
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_node_correction_and_maximum_latitude_are_parameters_not_recorded_positions(self):
        correction = self.row(
            "calculation_angle",
            dict(degree="1", arcminute="45"),
            role="historical_correction",
            argument_name="node_distance_correction",
        )
        maximum = self.row(
            "ecliptic_latitude",
            dict(degree="4", arcminute="34"),
            direction="north",
            source_parameter_kind="greatest_northern_latitude",
        )
        try:
            c, m = public_assertion(correction), public_assertion(maximum)
        except ValueError as error:
            self.fail("Reviewed historical parameters must export: " + str(error))
        self.assertEqual(c["argument_name"], "node_distance_correction")
        self.assertEqual(c["normalized"]["magnitude"], "6300")
        self.assertEqual(m["source_parameter_kind"], "greatest_northern_latitude")
        self.assertEqual(m["normalized"]["magnitude"], "16440")
        for row, change in (
            (correction, {"role": "recorded_reading"}),
            (correction, {"quantity": "ecliptic_longitude"}),
            (maximum, {"role": "recorded_coordinate"}),
            (maximum, {"direction": "south"}),
            (maximum, {"reference": "Earth"}),
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_source_residual_sign_does_not_become_a_latitude_hemisphere(self):
        for minutes, sign, want in (("2", "minus", "120"), ("0", "equal", "0")):
            row = self.row(
                "latitude_difference",
                dict(arcminute=minutes),
                role="calculation_intermediate",
                source_comparison_sign=sign,
                comparison_relation="observed_minus_computed",
            )
            try:
                out = public_assertion(row)
            except ValueError as error:
                self.fail("Reviewed source residual must export: " + str(error))
            self.assertEqual(out["source_comparison_sign"], sign)
            self.assertEqual(out["comparison_relation"], "observed_minus_computed")
            self.assertEqual(out["normalized"]["magnitude"], want)
            self.assertIsNone(out["normalized"]["signed_magnitude"])
        row = self.row(
            "latitude_difference",
            dict(arcminute="2"),
            role="calculation_intermediate",
            source_comparison_sign="minus",
            comparison_relation="observed_minus_computed",
        )
        for change in (
            {"source_comparison_sign": "equal"},
            {"direction": "south"},
            {"role": "recorded_reading"},
            {"comparison_relation": "private label"},
            {"model_name": "Copernicus"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
