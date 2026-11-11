import copy
import hashlib
import unittest
from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion


class AngularCountAndUnresolvedUnitsTests(unittest.TestCase):
    def test_model_parallax_and_diameter_keep_unresolved_component_units(self):
        for quantity, reference in (("parallax_angle", "Earth"), ("angular_diameter", None)):
            row = self.row(
                {"component_1": "56", "component_2": "44"},
                quantity=quantity,
                subject="Moon",
                reference=reference,
                source_angular_units_unresolved=True,
            )
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["source_components"], ["56", "44"])
            self.assertIsNone(out["normalized"]["magnitude"])
            for changes in ({"subject": "Sun"}, {"role": "recorded_reading"}):
                with (
                    self.subTest(quantity=quantity, changes=changes),
                    self.assertRaises(ValueError),
                ):
                    public_assertion(dict(row, **changes))

    def row(self, parts, **extra):
        row = dict(
            id="assertion-v12-" + "e" * 20,
            volume=12,
            printed_page=306,
            quantity="calculation_angle",
            components=parts,
            role="historical_input",
            subject="Mars",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        row.update(extra)
        row["normalized"] = normalize_quantity(row)
        return row

    def test_sign_count_is_thirty_degrees_without_a_named_zodiac_sign(self):
        try:
            row = self.row(
                dict(sign_count="6", degree="0"),
                argument_name="commutation_anomaly",
                source_angular_count_unit="sign_count",
            )
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Explicit sign count must export: " + str(error))
        self.assertEqual(out["normalized"]["magnitude_degrees"], "180")
        self.assertEqual(out["source_angular_count_unit"], "sign_count")
        self.assertNotIn("zodiac_sign", out["normalized"])
        self.assertEqual(
            normalize_quantity(
                dict(quantity="calculation_angle", components={"sexagena": "6", "degree": "0"})
            )["magnitude_degrees"],
            "360",
        )
        for degree in ("31", "60", "72"):
            norm = normalize_quantity(
                dict(quantity="calculation_angle", components=dict(sign_count="6", degree=degree))
            )
            self.assertEqual(norm["normalization_issue"], "degree_outside_sign")
            self.assertIsNone(norm["magnitude"])
        for parts in (dict(sign_count="6", sexagena="0"), dict(sexagena="6", degree="60")):
            with self.subTest(parts=parts), self.assertRaises(ValueError):
                normalize_quantity(dict(quantity="calculation_angle", components=parts))
        bad = copy.deepcopy(row)
        bad["quantity"] = "ecliptic_longitude"
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_unresolved_components_compile_without_a_guessed_angle(self):
        text = "6 18 0\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        source = dict(
            key="argument",
            line=1,
            span_id="s",
            quantity="calculation_angle",
            role="historical_input",
            subject="Mars",
            reference=None,
            direction=None,
            components=dict(component_1="6", component_2="18", component_3="0"),
            source_expression="6 18 0",
            unit_basis="Reviewed angular context; leading unit unestablished",
            source_angular_units_unresolved=True,
            flags=["not_an_additional_raw_reading"],
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        batch = dict(
            id="units-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=306),
            span_decisions=[
                dict(span_id="s", decision="include", reason="Angular source with unresolved scale")
            ],
            assertions=[source],
            events=[],
        )
        try:
            compiled = compile_catalogue([batch], {12: text}, [span])["assertions"][0]
            out = public_assertion(compiled)
        except ValueError as error:
            self.fail("Unresolved source components must remain available: " + str(error))
        self.assertEqual(out["normalized"]["status"], "unsupported")
        self.assertEqual(out["normalized"]["source_components"], ["6", "18", "0"])
        self.assertEqual(
            out["normalized"]["normalization_issue"], "angular_component_units_unresolved"
        )
        self.assertIsNone(out["normalized"]["magnitude"])
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        for change in ({"role": "recorded_coordinate"}, {"direction": "north"}):
            bad = copy.deepcopy(compiled)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
        bad = copy.deepcopy(compiled)
        bad["normalized"]["magnitude"] = "712800"
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_apogee_trial_shift_is_a_model_parameter_adjustment(self):
        row = self.row({"degree": "1"}, role="historical_correction", argument_name="apogee_shift")
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Apogee trial adjustment must export: " + str(error))
        self.assertEqual(out["normalized"]["magnitude"], "3600")
        bad = copy.deepcopy(row)
        bad["role"] = "recorded_coordinate"
        with self.assertRaises(ValueError):
            public_assertion(bad)
