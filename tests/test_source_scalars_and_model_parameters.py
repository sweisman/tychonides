import copy, hashlib, unittest
from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion


class SourceScalarAndModelParameterTests(unittest.TestCase):
    def test_editorial_period_count_requires_linked_unapplied_annotation(self):
        parent = "assertion-v12-" + "b" * 20
        for kind in ("source_year_count", "source_month_count"):
            row = self.row(
                "source_scalar",
                {"scalar": "29"},
                source_expression="29",
                subject="Saturn calculation",
                role="editorial_variant",
                source_parameter_kind=kind,
                variant_of_id=parent,
                annotation_of_id=parent,
                flags=[
                    "not_an_additional_raw_reading",
                    "source_annotation_variant",
                    "alternative_suggestion_not_applied",
                ],
            )
            with self.subTest(kind=kind):
                out = public_assertion(row)
                self.assertEqual(out["normalized"]["magnitude"], "29")
                self.assertEqual(out["source_parameter_kind"], kind)
            for changes in (
                {"variant_of_id": None},
                {"annotation_of_id": None},
                {"annotation_of_id": "assertion-v12-" + "c" * 20},
                {"flags": ["not_an_additional_raw_reading"]},
                {"event_id": "event-v12-" + "a" * 20},
                {"model_name": "Tycho Brahe"},
                {"source_parameter_kind": "source_record_count"},
            ):
                with self.subTest(kind=kind, changes=changes), self.assertRaises(ValueError):
                    public_assertion(dict(row, **changes))

    def test_known_angle_with_an_unresolved_reference_is_preserved(self):
        row = self.row(
            "angular_separation",
            {"degree": "7", "arcminute": "38", "arcsecond": "30"},
            subject="Capella",
            source_reference_status="antecedent_unresolved",
            flags=["not_an_additional_raw_reading", "reference_antecedent_unresolved"],
        )
        out = public_assertion(row)
        self.assertEqual(out["source_reference_status"], "antecedent_unresolved")
        self.assertEqual(out["normalized"]["magnitude"], "27510")
        self.assertIsNone(out["reference"])
        for changes in (
            {"source_reference_status": "unknown"},
            {"flags": ["not_an_additional_raw_reading"]},
            {"reference": "Regulus"},
            {"quantity": "declination"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                public_assertion(dict(row, **changes))

    def test_stadia_keep_the_printed_native_unit_without_a_metric_length(self):
        row = self.row(
            "distance_in_stadia",
            {"scalar": "500"},
            source_expression="500 stadia",
            subject="Earth",
        )
        self.assertEqual(row["normalized"]["status"], "exact")
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["unit"], "source_stadium")
        self.assertEqual(out["normalized"]["magnitude"], "500")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        for changes in (
            {"source_expression": "500 paces"},
            {"source_expression": "500 miles"},
            {"source_expression": "501 stadia"},
            {"components": {"degree": "500"}},
            {"direction": "north"},
            {"role": "recorded_reading"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                bad = dict(row, **changes)
                bad["normalized"] = normalize_quantity(bad)
                public_assertion(bad)

    def test_unknown_denominator_in_a_size_multiplier_stays_unresolved(self):
        row = self.row(
            "source_scalar",
            {},
            source_expression="2 2/[?]",
            subject="New Star calculation",
            source_parameter_kind="comparison_multiplier",
            flags=["not_an_additional_raw_reading", "source_notation_unresolved"],
        )
        out = public_assertion(row)
        self.assertEqual(row["source_expression"], "2 2/[?]")
        self.assertEqual(out["normalized"]["status"], "unsupported")
        self.assertEqual(out["normalized"]["unit"], "source_scalar")
        self.assertIsNone(out["normalized"]["magnitude"])
        self.assertIsNone(out["normalized"]["least_component_unit"])
        for changes in (
            {"components": {"scalar": "2"}},
            {"source_expression": "2 2/3"},
            {"reference": "Sun"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                bad = dict(row, **changes)
                bad["normalized"] = normalize_quantity(bad)
                public_assertion(bad)

    def test_unresolved_size_table_operands_never_acquire_a_scalar(self):
        for expression in ("15 0", "38 0", "7 ☩", "24 ☩"):
            with self.subTest(expression=expression):
                row = self.row(
                    "source_scalar",
                    {},
                    source_expression=expression,
                    subject="Sun calculation",
                    source_parameter_kind="comparison_multiplier",
                    flags=["not_an_additional_raw_reading", "source_notation_unresolved"],
                )
                out = public_assertion(row)
                self.assertEqual(out["normalized"]["status"], "unsupported")
                self.assertEqual(out["normalized"]["unit"], "source_scalar")
                self.assertEqual(row["source_expression"], expression)
                self.assertIsNone(out["normalized"]["magnitude"])
                self.assertIsNone(out["normalized"]["least_component_unit"])
                for changes in (
                    {"components": {"scalar": "7"}},
                    {"role": "recorded_reading"},
                    {"source_parameter_kind": "arithmetic_intermediate"},
                    {"reference": "Earth"},
                    {"source_expression": "7 ☩ 2"},
                    {"source_expression": "7 1"},
                ):
                    with self.subTest(changes=changes), self.assertRaises(ValueError):
                        bad = dict(row, **changes)
                        bad["normalized"] = normalize_quantity(bad)
                        public_assertion(bad)

    def test_printed_size_ratio_correction_remains_an_unapplied_variant(self):
        row = self.row(
            "source_scalar",
            {"scalar": "3375"},
            source_expression="3375",
            subject="Sun calculation",
            role="printed_correction",
            source_parameter_kind="comparison_multiplier",
            variant_of_id="assertion-v12-" + "b" * 20,
            flags=["not_an_additional_raw_reading", "alternative_suggestion_not_applied"],
        )
        out = public_assertion(row)
        self.assertEqual(out["role"], "printed_correction")
        self.assertEqual(out["variant_of_id"], row["variant_of_id"])
        self.assertEqual(out["normalized"]["magnitude"], "3375")
        self.assertIn("alternative_suggestion_not_applied", out["flags"])
        for changes in (
            {"variant_of_id": None},
            {"flags": ["not_an_additional_raw_reading"]},
            {"role": "historical_prediction"},
            {"source_parameter_kind": "eccentricity_as_stated"},
            {"reference": "Earth"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                public_assertion(dict(row, **changes))

    def test_pole_star_prediction_preserves_its_stated_model(self):
        for model in ("Tycho Brahe", "Alphonsine"):
            row = self.row(
                "polar_distance",
                {"degree": "3", "arcminute": "8", "arcsecond": "50"},
                subject="Polaris",
                role="historical_prediction",
                model_name=model,
            )
            out = public_assertion(row)
            self.assertEqual(out["model_name"], model)
            self.assertEqual(out["normalized"]["magnitude"], "11330")
            self.assertIsNone(out["normalized"]["signed_magnitude"])
            for changes in (
                {"model_name": "Copernicus"},
                {"flags": []},
                {"reference": "Earth"},
                {"event_id": "event-v12-" + "a" * 20},
            ):
                with self.subTest(model=model, changes=changes), self.assertRaises(ValueError):
                    public_assertion(dict(row, **changes))

    def test_extrapolated_stellar_population_is_a_calculation_not_a_new_census(self):
        row = self.row(
            "source_scalar",
            {"scalar": "62500"},
            subject="fixed stars",
            role="calculation_intermediate",
            source_parameter_kind="source_record_count",
        )
        out = public_assertion(row)
        self.assertEqual(out["role"], "calculation_intermediate")
        self.assertEqual(out["normalized"]["magnitude"], "62500")
        for changes in ({"role": "recorded_reading"}, {"model_name": "Ptolemy"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                public_assertion(dict(row, **changes))

    def test_sky_area_keeps_square_degrees_instead_of_a_linear_angle(self):
        row = self.row(
            "angular_area",
            {"scalar": "500"},
            source_expression="500 square degrees",
            subject="fixed stars",
        )
        self.assertEqual(row["normalized"]["status"], "exact")
        self.assertEqual(row["normalized"]["unit"], "square_degree")
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "500")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        for changes in (
            {"source_expression": "500 degrees"},
            {"source_expression": "500"},
            {"source_expression": "5000 square degrees"},
            {"components": {"degree": "500"}},
            {"direction": "north"},
            {"zodiac_sign": "Aries"},
            {"role": "recorded_reading"},
            {"reference": "Earth"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                bad = dict(row, **changes)
                bad["normalized"] = normalize_quantity(bad)
                public_assertion(bad)
        changed = copy.deepcopy(row)
        changed["normalized"]["magnitude"] = "501"
        with self.assertRaises(ValueError):
            public_assertion(changed)

    def test_unresolved_calendar_count_never_restores_a_missing_numeral(self):
        for expression in ("2[numeral: ?]4", "2[?]4", "[?]"):
            row = self.row(
                "source_scalar",
                {},
                subject="calendar calculation",
                role="historical_input",
                source_parameter_kind="source_year_count",
                source_expression=expression,
                flags=["not_an_additional_raw_reading", "source_notation_unresolved"],
            )
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["status"], "unsupported")
            self.assertIsNone(out["normalized"]["magnitude"])
            self.assertEqual(out["normalized"]["unit"], "source_scalar")
            for changes in (
                {"components": {"scalar": "284"}},
                {"source_expression": "284"},
                {"source_parameter_kind": "model_length"},
                {"subject": "Sun calculation"},
                {"role": "recorded_reading"},
                {"direction": "north"},
            ):
                with (
                    self.subTest(expression=expression, changes=changes),
                    self.assertRaises(ValueError),
                ):
                    changed = dict(row, **changes)
                    changed["normalized"] = normalize_quantity(changed)
                    public_assertion(changed)

    def test_native_model_length_alternative_keeps_its_scale_and_original_link(self):
        row = self.row(
            "source_scalar",
            {"scalar": "107956"},
            subject="Moon calculation",
            role="source_alternative",
            source_parameter_kind="model_length",
            source_scalar_scale="100000",
            variant_of_id="assertion-v12-" + "e" * 20,
            flags=["not_an_additional_raw_reading", "alternative_suggestion_not_applied"],
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "107956")
        self.assertEqual(out["source_scalar_scale"], "100000")
        with self.assertRaises(ValueError):
            public_assertion(dict(row, variant_of_id=None))

    def test_letter_shaped_lunar_numeral_has_no_adopted_native_value(self):
        row = self.row(
            "source_scalar",
            {},
            subject="Moon calculation",
            role="calculation_intermediate",
            source_expression="398S",
            source_parameter_kind="arithmetic_intermediate",
            flags=["not_an_additional_raw_reading", "source_notation_unresolved"],
        )
        out = public_assertion(row)
        self.assertIsNone(out["normalized"]["magnitude"])
        self.assertEqual(out["normalized"]["unit"], "source_scalar")
        for changes in (
            {"source_expression": "3988"},
            {"source_expression": "S"},
            {"subject": "Moon"},
            {"role": "recorded_reading"},
            {"reference": "Earth"},
            {"components": {"scalar": "3988"}},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                altered = dict(row, **changes)
                altered["normalized"] = normalize_quantity(altered)
                public_assertion(altered)

    def test_lunar_table_alternatives_remain_linked_and_unapplied(self):
        for expression, components in (("3803", {"scalar": "3803"}), ("97938?", {})):
            flags = ["not_an_additional_raw_reading", "alternative_suggestion_not_applied"]
            if not components:
                flags.append("source_notation_unresolved")
            row = self.row(
                "source_scalar",
                components,
                subject="Moon calculation",
                role="source_alternative",
                source_expression=expression,
                source_parameter_kind="unlabelled_table_value",
                variant_of_id="assertion-v12-" + "e" * 20,
                flags=flags,
            )
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["unit"], "source_scalar")
            self.assertEqual(out["normalized"]["magnitude"], "3803" if components else None)
            if not components:
                compiling = dict(row, variant_of_id=None, variant_of_key="printed-value")
                self.assertEqual(normalize_quantity(compiling), row["normalized"])
            for changes in (
                {"variant_of_id": None},
                {"flags": []},
                {"source_scalar_scale": "100000"},
                {"role": "recorded_reading"},
                {"reference": "Earth"},
            ):
                with self.subTest(expression=expression, changes=changes):
                    with self.assertRaises(ValueError):
                        altered = dict(row, **changes)
                        altered["normalized"] = normalize_quantity(altered)
                        public_assertion(altered)

    def test_stated_precision_is_an_angle_not_a_statistical_uncertainty(self):
        row = self.row(
            "stated_angular_precision",
            {"arcminute": "10"},
            subject="instrument",
            role="historical_input",
            flags=["not_an_additional_raw_reading", "source_approximate"],
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "600")
        self.assertEqual(out["normalized"]["unit"], "arcsecond")
        self.assertNotIn("uncertainty", out)
        self.assertEqual(out["role"], "historical_input")

    def test_recorded_solar_ruler_chord_preserves_native_units(self):
        row = self.row(
            "source_scalar",
            {"scalar": "117600"},
            subject="Sun",
            role="recorded_reading",
            flags=[],
            source_parameter_kind="instrument_chord",
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "117600")
        self.assertEqual(out["normalized"]["unit"], "source_scalar")
        self.assertNotIn("source_scalar_scale", out)
        out_scaled = public_assertion(dict(row, source_scalar_scale="100000"))
        self.assertEqual(out_scaled["source_scalar_scale"], "100000")
        with self.assertRaises(ValueError):
            public_assertion(dict(row, source_scalar_scale="0"))

    def test_unresolved_ruler_chord_keeps_literal_without_scalar(self):
        for expression in ("82[?]67", "11264[?]"):
            row = self.row(
                "source_scalar",
                {},
                subject="Sun",
                role="recorded_reading",
                source_expression=expression,
                flags=["source_notation_unresolved"],
                source_parameter_kind="instrument_chord",
            )
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["unit"], "source_scalar")
            self.assertIsNone(out["normalized"]["magnitude"])
            self.assertEqual(out["normalized"]["status"], "unsupported")
        with self.assertRaises(ValueError):
            public_assertion(dict(row, source_expression="82667"))

    def test_second_printed_chord_alternative_keeps_its_relation(self):
        row = self.row(
            "source_scalar",
            {"scalar": "54910"},
            subject="Sun",
            role="source_alternative",
            flags=["alternative_suggestion_not_applied", "not_an_additional_raw_reading"],
            source_parameter_kind="instrument_chord",
            variant_of_id="assertion-v12-" + "e" * 20,
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "54910")
        self.assertEqual(out["variant_of_id"], row["variant_of_id"])
        with self.assertRaises(ValueError):
            public_assertion(dict(row, variant_of_id=None))

    def test_staff_reading_stays_in_native_linear_parts(self):
        row = self.row(
            "source_scalar",
            {"scalar": "210"},
            subject="Mars",
            reference="Saturn",
            role="recorded_reading",
            flags=[],
            source_parameter_kind="instrument_linear_reading",
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "210")
        self.assertEqual(out["normalized"]["unit"], "source_scalar")
        with self.assertRaises(ValueError):
            public_assertion(dict(row, role="calculation_intermediate"))

    def test_unresolved_instrument_parts_never_acquire_a_scalar(self):
        for expression in ("1006 [?]", "1118 1⁄[?]", "[?]81 1⁄[?]", "79,2⅜"):
            row = self.row(
                "source_scalar",
                {},
                subject="Mars",
                reference="Saturn",
                role="recorded_reading",
                source_expression=expression,
                flags=["source_notation_unresolved"],
                source_parameter_kind="instrument_linear_reading",
            )
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["unit"], "source_scalar")
            self.assertIsNone(out["normalized"]["magnitude"])
            self.assertEqual(out["normalized"]["status"], "unsupported")
        for changes in (
            dict(source_expression="1118"),
            dict(source_expression="[?] private prose"),
            dict(source_scalar_scale="1000"),
            dict(role="historical_input"),
            dict(components={"scalar": "1118"}),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                altered = dict(row, **changes)
                altered["normalized"] = normalize_quantity(altered)
                public_assertion(altered)

    def test_visual_native_scales_preserve_ratios_without_angles(self):
        for kind in (
            "visual_palm",
            "visual_digit_breadth",
            "visual_lunar_diameter",
            "visual_lunar_semidiameter",
            "visual_lunar_reference_unstated",
            "visual_reference_separation",
        ):
            row = self.row(
                "source_fraction",
                {"fraction": "1/2"},
                reference="Aldebaran",
                role="recorded_reading",
                source_fraction_kind=kind,
                comparison_relation="separation_as_stated",
                flags=["source_visual_estimate", "geometry_interpretation_unestablished"],
            )
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["magnitude"], "1/2")
            self.assertIsNone(out["normalized"]["magnitude_degrees"])
            self.assertIsNone(out["normalized"]["signed_magnitude"])
            self.assertEqual(out["source_fraction_kind"], kind)
        for relation, flag in (
            ("greater_than_reference_fraction", "source_lower_bound"),
            ("less_than_reference_fraction", "source_upper_bound"),
            ("at_least_reference_fraction", "source_lower_bound"),
            ("at_most_reference_fraction", "source_upper_bound"),
        ):
            bounded = dict(row, comparison_relation=relation, flags=row["flags"] + [flag])
            self.assertEqual(public_assertion(bounded)["comparison_relation"], relation)
            with self.assertRaises(ValueError):
                public_assertion(dict(bounded, flags=row["flags"]))
        for changes in (
            dict(reference=None),
            dict(source_fraction_kind="visual_unknown"),
            dict(comparison_relation="unknown"),
            dict(flags=[]),
            dict(role="prediction"),
            dict(direction="north"),
            dict(model_name="Ptolemy"),
            dict(components={"fraction": "0"}),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                changed = dict(row, **changes)
                changed["normalized"] = normalize_quantity(changed)
                public_assertion(changed)
        illustration = dict(
            row, role="historical_input", flags=row["flags"] + ["not_an_additional_raw_reading"]
        )
        public_assertion(illustration)
        with self.assertRaises(ValueError):
            public_assertion(dict(illustration, flags=row["flags"]))

    def test_unresolved_visual_fraction_preserves_native_scale_without_value(self):
        for expression, kind in (
            ("[?]", "visual_digit_breadth"),
            ("[?]/[?]", "visual_reference_separation"),
        ):
            row = self.row(
                "source_fraction",
                {},
                reference="Saturn",
                role="recorded_reading",
                source_expression=expression,
                source_fraction_kind=kind,
                comparison_relation="separation_as_stated",
                flags=[
                    "source_visual_estimate",
                    "geometry_interpretation_unestablished",
                    "source_notation_unresolved",
                ],
            )
            out = public_assertion(row)
            self.assertEqual(out["normalized"]["status"], "unsupported")
            self.assertEqual(out["normalized"]["unit"], "source_fraction")
            self.assertIsNone(out["normalized"]["magnitude"])
            self.assertIsNone(out["normalized"]["magnitude_degrees"])
            self.assertEqual(out["source_fraction_kind"], kind)
            for changes in (
                dict(components={"fraction": "1"}),
                dict(source_expression="5"),
                dict(reference=None),
                dict(source_fraction_kind="unknown"),
                dict(direction="north"),
            ):
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    altered = dict(row, **changes)
                    altered["normalized"] = normalize_quantity(altered)
                    public_assertion(altered)

    def test_clock_counts_keep_calibration_separate_from_recorded_turns(self):
        for kind, role, value in (
            ("clock_wheel_teeth", "calibration", "56"),
            ("clock_complete_turns", "recorded_reading", "1"),
            ("clock_additional_teeth", "recorded_reading", "35"),
        ):
            row = self.row(
                "source_scalar",
                {"scalar": value},
                subject="observing clock",
                role=role,
                source_parameter_kind=kind,
                flags=["not_an_additional_raw_reading"] if role == "calibration" else [],
            )
            self.assertEqual(public_assertion(row)["normalized"]["magnitude"], value)
            for changes in (
                dict(subject="Mars"),
                dict(reference="Sun"),
                dict(role="historical_input"),
                dict(model_name="Alphonsine"),
            ):
                with self.subTest(kind=kind, changes=changes), self.assertRaises(ValueError):
                    public_assertion(dict(row, **changes))
            for invalid in ("0", "1/2"):
                with self.subTest(kind=kind, invalid=invalid), self.assertRaises(ValueError):
                    altered = dict(row, components={"scalar": invalid})
                    altered["normalized"] = normalize_quantity(altered)
                    public_assertion(altered)

    def test_lunar_eclipse_digit_estimate_keeps_lower_bound(self):
        row = self.row(
            "source_scalar",
            {"scalar": "4"},
            subject="Moon",
            role="recorded_reading",
            flags=["source_visual_estimate", "source_lower_bound"],
            source_parameter_kind="eclipse_digit_count",
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "4")
        self.assertIn("source_lower_bound", out["flags"])
        exact_visual = dict(row, flags=["source_visual_estimate"])
        self.assertEqual(public_assertion(exact_visual)["normalized"]["magnitude"], "4")
        solar_visual = dict(exact_visual, subject="Sun")
        self.assertEqual(public_assertion(solar_visual)["normalized"]["magnitude"], "4")
        predicted = self.row(
            "source_scalar",
            {"scalar": "10"},
            subject="Moon",
            role="historical_prediction",
            flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
            source_parameter_kind="eclipse_digit_count",
            model_name="Alphonsine",
        )
        self.assertEqual(public_assertion(predicted)["model_name"], "Alphonsine")
        with self.assertRaises(ValueError):
            public_assertion(dict(row, flags=[]))

    def test_solar_worked_trigonometry_keeps_scale_and_operation(self):
        for kind, value in (
            ("trigonometric_radius", "1000000"),
            ("scaled_sine", "399149"),
            ("scaled_secant", "7672599"),
        ):
            with self.subTest(kind=kind):
                row = self.row(
                    "source_scalar",
                    {"scalar": value},
                    subject="Sun calculation",
                    role="calculation_intermediate",
                    source_parameter_kind=kind,
                    source_scalar_scale="1000000",
                )
                out = public_assertion(row)
                self.assertEqual(out["normalized"]["magnitude"], value)
                self.assertEqual(out["source_scalar_scale"], "1000000")
        with self.assertRaises(ValueError):
            public_assertion(
                self.row(
                    "source_scalar",
                    {"scalar": "1000001"},
                    subject="Sun calculation",
                    role="calculation_intermediate",
                    source_parameter_kind="scaled_sine",
                    source_scalar_scale="1000000",
                )
            )

    def test_solar_eccentricity_keeps_source_diameter_scale(self):
        row = self.row(
            "source_scalar",
            {"scalar": "41378"},
            subject="Sun calculation",
            source_parameter_kind="model_length",
            source_scalar_scale="1000000",
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "41378")
        self.assertEqual(out["source_scalar_scale"], "1000000")
        for change in ({"source_scalar_scale": "0"}, {"role": "recorded_reading"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(dict(row, **change))

    def test_solar_apogee_argument_preserves_source_year_count(self):
        row = self.row(
            "source_scalar",
            {"scalar": "708"},
            subject="Sun calculation",
            source_parameter_kind="source_year_count",
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "708")
        self.assertEqual(out["source_parameter_kind"], "source_year_count")
        with self.assertRaises(ValueError):
            public_assertion(dict(row, role="recorded_reading"))

    def row(self, q, parts, **extra):
        row = dict(
            id="assertion-v12-" + "f" * 20,
            volume=12,
            printed_page=307,
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

    def test_unscaled_scalar_retains_the_number_without_a_reference_whole(self):
        text = "twice\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        source = dict(
            key="factor",
            line=1,
            span_id="s",
            source_expression="twice",
            quantity="source_scalar",
            components={"scalar": "2"},
            subject="Mars calculation",
            reference=None,
            direction=None,
            role="historical_input",
            source_parameter_kind="comparison_multiplier",
            source_word_numbers={"twice": "2"},
            flags=["not_an_additional_raw_reading"],
            unit_basis="Source comparison word, not an angular value",
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        batch = dict(
            id="scalar-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=307),
            span_decisions=[dict(span_id="s", decision="context", reason="Reviewed scalar")],
            assertions=[source],
            events=[],
        )
        try:
            out = public_assertion(compile_catalogue([batch], {12: text}, [span])["assertions"][0])
        except ValueError as error:
            self.fail("Unscaled source scalar must compile and export: " + str(error))
        self.assertEqual(out["normalized"]["magnitude"], "2")
        self.assertEqual(out["normalized"]["unit"], "source_scalar")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        self.assertNotIn("source_reference_scale", out["normalized"])
        for kind in (
            "eccentricity_as_stated",
            "tabular_argument_unit_unstated",
            "unresolved_instruction_count",
        ):
            row = self.row(
                "source_scalar",
                {"scalar": "9 1/2"},
                subject="Mars calculation",
                source_parameter_kind=kind,
            )
            self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "19/2")
        bad = copy.deepcopy(row)
        bad["role"] = "recorded_coordinate"
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_apogee_plus_minus_is_not_a_hemisphere_or_signed_position(self):
        for sign in ("plus", "minus"):
            row = self.row(
                "calculation_angle",
                {"degree": "2"},
                role="historical_correction",
                argument_name="apogee_shift",
                source_adjustment_sign=sign,
            )
            try:
                out = public_assertion(row)
            except ValueError as error:
                self.fail("Source adjustment sign must export: " + str(error))
            self.assertEqual(out.get("source_adjustment_sign"), sign)
            self.assertIsNone(out["normalized"]["signed_magnitude"])
            for change in (
                {"direction": "south"},
                {"argument_name": "eccentric_anomaly"},
                {"source_adjustment_sign": "private phrase"},
            ):
                bad = copy.deepcopy(row)
                bad.update(change)
                with self.subTest(change=change), self.assertRaises(ValueError):
                    public_assertion(bad)

    def test_southern_maximum_is_a_hypothetical_parameter(self):
        row = self.row(
            "ecliptic_latitude",
            {"degree": "6", "arcminute": "55"},
            direction="south",
            source_parameter_kind="greatest_southern_latitude",
        )
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Source southern maximum must export: " + str(error))
        self.assertEqual(out["normalized"]["signed_magnitude"], "-24900")
        for change in ({"role": "recorded_coordinate"}, {"direction": "north"}):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
