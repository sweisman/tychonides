import copy
import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path


class CatalogueTests(unittest.TestCase):
    def test_calculated_planet_orbital_coordinates_require_their_frame_and_origin(self):
        from src.public_assertions import public_assertion

        for body in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
            for role in ("historical_input", "calculation_intermediate"):
                for reference in (None, "Earth", "Sun"):
                    with self.subTest(body=body, role=role, reference=reference):
                        text, spans, batch = self.explicit_clock_case(
                            "8 signs 9° 57′ 16″",
                            {
                                "sign_count": "8",
                                "degree": "9",
                                "arcminute": "57",
                                "arcsecond": "16",
                            },
                        )
                        batch["assertions"][0].update(
                            quantity="orbital_longitude",
                            subject=body,
                            reference=reference,
                            role=role,
                            source_coordinate_frame="own_orbit_as_stated",
                            flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
                        )
                        row = self.module().compile_catalogue([batch], {10: text}, spans)[
                            "assertions"
                        ][0]
                        out = public_assertion(row)
                        self.assertEqual(out["normalized"]["magnitude"], "899836")
                        self.assertEqual(out["source_coordinate_frame"], "own_orbit_as_stated")
                        self.assertEqual(out["reference"], reference)
                        self.assertEqual(row["source_expression"], "8 signs 9° 57′ 16″")

        for changes in (
            {"role": "recorded_reading"},
            {"subject": "observing clock"},
            {"reference": "Aldebaran"},
            {"source_coordinate_frame": "ecliptic"},
            {"flags": ["not_an_additional_raw_reading"]},
            {"event_id": "event-unreviewed"},
            {"model_name": "Alphonsine"},
        ):
            with self.subTest(rejected=changes), self.assertRaises(ValueError):
                public_assertion(dict(row, **changes))

        text, spans, batch = self.explicit_clock_case("9° 57′", {"degree": "9", "arcminute": "57"})
        batch["assertions"][0].update(
            quantity="orbital_longitude",
            subject="Saturn",
            role="historical_input",
            source_coordinate_frame="own_orbit_as_stated",
            flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        with self.assertRaises(ValueError):
            public_assertion(row)

        for subject in ("Mars", "Moon centre"):
            text, spans, batch = self.explicit_clock_case("20° ♐", {"degree": "20"})
            batch["assertions"][0].update(
                quantity="orbital_longitude",
                subject=subject,
                role="reduction",
                source_coordinate_frame="own_orbit_as_stated",
                source_coordinate_state="true",
                zodiac_sign="Sagittarius",
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            self.assertEqual(public_assertion(row)["normalized"]["zodiac_longitude_degrees"], "260")

    def test_calculated_declination_correction_retains_its_operation_and_scope(self):
        from src.public_assertions import public_assertion

        for subject in ("ecliptic point", "planetary motion calculation"):
            with self.subTest(subject=subject):
                text, spans, batch = self.explicit_clock_case(
                    "1° 11′", {"degree": "1", "arcminute": "11"}
                )
                batch["assertions"][0].update(
                    quantity="declination_correction",
                    subject=subject,
                    role="calculation_intermediate",
                    source_correction_operation="add",
                    flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                out = public_assertion(row)
                self.assertEqual(out["normalized"]["magnitude"], "4260")
                self.assertEqual(out["source_correction_operation"], "add")
                self.assertEqual(out["role"], "calculation_intermediate")
                for changes in (
                    {"role": "recorded_reading"},
                    {"role": "historical_correction"},
                    {"subject": "observing clock"},
                    {"event_id": "event-unreviewed"},
                    {"source_correction_operation": "multiply"},
                    {"flags": ["not_an_additional_raw_reading"]},
                ):
                    with self.subTest(rejected=changes), self.assertRaises(ValueError):
                        public_assertion(dict(row, **changes))

    def test_computed_calendar_counts_keep_their_result_role(self):
        from src.public_assertions import public_assertion

        for kind, literal in (("source_day_count", "303191"), ("source_year_count", "1450")):
            with self.subTest(kind=kind):
                text, spans, batch = self.explicit_clock_case(literal, {"scalar": literal})
                batch["assertions"][0].update(
                    quantity="source_scalar",
                    subject="calendar calculation",
                    role="calculation_intermediate",
                    source_parameter_kind=kind,
                    flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                result = public_assertion(row)
                self.assertEqual(result["role"], "calculation_intermediate")
                self.assertEqual(result["normalized"]["magnitude"], literal)
                self.assertEqual(result["normalized"]["unit"], "source_scalar")
                for changes in (
                    {"role": "recorded_reading"},
                    {"reference": "Sun"},
                    {"event_id": "event-unreviewed"},
                    {"source_parameter_kind": "comparison_multiplier"},
                ):
                    with self.subTest(rejected=changes), self.assertRaises(ValueError):
                        public_assertion(dict(row, **changes))

    def test_time_correction_accepts_unbounded_leading_subunit_only(self):
        from src.public_assertions import public_assertion

        for literal, unit, expected in (
            ("223″", "second", "223"),
            ("146″", "second", "146"),
            ("75′", "minute", "4500"),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, {unit: literal[:-1]})
                batch["assertions"][0].update(
                    quantity="clock_correction",
                    subject="observing clock",
                    role="calculation_intermediate",
                    flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                norm = public_assertion(row)["normalized"]
                self.assertEqual(norm["magnitude"], expected)
                self.assertEqual(norm["unit"], "second_of_time")

        for parts in ({"hour": "1", "minute": "60"}, {"minute": "1", "second": "60"}):
            with self.subTest(invalid_subordinate=parts), self.assertRaises(ValueError):
                self.module().normalize_quantity(
                    dict(quantity="clock_correction", components=parts)
                )

        text, spans, batch = self.explicit_clock_case("223″", {"minute": "223"})
        batch["assertions"][0].update(quantity="clock_correction")
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([batch], {10: text}, spans)

    def test_stellar_calibration_preserves_relative_coefficients_and_arithmetic(self):
        from src.public_assertions import public_assertion

        for kind, literal, component, role, expected in (
            ("comparison_multiplier", "5⅘", "5 4/5", "historical_input", "29/5"),
            ("arithmetic_intermediate", "32", "32", "calculation_intermediate", "32"),
        ):
            with self.subTest(kind=kind):
                text, spans, batch = self.explicit_clock_case(literal, {"scalar": component})
                batch["assertions"][0].update(
                    quantity="source_scalar",
                    subject="stellar calibration calculation",
                    role=role,
                    source_parameter_kind=kind,
                    flags=["not_an_additional_raw_reading"],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                result = public_assertion(row)
                self.assertEqual(result["normalized"]["magnitude"], expected)
                self.assertEqual(result["normalized"]["unit"], "source_scalar")
                self.assertIsNone(result["normalized"]["magnitude_degrees"])
                physical = copy.deepcopy(row)
                physical.update(
                    role="historical_input",
                    source_parameter_kind="model_length",
                    source_scalar_scale="100000",
                )
                with self.assertRaises(ValueError):
                    public_assertion(physical)

    def test_capitalized_article_preserves_its_explicit_time_unit(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("A minute of time", {"minute": "1"})
        batch["assertions"][0].update(
            quantity="clock_elapsed_time",
            role="recorded_reading",
            source_word_numbers={"A": "1"},
            flags=["not_an_observing_clock"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        result = public_assertion(row)
        self.assertEqual(result["normalized"]["magnitude"], "60")
        self.assertEqual(result["normalized"]["unit"], "second_of_time")
        self.assertEqual(row["source_expression"], "A minute of time")
        batch["assertions"][0]["components"] = {"hour": "1"}
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([batch], {10: text}, spans)

    def test_angular_offset_does_not_claim_an_absolute_coordinate_axis(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("10 minutes west", {"arcminute": "10"})
        batch["assertions"][0].update(
            quantity="angular_offset",
            subject="Venus",
            reference="Regulus",
            direction="west",
            role="recorded_reading",
            unit_basis="Source visual offset; coordinate axis not stated.",
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        result = public_assertion(row)
        self.assertEqual(result["normalized"]["status"], "exact")
        self.assertEqual(result["normalized"]["magnitude"], "600")
        self.assertEqual(result["normalized"]["unit"], "arcsecond")
        self.assertIsNone(result["normalized"]["signed_magnitude"])
        self.assertNotIn("longitude_origin", result["normalized"])
        self.assertNotIn("zodiac_longitude_degrees", result["normalized"])
        missing = copy.deepcopy(row)
        missing["reference"] = None
        with self.assertRaisesRegex(ValueError, "both endpoints"):
            public_assertion(missing)
        batch["assertions"][0]["components"] = {"degree": "10"}
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([batch], {10: text}, spans)

    def test_literal_semidiameter_keeps_a_native_visual_coefficient(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("a semidiameter", {"scalar": "1"})
        batch["assertions"][0].update(
            quantity="source_scalar",
            subject="Venus",
            role="recorded_reading",
            source_parameter_kind="visual_coefficient_as_stated",
            source_word_numbers={"a semidiameter": "1"},
            flags=["source_visual_estimate", "geometry_interpretation_unestablished"],
            unit_basis="Native visual coefficient; no angular diameter inferred.",
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        result = public_assertion(row)
        self.assertEqual(row["source_expression"], "a semidiameter")
        self.assertEqual(result["normalized"]["magnitude"], "1")
        self.assertEqual(result["normalized"]["unit"], "source_scalar")
        self.assertIsNone(row["normalized"]["magnitude_degrees"])

    def test_numeric_ordinal_does_not_hide_its_explicit_unit(self):
        for literal, correct, incorrect, quantity in (
            ("13th hour", {"hour": "13"}, {"minute": "13"}, "recorded_clock"),
            ("41st minute", {"minute": "41"}, {"second": "41"}, "clock_elapsed_time"),
            ("2nd degree", {"degree": "2"}, {"arcminute": "2"}, "calculation_angle"),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, correct)
                batch["assertions"][0]["quantity"] = quantity
                self.module().compile_catalogue([batch], {10: text}, spans)
                batch["assertions"][0]["components"] = incorrect
                with self.assertRaisesRegex(ValueError, "explicit source unit"):
                    self.module().compile_catalogue([batch], {10: text}, spans)

    def test_forty_first_minute_is_an_elapsed_time_not_an_hour(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("forty-first minute", {"minute": "41"})
        row = batch["assertions"][0]
        row.update(
            quantity="clock_elapsed_time",
            source_word_numbers={"forty-first": "41"},
            flags=["not_an_observing_clock"],
        )
        compiled = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(public_assertion(compiled)["normalized"]["magnitude"], "2460")
        row["components"] = {"hour": "41"}
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([batch], {10: text}, spans)

    def test_superscript_roman_places_bind_before_unicode_compatibility_conversion(self):
        cases = (
            ("1ᵛ", "arcsexagesimal_fifth", "arcsecond", "1/216000"),
            ("1ᵛⁱ", "arcsexagesimal_sixth", "arcsexagesimal_seventh", "1/12960000"),
            ("1ᵛⁱⁱ", "arcsexagesimal_seventh", "arcsexagesimal_sixth", "1/777600000"),
            ("1ᵛⁱⁱⁱ", "arcsexagesimal_eighth", "arcsecond", "1/46656000000"),
        )
        for literal, unit, wrong_unit, expected in cases:
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, {unit: "1"})
                row = batch["assertions"][0]
                row.update(
                    quantity="angular_yearly_motion",
                    role="historical_input",
                    subject="fixed stars",
                    reference=None,
                    unit_basis="Explicit superscript Roman angular place.",
                    flags=["not_an_additional_raw_reading"],
                )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                self.assertEqual(compiled["source_expression"], literal)
                self.assertEqual(compiled["normalized"]["magnitude"], expected)
                self.assertEqual(compiled["normalized"]["unit"], "arcsecond_per_source_year")
                bad = copy.deepcopy(batch)
                bad["assertions"][0]["components"] = {wrong_unit: "1"}
                with self.assertRaisesRegex(ValueError, "explicit source unit"):
                    self.module().compile_catalogue([bad], {10: text}, spans)

    def test_multi_component_superscript_sixth_cannot_be_reviewed_as_seventh(self):
        text, spans, batch = self.explicit_clock_case(
            "54″ 32‴ 43⁗ 38ᵛ 20ᵛⁱ",
            dict(
                arcsecond="54",
                arcsexagesimal_third="32",
                arcsexagesimal_fourth="43",
                arcsexagesimal_fifth="38",
                arcsexagesimal_seventh="20",
            ),
        )
        batch["assertions"][0].update(
            quantity="angular_yearly_motion",
            role="historical_input",
            subject="fixed stars",
            reference=None,
            unit_basis="Explicit ordered angular second through sixth places.",
            flags=["not_an_additional_raw_reading"],
        )
        with self.assertRaisesRegex(ValueError, "explicit source unit"):
            self.module().compile_catalogue([batch], {10: text}, spans)

    def test_whole_hour_modifier_cannot_hide_an_explicit_time_unit(self):
        text, spans, batch = self.explicit_clock_case(
            "365 days and six whole hours", dict(day="365", hour="6")
        )
        row = batch["assertions"][0]
        row.update(
            quantity="clock_elapsed_time",
            role="historical_input",
            subject="Sun",
            reference=None,
            unit_basis="Printed day and whole-hour duration, not an observing epoch.",
            source_word_numbers={"six": "6"},
            flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
        )
        compiled = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(compiled["normalized"]["magnitude"], "31557600")
        self.assertEqual(compiled["source_expression"], "365 days and six whole hours")
        row["components"] = dict(day="365", minute="6")
        with self.assertRaisesRegex(ValueError, "explicit source unit"):
            self.module().compile_catalogue([batch], {10: text}, spans)

    def coordinate_product_case(self, quantity="ecliptic_latitude", role="historical_prediction"):
        authorities = ["Ptolemy", "al-Battānī", "Alfonso", "Copernicus"]
        label = ", ".join(authorities)
        literal = "1° 30′"
        text, spans, batch = self.explicit_clock_case(
            label + ": " + literal, {"degree": "1", "arcminute": "30"}
        )
        row = batch["assertions"][0]
        row.update(
            source_expression=literal,
            char_start=text.index(literal),
            char_end=text.index(literal) + len(literal),
            quantity=quantity,
            role=role,
            subject="Spica",
            reference=None,
            direction="south" if quantity in ("declination", "ecliptic_latitude") else None,
            flags=["not_an_additional_raw_reading"],
            context_keys=["coordinate-attribution"],
            unit_basis="Explicit angular coordinate in a source-attributed historical table.",
            source_coordinate_product={"basis_key": "coordinate-attribution"},
        )
        batch["contexts"] = [
            dict(
                key="coordinate-attribution",
                kind="source_observation_context",
                lines=[1],
                value=dict(
                    record_type="source_coordinate_product_attribution",
                    authorities=authorities,
                    source_label=label,
                    scientific_role=role,
                ),
            )
        ]
        return text, spans, batch

    def test_coordinate_products_preserve_joint_authority_without_multiplying_values(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.coordinate_product_case()
        compiled = self.module().compile_catalogue([batch], {10: text}, spans)
        self.assertEqual(len(compiled["assertions"]), 1)
        row = compiled["assertions"][0]
        out = public_assertion(row)
        product = out.get("source_coordinate_product", {})
        self.assertEqual(out["role"], "historical_prediction")
        self.assertEqual(out["normalized"]["magnitude"], "5400")
        self.assertEqual(out["normalized"]["signed_magnitude"], "-5400")
        self.assertEqual(
            product.get("authorities"), ["Ptolemy", "al-Battānī", "Alfonso", "Copernicus"]
        )
        self.assertEqual(product.get("basis_context_id"), compiled["contexts"][0]["id"])
        self.assertIn(product["basis_context_id"], row["context_ids"])

    def test_coordinate_products_cover_solar_predictions_and_stellar_comparisons(self):
        from src.public_assertions import public_assertion

        for quantity, role, subject, signed in (
            ("declination", "historical_prediction", "Sun", "-5400"),
            ("right_ascension", "historical_prediction", "Sun", None),
            ("right_ascension", "historical_prediction", "Spica", None),
            ("right_ascension_difference", "historical_comparison", "Spica", None),
            ("longitude_difference", "historical_comparison", "Sun", None),
            ("stated_angular_precision", "historical_comparison", "fixed stars", None),
        ):
            with self.subTest(quantity=quantity, role=role):
                text, spans, batch = self.coordinate_product_case(quantity, role)
                batch["assertions"][0]["subject"] = subject
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                out = public_assertion(row)
                self.assertEqual(out["quantity"], quantity)
                self.assertEqual(out["role"], role)
                self.assertEqual(out["normalized"]["magnitude"], "5400")
                self.assertEqual(out["normalized"]["signed_magnitude"], signed)

    def test_coordinate_product_attribution_requires_its_literal_review_context(self):
        changes = (
            lambda b: b["assertions"][0].update(context_keys=[]),
            lambda b: b["assertions"][0].update(source_coordinate_product={"basis_key": "missing"}),
            lambda b: b["contexts"][0]["value"].update(authorities=["Invented authority"]),
            lambda b: b["contexts"][0]["value"].update(authorities=[]),
            lambda b: b["contexts"][0]["value"].update(source_label="Absent label"),
            lambda b: b["contexts"][0]["value"].update(scientific_role="recorded_reading"),
            lambda b: b["contexts"][0].update(kind="instrument"),
        )
        for change in changes:
            with self.subTest(change=change):
                text, spans, batch = self.coordinate_product_case()
                change(batch)
                with self.assertRaisesRegex(ValueError, "coordinate product"):
                    self.module().compile_catalogue([batch], {10: text}, spans)

    def test_coordinate_product_marker_cannot_bypass_other_scientific_contracts(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.coordinate_product_case()
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        for change in (
            {"role": "recorded_reading"},
            {"quantity": "altitude"},
            {"event_id": "event-v10-00000000000000000000"},
            {"reference": "Sun"},
            {"flags": []},
            {"context_ids": []},
            {"model_name": "Copernicus"},
            {"source_prediction_kind": "eclipse_ephemeris"},
            {"source_difference_relation": "deficit"},
            {"normalized": dict(row["normalized"], magnitude="999")},
            {
                "source_coordinate_product": dict(
                    row.get("source_coordinate_product", {}), authorities=[]
                )
            },
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(dict(row, **change))

    def test_native_stellar_endpoint_labels_retain_their_rubric_context(self):
        from src.public_assertions import public_assertion

        literal = "ANDROMEDÆ: Head from the southern foot 1° 30′"
        text, spans, batch = self.explicit_clock_case(literal, {"degree": "1", "arcminute": "30"})
        row = batch["assertions"][0]
        row.update(
            quantity="angular_separation",
            role="adopted_value",
            subject="Head",
            reference="the southern foot",
            flags=["not_an_additional_raw_reading"],
            context_keys=["native-pair"],
        )
        batch.setdefault("contexts", []).append(
            dict(
                key="native-pair",
                kind="source_observation_context",
                lines=[row["line"]],
                value=dict(
                    record_type="source_stellar_distance_endpoints",
                    native_constellation_rubric="ANDROMEDÆ",
                    subject_native_label="Head",
                    reference_native_label="the southern foot",
                    modern_star_identification="not_assigned",
                ),
            )
        )
        compiled = self.module().compile_catalogue([batch], {10: text}, spans)
        out = public_assertion(compiled["assertions"][0])
        self.assertEqual(out["subject"], "Head")
        self.assertEqual(out["reference"], "the southern foot")
        self.assertEqual(out["normalized"]["magnitude"], "5400")
        context = next(c for c in compiled["contexts"] if c["key"] == "native-pair")
        self.assertIn(context["id"], compiled["assertions"][0]["context_ids"])
        self.assertEqual(context["value"]["native_constellation_rubric"], "ANDROMEDÆ")
        self.assertEqual(context["value"]["modern_star_identification"], "not_assigned")

    def test_eclipse_ephemeris_predictions_keep_model_phase_and_duration_roles(self):
        from src.public_assertions import public_assertion

        models = (
            {"model_name": "Alphonsine"},
            {"model_name": "Prutenic"},
            {"model_name": "Tycho Brahe"},
            {"model_name": "Lansbergian"},
            {
                "source_model_attribution": "unnamed_as_stated",
                "source_model_label": "old ephemeris",
            },
            {
                "source_model_attribution": "unestablished_from_canon",
                "source_model_label": "ephemerides",
            },
        )
        cases = (
            (
                "calculation_epoch",
                "5^h^ 30^m^",
                {"hour": "5", "minute": "30"},
                "19800",
                {"source_eclipse_phase": "unstated", "time_reference": "source_after_noon"},
            ),
            ("clock_elapsed_time", "2^h^ 1^m^", {"hour": "2", "minute": "1"}, "7260", {}),
            (
                "eclipse_extent",
                "9 0′",
                {"digit": "9", "digit_minute": "0"},
                "9",
                {"source_extent_unit": "digit"},
            ),
            ("eclipse_extent", "Total", {}, None, {"source_extent_unit": "digit"}),
            ("clock_elapsed_time", "2^h^ 8^m^ [?]", {}, None, {}),
        )
        duration = None
        for model in models:
            for quantity, literal, components, magnitude, extra in cases:
                with self.subTest(model=model, quantity=quantity):
                    text, spans, batch = self.explicit_clock_case(literal, components)
                    row = batch["assertions"][0]
                    row.update(
                        quantity=quantity,
                        role="historical_prediction",
                        subject="Sun",
                        reference=None,
                        source_prediction_kind="eclipse_ephemeris",
                        unit_basis="Source eclipse ephemeris: noon clocks, durations and native digits.",
                        flags=[
                            "not_an_additional_raw_reading",
                            "not_an_observing_clock",
                            "absolute_time_unestablished",
                        ],
                        **model,
                        **extra,
                    )
                    if quantity == "clock_elapsed_time" and not components:
                        row["flags"].append("source_notation_unresolved")
                    compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                        "assertions"
                    ][0]
                    out = public_assertion(compiled)
                    self.assertEqual(out["source_prediction_kind"], "eclipse_ephemeris")
                    self.assertEqual(out["normalized"]["magnitude"], magnitude)
                    if quantity == "calculation_epoch":
                        self.assertEqual(out["source_eclipse_phase"], "unstated")
                    else:
                        self.assertNotIn("source_eclipse_phase", out)
                    if "model_name" in model:
                        self.assertEqual(out["model_name"], model["model_name"])
                    else:
                        self.assertEqual(out["source_model_label"], model["source_model_label"])
                    if (
                        quantity == "clock_elapsed_time"
                        and model.get("model_name") == "Prutenic"
                        and magnitude is not None
                    ):
                        duration = compiled

        self.assertIsNotNone(duration)
        for change in (
            {"role": "recorded_reading"},
            {"event_id": "invented-event"},
            {"reference": "Mars"},
            {"model_name": "JPL"},
            {"model_name": None},
            {"source_model_label": "ephemerides"},
            {"source_prediction_kind": "anything"},
            {"source_eclipse_phase": "middle"},
            {"time_reference": "source_after_noon"},
            {"flags": ["not_an_additional_raw_reading"]},
            {"normalized": dict(duration["normalized"], magnitude="999")},
        ):
            with self.subTest(rejected=change), self.assertRaises(ValueError):
                public_assertion(dict(duration, **change))

    def test_native_eclipse_digit_columns_keep_primes_fractions_and_totality(self):
        from src.public_assertions import public_assertion

        cases = (
            ("9 0′", {"digit": "9", "digit_minute": "0"}, "9"),
            ("13 T. 18′", {"digit": "13", "digit_minute": "18"}, "133/10"),
            ("12½ Tot.", {"digit": "12 1/2"}, "25/2"),
            ("15 Tot.", {"digit": "15"}, "15"),
            ("20 T. 13′", {"digit": "20", "digit_minute": "13"}, "1213/60"),
            ("5 digits 37 minutes", {"digit": "5", "digit_minute": "37"}, "337/60"),
        )
        for literal, components, expected in cases:
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, components)
                row = batch["assertions"][0]
                row.update(
                    quantity="eclipse_extent",
                    subject="Moon",
                    reference=None,
                    role="historical_prediction",
                    source_extent_unit="digit",
                    unit_basis="Reviewed Digiti column: native digits and digit-minutes; T./Tot. is totality.",
                    flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
                )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                out = public_assertion(compiled)
                self.assertEqual(compiled["source_expression"], literal)
                self.assertEqual(out["normalized"]["unit"], "source_eclipse_digit")
                self.assertEqual(out["normalized"]["magnitude"], expected)

        for literal, components in (
            ("13 T. 60′", {"digit": "13", "digit_minute": "60"}),
            ("12½ Tot. 2", {"digit": "12 1/2"}),
            ("13 A. 18′", {"digit": "13", "digit_minute": "18"}),
            ("9 0″", {"digit": "9", "digit_minute": "0"}),
            ("9 0′", {"digit": "9", "digit_minute": "1"}),
        ):
            with self.subTest(rejected=literal), self.assertRaises(ValueError):
                text, spans, batch = self.explicit_clock_case(literal, components)
                batch["assertions"][0].update(
                    quantity="eclipse_extent",
                    subject="Moon",
                    reference=None,
                    role="historical_prediction",
                    source_extent_unit="digit",
                    unit_basis="Reviewed Digiti column: native digits and digit-minutes.",
                    flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
                )
                self.module().compile_catalogue([batch], {10: text}, spans)

    def test_general_planetary_native_inputs_and_editorial_supplies_keep_their_meaning(self):
        from src.public_assertions import public_assertion

        cases = (
            (
                "244005",
                {"scalar": "244005"},
                "source_scalar",
                "244005",
                "source_scalar",
                {"source_parameter_kind": "sine_value_scale_unstated"},
            ),
            (
                "2 6",
                {"proportional_minute": "2", "proportional_second": "6"},
                "proportional_minutes",
                "7/200",
                "ratio",
                {},
            ),
            (
                "[18] 21 37",
                {"degree": "18", "arcminute": "21", "arcsecond": "37"},
                "calculation_angle",
                "66097",
                "arcsecond",
                {"flags": ["not_an_additional_raw_reading", "source_editorial_component_supply"]},
            ),
        )
        for literal, components, quantity, magnitude, unit, extra in cases:
            with self.subTest(quantity=quantity):
                text, spans, batch = self.explicit_clock_case(literal, components)
                batch["assertions"][0].update(
                    quantity=quantity,
                    role="historical_input",
                    subject="planetary motion calculation",
                    reference=None,
                    direction=None,
                    flags=["not_an_additional_raw_reading"],
                    unit_basis="Stated native astronomical table units; no new physical inference",
                )
                batch["assertions"][0].update(extra)
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                out = public_assertion(row)
                self.assertEqual(row["source_expression"], literal)
                self.assertEqual(out["normalized"]["magnitude"], magnitude)
                self.assertEqual(out["normalized"]["unit"], unit)
                if quantity != "calculation_angle":
                    self.assertIsNone(out["normalized"]["magnitude_degrees"])
                    self.assertNotIn("source_scalar_scale", out)
                    with self.assertRaises(ValueError):
                        public_assertion(dict(row, role="recorded_reading"))
                else:
                    self.assertIn("source_editorial_component_supply", out["flags"])

    def test_decimal_degree_notation_keeps_literal_and_exact_value(self):
        from src.public_assertions import public_assertion

        for literal, degree, expected in (
            ("34.5 degrees", "69/2", "124200"),
            ("0.5 degree", "1/2", "1800"),
            ("2.5 degrees", "5/2", "9000"),
            ("12.125°", "97/8", "43650"),
            ("34.50 degrees", "69/2", "124200"),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, {"degree": degree})
                batch["assertions"][0].update(
                    quantity="altitude",
                    role="recorded_reading",
                    subject="comet head",
                    reference=None,
                    direction=None,
                    source_unit_notation="decimal_degrees",
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                out = public_assertion(row)
                self.assertEqual(row["source_expression"], literal)
                self.assertEqual(out["normalized"]["magnitude"], expected)
                self.assertEqual(out["source_unit_notation"], "decimal_degrees")
                with self.assertRaises(ValueError):
                    public_assertion(dict(row, components={"degree": "5"}))

    def test_decimal_degree_notation_rejects_partial_or_contradictory_expressions(self):
        from src.normalization import interpret_part_minute_notation

        for literal in (
            "34.5",
            "-34.5 degrees",
            "1.5 degrees 30 minutes",
            "34,5 degrees",
            "34.5 hours",
            "1e2 degrees",
            "34.5 degrees[?]",
            "prefix 34.5 degrees",
        ):
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                interpret_part_minute_notation(
                    dict(
                        source_expression=literal,
                        quantity="altitude",
                        source_unit_notation="decimal_degrees",
                    )
                )
        with self.assertRaises(ValueError):
            interpret_part_minute_notation(
                dict(
                    source_expression="34.5 degrees",
                    quantity="recorded_clock",
                    source_unit_notation="decimal_degrees",
                )
            )

    def test_decimal_hour_notation_preserves_times_without_degree_or_clock_inference(self):
        from src.public_assertions import public_assertion
        from src.normalization import interpret_part_minute_notation

        for literal, quantity, hour, expected in (
            ("7.25 hours", "annotated_time", "29/4", "26100"),
            ("7.5 hours", "recorded_clock", "15/2", "27000"),
            ("10.75 hours", "clock_elapsed_time", "43/4", "38700"),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, {"hour": hour})
                batch["assertions"][0].update(
                    quantity=quantity,
                    role="recorded_clock" if quantity == "recorded_clock" else "historical_input",
                    subject="observing clock",
                    reference=None,
                    direction=None,
                    source_unit_notation="decimal_hours",
                    flags=["absolute_time_unestablished"],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                self.assertEqual(public_assertion(row)["normalized"]["magnitude"], expected)
                self.assertEqual(row["source_expression"], literal)
        for literal in ("7.25 degrees", "7.25 hours 30 minutes", "7,25 hours", "7.25 hours[?]"):
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                interpret_part_minute_notation(
                    dict(
                        quantity="annotated_time",
                        source_unit_notation="decimal_hours",
                        source_expression=literal,
                    )
                )
        with self.assertRaises(ValueError):
            interpret_part_minute_notation(
                dict(
                    quantity="altitude",
                    source_unit_notation="decimal_hours",
                    source_expression="7.25 hours",
                )
            )

    def test_comparison_star_altitude_time_is_a_reduction_not_an_observing_clock(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("hour 5⅙", {"hour": "5 1/6"})
        batch["assertions"][0].update(
            quantity="inferred_time",
            role="reduction",
            subject="observing clock",
            reference=None,
            time_inference_basis="comparison_star_altitude",
            flags=["not_an_additional_raw_reading", "absolute_time_unestablished"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "18600")
        self.assertEqual(out["time_inference_basis"], "comparison_star_altitude")
        altitude_out = public_assertion(dict(row, time_inference_basis="observed_altitude"))
        self.assertEqual(altitude_out["normalized"]["magnitude"], "18600")
        self.assertEqual(altitude_out["time_inference_basis"], "observed_altitude")
        for change in (
            {"role": "recorded_clock"},
            {"quantity": "recorded_clock"},
            {"time_inference_basis": "invented_basis"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(dict(row, **change))

    def test_unsigned_witness_differences_preserve_complete_angles_without_a_sign(self):
        from src.public_assertions import public_assertion

        for literal, components, expected in (
            ("1° 26′", {"degree": "1", "arcminute": "26"}, "5160"),
            ("0° 26′", {"degree": "0", "arcminute": "26"}, "1560"),
            ("1½° 15½′", {"degree": "1 1/2", "arcminute": "15 1/2"}, "6330"),
            (
                "1° 30′ ½″",
                {"degree": "1", "arcminute": "30", "arcsecond": "1/2"},
                "10801/2",
            ),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, components)
                batch["assertions"][0].update(
                    quantity="separation_difference",
                    role="historical_comparison",
                    subject="New Star of 1572",
                    reference="Pole Star",
                    direction=None,
                    comparison_sources=["Cornelius Gemma", "Tycho Brahe"],
                    comparison_relation="unsigned_difference_as_stated",
                    source_comparison_sign="not_stated",
                    flags=["not_an_additional_raw_reading"],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                out = public_assertion(row)
                self.assertEqual(row["source_expression"], literal)
                self.assertEqual(out["normalized"]["magnitude"], expected)
                self.assertIsNone(out["normalized"]["signed_magnitude"])
                self.assertEqual(out["source_comparison_sign"], "not_stated")
                self.assertEqual(out["comparison_relation"], "unsigned_difference_as_stated")
                self.assertNotIn("comparison_label_original", out)

    def test_unsigned_witness_comparison_rejects_changed_units_or_invented_semantics(self):
        from src.normalization import normalize_quantity
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("1° 26′", {"degree": "1", "arcminute": "26"})
        batch["assertions"][0].update(
            quantity="separation_difference",
            role="historical_comparison",
            subject="New Star of 1572",
            reference="Pole Star",
            direction=None,
            comparison_sources=["Cornelius Gemma", "Tycho Brahe"],
            comparison_relation="unsigned_difference_as_stated",
            source_comparison_sign="not_stated",
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        for change in (
            {"components": {"degree": "1", "arcsecond": "26"}},
            {"components": {"degree": "1", "arcminute": "27"}},
            {"source_expression": "1° 26′ 9"},
            {"source_expression": "-1° 26′"},
            {"source_expression": "1° 26′ north"},
            {"source_comparison_sign": "plus"},
            {"comparison_label_original": "minus"},
            {"comparison_relation": "second_minus_first_as_stated"},
            {"comparison_sources": ["Gemma", "Gemma"]},
            {"reference": None},
            {"event_id": "event-v10-" + "a" * 20},
            {"role": "recorded_reading"},
            {"direction": "north"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                bad = dict(row, **change)
                bad["normalized"] = normalize_quantity(bad)
                public_assertion(bad)

    def test_comparison_contraction_is_a_sign_label_not_an_extra_digit(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("7 min⁹", {"arcminute": "7"})
        batch["assertions"][0].update(
            quantity="separation_difference",
            role="historical_comparison",
            subject="New Star of 1572",
            reference="Pole Star",
            direction=None,
            comparison_sources=["Hagecius, earlier Dialexis", "Brahe"],
            comparison_relation="second_minus_first_as_stated",
            comparison_label_original="min⁹",
            source_comparison_sign="minus",
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(row["source_expression"], "7 min⁹")
        self.assertEqual(out["normalized"]["magnitude"], "420")
        self.assertEqual(out["source_comparison_sign"], "minus")
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["source_comparison_sign"] = "plus"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_written_fractional_precision_and_clock_addend_keep_their_units(self):
        for literal, components, quantity, words, addends, expected in (
            (
                "eleven twelfths of a minute",
                {"arcminute": "11/12"},
                "parallax_angle",
                {"eleven twelfths": "11/12"},
                None,
                "55",
            ),
            (
                "one degree and three quarters",
                {"degree": "1 3/4"},
                "altitude_difference",
                {"one degree and three quarters": "1 3/4"},
                None,
                "6300",
            ),
            (
                "twenty-two degrees",
                {"degree": "22"},
                "altitude",
                {"twenty-two": "22"},
                None,
                "79200",
            ),
            (
                "two minutes and one quarter",
                {"minute": "2 1/4"},
                "clock_correction",
                {"two": "2", "one quarter": "1/4"},
                {"minute": ["2", "1/4"]},
                "135",
            ),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, components)
                a = batch["assertions"][0]
                a.update(quantity=quantity, source_word_numbers=words)
                if addends is not None:
                    a["source_component_addends"] = addends
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                self.assertEqual(row["normalized"]["magnitude"], expected)

    def test_prefixed_hour_with_written_fraction_uses_source_addends(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("hour 1 with a sixth part", {"hour": "7/6"})
        batch["assertions"][0].update(
            quantity="calculation_epoch",
            subject="Sun",
            reference=None,
            role="calculation_epoch",
            source_word_numbers={"a sixth": "1/6"},
            source_component_addends={"hour": ["1", "1/6"]},
            flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "4200")
        self.assertEqual(row["source_expression"], "hour 1 with a sixth part")
        self.assertEqual(row["components"], {"hour": "7/6"})
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["source_component_addends"]["hour"][1] = "1/5"
        bad["assertions"][0]["components"]["hour"] = "6/5"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_source_comparison_labels_consume_the_complete_fractional_magnitude(self):
        from src.normalization import source_numeric_text

        row = dict(
            quantity="separation_difference",
            role="historical_comparison",
            comparison_sources=["Earlier edition", "Later edition"],
            comparison_relation="second_minus_first_as_stated",
        )
        for label, sign in (
            ("plus", "plus"),
            ("pl.", "plus"),
            ("min.", "minus"),
            ("minus", "minus"),
            ("min⁹", "minus"),
            ("min", "minus"),
        ):
            with self.subTest(label=label):
                settings = dict(row, comparison_label_original=label, source_comparison_sign=sign)
                self.assertEqual(source_numeric_text(settings, "1½ " + label), "1 1/2")
                for expression in ("1 2 " + label, "1 " + label + " 2", "1 min9", "1"):
                    with self.subTest(expression=expression), self.assertRaises(ValueError):
                        source_numeric_text(settings, expression)

    def test_recorded_native_magnitude_class_keeps_observational_role_and_qualifications(self):
        from src.public_assertions import public_assertion

        for literal, value, words, flags in (
            ("3", "3", {}, []),
            ("fourth", "4", {"fourth": "4"}, ["source_approximate"]),
            ("3rd", "3", {"3rd": "3"}, []),
            ("5th", "5", {"5th": "5"}, []),
            ("6th", "6", {"6th": "6"}, []),
            ("10th", "10", {"10th": "10"}, []),
            ("12th", "12", {"12th": "12"}, []),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, {"scalar": value})
                batch["assertions"][0].update(
                    quantity="stellar_magnitude_class",
                    role="recorded_reading",
                    subject="Regulus",
                    reference=None,
                    source_word_numbers=words,
                    flags=flags,
                    unit_basis="Observer's stated native visual class",
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                out = public_assertion(row)
                self.assertEqual(out["role"], "recorded_reading")
                self.assertEqual(out["flags"], flags)
                self.assertEqual(out["normalized"]["magnitude"], value)
                self.assertEqual(out["normalized"]["unit"], "source_visual_magnitude_class")
                self.assertIsNone(out["normalized"]["magnitude_degrees"])
                self.assertIsNone(out["normalized"]["signed_magnitude"])
                for change in (
                    {"reference": "Venus"},
                    {"direction": "north"},
                    {"model_name": "Copernicus"},
                ):
                    with self.subTest(change=change), self.assertRaises(ValueError):
                        public_assertion(dict(row, **change))
                corrupt = copy.deepcopy(row)
                corrupt["normalized"]["magnitude"] = str(int(value) + 1)
                with self.assertRaises(ValueError):
                    public_assertion(corrupt)

    def test_explicit_no_hour_keeps_zero_hour_in_elapsed_interval(self):
        from src.public_assertions import public_assertion

        literal = "no hour, 37^m^"
        text, spans, batch = self.explicit_clock_case(literal, {"hour": "0", "minute": "37"})
        batch["assertions"][0].update(
            quantity="clock_elapsed_time",
            subject="Sun",
            reference=None,
            role="historical_input",
            flags=["not_an_additional_raw_reading"],
            source_word_numbers={"no hour": "0"},
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "2220")
        self.assertEqual(row["components"], {"hour": "0", "minute": "37"})
        self.assertEqual(row["source_expression"], literal)

    def test_native_mile_fraction_preserves_its_worded_expression_and_unspecified_unit(self):
        from src.public_assertions import public_assertion

        literal = "a mile and a half"
        text, spans, batch = self.explicit_clock_case(literal, {"mile": "1 1/2"})
        batch["assertions"][0].update(
            quantity="distance_in_unspecified_miles",
            role="historical_input",
            subject="Earth calculation",
            reference=None,
            flags=["not_an_additional_raw_reading"],
            source_word_numbers={literal: "1 1/2"},
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(row["source_expression"], literal)
        self.assertEqual(out["normalized"]["magnitude"], "3/2")
        self.assertEqual(out["normalized"]["unit"], "source_unspecified_mile")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])

    def test_queried_native_model_length_keeps_unit_without_adopting_a_value(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("1189 [?]", {})
        row = batch["assertions"][0]
        row.update(
            quantity="source_sexagesimal_length",
            role="historical_input",
            subject="Moon calculation",
            reference=None,
            flags=["not_an_additional_raw_reading", "source_notation_unresolved"],
        )
        compiled = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(compiled)
        self.assertEqual(out["normalized"]["unit"], "source_length_part")
        self.assertEqual(out["normalized"]["status"], "unsupported")
        self.assertIsNone(out["normalized"]["magnitude"])
        for change in ({"subject": "Moon"}, {"role": "recorded_reading"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(dict(compiled, **change))
        for change in ({"components": {"source_part": "1189"}}, {"direction": "north"}):
            bad = copy.deepcopy(batch)
            bad["assertions"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {10: text}, spans)

    def test_native_model_length_editorial_variant_requires_its_unapplied_original(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("42 [recte: 41]", {"source_part": "42"})
        row = batch["assertions"][0]
        row.update(
            quantity="source_sexagesimal_length",
            role="historical_input",
            subject="Moon calculation",
            reference=None,
            source_expression="42",
            flags=["not_an_additional_raw_reading"],
        )
        variant = dict(
            row,
            key="variant",
            source_expression="41",
            components={"source_part": "41"},
            role="editorial_variant",
            variant_of_key=row["key"],
            annotation_of_key=row["key"],
            flags=[
                "not_an_additional_raw_reading",
                "source_annotation_variant",
                "alternative_suggestion_not_applied",
            ],
        )
        batch["assertions"].append(variant)
        rows = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"]
        child = next(r for r in rows if r["role"] == "editorial_variant")
        self.assertEqual(public_assertion(child)["normalized"]["magnitude"], "41")
        self.assertEqual(
            next(r for r in rows if r["role"] == "historical_input")["normalized"]["magnitude"],
            "42",
        )
        for change in (
            {"variant_of_id": None},
            {"annotation_of_id": None},
            {"flags": ["not_an_additional_raw_reading"]},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(dict(child, **change))

    def test_scaled_model_length_editorial_variant_retains_its_original(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("42 [recte: 41]", {"scalar": "42"})
        row = batch["assertions"][0]
        row.update(
            quantity="source_scalar",
            role="historical_input",
            subject="Saturn calculation",
            reference=None,
            source_expression="42",
            source_parameter_kind="model_length",
            source_scalar_scale="100000",
            flags=["not_an_additional_raw_reading"],
        )
        batch["assertions"].append(
            dict(
                row,
                key="variant",
                source_expression="41",
                components={"scalar": "41"},
                role="editorial_variant",
                variant_of_key=row["key"],
                annotation_of_key=row["key"],
                flags=[
                    "not_an_additional_raw_reading",
                    "source_annotation_variant",
                    "alternative_suggestion_not_applied",
                ],
            )
        )
        rows = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"]
        child = next(r for r in rows if r["role"] == "editorial_variant")
        self.assertEqual(public_assertion(child)["normalized"]["magnitude"], "41")
        parent = next(r for r in rows if r["role"] == "historical_input")
        self.assertEqual(public_assertion(parent)["normalized"]["magnitude"], "42")
        for change in (
            {"variant_of_id": None},
            {"annotation_of_id": None},
            {"event_id": "invented-event"},
            {"flags": ["not_an_additional_raw_reading"]},
            {"source_scalar_scale": None},
            {"role": "recorded_reading"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(dict(child, **change))

    def test_native_stellar_class_source_alternative_requires_a_link(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("4, or 5", {"scalar": "4"})
        row = batch["assertions"][0]
        row.update(
            quantity="stellar_magnitude_class",
            role="adopted_value",
            subject="fixed stars",
            reference=None,
            source_expression="4",
            flags=["not_an_additional_raw_reading"],
        )
        batch["assertions"].append(
            dict(
                row,
                key="alternative",
                source_expression="5",
                components={"scalar": "5"},
                role="source_alternative",
                variant_of_key=row["key"],
                flags=["not_an_additional_raw_reading", "alternative_suggestion_not_applied"],
            )
        )
        rows = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"]
        child = next(r for r in rows if r["role"] == "source_alternative")
        self.assertEqual(public_assertion(child)["normalized"]["magnitude"], "5")
        for change in (
            {"variant_of_id": None},
            {"event_id": "invented-event"},
            {"flags": ["not_an_additional_raw_reading"]},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(dict(child, **change))

    def test_planetary_proportional_coefficients_keep_ratios_and_native_seconds(self):
        from src.public_assertions import public_assertion

        for subject in (
            "Saturn",
            "Jupiter",
            "Venus",
            "Mercury",
            "fixed stars",
            "Saturn, Jupiter and Mars calculation",
        ):
            for literal, components, expected in (
                ("2 57", {"proportional_minute": "2", "proportional_second": "57"}, "59/1200"),
                ("60 0", {"proportional_minute": "60", "proportional_second": "0"}, "1"),
                ("24", {"proportional_second": "24"}, "1/150"),
                ("90", {"proportional_second": "90"}, "1/40"),
                ("0", {"proportional_second": "0"}, "0"),
            ):
                with self.subTest(subject=subject, literal=literal):
                    text, spans, batch = self.explicit_clock_case(literal, components)
                    batch["assertions"][0].update(
                        quantity="proportional_minutes",
                        role="historical_input",
                        subject=subject,
                        reference=None,
                        flags=["not_an_additional_raw_reading"],
                    )
                    row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][
                        0
                    ]
                    out = public_assertion(row)
                    self.assertEqual(out["normalized"]["unit"], "ratio")
                    self.assertEqual(out["normalized"]["magnitude"], expected)
                    self.assertIsNone(out["normalized"]["magnitude_degrees"])
        for components in (
            {"proportional_second": "3601"},
            {"proportional_minute": "60", "proportional_second": "1"},
            {"proportional_minute": "1", "proportional_second": "60"},
        ):
            with self.subTest(invalid=components), self.assertRaises(ValueError):
                self.module().normalize_quantity(
                    dict(quantity="proportional_minutes", components=components)
                )

    def test_proportional_coefficients_preserve_the_third_sexagesimal_place(self):
        from src.public_assertions import public_assertion

        units = ("proportional_minute", "proportional_second", "proportional_third")
        for literal, values, expected in (
            ("45 12 0", ("45", "12", "0"), "113/150"),
            ("1′ 29″ 30‴", ("1", "29", "30"), "179/7200"),
            ("60 0 0", ("60", "0", "0"), "1"),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(
                    literal, dict(zip(units, values, strict=True))
                )
                batch["assertions"][0].update(
                    quantity="proportional_minutes",
                    role="historical_input",
                    subject="Jupiter",
                    flags=["not_an_additional_raw_reading"],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                out = public_assertion(row)
                self.assertEqual(out["normalized"]["magnitude"], expected)
                self.assertEqual(out["normalized"]["least_component_unit"], "proportional_third")
                self.assertEqual(row["source_expression"], literal)

        for values in (("1", "0", "60"), ("60", "0", "1"), ("0", "60", "0"), ("0", "0", "-1")):
            with self.subTest(invalid=values), self.assertRaises(ValueError):
                self.module().normalize_quantity(
                    dict(
                        quantity="proportional_minutes",
                        components=dict(zip(units, values, strict=True)),
                    )
                )

        text, spans, batch = self.explicit_clock_case(
            "1′ 29″ 30″", dict(zip(units, ("1", "29", "30"), strict=True))
        )
        batch["assertions"][0].update(quantity="proportional_minutes", subject="Jupiter")
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([batch], {10: text}, spans)

    def test_queried_planetary_proportional_coefficient_has_no_adopted_ratio(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("38 22 [?]", {})
        batch["assertions"][0].update(
            quantity="proportional_minutes",
            subject="Venus",
            reference=None,
            role="historical_input",
            flags=["source_notation_unresolved", "not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["unit"], "ratio")
        self.assertEqual(out["normalized"]["status"], "unsupported")
        self.assertIsNone(out["normalized"]["magnitude"])
        for change in (
            {"subject": "Regulus"},
            {"role": "recorded_reading"},
            {"reference": "Earth"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(dict(row, **change))
        for change in (
            {"direction": "north"},
            {"zodiac_sign": "Aries"},
            {"components": {"proportional_minute": "38"}},
        ):
            bad = copy.deepcopy(batch)
            bad["assertions"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {10: text}, spans)

    def test_proportional_coefficient_editorial_variant_requires_its_unapplied_original(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "2 57 [recte: 1 57]", {"proportional_minute": "2", "proportional_second": "57"}
        )
        row = batch["assertions"][0]
        row.update(
            quantity="proportional_minutes",
            role="historical_input",
            subject="Venus",
            reference=None,
            source_expression="2 57",
            flags=["not_an_additional_raw_reading"],
        )
        batch["assertions"].append(
            dict(
                row,
                key="variant",
                source_expression="1 57",
                components={"proportional_minute": "1", "proportional_second": "57"},
                role="editorial_variant",
                variant_of_key=row["key"],
                annotation_of_key=row["key"],
                flags=[
                    "not_an_additional_raw_reading",
                    "source_annotation_variant",
                    "alternative_suggestion_not_applied",
                ],
            )
        )
        rows = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"]
        child = next(r for r in rows if r["role"] == "editorial_variant")
        self.assertEqual(public_assertion(child)["normalized"]["magnitude"], "13/400")
        self.assertEqual(
            next(r for r in rows if r["role"] == "historical_input")["normalized"]["magnitude"],
            "59/1200",
        )
        for change in (
            {"variant_of_id": None},
            {"annotation_of_id": None},
            {"flags": ["not_an_additional_raw_reading"]},
            {"event_id": "invented"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(dict(child, **change))

    def test_shared_planetary_motion_table_keeps_one_elapsed_argument(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("30", {"hour": "30"})
        batch["assertions"][0].update(
            quantity="clock_elapsed_time",
            role="historical_input",
            subject="Saturn, Jupiter and Mars calculation",
            reference=None,
            flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
        )
        rows = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"]
        self.assertEqual(len(rows), 1)
        row = public_assertion(rows[0])
        self.assertEqual(row["normalized"]["magnitude"], "108000")
        self.assertEqual(row["normalized"]["unit"], "second_of_time")
        self.assertIsNone(row["event_id"])

    def test_native_stellar_magnitude_classes_preserve_notation_and_unresolved_entries(self):
        from src.public_assertions import public_assertion

        for literal, value, unresolved in (
            ("3:", "3", False),
            ("3-", "3", False),
            ("4.", "4", False),
            ("4½", "9/2", False),
            ("ne.", None, True),
            ("⟦3/5⟧", None, True),
            ("2 [?]", None, True),
        ):
            with self.subTest(literal=literal):
                components = {} if unresolved else {"scalar": "4 1/2" if value == "9/2" else value}
                text, spans, batch = self.explicit_clock_case(literal, components)
                batch["assertions"][0].update(
                    quantity="stellar_magnitude_class",
                    role="historical_input",
                    subject="Regulus",
                    reference=None,
                    flags=["not_an_additional_raw_reading"]
                    + (["source_notation_unresolved"] if unresolved else []),
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                out = public_assertion(row)
                self.assertEqual(out["normalized"]["magnitude"], value)
                self.assertEqual(out["normalized"]["unit"], "source_visual_magnitude_class")
                self.assertIsNone(out["normalized"]["magnitude_degrees"])
                self.assertIsNone(out["normalized"]["signed_magnitude"])
                self.assertEqual(row["source_expression"], literal)
                if literal == "ne.":
                    descriptive = dict(
                        batch["assertions"][0], flags=["not_an_additional_raw_reading"]
                    )
                    descriptive["normalized"] = self.module().normalize_quantity(descriptive)
                    self.assertIsNone(
                        public_assertion(dict(row, **descriptive))["normalized"]["magnitude"]
                    )
                with self.assertRaises(ValueError):
                    public_assertion(dict(row, direction="north"))
                with self.assertRaises(ValueError):
                    public_assertion(dict(row, role="historical_prediction"))
                altered = copy.deepcopy(row)
                altered["normalized"]["magnitude"] = "999"
                with self.assertRaises(ValueError):
                    public_assertion(altered)
                if unresolved:
                    interpreted = copy.deepcopy(batch)
                    interpreted["assertions"][0]["components"] = {"scalar": "3/5"}
                    with self.assertRaises(ValueError):
                        self.module().compile_catalogue([interpreted], {10: text}, spans)

    def test_multiple_source_zodiac_candidates_do_not_select_an_absolute_longitude(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "13° 9′ 19″ ⟦♍/♏⟧", {"degree": "13", "arcminute": "9", "arcsecond": "19"}
        )
        batch["assertions"][0].update(
            quantity="ecliptic_longitude",
            role="historical_input",
            subject="Sun",
            reference=None,
            direction=None,
            source_zodiac_candidates=["Virgo", "Scorpio"],
            flags=["not_an_additional_raw_reading", "source_zodiac_identification_uncertain"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(out["source_zodiac_candidates"], ["Virgo", "Scorpio"])
        self.assertEqual(out["normalized"]["magnitude"], "47359")
        self.assertNotIn("zodiac_longitude_degrees", out["normalized"])
        for candidates in (["Virgo"], ["Virgo", "Virgo"], ["Virgo", "Pisces"], "Virgo/Scorpio"):
            with self.subTest(candidates=candidates), self.assertRaises(ValueError):
                public_assertion(dict(row, source_zodiac_candidates=candidates))
        with self.assertRaises(ValueError):
            public_assertion(dict(row, source_zodiac_candidate="Virgo"))

    def test_tentative_solar_zodiac_keeps_known_components_without_adopting_a_sign(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "18° 51′ 22″", {"degree": "18", "arcminute": "51", "arcsecond": "22"}
        )
        batch["assertions"][0].update(
            quantity="ecliptic_longitude",
            role="historical_input",
            subject="Sun",
            reference=None,
            direction=None,
            source_zodiac_candidate="Pisces",
            flags=["not_an_additional_raw_reading", "source_zodiac_identification_uncertain"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(out["source_zodiac_candidate"], "Pisces")
        self.assertEqual(out["normalized"]["magnitude"], "67882")
        self.assertNotIn("zodiac_longitude_degrees", out["normalized"])
        self.assertNotIn("zodiac_sign", out["normalized"])
        bad = copy.deepcopy(row)
        bad["zodiac_sign"] = "Pisces"
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_stellar_calendar_counts_and_yearly_motion_keep_native_periods(self):
        from src.public_assertions import public_assertion

        for literal, value, kind in (
            ("3", "3", "source_year_count"),
            ("9⅓", "28/3", "source_month_count"),
        ):
            with self.subTest(kind=kind):
                text, spans, batch = self.explicit_clock_case(
                    literal, {"scalar": "3" if kind == "source_year_count" else "9 1/3"}
                )
                batch["assertions"][0].update(
                    quantity="source_scalar",
                    role="historical_input",
                    subject="stellar calibration calculation",
                    reference=None,
                    direction=None,
                    source_parameter_kind=kind,
                    flags=["not_an_additional_raw_reading"],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                out = public_assertion(row)
                self.assertEqual(out["normalized"]["magnitude"], value)
                self.assertEqual(out["source_parameter_kind"], kind)
        text, spans, batch = self.explicit_clock_case("51″", {"arcsecond": "51"})
        batch["assertions"][0].update(
            quantity="angular_yearly_motion",
            role="historical_input",
            subject="fixed stars",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["unit"], "arcsecond_per_source_year")
        self.assertEqual(out["normalized"]["magnitude"], "51")

    def test_native_model_scalars_support_all_named_classical_bodies(self):
        from src.public_assertions import public_assertion

        for body in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
            for kind in ("model_length", "arithmetic_intermediate"):
                with self.subTest(body=body, kind=kind):
                    text, spans, batch = self.explicit_clock_case("66262", {"scalar": "66262"})
                    a = batch["assertions"][0]
                    a.update(
                        quantity="source_scalar",
                        role="calculation_intermediate",
                        subject=body + " calculation",
                        reference=None,
                        direction=None,
                        source_parameter_kind=kind,
                        flags=["not_an_additional_raw_reading"],
                    )
                    if kind == "model_length":
                        a["source_scalar_scale"] = "100000"
                    row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][
                        0
                    ]
                    self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "66262")
                    bad = copy.deepcopy(row)
                    bad["role"] = "recorded_reading"
                    with self.assertRaises(ValueError):
                        public_assertion(bad)

    def test_instrument_circle_count_preserves_a_fraction_without_angle_conversion(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("one-and-a-half circles", {"scalar": "1 1/2"})
        batch["assertions"][0].update(
            quantity="source_scalar",
            role="historical_input",
            subject="instrument",
            reference=None,
            direction=None,
            source_parameter_kind="instrument_circle_count",
            source_word_numbers={"one-and-a-half": "1 1/2"},
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        norm = public_assertion(row)["normalized"]
        self.assertEqual(norm["magnitude"], "3/2")
        self.assertEqual(norm["unit"], "source_scalar")
        self.assertIsNone(norm["magnitude_degrees"])

    def test_incomplete_lunar_calculation_clock_does_not_supply_a_minute(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("6 hours 55″", {})
        batch["assertions"][0].update(
            quantity="calculation_epoch",
            role="calculation_epoch",
            subject="Moon",
            reference=None,
            direction=None,
            flags=[
                "source_notation_unresolved",
                "not_an_observing_clock",
                "not_an_additional_raw_reading",
            ],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        norm = public_assertion(row)["normalized"]
        self.assertEqual(norm["status"], "unsupported")
        self.assertIsNone(norm["magnitude"])

    def test_source_word_degree_error_claims_keep_their_literal_forms(self):
        for literal, value in (("a whole degree", "1"), ("a full degree and a half", "1 1/2")):
            text, spans, batch = self.explicit_clock_case(literal, {"degree": value})
            batch["assertions"][0].update(
                quantity="calculation_angle",
                role="historical_input",
                subject="Moon calculation",
                reference=None,
                direction=None,
                source_word_numbers={literal: value},
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            self.assertEqual(row["source_expression"], literal)
            self.assertEqual(row["components"], {"degree": value})

    def test_word_fifty_preserves_a_native_meridian_time_difference(self):
        text, spans, batch = self.explicit_clock_case("fifty minutes of time", {"minute": "50"})
        batch["assertions"][0].update(
            quantity="meridian_time_difference",
            role="historical_input",
            subject="observing site",
            reference=None,
            direction=None,
            source_word_numbers={"fifty": "50"},
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(row["normalized"]["magnitude"], "3000")
        self.assertEqual(row["source_expression"], "fifty minutes of time")

    def test_whole_sign_rate_retains_counted_sign_without_a_zodiac_origin(self):
        text, spans, batch = self.explicit_clock_case("a whole sign", {"sign_count": "1"})
        batch["assertions"][0].update(
            quantity="angular_yearly_motion",
            role="historical_input",
            subject="Jupiter",
            reference=None,
            direction=None,
            source_word_numbers={"a whole sign": "1"},
            flags=["not_an_additional_raw_reading", "source_upper_bound", "source_approximate"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(row["normalized"]["magnitude"], "108000")
        self.assertEqual(row["normalized"]["unit"], "arcsecond_per_source_year")
        self.assertIsNone(row["normalized"]["magnitude_degrees"])
        self.assertNotIn("zodiac_longitude_degrees", row["normalized"])

    def test_native_eclipse_prose_retains_commas_words_and_isolated_subunits(self):
        from fractions import Fraction
        from src.public_assertions import public_assertion

        cases = (
            ("13 digits, 36 minutes", {"digit": "13", "digit_minute": "36"}, Fraction(68, 5)),
            (
                "11 digits, 45 minutes, 36 seconds",
                {"digit": "11", "digit_minute": "45", "digit_second": "36"},
                Fraction(11) + Fraction(45, 60) + Fraction(36, 3600),
            ),
            ("50 minutes", {"digit_minute": "50"}, Fraction(5, 6)),
            ("36 seconds", {"digit_second": "36"}, Fraction(1, 100)),
            (
                "50 minutes, 36 seconds",
                {"digit_minute": "50", "digit_second": "36"},
                Fraction(50, 60) + Fraction(36, 3600),
            ),
            ("one digit", {"digit": "1"}, Fraction(1)),
            ("6", {"digit": "6"}, Fraction(6)),
        )
        for literal, components, expected in cases:
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, components)
                assertion = batch["assertions"][0]
                assertion.update(
                    quantity="eclipse_extent",
                    subject="Sun",
                    reference=None,
                    role="historical_input",
                    source_extent_unit="digit",
                    flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
                )
                if literal.startswith("one"):
                    assertion["source_word_numbers"] = {"one": "1"}
                if literal == "6":
                    assertion["unit_basis"] = (
                        "Digit unit inherited from the source eclipse-extent clause."
                    )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                row = public_assertion(compiled)
                self.assertEqual(compiled["source_expression"], literal)
                self.assertEqual(compiled["components"], components)
                self.assertEqual(Fraction(row["normalized"]["magnitude"]), expected)
                self.assertEqual(row["normalized"]["unit"], "source_eclipse_digit")
                self.assertIsNone(row["normalized"]["magnitude_degrees"])
                if "digit" not in components:
                    self.assertNotIn("digit", compiled["components"])
        for literal, components in (
            ("50 minutes", {"digit_second": "50"}),
            ("50 seconds", {"digit_minute": "50"}),
            ("60 minutes", {"digit_minute": "60"}),
            ("60 seconds", {"digit_second": "60"}),
            ("13 digits, 36 degrees", {"digit": "13", "digit_minute": "36"}),
            ("13 digits, 36 minutes and the rest", {"digit": "13", "digit_minute": "36"}),
            ("6", {"digit": "6"}),
        ):
            with self.subTest(invalid=literal), self.assertRaises(ValueError):
                self.module().normalize_quantity(
                    dict(
                        quantity="eclipse_extent",
                        source_extent_unit="digit",
                        source_expression=literal,
                        components=components,
                    )
                )

    def test_native_eclipse_extent_keeps_a_separately_glossed_minute_component(self):
        from src.public_assertions import public_assertion

        literal = "12 digits with a dextans — that is, 50 minutes"
        text, spans, batch = self.explicit_clock_case(
            literal, {"digit": "12", "digit_minute": "50"}
        )
        batch["contexts"] = [
            dict(
                key="gloss",
                kind="source_observation_context",
                lines=[1],
                value=dict(
                    record_type="source_continuation",
                    source_expression="with a dextans — that is,",
                ),
            )
        ]
        assertion = batch["assertions"][0]
        assertion.update(
            source_expression="12 digits",
            quantity="eclipse_extent",
            subject="Sun",
            reference=None,
            role="historical_input",
            source_extent_unit="digit",
            source_continuation_context_key="gloss",
            context_keys=["gloss"],
            source_fragments=[
                dict(line=1, span_id="s", source_expression="12 digits"),
                dict(line=1, span_id="s", source_expression="50 minutes"),
            ],
            flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
        )
        compiled = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        row = public_assertion(compiled)
        self.assertEqual(compiled["source_expression"], "12 digits")
        self.assertEqual(compiled["source_fragments"][1]["source_expression"], "50 minutes")
        self.assertEqual(row["normalized"]["magnitude"], "77/6")
        self.assertEqual(row["normalized"]["unit"], "source_eclipse_digit")
        batch["assertions"][0]["components"]["digit_minute"] = "49"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([batch], {10: text}, spans)

    def test_native_eclipse_digits_keep_sexagesimal_extent_and_source_units(self):
        from fractions import Fraction
        from src.public_assertions import public_assertion

        cases = [
            (
                "10 digits 55′ 6″",
                {"digit": "10", "digit_minute": "55", "digit_second": "6"},
                Fraction(6551, 600),
                "historical_prediction",
            ),
            (
                "9.34′ 52″",
                {"digit": "9", "digit_minute": "34", "digit_second": "52"},
                Fraction(8623, 900),
                "historical_prediction",
            ),
            ("12 digits", {"digit": "12"}, Fraction(12), "historical_input"),
            (
                "5 digits 37 minutes",
                {"digit": "5", "digit_minute": "37"},
                Fraction(337, 60),
                "historical_prediction",
            ),
            (
                "5 digits 37 minutes 12 seconds",
                {"digit": "5", "digit_minute": "37", "digit_second": "12"},
                Fraction(281, 50),
                "historical_prediction",
            ),
        ]
        for literal, components, expected, role in cases:
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, components)
                batch["assertions"][0].update(
                    quantity="eclipse_extent",
                    role=role,
                    subject="Moon",
                    reference=None,
                    direction=None,
                    source_extent_unit="digit",
                    flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                out = public_assertion(row)
                self.assertEqual(out["normalized"]["unit"], "source_eclipse_digit")
                self.assertEqual(Fraction(out["normalized"]["magnitude"]), expected)
                self.assertIsNone(out["normalized"]["magnitude_degrees"])
                self.assertEqual(out["source_extent_unit"], "digit")
                bad = copy.deepcopy(row)
                bad["normalized"]["magnitude"] = "999"
                with self.assertRaises(ValueError):
                    public_assertion(bad)
        for literal in (
            "10 digits 60′ 6″",
            "10 digits 55′ 60″",
            "9.34 52",
            "10° 55′ 6″",
            "10 digits 60 minutes 6 seconds",
            "10 digits 55 minutes 60 seconds",
        ):
            with self.subTest(invalid=literal), self.assertRaises(ValueError):
                self.module().normalize_quantity(
                    dict(
                        quantity="eclipse_extent",
                        role="historical_prediction",
                        source_extent_unit="digit",
                        source_expression=literal,
                        components={"digit": "10", "digit_minute": "55", "digit_second": "6"},
                    )
                )

    def test_native_eclipse_digit_table_retains_bare_columns_and_shared_application(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "2 | 30", {"digit": "2", "digit_minute": "30"}
        )
        batch["assertions"][0].update(
            quantity="eclipse_extent",
            role="historical_input",
            subject="Sun and Moon",
            reference=None,
            direction=None,
            source_extent_unit="digit",
            flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
            unit_basis="Shared Sun-or-Moon native Digit./minute conversion table",
        )
        try:
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            out = public_assertion(row)
        except ValueError as exc:
            self.fail(f"The source's shared application must not require two copies: {exc}")
        self.assertEqual(out["subject"], "Sun and Moon")
        self.assertEqual(out["normalized"]["unit"], "source_eclipse_digit")
        self.assertEqual(out["normalized"]["magnitude"], "5/2")
        with self.assertRaises(ValueError):
            public_assertion(dict(row, subject="Mars"))

        point_text, point_spans, point_batch = self.explicit_clock_case(
            "2 points 30′", {"point": "2", "point_minute": "30"}
        )
        point_batch["assertions"][0].update(
            quantity="eclipse_extent",
            role="historical_prediction",
            subject="Sun and Moon",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
        )
        point_row = self.module().compile_catalogue([point_batch], {10: point_text}, point_spans)[
            "assertions"
        ][0]
        with self.assertRaises(ValueError):
            public_assertion(point_row)

    def test_queried_native_eclipse_digits_preserve_the_native_unit_without_a_scalar(self):
        from src.public_assertions import public_assertion

        literal = "22 | 2 [?]"
        text, spans, batch = self.explicit_clock_case(literal, {})
        batch["assertions"][0].update(
            quantity="eclipse_extent",
            role="historical_input",
            subject="Sun and Moon",
            reference=None,
            direction=None,
            source_extent_unit="digit",
            flags=[
                "not_an_additional_raw_reading",
                "not_an_observing_clock",
                "source_notation_unresolved",
            ],
            unit_basis="Queried minute in a shared native Digit./minute table",
        )
        try:
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            out = public_assertion(row)
        except ValueError as exc:
            self.fail(
                f"A queried native digit reading must remain unresolved in its own unit: {exc}"
            )
        self.assertEqual(row["source_expression"], literal)
        self.assertEqual(row["components"], {})
        self.assertEqual(out["normalized"]["unit"], "source_eclipse_digit")
        self.assertEqual(out["normalized"]["status"], "unsupported")
        self.assertIsNone(out["normalized"]["magnitude"])
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["components"] = {"digit": "22", "digit_minute": "2"}
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, spans)
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["subject"] = "Mars"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_noncanonical_degree_within_sign_is_preserved_without_scalar(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "3 | 41° 42′ 36″",
            {"sign_count": "3", "degree": "41", "arcminute": "42", "arcsecond": "36"},
        )
        batch["assertions"][0].update(
            quantity="calculation_angle",
            role="historical_input",
            subject="Moon calculation",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        norm = public_assertion(row)["normalized"]
        self.assertEqual(norm["status"], "unsupported")
        self.assertEqual(norm["normalization_issue"], "degree_outside_sign")
        self.assertEqual(norm["source_components"], ["3", "41", "42", "36"])
        self.assertIsNone(norm["magnitude"])
        bad = copy.deepcopy(row)
        bad["normalized"].pop("normalization_issue")
        bad["normalized"].pop("source_components")
        bad["normalized"].update(status="exact", magnitude="474156", magnitude_degrees="39513/300")
        with self.assertRaises(ValueError):
            public_assertion(bad)
        self.assertEqual(
            self.module().normalize_quantity(
                dict(quantity="calculation_angle", components={"sign_count": "3", "degree": "30"})
            )["status"],
            "exact",
        )

    def test_worded_sign_and_half_keeps_relative_angle(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("a sign and a half", {"sign_count": "1 1/2"})
        batch["assertions"][0].update(
            quantity="calculation_angle",
            role="historical_input",
            subject="Moon calculation",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
            source_word_numbers={"a sign and a half": "1 1/2"},
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(public_assertion(row)["normalized"]["magnitude_degrees"], "45")

    def test_lunar_epoch_components_do_not_infer_units(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "7 | 6 | 14 | 57",
            {"component_1": "7", "component_2": "6", "component_3": "14", "component_4": "57"},
        )
        batch["assertions"][0].update(
            quantity="calculation_angle",
            role="historical_input",
            subject="Moon calculation",
            reference=None,
            direction=None,
            source_angular_units_unresolved=True,
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        norm = public_assertion(row)["normalized"]
        self.assertIsNone(norm["magnitude"])
        self.assertEqual(norm["source_components"], ["7", "6", "14", "57"])

    def test_unknown_printed_page_retains_explicit_pdf_locator(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("1°", {"degree": "1"})
        batch["assertions"][0].update(
            quantity="altitude", role="recorded_reading", subject="Mars", reference=None
        )
        locator = dict(source_pdf_page=127, printed_page_label="[?]2", later_hand_page_label="115")
        batch["basis"].update(
            kind="final_edition_review", printed_page=None, source_page_locator=locator
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertIsNone(out["printed_page"])
        self.assertEqual(out["source_page_locator"], locator)
        self.assertEqual(
            public_assertion(dict(row, source_fragment_pages=[None]))["source_fragment_pages"],
            [None],
        )
        ranged = dict(
            row,
            source_page_locator=dict(
                source_pdf_pages=[133, 134], printed_page_label=None, later_hand_page_label=None
            ),
        )
        self.assertEqual(
            public_assertion(ranged)["source_page_locator"]["source_pdf_pages"], [133, 134]
        )
        for pages in ([134, 133], [133, 135], [133], [True, 2]):
            bad_range = copy.deepcopy(ranged)
            bad_range["source_page_locator"]["source_pdf_pages"] = pages
            with self.assertRaises(ValueError):
                public_assertion(bad_range)
        for value in (0, True, "127"):
            bad = copy.deepcopy(row)
            bad["source_page_locator"]["source_pdf_page"] = value
            with self.assertRaises(ValueError):
                public_assertion(bad)
        bad = dict(row)
        bad.pop("source_page_locator")
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_scan_locator_follows_the_quantity_page_segment(self):
        text, spans, batch = self.explicit_clock_case("1°", {"degree": "1"})
        text += "2°\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        batch.update(edition_sha256=sha, line_end=2)
        batch["interval_sha256"] = hashlib.sha256(text.rstrip("\n").encode()).hexdigest()
        spans[0]["edition_sha256"] = sha
        spans.append(dict(spans[0], id="s2", line_start=2, line_end=2))
        batch["span_decisions"].append(dict(batch["span_decisions"][0], span_id="s2"))
        original = batch["assertions"][0]
        original.update(quantity="altitude", role="recorded_reading", subject="Sun")
        batch["assertions"].append(
            dict(
                original,
                key="second",
                line=2,
                span_id="s2",
                source_expression="2°",
                components={"degree": "2"},
            )
        )
        first_locator = dict(source_pdf_page=41, printed_page_label="1", later_hand_page_label=None)
        batch["basis"].update(
            kind="final_edition_review",
            source_page_locator=first_locator,
            page_segments=[
                dict(line_start=1, line_end=1, printed_page=1, pdf_page=41, witness_sha256=sha),
                dict(line_start=2, line_end=2, printed_page=2, pdf_page=42, witness_sha256=sha),
            ],
        )
        rows = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"]
        byline = {r["line"]: r for r in rows}
        self.assertEqual(byline[1]["source_page_locator"], first_locator)
        self.assertEqual(
            byline[2]["source_page_locator"],
            dict(source_pdf_page=42, printed_page_label="2", later_hand_page_label=None),
        )
        batch["basis"]["page_segments"][1]["pdf_page"] = None
        rows = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"]
        self.assertNotIn("source_page_locator", next(r for r in rows if r["line"] == 2))

    def test_tenth_sexagesimal_place_survives_exact_conversion(self):
        from fractions import Fraction
        from src.public_assertions import public_assertion

        parts = {"degree": "1", "arcsexagesimal_tenth": "1"}
        text, spans, batch = self.explicit_clock_case("1 | 1", parts)
        batch["assertions"][0].update(quantity="angular_daily_motion", role="historical_input")
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(Fraction(out["normalized"]["magnitude"]), 3600 + Fraction(1, 60**8))
        self.assertEqual(out["normalized"]["least_component_unit"], "arcsexagesimal_tenth")

    def test_observed_eclipse_table_digits_retain_native_fractions(self):
        from src.public_assertions import public_assertion

        for expression, parts, exact in (
            ("9 45", {"point": "9", "point_minute": "45"}, "39/4"),
            ("2½", {"point": "2 1/2"}, "5/2"),
        ):
            text, spans, batch = self.explicit_clock_case(expression, parts)
            batch["assertions"][0].update(
                quantity="eclipse_extent",
                role="recorded_reading",
                subject="Moon",
                reference=None,
                direction=None,
                flags=[
                    "source_visual_estimate",
                    "not_an_additional_raw_reading",
                    "not_an_observing_clock",
                ],
                unit_basis="DIGI header gives obscuration digits and sexagesimal minutes.",
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["magnitude"], exact)
            self.assertEqual(out["normalized"]["unit"], "source_eclipse_point")
            self.assertIsNone(out["normalized"]["magnitude_degrees"])
            for change in (dict(model_name="Alphonsine"), dict(flags=[])):
                with self.assertRaises(ValueError):
                    public_assertion(dict(row, **change))

    def test_written_eighth_part_angular_difference(self):
        text, spans, batch = self.explicit_clock_case("eighth part", {"arcminute": "1/8"})
        batch["assertions"][0].update(
            quantity="longitude_difference",
            source_word_numbers={"eighth part": "1/8"},
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(row["normalized"]["magnitude"], "15/2")

    def test_written_historical_mile_counts(self):
        from src.public_assertions import public_assertion

        for word, value in (("seventy thousand", "70000"), ("thirty-five thousand", "35000")):
            text, spans, batch = self.explicit_clock_case(word + " miles", {"scalar": value})
            batch["assertions"][0].update(
                quantity="distance_in_ordinary_miles",
                role="historical_input",
                subject="Sun calculation",
                reference=None,
                direction=None,
                source_word_numbers={word: value},
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            self.assertEqual(public_assertion(row)["normalized"]["magnitude"], value)

    def test_historical_mile_distances_keep_native_units(self):
        from src.public_assertions import public_assertion

        for quantity, unit in (
            ("distance_in_german_miles", "source_german_mile"),
            ("distance_in_ordinary_miles", "source_ordinary_mile"),
        ):
            text, spans, batch = self.explicit_clock_case("41½ miles", {"scalar": "41 1/2"})
            batch["assertions"][0].update(
                quantity=quantity,
                role="historical_input",
                subject="Sun calculation",
                reference=None,
                direction=None,
                flags=["not_an_additional_raw_reading"],
                unit_basis="Source explicitly states the historical mile convention.",
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["magnitude"], "83/2")
            self.assertEqual(out["normalized"]["unit"], unit)
            self.assertIsNone(out["normalized"]["magnitude_degrees"])
            for change in ({"unit": "arcsecond"}, {"magnitude": "42"}):
                bad = copy.deepcopy(row)
                bad["normalized"].update(change)
                with self.assertRaises(ValueError):
                    public_assertion(bad)
            for parts in ({"degree": "41 1/2"}, {"scalar": "-1"}):
                with self.assertRaises(ValueError):
                    self.module().normalize_quantity(dict(quantity=quantity, components=parts))

    def test_daily_motion_with_more_than_sixty_arcminutes(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "61′ 21″", dict(arcminute="61", arcsecond="21")
        )
        batch["assertions"][0].update(
            quantity="angular_daily_motion",
            role="calculation_intermediate",
            subject="Sun",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        norm = public_assertion(row)["normalized"]
        self.assertEqual(norm["magnitude"], "3681")
        self.assertEqual(norm["unit"], "arcsecond_per_source_day")
        self.assertIsNone(norm["magnitude_degrees"])
        for parts in ({"degree": "1", "arcminute": "61"}, {"arcminute": "61", "arcsecond": "60"}):
            with self.assertRaises(ValueError):
                self.module().normalize_quantity(
                    dict(quantity="angular_daily_motion", components=parts)
                )

    def test_literal_table_spans_can_overlap(self):
        from src.assembly import literal_intervals

        self.assertEqual(literal_intervals("| 0 | 0 | 0 |", "0 | 0"), [(2, 7), (6, 11)])
        self.assertEqual(literal_intervals("1400 400", "400"), [(5, 8)])

    def test_elapsed_argument_can_be_sixty_minutes(self):
        row = dict(quantity="clock_elapsed_time", components={"minute": "60"})
        self.assertEqual(self.module().normalize_quantity(row)["magnitude"], "3600")
        for components in ({"hour": "1", "minute": "60"}, {"minute": "1", "second": "60"}):
            with self.assertRaises(ValueError):
                self.module().normalize_quantity(dict(row, components=components))
        with self.assertRaises(ValueError):
            self.module().normalize_quantity(dict(row, quantity="recorded_clock"))

    def test_table_columns_stop_before_editorial_correction(self):
        text, spans, batch = self.explicit_clock_case(
            "| 8 | 19 | 34 [recte: 43] |", dict(arcminute="19", arcsecond="34")
        )
        batch["assertions"][0].update(
            quantity="longitude_difference",
            role="calculation_intermediate",
            subject="mean Sun",
            reference=None,
            direction=None,
            source_expression="19 | 34",
            source_columns=[2, 3],
            column=None,
            flags=["not_an_additional_raw_reading"],
        )
        out = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(out["normalized"]["magnitude"], "1174")
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["source_expression"] = "19"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_reviewed_columns_without_outer_table_pipes(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "365 | 5 | 48 | 45", dict(day="365", hour="5", minute="48", second="45")
        )
        batch["assertions"][0].update(
            quantity="clock_elapsed_time",
            role="calculation_intermediate",
            subject="Sun",
            reference=None,
            direction=None,
            source_columns=[1, 2, 3, 4],
            column=None,
            flags=["not_an_additional_raw_reading"],
        )
        out = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(public_assertion(out)["normalized"]["magnitude"], "31556925")
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["source_columns"] = [1, 2, 3]
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_printed_part_minute_word_and_letter_labels(self):
        from src.normalization import interpret_part_minute_notation
        from src.public_assertions import public_assertion

        for expression, components in [
            ("P. 17. l. 7. ll. 2.", dict(degree="17", arcminute="7", arcsecond="2")),
            ("part. 49. minut. 24½.", dict(degree="49", arcminute="24 1/2")),
            ("l. 2. ll. 58.", dict(arcminute="2", arcsecond="58")),
            ("min. 1¼.", dict(arcminute="1 1/4")),
        ]:
            text, spans, batch = self.explicit_clock_case(expression, components)
            batch["assertions"][0].update(
                source_unit_notation="roman_sexagesimal_places",
                quantity="calculation_angle",
                role="calculation_intermediate",
                subject="Sun",
                reference=None,
                direction=None,
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            self.assertEqual(interpret_part_minute_notation(row)[1], components)
            self.assertEqual(public_assertion(row)["normalized"], row["normalized"])

    def test_explicit_roman_sexagesimal_places(self):
        from src.normalization import interpret_part_minute_notation
        from src.public_assertions import public_assertion

        cases = [
            (
                "Sign 11, P. 29. 1. 44. 11. 49. 111. 40. 1111. 42. V. 53. V1. 38. V11. 30",
                "calculation_angle",
                dict(
                    sign_count="11",
                    degree="29",
                    arcminute="44",
                    arcsecond="49",
                    arcsexagesimal_third="40",
                    arcsexagesimal_fourth="42",
                    arcsexagesimal_fifth="53",
                    arcsexagesimal_sixth="38",
                    arcsexagesimal_seventh="30",
                ),
            ),
            ("11. 13. 111. 16½", "clock_elapsed_time", dict(second="13", time_third="16 1/2")),
        ]
        for expression, quantity, components in cases:
            text, spans, batch = self.explicit_clock_case(expression, components)
            batch["assertions"][0].update(
                source_unit_notation="roman_sexagesimal_places",
                quantity=quantity,
                role="calculation_intermediate",
                subject="Sun",
                reference=None,
                direction=None,
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            self.assertEqual(public_assertion(row)["normalized"], row["normalized"])
            self.assertEqual(interpret_part_minute_notation(row)[1], components)
            bad = dict(row, source_expression=expression + " 99")
            with self.assertRaises(ValueError):
                interpret_part_minute_notation(bad)
            bad = dict(row, source_expression=expression.replace("111.", "11.", 1))
            with self.assertRaises(ValueError):
                interpret_part_minute_notation(bad)

    def test_tabular_terminal_half_requires_a_complete_selected_application(self):
        from src.normalization import interpret_part_minute_notation, normalize_quantity

        common = dict(
            quantity="calculation_angle",
            role="historical_input",
            source_unit_notation="tabular_dms_terminal_half",
            source_tabular_application="hours_by_arcminutes",
        )
        for expression, seconds, magnitude in (
            ("0 0 2.", "2 1/2", "5/2"),
            ("2 25 2.", "2 1/2", "17405/2"),
            ("0 59 59.", "59 1/2", "7199/2"),
            ("0 0 2", "2", "2"),
        ):
            with self.subTest(expression=expression):
                row = dict(common, source_expression=expression)
                canonical, components = interpret_part_minute_notation(row)
                self.assertEqual(components["arcsecond"], seconds)
                self.assertIn("°", canonical)
                self.assertEqual(
                    normalize_quantity(dict(row, components=components))["magnitude"], magnitude
                )
        for expression in (
            "0 0",
            "0 0 2. 3",
            "0. 0 2",
            "0 0 2..",
            "0 0 [numeral: ?]",
            "0 0 -2.",
            "0° 0′ 2″",
            "0 0 2.5",
            "0 0 .5",
            "0 0 60.",
        ):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                row = dict(common, source_expression=expression)
                _, components = interpret_part_minute_notation(row)
                normalize_quantity(dict(row, components=components))
        for change in (
            {"source_tabular_application": None},
            {"source_tabular_application": "hours_by_degrees"},
            {"quantity": "recorded_clock"},
            {"role": "recorded_reading"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                interpret_part_minute_notation(dict(common, source_expression="0 0 2.", **change))

    def test_tabular_terminal_half_materializes_and_exports_its_application(self):
        from src.public_assertions import public_assertion
        from src.review_preparation import materialize_review

        text, spans, batch = self.explicit_clock_case("0 0 2.", {})
        selection = dict(batch["assertions"][0])
        selection.pop("components")
        selection.update(
            quantity="calculation_angle",
            role="historical_input",
            subject="planetary motion calculation",
            reference=None,
            direction=None,
            source_unit_notation="tabular_dms_terminal_half",
            source_tabular_application="hours_by_arcminutes",
            flags=["not_an_additional_raw_reading"],
        )
        batch["assertions"] = []
        batch["cell_groups"] = [dict(cells=[dict(selection, column=None)])]
        prepared = materialize_review(batch, text, spans)
        row = self.module().compile_catalogue([prepared], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(out["source_tabular_application"], "hours_by_arcminutes")
        self.assertEqual(out["source_unit_notation"], "tabular_dms_terminal_half")
        self.assertEqual(out["normalized"]["magnitude"], "5/2")
        alternative = dict(
            row,
            role="editorial_variant",
            variant_of_id="assertion-v10-0123456789abcdefabcd",
            flags=["not_an_additional_raw_reading", "alternative_suggestion_not_applied"],
        )
        self.assertEqual(public_assertion(alternative)["normalized"]["magnitude"], "5/2")
        with self.assertRaises(ValueError):
            public_assertion(dict(alternative, variant_of_id=None))
        bad = copy.deepcopy(row)
        bad["components"]["arcsecond"] = "2"
        bad["normalized"] = self.module().normalize_quantity(bad)
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_paired_native_tenths_are_exact_and_keep_the_source_second_basis(self):
        from src.public_assertions import public_assertion

        for literal, value in (
            ("48 5", "97/2"),
            ("48.5", "97/2"),
            ("38. 9", "389/10"),
            ("48.,2", "241/5"),
            ("10: 5", "21/2"),
            ("0. 0", "0"),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, {"scalar": value})
                row = batch["assertions"][0]
                row.update(
                    quantity="source_scalar",
                    role="historical_input",
                    subject="planetary motion calculation",
                    reference=None,
                    source_parameter_kind="sine_increment_per_source_second",
                    source_scalar_scale="10000000",
                    source_unit_notation="paired_decimal_tenths",
                    flags=["not_an_additional_raw_reading"],
                )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                out = public_assertion(compiled)
                self.assertEqual(out["normalized"]["magnitude"], value)
                self.assertEqual(out["normalized"]["unit"], "source_scalar")
                self.assertEqual(out["source_parameter_kind"], "sine_increment_per_source_second")
                self.assertEqual(out["source_unit_notation"], "paired_decimal_tenths")
                self.assertIsNone(out["normalized"]["magnitude_degrees"])
                bad = copy.deepcopy(compiled)
                bad["components"]["scalar"] = "485"
                bad["normalized"] = self.module().normalize_quantity(bad)
                with self.assertRaises(ValueError):
                    public_assertion(bad)

    def test_paired_native_tenths_reject_partial_or_misclassified_expressions(self):
        from src.normalization import interpret_part_minute_notation

        common = dict(
            quantity="source_scalar",
            role="historical_input",
            source_parameter_kind="sine_increment_per_source_second",
            source_unit_notation="paired_decimal_tenths",
        )
        for literal in (
            "48",
            "48.50",
            "48 50",
            "48.5 6",
            "48..5",
            "48. 5.",
            "48 [numeral: ?]",
            "-48.5",
            "48° 5′",
        ):
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                interpret_part_minute_notation(dict(common, source_expression=literal))
        for change in (
            {"quantity": "calculation_angle"},
            {"role": "recorded_reading"},
            {"source_parameter_kind": "scaled_sine"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                interpret_part_minute_notation(dict(common, source_expression="48.5", **change))

    def test_unread_native_trigonometric_fields_retain_scale_without_a_scalar(self):
        from src.public_assertions import public_assertion

        for literal, kind in (
            ("234001[?]", "scaled_sine"),
            ("649890[numeral: ?]", "scaled_sine"),
            ("6[numeral: ?]7199[numeral: ?]", "scaled_sine"),
            ("3[numeral: ?].2", "sine_increment_per_source_second"),
            ("457", "sine_increment_per_source_second"),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, {})
                batch["assertions"][0].update(
                    quantity="source_scalar",
                    role="historical_input",
                    subject="planetary motion calculation",
                    reference=None,
                    source_parameter_kind=kind,
                    source_scalar_scale="10000000",
                    flags=["not_an_additional_raw_reading", "source_notation_unresolved"],
                )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                out = public_assertion(compiled)
                self.assertIsNone(out["normalized"]["magnitude"])
                self.assertEqual(out["normalized"]["unit"], "source_scalar")
                self.assertEqual(out["source_scalar_scale"], "10000000")
                for change in (
                    {"source_scalar_scale": "0"},
                    {"components": {"scalar": "1"}},
                    {"role": "recorded_reading"},
                    {"reference": "Sun"},
                ):
                    with self.subTest(change=change), self.assertRaises(ValueError):
                        changed = dict(compiled, **change)
                        changed["normalized"] = self.module().normalize_quantity(changed)
                        public_assertion(changed)

    def test_explicit_latitude_terminal_point_adds_thirty_arcseconds(self):
        from src.public_assertions import public_assertion

        for literal, components, magnitude, direction, signed in (
            (
                "30° 33′.",
                {"degree": "30", "arcminute": "33", "arcsecond": "30"},
                "110010",
                "north",
                "110010",
            ),
            (
                "0° 0′.",
                {"degree": "0", "arcminute": "0", "arcsecond": "30"},
                "30",
                "south",
                "-30",
            ),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, components)
                batch["assertions"][0].update(
                    quantity="ecliptic_latitude",
                    subject="Aldebaran",
                    reference=None,
                    direction=direction,
                    role="historical_input",
                    source_unit_notation="dms_latitude_terminal_half_minute",
                    flags=["not_an_additional_raw_reading"],
                )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                row = public_assertion(compiled)
                self.assertEqual(row["normalized"]["magnitude"], magnitude)
                self.assertEqual(row["normalized"]["signed_magnitude"], signed)
                self.assertEqual(row["source_unit_notation"], "dms_latitude_terminal_half_minute")
                bad = copy.deepcopy(compiled)
                bad["components"]["arcsecond"] = "0"
                bad["normalized"] = self.module().normalize_quantity(bad)
                with self.assertRaises(ValueError):
                    public_assertion(bad)

    def test_latitude_terminal_point_requires_complete_scoped_notation(self):
        from src.normalization import interpret_part_minute_notation

        common = dict(
            quantity="ecliptic_latitude",
            role="historical_input",
            reference=None,
            source_unit_notation="dms_latitude_terminal_half_minute",
            flags=["not_an_additional_raw_reading"],
        )
        for literal in (
            "30° 33′",
            "30° 33′..",
            "30° 33′ 10″.",
            "30 33.",
            "30.33",
            "30° 60′.",
            "90° 0′.",
            "30° 3[?]′.",
            "-30° 33′.",
        ):
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                interpret_part_minute_notation(dict(common, source_expression=literal))
        for change in (
            {"quantity": "ecliptic_longitude"},
            {"quantity": "declination"},
            {"role": "recorded_reading"},
            {"flags": []},
            {"reference": "Sun"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                row = dict(common, source_expression="30° 33′.")
                row.update(change)
                interpret_part_minute_notation(row)

    def test_rising_and_oblique_coordinates_use_shared_angular_units(self):
        from src.public_assertions import public_assertion

        for quantity in (
            "rising_amplitude",
            "ascensional_difference",
            "oblique_ascension",
            "oblique_descension",
        ):
            with self.subTest(quantity=quantity):
                text, spans, batch = self.explicit_clock_case(
                    "1° 30′", {"degree": "1", "arcminute": "30"}
                )
                batch["assertions"][0].update(
                    quantity=quantity,
                    subject="fixed star calculation",
                    reference=None,
                    role="historical_input",
                    flags=["not_an_additional_raw_reading"],
                )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                normalized = public_assertion(compiled)["normalized"]
                self.assertEqual(normalized["status"], "exact")
                self.assertEqual(normalized["magnitude"], "5400")
                self.assertEqual(normalized["unit"], "arcsecond")
                self.assertEqual(normalized["magnitude_degrees"], "3/2")

    def test_paired_copernican_tychonic_solar_predictions_retain_attribution(self):
        from src.public_assertions import public_assertion

        for model in ("Copernicus", "Tycho Brahe"):
            with self.subTest(model=model):
                text, spans, batch = self.explicit_clock_case(
                    "1° 30′ ♈", {"degree": "1", "arcminute": "30"}
                )
                batch["assertions"][0].update(
                    quantity="ecliptic_longitude",
                    subject="Sun",
                    reference=None,
                    role="historical_prediction",
                    model_name=model,
                    zodiac_sign="Aries",
                    flags=["not_an_additional_raw_reading"],
                )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                row = public_assertion(compiled)
                self.assertEqual(row["model_name"], model)
                self.assertEqual(row["normalized"]["magnitude"], "5400")
                self.assertEqual(row["normalized"]["zodiac_longitude_degrees"], "3/2")
                for unsupported in (None, "unspecified"):
                    with self.subTest(unsupported=unsupported), self.assertRaises(ValueError):
                        public_assertion(dict(compiled, model_name=unsupported))

    def test_seventh_sexagesimal_mark_binds_to_its_printed_place(self):
        from src.public_assertions import public_assertion

        literal = "2′ 58″ 40‴ 16⁗ 51^V^ 25^VI^ 2^VII^"
        components = {
            "arcminute": "2",
            "arcsecond": "58",
            "arcsexagesimal_third": "40",
            "arcsexagesimal_fourth": "16",
            "arcsexagesimal_fifth": "51",
            "arcsexagesimal_sixth": "25",
            "arcsexagesimal_seventh": "2",
        }
        text, spans, batch = self.explicit_clock_case(literal, components)
        batch["assertions"][0].update(
            quantity="angular_daily_motion",
            subject="planetary motion calculation",
            role="historical_input",
            reference=None,
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["least_component_unit"], "arcsexagesimal_seventh")
        self.assertEqual(out["normalized"]["unit"], "arcsecond_per_source_day")
        incorrect = copy.deepcopy(batch)
        wrong = incorrect["assertions"][0]["components"]
        wrong["arcsexagesimal_eighth"] = wrong.pop("arcsexagesimal_seventh")
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([incorrect], {10: text}, spans)

    def test_tychonic_eclipse_parameters_keep_prediction_attribution(self):
        from src.public_assertions import public_assertion

        cases = (
            (
                "2° 49′ ♍",
                {"degree": "2", "arcminute": "49"},
                {
                    "quantity": "ecliptic_longitude",
                    "subject": "lunar ascending node",
                    "zodiac_sign": "Virgo",
                },
            ),
            (
                "15^h^ 47^m^",
                {"hour": "15", "minute": "47"},
                {
                    "quantity": "calculation_epoch",
                    "subject": "Moon",
                    "source_eclipse_phase": "middle",
                    "source_time_scale": "equal",
                },
            ),
            (
                "4 digits 7′",
                {"digit": "4", "digit_minute": "7"},
                {
                    "quantity": "eclipse_extent",
                    "subject": "Moon",
                    "source_extent_unit": "digit",
                },
            ),
        )
        for literal, components, fields in cases:
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, components)
                batch["assertions"][0].update(
                    **fields,
                    reference=None,
                    role="historical_prediction",
                    model_name="Tycho Brahe",
                    flags=[
                        "not_an_additional_raw_reading",
                        "not_an_observing_clock",
                        "absolute_time_unestablished",
                    ],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                projected = public_assertion(row)
                self.assertEqual(projected["role"], "historical_prediction")
                self.assertEqual(projected["model_name"], "Tycho Brahe")
                self.assertEqual(projected["normalized"], row["normalized"])
                with self.assertRaises(ValueError):
                    public_assertion(dict(row, model_name="unspecified"))

    def test_stadius_solar_node_and_daily_motion_predictions_keep_attribution(self):
        from src.public_assertions import public_assertion

        for subject, quantity, literal, parts, sign in (
            (
                "Sun",
                "ecliptic_longitude",
                "12° 0′ ♉",
                {"degree": "12", "arcminute": "0"},
                "Taurus",
            ),
            (
                "lunar ascending node",
                "ecliptic_longitude",
                "14° 41′ ♋",
                {"degree": "14", "arcminute": "41"},
                "Cancer",
            ),
            ("Venus", "angular_daily_motion", "3° 13′", {"degree": "3", "arcminute": "13"}, None),
            ("lunar ascending node", "angular_daily_motion", "3′", {"arcminute": "3"}, None),
        ):
            with self.subTest(subject=subject, quantity=quantity):
                text, spans, batch = self.explicit_clock_case(literal, parts)
                batch["assertions"][0].update(
                    quantity=quantity,
                    subject=subject,
                    reference=None,
                    role="historical_prediction",
                    model_name="Stadius",
                    flags=["not_an_additional_raw_reading"],
                )
                if sign:
                    batch["assertions"][0]["zodiac_sign"] = sign
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                row = public_assertion(compiled)
                self.assertEqual(row["model_name"], "Stadius")
                self.assertEqual(row["subject"], subject)
                self.assertEqual(row["normalized"]["status"], "exact")
                self.assertEqual(compiled["source_expression"], literal)
                bad = copy.deepcopy(compiled)
                bad["flags"] = []
                with self.assertRaises(ValueError):
                    public_assertion(bad)

    def test_named_sign_endpoints_and_noncanonical_source_components(self):
        from src.public_assertions import public_assertion

        for literal, sign, full_longitude in (
            ("30° 0′ ♈", "Aries", "30"),
            ("30° 0′ ♓", "Pisces", "360"),
        ):
            with self.subTest(endpoint=literal):
                text, spans, batch = self.explicit_clock_case(
                    literal, {"degree": "30", "arcminute": "0"}
                )
                batch["assertions"][0].update(
                    quantity="ecliptic_longitude",
                    subject="ecliptic point",
                    reference=None,
                    role="historical_input",
                    zodiac_sign=sign,
                    flags=["not_an_additional_raw_reading"],
                )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                norm = public_assertion(compiled)["normalized"]
                self.assertEqual(norm["status"], "exact")
                self.assertEqual(norm["magnitude_degrees"], "30")
                self.assertEqual(norm["zodiac_longitude_degrees"], full_longitude)
                self.assertEqual(compiled["source_expression"], literal)
        for literal, parts in (
            ("37° ♎", {"degree": "37"}),
            ("30° 0′ 1″ ♎", {"degree": "30", "arcminute": "0", "arcsecond": "1"}),
        ):
            with self.subTest(noncanonical=literal):
                text, spans, batch = self.explicit_clock_case(literal, parts)
                batch["assertions"][0].update(
                    quantity="ecliptic_longitude",
                    subject="ecliptic point",
                    reference=None,
                    role="historical_input",
                    zodiac_sign="Libra",
                    flags=["not_an_additional_raw_reading"],
                )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                norm = public_assertion(compiled)["normalized"]
                self.assertEqual(compiled["components"], parts)
                self.assertEqual(norm["status"], "unsupported")
                self.assertEqual(norm["normalization_issue"], "degree_outside_sign")
                self.assertEqual(norm["zodiac_sign"], "Libra")
                self.assertIsNone(norm["magnitude"])
                self.assertIsNone(norm["magnitude_degrees"])
                self.assertIsNone(norm.get("zodiac_longitude_degrees"))
                bad = copy.deepcopy(compiled)
                bad["normalized"].update(status="exact", magnitude="133200", magnitude_degrees="37")
                with self.assertRaises(ValueError):
                    public_assertion(bad)
                with self.assertRaises(ValueError):
                    self.module().zodiac_arithmetic_values([compiled["normalized"]])

    def test_queried_calculation_interval_preserves_literal_without_a_scalar(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("3^m^ 4[?]^s^", {})
        batch["assertions"][0].update(
            quantity="clock_elapsed_time",
            subject="Sun",
            reference=None,
            role="historical_input",
            flags=[
                "source_notation_unresolved",
                "not_an_observing_clock",
                "not_an_additional_raw_reading",
            ],
        )
        compiled = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        norm = public_assertion(compiled)["normalized"]
        self.assertEqual(compiled["source_expression"], "3^m^ 4[?]^s^")
        self.assertEqual(norm["unit"], "second_of_time")
        self.assertEqual(norm["normalization_issue"], "source_notation_unresolved")
        self.assertIsNone(norm["magnitude"])
        bad = copy.deepcopy(compiled)
        bad["normalized"].update(status="exact", magnitude="184")
        with self.assertRaises(ValueError):
            public_assertion(bad)
        bad = copy.deepcopy(compiled)
        bad["flags"].remove("not_an_observing_clock")
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_historical_body_period_keeps_unresolved_denominator_unit(self):
        from src.public_assertions import public_assertion

        for subject in (
            "Sun",
            "Moon",
            "Mercury",
            "Venus",
            "Earth",
            "Mars",
            "Jupiter",
            "Saturn",
            *(f"satellite {label} of Jupiter" for label in ("I", "II", "III", "IV")),
        ):
            with self.subTest(subject=subject):
                text, spans, batch = self.explicit_clock_case("1 | 769/1000", {})
                row = batch["assertions"][0]
                row.update(
                    quantity="clock_elapsed_time",
                    subject=subject,
                    reference=None,
                    role="historical_input",
                    flags=[
                        "source_notation_unresolved",
                        "not_an_observing_clock",
                        "not_an_additional_raw_reading",
                    ],
                )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                out = public_assertion(compiled)
                self.assertEqual(compiled["source_expression"], "1 | 769/1000")
                self.assertEqual(out["normalized"]["status"], "unsupported")
                self.assertEqual(out["normalized"]["unit"], "second_of_time")
                self.assertIsNone(out["normalized"]["magnitude"])
                for guessed in (
                    {"day": "1", "hour": "769/1000"},
                    {"day": "1 769/1000"},
                ):
                    bad = copy.deepcopy(batch)
                    bad["assertions"][0]["components"] = guessed
                    with self.subTest(guessed=guessed), self.assertRaises(ValueError):
                        self.module().compile_catalogue([bad], {10: text}, spans)

    def test_ecliptic_point_calculation_retains_its_own_subject(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "1° 30′ ♊", {"degree": "1", "arcminute": "30"}
        )
        batch["assertions"][0].update(
            quantity="ecliptic_longitude",
            subject="ecliptic point",
            reference=None,
            role="historical_input",
            zodiac_sign="Gemini",
            flags=["not_an_additional_raw_reading"],
        )
        compiled = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        row = public_assertion(compiled)
        self.assertEqual(row["subject"], "ecliptic point")
        self.assertEqual(row["normalized"]["magnitude"], "5400")
        self.assertEqual(row["normalized"]["zodiac_longitude_degrees"], "123/2")

    def test_native_year_count_accepts_written_forty_without_day_conversion(self):
        from src.public_assertions import public_assertion

        for literal, value in (
            ("forty", "40"),
            ("nine hundred", "900"),
            ("forty-nine thousand", "49000"),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, {"scalar": value})
                batch["assertions"][0].update(
                    quantity="source_scalar",
                    subject="fixed star calculation",
                    reference=None,
                    role="historical_input",
                    source_parameter_kind="source_year_count",
                    source_word_numbers={literal: value},
                    flags=["not_an_additional_raw_reading"],
                )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                row = public_assertion(compiled)
                self.assertEqual(compiled["source_expression"], literal)
                self.assertEqual(row["normalized"]["magnitude"], value)
                self.assertEqual(row["normalized"]["unit"], "source_scalar")
                self.assertEqual(row["source_parameter_kind"], "source_year_count")

    def test_partial_angle_components_keep_their_units_without_a_complete_scalar(self):
        from src.public_assertions import public_assertion

        for literal, components in (
            ("28°", {"degree": "28"}),
            ("27′ 33″", {"arcminute": "27", "arcsecond": "33"}),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, components)
                batch["assertions"][0].update(
                    quantity="calculation_angle",
                    subject="planetary motion calculation",
                    role="historical_input",
                    reference=None,
                    incomplete=True,
                    flags=["not_an_additional_raw_reading", "source_quantity_fragment"],
                )
                compiled = self.module().compile_catalogue([batch], {10: text}, spans)[
                    "assertions"
                ][0]
                row = public_assertion(compiled)
                self.assertEqual(compiled["components"], components)
                self.assertEqual(row["normalized"]["status"], "incomplete")
                self.assertEqual(row["normalized"]["unit"], "arcsecond")
                self.assertIsNone(row["normalized"]["magnitude"])
                self.assertIn("source_quantity_fragment", row["flags"])

    def test_elapsed_clock_thirds_are_not_day_thirds(self):
        from fractions import Fraction
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "365 6 9′ 26″ 43½‴",
            dict(day="365", hour="6", minute="9", second="26", time_third="43 1/2"),
        )
        batch["assertions"][0].update(
            quantity="clock_elapsed_time",
            role="calculation_intermediate",
            subject="Sun",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        expected = Fraction(365 * 86400 + 6 * 3600 + 9 * 60 + 26) + Fraction(87, 120)
        self.assertEqual(out["normalized"]["magnitude"], str(expected))
        self.assertEqual(out["normalized"]["least_component_unit"], "time_third")
        bad = copy.deepcopy(batch)
        parts = bad["assertions"][0]["components"]
        parts["day_third"] = parts.pop("time_third")
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_duration_fourths_and_fifths_preserve_exact_time_units(self):
        from fractions import Fraction
        from src.public_assertions import public_assertion

        literal = "365 days, 5^h^ 49^m^ 15^s^ 45‴ 52⁗ 48^v^"
        parts = dict(
            day="365",
            hour="5",
            minute="49",
            second="15",
            time_third="45",
            time_fourth="52",
            time_fifth="48",
        )
        text, spans, batch = self.explicit_clock_case(literal, parts)
        batch["assertions"][0].update(
            quantity="clock_elapsed_time",
            role="historical_input",
            subject="Sun calculation",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        result = public_assertion(row)
        expected = (
            Fraction(365 * 86400 + 5 * 3600 + 49 * 60 + 15)
            + Fraction(45, 60)
            + Fraction(52, 3600)
            + Fraction(48, 216000)
        )
        self.assertEqual(result["normalized"]["magnitude"], str(expected))
        self.assertEqual(result["normalized"]["unit"], "second_of_time")
        self.assertEqual(result["normalized"]["least_component_unit"], "time_fifth")
        self.assertEqual(row["source_expression"], literal)

    def test_fine_day_fractions_keep_the_day_scale_through_sixths(self):
        from fractions import Fraction
        from src.public_assertions import public_assertion

        literal = "29 days and, of a day, 31′ 50″ 7‴ 56⁗ 35^V^ 24^VI^"
        parts = dict(
            day="29",
            day_minute="31",
            day_second="50",
            day_third="7",
            day_fourth="56",
            day_fifth="35",
            day_sixth="24",
        )
        text, spans, batch = self.explicit_clock_case(literal, parts)
        batch["assertions"][0].update(
            quantity="clock_elapsed_time",
            role="historical_input",
            subject="Moon calculation",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        expected = 86400 * (
            Fraction(29)
            + Fraction(31, 60)
            + Fraction(50, 3600)
            + Fraction(7, 216000)
            + Fraction(56, 12960000)
            + Fraction(35, 777600000)
            + Fraction(24, 46656000000)
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], str(expected))
        self.assertEqual(out["normalized"]["unit"], "second_of_time")
        self.assertEqual(out["normalized"]["least_component_unit"], "day_sixth")

    def test_sixth_of_day_mark_cannot_be_relabelled_as_a_fifth(self):
        literal = "1^VI^ of a day"
        text, spans, batch = self.explicit_clock_case(literal, dict(day_sixth="1"))
        batch["assertions"][0].update(
            quantity="clock_elapsed_time",
            role="historical_input",
            subject="Moon calculation",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        self.module().compile_catalogue([batch], {10: text}, spans)
        wrong = copy.deepcopy(batch)
        wrong["assertions"][0]["components"] = dict(day_fifth="1")
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([wrong], {10: text}, spans)

    def test_native_calendar_queries_preserve_spaces_and_unknown_fraction(self):
        from src.public_assertions import public_assertion

        for literal in ("28 [?]", "312[fraction: ?]"):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, {})
                batch["assertions"][0].update(
                    quantity="source_scalar",
                    role="historical_input",
                    subject="calendar calculation",
                    reference=None,
                    direction=None,
                    flags=["not_an_additional_raw_reading", "source_notation_unresolved"],
                    source_parameter_kind="source_year_count",
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                result = public_assertion(row)
                self.assertEqual(row["source_expression"], literal)
                self.assertEqual(result["normalized"]["unit"], "source_scalar")
                self.assertIsNone(result["normalized"]["magnitude"])
                wrong = copy.deepcopy(batch)
                wrong["assertions"][0]["components"] = {"scalar": "28"}
                with self.assertRaises(ValueError):
                    self.module().compile_catalogue([wrong], {10: text}, spans)

    def test_calendar_word_counts_keep_their_native_dimension(self):
        from src.public_assertions import public_assertion

        for literal, expected in (
            ("Twelve", "12"),
            ("Thirteen", "13"),
            ("fifty-one", "51"),
            ("twenty-eight", "28"),
            ("eighth", "8"),
            ("nineteenth", "19"),
            ("I", "1"),
            ("IIII", "4"),
            ("XIIX", "18"),
            ("XXIIX", "28"),
            ("XXIIII", "24"),
            ("XXIX", "29"),
            ("ij", "2"),
            ("xij", "12"),
            ("xviij", "18"),
            ("thirteenth", "13"),
            ("fourteenth", "14"),
            ("twenty-first", "21"),
            ("twenty-seven", "27"),
            ("twenty-ninth", "29"),
            ("a week", "1"),
            ("67th", "67"),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, dict(scalar=expected))
                batch["assertions"][0].update(
                    quantity="source_scalar",
                    role="historical_input",
                    subject="calendar calculation",
                    reference=None,
                    direction=None,
                    flags=["not_an_additional_raw_reading"],
                    source_word_numbers={literal: expected},
                    source_parameter_kind=(
                        "source_week_count" if literal == "a week" else "source_day_count"
                    ),
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                result = public_assertion(row)
                self.assertEqual(result["normalized"]["magnitude"], expected)
                self.assertEqual(result["normalized"]["unit"], "source_scalar")

    def test_duration_day_and_fine_unit_marks_reject_wrong_component_names(self):
        for literal, correct, wrong in (
            ("2 days", dict(day="2"), dict(hour="2")),
            (
                "5⁗ 6^v^",
                dict(time_fourth="5", time_fifth="6"),
                dict(time_third="5", time_fifth="6"),
            ),
            (
                "5^iv^ 6^v^",
                dict(time_fourth="5", time_fifth="6"),
                dict(time_fourth="5", time_third="6"),
            ),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, correct)
                batch["assertions"][0].update(
                    quantity="clock_elapsed_time",
                    role="historical_input",
                    subject="Sun calculation",
                    reference=None,
                    direction=None,
                    flags=["not_an_additional_raw_reading"],
                )
                self.module().compile_catalogue([batch], {10: text}, spans)
                bad = copy.deepcopy(batch)
                bad["assertions"][0]["components"] = wrong
                with self.assertRaises(ValueError):
                    self.module().compile_catalogue([bad], {10: text}, spans)

    def test_fractional_fourths_in_daily_angular_motion(self):
        from fractions import Fraction
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "0° 59′ 8″ 19‴ 43⁗ ⅔",
            {
                "degree": "0",
                "arcminute": "59",
                "arcsecond": "8",
                "arcsexagesimal_third": "19",
                "arcsexagesimal_fourth": "43 2/3",
            },
        )
        batch["assertions"][0].update(
            quantity="angular_daily_motion",
            role="historical_input",
            subject="Sun",
            reference=None,
            direction=None,
            source_component_addends={"arcsexagesimal_fourth": ["43", "2/3"]},
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        want = Fraction(59 * 60 + 8) + Fraction(19, 60) + Fraction(131, 10800)
        self.assertEqual(out["normalized"]["magnitude"], str(want))
        self.assertEqual(out["normalized"]["least_component_unit"], "arcsexagesimal_fourth")
        self.assertEqual(out["normalized"]["unit"], "arcsecond_per_source_day")
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["components"]["arcsexagesimal_third"] = "60"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_clock_across_explicit_table_columns(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "| 1584 | 9 | 21 | 30 |", {"hour": "21", "minute": "30"}
        )
        row = batch["assertions"][0]
        row.update(source_expression="21 | 30", column=None, source_columns=[3, 4])
        out = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(out["normalized"]["magnitude"], "77400")
        self.assertEqual(public_assertion(out)["source_columns"], [3, 4])
        for columns in ([2, 3], [3, 3], [3, 5]):
            bad = copy.deepcopy(batch)
            bad["assertions"][0]["source_columns"] = columns
            with self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {10: text}, spans)

    def test_source_bound_ordinal_longitude(self):
        from src.public_assertions import public_assertion

        expression = "48′ of the 20th degree of Virgo ♍"
        evidence = "19° 48′ of Virgo"
        text, spans, batch = self.explicit_clock_case(
            expression + "; later: " + evidence,
            {"arcminute": "48", "ordinal_degree": "20"},
        )
        batch["assertions"][0].update(
            source_expression=expression,
            quantity="ecliptic_longitude",
            role="reduction",
            subject="Sun",
            reference=None,
            direction=None,
            zodiac_sign="Virgo",
            source_component_order=["arcminute", "ordinal_degree"],
            ordinal_degree_evidence={"line": 1, "expression": evidence},
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude_degrees"], "99/5")
        self.assertEqual(out["normalized"]["zodiac_longitude_degrees"], "849/5")
        self.assertEqual(out["normalized"]["source_ordinal_degree"], "20")
        for change in (
            {"ordinal_degree_evidence": None},
            {"ordinal_degree_evidence": {"line": 1, "expression": "18° 48′ of Virgo"}},
        ):
            bad = copy.deepcopy(batch)
            bad["assertions"][0].update(change)
            with self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {10: text}, spans)

    def test_written_fractional_degree_qualifications_keep_native_units(self):
        from src.public_assertions import public_assertion

        for literal, words, value, expected in (
            ("two-fifths of a degree", {"two-fifths": "2/5"}, "2/5", "1440"),
            ("one-sixth of a degree", {"one-sixth": "1/6"}, "1/6", "600"),
            ("a tenth part of a single degree", {"a tenth part": "1/10"}, "1/10", "360"),
            ("a full degree", {"a full degree": "1"}, "1", "3600"),
            (
                "sixth part of one degree",
                {"sixth part of one degree": "1/6"},
                "1/6",
                "600",
            ),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, {"degree": value})
                batch["assertions"][0].update(
                    quantity="calculation_angle",
                    role="historical_input",
                    subject="New Star of 1572",
                    reference=None,
                    direction=None,
                    source_word_numbers=words,
                    flags=["not_an_additional_raw_reading"],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                result = public_assertion(row)
                self.assertEqual(row["source_expression"], literal)
                self.assertEqual(result["normalized"]["magnitude"], expected)
                self.assertEqual(result["normalized"]["unit"], "arcsecond")

    def test_native_sexagesimal_length_is_not_an_angle(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "2° 3′ 32″", {"source_part": "2", "part_minute": "3", "part_second": "32"}
        )
        batch["assertions"][0].update(
            quantity="source_sexagesimal_length",
            role="historical_input",
            subject="Sun calculation",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
            unit_basis="Source explicitly describes linear eccentricity in parts on radius60 scale.",
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "1853/900")
        self.assertEqual(out["normalized"]["unit"], "source_length_part")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["components"] = {
            "source_part": "2",
            "part_second": "3",
            "part_minute": "32",
        }
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, spans)
        bad_row = copy.deepcopy(row)
        bad_row["normalized"]["magnitude"] = "2"
        with self.assertRaises(ValueError):
            public_assertion(bad_row)

    def test_native_length_without_written_seconds(self):
        from src.public_assertions import public_assertion

        for expression, minute, expected in (("2° 9′", "9", "43/20"), ("2°9⅓", "9 1/3", "97/45")):
            text, spans, batch = self.explicit_clock_case(
                expression, {"source_part": "2", "part_minute": minute}
            )
            batch["assertions"][0].update(
                quantity="source_sexagesimal_length",
                role="historical_input",
                subject="Sun calculation",
                reference=None,
                direction=None,
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["magnitude"], expected)
            self.assertEqual(out["normalized"]["least_component_unit"], "part_minute")
            self.assertNotIn("part_second", row["components"])

    def test_seventh_angular_place_remains_exact(self):
        from fractions import Fraction
        from src.public_assertions import public_assertion

        components = dict(
            degree="0",
            arcminute="59",
            arcsecond="8",
            arcsexagesimal_third="11",
            arcsexagesimal_fourth="27",
            arcsexagesimal_fifth="14",
            arcsexagesimal_sixth="26",
            arcsexagesimal_seventh="54",
        )
        expression = "0° 59′ 8″ 11‴ 27⁗ 14′′′′′ 26′′′′′′ 54′′′′′′′"
        text, spans, batch = self.explicit_clock_case(expression, components)
        batch["assertions"][0].update(
            quantity="angular_daily_motion",
            role="calculation_intermediate",
            subject="Sun",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        expected = Fraction(59 * 60 + 8) + sum(
            Fraction(value, 60**power) for power, value in enumerate((11, 27, 14, 26, 54), 1)
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], str(expected))
        self.assertEqual(out["normalized"]["least_component_unit"], "arcsexagesimal_seventh")
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["components"]["arcsexagesimal_seventh"] = "60"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_gradus_and_comma_minute_notation(self):
        from src.public_assertions import public_assertion

        for expr, comps, expected in (
            ("G. 27. 1. 26", {"degree": "27", "arcminute": "26"}, "98760"),
            ("P. 338, 1. 23", {"degree": "338", "arcminute": "23"}, "1218180"),
            (
                "Sign 5, G. 25. 1. 34",
                {"sign_count": "5", "degree": "25", "arcminute": "34"},
                "632040",
            ),
        ):
            text, spans, batch = self.explicit_clock_case(expr, comps)
            batch["assertions"][0].update(
                quantity="calculation_angle",
                role="historical_input",
                subject="Sun calculation",
                reference=None,
                direction=None,
                source_unit_notation="parts_1_minutes",
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            self.assertEqual(public_assertion(row)["normalized"]["magnitude"], expected)

    def test_reviewed_parts_minute_marker(self):
        from src.public_assertions import public_assertion

        for expression, quantity, components, expected in (
            ("P. 2. 1. 10", "calculation_angle", {"degree": "2", "arcminute": "10"}, "7800"),
            (
                "P. 2. 1. 29½",
                "source_sexagesimal_length",
                {"source_part": "2", "part_minute": "29 1/2"},
                "299/120",
            ),
            (
                "Sign 6, P. 2. 1. 10",
                "calculation_angle",
                {"sign_count": "6", "degree": "2", "arcminute": "10"},
                "655800",
            ),
        ):
            text, spans, batch = self.explicit_clock_case(expression, components)
            batch["assertions"][0].update(
                quantity=quantity,
                role="historical_input",
                subject="Sun calculation",
                reference=None,
                direction=None,
                source_unit_notation="parts_1_minutes",
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["magnitude"], expected)
            self.assertEqual(out["source_unit_notation"], "parts_1_minutes")
            bad = copy.deepcopy(batch)
            key = "arcminute" if "arcminute" in components else "part_minute"
            bad["assertions"][0]["components"][key] = "1"
            with self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {10: text}, spans)
            bad = copy.deepcopy(row)
            bad["components"][key] = "1"
            with self.assertRaises(ValueError):
                public_assertion(bad)

    def test_stated_one_131st_day_is_preserved(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("a 131st part", {"day": "1/131"})
        batch["assertions"][0].update(
            quantity="clock_elapsed_time",
            role="historical_input",
            subject="Sun",
            reference=None,
            direction=None,
            source_word_numbers={"a 131st part": "1/131"},
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "86400/131")

    def test_omitted_whole_degrees_are_not_inherited(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("22′¾", {"arcminute": "22 3/4"})
        batch["assertions"][0].update(
            quantity="altitude",
            role="historical_input",
            subject="site pole elevation",
            reference=None,
            direction=None,
            source_component_addends={"arcminute": ["22", "3/4"]},
            flags=["not_an_additional_raw_reading", "source_component_omitted"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(row["components"], {"arcminute": "22 3/4"})
        self.assertEqual(out["normalized"]["magnitude"], "1365")
        self.assertIn("source_component_omitted", out["flags"])

    def test_unclassified_historical_angle_is_not_a_raw_reading(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("4°½", {"degree": "4 1/2"})
        batch["assertions"][0].update(
            quantity="unclassified_angle",
            role="historical_input",
            subject="Sun",
            reference=None,
            direction=None,
            source_component_addends={"degree": ["4", "1/2"]},
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(out["quantity"], "unclassified_angle")
        self.assertEqual(out["role"], "historical_input")
        self.assertEqual(out["normalized"]["magnitude"], "16200")
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        for change in (
            {"flags": []},
            {"role": "recorded_reading"},
            {"direction": "north"},
            {"reference": "Aldebaran"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(dict(row, **change))

    def test_native_length_difference_in_seconds_only(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("single second", {"part_second": "1"})
        batch["assertions"][0].update(
            quantity="source_sexagesimal_length",
            role="historical_input",
            subject="Sun calculation",
            reference=None,
            direction=None,
            source_word_numbers={"single": "1"},
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "1/3600")
        self.assertEqual(out["normalized"]["least_component_unit"], "part_second")
        self.assertEqual(row["components"], {"part_second": "1"})

    def test_native_distance_sixtieths_without_a_whole_radius(self):
        from src.public_assertions import public_assertion

        for token, expected in (("17", "17/60"), ("0", "0"), ("60", "1"), ("120", "2")):
            text, spans, batch = self.explicit_clock_case(
                token + " sixtieths", {"semidiameter_minute": token}
            )
            batch["assertions"][0].update(
                quantity="distance_in_semidiameters",
                role="historical_input",
                subject="Moon",
                reference="Earth",
                direction=None,
                source_semidiameter_body="Earth",
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["magnitude"], expected)
            self.assertEqual(out["normalized"]["least_component_unit"], "semidiameter_minute")
            self.assertEqual(row["components"], {"semidiameter_minute": token})
        from src.normalization import normalize_quantity

        for components in (
            {"semidiameter": "0", "semidiameter_minute": "60"},
            {"semidiameter_minute": "-1"},
            {"semidiameter_minute": "120", "semidiameter_second": "60"},
        ):
            with self.assertRaises(ValueError):
                normalize_quantity(
                    dict(quantity="distance_in_semidiameters", components=components)
                )
        self.assertEqual(
            normalize_quantity(dict(quantity="distance_in_semidiameters", components={}))["status"],
            "unsupported",
        )

    def test_native_radius_and_mile_places_keep_their_length_units(self):
        from src.public_assertions import public_assertion
        from src.normalization import normalize_quantity

        for literal, quantity, components, expected, least, unit in (
            (
                "19 Earth-radii 50 minutes 12 seconds",
                "distance_in_semidiameters",
                {"semidiameter": "19", "semidiameter_minute": "50", "semidiameter_second": "12"},
                "5951/300",
                "semidiameter_second",
                "source_semidiameter",
            ),
            (
                "19 Earth-radii 12 seconds",
                "distance_in_semidiameters",
                {"semidiameter": "19", "semidiameter_second": "12"},
                "5701/300",
                "semidiameter_second",
                "source_semidiameter",
            ),
            (
                "46 miles 49⅔ minutes",
                "distance_in_german_miles",
                {"mile": "46", "mile_minute": "49 2/3"},
                "8429/180",
                "mile_minute",
                "source_german_mile",
            ),
            (
                "1 mile 30 minutes 30 seconds",
                "distance_in_ordinary_miles",
                {"mile": "1", "mile_minute": "30", "mile_second": "30"},
                "181/120",
                "mile_second",
                "source_ordinary_mile",
            ),
        ):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, components)
                batch["assertions"][0].update(
                    quantity=quantity,
                    role="historical_input",
                    subject="New Star calculation",
                    reference="Earth" if quantity == "distance_in_semidiameters" else None,
                    direction=None,
                    flags=["not_an_additional_raw_reading"],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                norm = public_assertion(row)["normalized"]
                self.assertEqual(
                    (norm["magnitude"], norm["unit"], norm["least_component_unit"]),
                    (expected, unit, least),
                )
                self.assertIsNone(norm["magnitude_degrees"])
                self.assertEqual(row["source_expression"], literal)
        for quantity, component in (
            ("distance_in_semidiameters", "semidiameter_second"),
            ("distance_in_german_miles", "mile_second"),
        ):
            self.assertEqual(
                normalize_quantity(dict(quantity=quantity, components={component: "60"}))[
                    "magnitude"
                ],
                "1/60",
            )
            for value in ("60", "-1"):
                with self.subTest(component=component, value=value), self.assertRaises(ValueError):
                    base = "semidiameter" if quantity == "distance_in_semidiameters" else "mile"
                    normalize_quantity(
                        dict(quantity=quantity, components={base: "0", component: value})
                    )
        for quantity, wrong in (
            ("distance_in_semidiameters", "semidiameter_minute"),
            ("distance_in_german_miles", "mile_minute"),
        ):
            text, spans, batch = self.explicit_clock_case("12 seconds", {wrong: "12"})
            batch["assertions"][0].update(quantity=quantity)
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                self.module().compile_catalogue([batch], {10: text}, spans)

    def test_native_paces_and_unspecified_miles_do_not_choose_a_physical_conversion(self):
        from src.public_assertions import public_assertion

        for quantity, unit in (
            ("distance_in_paces", "source_pace"),
            ("distance_in_unspecified_miles", "source_unspecified_mile"),
        ):
            text, spans, batch = self.explicit_clock_case("2905", {"scalar": "2905"})
            batch["assertions"][0].update(
                quantity=quantity,
                role="historical_input",
                subject="New Star calculation",
                reference=None,
                direction=None,
                flags=["not_an_additional_raw_reading"],
            )
            out = public_assertion(
                self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            )
            self.assertEqual(
                (out["normalized"]["magnitude"], out["normalized"]["unit"]), ("2905", unit)
            )
            self.assertIsNone(out["normalized"]["magnitude_degrees"])

    def test_geographic_latitude_and_diameter_variation_keep_distinct_meanings(self):
        from src.public_assertions import public_assertion

        for quantity, subject in (
            ("geographical_latitude", "observing site"),
            ("angular_diameter_variation", "Sun"),
        ):
            text, spans, batch = self.explicit_clock_case(
                "1° 30′", {"degree": "1", "arcminute": "30"}
            )
            batch["assertions"][0].update(
                quantity=quantity,
                role="historical_input",
                subject=subject,
                reference=None,
                direction=None,
                flags=["not_an_additional_raw_reading"],
            )
            out = public_assertion(
                self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            )
            self.assertEqual(out["quantity"], quantity)
            self.assertEqual(out["normalized"]["magnitude"], "5400")
            self.assertEqual(out["normalized"]["unit"], "arcsecond")

    def test_postfixed_slashes_preserve_minute_second_and_third_places(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "19 /6 // 1 ///", {"arcminute": "19", "arcsecond": "6", "arcsexagesimal_third": "1"}
        )
        row = batch["assertions"][0]
        row.update(
            quantity="angular_length",
            role="historical_input",
            subject="New Star of 1572",
            reference=None,
            direction=None,
            source_unit_notation="postfixed_minute_second_third_slashes",
            flags=["not_an_additional_raw_reading", "source_quality_note_present"],
        )
        out = public_assertion(
            self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        )
        self.assertEqual(out["normalized"]["magnitude"], "68761/60")
        for literal in ("19/6", "19 /6 // 1 //", "19 /6 // 1 /// 2", "19 /60 // 1 ///"):
            text, spans, batch = self.explicit_clock_case(literal, row["components"])
            batch["assertions"][0].update(
                {
                    k: row[k]
                    for k in (
                        "quantity",
                        "role",
                        "subject",
                        "reference",
                        "direction",
                        "source_unit_notation",
                        "flags",
                    )
                }
            )
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                self.module().compile_catalogue([batch], {10: text}, spans)

    def test_decan_position_preserves_sector_bounds_without_a_point_longitude(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("first face ♉", {})
        row = batch["assertions"][0]
        row.update(
            quantity="ecliptic_longitude",
            role="historical_input",
            subject="New Star of 1572",
            reference=None,
            direction=None,
            zodiac_sign="Taurus",
            source_zodiac_sector={"kind": "decan", "ordinal": 1},
            flags=["not_an_additional_raw_reading"],
        )
        compiled = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        out = public_assertion(compiled)
        self.assertIsNone(out["normalized"]["magnitude"])
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        self.assertEqual(out["normalized"]["within_sign_range_degrees"], ["0", "10"])
        self.assertEqual(out["normalized"]["zodiac_longitude_range_degrees"], ["30", "40"])
        self.assertEqual(out["normalized"]["normalization_issue"], "coordinate_sector_not_scalar")
        for change in (
            {"source_zodiac_sector": {"kind": "decan", "ordinal": 2}},
            {"components": {"degree": "5"}},
            {"direction": "north"},
        ):
            row.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().compile_catalogue([batch], {10: text}, spans)
            row.update(
                components={}, direction=None, source_zodiac_sector={"kind": "decan", "ordinal": 1}
            )
        compiled["normalized"]["within_sign_range_degrees"] = ["900", "1000"]
        with self.assertRaises(ValueError):
            public_assertion(compiled)

    def test_reviewed_parts_slash_minutes_do_not_become_fractions(self):
        from src.public_assertions import public_assertion

        for literal, degree, minute in (
            ("p. 60./0", "60", "0"),
            ("p. 41/35", "41", "35"),
            ("P.0./39", "0", "39"),
        ):
            text, spans, batch = self.explicit_clock_case(
                literal, {"degree": degree, "arcminute": minute}
            )
            batch["assertions"][0].update(
                quantity="altitude",
                role="historical_input",
                subject="Mars",
                reference=None,
                direction=None,
                source_unit_notation="parts_slash_minutes",
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            self.assertEqual(
                public_assertion(row)["normalized"]["magnitude"],
                str(int(degree) * 3600 + int(minute) * 60),
            )
            self.assertEqual(row["source_expression"], literal)
            batch["assertions"][0]["components"] = {"degree": degree, "arcsecond": minute}
            with self.assertRaises(ValueError):
                self.module().compile_catalogue([batch], {10: text}, spans)
        for literal in ("41/35", "p.41/35/10", "p.41/?", "p.41/35 1/2"):
            text, spans, batch = self.explicit_clock_case(
                literal, {"degree": "41", "arcminute": "35"}
            )
            batch["assertions"][0].update(
                quantity="altitude", source_unit_notation="parts_slash_minutes"
            )
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                self.module().compile_catalogue([batch], {10: text}, spans)

    def test_grouped_mixed_lengths_preserve_fraction_and_reject_partial_numbers(self):
        from src.public_assertions import public_assertion
        from src.normalization import source_numeric_text

        for literal, quantity, component, token, expected in (
            ("107,231 1/7", "source_sexagesimal_length", "source_part", "107231 1/7", "750618/7"),
            ("17,059½", "distance_in_german_miles", "scalar", "17059 1/2", "34119/2"),
        ):
            text, spans, batch = self.explicit_clock_case(literal, {component: token})
            batch["assertions"][0].update(
                quantity=quantity,
                role="historical_input",
                subject="New Star calculation",
                reference=None,
                direction=None,
                source_number_grouping="comma_thousands_mixed_fraction",
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            self.assertEqual(public_assertion(row)["normalized"]["magnitude"], expected)
            self.assertEqual(row["source_expression"], literal)
        for literal in (
            "107,23 1/7",
            "107,231 1/0",
            "107,231 7/7",
            "107,231 1/7 2",
            "107,231 1/7 minutes",
        ):
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                source_numeric_text(
                    dict(
                        quantity="source_scalar",
                        source_number_grouping="comma_thousands_mixed_fraction",
                    ),
                    literal,
                )
        with self.assertRaises(ValueError):
            source_numeric_text(
                dict(quantity="source_scalar", source_number_grouping="comma_thousands"),
                "107,231 1/7",
            )

    def test_native_distance_counts_accept_only_whole_comma_grouping(self):
        from src.public_assertions import public_assertion
        from src.normalization import source_numeric_text

        for expression, quantity, components, subject, reference, unit in (
            (
                "100,000",
                "source_sexagesimal_length",
                {"source_part": "100000"},
                "New Star calculation",
                None,
                "source_length_part",
            ),
            (
                "1,182",
                "distance_in_semidiameters",
                {"semidiameter": "1182"},
                "New Star of 1572",
                "Earth",
                "source_semidiameter",
            ),
            (
                "5,400",
                "distance_in_german_miles",
                {"scalar": "5400"},
                "Earth",
                None,
                "source_german_mile",
            ),
            (
                "8,600,000,000",
                "distance_in_german_miles",
                {"mile": "8600000000"},
                "fixed stars",
                "Earth",
                "source_german_mile",
            ),
        ):
            with self.subTest(quantity=quantity):
                text, spans, batch = self.explicit_clock_case(expression, components)
                batch["assertions"][0].update(
                    quantity=quantity,
                    role="historical_input",
                    subject=subject,
                    reference=reference,
                    direction=None,
                    source_number_grouping="comma_thousands",
                    flags=["not_an_additional_raw_reading"],
                )
                result = self.module().compile_catalogue([batch], {10: text}, spans)
                out = public_assertion(result["assertions"][0])
                self.assertEqual(out["normalized"]["unit"], unit)
                self.assertEqual(out["normalized"]["magnitude"], next(iter(components.values())))
        with self.assertRaises(ValueError):
            source_numeric_text(
                dict(
                    quantity="distance_in_semidiameters",
                    source_number_grouping="spaced_integer_digits",
                ),
                "52 25",
            )
        with self.assertRaises(ValueError):
            source_numeric_text(
                dict(
                    quantity="distance_in_semidiameters", source_number_grouping="comma_thousands"
                ),
                "52 semidiameters 25′",
            )

    def test_reviewed_native_integer_grouping(self):
        from src.public_assertions import public_assertion
        from src.normalization import source_numeric_text

        for expression, grouping, expected in (
            ("18 22 58 68", "spaced_integer_digits", "18225868"),
            ("1999 23 42", "spaced_integer_digits", "19992342"),
            ("6,873,833", "comma_thousands", "6873833"),
        ):
            text, spans, batch = self.explicit_clock_case(expression, {"scalar": expected})
            batch["assertions"][0].update(
                quantity="source_scalar",
                role="calculation_intermediate",
                subject="Sun calculation",
                reference=None,
                direction=None,
                source_number_grouping=grouping,
                source_parameter_kind="model_length",
                source_scalar_scale="10000000",
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["magnitude"], expected)
            self.assertEqual(row["source_expression"], expression)
            self.assertEqual(
                public_assertion(dict(row, subject="Moon calculation"))["normalized"]["magnitude"],
                expected,
            )
            bad = copy.deepcopy(row)
            bad["components"]["scalar"] = "1"
            with self.assertRaises(ValueError):
                public_assertion(bad)
        for expression, grouping in (
            ("1 1/2", "spaced_integer_digits"),
            ("2° 9′", "spaced_integer_digits"),
            ("1,25", "comma_thousands"),
            ("1,234 56", "comma_thousands"),
        ):
            with self.assertRaises(ValueError):
                source_numeric_text(
                    dict(quantity="source_scalar", source_number_grouping=grouping), expression
                )
        with self.assertRaises(ValueError):
            source_numeric_text(
                dict(quantity="calculation_angle", source_number_grouping="spaced_integer_digits"),
                "18 22",
            )

    def test_worded_precision_fractions(self):
        from src.public_assertions import public_assertion

        for expression, value, expected in (("a third", "1/3", "20"), ("a fourth", "1/4", "15")):
            text, spans, batch = self.explicit_clock_case(expression, {"arcminute": value})
            batch["assertions"][0].update(
                quantity="stated_angular_precision",
                role="historical_input",
                subject="Sun",
                reference=None,
                direction=None,
                source_word_numbers={expression: value},
                flags=["not_an_additional_raw_reading"],
            )
            row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            self.assertEqual(public_assertion(row)["normalized"]["magnitude"], expected)

    def test_worded_zodiac_division_preserves_degrees(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "thirty equal parts, or degrees", {"degree": "30"}
        )
        batch["assertions"][0].update(
            quantity="calculation_angle",
            role="historical_input",
            subject="ecliptic",
            reference=None,
            direction=None,
            source_word_numbers={"thirty": "30"},
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "108000")

    def test_worded_sixth_degree_table_step(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("sixth of a degree", {"degree": "1/6"})
        batch["assertions"][0].update(
            quantity="calculation_angle",
            role="historical_input",
            subject="Sun",
            reference=None,
            direction=None,
            source_word_numbers={"sixth of a degree": "1/6"},
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "600")

    def test_right_ascension_difference_preserves_unreduced_leading_minutes(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "65′ 27″", {"arcminute": "65", "arcsecond": "27"}
        )
        batch["assertions"][0].update(
            quantity="right_ascension_difference",
            role="historical_input",
            subject="ecliptic",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "3927")
        with self.assertRaises(ValueError):
            self.module().normalize_quantity(
                dict(
                    quantity="right_ascension_difference",
                    components={"degree": "1", "arcminute": "65"},
                )
            )

    def test_worded_solar_correction_and_precision_values(self):
        from src.public_assertions import public_assertion

        cases = [
            ("five-twelfths", "degree", "5/12", "1500"),
            ("a minute", "arcminute", "1", "60"),
            ("whole one", "arcminute", "1", "60"),
            ("halves", "arcminute", "1/2", "30"),
            ("quarters", "arcminute", "1/4", "15"),
            ("tens", "arcsecond", "10", "10"),
            ("fives", "arcsecond", "5", "5"),
        ]
        for expression, unit, value, expected in cases:
            with self.subTest(expression=expression):
                text, spans, batch = self.explicit_clock_case(expression, {unit: value})
                batch["assertions"][0].update(
                    quantity="calculation_angle",
                    role="historical_input",
                    subject="Sun",
                    reference=None,
                    direction=None,
                    source_word_numbers={expression: value},
                    flags=["not_an_additional_raw_reading"],
                )
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                self.assertEqual(public_assertion(row)["normalized"]["magnitude"], expected)

    def test_worded_degree_and_sixth_retains_addends(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "sixty-three degrees, with a sixth", {"degree": "63 1/6"}
        )
        batch["assertions"][0].update(
            quantity="right_ascension",
            role="reduction",
            subject="Aldebaran",
            reference=None,
            direction=None,
            source_word_numbers={"sixty-three": "63", "a sixth": "1/6"},
            source_component_addends={"degree": ["63", "1/6"]},
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "227400")
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["source_word_numbers"]["a sixth"] = "6"
        with self.assertRaisesRegex(ValueError, "word number"):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_worded_obliquity_preserves_half_degree(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "twenty-three and a half degrees", {"degree": "23 1/2"}
        )
        batch["assertions"][0].update(
            quantity="obliquity",
            role="historical_input",
            subject="Sun",
            reference=None,
            direction=None,
            source_word_numbers={"twenty-three and a half": "23 1/2"},
            flags=["not_an_additional_raw_reading", "source_approximate"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "84600")
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["components"]["degree"] = "23"
        with self.assertRaisesRegex(ValueError, "complete source number"):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_uncertain_solar_calculation_epoch_has_no_scalar(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("20^h^ 4½ [?]^m^", {})
        batch["assertions"][0].update(
            quantity="calculation_epoch",
            role="calculation_epoch",
            subject="Sun",
            reference=None,
            direction=None,
            flags=[
                "source_notation_unresolved",
                "not_an_observing_clock",
                "not_an_additional_raw_reading",
                "absolute_time_unestablished",
            ],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        public = public_assertion(row)
        self.assertEqual(public["normalized"]["status"], "unsupported")
        self.assertIsNone(public["normalized"]["magnitude"])
        bad = copy.deepcopy(row)
        bad["normalized"]["magnitude"] = "72270"
        with self.assertRaisesRegex(ValueError, "interpreted scalar"):
            public_assertion(bad)

    def test_quarter_of_one_arcminute_preserves_full_precision_expression(self):
        from src.public_assertions import public_assertion

        expression = "a quarter of 1′"
        text, spans, batch = self.explicit_clock_case(expression, {"arcminute": "1/4"})
        batch["assertions"][0].update(
            quantity="stated_angular_precision",
            role="historical_input",
            subject="Sun",
            reference=None,
            direction=None,
            source_word_numbers={"a quarter of 1": "1/4"},
            flags=["not_an_additional_raw_reading"],
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(row["source_expression"], expression)
        self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "15")
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["components"]["arcminute"] = "1"
        with self.assertRaisesRegex(ValueError, "complete source number"):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_geographical_longitude_is_not_a_zodiac_coordinate(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case(
            "39° 50′", {"degree": "39", "arcminute": "50"}
        )
        row = batch["assertions"][0]
        row.update(
            quantity="geographical_longitude",
            role="historical_input",
            subject="historical observatory longitude",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
        )
        out = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        normalized = public_assertion(out)["normalized"]
        self.assertEqual(normalized["magnitude"], "143400")
        self.assertNotIn("zodiac_sign", normalized)
        self.assertIsNone(normalized["signed_magnitude"])

    def test_lunar_semidiameter_retains_its_own_angle_without_doubling(self):
        from src.public_assertions import public_assertion

        text, spans, batch = self.explicit_clock_case("18′", {"arcminute": "18"})
        row = batch["assertions"][0]
        row.update(
            quantity="angular_semidiameter",
            role="historical_correction",
            subject="Moon",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
            unit_basis="Printed lunar semidiameter in minutes",
        )
        out = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        public = public_assertion(out)
        self.assertEqual(public["normalized"]["magnitude"], "1080")
        self.assertEqual(public["normalized"]["unit"], "arcsecond")
        self.assertEqual(public["quantity"], "angular_semidiameter")

    def test_approximate_seventh_hour_preserves_word_expression(self):
        text, spans, batch = self.explicit_clock_case(
            "around the seventh hour of evening", {"hour": "7"}
        )
        row = batch["assertions"][0]
        row.update(
            source_expression="seventh",
            quantity="annotated_time",
            role="recorded_reading",
            subject="Mars",
            source_word_numbers={"seventh": "7"},
            flags=["source_approximate"],
        )
        out = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(
            (out["source_expression"], out["normalized"]["magnitude"]), ("seventh", "25200")
        )
        self.assertIn("source_approximate", out["flags"])

    def test_journal_ordinal_hour_labels_preserve_native_clock_units(self):
        for literal, value in (("2nd hour", "2"), ("7th hour", "7")):
            with self.subTest(literal=literal):
                text, spans, batch = self.explicit_clock_case(literal, {"hour": value})
                batch["assertions"][0]["source_word_numbers"] = {literal.split()[0]: value}
                row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                self.assertEqual(row["source_expression"], literal)
                self.assertEqual(row["normalized"]["magnitude"], str(int(value) * 3600))

    def test_chart_dot_with_reviewed_degree_minute_units_is_not_a_decimal(self):
        text, spans, batch = self.explicit_clock_case(
            "☉ 9.47 ♐", {"degree": "9", "arcminute": "47"}
        )
        batch["assertions"][0].update(
            quantity="ecliptic_longitude",
            role="historical_input",
            subject="Sun",
            zodiac_sign="Sagittarius",
            flags=["not_an_additional_raw_reading"],
            unit_basis="The source figure description explicitly expands this label as9degrees47minutes.",
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(row["source_expression"], "☉ 9.47 ♐")
        self.assertEqual(row["components"], {"degree": "9", "arcminute": "47"})
        self.assertEqual(row["normalized"]["magnitude"], "35220")

    def test_book_preparation_is_shared_within_a_compile_but_not_between_calls(self):
        class CountedText(str):
            splits = 0
            encodings = 0

            def splitlines(self, *args, **kwargs):
                self.splits += 1
                return super().splitlines(*args, **kwargs)

            def encode(self, *args, **kwargs):
                self.encodings += 1
                return super().encode(*args, **kwargs)

        text = CountedText("1°\n2°\n")
        sha = hashlib.sha256(str(text).encode()).hexdigest()
        spans = []
        batches = []
        for line, value in ((1, "1"), (2, "2")):
            sid = "s" + value
            spans.append(
                dict(id=sid, volume=10, edition_sha256=sha, line_start=line, line_end=line)
            )
            batches.append(
                dict(
                    id="r" + value,
                    volume=10,
                    edition_sha256=sha,
                    line_start=line,
                    line_end=line,
                    interval_sha256=hashlib.sha256((value + "°").encode()).hexdigest(),
                    basis=dict(kind="final_edition_review", printed_page=1),
                    span_decisions=[dict(span_id=sid, decision="include", reason="Recorded angle")],
                    assertions=[
                        dict(
                            key="angle",
                            line=line,
                            span_id=sid,
                            source_expression=value + "°",
                            quantity="altitude",
                            role="recorded_reading",
                            subject="Mars",
                            reference=None,
                            components=dict(degree=value),
                            unit_basis="Explicit degrees",
                        )
                    ],
                )
            )
        out = self.module().compile_catalogue(batches, {10: text}, spans, edition_hashes={10: sha})
        self.assertEqual(
            sorted(a["normalized"]["magnitude"] for a in out["assertions"]), ["3600", "7200"]
        )
        self.assertEqual((text.splits, text.encodings), (1, 0))
        unhashed = CountedText(str(text))
        self.assertEqual(self.module().compile_catalogue(batches, {10: unhashed}, spans), out)
        self.assertEqual((unhashed.splits, unhashed.encodings), (1, 1))
        changed = CountedText("3°\n2°\n")
        with self.assertRaises(ValueError):
            self.module().compile_catalogue(batches, {10: changed}, spans, edition_hashes={10: sha})

    def test_sexagesimal_day_parts_are_durations_not_clock_minutes(self):
        from src.public_checkpoint import public_assertion

        text = "D. 1 M. 59\n1°57′41″\n1ᵈ 59′ 8″ 10‴\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=3)
        common = dict(
            span_id="s",
            quantity="clock_elapsed_time",
            role="calculation_intermediate",
            subject="Mars",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
            unit_basis="Contextual sexagesimal day fractions; literal expressions unchanged",
        )
        assertions = [
            dict(
                common,
                key="first",
                line=1,
                source_expression="D. 1 M. 59",
                components=dict(day="1", day_minute="59"),
            ),
            dict(
                common,
                key="second",
                line=2,
                source_expression="1°57′41″",
                components=dict(day="1", day_minute="57", day_second="41"),
            ),
            dict(
                common,
                key="third",
                line=3,
                source_expression="1ᵈ 59′ 8″ 10‴",
                components=dict(day="1", day_minute="59", day_second="8", day_third="10"),
            ),
        ]
        batch = dict(
            id="fractional-days",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=3,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=198),
            assertions=assertions,
            span_decisions=[
                dict(span_id="s", decision="include", reason="Explicit contextual duration")
            ],
        )
        out = self.module().compile_catalogue([batch], {10: text}, [span])["assertions"]
        indexed = {a["key"]: a for a in out}
        self.assertEqual(
            {k: a["normalized"]["magnitude"] for k, a in indexed.items()},
            {"first": "171360", "second": "169464", "third": "171556"},
        )
        for a in out:
            self.assertEqual(public_assertion(a)["normalized"], a["normalized"])
        self.assertEqual(indexed["first"]["source_expression"], "D. 1 M. 59")
        ordinary = self.module().normalize_quantity(
            dict(quantity="clock_elapsed_time", components=dict(day="1", minute="59"))
        )
        self.assertEqual(ordinary["magnitude"], "89940")
        for changes in (
            dict(quantity="recorded_clock"),
            dict(components=dict(day="1", day_minute="59", hour="2")),
            dict(components=dict(day="1", day_minute="60")),
            dict(components=dict(day="1", day_second="60")),
            dict(components=dict(day="1", day_third="60")),
        ):
            bad = dict(assertions[0])
            bad.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().normalize_quantity(bad)

    def test_lunar_word_components_preserve_degree_and_dimensionless_fractions(self):
        text = "first degree of ♈ at 20′ 9″\none and a half\nfifth part\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=3)]
        common = dict(
            span_id="s",
            role="historical_input",
            reference=None,
            flags=["not_an_additional_raw_reading"],
            unit_basis="Explicit source word component",
        )
        assertions = [
            dict(
                common,
                key="degree",
                line=1,
                source_expression=text.splitlines()[0],
                subject="Moon",
                quantity="ecliptic_longitude",
                zodiac_sign="Aries",
                components={"degree": "1", "arcminute": "20", "arcsecond": "9"},
                source_word_numbers={"first": "1"},
            )
        ]
        for n, word, value in [(2, "one and a half", "1 1/2"), (3, "fifth part", "1/5")]:
            assertions.append(
                dict(
                    common,
                    key=str(n),
                    line=n,
                    source_expression=word,
                    subject="Moon calculation",
                    quantity="source_scalar",
                    source_parameter_kind="arithmetic_intermediate",
                    components={"scalar": value},
                    source_word_numbers={word: value},
                )
            )
        batch = dict(
            id="lunar-words",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=3,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=62),
            assertions=assertions,
            span_decisions=[dict(span_id="s", decision="include", reason="Bound source words")],
        )
        result = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"]
        self.assertEqual(
            {r["key"]: r["normalized"]["magnitude"] for r in result},
            {"degree": "4809", "2": "3/2", "3": "1/5"},
        )
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["source_word_numbers"]["first"] = "0"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_latin_quarter_hour_retains_wording_and_exact_fraction(self):
        text = "Venus and Moon, hora nona cum quadrante\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=1)
        row = dict(
            key="clock",
            line=1,
            span_id="s",
            source_expression="hora nona cum quadrante",
            quantity="recorded_clock",
            role="recorded_clock",
            subject="observing clock",
            reference=None,
            components={"hour": "9 1/4"},
            source_word_numbers={"nona cum quadrante": "9 1/4"},
            flags=["absolute_time_unestablished"],
            unit_basis="Explicit ninth hour with a quarter",
        )
        batch = dict(
            id="latin-quarter",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=49),
            assertions=[row],
            span_decisions=[
                dict(span_id="s", decision="include", reason="Explicit word-number clock")
            ],
        )
        try:
            out = self.module().compile_catalogue([batch], {10: text}, [span])["assertions"][0]
        except ValueError as error:
            self.fail(f"Explicit Latin quarter-hour must normalize: {error}")
        self.assertEqual(
            (out["source_expression"], out["normalized"]["magnitude"]),
            ("hora nona cum quadrante", "33300"),
        )
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["source_word_numbers"]["nona cum quadrante"] = "9 3/4"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, [span])

    def test_source_component_order_keeps_reverse_wording_and_an_unresolved_alternative(self):
        from src.public_checkpoint import public_assertion

        text = "northern latitude of 45\nor up to min. 40 above one degree\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=2)]
        original = dict(
            key="first",
            line=1,
            span_id="s",
            source_expression="45",
            quantity="ecliptic_latitude",
            role="reduction",
            subject="Mars",
            reference=None,
            direction="north",
            components=None,
            flags=["source_notation_unresolved", "not_an_additional_raw_reading"],
            unit_basis="Unresolved leading component",
        )
        alternative = dict(
            original,
            key="alternative",
            line=2,
            source_expression="up to min. 40 above one degree",
            role="source_alternative",
            variant_of_key="first",
            components=dict(degree="1", arcminute="40"),
            source_word_numbers={"one": "1"},
            source_component_order=["arcminute", "degree"],
            flags=[
                "alternative_suggestion_not_applied",
                "not_an_additional_raw_reading",
                "source_upper_bound",
            ],
        )
        batch = dict(
            id="reverse-units",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=18),
            assertions=[original, alternative],
            span_decisions=[
                dict(span_id="s", decision="include", reason="Explicit reverse unit order")
            ],
        )
        try:
            result = self.module().compile_catalogue([batch], {10: text}, spans)
        except ValueError as error:
            self.fail("Source unit order must preserve the explicit alternative: " + str(error))
        rows = {a["key"]: a for a in result["assertions"]}
        self.assertIsNone(rows["first"]["normalized"]["magnitude"])
        self.assertEqual(rows["alternative"]["normalized"]["magnitude"], "6000")
        self.assertEqual(rows["alternative"]["normalized"]["signed_magnitude"], "6000")
        self.assertEqual(rows["alternative"]["variant_of_id"], rows["first"]["id"])
        self.assertEqual(public_assertion(rows["alternative"])["normalized"]["magnitude"], "6000")
        for order in (["degree", "arcminute"], ["arcminute", "arcminute"], ["degree"], [], None):
            bad = copy.deepcopy(batch)
            bad["assertions"][1]["source_component_order"] = order
            with self.subTest(order=order), self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {10: text}, spans)

    def test_written_zodiac_name_can_bind_apogee_table_column(self):
        text = "| Ptolemy | 5° 30′ | Gemini [Gemin.] |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="row", volume=10, edition_sha256=sha, line_start=1, line_end=1)
        frame = dict(
            key="sign",
            kind="source_coordinate_frame",
            lines=[1],
            value=dict(
                subject="Sun",
                zodiac_sign="Gemini",
                line_start=1,
                line_end=1,
                source_expression="Gemini [Gemin.]",
            ),
        )
        row = dict(
            key="apogee",
            line=1,
            span_id="row",
            column=2,
            source_expression="5° 30′",
            quantity="ecliptic_longitude",
            role="historical_input",
            subject="Sun",
            reference=None,
            direction=None,
            components=dict(degree="5", arcminute="30"),
            zodiac_sign="Gemini",
            zodiac_sign_basis_key="sign",
            context_keys=["sign"],
            unit_basis="Separate written sign column",
            flags=["not_an_additional_raw_reading"],
        )
        batch = dict(
            id="apogee-review",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=105),
            contexts=[frame],
            assertions=[row],
            span_decisions=[dict(span_id="row", decision="include", reason="Written sign column")],
        )
        result = self.module().compile_catalogue([batch], {10: text}, [span])
        self.assertEqual(result["assertions"][0]["normalized"]["zodiac_sign"], "Gemini")
        bad = copy.deepcopy(batch)
        bad["contexts"][0]["value"]["source_expression"] = "Ptolemy"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, [span])

    def test_following_table_note_supplies_only_its_reviewed_zodiac_scope(self):
        from src.public_assertions import public_assertion

        text = "| 6° 54′ |\n| 7° 0′ |\n\nAll longitudes are in Taurus ♉.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [
            dict(id=f"s{n}", volume=10, edition_sha256=sha, line_start=n, line_end=n)
            for n in range(1, 5)
        ]
        frame = dict(
            key="frame",
            kind="source_coordinate_frame",
            lines=[4],
            value=dict(
                subject="New Star of 1572",
                zodiac_sign="Taurus",
                line_start=1,
                line_end=2,
                source_expression="All longitudes are in Taurus ♉.",
                scope_basis="following_table_note",
            ),
        )
        batch = dict(
            id="following-note",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=4,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=383),
            contexts=[frame],
            assertions=[],
            span_decisions=[
                dict(span_id=s["id"], decision="include", reason="Reviewed table note")
                for s in spans
            ],
        )
        for n, degree, minute in ((1, "6", "54"), (2, "7", "0")):
            batch["assertions"].append(
                dict(
                    key=f"q{n}",
                    line=n,
                    column=1,
                    span_id=f"s{n}",
                    source_expression=f"{degree}° {minute}′",
                    quantity="ecliptic_longitude",
                    role="historical_input",
                    subject="New Star of 1572",
                    reference=None,
                    direction=None,
                    components=dict(degree=degree, arcminute=minute),
                    zodiac_sign="Taurus",
                    zodiac_sign_basis_key="frame",
                    context_keys=["frame"],
                    flags=["not_an_additional_raw_reading"],
                    unit_basis="Explicit table note",
                )
            )
        result = self.module().compile_catalogue([batch], {10: text}, spans)
        self.assertEqual(
            {
                row["key"]: public_assertion(row)["normalized"]["zodiac_longitude_degrees"]
                for row in result["assertions"]
            },
            {"q1": "369/10", "q2": "37"},
        )
        for change in ({"scope_basis": "unreviewed"}, {"line_end": 3}, {"line_start": 2}):
            bad = copy.deepcopy(batch)
            bad["contexts"][0]["value"].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {10: text}, spans)
        bad = copy.deepcopy(batch)
        bad["assertions"][0].pop("column")
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: text}, spans)
        interrupted = text.replace("\n\nAll", "\n# Other section\nAll")
        bad = copy.deepcopy(batch)
        bad["edition_sha256"] = hashlib.sha256(interrupted.encode()).hexdigest()
        bad["interval_sha256"] = hashlib.sha256(interrupted.rstrip("\n").encode()).hexdigest()
        changed_spans = [dict(s, edition_sha256=bad["edition_sha256"]) for s in spans]
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([bad], {10: interrupted}, changed_spans)

    def test_reviewed_prose_zodiac_scope_binds_positions_without_fabricated_columns(self):
        from src.public_checkpoint import public_assertion

        text = "28° 45′, or rather 50, of ♌\n| Observation | 28 50 |\n| Stadius | 29 44 |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [
            dict(id="prose", volume=10, edition_sha256=sha, line_start=1, line_end=1),
            dict(id="table", volume=10, edition_sha256=sha, line_start=2, line_end=3),
        ]
        context = dict(
            key="frame",
            kind="source_coordinate_frame",
            lines=[1],
            value=dict(
                subject="Mars",
                zodiac_sign="Leo",
                line_start=1,
                line_end=3,
                source_expression="28° 45′, or rather 50, of ♌",
            ),
        )
        batch = dict(
            id="reviewed-frame",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=3,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=18),
            contexts=[context],
            assertions=[],
            span_decisions=[
                dict(span_id=s["id"], decision="include", reason="Explicit shared frame")
                for s in spans
            ],
        )
        for key, line, expression, minute, role, model in [
            ("prose-position", 1, "28° 45′", "45", "reduction", None),
            ("observed-place", 2, "28 50", "50", "reduction", None),
            ("model-place", 3, "29 44", "44", "historical_prediction", "Stadius"),
        ]:
            assertion = dict(
                key=key,
                line=line,
                span_id="prose" if line == 1 else "table",
                source_expression=expression,
                quantity="ecliptic_longitude",
                role=role,
                subject="Mars",
                reference=None,
                direction=None,
                components=dict(degree="29" if line == 3 else "28", arcminute=minute),
                zodiac_sign="Leo",
                zodiac_sign_basis_key="frame",
                context_keys=["frame"],
                flags=["not_an_additional_raw_reading"],
                unit_basis="Reviewed explicit prose frame",
            )
            if line > 1:
                assertion["column"] = 2
            if model:
                assertion["model_name"] = model
            batch["assertions"].append(assertion)
        try:
            result = self.module().compile_catalogue([batch], {10: text}, spans)
        except ValueError as error:
            self.fail("Explicit source frame must bind these positions: " + str(error))
        bykey = {a["key"]: a for a in result["assertions"]}
        self.assertIsNone(bykey["prose-position"].get("column"))
        self.assertEqual(bykey["prose-position"]["normalized"]["zodiac_longitude_degrees"], "595/4")
        self.assertEqual(bykey["model-place"]["normalized"]["zodiac_longitude_degrees"], "2246/15")
        exported = public_assertion(bykey["model-place"])
        self.assertEqual(exported["normalized"]["zodiac_sign"], "Leo")
        self.assertNotIn("zodiac_sign_basis_key", exported)
        self.assertEqual(
            exported["zodiac_sign_basis_context_id"],
            bykey["model-place"]["zodiac_sign_basis_context_id"],
        )
        orbital = copy.deepcopy(batch)
        orbital["assertions"] = orbital["assertions"][:1]
        orbital["assertions"][0].update(
            quantity="orbital_longitude", role="calculation_intermediate"
        )
        orbital_row = self.module().compile_catalogue([orbital], {10: text}, spans)["assertions"][0]
        self.assertEqual(orbital_row["normalized"]["zodiac_longitude_degrees"], "595/4")
        for source_name in ("Scorpio", "Scorpius"):
            with self.subTest(source_name=source_name):
                named = copy.deepcopy(batch)
                named_text = text.replace("♌", source_name)
                named["edition_sha256"] = hashlib.sha256(named_text.encode()).hexdigest()
                named["interval_sha256"] = hashlib.sha256(
                    named_text.rstrip("\n").encode()
                ).hexdigest()
                frame = named["contexts"][0]["value"]
                frame.update(zodiac_sign="Scorpio", source_expression=source_name)
                for assertion in named["assertions"]:
                    assertion["zodiac_sign"] = "Scorpio"
                named_spans = [dict(s, edition_sha256=named["edition_sha256"]) for s in spans]
                rows = self.module().compile_catalogue([named], {10: named_text}, named_spans)
                prose = next(row for row in rows["assertions"] if row["key"] == "prose-position")
                self.assertEqual(prose["normalized"]["zodiac_sign"], "Scorpio")
                self.assertEqual(prose["normalized"]["zodiac_longitude_degrees"], "955/4")
        for change in (
            "wrong-subject",
            "wrong-sign",
            "outside-scope",
            "missing-binding",
            "missing-glyph",
            "heading",
        ):
            bad = copy.deepcopy(batch)
            modified = text
            value = bad["contexts"][0]["value"]
            if change == "wrong-subject":
                value["subject"] = "Venus"
            elif change == "wrong-sign":
                value["zodiac_sign"] = "Aries"
            elif change == "outside-scope":
                value["line_end"] = 2
            elif change == "missing-binding":
                bad["assertions"][0]["context_keys"] = []
            elif change == "missing-glyph":
                value["source_expression"] = "28° 45′"
            else:
                modified = text.replace("| Observation | 28 50 |", "### A new report")
                bad["assertions"].pop(1)
                bad["edition_sha256"] = hashlib.sha256(modified.encode()).hexdigest()
                bad["interval_sha256"] = hashlib.sha256(modified.rstrip("\n").encode()).hexdigest()
            bad_spans = [dict(s, edition_sha256=bad["edition_sha256"]) for s in spans]
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {10: modified}, bad_spans)

    def direction_review_fixture(self):
        text = "Latitudo 3 50 51 S.\nLatitudo 3 37 15\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="latitude-span", volume=13, edition_sha256=sha, line_start=1, line_end=2)
        base = dict(
            id="latitude-source",
            volume=13,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=224, witness_sha256=sha),
            contexts=[],
            events=[],
            derivations=[],
            span_decisions=[
                dict(span_id=span["id"], decision="include", reason="Reviewed latitude column")
            ],
            assertions=[],
        )
        for line, expression, minute, second in [
            (1, "3 50 51 S.", "50", "51"),
            (2, "3 37 15", "37", "15"),
        ]:
            base["assertions"].append(
                dict(
                    key="latitude-" + str(line),
                    line=line,
                    column=2,
                    span_id=span["id"],
                    source_expression=expression,
                    quantity="ecliptic_latitude",
                    role="reduction",
                    subject="Mars",
                    reference=None,
                    direction="south",
                    components=dict(degree="3", arcminute=minute, arcsecond=second),
                    unit_basis="Reviewed D/M/S latitude column",
                    context_keys=[],
                    flags=["hemisphere_inherited"] if line == 2 else [],
                )
            )
        correction = dict(
            base, id="z-direction-review", assertions=[], span_decisions=[], direction_reviews=[]
        )
        for line in (1, 2):
            entry = dict(
                key="review-" + str(line),
                target_ref=dict(
                    review_id=base["id"],
                    key="latitude-" + str(line),
                    basis="Reviewed Latin abbreviation",
                ),
                expected_direction="south",
                direction="north",
                source_label="S.",
                source_expansion="septentrionalis",
                reason="Latin source context, not an English direction abbreviation",
            )
            if line == 2:
                entry["source_label_ref"] = dict(
                    review_id=base["id"], key="latitude-1", basis="Same latitude column"
                )
            correction["direction_reviews"].append(entry)
        return text, [span], base, correction

    def test_reviewed_direction_changes_preserve_source_ids_magnitudes_and_history(self):
        text, spans, base, correction = self.direction_review_fixture()
        before = self.module().compile_catalogue([base], {13: text}, spans)
        after = self.module().compile_catalogue([base, correction], {13: text}, spans)
        self.assertEqual(after["summary"]["source_assertions"], 2)
        self.assertEqual(after["summary"]["inspected_candidate_spans"], 1)
        self.assertEqual(after["summary"]["inspected_source_lines"], 2)
        for old, new in zip(before["assertions"], after["assertions"], strict=True):
            self.assertEqual(
                (new["id"], new["components"], new["source_expression"]),
                (old["id"], old["components"], old["source_expression"]),
            )
            self.assertEqual(new["normalized"]["magnitude"], old["normalized"]["magnitude"])
            self.assertEqual(new["direction"], "north")
            self.assertEqual(new["normalized"]["signed_magnitude"], new["normalized"]["magnitude"])
            history = new["direction_review_history"][0]
            self.assertEqual(history["previous_normalized"], old["normalized"])
            self.assertEqual(history["old_direction"], "south")
            self.assertEqual(history["review_id"], correction["id"])
        self.assertTrue(all(a["direction"] == "south" for a in base["assertions"]))

    def test_direction_review_rejects_wrong_prior_direction_or_unbound_label(self):
        text, spans, base, correction = self.direction_review_fixture()
        for changes in [
            dict(expected_direction="north"),
            dict(source_label="N."),
            dict(source_expansion="meridionalis"),
            dict(reason=""),
            dict(source_label_ref=dict(review_id="missing", key="latitude-1", basis="unbound")),
        ]:
            changed = copy.deepcopy(correction)
            changed["direction_reviews"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().compile_catalogue([base, changed], {13: text}, spans)
        changed = copy.deepcopy(base)
        changed["assertions"][1]["column"] = 3
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([changed, correction], {13: text}, spans)

    def module(self):
        try:
            return importlib.import_module("src.catalog")
        except ModuleNotFoundError:
            self.fail("Reviewed catalogue compiler is not implemented")

    def fixture(self):
        text = "21 January\nMars to star A\n6 22 — 37 37¾\nRegulus H. 8 M. 22; Decl. Mars 17 20¼\nTransit 6 56⅔; expected 7 14½\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [
            dict(id="s1", volume=10, edition_sha256=sha, line_start=2, line_end=3),
            dict(id="s2", volume=10, edition_sha256=sha, line_start=4, line_end=4),
            dict(id="s3", volume=10, edition_sha256=sha, line_start=5, line_end=5),
        ]
        batch = dict(
            id="review-1",
            volume=10,
            edition_sha256=sha,
            line_start=2,
            line_end=5,
            interval_sha256=hashlib.sha256("\n".join(text.splitlines()[1:5]).encode()).hexdigest(),
            basis=dict(kind="scan_review", printed_page=385, witness_sha256="a" * 64),
            span_decisions=[
                dict(span_id=s["id"], decision="include", reason="label and columns inspected")
                for s in spans
            ],
            contexts=[
                dict(
                    key="date",
                    kind="recorded_date",
                    lines=[1],
                    value="21 January",
                    calendar=None,
                    day_origin=None,
                )
            ],
            events=[dict(key="pointing", line=4, context_keys=["date"], clock_key=None)],
            assertions=[
                dict(
                    key="decl",
                    line=4,
                    span_id="s2",
                    source_expression="17 20¼",
                    quantity="declination",
                    role="recorded_coordinate",
                    subject="Mars",
                    reference=None,
                    components={"degree": "17", "arcminute": "20¼"},
                    unit_basis="declination columns",
                    event_key="pointing",
                    context_keys=["date"],
                    direction=None,
                    flags=["hemisphere_unspecified"],
                ),
                dict(
                    key="ha",
                    line=4,
                    span_id="s2",
                    source_expression="H. 8 M. 22",
                    quantity="hour_angle",
                    role="calibration",
                    subject="Regulus",
                    reference="meridian",
                    components={"hour": "8", "minute": "22"},
                    unit_basis="H. M.",
                    direction="east",
                ),
            ],
        )
        return text, spans, batch

    def test_non_observational_exclusions_need_no_invented_printed_page(self):
        text, spans, batch = self.fixture()
        batch.update(assertions=[], events=[], contexts=[])
        batch["basis"] = dict(
            kind="final_edition_review", printed_page=None, non_observational_exclusion=True
        )
        for decision in batch["span_decisions"]:
            decision.update(decision="exclude", reason="Reviewed non-observational material")
        result = self.module().compile_catalogue([batch], {10: text}, spans)
        self.assertEqual(result["summary"]["source_assertions"], 0)
        self.assertEqual(result["summary"]["inspected_candidate_spans"], 3)
        self.assertIsNone(result["coverage"][0]["basis"]["printed_page"])
        for changes in (
            dict(assertions=self.fixture()[2]["assertions"]),
            dict(events=self.fixture()[2]["events"]),
            dict(span_decisions=[dict(span_id="s1", decision="include", reason="Measurement")]),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().compile_catalogue([dict(batch, **changes)], {10: text}, spans)
        for basis in (
            dict(kind="scan_review", non_observational_exclusion=True),
            dict(kind="final_edition_review"),
        ):
            with self.subTest(basis=basis), self.assertRaises(ValueError):
                self.module().compile_catalogue([dict(batch, basis=basis)], {10: text}, spans)

    def test_unpaged_edition_annotations_require_literal_attachment_evidence(self):
        text, spans, batch = self.fixture()
        text = "A reading[^ed1]\n[^ed1]: Printed without a hemisphere.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        batch.update(
            edition_sha256=sha,
            line_start=2,
            line_end=2,
            interval_sha256=hashlib.sha256(text.splitlines()[1].encode()).hexdigest(),
            assertions=[],
            events=[],
            basis=dict(kind="final_edition_review", printed_page=None, edition_annotations=True),
            span_decisions=[dict(span_id="annotation", decision="context", reason="Edition note")],
            contexts=[
                dict(
                    key="note",
                    kind="source_observation_context",
                    lines=[1, 2],
                    value=dict(
                        record_type="edition_annotation",
                        note_marker="[^ed1]",
                        definition_line=2,
                        attachment_lines=[1],
                        summary="Hemisphere absent; no direction supplied.",
                    ),
                )
            ],
        )
        spans = [dict(id="annotation", volume=10, edition_sha256=sha, line_start=2, line_end=2)]
        result = self.module().compile_catalogue([batch], {10: text}, spans)
        self.assertEqual(len(result["contexts"]), 1)
        self.assertEqual(result["assertions"], [])
        for field, value in (
            ("note_marker", "[^ed2]"),
            ("attachment_lines", [2]),
            ("definition_line", 1),
            ("record_type", "observation"),
        ):
            bad = copy.deepcopy(batch)
            bad["contexts"][0]["value"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {10: text}, spans)
        for field in ("assertions", "events"):
            bad = copy.deepcopy(batch)
            bad[field] = self.fixture()[2][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {10: text}, spans)

    def numeric_endnote_fixture(self):
        text = "12° 30′[^ed1]\n[^ed1]: Another copy reads 12° 31′.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [
            dict(id="reading", volume=10, edition_sha256=sha, line_start=1, line_end=1),
            dict(id="note", volume=10, edition_sha256=sha, line_start=2, line_end=2),
        ]
        common = dict(volume=10, edition_sha256=sha, events=[])
        target = dict(
            key="angle",
            line=1,
            span_id="reading",
            source_expression="12° 30′",
            quantity="calculation_angle",
            subject="Mars",
            reference=None,
            direction=None,
            role="historical_input",
            components={"degree": "12", "arcminute": "30"},
            unit_basis="Printed angular units",
            context_keys=[],
            flags=["not_an_additional_raw_reading"],
        )
        parent = dict(
            common,
            id="base",
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.splitlines()[0].encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=10),
            contexts=[],
            assertions=[target],
            span_decisions=[dict(span_id="reading", decision="include", reason="Original")],
        )
        note = dict(
            common,
            id="note",
            line_start=2,
            line_end=2,
            interval_sha256=hashlib.sha256(text.splitlines()[1].encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=None, edition_annotations=True),
            contexts=[
                dict(
                    key="note",
                    kind="source_observation_context",
                    lines=[1, 2],
                    value=dict(
                        record_type="edition_annotation",
                        note_marker="[^ed1]",
                        definition_line=2,
                        attachment_lines=[1],
                        correction_applied=False,
                    ),
                )
            ],
            span_decisions=[dict(span_id="note", decision="context", reason="Edition annotation")],
            assertions=[
                dict(
                    target,
                    key="alternative",
                    line=2,
                    span_id="note",
                    source_expression="12° 31′",
                    role="editorial_variant",
                    components={"degree": "12", "arcminute": "31"},
                    context_keys=["note"],
                    annotation_of_ref=dict(
                        review_id="base", key="angle", basis="Literal footnote attachment"
                    ),
                    flags=[
                        "not_an_additional_raw_reading",
                        "source_annotation_variant",
                        "alternative_suggestion_not_applied",
                    ],
                )
            ],
        )
        return text, spans, parent, note

    def test_numeric_endnote_uses_marker_without_inventing_page_or_changing_original(self):
        from src.public_assertions import public_assertion

        text, spans, parent, note = self.numeric_endnote_fixture()
        before = self.module().compile_catalogue([parent], {10: text}, spans)["assertions"][0]
        result = self.module().compile_catalogue([parent, note], {10: text}, spans)
        original = next(r for r in result["assertions"] if r["id"] == before["id"])
        alternative = next(r for r in result["assertions"] if r["role"] == "editorial_variant")
        self.assertEqual(original, before)
        self.assertIsNone(alternative["printed_page"])
        self.assertEqual(alternative["edition_note_marker"], "[^ed1]")
        self.assertEqual(alternative.get("locator"), "[^ed1]")
        self.assertEqual(alternative["annotation_of_id"], original["id"])
        public = public_assertion(alternative)
        self.assertEqual(public["edition_note_marker"], "[^ed1]")
        self.assertEqual(public["normalized"]["magnitude"], "45060")
        self.assertIsNone(public["event_id"])
        self.assertEqual(result["events"], [])

    def test_numeric_endnote_rejects_unbound_or_non_editorial_values(self):
        text, spans, parent, note = self.numeric_endnote_fixture()
        for changes in (
            dict(role="recorded_reading"),
            dict(context_keys=[]),
            dict(flags=[]),
            dict(annotation_of_ref=None),
            dict(edition_note_marker="[^invented]"),
            dict(annotation_of_ref=dict(review_id="base", key="missing", basis="Unbound")),
        ):
            bad = copy.deepcopy(note)
            bad["assertions"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().compile_catalogue([parent, bad], {10: text}, spans)
        for changes in (dict(note_marker="[^ed2]"), dict(attachment_lines=[2])):
            bad = copy.deepcopy(note)
            bad["contexts"][0]["value"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().compile_catalogue([parent, bad], {10: text}, spans)

    def test_annotation_attachment_citation_requires_bound_note_and_attachment(self):
        text, spans, parent, note = self.numeric_endnote_fixture()
        citation = copy.deepcopy(note)
        citation.update(id="zz-citation", assertions=[])
        entry = dict(review_id="note", context_key="note", line=1, printed_page=10)
        citation["basis"]["annotation_attachment_citations"] = [entry]
        self.module().compile_catalogue([parent, note, citation], {10: text}, spans)
        for changes in (
            dict(review_id="missing"),
            dict(context_key="missing"),
            dict(line=2),
            dict(printed_page=None),
            dict(printed_page=True),
        ):
            bad = copy.deepcopy(citation)
            bad["basis"]["annotation_attachment_citations"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().compile_catalogue([parent, note, bad], {10: text}, spans)
        for changes in (dict(edition_annotations=False), dict(printed_page=10)):
            bad = copy.deepcopy(citation)
            bad["basis"].update(changes)
            with self.subTest(basis=changes), self.assertRaises(ValueError):
                self.module().compile_catalogue([parent, note, bad], {10: text}, spans)

    def test_supplement_reuses_prior_event_without_duplicating_it(self):
        text, spans, first = self.fixture()
        first["events"][0]["subject"] = "Mars"
        second = copy.deepcopy(first)
        first["assertions"] = []
        second.update(id="supplement", events=[])
        second["assertions"] = second["assertions"][:1]
        row = second["assertions"][0]
        row.pop("event_key")
        row["event_ref"] = dict(review_id="review-1", key="pointing", basis="Same source session")
        result = self.module().compile_catalogue([first, second], {10: text}, spans)
        self.assertEqual(len(result["events"]), 1)
        self.assertEqual(result["assertions"][0]["event_id"], result["events"][0]["id"])
        for field, value in (("review_id", "missing"), ("key", "missing"), ("basis", "")):
            bad = copy.deepcopy(second)
            bad["assertions"][0]["event_ref"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.module().compile_catalogue([first, bad], {10: text}, spans)
        bad = copy.deepcopy(second)
        bad["assertions"][0]["subject"] = "Jupiter"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([first, bad], {10: text}, spans)
        bad = copy.deepcopy(second)
        bad["assertions"][0]["event_key"] = "pointing"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([first, bad], {10: text}, spans)

    def test_supplementary_clocks_fill_only_explicit_empty_point_links(self):
        text, spans, second = self.explicit_clock_case("3^h^", {"hour": "3"})
        first = copy.deepcopy(second)
        first.update(
            id="a-group", assertions=[], events=[dict(key="session", line=1, subject="Mars")]
        )
        row = second["assertions"][0]
        row.update(
            quantity="recorded_clock",
            role="recorded_clock",
            direction=None,
            flags=["absolute_time_unestablished"],
            event_clock_ref=dict(
                review_id="a-group", key="session", basis="Clock in the same source statement"
            ),
        )
        for kind in ("point", "interval_lower", "interval_upper"):
            row["clock_association_kind"] = kind
            out = self.module().compile_catalogue([first, second], {10: text}, spans)
            self.assertEqual(len(out["events"]), 1)
            self.assertEqual(out["assertions"][0]["event_id"], out["events"][0]["id"])
            self.assertEqual(
                out["events"][0]["clock_assertion_id"],
                out["assertions"][0]["id"] if kind == "point" else None,
            )
        row["clock_association_kind"] = "point"
        occupied = copy.deepcopy(first)
        old = copy.deepcopy(row)
        old.pop("event_clock_ref")
        old.pop("clock_association_kind")
        old["key"] = "old-clock"
        occupied["assertions"] = [old]
        occupied["events"][0]["clock_key"] = "old-clock"
        with self.assertRaises(ValueError):
            self.module().compile_catalogue([occupied, second], {10: text}, spans)
        for change in (
            dict(quantity="calculation_epoch"),
            dict(clock_association_kind="guessed"),
            dict(subject="Mars"),
            dict(flags=["clock_association_unresolved"]),
        ):
            bad = copy.deepcopy(second)
            bad["assertions"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().compile_catalogue([first, bad], {10: text}, spans)

    def test_native_eclipse_points_keep_sexagesimal_minutes_out_of_angles(self):
        from src.public_assertions import public_assertion

        for expression, points, minutes, expected in (
            ("6 points 34′", "6", "34", "197/30"),
            ("13 points 27′", "13", "27", "269/20"),
        ):
            text, spans, batch = self.explicit_clock_case(
                expression, {"point": points, "point_minute": minutes}
            )
            row = batch["assertions"][0]
            row.update(
                quantity="eclipse_extent",
                role="historical_prediction",
                subject="Moon",
                reference=None,
                direction=None,
                model_name="Alphonsine",
                flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
            )
            compiled = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
            public = public_assertion(compiled)
            self.assertEqual(public["normalized"]["magnitude"], expected)
            self.assertEqual(public["normalized"]["unit"], "source_eclipse_point")
            self.assertIsNone(public["normalized"]["magnitude_degrees"])
            bad = copy.deepcopy(compiled)
            bad["normalized"]["magnitude"] = "999"
            with self.assertRaises(ValueError):
                public_assertion(bad)
            for change in (
                dict(components={"point": minutes, "point_minute": points}),
                dict(components={"degree": points, "arcminute": minutes}),
                dict(
                    source_expression="6 points 60′",
                    components={"point": "6", "point_minute": "60"},
                ),
                dict(source_expression="6 points 34″"),
            ):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    self.module().normalize_quantity(dict(row, **change))

    def test_known_angle_does_not_require_an_invented_measurement_type(self):
        row = dict(
            quantity="unclassified_angle",
            role="recorded_reading",
            direction=None,
            flags=["measurement_type_unresolved"],
            components={"degree": "30", "arcminute": "6"},
        )
        result = self.module().normalize_quantity(row)
        self.assertEqual(
            (result["status"], result["unit"], result["magnitude"]),
            ("exact", "arcsecond", "108360"),
        )
        self.assertIsNone(result["signed_magnitude"])

    def test_visual_separation_ratio_and_worded_duration_remain_distinct(self):
        text = "three or four hours before sunrise; about double the distance; latitude none\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="visual", volume=13, edition_sha256=sha, line_start=1, line_end=1)
        batch = dict(
            id="visual-estimate",
            volume=13,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=178),
            span_decisions=[dict(span_id="visual", decision="include", reason="Visual estimate")],
            assertions=[],
        )
        for key, word, value, quantity, components in (
            ("early", "three", "3", "clock_elapsed_time", {"hour": "3"}),
            ("late", "four", "4", "clock_elapsed_time", {"hour": "4"}),
            ("ratio", "double", "2", "separation_ratio", {"ratio": "2"}),
            ("latitude", "none", "0", "latitude_difference", {"arcminute": "0"}),
        ):
            batch["assertions"].append(
                dict(
                    key=key,
                    line=1,
                    span_id="visual",
                    source_expression=word,
                    quantity=quantity,
                    role="recorded_reading",
                    subject="Mars",
                    reference=None,
                    components=components,
                    source_word_numbers={word: value},
                    unit_basis="Reviewed source wording",
                )
            )
        rows = {
            a["key"]: a
            for a in self.module().compile_catalogue([batch], {13: text}, [span])["assertions"]
        }
        self.assertEqual(
            [rows[k]["normalized"]["magnitude"] for k in ("early", "late", "ratio")],
            ["10800", "14400", "2"],
        )
        self.assertEqual(rows["ratio"]["normalized"]["unit"], "ratio")
        self.assertIsNone(rows["ratio"]["normalized"]["magnitude_degrees"])
        self.assertEqual(rows["latitude"]["normalized"]["magnitude"], "0")
        bad = copy.deepcopy(batch)
        bad["assertions"][2]["source_word_numbers"]["double"] = "3"
        with self.assertRaisesRegex(ValueError, "word number"):
            self.module().compile_catalogue([bad], {13: text}, [span])

    def test_final_edition_split_pages_does_not_require_image_locator(self):
        text, spans, batch = self.fixture()
        batch["basis"] = dict(
            kind="final_edition_review",
            printed_page=43,
            page_segments=[
                dict(
                    line_start=2,
                    line_end=3,
                    printed_page=43,
                    witness_sha256=batch["edition_sha256"],
                ),
                dict(
                    line_start=4,
                    line_end=5,
                    printed_page=44,
                    witness_sha256=batch["edition_sha256"],
                ),
            ],
        )
        batch["assertions"].append(
            dict(
                key="sep",
                line=3,
                span_id="s1",
                source_expression="37 37¾",
                quantity="angular_separation",
                role="recorded_reading",
                subject="Mars",
                reference="star A",
                components={"degree": "37", "arcminute": "37¾"},
                unit_basis="Source angular columns",
            )
        )
        result = self.module().compile_catalogue([batch], {10: text}, spans)
        self.assertEqual(
            {a["key"]: a["printed_page"] for a in result["assertions"]},
            {"decl": 44, "ha": 44, "sep": 43},
        )
        scan = copy.deepcopy(batch)
        scan["basis"]["kind"] = "scan_review"
        with self.assertRaisesRegex(ValueError, "page segment"):
            self.module().compile_catalogue([scan], {10: text}, spans)
        for invalid in (0, -1, "unknown", True):
            bad = copy.deepcopy(batch)
            bad["basis"]["page_segments"][0]["pdf_page"] = invalid
            with self.subTest(pdf_page=invalid), self.assertRaisesRegex(ValueError, "page segment"):
                self.module().compile_catalogue([bad], {10: text}, spans)

    def test_separation_with_explicitly_missing_star_keeps_tentative_proposal(self):
        text = "Distance to unnamed star\n18 26⅙\nName missing; probably bright Aries.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=13, edition_sha256=sha, line_start=1, line_end=3)]
        batch = dict(
            id="missing-reference",
            volume=13,
            edition_sha256=sha,
            line_start=1,
            line_end=3,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=44),
            span_decisions=[
                dict(span_id="s", decision="include", reason="Named absence and proposal reviewed")
            ],
            contexts=[
                dict(
                    key="note",
                    kind="source_observation_context",
                    lines=[3],
                    value="Tentative editorial proposal",
                )
            ],
            assertions=[
                dict(
                    key="distance",
                    line=2,
                    span_id="s",
                    source_expression="18 26⅙",
                    quantity="angular_separation",
                    role="recorded_reading",
                    subject="Mars",
                    reference=None,
                    source_reference_status="not_recorded",
                    editorial_reference_alternative="bright star of Aries",
                    editorial_reference_status="tentative",
                    components={"degree": "18", "arcminute": "26 1/6"},
                    unit_basis="Source distance columns",
                    context_keys=["note"],
                )
            ],
        )
        out = self.module().compile_catalogue([batch], {13: text}, spans)["assertions"][0]
        self.assertIsNone(out["reference"])
        self.assertEqual(out["editorial_reference_status"], "tentative")
        self.assertEqual(out["normalized"]["magnitude"], "66370")
        for changes in (
            {"source_reference_status": None},
            {"reference": "Aldebaran"},
            {"quantity": "declination"},
        ):
            bad = copy.deepcopy(batch)
            bad["assertions"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {13: text}, spans)
        unexplained = copy.deepcopy(batch)
        unexplained["assertions"][0].pop("source_reference_status")
        with self.assertRaisesRegex(ValueError, "both endpoints"):
            self.module().compile_catalogue([unexplained], {13: text}, spans)

    def test_exact_fractional_angles_and_recorded_precision(self):
        m = self.module()
        result = m.normalize_quantity(
            dict(quantity="angular_separation", components={"degree": "37", "arcminute": "37¾"})
        )
        self.assertEqual(result["magnitude"], "135465")
        self.assertEqual(result["magnitude_degrees"], "9031/240")
        self.assertEqual(result["least_component_unit"], "arcminute")
        self.assertEqual(result["status"], "exact")

    def explicit_clock_case(self, expression, components):
        text = expression + "\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=1)]
        batch = dict(
            id="clock-review",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(expression.encode()).hexdigest(),
            basis=dict(kind="scan_review", printed_page=1),
            span_decisions=[
                dict(
                    span_id="s",
                    decision="include",
                    reason="Explicit superscript time unit reviewed",
                )
            ],
            assertions=[
                dict(
                    key="adjustment",
                    line=1,
                    span_id="s",
                    source_expression=expression,
                    quantity="clock_correction",
                    role="historical_correction",
                    subject="observing clock",
                    reference=None,
                    components=components,
                    unit_basis="Explicit time unit",
                )
            ],
        )
        return text, spans, batch

    def test_explicit_time_unit_rejects_the_hours_for_minutes_import_error(self):
        text, spans, batch = self.explicit_clock_case("32^m^", {"hour": "32"})
        with self.assertRaisesRegex(ValueError, "explicit time unit"):
            self.module().compile_catalogue([batch], {10: text}, spans)

    def test_single_explicit_time_units_keep_minutes_seconds_and_fractional_hours(self):
        for expression, components, expected in [
            ("32^m^", {"minute": "32"}, "1920"),
            ("30^s^", {"second": "30"}, "30"),
            ("2⅔^h^", {"hour": "2⅔"}, "9600"),
        ]:
            with self.subTest(expression=expression):
                text, spans, batch = self.explicit_clock_case(expression, components)
                out = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                self.assertEqual(out["normalized"]["magnitude"], expected)

    def test_hour_angles_have_time_units_without_becoming_clocks(self):
        m = self.module()
        r = m.normalize_quantity(
            dict(quantity="hour_angle", components={"hour": "8", "minute": "22"}, direction="east")
        )
        self.assertEqual(r["magnitude"], "30120")
        self.assertEqual(r["unit"], "second_of_time")
        self.assertIsNone(r["signed_magnitude"])
        with self.assertRaises(ValueError):
            m.normalize_quantity(
                dict(quantity="declination", components={"hour": "8", "minute": "22"})
            )

    def test_fractional_word_minute_is_distinct_from_ordinal_third_hour(self):
        cases = [
            ("nineteen years", "nineteen", "19", "source_scalar", {"scalar": "19"}, "19"),
            (
                "two degrees less a quarter",
                "two degrees less a quarter",
                "1 3/4",
                "calculation_angle",
                {"degree": "1 3/4"},
                "6300",
            ),
            (
                "One third of one minute",
                "One third",
                "1/3",
                "calculation_angle",
                {"arcminute": "1/3"},
                "20",
            ),
            ("third hour", "third", "3", "calculation_epoch", {"hour": "3"}, "10800"),
            (
                "By the sixth hour it had already passed",
                "sixth",
                "6",
                "annotated_time",
                {"hour": "6"},
                "21600",
            ),
            (
                "nearer by a third",
                "by a third",
                "1/3",
                "source_fraction",
                {"fraction": "1/3"},
                "1/3",
            ),
            (
                "a sixth part of her diameter",
                "sixth part",
                "1/6",
                "source_fraction",
                {"fraction": "1/6"},
                "1/6",
            ),
            ("about eight days before", "eight", "8", "clock_elapsed_time", {"day": "8"}, "691200"),
            ("III degrees", "III", "3", "calculation_angle", {"degree": "3"}, "10800"),
            ("a degree", "a degree", "1", "calculation_angle", {"degree": "1"}, "3600"),
            (
                "half a degree",
                "half a degree",
                "1/2",
                "calculation_angle",
                {"degree": "1/2"},
                "1800",
            ),
            ("tenth hour after noon", "tenth", "10", "recorded_clock", {"hour": "10"}, "36000"),
            ("Half an hour", "Half", "1/2", "recorded_clock", {"hour": "1/2"}, "1800"),
            ("an hour", "an hour", "1", "recorded_clock", {"hour": "1"}, "3600"),
            ("An hour", "An hour", "1", "recorded_clock", {"hour": "1"}, "3600"),
            ("no latitude", "no latitude", "0", "ecliptic_latitude", {"degree": "0"}, "0"),
            (
                "without latitude",
                "without latitude",
                "0",
                "ecliptic_latitude",
                {"degree": "0"},
                "0",
            ),
            ("without altitude", "without altitude", "0", "altitude", {"degree": "0"}, "0"),
            (
                "about the ninth hour after noon",
                "ninth",
                "9",
                "recorded_clock",
                {"hour": "9"},
                "32400",
            ),
            (
                "exactly at the beginning of ♍",
                "exactly at the beginning",
                "0",
                "ecliptic_longitude",
                {"degree": "0"},
                "0",
            ),
        ]
        for text_value, expression, value, quantity, components, want in cases:
            with self.subTest(expression=expression):
                text, spans, batch = self.explicit_clock_case(text_value, components)
                row = batch["assertions"][0]
                row.update(
                    source_expression=expression,
                    quantity=quantity,
                    subject="Mars",
                    source_word_numbers={expression: value},
                    unit_basis="Printed fractional minute or ordinal hour",
                )
                if quantity == "annotated_time":
                    row.update(role="historical_input", flags=["source_upper_bound"])
                if quantity == "clock_elapsed_time":
                    row.update(role="recorded_reading", flags=["source_approximate"])
                if quantity == "recorded_clock":
                    row.update(role="recorded_clock", subject="observing clock")
                if quantity == "ecliptic_longitude":
                    row.update(source_expression=text_value, zodiac_sign="Virgo")
                out = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                self.assertEqual(out["normalized"]["magnitude"], want)
                if quantity == "ecliptic_longitude":
                    self.assertEqual(out["normalized"]["zodiac_longitude_degrees"], "150")
                    self.assertEqual(out["source_expression"], "exactly at the beginning of ♍")
                if quantity == "annotated_time":
                    self.assertEqual(out["source_expression"], "sixth")
                    self.assertIn("source_upper_bound", out["flags"])
                if quantity == "clock_elapsed_time":
                    self.assertEqual(out["normalized"]["unit"], "second_of_time")
                    self.assertIn("source_approximate", out["flags"])

    def test_worded_thirteenth_hour_and_quarter_preserves_fractional_clock(self):
        expression = "thirteenth hour and a quarter"
        text, spans, batch = self.explicit_clock_case(expression, {"hour": "13 1/4"})
        batch["assertions"][0].update(
            quantity="recorded_clock",
            role="recorded_clock",
            source_word_numbers={expression: "13 1/4"},
        )
        row = self.module().compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(row["source_expression"], expression)
        self.assertEqual(row["normalized"]["magnitude"], "47700")
        self.assertEqual(row["normalized"]["unit"], "second_of_time")
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["source_word_numbers"][expression] = "13"
        with self.assertRaisesRegex(ValueError, "word number"):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_incomplete_values_and_invalid_minutes_do_not_become_numbers(self):
        m = self.module()
        r = m.normalize_quantity(
            dict(quantity="declination", source_expression="17…", components=None, incomplete=True)
        )
        self.assertIsNone(r["magnitude"])
        self.assertEqual(r["status"], "incomplete")
        with self.assertRaises(ValueError):
            m.normalize_quantity(
                dict(quantity="altitude", components={"degree": "17", "arcminute": "62"})
            )
        with self.assertRaises(ValueError):
            m.normalize_quantity(
                dict(quantity="altitude", components={"degree": "-17", "arcminute": "20"})
            )

    def test_reviewed_declination_keeps_hour_angle_as_separate_assertion(self):
        text, spans, batch = self.fixture()
        r = self.module().compile_catalogue([batch], {10: text}, spans)
        decl = next(a for a in r["assertions"] if a["quantity"] == "declination")
        self.assertEqual(decl["normalized"]["magnitude"], "62415")
        self.assertIsNone(decl["normalized"]["signed_magnitude"])
        self.assertEqual(r["events"][0]["clock_assertion_id"], None)
        self.assertEqual(r["summary"]["inspected_candidate_spans"], 3)
        self.assertEqual(r["summary"]["inspected_source_lines"], 4)
        self.assertIsNone(r["summary"]["measurement_count"])
        self.assertEqual(decl["printed_page"], 385)
        self.assertEqual(len(decl["context_ids"]), 1)

    def test_unresolved_source_notation_keeps_angle_unit_without_fabricating_scalar(self):
        row = dict(
            quantity="altitude",
            source_expression="17 -20",
            components=None,
            flags=["source_notation_unresolved"],
        )
        out = self.module().normalize_quantity(row)
        self.assertEqual(
            (out["status"], out["unit"], out["normalization_issue"]),
            ("unsupported", "arcsecond", "source_notation_unresolved"),
        )
        for key in ("magnitude", "magnitude_degrees", "signed_magnitude", "least_component_unit"):
            self.assertIsNone(out[key])
        for changes in (
            dict(components={"degree": "17", "arcminute": "20"}),
            dict(quantity="recorded_clock"),
            dict(incomplete=True),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().normalize_quantity(dict(row, **changes))

    def test_unresolved_recorded_clock_keeps_source_wording_without_hour_conversion(self):
        row = dict(
            quantity="recorded_clock",
            role="recorded_clock",
            subject="observing clock",
            reference=None,
            source_expression="At the half of the ninth",
            components={},
            flags=["source_notation_unresolved", "absolute_time_unestablished"],
        )
        out = self.module().normalize_quantity(row)
        self.assertEqual(
            (out["status"], out["unit"], out["magnitude"]), ("unsupported", "second_of_time", None)
        )
        for changes in (
            dict(components={"hour": "8 1/2"}),
            dict(subject="Mars"),
            dict(reference="Aldebaran"),
            dict(role="calculation_epoch"),
            dict(direction="south"),
            dict(incomplete=True),
            dict(flags=["source_notation_unresolved"]),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().normalize_quantity(dict(row, **changes))

    def test_unresolved_calculation_epoch_keeps_time_unit_without_invented_minutes(self):
        row = dict(
            quantity="calculation_epoch", components={}, flags=["source_notation_unresolved"]
        )
        out = self.module().normalize_quantity(row)
        self.assertEqual(
            (out["status"], out["unit"], out["magnitude"]), ("unsupported", "second_of_time", None)
        )
        for changes in (
            dict(components={"hour": "9", "minute": "32"}),
            dict(quantity="recorded_clock"),
            dict(incomplete=True),
        ):
            with self.assertRaises(ValueError):
                self.module().normalize_quantity(dict(row, **changes))

    def test_unclassified_numeric_expression_does_not_choose_angular_or_time_units(self):
        row = dict(quantity="unclassified_numeric_expression", components={}, direction=None)
        out = self.module().normalize_quantity(row)
        self.assertEqual(
            (out["status"], out["unit"], out["magnitude"]),
            ("unsupported", "source_numeric_expression", None),
        )
        self.assertEqual(out["normalization_issue"], "physical_quantity_or_units_unresolved")
        for changes in (
            dict(components={"arcminute": "14", "arcsecond": "40"}),
            dict(incomplete=True),
            dict(direction="north"),
        ):
            with self.assertRaises(ValueError):
                self.module().normalize_quantity(dict(row, **changes))

    def test_worded_quarter_hour_links_to_earlier_observations_without_a_clock(self):
        text = "Mars 18°39′\nabout a quarter of an hour after the preceding observations"
        sha = hashlib.sha256(text.encode()).hexdigest()
        batch = dict(
            id="relative-series",
            volume=13,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            interval_sha256=sha,
            basis=dict(kind="final_edition_review", printed_page=222),
            span_decisions=[
                dict(span_id="s", decision="include", reason="Source interval reviewed")
            ],
            events=[
                dict(key="earlier", line=1, clock_key=None),
                dict(key="later", line=2, clock_key=None),
            ],
            assertions=[
                dict(
                    key="distance",
                    line=1,
                    span_id="s",
                    source_expression="18°39′",
                    quantity="angular_separation",
                    subject="Mars",
                    reference="Regulus",
                    role="recorded_reading",
                    components={"degree": "18", "arcminute": "39"},
                    unit_basis="Source units",
                    event_key="earlier",
                ),
                dict(
                    key="duration",
                    line=2,
                    span_id="s",
                    source_expression="about a quarter of an hour",
                    quantity="clock_elapsed_time",
                    subject="Mars",
                    reference=None,
                    role="recorded_reading",
                    components={"hour": "1/4"},
                    source_word_numbers={"quarter": "1/4"},
                    unit_basis="Source quarter hour",
                    event_key="later",
                    source_time_anchor_event_key="earlier",
                    time_reference="elapsed_after_prior_observations",
                    flags=["source_approximate"],
                ),
            ],
        )
        spans = [dict(id="s", volume=13, edition_sha256=sha, line_start=1, line_end=2)]
        out = self.module().compile_catalogue([batch], {13: text}, spans)
        duration = next(a for a in out["assertions"] if a["key"] == "duration")
        earlier = next(e for e in out["events"] if e["key"] == "earlier")
        self.assertEqual(duration["normalized"]["magnitude"], "900")
        self.assertEqual(duration["source_time_anchor_event_id"], earlier["id"])
        for target in ("missing", "later"):
            bad = copy.deepcopy(batch)
            bad["assertions"][1]["source_time_anchor_event_key"] = target
            with self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {13: text}, spans)

    def test_explicit_zodiac_frame_sum_preserves_named_sign_and_other_operations(self):
        from src.public_checkpoint import public_derivation

        text = "3 6 46 4\n3 18 39\n28 15 5\n♌ 8 19 48"
        sha = hashlib.sha256(text.encode()).hexdigest()
        parts = [
            {"sign_count": "3", "degree": "6", "arcminute": "46", "arcsecond": "4"},
            {"degree": "3", "arcminute": "18", "arcsecond": "39"},
            {"degree": "28", "arcminute": "15", "arcsecond": "5"},
            {"degree": "8", "arcminute": "19", "arcsecond": "48"},
        ]
        assertions = [
            dict(
                key=str(i),
                line=i + 1,
                span_id="s",
                source_expression=line,
                quantity="ecliptic_longitude" if i == 3 else "calculation_angle",
                subject="Mars",
                reference=None,
                role="reduction",
                components=parts[i],
                unit_basis="Explicit source angular columns",
                **({"zodiac_sign": "Leo"} if i == 3 else {}),
            )
            for i, line in enumerate(text.splitlines())
        ]
        batch = dict(
            id="zodiac-sum",
            volume=13,
            edition_sha256=sha,
            line_start=1,
            line_end=4,
            interval_sha256=sha,
            basis=dict(kind="final_edition_review", printed_page=221),
            span_decisions=[dict(span_id="s", decision="include", reason="Source sum")],
            assertions=assertions,
            derivations=[
                dict(
                    key="sum",
                    operation="sum_modulo_360_in_zodiac_frame",
                    input_keys=["0", "1", "2"],
                    output_key="3",
                )
            ],
        )
        spans = [dict(id="s", volume=13, edition_sha256=sha, line_start=1, line_end=4)]
        out = self.module().compile_catalogue([batch], {13: text}, spans)
        d = out["derivations"][0]
        index = {a["id"]: a for a in out["assertions"]}
        self.assertEqual((d["computed_magnitude"], d["arithmetic_agrees"]), ("461988", True))
        self.assertEqual(index[d["output_id"]]["normalized"]["magnitude"], "29988")
        self.assertEqual(public_derivation(d, index)["arithmetic_frame"], "zodiac_zero")
        batch["derivations"][0]["operation"] = "sum_modulo_360_degrees"
        old = self.module().compile_catalogue([batch], {13: text}, spans)["derivations"][0]
        self.assertFalse(old["arithmetic_agrees"])
        bad = copy.deepcopy(index)
        bad[d["output_id"]]["normalized"]["unit"] = "second_of_time"
        with self.assertRaises(ValueError):
            public_derivation(d, bad)

    def test_zodiac_difference_checks_cross_sign_distances_without_correcting_source(self):
        from src.public_checkpoint import public_derivation

        for left, right, reported, expected, agrees in (
            ("13 28 ♋", "24 6 ♊", "19 22", "69720", True),
            ("29 58 ♋", "11 57 ♋", "18 0", "64860", False),
        ):
            text = "\n".join((left, right, reported))
            sha = hashlib.sha256(text.encode()).hexdigest()
            parts = [left.split(), right.split(), reported.split()]
            assertions = [
                dict(
                    key=str(i),
                    line=i + 1,
                    span_id="s",
                    source_expression=expression,
                    quantity="ecliptic_longitude" if i < 2 else "angular_separation",
                    subject="Mars",
                    reference=None if i < 2 else "Venus",
                    role="reduction",
                    components={"degree": parts[i][0], "arcminute": parts[i][1]},
                    unit_basis="Printed source degrees/minutes",
                    **(
                        {"zodiac_sign": "Cancer" if parts[i][2] == "♋" else "Gemini"}
                        if i < 2
                        else {}
                    ),
                )
                for i, expression in enumerate(text.splitlines())
            ]
            batch = dict(
                id="zodiac-difference",
                volume=10,
                edition_sha256=sha,
                line_start=1,
                line_end=3,
                interval_sha256=sha,
                basis=dict(kind="final_edition_review", printed_page=5),
                span_decisions=[dict(span_id="s", decision="include", reason="Source arithmetic")],
                assertions=assertions,
                derivations=[
                    dict(
                        key="difference",
                        operation="difference_modulo_360_in_zodiac_frame",
                        input_keys=["0", "1"],
                        output_key="2",
                    )
                ],
            )
            spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=3)]
            out = self.module().compile_catalogue([batch], {10: text}, spans)
            d = out["derivations"][0]
            self.assertEqual((d["computed_magnitude"], d["arithmetic_agrees"]), (expected, agrees))
            index = {a["id"]: a for a in out["assertions"]}
            self.assertEqual(public_derivation(d, index)["arithmetic_frame"], "zodiac_zero")
            self.assertEqual(index[d["output_id"]]["source_expression"], reported)
            bad = copy.deepcopy(batch)
            bad["derivations"][0]["input_keys"] = ["0", "1", "0"]
            with self.assertRaisesRegex(ValueError, "two ordered inputs"):
                self.module().compile_catalogue([bad], {10: text}, spans)

    def test_source_and_review_scope_are_bound_to_current_edition(self):
        text, spans, batch = self.fixture()
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            self.module().compile_catalogue([batch], {10: text + "changed"}, spans)
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["source_expression"] = "17 21¼"
        with self.assertRaisesRegex(ValueError, "expression"):
            self.module().compile_catalogue([bad], {10: text}, spans)
        bad = copy.deepcopy(batch)
        bad["assertions"][0]["components"]["arcminute"] = "21¼"
        with self.assertRaisesRegex(ValueError, "[Cc]omponent"):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_component_map_order_cannot_change_sexagesimal_interpretation(self):
        text, spans, batch = self.fixture()
        batch["assertions"][0]["components"] = {"arcminute": "20¼", "degree": "17"}
        result = self.module().compile_catalogue([batch], {10: text}, spans)
        self.assertEqual(
            next(a for a in result["assertions"] if a["key"] == "decl")["normalized"]["magnitude"],
            "62415",
        )

    def test_component_binding_does_not_drop_a_printed_fraction(self):
        text, spans, batch = self.fixture()
        batch["assertions"][0]["components"]["arcminute"] = "20"
        with self.assertRaisesRegex(ValueError, "[Cc]omponent"):
            self.module().compile_catalogue([batch], {10: text}, spans)

    def test_excluded_span_cannot_supply_a_normalized_reading(self):
        text, spans, batch = self.fixture()
        batch["span_decisions"][1]["decision"] = "exclude"
        with self.assertRaisesRegex(ValueError, "relevant inspected"):
            self.module().compile_catalogue([batch], {10: text}, spans)

    def variant_fixture(self):
        text = "3 2⅔ — I\nfor minutes read 3²⁄₈\nadopt at 6¾: 2 47½\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="v", volume=10, edition_sha256=sha, line_start=1, line_end=3)]
        raw = dict(
            key="raw",
            line=1,
            span_id="v",
            source_expression="3 2⅔",
            quantity="angular_separation",
            role="repeated_reading",
            subject="Mars",
            reference="Leo neck star",
            components={"degree": "3", "arcminute": "2⅔"},
            unit_basis="angular columns",
            series_key="series",
            ordinal=1,
            ordinal_original="I",
        )
        corrected = dict(
            raw,
            key="corrected",
            line=2,
            source_expression="3²⁄₈",
            role="printed_correction",
            components={"degree": "3", "arcminute": "3²⁄₈"},
            variant_of_key="raw",
            inherited_components={"degree": "raw"},
        )
        corrected.pop("series_key")
        corrected.pop("ordinal")
        corrected.pop("ordinal_original")
        epoch = dict(
            key="epoch",
            line=3,
            span_id="v",
            source_expression="6¾",
            quantity="calculation_epoch",
            role="calculation_epoch",
            subject="adoption epoch",
            components={"hour": "6¾"},
            unit_basis="at hour",
        )
        batch = dict(
            id="variant-review",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=3,
            interval_sha256=hashlib.sha256("\n".join(text.splitlines()).encode()).hexdigest(),
            basis=dict(kind="edition_and_scan_review", printed_page=385),
            span_decisions=[
                dict(span_id="v", decision="include", reason="labels and variants checked")
            ],
            contexts=[dict(key="series", kind="repeated_series", lines=[1], value="first series")],
            assertions=[raw, corrected, epoch],
            events=[dict(key="adoption", line=3, clock_key=None, epoch_key="epoch")],
        )
        return text, spans, batch

    def test_explicit_same_amount_links_a_separation_without_inventing_components(self):
        text = "Mars from first star 9° 24′; from second star the same amount.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=13, edition_sha256=sha, line_start=1, line_end=1)]
        first = dict(
            key="first",
            line=1,
            span_id="s",
            source_expression="9° 24′",
            quantity="angular_separation",
            role="recorded_reading",
            subject="Mars",
            reference="southern head of Gemini",
            components={"degree": "9", "arcminute": "24"},
            unit_basis="Explicit D/M",
            context_keys=["relation"],
        )
        second = dict(
            first,
            key="second",
            source_expression="the same amount",
            reference="upper head of Gemini",
            components={},
            source_value_equal_to_key="first",
            flags=["source_value_stated_equal"],
        )
        batch = dict(
            id="same-amount",
            volume=13,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=151),
            span_decisions=[
                dict(span_id="s", decision="include", reason="Explicit equality reviewed")
            ],
            contexts=[
                dict(
                    key="relation",
                    kind="source_observation_context",
                    lines=[1],
                    value="Second distance stated equal",
                )
            ],
            assertions=[first, second],
        )
        result = self.module().compile_catalogue([batch], {13: text}, spans)
        bykey = {a["key"]: a for a in result["assertions"]}
        self.assertEqual(bykey["second"]["normalized"]["magnitude"], "33840")
        self.assertEqual(bykey["second"]["components"], {})
        self.assertEqual(bykey["second"]["source_expression"], "the same amount")
        self.assertEqual(bykey["second"]["source_value_equal_to_id"], bykey["first"]["id"])
        from src.public_assertions import public_assertion

        projected = public_assertion(bykey["second"])
        self.assertEqual(projected["normalized"]["magnitude"], "33840")
        self.assertEqual(projected["source_value_equal_to_id"], bykey["first"]["id"])
        for changes in (
            dict(components={"degree": "9", "arcminute": "24"}),
            dict(flags=[]),
            dict(source_value_equal_to_key="second"),
            dict(context_keys=[]),
        ):
            bad = copy.deepcopy(batch)
            bad["assertions"][1].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().compile_catalogue([bad], {13: text}, spans)

    def test_same_interval_wording_preserves_a_linked_value_without_components(self):
        text = "Comet from the second star 3° 40′; the sixth star by the same interval.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=13, edition_sha256=sha, line_start=1, line_end=1)]
        first = dict(
            key="first",
            line=1,
            span_id="s",
            source_expression="3° 40′",
            quantity="angular_separation",
            role="recorded_reading",
            subject="comet head",
            reference="second star in head of Fish",
            components={"degree": "3", "arcminute": "40"},
            unit_basis="Explicit D/M",
            context_keys=["relation"],
        )
        second = dict(
            first,
            key="second",
            source_expression="by the same interval",
            reference="sixth star in breast of Fish",
            components={},
            source_value_equal_to_key="first",
            flags=["source_value_stated_equal"],
        )
        batch = dict(
            id="same-interval",
            volume=13,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=305),
            span_decisions=[
                dict(span_id="s", decision="include", reason="Explicit source equality")
            ],
            contexts=[
                dict(
                    key="relation",
                    kind="source_observation_context",
                    lines=[1],
                    value="Same interval",
                )
            ],
            assertions=[first, second],
        )
        result = self.module().compile_catalogue([batch], {13: text}, spans)
        bykey = {a["key"]: a for a in result["assertions"]}
        self.assertEqual(bykey["second"]["normalized"]["magnitude"], "13200")
        self.assertEqual(bykey["second"]["source_expression"], "by the same interval")
        self.assertEqual(bykey["second"]["components"], {})
        self.assertEqual(bykey["second"]["source_value_equal_to_id"], bykey["first"]["id"])

    def test_source_alternative_inherits_degree_without_claiming_a_correction(self):
        text = "16 28\nor 30^M^\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=13, edition_sha256=sha, line_start=1, line_end=2)]
        raw = dict(
            key="raw",
            line=1,
            span_id="s",
            source_expression="16 28",
            quantity="angular_separation",
            role="recorded_reading",
            subject="Mars",
            reference="Aldebaran",
            components={"degree": "16", "arcminute": "28"},
            unit_basis="D/M source columns",
        )
        alternate = dict(
            raw,
            key="alternate",
            line=2,
            source_expression="30^M^",
            role="source_alternative",
            components={"degree": "16", "arcminute": "30"},
            variant_of_key="raw",
            inherited_components={"degree": "raw"},
            flags=["alternative_suggestion_not_applied", "not_an_additional_raw_reading"],
        )
        batch = dict(
            id="source-alternative",
            volume=13,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=145),
            span_decisions=[dict(span_id="s", decision="include", reason="Source alternative")],
            assertions=[raw, alternate],
        )
        try:
            result = self.module().compile_catalogue([batch], {13: text}, spans)
        except ValueError as error:
            self.fail(f"Printed source alternative must be preserved: {error}")
        bykey = {a["key"]: a for a in result["assertions"]}
        self.assertEqual(bykey["raw"]["normalized"]["magnitude"], "59280")
        self.assertEqual(bykey["alternate"]["normalized"]["magnitude"], "59400")
        self.assertEqual(bykey["alternate"]["variant_of_id"], bykey["raw"]["id"])
        self.assertEqual(bykey["alternate"]["source_expression"], "30^M^")
        self.assertEqual(bykey["alternate"]["role"], "source_alternative")
        bad = copy.deepcopy(batch)
        bad["assertions"][1]["components"]["degree"] = "17"
        with self.assertRaisesRegex(ValueError, "[Ii]nherited"):
            self.module().compile_catalogue([bad], {13: text}, spans)

    def test_corrected_component_inherits_only_the_linked_original_component(self):
        text, spans, batch = self.variant_fixture()
        r = self.module().compile_catalogue([batch], {10: text}, spans)
        raw = next(a for a in r["assertions"] if a["key"] == "raw")
        corrected = next(a for a in r["assertions"] if a["key"] == "corrected")
        self.assertEqual(raw["normalized"]["magnitude"], "10960")
        # Literal 3²⁄₈ means 3 + 2/8 minutes, not 3 + 3/8.
        self.assertEqual(corrected["normalized"]["magnitude"], "10995")
        self.assertEqual(corrected["variant_of_id"], raw["id"])
        bad = copy.deepcopy(batch)
        bad["assertions"][1]["components"]["degree"] = "4"
        with self.assertRaisesRegex(ValueError, "[Ii]nherited"):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_adopted_epoch_and_repeated_series_remain_distinct_from_observing_clock(self):
        text, spans, batch = self.variant_fixture()
        r = self.module().compile_catalogue([batch], {10: text}, spans)
        epoch = next(a for a in r["assertions"] if a["key"] == "epoch")
        self.assertEqual(epoch["normalized"]["magnitude"], "24300")
        self.assertEqual(r["events"][0]["epoch_assertion_id"], epoch["id"])
        self.assertIsNone(r["events"][0]["clock_assertion_id"])
        raw = next(a for a in r["assertions"] if a["key"] == "raw")
        self.assertEqual(raw["series_id"], r["contexts"][0]["id"])
        self.assertEqual(raw["ordinal_original"], "I")
        bad = copy.deepcopy(batch)
        bad["events"][0]["clock_key"] = "epoch"
        with self.assertRaisesRegex(ValueError, "clock"):
            self.module().compile_catalogue([bad], {10: text}, spans)

    def test_public_preview_keeps_cancellation_and_correction_roles(self):
        text, spans, batch = self.variant_fixture()
        batch["assertions"][0]["record_status"] = "cancelled"
        batch["assertions"][0]["flags"] = ["struck_through_in_source"]
        r = self.module().public_preview(
            self.module().compile_catalogue([batch], {10: text}, spans)
        )
        raw = next(a for a in r["assertions"] if a["role"] == "repeated_reading")
        self.assertEqual(raw["record_status"], "cancelled")
        corrected = next(a for a in r["assertions"] if a["role"] == "printed_correction")
        self.assertEqual(corrected["variant_of_id"], raw["id"])

    def test_event_clock_links_reject_an_hour_angle(self):
        text, spans, batch = self.fixture()
        batch["events"][0]["clock_key"] = "ha"
        with self.assertRaisesRegex(ValueError, "clock"):
            self.module().compile_catalogue([batch], {10: text}, spans)

    def test_inspected_coverage_counts_overlapping_intervals_once(self):
        text, spans, batch = self.fixture()
        other = copy.deepcopy(batch)
        other.update(id="review-2", assertions=[], contexts=[], events=[])
        r = self.module().compile_catalogue([batch, other], {10: text}, spans)
        self.assertEqual(r["summary"]["inspected_source_lines"], 4)
        self.assertEqual(r["summary"]["inspected_candidate_spans"], 3)
        again = self.module().compile_catalogue([other, batch], {10: text}, spans)
        self.assertEqual(r, again)

    def test_public_preview_omits_private_source_text_and_locators(self):
        text, spans, batch = self.fixture()
        r = self.module().compile_catalogue([batch], {10: text}, spans)
        public = self.module().public_preview(r)
        self.assertEqual(public["summary"]["source_assertions"], 2)
        self.assertNotIn("source_expression", str(public))
        self.assertNotIn("line_start", str(public))
        self.assertNotIn("edition_sha256", str(public))

    def test_historical_arithmetic_is_checked_without_replacing_recorded_output(self):
        text, spans, batch = self.fixture()
        # Independent hand calculation: 46°35′ + 39°30′ = 86°05′.
        text += "46 35; 39 30; difference 86 6\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        for s in spans:
            s["edition_sha256"] = sha
        spans.append(dict(id="s4", volume=10, edition_sha256=sha, line_start=6, line_end=6))
        batch.update(
            edition_sha256=sha,
            line_end=6,
            interval_sha256=hashlib.sha256("\n".join(text.splitlines()[1:6]).encode()).hexdigest(),
        )
        batch["span_decisions"].append(
            dict(span_id="s4", decision="include", reason="difference labelled")
        )
        for key, expr, d, m in [
            ("east", "46 35", "46", "35"),
            ("west", "39 30", "39", "30"),
            ("difference", "86 6", "86", "6"),
        ]:
            batch["assertions"].append(
                dict(
                    key=key,
                    line=6,
                    span_id="s4",
                    source_expression=expr,
                    quantity="right_ascension_difference"
                    if key == "difference"
                    else "meridian_distance",
                    role="reduction" if key == "difference" else "recorded_reading",
                    subject="Mars",
                    components={"degree": d, "arcminute": m},
                    unit_basis="angular columns",
                )
            )
        batch["derivations"] = [
            dict(key="sum", input_keys=["east", "west"], output_key="difference", operation="sum")
        ]
        r = self.module().compile_catalogue([batch], {10: text}, spans)
        self.assertFalse(r["derivations"][0]["arithmetic_agrees"])
        self.assertEqual(r["derivations"][0]["computed_magnitude"], "309900")
        output = next(a for a in r["assertions"] if a["key"] == "difference")
        self.assertEqual(output["normalized"]["magnitude"], "309960")

    def test_explicit_source_means_preserve_fractional_results_and_stated_outputs(self):
        from src.public_checkpoint import public_derivation

        cases = [
            (
                "declination",
                ["17 25⅙", "17 24½", "17 24 50"],
                [
                    {"degree": "17", "arcminute": "25 1/6"},
                    {"degree": "17", "arcminute": "24 1/2"},
                    {"degree": "17", "arcminute": "24", "arcsecond": "50"},
                ],
                "62690",
                "62690",
                True,
            ),
            (
                "altitude",
                ["51 29⅓", "51 28¾", "51 29 5"],
                [
                    {"degree": "51", "arcminute": "29 1/3"},
                    {"degree": "51", "arcminute": "28 3/4"},
                    {"degree": "51", "arcminute": "29", "arcsecond": "5"},
                ],
                "370685/2",
                "185345",
                False,
            ),
        ]
        for quantity, expressions, components, want, stated, agrees in cases:
            with self.subTest(quantity=quantity):
                text = "\n".join(expressions)
                sha = hashlib.sha256(text.encode()).hexdigest()
                spans = [dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=3)]
                batch = dict(
                    id="source-mean",
                    volume=12,
                    edition_sha256=sha,
                    line_start=1,
                    line_end=3,
                    interval_sha256=sha,
                    basis=dict(kind="final_edition_review", printed_page=451),
                    span_decisions=[
                        dict(span_id="s", decision="include", reason="Explicit source mean")
                    ],
                    assertions=[
                        dict(
                            key=key,
                            line=i + 1,
                            span_id="s",
                            source_expression=expressions[i],
                            quantity=quantity,
                            role="reduction" if i == 2 else "recorded_reading",
                            subject="Mars",
                            reference=None,
                            components=components[i],
                            unit_basis="Source angular units",
                        )
                        for i, key in enumerate(("a", "b", "mean"))
                    ],
                    derivations=[
                        dict(key="mean", input_keys=["a", "b"], output_key="mean", operation="mean")
                    ],
                )
                before = copy.deepcopy(batch)
                out = self.module().compile_catalogue([batch], {12: text}, spans)
                derivation = out["derivations"][0]
                indexed = {a["id"]: a for a in out["assertions"]}
                self.assertEqual(
                    (derivation["computed_magnitude"], derivation["arithmetic_agrees"]),
                    (want, agrees),
                )
                self.assertEqual(
                    indexed[derivation["output_id"]]["normalized"]["magnitude"], stated
                )
                self.assertEqual(public_derivation(derivation, indexed)["computed_magnitude"], want)
                self.assertEqual(batch, before)
                with self.assertRaises(ValueError):
                    public_derivation(
                        dict(derivation, input_ids=derivation["input_ids"][:1]), indexed
                    )
                batch["derivations"][0]["input_keys"] = ["a"]
                with self.assertRaises(ValueError):
                    self.module().compile_catalogue([batch], {12: text}, spans)

    def test_workspace_writes_reproducibly_and_refuses_source_output(self):
        m = self.module()
        text, spans, batch = self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            work = root / "mars"
            source.mkdir()
            work.mkdir()
            rel = Path(
                "brahe/thesaurus_observationum_vol1/translation/brahe_thesaurus_observationum_vol1_prepub.md"
            )
            path = source / rel
            path.parent.mkdir(parents=True)
            path.write_text(text)
            (work / "witnesses.json").write_text(
                json.dumps(
                    [
                        dict(
                            volume=10,
                            private_source=str(rel),
                            edition_sha256=batch["edition_sha256"],
                        )
                    ]
                )
            )
            (work / "inventory_spans.jsonl").write_text(
                "\n".join(json.dumps(s) for s in spans) + "\n"
            )
            (work / "review_batches.json").write_text(json.dumps([batch]))
            m.build_workspace(source, work)
            outputs = [
                "assertions.jsonl",
                "assertions.csv",
                "public_catalogue_preview.json",
                "catalogue_manifest.json",
            ]
            before = {name: (work / name).read_bytes() for name in outputs}
            m.build_workspace(source, work)
            self.assertEqual(before, {name: (work / name).read_bytes() for name in outputs})
            self.assertEqual(path.read_text(), text)
            with self.assertRaisesRegex(ValueError, "source"):
                m.build_workspace(source, source / "output")


if __name__ == "__main__":
    unittest.main()
