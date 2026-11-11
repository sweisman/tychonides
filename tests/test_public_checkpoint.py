import copy
import importlib
import unittest


class PublicCheckpointTests(unittest.TestCase):
    def test_solar_ephemeris_eclipse_keeps_predicted_clock_and_native_extent(self):
        from src.normalization import normalize_quantity

        common = dict(
            self.fixture(),
            subject="Sun",
            reference=None,
            direction=None,
            event_id=None,
            role="historical_prediction",
            model_name="Magini",
            flags=[
                "not_an_additional_raw_reading",
                "not_an_observing_clock",
                "absolute_time_unestablished",
            ],
        )
        clock = dict(
            common,
            quantity="calculation_epoch",
            components={"hour": "7", "minute": "25"},
            source_expression="7^h^ 25^m^",
            source_eclipse_phase="middle",
            time_reference="source_after_noon",
        )
        clock["normalized"] = normalize_quantity(clock)
        out = self.module().public_assertion(clock)
        self.assertEqual(out["normalized"]["magnitude"], "26700")
        self.assertEqual(out["source_eclipse_phase"], "middle")
        extent = dict(
            common,
            quantity="eclipse_extent",
            components={"digit": "5", "digit_minute": "37"},
            source_expression="5 digits 37 minutes",
            source_extent_unit="digit",
        )
        extent["normalized"] = normalize_quantity(extent)
        out = self.module().public_assertion(extent)
        self.assertEqual(out["normalized"]["unit"], "source_eclipse_digit")
        self.assertEqual(out["normalized"]["magnitude"], "337/60")

    def test_named_ephemeris_compilers_keep_predictions_and_unsigned_error_claims(self):
        from src.normalization import normalize_quantity

        for model in ("Magini", "Origanus", "Scala"):
            for body in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
                for role, quantity in (
                    ("historical_prediction", "ecliptic_longitude"),
                    ("historical_prediction", "angular_daily_motion"),
                    ("historical_comparison", "longitude_difference"),
                ):
                    row = dict(
                        self.fixture(),
                        subject=body,
                        reference=None,
                        direction=None,
                        model_name=model,
                        role=role,
                        quantity=quantity,
                        event_id=None,
                        components={"degree": "12", "arcminute": "4"},
                        source_expression="12° 4′",
                        flags=["not_an_additional_raw_reading"],
                    )
                    if role == "historical_comparison":
                        row.update(
                            comparison_relation="coordinate_difference",
                            source_comparison_sign="plus",
                        )
                    else:
                        row["flags"].append("zodiac_sign_unstated")
                    row["normalized"] = normalize_quantity(row)
                    with self.subTest(model=model, body=body, role=role):
                        out = self.module().public_assertion(row)
                        self.assertEqual(out["model_name"], model)
                        self.assertEqual(out["role"], role)
                        self.assertEqual(out["normalized"]["magnitude"], "43440")
                        self.assertIsNone(out["normalized"]["signed_magnitude"])
                        self.assertNotIn("zodiac_longitude_degrees", out["normalized"])

    def test_named_sign_origin_exports_its_bound_context_identity(self):
        from src.normalization import normalize_quantity

        context_id = "context-v10-" + "a" * 20
        row = dict(
            self.fixture(),
            quantity="ecliptic_longitude",
            role="historical_input",
            subject="Mars",
            reference=None,
            direction=None,
            source_expression="6° 54′",
            components={"degree": "6", "arcminute": "54"},
            zodiac_sign="Taurus",
            context_ids=[context_id],
            zodiac_sign_basis_context_id=context_id,
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        self.assertEqual(
            self.module().public_assertion(row)["zodiac_sign_basis_context_id"], context_id
        )
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, context_ids=[]))
        with self.assertRaises(ValueError):
            self.module().public_assertion(
                dict(row, context_ids=[None], zodiac_sign_basis_context_id=None)
            )

    def test_unresolved_coordinate_retains_known_origin_evidence_without_a_scalar(self):
        from src.normalization import normalize_quantity

        context_id = "context-v10-" + "a" * 20
        row = dict(
            self.fixture(),
            quantity="ecliptic_longitude",
            role="historical_input",
            subject="Mars",
            reference=None,
            direction=None,
            source_expression="6° ?′",
            components={},
            zodiac_sign="Taurus",
            context_ids=[context_id],
            zodiac_sign_basis_context_id=context_id,
            flags=["not_an_additional_raw_reading", "source_notation_unresolved"],
        )
        row["normalized"] = normalize_quantity(row)
        result = self.module().public_assertion(row)
        self.assertEqual(result["zodiac_sign_basis_context_id"], context_id)
        self.assertEqual(result["normalized"]["status"], "unsupported")
        self.assertIsNone(result["normalized"]["magnitude"])

    def test_uncertain_comparison_operand_retains_literal_without_choosing_fraction(self):
        from src.normalization import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="source_scalar",
            subject="New Star calculation",
            reference=None,
            direction=None,
            event_id=None,
            role="historical_input",
            source_expression="⟦33/53⟧",
            components={},
            source_parameter_kind="comparison_multiplier",
            flags=["not_an_additional_raw_reading", "source_notation_unresolved"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(row["source_expression"], "⟦33/53⟧")
        self.assertEqual(out["normalized"]["status"], "unsupported")
        self.assertEqual(out["normalized"]["unit"], "source_scalar")
        self.assertIsNone(out["normalized"]["magnitude"])
        for change in (
            {"components": {"scalar": "33"}},
            {"role": "recorded_reading"},
            {"event_id": "invented-event"},
            {"direction": "north"},
            {"source_expression": "33/53"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                bad = dict(row, **change)
                bad["normalized"] = normalize_quantity(bad)
                self.module().public_assertion(bad)

    def test_zenith_distance_retains_measured_angle_without_altitude_conversion(self):
        from src.normalization import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="zenith_distance",
            subject="Moon",
            reference=None,
            direction=None,
            role="historical_input",
            source_expression="50°",
            components={"degree": "50"},
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["quantity"], "zenith_distance")
        self.assertEqual(out["normalized"]["magnitude"], "180000")
        self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_native_linear_sexagesimal_scale_is_not_an_angle_or_earth_radius(self):
        from src.normalization import normalize_quantity

        row = dict(
            self.fixture(),
            subject="Saturn calculation",
            reference=None,
            direction=None,
            event_id=None,
            quantity="source_sexagesimal_length",
            role="historical_input",
            source_expression="230° 10′",
            components={"source_part": "230", "part_minute": "10"},
            source_scalar_scale="25",
            source_length_role="orbital_radius",
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_scalar_scale"], "25")
        self.assertEqual(out["normalized"]["unit"], "source_length_part")
        self.assertEqual(out["normalized"]["magnitude"], "1381/6")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        for value in ("0", "-25", "twenty-five", 25, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, source_scalar_scale=value))

    def test_native_length_role_separates_body_diameter_from_radial_distance(self):
        from src.normalization import normalize_quantity

        row = dict(
            self.fixture(),
            subject="Sun",
            reference="Earth",
            direction=None,
            event_id=None,
            quantity="distance_in_semidiameters",
            role="historical_input",
            source_expression="11",
            components={"semidiameter": "11"},
            source_semidiameter_body="Earth",
            source_length_role="physical_diameter",
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        self.assertEqual(
            self.module().public_assertion(row)["source_length_role"], "physical_diameter"
        )
        for value in ("radar_range", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, source_length_role=value))

    def test_native_size_comparison_preserves_measure_operands_and_inverse_relation(self):
        from src.normalization import normalize_quantity

        row = dict(
            self.fixture(),
            subject="Sun calculation",
            reference=None,
            direction=None,
            event_id=None,
            quantity="source_scalar",
            role="historical_input",
            source_expression="166⅜",
            components={"scalar": "166 3/8"},
            source_parameter_kind="comparison_multiplier",
            source_comparison_measure="bulk",
            source_comparison_endpoints=["Sun", "Earth"],
            source_comparison_relation="first_larger",
            source_comparison_term="factor",
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_comparison_measure"], "bulk")
        self.assertEqual(out["source_comparison_endpoints"], ["Sun", "Earth"])
        self.assertEqual(out["normalized"]["magnitude"], "1331/8")
        inverse = dict(
            row,
            subject="Moon calculation",
            source_comparison_endpoints=["Moon", "Earth"],
            source_comparison_relation="first_smaller",
            source_expression="39",
            components={"scalar": "39"},
        )
        inverse["normalized"] = normalize_quantity(inverse)
        self.assertEqual(self.module().public_assertion(inverse)["normalized"]["magnitude"], "39")
        comet = dict(
            inverse,
            subject="comet calculation",
            source_comparison_endpoints=["comet", "Earth"],
            source_expression="870",
            components={"scalar": "870"},
        )
        comet["normalized"] = normalize_quantity(comet)
        projected_comet = self.module().public_assertion(comet)
        self.assertEqual(projected_comet["source_comparison_endpoints"], ["comet", "Earth"])
        self.assertEqual(projected_comet["source_comparison_relation"], "first_smaller")
        self.assertEqual(projected_comet["normalized"]["magnitude"], "870")
        operand = dict(
            row,
            source_comparison_measure="diameter",
            source_comparison_term="second_operand",
            source_comparison_relation="first_to_second_as_stated",
            source_expression="2",
            components={"scalar": "2"},
        )
        operand["normalized"] = normalize_quantity(operand)
        self.assertEqual(
            self.module().public_assertion(operand)["source_comparison_term"], "second_operand"
        )
        unspecified = dict(operand, source_comparison_measure="not_stated")
        projected = self.module().public_assertion(unspecified)
        self.assertEqual(projected["source_comparison_measure"], "not_stated")
        self.assertEqual(projected["normalized"]["magnitude"], "2")
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(unspecified, source_comparison_term="factor"))
        for change in (
            {"source_comparison_measure": "astrology"},
            {"source_comparison_endpoints": ["Sun"]},
            {"source_comparison_endpoints": ["Sun", "Sun"]},
            {"source_comparison_term": "sum"},
            {"source_comparison_relation": "measured_distance"},
            {"subject": "Mars calculation"},
            {"reference": "Earth"},
            {"role": "recorded_reading"},
            {"flags": []},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                bad = dict(row, **change)
                bad["normalized"] = normalize_quantity(bad)
                self.module().public_assertion(bad)
        fixed = dict(
            row,
            subject="fixed star calculation",
            source_comparison_endpoints=["fixed stars", "Earth"],
            source_stellar_class=1,
        )
        self.assertEqual(self.module().public_assertion(fixed)["source_stellar_class"], 1)
        for value in (0, 7, True, "1"):
            with self.subTest(stellar_class=value), self.assertRaises(ValueError):
                self.module().public_assertion(dict(fixed, source_stellar_class=value))
        native = dict(
            row,
            quantity="source_sexagesimal_length",
            components={"source_part": "5", "part_minute": "27"},
            source_comparison_measure="diameter",
            source_comparison_term="first_operand",
            source_comparison_relation="first_to_second_as_stated",
        )
        del native["source_parameter_kind"]
        native["normalized"] = normalize_quantity(native)
        out_native = self.module().public_assertion(native)
        self.assertEqual(out_native["normalized"]["unit"], "source_length_part")
        self.assertEqual(out_native["source_comparison_term"], "first_operand")
        del row["source_comparison_term"]
        with self.assertRaises(ValueError):
            self.module().public_assertion(row)

    def test_attributed_separation_difference_keeps_literal_sign_and_magnitude(self):
        from src.normalization import normalize_quantity

        row = dict(
            self.fixture(),
            subject="New Star of 1572",
            reference="Pole Star",
            direction=None,
            event_id=None,
            quantity="separation_difference",
            role="historical_comparison",
            source_expression="6 min⁹",
            components={"arcminute": "6"},
            comparison_sources=["Hagecius, earlier Dialexis", "Brahe"],
            comparison_relation="second_minus_first_as_stated",
            comparison_label_original="min⁹",
            source_comparison_sign="minus",
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(row["source_expression"], "6 min⁹")
        self.assertEqual(out["normalized"]["magnitude"], "360")
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        self.assertEqual(out["source_comparison_sign"], "minus")
        self.assertEqual(out["comparison_label_original"], "min⁹")
        self.assertEqual(out["comparison_sources"], ["Hagecius, earlier Dialexis", "Brahe"])
        for change in (
            {"comparison_sources": ["Hagecius"]},
            {"comparison_sources": ["Brahe", "Brahe"]},
            {"comparison_sources": ["", "Brahe"]},
            {"comparison_relation": "observed_parallax"},
            {"comparison_label_original": "min9"},
            {"source_comparison_sign": "plus"},
            {"model_name": "Copernicus"},
            {"event_id": "event-v10-" + "a" * 20},
            {"role": "recorded_reading"},
            {"reference": None},
            {"direction": "north"},
            {"flags": []},
            {"components": {"arcminute": "7"}},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                bad = dict(row, **change)
                bad["normalized"] = normalize_quantity(bad)
                self.module().public_assertion(bad)

    def test_solar_fractional_comparison_keeps_native_scalar(self):
        from src.normalization import normalize_quantity

        row = dict(
            self.fixture(),
            subject="Sun calculation",
            reference=None,
            direction=None,
            quantity="source_scalar",
            role="historical_input",
            source_parameter_kind="comparison_multiplier",
            components={"scalar": "1/3"},
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "1/3")
        self.assertEqual(out["normalized"]["unit"], "source_scalar")
        self.assertEqual(out["source_parameter_kind"], "comparison_multiplier")
        for change in ({"subject": "Sun"}, {"role": "recorded_reading"}, {"flags": []}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **change))

    def test_source_angular_comparisons_keep_model_relation_and_session(self):
        from src.normalization import normalize_quantity

        for kind, relation, minutes, expected in (
            ("parallax_angle", "model_smaller_than_source", "1 1/2", "90"),
            ("angular_diameter", "model_larger_than_source", "1/2", "30"),
        ):
            with self.subTest(kind=kind):
                row = dict(
                    self.fixture(),
                    quantity="calculation_angle",
                    role="historical_comparison",
                    subject="Moon",
                    reference=None,
                    direction=None,
                    event_id="event-v10-" + "a" * 20,
                    model_name="Copernicus",
                    comparison_quantity=kind,
                    comparison_relation=relation,
                    components={"arcminute": minutes},
                    flags=["not_an_additional_raw_reading", "historical_parallax_not_detection"],
                )
                row["normalized"] = normalize_quantity(row)
                out = self.module().public_assertion(row)
                self.assertEqual(out["normalized"]["magnitude"], expected)
                self.assertIsNone(out["normalized"]["signed_magnitude"])
                self.assertEqual(out["model_name"], "Copernicus")
                self.assertEqual(out["comparison_quantity"], kind)
                self.assertEqual(out["comparison_relation"], relation)
                self.assertEqual(out["event_id"], "event-v10-" + "a" * 20)
                for change in (
                    {"comparison_quantity": "distance"},
                    {"comparison_relation": "detected_parallax"},
                    {"model_name": None},
                    {"role": "recorded_reading"},
                    {"quantity": "angular_separation"},
                    {"reference": "Earth"},
                    {"direction": "north"},
                    {"flags": []},
                    {"components": {"arcminute": "2"}},
                ):
                    with self.subTest(change=change), self.assertRaises(ValueError):
                        self.module().public_assertion(dict(row, **change))
                forged = dict(row, normalized=dict(row["normalized"], magnitude="999"))
                with self.assertRaises(ValueError):
                    self.module().public_assertion(forged)

    def test_unresolved_native_model_length_retains_scale_without_a_value(self):
        from src.normalization import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="source_scalar",
            role="calculation_intermediate",
            subject="New Star calculation",
            reference=None,
            direction=None,
            event_id=None,
            components={},
            source_expression="23 23138 [?]",
            source_parameter_kind="model_length",
            source_scalar_scale="10000000",
            flags=["not_an_additional_raw_reading", "source_notation_unresolved"],
        )
        row["normalized"] = normalize_quantity(row)
        result = self.module().public_assertion(row)
        self.assertEqual(result["source_scalar_scale"], "10000000")
        self.assertEqual(result["normalized"]["unit"], "source_scalar")
        self.assertIsNone(result["normalized"]["magnitude"])
        for change in (
            {"role": "recorded_reading"},
            {"subject": "Mars"},
            {"source_scalar_scale": "0"},
            {"source_scalar_scale": None},
            {"direction": "north"},
            {"components": {"scalar": "2323138"}},
            {"source_expression": "2323138"},
            {"reference": "Earth"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                bad = dict(row, **change)
                bad["normalized"] = normalize_quantity(bad)
                self.module().public_assertion(bad)

    def test_natal_chart_star_labels_preserve_source_names(self):
        from src.catalog import normalize_quantity

        for subject in (
            "Castor",
            "Palilicium",
            "Pleiades",
            "Lyra",
            "Dog Star",
            "head of Serpentarius",
            "preceding star in right foot of Serpentarius",
            "wing of Pegasus",
            "Hercules",
            "bright one of the Southern scale",
            "Southern Claw",
        ):
            with self.subTest(subject=subject):
                row = dict(
                    self.fixture(),
                    subject=subject,
                    reference=None,
                    quantity="ecliptic_longitude",
                    role="historical_input",
                    source_expression="12°",
                    components={"degree": "12"},
                    flags=["not_an_additional_raw_reading"],
                )
                row["normalized"] = normalize_quantity(row)
                self.assertEqual(self.module().public_assertion(row)["subject"], subject)

    def test_circumpolar_source_labels_keep_polar_distance_endpoints(self):
        from src.catalog import normalize_quantity

        subjects = (
            "preceding star in flank of Lesser Bear",
            "star in right shoulder of Cepheus",
            "star in right flank of Cepheus beneath girdle",
            "star at springing of tail of Greater Bear",
            "middle star in tail of Greater Bear",
            "star in shoulder of Greater Bear",
            "left leg of Greater Bear",
            "star at flanks of Greater Bear",
            "knee of Cassiopeia",
            "Bright Star of the Chair",
            "Schedir",
            "Flexura",
        )
        for subject in subjects:
            with self.subTest(subject=subject):
                row = dict(
                    self.fixture(),
                    subject=subject,
                    reference="celestial pole",
                    quantity="angular_separation",
                    role="reduction",
                    components={"degree": "14", "arcminute": "5 1/6"},
                    flags=["not_an_additional_raw_reading"],
                )
                row["normalized"] = normalize_quantity(row)
                result = self.module().public_assertion(row)
                self.assertEqual(result["subject"], subject)
                self.assertEqual(result["reference"], "celestial pole")
                self.assertEqual(result["role"], "reduction")
                self.assertEqual(result["normalized"]["magnitude"], "50710")

    def test_schedir_can_be_the_recorded_separation_reference(self):
        from src.normalization import normalize_quantity

        row = dict(
            self.fixture(),
            subject="New Star of 1572",
            reference="Schedir",
            quantity="angular_separation",
            role="historical_input",
            direction=None,
            components={"degree": "7", "arcminute": "50"},
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["reference"], "Schedir")
        self.assertEqual(out["normalized"]["magnitude"], "28200")

    def test_lunar_latitude_parallax_is_a_qualified_historical_input(self):
        from src.catalog import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="parallax_angle",
            role="historical_input",
            subject="Moon",
            reference="Earth",
            parallax_component="latitude",
            components={"arcminute": "28", "arcsecond": "3"},
            flags=["not_an_additional_raw_reading", "historical_parallax_not_detection"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "1683")
        self.assertEqual(out["parallax_component"], "latitude")
        for changes in (
            {"role": "recorded_reading"},
            {"reference": None},
            {"subject": "Sun"},
            {"flags": ["not_an_additional_raw_reading"]},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_native_calculation_day_count_is_not_an_absolute_timestamp(self):
        from src.catalog import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="calculation_epoch",
            role="calculation_epoch",
            subject="Sun",
            components={"day": "16", "hour": "19", "minute": "18"},
            source_expression="16 D. 19 H. 18 /",
            flags=["not_an_additional_raw_reading", "not_an_observing_clock"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "1451880")
        self.assertEqual(out["normalized"]["least_component_unit"], "minute")
        self.assertNotIn("derived_timestamp", out)
        with self.assertRaises(ValueError):
            normalize_quantity(dict(row, flags=[]))
        for parts in ({"day": "16", "hour": "24"}, {"day": "16", "minute": "60"}):
            with self.subTest(parts=parts), self.assertRaises(ValueError):
                normalize_quantity(dict(row, components=parts))

    def test_copernican_lunar_prediction_retains_explicit_zodiac_origin(self):
        from src.catalog import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="ecliptic_longitude",
            role="historical_prediction",
            subject="Moon",
            model_name="Copernicus",
            zodiac_sign="Gemini",
            components={"degree": "27", "arcminute": "36"},
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["zodiac_longitude_degrees"], "438/5")
        self.assertEqual(out["model_name"], "Copernicus")
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, event_id="event-v10-" + "a" * 20))

    def test_printed_lunar_model_difference_is_not_recomputed(self):
        from src.catalog import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="longitude_difference",
            role="historical_comparison",
            subject="Moon",
            model_name="Alphonsine",
            comparison_relation="coordinate_difference",
            components={"degree": "1", "arcminute": "10"},
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "4200")
        self.assertEqual(out["comparison_relation"], "coordinate_difference")

    def test_lunar_unlabelled_table_scalar_preserves_native_zero(self):
        from src.catalog import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="source_scalar",
            subject="Moon calculation",
            role="historical_input",
            source_expression="00",
            components={"scalar": "00"},
            reference=None,
            direction=None,
            source_parameter_kind="unlabelled_table_value",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="source_scalar", components={"scalar": "00"})
            ),
        )
        result = self.module().public_assertion(row)
        self.assertEqual(row["source_expression"], "00")
        self.assertEqual(result["normalized"]["magnitude"], "0")
        self.assertEqual(result["normalized"]["unit"], "source_scalar")
        for changes in (
            {"role": "recorded_reading"},
            {"source_scalar_scale": "100000"},
            {"reference": "Earth"},
            {"flags": []},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_stated_earth_rotation_period_is_not_an_observing_clock(self):
        from src.catalog import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="clock_elapsed_time",
            subject="Earth",
            role="historical_input",
            source_expression="twenty-four hours",
            components={"hour": "24"},
            source_word_numbers={"twenty-four": "24"},
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="clock_elapsed_time", components={"hour": "24"})
            ),
        )
        result = self.module().public_assertion(row)
        self.assertEqual(result["normalized"]["magnitude"], "86400")
        self.assertEqual(result["role"], "historical_input")

    def test_stellar_catalogue_counts_are_whole_nonobservational_counts(self):
        from src.catalog import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="source_scalar",
            subject="fixed stars",
            role="historical_input",
            source_parameter_kind="source_record_count",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="source_scalar", components={"scalar": "1022"})
            ),
        )
        self.assertEqual(self.module().public_assertion(row)["normalized"]["magnitude"], "1022")
        for changes in (
            {"role": "recorded_reading"},
            {"flags": []},
            {"source_scalar_scale": "60"},
            {
                "normalized": normalize_quantity(
                    dict(quantity="source_scalar", components={"scalar": "1/2"})
                )
            },
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_saturn_reported_observation_count_keeps_aggregate_role(self):
        from src.catalog import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="source_scalar",
            subject="Saturn calculation",
            role="historical_input",
            source_parameter_kind="source_record_count",
            flags=["not_an_additional_raw_reading", "source_approximate"],
            normalized=normalize_quantity(
                dict(quantity="source_scalar", components={"scalar": "70"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "70")
        self.assertEqual(out["role"], "historical_input")
        self.assertIn("source_approximate", out["flags"])
        for changes in (
            {"role": "recorded_reading"},
            {"flags": []},
            {
                "normalized": normalize_quantity(
                    dict(quantity="source_scalar", components={"scalar": "1/2"})
                )
            },
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_origanus_new_star_labels_remain_distinct_historical_inputs(self):
        from src.catalog import normalize_quantity

        for subject in (
            "new star in Cygnus (Origanus)",
            "new star in Ophiuchus (Origanus)",
        ):
            with self.subTest(subject=subject):
                row = dict(
                    self.fixture(),
                    subject=subject,
                    quantity="ecliptic_latitude",
                    role="historical_input",
                    direction="north",
                    source_expression="1°",
                    components={"degree": "1"},
                    flags=["not_an_additional_raw_reading"],
                )
                row["normalized"] = normalize_quantity(row)
                result = self.module().public_assertion(row)
                self.assertEqual(result["subject"], subject)
                self.assertEqual(result["role"], "historical_input")
                self.assertIsNone(result["event_id"])
                self.assertEqual(result["normalized"]["signed_magnitude"], "3600")

    def test_native_tangent_and_linked_editorial_scalar(self):
        from src.catalog import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="source_scalar",
            subject="Mars calculation",
            role="calculation_intermediate",
            source_parameter_kind="scaled_tangent",
            source_scalar_scale="10000000",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="source_scalar", components={"scalar": "1301115"})
            ),
        )
        self.assertEqual(self.module().public_assertion(row)["normalized"]["magnitude"], "1301115")
        large = dict(
            row,
            normalized=normalize_quantity(
                dict(quantity="source_scalar", components={"scalar": "30000000"})
            ),
        )
        self.module().public_assertion(large)  # Tangents are not bounded by the radius.
        for scale in (None, "0", "-1"):
            with self.subTest(scale=scale), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, source_scalar_scale=scale))
        variant = dict(
            row,
            role="editorial_variant",
            source_parameter_kind="arithmetic_intermediate",
            variant_of_id="assertion-v10-1123456789abcdefabcd",
            flags=["not_an_additional_raw_reading", "alternative_suggestion_not_applied"],
            normalized=normalize_quantity(
                dict(quantity="source_scalar", components={"scalar": "807"})
            ),
        )
        variant.pop("source_scalar_scale")
        self.assertEqual(self.module().public_assertion(variant)["role"], "editorial_variant")
        for change in ({"variant_of_id": None}, {"flags": ["not_an_additional_raw_reading"]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_assertion(dict(variant, **change))

    def test_unread_instrument_scale_label_has_no_invented_value(self):
        from src.catalog import normalize_quantity

        native = dict(
            quantity="source_scalar",
            role="historical_input",
            subject="instrument",
            reference=None,
            direction=None,
            source_expression="[?]00",
            components={},
            source_parameter_kind="instrument_scale_value",
            flags=["source_notation_unresolved", "not_an_additional_raw_reading"],
        )
        norm = normalize_quantity(native)
        self.assertEqual(norm["status"], "unsupported")
        self.assertIsNone(norm["magnitude"])
        row = dict(self.fixture(), **native, normalized=norm)
        self.assertIsNone(self.module().public_assertion(row)["normalized"]["magnitude"])
        for change in (
            {"role": "recorded_reading"},
            {"subject": "Mars"},
            {"flags": ["source_notation_unresolved"]},
            {"components": {"scalar": "200"}},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                modified = dict(native, **change)
                self.module().public_assertion(
                    dict(self.fixture(), **modified, normalized=normalize_quantity(modified))
                )

    def test_calculated_chords_keep_scale_and_printed_outliers(self):
        from src.catalog import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="source_scalar",
            subject="Sun",
            role="historical_input",
            source_parameter_kind="calculated_chord",
            source_scalar_scale="100000",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="source_scalar", components={"scalar": "58385"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "58385")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        for role in ("calculation_intermediate", "reduction"):
            self.assertEqual(self.module().public_assertion(dict(row, role=role))["role"], role)
        for change in (
            {"role": "recorded_reading"},
            {"source_scalar_scale": "0"},
            {"source_scalar_scale": None},
            {"flags": []},
            {"direction": "north"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **change))
        outlier = dict(
            row,
            normalized=normalize_quantity(
                dict(quantity="source_scalar", components={"scalar": "217588"})
            ),
        )
        with self.assertRaises(ValueError):
            self.module().public_assertion(outlier)
        outlier["flags"] = ["not_an_additional_raw_reading", "source_quality_note_present"]
        self.assertEqual(
            self.module().public_assertion(outlier)["normalized"]["magnitude"], "217588"
        )

    def test_instrument_construction_preserves_native_units_and_counts(self):
        from src.catalog import normalize_quantity

        for kind, value in (
            ("instrument_dimension_cubits", "9/2"),
            ("instrument_dimension_feet", "10"),
            ("instrument_dimension_inches", "3/2"),
            ("instrument_dimension_palms", "55"),
            ("instrument_dimension_digits", "3/2"),
            ("instrument_dimension_ratio", "1/3"),
            ("instrument_count", "10"),
            ("instrument_component_count", "2"),
            ("instrument_scale_divisions", "10"),
            ("instrument_scale_value", "100000"),
        ):
            row = dict(
                self.fixture(),
                quantity="source_scalar",
                subject="instrument",
                role="historical_input",
                source_parameter_kind=kind,
                flags=["not_an_additional_raw_reading"],
                normalized=normalize_quantity(
                    dict(quantity="source_scalar", components={"scalar": value})
                ),
            )
            with self.subTest(kind=kind):
                out = self.module().public_assertion(row)
                self.assertEqual(out["source_parameter_kind"], kind)
                self.assertEqual(out["normalized"]["magnitude"], value)
                self.assertIsNone(out["normalized"]["magnitude_degrees"])
                for change in (
                    {"role": "recorded_reading"},
                    {"subject": "Mars"},
                    {"flags": []},
                    {"direction": "north"},
                    {"source_scalar_scale": "100000"},
                    {"event_id": "event-v10-0123456789abcdefabcd"},
                ):
                    with self.subTest(change=change), self.assertRaises(ValueError):
                        self.module().public_assertion(dict(row, **change))
                for bad in ("0", "-1", "1/2"):
                    if (
                        kind
                        in (
                            "instrument_dimension_cubits",
                            "instrument_dimension_feet",
                            "instrument_dimension_inches",
                            "instrument_dimension_palms",
                            "instrument_dimension_digits",
                            "instrument_dimension_ratio",
                        )
                        and bad == "1/2"
                    ):
                        continue
                    with self.subTest(bad=bad), self.assertRaises(ValueError):
                        bad_row = dict(
                            row,
                            normalized=normalize_quantity(
                                dict(quantity="source_scalar", components={"scalar": bad})
                            ),
                        )
                        self.module().public_assertion(bad_row)

    def test_inner_Gemini_head_remains_a_literal_reference(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="adopted_value",
            subject="Mars",
            reference="inner head of Gemini",
            direction=None,
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components=dict(degree="24", arcminute="22½"))
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["reference"], out["normalized"]["magnitude"]), ("inner head of Gemini", "87750")
        )

    def test_model_direct_advance_is_an_interval_angle_with_source_bounds(self):
        from src.catalog import normalize_quantity

        for model, minutes, bounded in [("Alphonsine", "46", False), ("Copernicus", "17", True)]:
            row = self.fixture()
            row.update(
                quantity="longitude_difference",
                role="historical_prediction",
                subject="Mars",
                reference=None,
                direction=None,
                event_id=None,
                model_name=model,
                prediction_relation="direct_change_over_source_interval",
                flags=["not_an_additional_raw_reading"]
                + (["source_lower_bound"] if bounded else []),
                normalized=normalize_quantity(
                    dict(quantity="longitude_difference", components=dict(arcminute=minutes))
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(
                (out["prediction_relation"], out["normalized"]["unit"]),
                ("direct_change_over_source_interval", "arcsecond"),
            )
            self.assertEqual("source_lower_bound" in out["flags"], bounded)
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, event_id="event-v10-" + "a" * 20))

    def test_historical_year_count_keeps_native_scalar_without_seconds(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="source_scalar",
            role="historical_input",
            subject="Mars calculation",
            reference=None,
            direction=None,
            source_parameter_kind="source_year_count",
            flags=["not_an_additional_raw_reading", "source_approximate"],
            normalized=normalize_quantity(
                dict(quantity="source_scalar", components=dict(scalar="1500"))
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (
                out["source_parameter_kind"],
                out["normalized"]["unit"],
                out["normalized"]["magnitude"],
            ),
            ("source_year_count", "source_scalar", "1500"),
        )
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, role="recorded_reading"))

        for subject in ("New Star calculation", "comet calculation", "calendar calculation"):
            for kind in ("source_year_count", "source_month_count"):
                with self.subTest(subject=subject, kind=kind):
                    native = dict(row, subject=subject, source_parameter_kind=kind)
                    result = self.module().public_assertion(native)
                    self.assertEqual(result["normalized"]["unit"], "source_scalar")
                    self.assertIsNone(result["normalized"]["magnitude_degrees"])

        for changes in (
            {"source_parameter_kind": "eccentricity_as_stated"},
            {"source_parameter_kind": "comparison_multiplier"},
            {"quantity": "declination"},
            {"role": "recorded_reading"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, subject="calendar calculation", **changes))

    def test_calendar_native_counts_preserve_dimensions_and_linked_editorial_variant(self):
        from src.catalog import normalize_quantity

        common = dict(
            self.fixture(),
            quantity="source_scalar",
            role="historical_input",
            subject="calendar calculation",
            reference=None,
            direction=None,
            event_id=None,
            flags=["not_an_additional_raw_reading"],
            source_expression="424",
            components={"scalar": "424"},
        )
        common["normalized"] = normalize_quantity(common)
        for kind in (
            "source_year_count",
            "source_month_count",
            "source_day_count",
            "source_cycle_count",
            "source_week_count",
        ):
            row = dict(common, source_parameter_kind=kind)
            with self.subTest(kind=kind):
                out = self.module().public_assertion(row)
                self.assertEqual(out["normalized"]["magnitude"], "424")
                self.assertEqual(out["normalized"]["unit"], "source_scalar")
                self.assertIsNone(out["normalized"]["magnitude_degrees"])
        variant = dict(
            common,
            source_parameter_kind="source_year_count",
            role="editorial_variant",
            variant_of_id="assertion-v10-" + "a" * 20,
        )
        out = self.module().public_assertion(variant)
        self.assertEqual(out["variant_of_id"], variant["variant_of_id"])
        for changes in (
            {"variant_of_id": None},
            {"model_name": "Copernicus"},
            {"reference": "Earth"},
            {"event_id": "event-v10-" + "b" * 20},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(variant, **changes))

    def test_Ophiuchus_meridian_arc_retains_its_stellar_subject(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="meridian_distance",
            role="calibration",
            subject="head of Ophiuchus",
            reference="meridian",
            direction=None,
            normalized=normalize_quantity(
                dict(quantity="meridian_distance", components=dict(degree="38", arcminute="11"))
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["subject"], out["reference"], out["normalized"]["magnitude"]),
            ("head of Ophiuchus", "meridian", "137460"),
        )

    def test_Mars_RA_difference_retains_right_shoulder_of_Orion_endpoint(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="right_ascension_difference",
            role="recorded_reading",
            subject="Mars",
            reference="right shoulder of Orion",
            direction=None,
            normalized=normalize_quantity(
                dict(
                    quantity="right_ascension_difference",
                    components=dict(degree="69", arcminute="51½"),
                )
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["subject"], out["reference"], out["normalized"]["magnitude"]),
            ("Mars", "right shoulder of Orion", "251490"),
        )

    def test_armillae_stellar_declination_calibration_keeps_instrument(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="declination",
            role="calibration",
            subject="heart of Leo",
            reference=None,
            direction="north",
            source_instrument_label="armillae",
            normalized=normalize_quantity(
                dict(
                    quantity="declination",
                    direction="north",
                    components=dict(degree="13", arcminute="58"),
                )
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["role"], out["source_instrument_label"], out["normalized"]["magnitude"]),
            ("calibration", "armillae", "50280"),
        )
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, role="historical_prediction"))

    def test_stellar_RA_calibration_retains_both_descriptive_endpoints(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="right_ascension_difference",
            role="calibration",
            subject="eye of Taurus",
            reference="hip of Leo",
            direction=None,
            flags=[],
            normalized=normalize_quantity(
                dict(
                    quantity="right_ascension_difference",
                    components=dict(degree="99", arcminute="51½"),
                )
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["subject"], out["reference"], out["quantity"]),
            ("eye of Taurus", "hip of Leo", "right_ascension_difference"),
        )
        self.assertEqual(out["normalized"]["magnitude"], "359490")

    def test_reused_parallax_component_retains_its_historical_input_role(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="parallax_angle",
            role="historical_input",
            subject="Mars",
            reference="Earth",
            direction=None,
            parallax_component="altitude",
            flags=["not_an_additional_raw_reading", "historical_parallax_not_detection"],
            normalized=normalize_quantity(
                dict(quantity="parallax_angle", components=dict(arcminute="3", arcsecond="41"))
            ),
        )
        out = self.module().public_assertion(row)
        nova = self.module().public_assertion(dict(row, subject="New Star of 1572"))
        self.assertEqual(nova["parallax_component"], "altitude")
        self.assertEqual(
            (out["parallax_component"], out["role"], out["normalized"]["magnitude"]),
            ("altitude", "historical_input", "221"),
        )
        for changes in (
            dict(role="recorded_reading"),
            dict(flags=["not_an_additional_raw_reading"]),
            dict(reference=None),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_source_motion_shortfall_is_an_interval_comparison_not_a_position(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="angular_motion_difference",
            role="historical_comparison",
            subject="Mars",
            reference=None,
            direction=None,
            event_id=None,
            model_name="Copernicus",
            comparison_relation="angular_motion_shortfall_over_source_interval",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="angular_motion_difference", components=dict(arcminute="25"))
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["normalized"]["magnitude"], out["normalized"]["unit"], out["comparison_relation"]),
            ("1500", "arcsecond", "angular_motion_shortfall_over_source_interval"),
        )
        for changes in (
            dict(quantity="longitude_difference"),
            dict(role="historical_prediction"),
            dict(reference="Earth"),
            dict(direction="east"),
            dict(flags=[]),
            dict(event_id="event-v12-" + "a" * 20),
            dict(comparison_relation="coordinate_difference"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_second_only_clock_does_not_invent_missing_hour_or_minute(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="transit_clock",
            role="recorded_clock",
            subject="Mars",
            reference=None,
            direction=None,
            flags=["clock_hour_unstated", "clock_minute_unstated"],
            normalized=normalize_quantity(
                dict(quantity="transit_clock", components=dict(second="10"))
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["normalized"]["magnitude"], out["normalized"]["least_component_unit"]),
            ("10", "second"),
        )
        self.assertIn("clock_minute_unstated", out["flags"])

    def test_printed_Gemini_subject_and_editorial_Mars_correction_remain_distinct(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            subject="Gemini",
            reference="lower head of Gemini",
            direction=None,
            flags=["source_endpoint_editorially_disputed"],
            editorial_subject_alternative="Mars",
            editorial_subject_status="correction_as_stated",
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components=dict(degree="10", arcminute="7 2/3"))
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["subject"], out["editorial_subject_alternative"], out["normalized"]["magnitude"]),
            ("Gemini", "Mars", "36460"),
        )
        star = self.fixture()
        star.update(
            quantity="transit_clock",
            role="recorded_clock",
            subject="bright star in head of Leo",
            reference=None,
            direction=None,
            normalized=normalize_quantity(
                dict(quantity="transit_clock", components=dict(hour="9", minute="30", second="20"))
            ),
        )
        self.assertEqual(
            self.module().public_assertion(star)["subject"], "bright star in head of Leo"
        )

    def test_azimuth_correction_is_separate_from_a_recorded_bearing(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="azimuth_correction",
            role="historical_correction",
            subject="Mars",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="azimuth_correction", components=dict(arcminute="10"))
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["quantity"], out["normalized"]["magnitude"]), ("azimuth_correction", "600")
        )
        self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_journal_instrument_and_reference_labels_keep_their_source_scope(self):
        from src.catalog import normalize_quantity

        for quantity, reference, label in (
            ("angular_separation", "upper head of Gemini", "astronomical arc"),
            ("altitude", None, "greatest quadrant"),
        ):
            row = self.fixture()
            row.update(
                quantity=quantity,
                role="recorded_reading",
                subject="Mars",
                reference=reference,
                source_instrument_label=label,
                direction=None,
                normalized=normalize_quantity(
                    dict(quantity=quantity, components=dict(degree="7", arcminute="34"))
                ),
            )
            self.assertEqual(self.module().public_assertion(row)["source_instrument_label"], label)
        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            subject="Mars",
            reference="Mars comparison line",
            direction=None,
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components=dict(arcminute="20"))
            ),
        )
        self.assertEqual(self.module().public_assertion(row)["reference"], "Mars comparison line")

    def test_reported_altitude_difference_keeps_its_own_angular_value(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="altitude_difference",
            role="reduction",
            subject="Aldebaran",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="altitude_difference", components=dict(arcminute="2"))
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["quantity"], out["normalized"]["magnitude"], out["normalized"]["unit"]),
            ("altitude_difference", "120", "arcsecond"),
        )
        self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_Gemini_comparison_labels_retain_their_recorded_locations(self):
        from src.catalog import normalize_quantity

        for reference in (
            "star in shoulder of lower Gemini",
            "star in armpit of lower Gemini",
            "preceding head of Gemini",
        ):
            row = self.fixture()
            row.update(
                quantity="angular_separation",
                role="recorded_reading",
                subject="Mars",
                reference=reference,
                direction=None,
                normalized=normalize_quantity(
                    dict(quantity="angular_separation", components=dict(degree="7", arcminute="51"))
                ),
            )
            self.assertEqual(self.module().public_assertion(row)["reference"], reference)
        row = self.fixture()
        row.update(
            quantity="altitude",
            role="recorded_reading",
            subject="star in armpit of lower Gemini",
            reference=None,
            direction=None,
            normalized=normalize_quantity(
                dict(quantity="altitude", components=dict(degree="59", arcminute="25"))
            ),
        )
        self.assertEqual(
            self.module().public_assertion(row)["subject"], "star in armpit of lower Gemini"
        )

    def test_bright_foot_reference_preserves_its_unspecified_upper_lower_identity(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="repeated_reading",
            subject="Mars",
            reference="brighter foot of Erichthonius",
            direction=None,
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components=dict(degree="23", arcminute="25"))
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["reference"], "brighter foot of Erichthonius")
        self.assertEqual(out["normalized"]["magnitude"], "84300")

    def test_jovian_semidiameter_keeps_its_unit_body_and_native_fraction(self):
        from src.catalog import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="distance_in_semidiameters",
            subject="satellite I of Jupiter",
            reference="Jupiter",
            role="historical_input",
            source_semidiameter_body="Jupiter",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(
                    quantity="distance_in_semidiameters",
                    components={"semidiameter": "3", "semidiameter_minute": "30"},
                )
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_semidiameter_body"], "Jupiter")
        self.assertEqual(out["reference"], "Jupiter")
        self.assertEqual(out["normalized"]["magnitude"], "7/2")
        self.assertEqual(out["normalized"]["unit"], "source_semidiameter")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, source_semidiameter_body="Sun"))

    def test_source_derived_Copernican_distance_is_not_an_observed_distance(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="distance_in_semidiameters",
            role="reduction",
            subject="Mars",
            reference="Earth",
            direction=None,
            source_semidiameter_body="Earth",
            source_distance_model="Copernicus",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="distance_in_semidiameters", components=dict(semidiameter="721"))
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual((out["role"], out["source_distance_model"]), ("reduction", "Copernicus"))
        for changes in (
            dict(role="recorded_reading"),
            dict(reference="Sun"),
            dict(source_semidiameter_body="Sun"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_calculated_parallax_components_keep_the_distance_premise_explicit(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="distance_in_semidiameters",
            role="historical_input",
            subject="Mars",
            reference="Earth",
            direction=None,
            source_semidiameter_body="Earth",
            source_distance_model="Copernicus",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="distance_in_semidiameters", components=dict(semidiameter="721"))
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["source_distance_model"], out["source_semidiameter_body"]), ("Copernicus", "Earth")
        )
        for changes in (
            dict(source_distance_model="Ptolemy"),
            dict(role="recorded_reading"),
            dict(reference="Sun"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))
        for component in ("altitude", "longitude", "latitude"):
            r = self.fixture()
            r.update(
                quantity="parallax_angle",
                role="reduction",
                subject="Mars",
                reference="Earth",
                direction=None,
                parallax_component=component,
                flags=["not_an_additional_raw_reading"],
                normalized=normalize_quantity(
                    dict(
                        quantity="parallax_angle",
                        components=dict(degree="0", arcminute="3", arcsecond="39"),
                    )
                ),
            )
            self.assertEqual(self.module().public_assertion(r)["parallax_component"], component)
            for changes in (
                dict(parallax_component="horizontal"),
                dict(role="recorded_reading"),
                dict(reference="Sun"),
                dict(direction="north"),
                dict(quantity="altitude"),
            ):
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    self.module().public_assertion(dict(r, **changes))

    def test_main_parallax_triangle_and_colure_labels_remain_local_subjects(self):
        from src.catalog import normalize_quantity

        for label in (
            "triangle GBK",
            "triangle CDE",
            "triangle CBE",
            "triangle AKB",
            "solstitial colure",
        ):
            r = self.fixture()
            r.update(
                subject=label,
                reference=None,
                quantity="calculation_angle",
                role="historical_input",
                direction=None,
                normalized=normalize_quantity(
                    dict(quantity="calculation_angle", components=dict(degree="23", arcminute="31"))
                ),
            )
            self.assertEqual(self.module().public_assertion(r)["subject"], label)

    def test_equator_setting_and_lower_foot_input_are_distinct_from_Mars(self):
        from src.catalog import normalize_quantity

        for label, quantity in [
            ("equator", "altitude"),
            ("lower foot of Erichthonius", "declination"),
        ]:
            row = self.fixture()
            row.update(
                subject=label,
                reference=None,
                quantity=quantity,
                role="historical_input",
                direction=None,
                normalized=normalize_quantity(
                    dict(quantity=quantity, components=dict(degree="34", arcminute="5 1/2"))
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual((out["subject"], out["role"]), (label, "historical_input"))
            self.assertIsNone(out["direction"])

    def test_model_retrogression_predictions_keep_interval_meaning(self):
        from src.catalog import normalize_quantity

        for model in ("Copernicus", "Alphonsine"):
            row = self.fixture()
            row.update(
                quantity="longitude_difference",
                role="historical_prediction",
                subject="Mars",
                reference=None,
                direction=None,
                event_id=None,
                model_name=model,
                prediction_relation="retrograde_change_over_source_interval",
                flags=["not_an_additional_raw_reading"],
                normalized=normalize_quantity(
                    dict(
                        quantity="longitude_difference", components=dict(degree="1", arcminute="44")
                    )
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(
                (out["model_name"], out["prediction_relation"], out["normalized"]["magnitude"]),
                (model, "retrograde_change_over_source_interval", "6240"),
            )
            for changes in (
                dict(prediction_relation=None),
                dict(prediction_relation="coordinate_difference"),
                dict(model_name="Stadius"),
                dict(role="historical_input"),
                dict(quantity="ecliptic_longitude"),
                dict(event_id="event-v10-1234567890abcdef1234"),
            ):
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **changes))
            missing = dict(row)
            missing.pop("prediction_relation")
            with self.assertRaises(ValueError):
                self.module().public_assertion(missing)

    def test_pab_triangle_and_culminating_point_keep_their_subjects(self):
        from src.catalog import normalize_quantity

        for label in ("triangle PAB", "culminating point"):
            row = self.fixture()
            row.update(
                subject=label,
                reference=None,
                quantity="calculation_angle",
                role="calculation_intermediate",
                direction=None,
                normalized=normalize_quantity(
                    dict(
                        quantity="calculation_angle", components={"degree": "16", "arcminute": "32"}
                    )
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["subject"], label)
            self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_mars_reduction_triangles_and_northern_head_remain_distinct_subjects(self):
        from src.catalog import normalize_quantity

        for label in (
            "triangle ABP",
            "triangle ABC",
            "triangle PBC",
            "triangle APC",
            "triangle DBC",
            "triangle BDA",
            "northern head of Gemini",
        ):
            row = self.fixture()
            row.update(
                subject=label,
                reference=None,
                quantity="calculation_angle",
                role="calculation_intermediate",
                direction=None,
                normalized=normalize_quantity(
                    dict(
                        quantity="calculation_angle",
                        components={"degree": "40", "arcminute": "29", "arcsecond": "9"},
                    )
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["subject"], label)
            self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_erichthonius_foot_labels_preserve_comparison_and_transit_roles(self):
        from src.catalog import normalize_quantity

        labels = [
            ("Mars", "lower foot of Erichthonius", "angular_separation", "recorded_reading"),
            ("upper foot of Erichthonius", None, "transit_clock", "recorded_clock"),
            ("brighter foot of Erichthonius", None, "transit_clock", "recorded_clock"),
        ]
        for subject, reference, quantity, role in labels:
            components = (
                {"degree": "29", "arcminute": "13 1/2"}
                if quantity == "angular_separation"
                else {"hour": "9", "minute": "7", "second": "10"}
            )
            row = self.fixture()
            row.update(
                subject=subject,
                reference=reference,
                quantity=quantity,
                role=role,
                direction=None,
                normalized=normalize_quantity(dict(quantity=quantity, components=components)),
            )
            out = self.module().public_assertion(row)
            self.assertEqual((out["subject"], out["reference"]), (subject, reference))
            self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_lower_erichthonius_foot_retains_shared_horn_qualification(self):
        from src.catalog import normalize_quantity

        label = "lower foot of Erichthonius shared with horn of Taurus"
        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            subject="Mars",
            reference=label,
            direction=None,
            normalized=normalize_quantity(
                dict(
                    quantity="angular_separation",
                    components={"degree": "29", "arcminute": "33 1/2"},
                )
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["reference"], label)
        self.assertEqual(out["normalized"]["magnitude"], "106410")
        self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_nearby_gemini_shoulder_star_keeps_literal_endpoint(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            subject="Mars",
            reference="small star nearest Mars in shoulders of Gemini",
            direction=None,
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components={"degree": "1", "arcminute": "7"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["reference"], "small star nearest Mars in shoulders of Gemini")
        self.assertEqual(out["normalized"]["magnitude"], "4020")
        self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_daily_gemini_knee_labels_retain_their_own_qualifications(self):
        from src.catalog import normalize_quantity

        labels = ("star in knee of northern Gemini", "star in knee of Gemini")
        for label in labels:
            row = self.fixture()
            row.update(
                quantity="angular_separation",
                role="recorded_reading",
                subject="Mars",
                reference=label,
                direction=None,
                normalized=normalize_quantity(
                    dict(
                        quantity="angular_separation",
                        components={"degree": "22", "arcminute": "32"},
                    )
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["reference"], label)
            self.assertIsNone(out["direction"])
            self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_upper_knee_of_gemini_remains_an_unqualified_reference(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            subject="Mars",
            reference="star in upper knee of Gemini",
            direction=None,
            normalized=normalize_quantity(
                dict(
                    quantity="angular_separation",
                    components={"degree": "22", "arcminute": "32 1/3"},
                )
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["reference"], "star in upper knee of Gemini")
        self.assertIsNone(out["direction"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_slow_clock_drift_retains_direction_as_source_metadata(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="clock_drift",
            role="calibration",
            subject="observing clock",
            flags=["clock_runs_slow", "clock_drift_not_applied_to_times"],
            normalized=normalize_quantity(dict(quantity="clock_drift", components={"minute": "2"})),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["normalized"]["magnitude"], out["normalized"]["unit"]), ("120", "second_of_time")
        )
        self.assertIn("clock_runs_slow", out["flags"])
        self.assertNotIn("clock_runs_fast", out["flags"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_unclassified_angle_alternative_preserves_type_uncertainty(self):
        from src.catalog import normalize_quantity

        original = self.fixture()
        original.update(
            quantity="unclassified_angle",
            role="recorded_reading",
            flags=["measurement_type_unresolved"],
            normalized=normalize_quantity(
                dict(quantity="unclassified_angle", components={"arcminute": "4"})
            ),
        )
        alternate = dict(
            original,
            id="assertion-v10-1123456789abcdefabcd",
            role="source_alternative",
            variant_of_id=original["id"],
            flags=[
                "measurement_type_unresolved",
                "not_an_additional_raw_reading",
                "alternative_suggestion_not_applied",
            ],
            normalized=normalize_quantity(
                dict(quantity="unclassified_angle", components={"arcminute": "5"})
            ),
        )
        rows = [self.module().public_assertion(r) for r in (original, alternate)]
        self.module().validate_links(rows, [])
        self.assertEqual(rows[1]["normalized"]["magnitude"], "300")
        for changes in (
            dict(direction="north"),
            dict(reference="Mars"),
            dict(model_name="Copernicus"),
            dict(variant_of_id=None),
            dict(flags=["measurement_type_unresolved"]),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(alternate, **changes))
        for changes in (
            dict(quantity="angular_length"),
            dict(subject="Moon"),
            dict(role="source_alternative"),
            dict(flags=[]),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().validate_links([dict(rows[0], **changes), rows[1]], [])

    def test_mixed_cetus_and_hyades_transit_targets_stay_literal(self):
        from src.catalog import normalize_quantity

        labels = (
            "more northerly of two toward tail of Cetus in quadrilateral",
            "bright star in middle of jaw of Cetus",
            "bright star at far end of jaw of Cetus",
            "first Hyad in nostrils of Taurus",
            "star between first Hyad and northern eye of Taurus",
            "middle star between first Hyad and southern eye of Taurus",
            "ruddy star in southern eye of Taurus",
        )
        for label in labels:
            for quantity, role, parts in [
                ("altitude", "recorded_reading", {"degree": "23", "arcminute": "41 2/3"}),
                ("transit_clock", "recorded_clock", {"hour": "6", "minute": "59", "second": "45"}),
            ]:
                row = self.fixture()
                row.update(
                    quantity=quantity,
                    role=role,
                    subject=label,
                    normalized=normalize_quantity(dict(quantity=quantity, components=parts)),
                )
                out = self.module().public_assertion(row)
                self.assertEqual(out["subject"], label)
                self.assertIsNone(out["direction"])
        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            reference="breast of Taurus",
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components={"degree": "11", "arcminute": "1"})
            ),
        )
        self.assertEqual(self.module().public_assertion(row)["reference"], "breast of Taurus")

    def test_december_taurus_labels_and_cetus_transit_preserve_the_source(self):
        from src.catalog import normalize_quantity

        for label in (
            "star of third magnitude in breast of Taurus",
            "horn of Taurus shared with foot of Erichthonius",
            "other horn of Taurus",
            "southern eye of Taurus",
        ):
            row = self.fixture()
            row.update(
                quantity="angular_separation",
                role="recorded_reading",
                reference=label,
                normalized=normalize_quantity(
                    dict(
                        quantity="angular_separation", components={"degree": "11", "arcminute": "0"}
                    )
                ),
            )
            self.assertEqual(self.module().public_assertion(row)["reference"], label)
        row = self.fixture()
        row.update(
            quantity="transit_clock",
            role="recorded_clock",
            subject="bright star in head of Cetus",
            flags=["absolute_time_unestablished"],
            normalized=normalize_quantity(
                dict(quantity="transit_clock", components={"hour": "6", "minute": "57"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["subject"], out["normalized"]["magnitude"], out["normalized"]["unit"]),
            ("bright star in head of Cetus", "25020", "second_of_time"),
        )

    def test_quadrant_bias_can_belong_to_a_historical_reduction_only(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="instrument_altitude_bias",
            role="historical_correction",
            subject="Aldebaran and Mars",
            event_id="event-v10-0123456789abcdefabcd",
            flags=["not_an_additional_raw_reading", "historical_reduction_context"],
            source_instrument_label="quadrant",
            source_bias_direction="high",
            source_correction_operation="subtract",
            source_correction_application="historical_reduction_as_stated",
            normalized=normalize_quantity(
                dict(
                    quantity="instrument_altitude_bias",
                    components={"arcminute": "4", "arcsecond": "45"},
                )
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "285")
        self.assertEqual(out["source_instrument_label"], "quadrant")
        self.assertEqual(out["source_correction_operation"], "subtract")
        self.assertEqual(out["source_correction_application"], "historical_reduction_as_stated")
        for changes in (
            dict(role="recorded_reading"),
            dict(subject="Mars"),
            dict(event_id=None),
            dict(source_instrument_label="Radius"),
            dict(source_bias_direction="low"),
            dict(source_correction_operation="add"),
            dict(source_correction_application="applied_to_all_readings"),
            dict(flags=["not_an_additional_raw_reading"]),
            dict(direction="north"),
            dict(reference="Mars"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_november_1580_stellar_endpoints_remain_distinct(self):
        from src.catalog import normalize_quantity

        labels = [
            "upper foot of Erichthonius",
            "foot of Erichthonius shared with other horn of Taurus",
            "left horn of Taurus",
            "foot of Erichthonius in horn of Taurus",
        ]
        for label in labels:
            row = self.fixture()
            row.update(
                quantity="angular_separation",
                role="recorded_reading",
                subject="Mars",
                reference=label,
                direction=None,
                normalized=normalize_quantity(
                    dict(
                        quantity="angular_separation",
                        components={"degree": "10", "arcminute": "56"},
                    )
                ),
            )
            self.assertEqual(self.module().public_assertion(row)["reference"], label)
        row.update(
            quantity="right_ascension",
            role="historical_input",
            subject="southern horn of Taurus",
            reference=None,
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="right_ascension", components={"degree": "28", "arcminute": "8"})
            ),
        )
        self.assertEqual(self.module().public_assertion(row)["normalized"]["magnitude"], "101280")

    def test_northern_eye_reference_does_not_set_mars_hemisphere(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            subject="Mars",
            reference="northern eye of Taurus",
            direction=None,
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components={"degree": "2", "arcminute": "41"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["reference"], "northern eye of Taurus")
        self.assertIsNone(out["direction"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        self.assertEqual(out["normalized"]["magnitude"], "9660")

    def test_hagecius_raw_attribution_does_not_infer_a_site_or_calculation(self):
        from src.catalog import normalize_quantity

        for quantity, role, subject, reference, parts in [
            (
                "angular_separation",
                "recorded_reading",
                "Mars",
                "first star of Aries",
                {"degree": "20", "arcminute": "1"},
            ),
            ("altitude", "repeated_reading", "Spica", None, {"degree": "31", "arcminute": "10"}),
            ("recorded_clock", "recorded_clock", "observing clock", None, {"hour": "9"}),
        ]:
            row = self.fixture()
            row.update(
                quantity=quantity,
                role=role,
                subject=subject,
                reference=reference,
                observer_names=["Thaddaeus Hagecius"],
                normalized=normalize_quantity(dict(quantity=quantity, components=parts)),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["observer_names"], ["Thaddaeus Hagecius"])
            self.assertNotIn("observing_site", out)
            for change in (
                dict(observing_site="Prague"),
                dict(observing_site="Uraniborg"),
                dict(role="historical_input"),
            ):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **change))

    def test_hagecius_numbered_stars_and_unresolved_same_star_stay_literal(self):
        from src.catalog import normalize_quantity

        for subject, reference in [
            ("first star of Aries", "second star of Aries"),
            ("second star of Aries", "third star of Aries"),
            ("Mars", "same star, antecedent unresolved"),
        ]:
            row = self.fixture()
            row.update(
                quantity="angular_separation",
                role="recorded_reading",
                subject=subject,
                reference=reference,
                normalized=normalize_quantity(
                    dict(
                        quantity="angular_separation", components={"degree": "7", "arcminute": "52"}
                    )
                ),
            )
            if reference.startswith("same star"):
                row["flags"] = ["reference_antecedent_unresolved"]
            out = self.module().public_assertion(row)
            self.assertEqual(
                (out["subject"], out["reference"], out["normalized"]["magnitude"]),
                (subject, reference, "28320"),
            )
        for subject, quantity, role, parts, value in [
            (
                "24th star of Hydra",
                "altitude",
                "recorded_reading",
                {"degree": "19", "arcminute": "35"},
                "70500",
            ),
            (
                "Hagecius pole elevation",
                "calculation_angle",
                "historical_input",
                {"degree": "50", "arcminute": "7"},
                "180420",
            ),
        ]:
            row = self.fixture()
            row.update(
                quantity=quantity,
                role=role,
                subject=subject,
                reference=None,
                normalized=normalize_quantity(dict(quantity=quantity, components=parts)),
            )
            self.assertEqual(self.module().public_assertion(row)["normalized"]["magnitude"], value)

    def test_march_planet_comparisons_keep_literal_endpoints_and_quantity(self):
        from src.catalog import normalize_quantity

        for subject, reference in [
            ("Saturn", "bright star in head of Sagittarius"),
            ("Mars", "more southerly star of right horn of Capricorn"),
            (
                "more southerly star of right horn of Capricorn",
                "bright star in head of Sagittarius",
            ),
        ]:
            row = self.fixture()
            row.update(
                quantity="angular_separation",
                role="recorded_reading",
                subject=subject,
                reference=reference,
                normalized=normalize_quantity(
                    dict(
                        quantity="angular_separation", components={"degree": "18", "arcminute": "0"}
                    )
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual((out["subject"], out["reference"]), (subject, reference))
        row.update(
            quantity="latitude_difference",
            subject="Saturn",
            reference="Mars",
            flags=["source_visual_estimate", "geometry_interpretation_unestablished"],
            normalized=normalize_quantity(
                dict(quantity="latitude_difference", components={"degree": "1", "arcminute": "3"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["quantity"], out["direction"], out["normalized"]["magnitude"]),
            ("latitude_difference", None, "3780"),
        )

    def test_historical_observatory_longitude_is_a_parameter(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="calculation_angle",
            role="historical_input",
            subject="historical observatory longitude",
            reference=None,
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="calculation_angle", components={"degree": "28", "arcminute": "0"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["subject"], out["role"], out["normalized"]["magnitude"]),
            ("historical observatory longitude", "historical_input", "100800"),
        )

    def test_named_lunar_eclipse_predictions_preserve_phase_and_native_clock(self):
        from src.catalog import normalize_quantity

        for model, hour, minute, phase, value in [
            ("Alphonsine", "13", "35", "beginning", "48900"),
            ("Stadius", "13", "25", "middle", "48300"),
            ("Prutenic", "1", "50", "middle", "6600"),
        ]:
            row = self.fixture()
            row.update(
                quantity="calculation_epoch",
                role="historical_prediction",
                subject="Moon",
                reference=None,
                model_name=model,
                source_eclipse_phase=phase,
                flags=[
                    "not_an_additional_raw_reading",
                    "not_an_observing_clock",
                    "absolute_time_unestablished",
                ],
                normalized=normalize_quantity(
                    dict(quantity="calculation_epoch", components={"hour": hour, "minute": minute})
                ),
            )
            if model == "Prutenic":
                row["time_reference"] = "source_after_midnight_label"
            out = self.module().public_assertion(row)
            self.assertEqual(
                (out["model_name"], out["source_eclipse_phase"], out["normalized"]["magnitude"]),
                (model, phase, value),
            )
            for change in (
                dict(source_eclipse_phase="unknown phase"),
                dict(subject="Mars"),
                dict(model_name="unreviewed model"),
                dict(reference="Sun"),
                dict(direction="south"),
                dict(role="recorded_clock"),
                dict(event_id="event-v10-0123456789abcdefabcd"),
                dict(flags=[]),
            ):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **change))
            no_phase = dict(row)
            no_phase.pop("source_eclipse_phase")
            with self.assertRaises(ValueError):
                self.module().public_assertion(no_phase)

    def test_unnamed_vienna_eclipse_tables_keep_attribution_uncertain(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="calculation_epoch",
            role="historical_prediction",
            subject="Moon",
            reference=None,
            model_name=None,
            source_model_attribution="unnamed_as_stated",
            source_model_label="tables for Vienna",
            source_eclipse_phase="middle",
            time_reference="source_after_noon",
            flags=[
                "not_an_additional_raw_reading",
                "not_an_observing_clock",
                "absolute_time_unestablished",
            ],
            normalized=normalize_quantity(
                dict(quantity="calculation_epoch", components={"hour": "8", "minute": "13"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertIsNone(out["model_name"])
        self.assertEqual(out["source_model_label"], "tables for Vienna")
        midnight_tables = dict(
            row, source_model_label="tables", time_reference="source_after_midnight_label"
        )
        self.assertEqual(
            self.module().public_assertion(midnight_tables)["source_model_label"], "tables"
        )
        calculation = dict(
            midnight_tables, source_model_label="Calculation", source_eclipse_phase="end"
        )
        self.assertEqual(
            self.module().public_assertion(calculation)["source_model_label"], "Calculation"
        )
        for change in (
            {"source_model_attribution": "named"},
            {"source_eclipse_phase": "unreviewed"},
            {"flags": []},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **change))

    def test_1461_alphonsine_eclipse_end_and_saturn_position(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="calculation_epoch",
            role="historical_prediction",
            subject="Moon",
            reference=None,
            model_name="Alphonsine",
            source_eclipse_phase="end",
            time_reference="source_after_sunset",
            flags=[
                "not_an_additional_raw_reading",
                "not_an_observing_clock",
                "absolute_time_unestablished",
            ],
            normalized=normalize_quantity(
                dict(quantity="calculation_epoch", components={"hour": "1", "minute": "56"})
            ),
        )
        self.assertEqual(
            self.module().public_assertion(row)["time_reference"], "source_after_sunset"
        )
        row.update(
            quantity="ecliptic_longitude",
            subject="Saturn",
            normalized=normalize_quantity(
                dict(quantity="ecliptic_longitude", components={"degree": "0", "arcminute": "24"})
            ),
        )
        row.pop("source_eclipse_phase")
        row.pop("time_reference")
        self.assertEqual(self.module().public_assertion(row)["model_name"], "Alphonsine")

    def test_lunar_node_longitude_remains_a_historical_parameter(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="ecliptic_longitude",
            role="historical_input",
            subject="lunar ascending node",
            reference=None,
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(
                    quantity="ecliptic_longitude",
                    components={"degree": "22", "arcminute": "43"},
                    zodiac_sign="Pisces",
                )
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (
                out["subject"],
                out["role"],
                out["normalized"]["zodiac_sign"],
                out["normalized"]["magnitude"],
            ),
            ("lunar ascending node", "historical_input", "Pisces", "81780"),
        )

    def test_descending_lunar_node_keeps_its_recorded_calculation_identity(self):
        from src.normalization import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="ecliptic_longitude",
            role="calculation_intermediate",
            subject="lunar descending node",
            reference=None,
            direction=None,
            event_id=None,
            components={"degree": "12", "arcminute": "34"},
            source_expression="12° 34′ ♎",
            zodiac_sign="Libra",
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["subject"], "lunar descending node")
        self.assertEqual(out["role"], "calculation_intermediate")
        self.assertIsNone(out["event_id"])
        self.assertEqual(out["normalized"]["magnitude"], "45240")
        self.assertEqual(out["normalized"]["zodiac_longitude_degrees"], "5777/30")

    def test_october_stellar_labels_remain_literal(self):
        from src.catalog import normalize_quantity

        for subject in (
            "Scheat of Pegasus",
            "spine in tail of Capricorn",
            "brighter of two in neck of Pegasus",
            "hinder star in wing of Pegasus",
        ):
            row = self.fixture()
            row.update(
                quantity="altitude",
                role="recorded_reading",
                subject=subject,
                reference=None,
                normalized=normalize_quantity(
                    dict(quantity="altitude", components={"degree": "60", "arcminute": "0"})
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(
                (out["subject"], out["quantity"], out["normalized"]["magnitude"]),
                (subject, "altitude", "216000"),
            )

    def test_lunar_diameters_keep_instruments_and_limb_distance_keeps_endpoint(self):
        from src.catalog import normalize_quantity

        values = []
        for instrument, minutes in [
            ("Radius", "29"),
            ("sextant", "25"),
            ("sextant and Radius", "32"),
        ]:
            row = self.fixture()
            row.update(
                quantity="angular_diameter",
                role="recorded_reading",
                subject="Moon",
                reference=None,
                source_instrument_label=instrument,
                normalized=normalize_quantity(
                    dict(quantity="angular_diameter", components={"arcminute": minutes})
                ),
            )
            out = self.module().public_assertion(row)
            values.append(out["normalized"]["magnitude"])
            self.assertEqual(
                (out["quantity"], out["subject"], out["reference"], out["source_instrument_label"]),
                ("angular_diameter", "Moon", None, instrument),
            )
            for changes in (
                dict(reference="Mars"),
                dict(role="historical_prediction"),
                dict(subject="Mars"),
            ):
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **changes))
        self.assertEqual(values, ["1740", "1500", "1920"])
        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            subject="Moon nearer limb",
            reference="Mars",
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components={"degree": "11", "arcminute": "40"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["subject"], out["reference"], out["normalized"]["magnitude"]),
            ("Moon nearer limb", "Mars", "42000"),
        )

    def test_lunar_aries_comparisons_keep_literal_star_labels(self):
        from src.catalog import normalize_quantity

        for reference in (
            "brighter star in right horn of Aries",
            "first star of Aries",
            "second star of Aries",
        ):
            row = self.fixture()
            row.update(
                quantity="angular_separation",
                role="recorded_reading",
                subject="Moon nearer limb",
                reference=reference,
                normalized=normalize_quantity(
                    dict(
                        quantity="angular_separation",
                        components={"degree": "26", "arcminute": "45"},
                    )
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(
                (out["subject"], out["reference"], out["normalized"]["magnitude"]),
                ("Moon nearer limb", reference, "96300"),
            )
        row.update(
            quantity="right_ascension",
            role="calculation_intermediate",
            subject="midheaven",
            reference=None,
            normalized=normalize_quantity(
                dict(quantity="right_ascension", components={"degree": "34"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["subject"], out["quantity"], out["normalized"]["unit"]),
            ("midheaven", "right_ascension", "arcsecond"),
        )

    def test_scorpio_comparison_keeps_star_as_first_endpoint_and_pole_as_input(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            subject="middle star in forehead of Scorpio",
            reference="Mars",
            flags=["modern_star_id_unresolved"],
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components={"degree": "7", "arcminute": "18"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["subject"], out["reference"], out["normalized"]["magnitude"]),
            ("middle star in forehead of Scorpio", "Mars", "26280"),
        )
        row.update(
            quantity="calculation_angle",
            role="historical_input",
            subject="observatory pole",
            reference=None,
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="calculation_angle", components={"degree": "55", "arcminute": "53"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["role"], out["normalized"]["magnitude"]), ("historical_input", "201180")
        )

    def test_semidiameter_instruction_does_not_change_recorded_distance(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            reference="Moon",
            flags=["source_lunar_semidiameter_to_add"],
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components={"degree": "19", "arcminute": "10"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual((out["reference"], out["normalized"]["magnitude"]), ("Moon", "69000"))
        self.assertIn("source_lunar_semidiameter_to_add", out["flags"])

    def test_source_star_labels_and_supplied_witness_value_remain_distinct(self):
        from src.catalog import normalize_quantity

        pairs = [
            ("capram", "Aldebaran"),
            ("hircus", "Venus"),
            ("left foot of Erichthonius", "Venus"),
            ("Mars", "right foot of Erichthonius shared with horn of Taurus"),
        ]
        for subject, reference in pairs:
            row = self.fixture()
            row.update(
                quantity="angular_separation",
                role="recorded_reading",
                subject=subject,
                reference=reference,
                flags=["modern_star_id_unresolved"],
                normalized=normalize_quantity(
                    dict(
                        quantity="angular_separation", components={"degree": "9", "arcminute": "47"}
                    )
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(
                (out["subject"], out["reference"], out["normalized"]["magnitude"]),
                (subject, reference, "35220"),
            )
        row.update(
            role="editorial_addition",
            flags=["source_value_restored_from_witness", "not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components={"degree": "9", "arcminute": "11"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["role"], out["normalized"]["magnitude"]), ("editorial_addition", "33060")
        )
        self.assertIn("source_value_restored_from_witness", out["flags"])

    def test_knee_reference_preserves_the_unqualified_source_label(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            reference="knee of Erichthonius",
            flags=["modern_star_id_unresolved"],
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components={"degree": "14", "arcminute": "22"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["subject"], out["reference"], out["normalized"]["magnitude"]),
            ("Mars", "knee of Erichthonius", "51720"),
        )
        self.assertIn("modern_star_id_unresolved", out["flags"])

    def test_unresolved_recorded_clock_keeps_time_unit_and_rejects_invented_scalar(self):
        row = self.fixture()
        row.update(
            quantity="recorded_clock",
            role="recorded_clock",
            subject="observing clock",
            reference=None,
            direction=None,
            components={},
            source_expression="At the half of the ninth",
            flags=["source_notation_unresolved", "absolute_time_unestablished"],
            normalized=dict(
                status="unsupported",
                unit="second_of_time",
                magnitude=None,
                magnitude_degrees=None,
                signed_magnitude=None,
                least_component_unit=None,
                normalization_issue="source_notation_unresolved",
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["quantity"], out["normalized"]["unit"], out["normalized"]["magnitude"]),
            ("recorded_clock", "second_of_time", None),
        )
        for change in (
            dict(subject="Mars"),
            dict(reference="Aldebaran"),
            dict(role="calculation_epoch"),
            dict(direction="south"),
            dict(components={"hour": "8 1/2"}),
            dict(flags=["source_notation_unresolved"]),
            dict(normalized=dict(row["normalized"], magnitude="30600")),
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **change))

    def test_moon_horn_gap_keeps_native_diameter_fraction_and_limb_endpoint(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="source_fraction",
            role="recorded_reading",
            subject="Moon lower horn",
            reference="Mars",
            source_fraction_kind="lunar_diameter",
            comparison_relation="limb_separation_as_stated",
            flags=[
                "source_visual_estimate",
                "geometry_interpretation_unestablished",
                "source_upper_bound",
            ],
            normalized=normalize_quantity(
                dict(quantity="source_fraction", components={"fraction": "1/6"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["normalized"]["magnitude"], out["normalized"]["unit"]), ("1/6", "source_fraction")
        )
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        for change in (
            dict(subject="Moon centre"),
            dict(reference="Aldebaran"),
            dict(role="calibration"),
            dict(flags=["source_visual_estimate", "geometry_interpretation_unestablished"]),
            dict(direction="south"),
            dict(
                normalized=normalize_quantity(
                    dict(quantity="source_fraction", components={"fraction": "2"})
                )
            ),
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **change))

    def test_conditional_globe_correction_is_not_a_reported_application(self):
        from src.catalog import normalize_quantity

        for amount in ("4", "1/2"):
            row = self.fixture()
            row.update(
                quantity="separation_correction",
                role="historical_correction",
                source_correction_operation="add",
                source_correction_application="conditional_not_reported_applied",
                flags=["not_an_additional_raw_reading"]
                + (["source_upper_bound"] if amount == "4" else []),
                normalized=normalize_quantity(
                    dict(quantity="separation_correction", components={"arcminute": amount})
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(
                out["source_correction_application"], "conditional_not_reported_applied"
            )
            self.assertEqual(out["normalized"]["magnitude"], "240" if amount == "4" else "30")
            for change in (
                dict(subject="Jupiter"),
                dict(role="recorded_reading"),
                dict(source_correction_operation="subtract"),
                dict(flags=[]),
            ):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **change))

    def test_stadius_reported_longitude_error_keeps_attribution_and_source_sign(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="longitude_difference",
            role="historical_comparison",
            model_name="Stadius",
            comparison_relation="coordinate_difference",
            source_comparison_sign="plus",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="longitude_difference", components={"degree": "1", "arcminute": "10"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["model_name"], out["source_comparison_sign"], out["normalized"]["magnitude"]),
            ("Stadius", "plus", "4200"),
        )
        for changes in (
            dict(subject="Jupiter"),
            dict(comparison_relation="observed error"),
            dict(model_name="unreviewed model"),
            dict(event_id="event-v10-aaaaaaaaaaaaaaaaaaaa"),
            dict(quantity="parallax_angle"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_calibration_fraction_does_not_invent_angular_units_or_apply_correction(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="source_fraction",
            role="calibration",
            subject="Aldebaran",
            reference="northern horn of Taurus",
            source_fraction_kind="calibration_difference_unit_unstated",
            comparison_relation="less_than_both_as_stated",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="source_fraction", components={"fraction": "1/6"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "1/6")
        self.assertEqual(out["normalized"]["unit"], "source_fraction")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        for changes in (
            dict(role="historical_correction"),
            dict(subject="Mars"),
            dict(reference=None),
            dict(direction="south"),
            dict(flags=[]),
            dict(comparison_relation="subtract_from_all_readings"),
            dict(
                normalized=normalize_quantity(
                    dict(quantity="angular_separation", components={"degree": "1/6"})
                )
            ),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_restored_manuscript_endpoint_does_not_replace_the_missing_recorded_endpoint(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            reference=None,
            source_reference_status="not_recorded",
            editorial_reference_alternative="lowest of three foremost stars of Leo",
            editorial_reference_status="restored_from_witness",
            flags=["source_quality_note_present"],
            normalized=normalize_quantity(
                dict(quantity="angular_separation", components={"degree": "3", "arcminute": "40"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertIsNone(out["reference"])
        self.assertEqual(out["editorial_reference_status"], "restored_from_witness")
        self.assertEqual(
            out["editorial_reference_alternative"], "lowest of three foremost stars of Leo"
        )
        for changes in (
            dict(reference="heart of Leo"),
            dict(source_reference_status=None),
            dict(editorial_reference_status="computed_guess"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_historical_stellar_sines_keep_unknown_scale_and_native_values(self):
        from src.catalog import normalize_quantity

        for value in ["17", "556", "560", "180", "593"]:
            row = self.fixture()
            row.update(
                quantity="source_scalar",
                role="historical_input",
                subject="stellar calibration calculation",
                reference=None,
                direction=None,
                source_parameter_kind="sine_value_scale_unstated",
                flags=["not_an_additional_raw_reading"],
                normalized=normalize_quantity(
                    dict(quantity="source_scalar", components={"scalar": value})
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["normalized"]["magnitude"], value)
            self.assertIsNone(out["normalized"]["magnitude_degrees"])
            for change in [
                dict(source_scalar_scale="100000"),
                dict(subject="Mars"),
                dict(role="recorded_reading"),
            ]:
                with self.subTest(change=change), self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **change))

    def test_unassigned_table_angle_and_literal_Aries_origin_remain_unresolved(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            subject="unassigned table entry",
            quantity="unclassified_angle",
            role="recorded_reading",
            flags=["measurement_type_unresolved"],
            normalized=normalize_quantity(
                dict(quantity="unclassified_angle", components={"degree": "6", "arcminute": "27"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["subject"], "unassigned table entry")
        self.assertIsNone(out["event_id"])
        row = self.fixture()
        row.update(
            quantity="ecliptic_longitude",
            role="reduction",
            source_longitude_origin="first_point_of_Aries_as_stated",
            normalized=normalize_quantity(
                dict(quantity="ecliptic_longitude", components={"degree": "119¾"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "431100")
        self.assertEqual(out["source_longitude_origin"], "first_point_of_Aries_as_stated")
        self.assertNotIn("zodiac_longitude_degrees", out["normalized"])

    def test_lunar_proportional_minutes_remain_a_coefficient(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="proportional_minutes",
            role="historical_input",
            subject="Moon",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(
                    quantity="proportional_minutes",
                    components={"proportional_minute": "47", "proportional_second": "29"},
                )
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "2849/3600")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        for change in (dict(role="recorded_reading"), dict(subject="Sun"), dict(flags=[])):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **change))

    def test_lunar_table_predictions_keep_model_and_explicit_zodiac(self):
        from src.catalog import normalize_quantity

        for model in ("Prutenic", "Alphonsine", "Leovitius"):
            row = self.fixture()
            row.update(
                quantity="ecliptic_longitude",
                role="historical_prediction",
                subject="Moon",
                reference=None,
                direction=None,
                model_name=model,
                flags=["not_an_additional_raw_reading"],
                normalized=normalize_quantity(
                    dict(
                        quantity="ecliptic_longitude",
                        components={"degree": "4", "arcminute": "20"},
                        zodiac_sign="Gemini",
                    )
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["model_name"], model)
            self.assertEqual(out["normalized"]["zodiac_longitude_degrees"], "193/3")
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, event_id="event-v10-0123456789abcdefabcd"))

    def test_source_time_scale_does_not_label_an_angle_or_invent_modern_time(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="calculation_epoch",
            role="calculation_epoch",
            subject="Moon",
            reference=None,
            direction=None,
            source_time_scale="apparent",
            normalized=normalize_quantity(
                dict(quantity="calculation_epoch", components={"hour": "7", "minute": "5½"})
            ),
        )
        self.assertEqual(self.module().public_assertion(row)["source_time_scale"], "apparent")
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, source_time_scale="UTC"))
        row = self.fixture()
        row["source_time_scale"] = "equal"
        with self.assertRaises(ValueError):
            self.module().public_assertion(row)

    def test_augsburg_instrument_bias_keeps_operation_without_automatic_application(self):
        from src.catalog import normalize_quantity

        for bias, operation, components, want in [
            ("high", "subtract", {"degree": "1", "arcminute": "50"}, "6600"),
            ("low", "add", {"arcminute": "4"}, "240"),
        ]:
            row = self.fixture()
            row.update(
                quantity="instrument_separation_bias",
                role="historical_correction",
                subject="Augsburg instrument separations",
                reference=None,
                direction=None,
                flags=["not_an_additional_raw_reading"],
                source_bias_direction=bias,
                source_correction_operation=operation,
                source_correction_application="individual_application_unestablished",
                normalized=normalize_quantity(
                    dict(quantity="instrument_separation_bias", components=components)
                ),
            )
            if bias == "high":
                high = copy.deepcopy(row)
            try:
                out = self.module().public_assertion(row)
            except ValueError as error:
                self.fail("Instrument calibration must retain its limited operation: " + str(error))
            self.assertEqual(out["normalized"]["magnitude"], want)
            self.assertEqual(out["source_correction_operation"], operation)
            self.assertEqual(
                out["source_correction_application"], "individual_application_unestablished"
            )
            self.assertIsNone(out["direction"])
            self.assertIsNone(out["event_id"])
        for change in (
            dict(quantity="parallax_angle"),
            dict(subject="Mars"),
            dict(reference="Earth"),
            dict(direction="north"),
            dict(event_id="event-v10-0123456789abcdefabcd"),
            dict(source_bias_direction="low"),
            dict(source_correction_operation=None),
            dict(source_correction_application="applied_to_all"),
            dict(flags=[]),
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_assertion(dict(high, **change))

    def test_named_ephemeris_latitudes_preserve_hemisphere_without_inventing_one(self):
        from src.catalog import normalize_quantity

        for model, direction in [("Stadius", None), ("Stadius", "north"), ("Carelli", "south")]:
            row = self.fixture()
            row.update(
                quantity="ecliptic_latitude",
                role="historical_prediction",
                subject="Mars",
                reference=None,
                direction=direction,
                model_name=model,
                flags=["not_an_additional_raw_reading"],
            )
            row["normalized"] = normalize_quantity(
                dict(
                    quantity="ecliptic_latitude",
                    direction=direction,
                    components=dict(degree="1", arcminute="45"),
                )
            )
            try:
                out = self.module().public_assertion(row)
            except ValueError as error:
                self.fail(
                    "Named ephemeris latitude must retain its source hemisphere: " + str(error)
                )
            self.assertEqual(out["model_name"], model)
            self.assertEqual(out["normalized"]["magnitude"], "6300")
            self.assertEqual(out["direction"], direction)
            self.assertEqual(
                out["normalized"]["signed_magnitude"],
                {"north": "6300", "south": "-6300"}.get(direction),
            )
        for change in (
            dict(event_id="event-v10-0123456789abcdefabcd"),
            dict(reference="Earth"),
            dict(flags=[]),
            dict(direction="east"),
            dict(model_name="unreviewed model"),
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_assertion(bad)
        bad = copy.deepcopy(row)
        bad["direction"] = None
        bad["normalized"] = normalize_quantity(
            dict(quantity="ecliptic_latitude", components=dict(degree="91"))
        )
        with self.assertRaises(ValueError):
            self.module().public_assertion(bad)

    def module(self):
        return importlib.import_module("src.public_checkpoint")

    def fixture(self):
        return dict(
            id="assertion-v10-0123456789abcdefabcd",
            volume=10,
            printed_page=385,
            quantity="declination",
            role="recorded_coordinate",
            subject="Mars",
            reference=None,
            direction=None,
            event_id=None,
            variant_of_id=None,
            series_id=None,
            ordinal=None,
            record_status=None,
            normalized=dict(
                status="exact",
                magnitude="62415",
                magnitude_degrees="4161/240",
                signed_magnitude=None,
                unit="arcsecond",
                least_component_unit="arcminute",
            ),
            text_original="PRIVATE SOURCE TEXT",
            source="/private/library",
            context_ids=["private-context"],
        )

    def test_endnote_marker_cannot_license_an_unpaged_observation(self):
        from src.normalization import normalize_quantity

        row = dict(
            self.fixture(),
            printed_page=None,
            edition_note_marker="[^ed7]",
            quantity="calculation_angle",
            role="editorial_suggestion",
            subject="Mars",
            components={"arcminute": "47"},
            source_expression="47′",
            annotation_of_id="assertion-v10-aaaaaaaaaaaaaaaaaaaa",
            flags=[
                "source_annotation_variant",
                "not_an_additional_raw_reading",
                "alternative_suggestion_not_applied",
            ],
        )
        row["normalized"] = normalize_quantity(row)
        public = self.module().public_assertion(row)
        self.assertEqual(public["edition_note_marker"], "[^ed7]")
        self.assertIsNone(public["printed_page"])
        for changes in (
            dict(role="recorded_reading"),
            dict(role="historical_input"),
            dict(flags=[]),
            dict(edition_note_marker="not a note"),
            dict(edition_note_marker=None),
            dict(annotation_of_id=None),
            dict(annotation_of_id=row["id"]),
            dict(event_id="event-v10-aaaaaaaaaaaaaaaaaaaa"),
            dict(printed_page=385),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_export_projects_nested_fields_and_excludes_private_payload(self):
        row = self.fixture()
        row["normalized"]["private_note"] = "PRIVATE NOTE"
        result = self.module().public_assertion(row)
        self.assertNotIn("text_original", result)
        self.assertNotIn("source", result)
        self.assertNotIn("context_ids", result)
        self.assertNotIn("private_note", result["normalized"])
        self.assertEqual(result["normalized"]["magnitude"], "62415")

    def test_descriptive_endpoints_do_not_require_modern_star_identifications(self):
        for reference in (
            "little star below heart of Leo",
            "highest and northernmost star of three hinder feet of Leo",
            "middle of three foremost stars of Leo",
            "belly of Leo",
            "uppermost of three hindmost stars of Leo",
            "lowest of three foremost stars of Leo",
            "star in flank of Leo",
            "star behind heart in belly of Leo",
            "bright one of three hindmost stars of Leo",
            "third and lower of three hindmost stars of Leo",
            "middle of three hindmost stars of Leo",
            "star following three hindmost stars of Leo toward south",
            "southern and following star of the left hind foot",
            "lower preceding star in quadrangle of Ursa Major",
            "lower following star in quadrangle of Ursa Major",
            "lower preceding star in quadrangle of the Bear",
            "Markab of Pegasus",
            "extreme star of wing of Pegasus",
            "second star in head of Fish",
            "sixth star in breast of Fish",
            "first star in neck of Pegasus",
            "middle star in neck of Pegasus",
            "more northern star in back of head of Hydra",
            "bright star of neck of Leo",
            "middle star in neck of Leo",
            "small star in belly of Leo",
            "neck of Leo",
            "northern Ass",
            "southern Ass",
            "southern star in head of Leo",
            "preceding shoulder of Orion",
            "Castor",
            "Dubhe",
            "back of Leo",
        ):
            row = self.fixture()
            row.update(
                quantity="angular_separation",
                role="recorded_reading",
                reference=reference,
                flags=["reference_star_modern_id_unresolved"],
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["reference"], reference)
            self.assertEqual(out["normalized"], {k: v for k, v in row["normalized"].items()})
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, reference="unreviewed modern identification"))

    def test_comet_measurements_keep_actual_target_and_source_precision(self):
        from src.catalog import normalize_quantity

        for quantity, reference, components, want in (
            (
                "angular_separation",
                "Markab of Pegasus",
                {"degree": "15", "arcminute": "20"},
                "55200",
            ),
            ("azimuth", None, {"degree": "21", "arcminute": "0"}, "75600"),
            ("altitude", None, {"degree": "30", "arcminute": "17"}, "109020"),
            ("angular_diameter", None, {"arcminute": "8"}, "480"),
        ):
            with self.subTest(quantity=quantity):
                row = self.fixture()
                row.update(
                    quantity=quantity,
                    role="recorded_reading",
                    subject="comet head",
                    reference=reference,
                    direction="east" if quantity == "azimuth" else None,
                    flags=[],
                    normalized=normalize_quantity(dict(quantity=quantity, components=components)),
                )
                out = self.module().public_assertion(row)
                self.assertEqual(out["subject"], "comet head")
                self.assertEqual(out["reference"], reference)
                self.assertEqual(out["normalized"]["magnitude"], want)
                self.assertEqual(out["normalized"]["unit"], "arcsecond")
                self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_comet_tail_length_preserves_exact_angle_and_actual_subject(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="angular_length",
            role="recorded_reading",
            subject="comet tail",
            reference=None,
            direction=None,
            flags=["source_visual_estimate"],
            normalized=normalize_quantity(
                dict(quantity="angular_length", components={"degree": "4½"})
            ),
        )
        self.assertEqual(row["normalized"]["magnitude"], "16200")
        out = self.module().public_assertion(row)
        self.assertEqual((out["quantity"], out["subject"]), ("angular_length", "comet tail"))
        self.assertEqual(out["normalized"]["magnitude_degrees"], "9/2")
        self.assertEqual(out["normalized"]["unit"], "arcsecond")
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        with self.assertRaises(ValueError):
            normalize_quantity(dict(quantity="angular_length", components={"hour": "4½"}))

    def test_mixed_table_stellar_readings_keep_literal_targets(self):
        from src.catalog import normalize_quantity

        for quantity, subject, reference, components, want in (
            (
                "angular_separation",
                "first star in neck of Pegasus",
                "middle star in neck of Pegasus",
                {"degree": "7", "arcminute": "37"},
                "27420",
            ),
            (
                "altitude",
                "Orion foot marked s.",
                None,
                {"degree": "25", "arcminute": "23"},
                "91380",
            ),
        ):
            with self.subTest(subject=subject):
                row = self.fixture()
                row.update(
                    quantity=quantity,
                    role="calibration",
                    subject=subject,
                    reference=reference,
                    flags=[],
                    normalized=normalize_quantity(dict(quantity=quantity, components=components)),
                )
                out = self.module().public_assertion(row)
                self.assertEqual((out["subject"], out["reference"]), (subject, reference))
                self.assertEqual(out["normalized"]["magnitude"], want)
                self.assertIsNone(out["normalized"]["signed_magnitude"])

    def test_visual_coefficient_preserves_literal_number_without_assigning_a_baseline(self):
        from src.catalog import normalize_quantity

        for value in ("1/2", "2"):
            row = self.fixture()
            row.update(
                quantity="source_scalar",
                role="recorded_reading",
                source_parameter_kind="visual_coefficient_as_stated",
                flags=["source_visual_estimate", "geometry_interpretation_unestablished"],
                normalized=normalize_quantity(
                    dict(quantity="source_scalar", components={"scalar": value})
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["normalized"]["magnitude"], value)
            self.assertEqual(out["normalized"]["unit"], "source_scalar")
            self.assertIsNone(out["normalized"]["magnitude_degrees"])
            self.assertIsNone(out["reference"])
            self.assertEqual(out["source_parameter_kind"], "visual_coefficient_as_stated")
            for changes in (
                dict(role="historical_input"),
                dict(subject="Mars calculation"),
                dict(reference="Jupiter"),
                dict(model_name="Copernicus"),
                dict(source_parameter_kind="comparison_multiplier"),
                dict(flags=["source_visual_estimate"]),
                dict(
                    normalized=normalize_quantity(
                        dict(quantity="source_scalar", components={"scalar": "0"})
                    )
                ),
            ):
                with self.subTest(value=value, changes=changes), self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **changes))

    def test_visual_separation_ratio_requires_its_baseline_and_estimate_status(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="separation_ratio",
            role="recorded_reading",
            reference="lower head of Gemini",
            separation_ratio_denominator=["lower head of Gemini", "upper head of Gemini"],
            flags=["source_approximate", "source_visual_estimate"],
            normalized=normalize_quantity(
                dict(quantity="separation_ratio", components={"ratio": "2"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            out["separation_ratio_denominator"], ["lower head of Gemini", "upper head of Gemini"]
        )
        self.assertEqual(
            (out["normalized"]["unit"], out["normalized"]["magnitude"]), ("ratio", "2")
        )
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        for changes in (
            dict(separation_ratio_denominator=None),
            dict(separation_ratio_denominator=["lower head of Gemini"] * 2),
            dict(separation_ratio_denominator=["lower head of Gemini", "private star"]),
            dict(flags=[]),
            dict(role="historical_correction"),
            dict(reference=None),
            dict(direction="north"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))
        with self.assertRaises(ValueError):
            self.module().public_assertion(
                dict(
                    self.fixture(),
                    separation_ratio_denominator=["lower head of Gemini", "upper head of Gemini"],
                )
            )

    def test_aselli_visual_quarter_preserves_two_descriptive_baseline_endpoints(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="separation_ratio",
            role="recorded_reading",
            reference="upper Asellus",
            separation_ratio_denominator=["upper Asellus", "lower Asellus"],
            flags=["source_approximate", "source_visual_estimate"],
            normalized=normalize_quantity(
                dict(quantity="separation_ratio", components={"ratio": "1/4"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["separation_ratio_denominator"], ["upper Asellus", "lower Asellus"])
        self.assertEqual(
            (out["normalized"]["magnitude"], out["normalized"]["unit"]), ("1/4", "ratio")
        )
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        self.assertIsNone(out["direction"])
        for changes in (
            dict(separation_ratio_denominator=["upper Asellus", "upper Asellus"]),
            dict(direction="north"),
            dict(flags=[]),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_upper_gemini_head_altitude_retains_its_stellar_subject(self):
        row = self.fixture()
        row.update(quantity="altitude", role="recorded_reading", subject="upper head of Gemini")
        out = self.module().public_assertion(row)
        self.assertEqual(out["subject"], "upper head of Gemini")
        self.assertEqual(out["normalized"]["magnitude"], row["normalized"]["magnitude"])
        self.assertNotIn("modern_star_id", out)

    def test_hours_before_sunrise_are_approximate_durations_not_clock_readings(self):
        from src.catalog import normalize_quantity

        for hour in ("3", "4"):
            row = self.fixture()
            row.update(
                quantity="clock_elapsed_time",
                role="recorded_reading",
                time_reference="elapsed_before_sunrise",
                flags=["source_approximate"],
                normalized=normalize_quantity(
                    dict(quantity="clock_elapsed_time", components={"hour": hour})
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["time_reference"], "elapsed_before_sunrise")
            self.assertEqual(out["normalized"]["magnitude"], str(int(hour) * 3600))
            self.assertIn("source_approximate", out["flags"])
            for changes in (dict(quantity="recorded_clock"), dict(role="calculation_epoch")):
                with self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **changes))

    def test_hour_before_twilight_preserves_the_relative_anchor_without_claiming_a_clock(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="clock_elapsed_time",
            role="recorded_reading",
            time_reference="elapsed_before_twilight",
            flags=[],
            normalized=normalize_quantity(
                dict(quantity="clock_elapsed_time", components={"hour": "1"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["time_reference"], out["normalized"]["magnitude"]),
            ("elapsed_before_twilight", "3600"),
        )
        self.assertNotIn("source_approximate", out["flags"])
        self.assertIsNone(out["event_id"])
        for changes in (
            dict(quantity="recorded_clock"),
            dict(role="calculation_epoch"),
            dict(direction="east"),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_after_meridian_duration_keeps_its_subject_without_becoming_a_clock(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="clock_elapsed_time",
            role="recorded_reading",
            time_reference="elapsed_after_meridian_transit",
            subject="Mars",
            normalized=normalize_quantity(
                dict(quantity="clock_elapsed_time", components={"hour": "2"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["time_reference"], out["normalized"]["magnitude"]),
            ("elapsed_after_meridian_transit", "7200"),
        )
        self.assertIsNone(out["event_id"])
        for changes in (
            dict(quantity="transit_clock"),
            dict(role="calculation_epoch"),
            dict(subject="Sun"),
            dict(direction="east"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_before_meridian_duration_is_not_a_transit_clock_or_altitude_epoch(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="clock_elapsed_time",
            role="recorded_reading",
            time_reference="elapsed_before_meridian_transit",
            normalized=normalize_quantity(
                dict(quantity="clock_elapsed_time", components={"hour": "1"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["time_reference"], out["normalized"]["magnitude"]),
            ("elapsed_before_meridian_transit", "3600"),
        )
        for changes in (
            dict(quantity="transit_clock"),
            dict(subject="Sun"),
            dict(role="reduction"),
            dict(direction="east"),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_sextant_shortfall_is_an_instrument_bias_without_an_invented_application(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="instrument_separation_bias",
            role="historical_correction",
            subject="sextant separations",
            flags=["not_an_additional_raw_reading"],
            source_bias_direction="low",
            source_correction_application="individual_application_unestablished",
            normalized=normalize_quantity(
                dict(quantity="instrument_separation_bias", components={"arcminute": "1 1/2"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["normalized"]["magnitude"], out["source_bias_direction"]), ("90", "low")
        )
        self.assertNotIn("source_correction_operation", out)
        for changes in (
            dict(subject="Mars"),
            dict(quantity="parallax_angle"),
            dict(source_bias_direction="high"),
            dict(source_correction_operation="add"),
            dict(source_correction_application="applied_to_all"),
            dict(flags=[]),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_sextant_readings_and_east_armillae_angles_retain_distinct_instrument_scopes(self):
        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="calibration",
            subject="heart of Leo",
            reference="Canis Minor",
            source_instrument_label="sextant",
        )
        self.assertEqual(self.module().public_assertion(row)["source_instrument_label"], "sextant")
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, role="expected_calibration"))
        row.update(
            quantity="meridian_distance",
            role="recorded_reading",
            subject="tail of Leo",
            reference="meridian",
            direction="east",
        )
        for label in ("armillae", "equatorial armillae"):
            row["source_instrument_label"] = label
            self.assertEqual(self.module().public_assertion(row)["source_instrument_label"], label)
            for changes in (
                dict(quantity="azimuth"),
                dict(reference=None),
                dict(direction=None),
                dict(subject="Mars"),
            ):
                with self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **changes))

    def test_approximate_lunar_phase_interval_is_separate_from_mars_timing(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="clock_elapsed_time",
            role="recorded_reading",
            subject="Moon",
            time_reference="elapsed_after_lunar_quadrature",
            flags=["source_approximate"],
            normalized=normalize_quantity(
                dict(quantity="clock_elapsed_time", components={"day": "2"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "172800")
        self.assertEqual(out["subject"], "Moon")
        for changes in (
            dict(subject="Mars"),
            dict(quantity="recorded_clock"),
            dict(role="reduction"),
            dict(flags=[]),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_reported_altitude_bias_preserves_qualified_application_without_a_per_record_operation(
        self,
    ):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="instrument_altitude_bias",
            role="historical_correction",
            subject="Benatky altitude instruments",
            flags=["not_an_additional_raw_reading"],
            source_bias_direction="high",
            source_correction_application="corrected_where_found_individual_application_unestablished",
            normalized=normalize_quantity(
                dict(quantity="instrument_altitude_bias", components={"arcminute": "2"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["normalized"]["unit"], out["normalized"]["magnitude"]), ("arcsecond", "120")
        )
        self.assertEqual(out["source_bias_direction"], "high")
        self.assertEqual(out["source_correction_application"], row["source_correction_application"])
        self.assertNotIn("source_correction_operation", out)
        for changes in (
            dict(subject="Mars"),
            dict(role="recorded_reading"),
            dict(flags=[]),
            dict(source_bias_direction="low"),
            dict(source_correction_operation="subtract"),
            dict(source_correction_application="applied_to_all_readings"),
            dict(event_id="event-v10-0123456789abcdefabcd"),
            dict(direction="north"),
            dict(quantity="parallax_angle"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_supporting_stellar_and_lunar_altitudes_keep_their_literal_subjects(self):
        for subject in (
            "bright star of neck of Leo",
            "Moon upper horn",
            "Hydra",
            "left foot of Orion",
        ):
            row = self.fixture()
            row.update(subject=subject, quantity="altitude", role="recorded_reading")
            self.assertEqual(self.module().public_assertion(row)["subject"], subject)

    def test_sextant_altitude_label_does_not_identify_an_instrument_for_derived_coordinates(self):
        for label in ("sextant", "iron quadrant"):
            row = self.fixture()
            row.update(quantity="altitude", role="recorded_reading", source_instrument_label=label)
            self.assertEqual(self.module().public_assertion(row)["source_instrument_label"], label)
            for changes in (dict(quantity="right_ascension"), dict(role="reduction")):
                with self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **changes))

    def test_comparison_star_coordinates_keep_the_literal_subject_and_unknown_hemisphere(self):
        from src.catalog import normalize_quantity

        subject = "lower following star in quadrangle of Ursa Major"
        for quantity, components, extra in (
            ("ecliptic_longitude", {"degree": "25", "arcminute": "45"}, {"zodiac_sign": "Leo"}),
            ("ecliptic_latitude", {"degree": "47", "arcminute": "6 1/2"}, {}),
        ):
            row = self.fixture()
            row.update(
                subject=subject,
                quantity=quantity,
                role="historical_input",
                flags=["not_an_additional_raw_reading"],
                normalized=normalize_quantity(
                    dict(quantity=quantity, components=components, **extra)
                ),
                **extra,
            )
            out = self.module().public_assertion(row)
            self.assertEqual(
                (out["subject"], out["role"], out["direction"]), (subject, "historical_input", None)
            )
            self.assertIsNone(out["normalized"]["signed_magnitude"])
            if quantity == "ecliptic_longitude":
                self.assertEqual(out["normalized"]["zodiac_longitude_degrees"], "583/4")
            else:
                self.assertEqual(out["normalized"]["magnitude"], "169590")
            self.assertNotIn("modern_star_id", out)

    def test_saturn_supporting_coordinates_preserve_body_sign_and_hemisphere(self):
        from src.catalog import normalize_quantity

        for quantity, components, extra in (
            (
                "ecliptic_longitude",
                {"degree": "0", "arcminute": "36"},
                {"zodiac_sign": "Capricorn"},
            ),
            ("ecliptic_latitude", {"degree": "1", "arcminute": "40"}, {"direction": "north"}),
        ):
            row = self.fixture()
            row.update(
                subject="Saturn",
                quantity=quantity,
                role="historical_input",
                flags=["not_an_additional_raw_reading"],
                normalized=normalize_quantity(
                    dict(quantity=quantity, components=components, **extra)
                ),
                **extra,
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["subject"], "Saturn")
            self.assertEqual(out["role"], "historical_input")
            if quantity == "ecliptic_longitude":
                self.assertEqual(out["normalized"]["zodiac_longitude_degrees"], "1353/5")
            else:
                self.assertEqual(
                    (out["direction"], out["normalized"]["signed_magnitude"]), ("north", "6000")
                )

    def test_named_ephemerides_keep_positions_and_computed_distances_distinct(self):
        from src.catalog import normalize_quantity

        for model in ("Stadius", "Carelli"):
            for subject, quantity, reference, components, sign, want in (
                (
                    "Moon",
                    "ecliptic_longitude",
                    None,
                    {"degree": "5", "arcminute": "0"},
                    "Cancer",
                    "18000",
                ),
                (
                    "Saturn",
                    "ecliptic_longitude",
                    None,
                    {"degree": "27", "arcminute": "42"},
                    "Cancer",
                    "99720",
                ),
                (
                    "Mars",
                    "angular_separation",
                    "Venus",
                    {"degree": "19", "arcminute": "22"},
                    None,
                    "69720",
                ),
                ("Saturn", "longitude_difference", "Mars", {"arcminute": "10"}, None, "600"),
                ("Saturn", "latitude_difference", "Mars", {"arcminute": "44"}, None, "2640"),
            ):
                row = self.fixture()
                row.update(
                    subject=subject,
                    quantity=quantity,
                    reference=reference,
                    role="historical_prediction",
                    model_name=model,
                    flags=["not_an_additional_raw_reading"],
                    normalized=normalize_quantity(
                        dict(
                            quantity=quantity,
                            components=components,
                            **({"zodiac_sign": sign} if sign else {}),
                        )
                    ),
                )
                out = self.module().public_assertion(row)
                self.assertEqual(
                    (out["model_name"], out["quantity"], out["subject"]), (model, quantity, subject)
                )
                self.assertEqual(out["normalized"]["magnitude"], want)
                for changes in (
                    dict(subject="Spica"),
                    dict(model_name="unreviewed ephemeris"),
                    dict(event_id="event-v10-0123456789abcdefabcd"),
                    dict(flags=[]),
                    dict(quantity="declination"),
                ):
                    with self.subTest(model=model, changes=changes), self.assertRaises(ValueError):
                        self.module().public_assertion(dict(row, **changes))

    def test_unnamed_solar_calculation_preserves_attribution_uncertainty(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="ecliptic_longitude",
            role="historical_prediction",
            subject="Sun",
            argument_name="equated_longitude",
            model_name=None,
            source_model_attribution="unnamed_as_stated",
            source_model_label="our calculation",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(
                    quantity="ecliptic_longitude",
                    components={"degree": "14", "arcminute": "8"},
                    zodiac_sign="Aquarius",
                )
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_model_label"], "our calculation")
        self.assertIsNone(out["model_name"])
        self.assertEqual(out["normalized"]["magnitude"], "50880")
        alternate = dict(row, source_model_label="our own rectification")
        self.assertEqual(
            self.module().public_assertion(alternate)["source_model_label"],
            "our own rectification",
        )
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(alternate, subject="Jupiter"))
        for changes in (
            dict(subject="Spica"),
            dict(source_model_label="our restitution"),
            dict(model_name="Copernicus"),
            dict(flags=[]),
            dict(role="recorded_reading"),
            dict(source_model_attribution=None),
            dict(event_id="event-v10-0123456789abcdefabcd"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_unnamed_planetary_calculation_keeps_missing_coordinate_origins(self):
        from src.catalog import normalize_quantity

        for quantity, components, flag in (
            (
                "ecliptic_longitude",
                {"degree": "3", "arcminute": "43", "arcsecond": "23"},
                "zodiac_sign_unstated",
            ),
            (
                "ecliptic_latitude",
                {"degree": "2", "arcminute": "19", "arcsecond": "26"},
                "hemisphere_unspecified",
            ),
        ):
            row = self.fixture()
            row.update(
                quantity=quantity,
                components=components,
                subject="Saturn",
                role="historical_prediction",
                model_name=None,
                source_model_attribution="unnamed_as_stated",
                source_model_label="our calculation",
                flags=["not_an_additional_raw_reading", flag],
                normalized=normalize_quantity(dict(quantity=quantity, components=components)),
            )
            if quantity == "ecliptic_longitude":
                row["argument_name"] = "equated_longitude"
            out = self.module().public_assertion(row)
            self.assertIsNone(out["normalized"]["signed_magnitude"])
            self.assertNotIn("zodiac_longitude_degrees", out["normalized"])
            self.assertEqual(out["source_model_label"], "our calculation")
            for changes in (
                dict(flags=["not_an_additional_raw_reading"]),
                dict(source_model_attribution=None),
                dict(subject="Spica"),
                dict(model_name="Copernicus"),
            ):
                with (
                    self.subTest(quantity=quantity, changes=changes),
                    self.assertRaises(ValueError),
                ):
                    self.module().public_assertion(dict(row, **changes))

    def test_unnamed_source_model_keeps_its_label_without_inventing_attribution(self):
        row = self.fixture()
        row.update(
            quantity="calculation_angle",
            role="historical_prediction",
            argument_name="equated_longitude",
            model_name=None,
            source_model_attribution="unnamed_as_stated",
            source_model_label="our restitution",
            flags=["not_an_additional_raw_reading"],
        )
        try:
            out = self.module().public_assertion(row)
        except ValueError as error:
            self.fail(f"Unidentified source prediction must retain its uncertainty: {error}")
        self.assertIsNone(out["model_name"])
        self.assertEqual(out["source_model_label"], "our restitution")
        self.assertEqual(out["source_model_attribution"], "unnamed_as_stated")
        comparison = dict(
            row,
            quantity="longitude_difference",
            role="historical_comparison",
            comparison_relation="coordinate_difference",
            source_comparison_sign="plus",
        )
        comparison.pop("argument_name")
        self.assertEqual(
            self.module().public_assertion(comparison)["source_comparison_sign"], "plus"
        )
        for changes in (
            dict(source_model_label="/private/model"),
            dict(source_model_label=None),
            dict(source_model_attribution=None),
            dict(model_name="Copernicus"),
            dict(quantity="declination"),
            dict(flags=[]),
            dict(role="calibration"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_comparative_fraction_preserves_literal_value_without_an_angular_interpolation(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="source_fraction",
            role="recorded_reading",
            source_fraction_kind="comparative_line_proximity",
            comparison_relation="nearer_by_fraction_as_stated",
            flags=["source_visual_estimate", "geometry_interpretation_unestablished"],
            normalized=normalize_quantity(
                dict(quantity="source_fraction", components={"fraction": "1/3"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "1/3")
        self.assertEqual(out["normalized"]["unit"], "source_fraction")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        self.assertEqual(out["comparison_relation"], "nearer_by_fraction_as_stated")
        self.assertNotIn("interpolation_fraction", out)
        for changes in (
            dict(role="reduction"),
            dict(flags=["source_visual_estimate"]),
            dict(comparison_relation="one_third_along_arc"),
            dict(subject="Jupiter"),
            dict(direction="north"),
            dict(
                normalized=normalize_quantity(
                    dict(quantity="source_fraction", components={"fraction": "2"})
                )
            ),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))
        historical = dict(
            row,
            role="historical_correction",
            source_fraction_kind="latitude_reconciliation",
            comparison_relation="greater_than_computed",
            flags=["not_an_additional_raw_reading"],
        )
        self.assertEqual(
            self.module().public_assertion(historical)["source_fraction_kind"],
            "latitude_reconciliation",
        )

    def test_stated_equal_value_requires_an_exact_matching_original(self):
        parent = self.fixture()
        parent.update(quantity="angular_separation", role="recorded_reading", reference="Aldebaran")
        row = copy.deepcopy(parent)
        row.update(
            id="assertion-v10-aaaaaaaaaaaaaaaaaaaa",
            reference="upper head of Gemini",
            components={},
            source_value_equal_to_id=parent["id"],
            flags=["source_value_stated_equal"],
        )
        exported = [self.module().public_assertion(x) for x in (parent, row)]
        self.assertEqual(exported[1].get("source_value_equal_to_id"), parent["id"])
        self.module().validate_links(exported, [], [])
        changed = copy.deepcopy(exported)
        changed[1]["normalized"]["magnitude"] = "62416"
        with self.assertRaises(ValueError):
            self.module().validate_links(changed, [], [])
        for changes in (
            dict(source_value_equal_to_id=None),
            dict(flags=[]),
            dict(components={"degree": "17"}),
            dict(quantity="declination"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_source_alternative_requires_its_original_and_unapplied_status(self):
        row = self.fixture()
        row.update(
            role="source_alternative",
            variant_of_id="assertion-v10-aaaaaaaaaaaaaaaaaaaa",
            flags=["alternative_suggestion_not_applied", "not_an_additional_raw_reading"],
        )
        try:
            result = self.module().public_assertion(row)
        except ValueError as error:
            self.fail(f"Source alternative must remain distinct from editorial correction: {error}")
        self.assertEqual(result["role"], "source_alternative")
        self.assertEqual(result["variant_of_id"], "assertion-v10-aaaaaaaaaaaaaaaaaaaa")
        for changes in (
            dict(variant_of_id=None),
            dict(flags=[]),
            dict(flags=["alternative_suggestion_not_applied"]),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_unclassified_angle_preserves_value_without_claiming_a_coordinate_type(self):
        row = self.fixture()
        row.update(
            quantity="unclassified_angle",
            role="recorded_reading",
            subject="tail of Leo",
            flags=["measurement_type_unresolved"],
        )
        result = self.module().public_assertion(row)
        self.assertEqual(result["quantity"], "unclassified_angle")
        self.assertEqual(result["flags"], ["measurement_type_unresolved"])
        self.assertEqual(result["normalized"], row["normalized"])
        for changes in (
            dict(flags=[]),
            dict(direction="east"),
            dict(reference="Mars"),
            dict(role="historical_input"),
            dict(quantity="altitude"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_polar_distance_remains_unsigned_source_input_without_declination_conversion(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="polar_distance",
            role="historical_input",
            subject="pole star",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(
                    quantity="polar_distance",
                    direction=None,
                    components={"degree": "2", "arcminute": "51 3/4"},
                )
            ),
        )
        self.assertEqual(row["normalized"]["magnitude"], "10305")
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["quantity"], out["normalized"]["magnitude_degrees"]), ("polar_distance", "229/80")
        )
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, direction="north"))

    def test_missing_reference_does_not_promote_editorial_proposal_to_observed_star(self):
        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            source_reference_status="not_recorded",
            editorial_reference_alternative="bright star of Aries",
            editorial_reference_status="tentative",
        )
        out = self.module().public_assertion(row)
        self.assertIsNone(out["reference"])
        self.assertEqual(out["source_reference_status"], "not_recorded")
        self.assertEqual(out["editorial_reference_alternative"], "bright star of Aries")
        self.assertEqual(out["editorial_reference_status"], "tentative")
        for changes in (
            {"source_reference_status": None},
            {"reference": "Aldebaran"},
            {"quantity": "declination"},
            {"editorial_reference_status": "certain"},
            {"editorial_reference_alternative": None},
            {"editorial_reference_alternative": "/private/star"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))
        unexplained = copy.deepcopy(row)
        unexplained.pop("source_reference_status")
        with self.assertRaises(ValueError):
            self.module().public_assertion(unexplained)
        legacy = self.fixture()
        legacy.update(
            quantity="angular_separation",
            role="recorded_reading",
            reference="bright star of Aries",
            editorial_reference_alternative="Aldebaran",
            flags=["source_endpoint_editorially_disputed"],
        )
        self.assertEqual(
            self.module().public_assertion(legacy)["reference"], "bright star of Aries"
        )

    def test_solar_observations_keep_sun_distinct_from_historical_model_suns(self):
        for subject in ("Sun", "mean Sun", "simple Sun"):
            row = self.fixture()
            row["subject"] = subject
            with self.subTest(subject=subject):
                result = self.module().public_assertion(row)
                self.assertEqual(result["subject"], subject)
                self.assertIsNone(result["direction"])

    def test_unresolved_notation_exports_known_quantity_without_a_chosen_angle(self):
        row = self.fixture()
        row.update(
            quantity="altitude",
            role="recorded_reading",
            components=None,
            flags=["source_notation_unresolved"],
            normalized=dict(
                status="unsupported",
                unit="arcsecond",
                magnitude=None,
                magnitude_degrees=None,
                signed_magnitude=None,
                least_component_unit=None,
                normalization_issue="source_notation_unresolved",
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["quantity"], "altitude")
        self.assertEqual(out["normalized"]["normalization_issue"], "source_notation_unresolved")
        self.assertIsNone(out["normalized"]["magnitude"])
        for changes in (
            dict(flags=[]),
            dict(components={"degree": "17", "arcminute": "20"}),
            dict(quantity="recorded_clock"),
            dict(normalized=dict(row["normalized"], magnitude="62400")),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_unresolved_source_epoch_is_not_exported_as_a_reconstructed_clock(self):
        row = self.fixture()
        row.update(
            quantity="calculation_epoch",
            role="calculation_epoch",
            components={},
            flags=[
                "source_notation_unresolved",
                "not_an_observing_clock",
                "not_an_additional_raw_reading",
            ],
            normalized=dict(
                status="unsupported",
                unit="second_of_time",
                magnitude=None,
                magnitude_degrees=None,
                signed_magnitude=None,
                least_component_unit=None,
                normalization_issue="source_notation_unresolved",
            ),
        )
        out = self.module().public_assertion(row)
        self.assertIsNone(out["normalized"]["magnitude"])
        for changes in (
            dict(quantity="recorded_clock"),
            dict(role="recorded_reading"),
            dict(components={"hour": "9", "minute": "32"}),
            dict(flags=["source_notation_unresolved"]),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_unnamed_model_prediction_can_retain_a_named_zodiac_longitude_and_unsigned_difference(
        self,
    ):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="ecliptic_longitude",
            role="historical_prediction",
            argument_name="equated_longitude",
            model_name=None,
            source_model_attribution="unnamed_as_stated",
            source_model_label="our restitution",
            flags=["not_an_additional_raw_reading"],
            zodiac_sign="Leo",
            normalized=normalize_quantity(
                dict(
                    quantity="ecliptic_longitude",
                    zodiac_sign="Leo",
                    components={"degree": "8", "arcminute": "19", "arcsecond": "48"},
                )
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["zodiac_longitude_degrees"], "12833/100")
        self.assertIsNone(out["model_name"])
        comparison = dict(
            row,
            quantity="longitude_difference",
            role="historical_comparison",
            comparison_relation="coordinate_difference",
            normalized=normalize_quantity(
                dict(
                    quantity="longitude_difference",
                    components={"arcminute": "1", "arcsecond": "24"},
                )
            ),
        )
        comparison.pop("argument_name")
        comparison.pop("zodiac_sign")
        self.assertNotIn("source_comparison_sign", self.module().public_assertion(comparison))
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, model_name="Copernicus"))

    def test_source_anomaly_label_does_not_claim_a_modern_anomaly_definition(self):
        row = self.fixture()
        row.update(
            quantity="calculation_angle",
            role="historical_input",
            argument_name="anomaly",
            flags=["not_an_additional_raw_reading"],
        )
        self.assertEqual(self.module().public_assertion(row)["argument_name"], "anomaly")
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, role="recorded_reading"))

    def test_unclassified_numeric_expression_exports_only_its_bounded_numeric_literal(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="unclassified_numeric_expression",
            role="calculation_intermediate",
            subject="Mars calculation",
            components={},
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="unclassified_numeric_expression", components={})
            ),
        )
        for expression in (
            "14′40″",
            "85′20″",
            "80 49",
            "4.30 [?]",
            "5248 | 58753",
            r"1\|8620848",
            "11867,954,041",
            "20‴ ½.",
            "15 minutes",
            "1 hour 30 minutes",
            "49 seconds 45 thirds",
            "42 [hours? days?]",
            "¼ minute",
            "½ second",
        ):
            row["source_expression"] = expression
            out = self.module().public_assertion(row)
            self.assertEqual(out["numeric_expression_original"], expression)
            self.assertIsNone(out["normalized"]["magnitude"])
            self.assertNotIn("text_original", out)
        lunar_argument = dict(
            row,
            subject="Moon calculation",
            role="historical_input",
            source_expression="0. 1. 31. 5.",
        )
        self.assertIsNone(self.module().public_assertion(lunar_argument)["normalized"]["magnitude"])
        for changes in (
            dict(source_expression="/home/private"),
            dict(source_expression="source prose"),
            dict(source_expression="12 minutes source prose"),
            dict(source_expression=r"1\n8620848"),
            dict(source_expression="minutes"),
            dict(source_expression="?"),
            dict(source_expression="1" * 81),
            dict(role="recorded_reading"),
            dict(flags=[]),
            dict(direction="north"),
            dict(components={"degree": "4"}),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_unclassified_calculation_numbers_support_other_bodies_without_inventing_units(self):
        from src.normalization import normalize_quantity

        for subject in (
            "Sun calculation",
            "New Star calculation",
            "fixed star calculation",
            "unidentified astronomical calculation",
        ):
            row = dict(
                self.fixture(),
                quantity="unclassified_numeric_expression",
                role="historical_input",
                subject=subject,
                reference=None,
                direction=None,
                components={},
                source_expression="358400",
                flags=["not_an_additional_raw_reading"],
            )
            row["normalized"] = normalize_quantity(row)
            out = self.module().public_assertion(row)
            self.assertEqual(out["numeric_expression_original"], "358400")
            self.assertEqual(out["normalized"]["unit"], "source_numeric_expression")
            self.assertIsNone(out["normalized"]["magnitude"])
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, role="recorded_reading"))

    def test_unclassified_word_numeral_keeps_units_unresolved_and_validates_conversion(self):
        from src.normalization import normalize_quantity

        row = dict(
            self.fixture(),
            quantity="unclassified_numeric_expression",
            role="historical_input",
            subject="New Star calculation",
            reference=None,
            direction=None,
            components={},
            source_expression="quadraginta",
            source_word_numbers={"quadraginta": "40"},
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["numeric_expression_original"], "quadraginta")
        self.assertEqual(out["source_word_numbers"], {"quadraginta": "40"})
        self.assertIsNone(out["normalized"]["magnitude"])
        ordinal = dict(row, source_expression="eighth parts", source_word_numbers={"eighth": "8"})
        ordinal["normalized"] = normalize_quantity(ordinal)
        ordinal_out = self.module().public_assertion(ordinal)
        self.assertEqual(ordinal_out["numeric_expression_original"], "eighth parts")
        self.assertIsNone(ordinal_out["normalized"]["magnitude"])
        for change in (
            {"source_word_numbers": {"quadraginta": "41"}},
            {"source_expression": "forty unknown words"},
            {"source_word_numbers": {}},
            {"source_word_numbers": {"unknown": None}},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **change))

    def test_unclassified_comet_reading_keeps_units_and_endpoint_unresolved(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="unclassified_numeric_expression",
            role="recorded_reading",
            subject="comet head",
            reference=None,
            direction=None,
            components={},
            source_expression="953. 190.",
            flags=["limb_or_instrument_setting_unresolved", "reference_antecedent_unresolved"],
            normalized=normalize_quantity(
                dict(quantity="unclassified_numeric_expression", components={})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["numeric_expression_original"], "953. 190.")
        self.assertEqual(out["normalized"]["status"], "unsupported")
        self.assertIsNone(out["normalized"]["magnitude"])
        for changes in (
            dict(flags=[]),
            dict(flags=["reference_antecedent_unresolved"]),
            dict(reference="Aldebaran"),
            dict(source_expression="953 degrees"),
            dict(source_expression="953"),
            dict(subject="Mars calculation"),
            dict(components={"degree": "953"}),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_greatest_latitude_parameter_can_be_a_derived_result_without_becoming_raw(self):
        row = self.fixture()
        row.update(
            quantity="ecliptic_latitude",
            role="reduction",
            direction="north",
            source_parameter_kind="greatest_northern_latitude",
            flags=["not_an_additional_raw_reading"],
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_parameter_kind"], "greatest_northern_latitude")
        for changes in (dict(role="recorded_reading"), dict(flags=[]), dict(direction="south")):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_corrected_longitude_input_does_not_invent_an_original_or_correction_amount(self):
        row = self.fixture()
        row.update(
            quantity="ecliptic_longitude",
            role="historical_input",
            source_coordinate_state="corrected_as_stated",
            flags=["not_an_additional_raw_reading"],
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_coordinate_state"], "corrected_as_stated")
        self.assertNotIn("source_correction_operation", out)
        for changes in (
            dict(role="recorded_coordinate"),
            dict(subject="Sun"),
            dict(flags=[]),
            dict(quantity="ecliptic_latitude"),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_four_repetitions_preserve_one_magnitude_and_the_source_count(self):
        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            reference="heart of Leo",
            source_repeat_count=4,
            source_repetition_label="four times",
            flags=["source_repetition_note_present"],
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_repeat_count"], 4)
        self.assertEqual(out["normalized"]["magnitude"], "62415")
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, source_repeat_count=3))

    def test_stellar_transit_duration_cannot_be_relabelled_as_an_observing_clock(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="clock_elapsed_time",
            role="recorded_reading",
            reference="head of Hydra",
            time_reference="elapsed_after_stellar_meridian_transit",
            flags=["source_approximate"],
            normalized=normalize_quantity(
                dict(quantity="clock_elapsed_time", components={"hour": "1/2"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["reference"], out["normalized"]["magnitude"]), ("head of Hydra", "1800")
        )
        for changes in (
            dict(quantity="recorded_clock"),
            dict(reference="Sun"),
            dict(flags=[]),
            dict(role="reduction"),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_acronychal_interval_keeps_approximation_without_an_absolute_opposition_epoch(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="clock_elapsed_time",
            role="historical_input",
            time_reference="elapsed_after_acronychal_position",
            flags=["source_approximate", "not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="clock_elapsed_time", components={"day": "5"})
            ),
        )
        self.assertEqual(self.module().public_assertion(row)["normalized"]["magnitude"], "432000")
        for changes in (
            dict(subject="Sun"),
            dict(reference="Sun"),
            dict(flags=[]),
            dict(role="recorded_reading"),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_prior_observation_duration_requires_a_different_source_reading_group(self):
        from src.catalog import normalize_quantity

        earlier = "event-v10-" + "1" * 20
        later = "event-v10-" + "2" * 20
        row = self.fixture()
        row.update(
            quantity="clock_elapsed_time",
            role="recorded_reading",
            event_id=later,
            time_reference="elapsed_after_prior_observations",
            source_time_anchor_event_id=earlier,
            flags=["source_approximate"],
            normalized=normalize_quantity(
                dict(quantity="clock_elapsed_time", components={"hour": "1/4"})
            ),
        )
        out = self.module().public_assertion(row)
        prior = self.fixture()
        prior.update(
            id="assertion-v10-" + "3" * 20,
            quantity="angular_separation",
            role="recorded_reading",
            event_id=earlier,
            reference="Regulus",
        )
        prior = self.module().public_assertion(prior)
        events = [
            dict(id=e, clock_assertion_id=None, epoch_assertion_id=None) for e in (earlier, later)
        ]
        self.module().validate_links([out, prior], events)
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, source_time_anchor_event_id=later))
        with self.assertRaises(ValueError):
            self.module().validate_links([out], events)
        out["source_date_claim_ids"] = ["context-v10-" + "a" * 20]
        prior["source_date_claim_ids"] = ["context-v10-" + "b" * 20]
        with self.assertRaises(ValueError):
            self.module().validate_links([out, prior], events)

    def test_editorial_stellar_subject_correction_keeps_recorded_label_and_angle(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="meridian_distance",
            role="calibration",
            subject="Greater Dog",
            direction="west",
            editorial_subject_alternative="Lesser Dog",
            editorial_subject_status="correction_as_stated",
            flags=["source_endpoint_editorially_disputed"],
            normalized=normalize_quantity(
                dict(
                    quantity="meridian_distance",
                    direction="west",
                    components={"degree": "23", "arcminute": "51"},
                )
            ),
        )
        for quantity, role, reference in (
            ("meridian_distance", "calibration", None),
            ("altitude", "recorded_reading", None),
            ("angular_separation", "recorded_reading", "Mars"),
        ):
            out = self.module().public_assertion(
                dict(row, quantity=quantity, role=role, reference=reference)
            )
            self.assertEqual(
                (
                    out["subject"],
                    out["editorial_subject_alternative"],
                    out["editorial_subject_status"],
                ),
                ("Greater Dog", "Lesser Dog", "correction_as_stated"),
            )
            self.assertEqual(out["reference"], reference)
            self.assertEqual(out["normalized"]["magnitude"], "85860")
        for changes in (
            dict(editorial_subject_alternative="Greater Dog"),
            dict(editorial_subject_alternative="/private/star"),
            dict(editorial_subject_alternative=None),
            dict(editorial_subject_status="tentative"),
            dict(role="historical_input"),
            dict(flags=[]),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))
        missing_status = copy.deepcopy(row)
        missing_status.pop("editorial_subject_status")
        with self.assertRaises(ValueError):
            self.module().public_assertion(missing_status)

    def test_jupiter_comparison_preserves_the_mouth_of_pegasus_endpoint(self):
        row = self.fixture()
        row.update(
            subject="Jupiter",
            reference="mouth of Pegasus",
            quantity="angular_separation",
            role="recorded_reading",
        )
        result = self.module().public_assertion(row)
        self.assertEqual((result["subject"], result["reference"]), ("Jupiter", "mouth of Pegasus"))
        self.assertNotIn("text_original", result)
        row.update(
            subject="mouth of Pegasus",
            reference=None,
            quantity="ecliptic_longitude",
            role="historical_input",
        )
        self.assertEqual(self.module().public_assertion(row)["subject"], "mouth of Pegasus")

    def test_september_mars_endpoints_preserve_source_labels_without_aliasing(self):
        for ref in ("bright foot of Gemini", "Aries reference marked 3"):
            row = self.fixture()
            row.update(quantity="angular_separation", role="historical_input", reference=ref)
            self.assertEqual(self.module().public_assertion(row)["reference"], ref)

    def test_october25_source_star_names_remain_distinct_without_modern_aliases(self):
        for reference in ("head of Medusa", "bright side of Perseus"):
            row = self.fixture()
            row.update(quantity="angular_separation", role="recorded_reading", reference=reference)
            out = self.module().public_assertion(row)
            self.assertEqual((out["subject"], out["reference"]), ("Mars", reference))
        for subject in (
            "Canicula",
            "Lesser Dog",
            "Greater Dog",
            "left shoulder of Orion",
            "right shoulder of Orion",
        ):
            row = self.fixture()
            row.update(
                quantity="meridian_distance", role="calibration", subject=subject, direction="west"
            )
            self.assertEqual(self.module().public_assertion(row)["subject"], subject)

    def test_perseus_reduction_preserves_stellar_subject_and_printed_vertex_order(self):
        row = self.fixture()
        row.update(
            subject="bright side of Perseus", quantity="ecliptic_latitude", role="historical_input"
        )
        with self.subTest(stellar_subject=True):
            self.assertEqual(
                self.module().public_assertion(row)["subject"], "bright side of Perseus"
            )
        for label in ("BD", "ABD", "ACB"):
            row = self.fixture()
            row.update(
                quantity="calculation_angle",
                role="calculation_intermediate",
                geometry_label=label,
                geometry_column=1,
            )
            with self.subTest(label=label):
                self.assertEqual(self.module().public_assertion(row)["geometry_label"], label)

    def test_gemini_reduction_preserves_head_and_foot_as_distinct_stellar_inputs(self):
        rows = []
        for star in ("lower head of Gemini", "bright foot of Gemini"):
            row = self.fixture()
            row.update(
                subject=star,
                role="historical_input",
                flags=["hemisphere_unspecified", "not_an_additional_raw_reading"],
            )
            rows.append(self.module().public_assertion(row))
        self.assertEqual(
            [row["subject"] for row in rows], ["lower head of Gemini", "bright foot of Gemini"]
        )
        self.assertTrue(all(row["direction"] is None for row in rows))

    def test_stellar_meridian_calibrations_keep_instrument_labels_and_roles(self):
        from src.catalog import normalize_quantity

        for label, minute, want in (
            ("steel instrument", "35 2/3", "200140"),
            ("revolving quadrant", "35 1/2", "200130"),
        ):
            row = self.fixture()
            row.update(
                subject="bright star of Aries",
                quantity="altitude",
                role="calibration",
                source_instrument_label=label,
                normalized=normalize_quantity(
                    dict(quantity="altitude", components={"degree": "55", "arcminute": minute})
                ),
            )
            with self.subTest(label=label):
                out = self.module().public_assertion(row)
                self.assertEqual(
                    (out["subject"], out["role"], out["source_instrument_label"]),
                    ("bright star of Aries", "calibration", label),
                )
                self.assertEqual(out["normalized"]["magnitude"], want)
                with self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, role="historical_input"))

    def test_october27_reference_names_and_repeated_calibrations_remain_source_claims(self):
        for ref in ("Capella", "first of Aries"):
            row = self.fixture()
            row.update(quantity="angular_separation", role="recorded_reading", reference=ref)
            with self.subTest(reference=ref):
                self.assertEqual(self.module().public_assertion(row)["reference"], ref)
        for subject in (
            "bright star of foot of Perseus",
            "first of Aries",
            "bright foot of Gemini",
            "Capella",
        ):
            row = self.fixture()
            row.update(subject=subject, role="calibration")
            with self.subTest(stellar_calibration=subject):
                self.assertEqual(self.module().public_assertion(row)["subject"], subject)
        row = self.fixture()
        row.update(
            quantity="angular_separation",
            subject="Aldebaran",
            reference="bright star of Aries",
            role="calibration",
            source_repeat_count=2,
            source_repetition_label="bis",
            flags=["source_repetition_note_present"],
        )
        with self.subTest(repeated_calibration=True):
            out = self.module().public_assertion(row)
            self.assertEqual(
                (out["role"], out["source_repeat_count"], out["source_repetition_label"]),
                ("calibration", 2, "bis"),
            )

    def test_separation_repeat_counts_preserve_once_twice_and_thrice_without_expanding_readings(
        self,
    ):
        for label, count in (
            ("semel", 1),
            ("once", 1),
            ("bis", 2),
            ("twice", 2),
            ("ter", 3),
            ("three times", 3),
            ("semel atque iterum", 2),
        ):
            row = self.fixture()
            row.update(
                quantity="angular_separation",
                role="recorded_reading",
                reference="upper head of Gemini",
                source_repeat_count=count,
                source_repetition_label=label,
                flags=["source_repetition_note_present"],
            )
            with self.subTest(label=label):
                out = self.module().public_assertion(row)
                self.assertEqual(
                    (out["source_repeat_count"], out["source_repetition_label"]), (count, label)
                )
                self.assertEqual(out["id"], row["id"])
                for changes in (
                    dict(source_repeat_count=count + 1),
                    dict(source_repeat_count=True),
                    dict(quantity="declination"),
                    dict(flags=[]),
                ):
                    with self.assertRaises(ValueError):
                        self.module().public_assertion(dict(row, **changes))

    def test_repeated_separation_keeps_explicit_twice_claim_as_one_record(self):
        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="repeated_reading",
            reference="heart of Leo",
            source_repeat_count=2,
            source_repetition_label="bis",
            flags=["source_repetition_note_present"],
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["role"], out["source_repeat_count"], out["id"]), ("repeated_reading", 2, row["id"])
        )
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(row, source_repeat_count=3))

    def test_radius_label_belongs_to_measured_separation_without_changing_its_value(self):
        row = self.fixture()
        row.update(
            quantity="angular_separation",
            role="recorded_reading",
            reference="bright foot of Gemini",
            source_instrument_label="Radius",
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["source_instrument_label"], out["subject"], out["reference"]),
            ("Radius", "Mars", "bright foot of Gemini"),
        )
        self.assertEqual(out["normalized"]["magnitude"], "62415")
        for changes in (
            dict(quantity="right_ascension"),
            dict(role="historical_prediction"),
            dict(source_instrument_label="unreviewed instrument"),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_channel_dimension_is_not_a_celestial_parallax_or_applied_correction(self):
        from src.catalog import normalize_quantity

        norm = normalize_quantity(
            dict(quantity="instrument_dimension_angle", components={"degree": "2/3"})
        )
        self.assertEqual(
            (norm["status"], norm["unit"], norm["magnitude"], norm["magnitude_degrees"]),
            ("exact", "arcsecond", "2400", "2/3"),
        )
        row = self.fixture()
        row.update(
            quantity="instrument_dimension_angle",
            role="historical_input",
            subject="Radius brass channel",
            flags=["not_an_additional_raw_reading"],
            normalized=norm,
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["quantity"], out["subject"], out["normalized"]["magnitude"]),
            ("instrument_dimension_angle", "Radius brass channel", "2400"),
        )
        for changes in (
            dict(quantity="parallax_angle"),
            dict(subject="Mars"),
            dict(role="recorded_reading"),
            dict(flags=[]),
            dict(reference="Earth"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_radius_shortfall_instruction_does_not_claim_a_correction_was_applied(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="separation_correction",
            role="historical_correction",
            subject="Radius separations",
            flags=["not_an_additional_raw_reading"],
            source_correction_operation="add",
            source_correction_application="instruction_not_reported_applied",
            normalized=normalize_quantity(
                dict(quantity="separation_correction", components={"arcminute": "4"})
            ),
        )
        before = copy.deepcopy(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "240")
        self.assertEqual(
            (out["source_correction_operation"], out["source_correction_application"]),
            ("add", "instruction_not_reported_applied"),
        )
        self.assertEqual(row, before)
        for changes in (
            dict(source_correction_application="applied_to_following_distances"),
            dict(subject="Mars"),
            dict(source_correction_operation="subtract"),
            dict(role="recorded_reading"),
            dict(flags=[]),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_declination_addition_is_a_separate_unapplied_angular_correction(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="declination_correction",
            role="historical_correction",
            source_correction_operation="add",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="declination_correction", components={"arcminute": "1"})
            ),
        )
        before = copy.deepcopy(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "60")
        self.assertEqual(out["source_correction_operation"], "add")
        self.assertNotIn("source_correction_application", out)
        self.assertEqual(row, before)

    def test_stellar_calibration_retains_unresolved_with_both_annotation(self):
        row = self.fixture()
        row.update(
            subject="Aldebaran",
            role="calibration",
            source_component_label="with both",
            flags=["limb_or_instrument_setting_unresolved", "source_repetition_note_present"],
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["subject"], out["role"], out["source_component_label"]),
            ("Aldebaran", "calibration", "with both"),
        )
        self.assertIsNone(out["direction"])
        for changes in (
            dict(quantity="recorded_clock"),
            dict(role="historical_input"),
            dict(flags=[]),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_declination_correction_operation_rejects_wrong_scope_and_raw_values(self):
        row = self.fixture()
        row.update(
            quantity="declination_correction",
            role="historical_correction",
            source_correction_operation="add",
            flags=["not_an_additional_raw_reading"],
        )
        for changes in (
            dict(role="recorded_reading"),
            dict(subject="Aldebaran"),
            dict(flags=[]),
            dict(source_correction_operation="multiply"),
            dict(source_correction_application="applied_to_following_distances"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_approximate_declination_subtraction_remains_an_unapplied_instruction(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="declination_correction",
            role="historical_correction",
            source_correction_operation="subtract",
            flags=["not_an_additional_raw_reading", "source_approximate"],
            normalized=normalize_quantity(
                dict(quantity="declination_correction", components={"arcminute": "2"})
            ),
        )
        before = copy.deepcopy(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "120")
        self.assertEqual(out["source_correction_operation"], "subtract")
        self.assertIn("source_approximate", out["flags"])
        self.assertNotIn("source_correction_application", out)
        self.assertEqual(row, before)
        for changes in (
            dict(role="recorded_coordinate"),
            dict(source_correction_operation="add_or_subtract"),
            dict(source_correction_application="applied_to_prior_readings"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_globe_reductions_keep_small_and_largest_globes_distinct(self):
        for method in ("small_globe", "largest_globe", "great_brass_globe"):
            row = self.fixture()
            row.update(
                quantity="ecliptic_latitude",
                role="reduction",
                source_reduction_method=method,
                source_reduction_references=[],
                flags=["not_an_additional_raw_reading"],
            )
            self.assertEqual(self.module().public_assertion(row)["source_reduction_method"], method)

    def test_great_brass_globe_stellar_calibration_is_a_separate_reduction(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="ecliptic_latitude",
            role="reduction",
            subject="head of Medusa",
            source_reduction_method="great_brass_globe",
            source_reduction_references=[],
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="ecliptic_latitude", components={"degree": "22", "arcminute": "25"})
            ),
        )
        out = self.module().public_assertion(row)
        self.assertEqual(
            (out["subject"], out["normalized"]["magnitude"]), ("head of Medusa", "80700")
        )
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        for changes in (
            dict(source_reduction_method="small_globe"),
            dict(source_reduction_method="largest_globe"),
            dict(role="recorded_reading"),
            dict(subject="Moon"),
            dict(source_reduction_references=["Aldebaran"]),
            dict(flags=[]),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_stellar_reduction_retains_pollux_without_turning_it_into_a_separation(self):
        row = self.fixture()
        row.update(
            quantity="ecliptic_latitude",
            role="reduction",
            source_reduction_method="comparison_directions",
            source_reduction_references=["Pollux"],
            flags=["not_an_additional_raw_reading", "hemisphere_unspecified"],
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_reduction_references"], ["Pollux"])
        self.assertEqual(out["quantity"], "ecliptic_latitude")
        self.assertIsNone(out["reference"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        with self.assertRaises(ValueError):
            self.module().public_assertion(
                dict(row, source_reduction_references=["unreviewed star"])
            )

    def test_globe_labels_cannot_relabel_raw_readings_or_invent_stellar_inputs(self):
        for method in ("small_globe", "great_brass_globe"):
            row = self.fixture()
            row.update(
                quantity="ecliptic_latitude",
                role="reduction",
                source_reduction_method=method,
                source_reduction_references=[],
                flags=["not_an_additional_raw_reading"],
            )
            for changes in (
                dict(role="recorded_coordinate"),
                dict(quantity="right_ascension"),
                dict(flags=[]),
                dict(source_reduction_references=["Aldebaran"]),
            ):
                with self.subTest(method=method, changes=changes), self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **changes))

    def test_source_sites_can_be_retained_without_inventing_observer_names(self):
        raw = self.fixture()
        raw["observing_site"] = "Uraniborg"
        out = self.module().public_assertion(raw)
        self.assertEqual(out["observing_site"], "Uraniborg")
        self.assertNotIn("observer_names", out)
        globe = self.fixture()
        globe.update(
            quantity="ecliptic_latitude",
            role="reduction",
            observing_site="Copenhagen",
            source_reduction_method="largest_globe",
            source_reduction_references=[],
            flags=["not_an_additional_raw_reading"],
        )
        out = self.module().public_assertion(globe)
        self.assertEqual(out["observing_site"], "Copenhagen")
        self.assertNotIn("observer_names", out)

    def test_girsitz_and_benatky_are_distinct_raw_observation_sites_without_inferred_observers(
        self,
    ):
        for site in ("Girsitzæ", "Benatky"):
            row = self.fixture()
            row.update(quantity="altitude", role="recorded_reading", observing_site=site)
            out = self.module().public_assertion(row)
            self.assertEqual(out["observing_site"], site)
            self.assertNotIn("observer_names", out)
            for change in (
                dict(role="historical_prediction"),
                dict(observer_names=["Tycho"]),
                dict(observing_site="unknown site"),
            ):
                with self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **change))

    def test_generic_quadrant_label_does_not_supply_a_subtype_or_reduction_method(self):
        row = self.fixture()
        row.update(quantity="altitude", role="recorded_reading", source_instrument_label="quadrant")
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_instrument_label"], "quadrant")
        self.assertNotIn("source_reduction_method", out)
        for change in (
            dict(quantity="declination"),
            dict(role="historical_input"),
            dict(source_instrument_qualifier="largest"),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **change))

    def test_solid_quadrant_is_preserved_as_a_distinct_source_instrument_label(self):
        row = self.fixture()
        row.update(
            quantity="altitude", role="recorded_reading", source_instrument_label="solid quadrant"
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_instrument_label"], "solid quadrant")
        self.assertEqual(out["normalized"]["magnitude"], row["normalized"]["magnitude"])
        for change in (dict(quantity="declination"), dict(role="historical_input")):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **change))

    def test_source_sites_require_reviewed_roles_and_reject_unstated_names(self):
        row = self.fixture()
        row["observing_site"] = "Uraniborg"
        for changes in (
            dict(observing_site="unreviewed place"),
            dict(observer_names=["Tycho"]),
            dict(role="historical_input"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_meridian_altitude_declination_remains_a_reduction_without_inferred_hemisphere(self):
        row = self.fixture()
        row.update(
            role="reduction",
            source_reduction_method="meridian_altitude",
            source_reduction_references=[],
            flags=["not_an_additional_raw_reading"],
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_reduction_method"], "meridian_altitude")
        self.assertIsNone(out["direction"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        self.assertNotIn("source_coordinate_state", out)

    def test_regulus_meridian_calibration_retains_the_stellar_reduction_and_unknown_sign(self):
        row = self.fixture()
        row.update(
            subject="Regulus",
            role="reduction",
            source_reduction_method="meridian_altitude",
            source_reduction_references=[],
            flags=["not_an_additional_raw_reading"],
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["subject"], "Regulus")
        self.assertEqual(out["source_reduction_method"], "meridian_altitude")
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        for change in (
            dict(role="recorded_coordinate"),
            dict(flags=[]),
            dict(source_reduction_references=["Mars"]),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **change))

    def test_fabricius_raw_attribution_does_not_invent_a_site_or_apply_to_calculations(self):
        from src.catalog import normalize_quantity

        for quantity in ("altitude", "clock_elapsed_time"):
            row = self.fixture()
            row.update(
                quantity=quantity, role="recorded_reading", observer_names=["David Fabricius"]
            )
            if quantity == "clock_elapsed_time":
                row["normalized"] = normalize_quantity(
                    dict(quantity=quantity, components={"hour": "1"})
                )
            out = self.module().public_assertion(row)
            self.assertEqual(out["observer_names"], ["David Fabricius"])
            self.assertNotIn("observing_site", out)
            for change in (
                dict(role="reduction"),
                dict(observing_site="Resterhafe"),
                dict(observer_names=["Tycho"]),
            ):
                with self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **change))

    def test_sunrise_duration_can_be_stated_without_an_approximation_label(self):
        from src.catalog import normalize_quantity

        for hour in ("1", "1 1/2"):
            row = self.fixture()
            row.update(
                quantity="clock_elapsed_time",
                role="recorded_reading",
                time_reference="elapsed_before_sunrise",
                flags=[],
                normalized=normalize_quantity(
                    dict(quantity="clock_elapsed_time", components={"hour": hour})
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["time_reference"], "elapsed_before_sunrise")
            self.assertNotIn("source_approximate", out["flags"])
            for change in (
                dict(quantity="recorded_clock"),
                dict(role="calculation_epoch"),
                dict(direction="east"),
            ):
                with self.assertRaises(ValueError):
                    self.module().public_assertion(dict(row, **change))

    def test_source_true_meridian_declination_is_a_historical_label_without_a_hemisphere(self):
        row = self.fixture()
        row.update(
            role="reduction",
            source_reduction_method="meridian_altitude",
            source_reduction_references=[],
            source_coordinate_state="true",
            flags=["not_an_additional_raw_reading"],
        )
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_coordinate_state"], "true")
        self.assertIsNone(out["direction"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        for change in (
            dict(role="recorded_coordinate"),
            dict(subject="Aldebaran"),
            dict(flags=[]),
            dict(source_reduction_method=None),
            dict(source_coordinate_state="apparent"),
        ):
            with self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **change))

    def test_southern_gemini_head_altitude_preserves_the_star_as_subject(self):
        row = self.fixture()
        row.update(quantity="altitude", role="recorded_reading", subject="southern head of Gemini")
        out = self.module().public_assertion(row)
        self.assertEqual(out["subject"], "southern head of Gemini")
        self.assertIsNone(out["reference"])

    def test_declination_reduction_method_rejects_raw_values_and_unsupported_routes(self):
        row = self.fixture()
        row.update(
            role="reduction",
            source_reduction_method="meridian_altitude",
            source_reduction_references=[],
            flags=["not_an_additional_raw_reading"],
        )
        for changes in (
            dict(role="recorded_coordinate"),
            dict(role="historical_input"),
            dict(subject="Aldebaran"),
            dict(flags=[]),
            dict(
                source_reduction_method="angular_distances",
                source_reduction_references=["Aldebaran"],
            ),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_stellar_declination_shortfall_keeps_the_unprinted_reference_unknown(self):
        from src.catalog import normalize_quantity

        row = self.fixture()
        row.update(
            quantity="declination_difference",
            role="historical_comparison",
            subject="Aldebaran",
            source_difference_relation="deficit",
            source_difference_reference="stellar_reference_declination_unstated",
            flags=["not_an_additional_raw_reading"],
            normalized=normalize_quantity(
                dict(quantity="declination_difference", components={"arcminute": "2"})
            ),
        )
        before = copy.deepcopy(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "120")
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        self.assertEqual(out["source_difference_relation"], "deficit")
        self.assertEqual(
            out["source_difference_reference"], "stellar_reference_declination_unstated"
        )
        self.assertNotIn("reference_value", out)
        self.assertNotIn("model_name", out)
        self.assertEqual(row, before)

    def test_stellar_shortfall_cannot_become_a_mars_correction_or_raw_coordinate(self):
        row = self.fixture()
        row.update(
            quantity="declination_difference",
            role="historical_comparison",
            subject="Aldebaran",
            source_difference_relation="deficit",
            source_difference_reference="stellar_reference_declination_unstated",
            flags=["not_an_additional_raw_reading"],
        )
        for changes in (
            dict(subject="Mars"),
            dict(role="recorded_coordinate"),
            dict(quantity="declination"),
            dict(source_difference_relation="excess"),
            dict(source_difference_reference="limited_position_as_stated"),
            dict(direction="north"),
            dict(flags=[]),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **changes))

    def test_taurus_transits_preserve_distinct_named_stars_and_a_corrected_clock_without_original(
        self,
    ):
        for name in ("breast of Taurus", "eye of Taurus"):
            row = self.fixture()
            row.update(
                subject=name,
                quantity="transit_clock",
                role="printed_correction",
                flags=["source_clock_correction", "original_clock_unstated"],
                normalized=dict(
                    status="exact",
                    magnitude="14624",
                    magnitude_degrees=None,
                    signed_magnitude=None,
                    unit="second_of_time",
                    least_component_unit="second",
                ),
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["subject"], name)
            self.assertEqual(out["role"], "printed_correction")
            self.assertIsNone(out["variant_of_id"])
            self.assertIn("original_clock_unstated", out["flags"])
            altitude = self.fixture()
            altitude.update(subject=name, quantity="altitude", role="recorded_reading")
            self.assertEqual(self.module().public_assertion(altitude)["subject"], name)

    def test_unknown_free_text_and_invalid_magnitudes_fail_closed(self):
        for field, value in [("subject", "/private/person"), ("role", "private narrative")]:
            row = self.fixture()
            row[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.module().public_assertion(row)
        row = self.fixture()
        row["normalized"]["magnitude"] = "NaN"
        with self.assertRaises(ValueError):
            self.module().public_assertion(row)

    def test_mars_separation_preserves_southern_taurus_horn_without_modern_star_guess(self):
        row = self.fixture()
        row.update(
            subject="Mars",
            reference="southern horn of Taurus",
            quantity="angular_separation",
            role="recorded_reading",
        )
        before = copy.deepcopy(row)
        result = self.module().public_assertion(row)
        self.assertEqual(
            (result["subject"], result["reference"]), ("Mars", "southern horn of Taurus")
        )
        self.assertEqual(row, before)
        self.assertNotIn("text_original", result)
        row["reference"] = "southern horn of Taurus /private/note"
        with self.assertRaises(ValueError):
            self.module().public_assertion(row)

    def test_extra_aggregate_keys_cannot_be_exported(self):
        projection = self.module().public_counts(dict(count=4, private_note="secret"), ("count",))
        self.assertEqual(projection, dict(count=4))
        with self.assertRaises(ValueError):
            self.module().public_counts(dict(count="/private"), ("count",))

    def test_source_date_links_are_explicit_validated_metadata(self):
        row = self.fixture()
        self.assertNotIn("source_date_claim_ids", self.module().public_assertion(row))
        cid = "context-v10-0123456789abcdefabcd"
        row["source_date_claim_ids"] = [cid]
        self.assertEqual(self.module().public_assertion(row)["source_date_claim_ids"], [cid])
        for ids in ("private text", ["/private"], [None]):
            row["source_date_claim_ids"] = ids
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                self.module().public_assertion(row)

    def test_unlinked_recorded_declinations_exclude_controls_other_targets_and_reductions(self):
        base = self.fixture()
        base["id"] = "assertion-v12-0123456789abcdefabcd"
        rows = [
            base,
            dict(base, id="controlled", workbook_control_id="Sheet1:212"),
            dict(base, id="star", subject="Arcturus"),
            dict(base, id="reduced", role="reduction"),
            dict(base, id="input", role="historical_input"),
            dict(base, id="clock", quantity="recorded_clock"),
        ]
        self.assertEqual(self.module().unlinked_recorded_mars_declinations(rows), [base["id"]])
        rows[0]["normalized"]["magnitude"] = "different"
        self.assertEqual(self.module().unlinked_recorded_mars_declinations(rows), [base["id"]])

    def test_reviewed_control_links_use_identities_without_reading_values(self):
        aid = "assertion-v11-0123456789abcdefabcd"
        rows = [
            dict(reviewed_assertion_id=aid, benchmark_control_id="Sheet1:76", magnitude="wrong"),
            dict(reviewed_assertion_id=None, benchmark_control_id="Sheet1:77"),
        ]
        self.assertEqual(self.module().reviewed_control_links(rows), {aid: "Sheet1:76"})
        rows[0]["magnitude"] = "different"
        self.assertEqual(self.module().reviewed_control_links(rows), {aid: "Sheet1:76"})
        with self.assertRaises(ValueError):
            self.module().reviewed_control_links([rows[0], rows[0]])
        row = self.fixture()
        row["workbook_control_id"] = "Sheet1:76"
        self.assertEqual(self.module().public_assertion(row)["workbook_control_id"], "Sheet1:76")
        row["workbook_control_id"] = "/private"
        with self.assertRaises(ValueError):
            self.module().public_assertion(row)

    def test_source_quality_and_uncertainty_flags_are_preserved_with_fixed_vocabulary(self):
        row = self.fixture()
        row["flags"] = ["hemisphere_unspecified", "not_certain_enough"]
        self.assertEqual(self.module().public_assertion(row)["flags"], row["flags"])
        row["flags"] = ["private narrative"]
        with self.assertRaises(ValueError):
            self.module().public_assertion(row)

    def test_a_source_upper_bound_is_preserved_as_an_unapplied_clock_claim(self):
        row = self.fixture()
        row.update(
            quantity="clock_correction",
            role="historical_correction",
            subject="observing clock",
            flags=["source_upper_bound", "clock_correction_not_applied"],
            normalized=dict(
                status="exact",
                magnitude="30",
                unit="second_of_time",
                magnitude_degrees=None,
                signed_magnitude=None,
                least_component_unit="minute",
            ),
        )
        result = self.module().public_assertion(row)
        self.assertEqual(result["normalized"]["magnitude"], "30")
        self.assertIn("source_upper_bound", result["flags"])
        self.assertIsNone(result["event_id"])

    def test_reported_jupiter_distance_adjustment_keeps_application_and_operation(self):
        row = self.fixture()
        self.assertNotIn("source_correction_application", self.module().public_assertion(row))
        row.update(
            quantity="separation_correction",
            role="historical_correction",
            subject="Jupiter",
            flags=["not_an_additional_raw_reading"],
            source_correction_application="applied_to_following_distances",
            source_correction_operation="add",
            normalized=dict(
                status="exact",
                magnitude="150",
                magnitude_degrees="1/24",
                signed_magnitude=None,
                unit="arcsecond",
                least_component_unit="arcminute",
            ),
        )
        before = copy.deepcopy(row)
        result = self.module().public_assertion(row)
        self.assertEqual(result["source_correction_application"], "applied_to_following_distances")
        self.assertEqual(result["source_correction_operation"], "add")
        self.assertEqual(result["normalized"]["magnitude"], "150")
        self.assertEqual(row, before)

        pending = dict(row, source_correction_application="not_yet_added_as_stated")
        out = self.module().public_assertion(pending)
        self.assertEqual(out["source_correction_application"], "not_yet_added_as_stated")
        self.assertEqual(out["source_correction_operation"], "add")
        self.assertEqual(out["normalized"]["magnitude"], "150")
        mars = self.module().public_assertion(dict(pending, subject="Mars"))
        self.assertEqual(mars["subject"], "Mars")
        self.assertEqual(mars["source_correction_application"], "not_yet_added_as_stated")
        with self.assertRaises(ValueError):
            self.module().public_assertion(dict(pending, subject="Moon"))

    def test_historical_coordinate_comparison_retains_direction_without_inventing_baseline(self):
        for q, relation in [("longitude_difference", "excess"), ("latitude_difference", "deficit")]:
            row = self.fixture()
            row.update(
                quantity=q,
                role="historical_comparison",
                subject="Jupiter",
                flags=["not_an_additional_raw_reading"],
                source_difference_relation=relation,
                source_difference_reference="limited_position_as_stated",
            )
            out = self.module().public_assertion(row)
            self.assertEqual(out["source_difference_relation"], relation)
            self.assertEqual(out["source_difference_reference"], "limited_position_as_stated")
            self.assertIsNone(out["direction"])
            self.assertNotIn("reference_value", out)

    def test_historical_coordinate_comparison_rejects_unreviewed_reference_or_quantity(self):
        row = self.fixture()
        row.update(
            quantity="longitude_difference",
            role="historical_comparison",
            subject="Jupiter",
            flags=["not_an_additional_raw_reading"],
            source_difference_relation="excess",
            source_difference_reference="limited_position_as_stated",
        )
        for change in [
            dict(source_difference_relation="north"),
            dict(source_difference_reference="/private"),
            dict(source_difference_reference=None),
            dict(quantity="declination"),
            dict(role="recorded_reading"),
            dict(subject="Mars"),
            dict(flags=[]),
        ]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_assertion(dict(row, **change))

    def test_reported_adjustment_metadata_rejects_estimates_raw_readings_and_partial_labels(self):
        base = self.fixture()
        base.update(
            quantity="separation_correction",
            role="historical_correction",
            subject="Jupiter",
            flags=["not_an_additional_raw_reading"],
            source_correction_application="applied_to_following_distances",
            source_correction_operation="add",
        )
        for change in [
            dict(role="calibration"),
            dict(role="recorded_reading"),
            dict(subject="Mars"),
            dict(quantity="angular_separation", reference="Vulture"),
            dict(source_correction_operation=None),
            dict(source_correction_operation="subtract"),
            dict(source_correction_application=None),
            dict(source_correction_application="/private/narrative"),
            dict(flags=[]),
        ]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_assertion(dict(base, **change))

    def test_corrected_mars_declination_keeps_unknown_hemisphere_and_correction_amount(self):
        row = self.fixture()
        row.update(
            role="historical_input",
            source_coordinate_state="corrected_as_stated",
            flags=["not_an_additional_raw_reading"],
        )
        before = copy.deepcopy(row)
        out = self.module().public_assertion(row)
        self.assertEqual(out["source_coordinate_state"], "corrected_as_stated")
        self.assertIsNone(out["direction"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        self.assertNotIn("correction_amount", out)
        self.assertEqual(row, before)

    def test_corrected_declination_label_cannot_turn_raw_or_stellar_readings_into_inputs(self):
        base = self.fixture()
        base.update(
            role="historical_input",
            source_coordinate_state="corrected_as_stated",
            flags=["not_an_additional_raw_reading"],
        )
        for changes in (
            dict(role="recorded_coordinate"),
            dict(subject="Aldebaran"),
            dict(quantity="ecliptic_latitude"),
            dict(flags=[]),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.module().public_assertion(dict(base, **changes))

    def test_both_pinnules_is_a_component_label_for_one_stated_quantity(self):
        row = self.fixture()
        row["source_component_label"] = "both pinnules"
        result = self.module().public_assertion(row)
        self.assertEqual(result["source_component_label"], "both pinnules")
        self.assertEqual(result["id"], row["id"])
        row["source_component_label"] = "three pinnules"
        with self.assertRaises(ValueError):
            self.module().public_assertion(row)

    def test_mercury_mars_comparison_keeps_the_measured_planet_and_endpoint_order(self):
        row = self.fixture()
        row.update(subject="Mercury", direction="south")
        row["normalized"]["signed_magnitude"] = "-62415"
        result = self.module().public_assertion(row)
        self.assertEqual(result["subject"], "Mercury")
        self.assertEqual(result["normalized"]["signed_magnitude"], "-62415")
        self.assertEqual(self.module().unlinked_recorded_mars_declinations([result]), [])
        row.update(
            quantity="angular_separation",
            subject="Mercury",
            reference="Mars",
            direction=None,
            role="recorded_reading",
        )
        row["normalized"]["signed_magnitude"] = None
        self.assertEqual(self.module().public_assertion(row)["reference"], "Mars")
        row.update(subject="Mars", reference="Mercury", role="adopted_value")
        self.assertEqual(self.module().public_assertion(row)["reference"], "Mercury")
        row.update(
            subject="Mercury",
            reference=None,
            quantity="ecliptic_longitude",
            role="historical_prediction",
            model_name="Copernicus",
        )
        self.assertEqual(self.module().public_assertion(row)["model_name"], "Copernicus")
        row["model_name"] = "unreviewed model"
        with self.assertRaises(ValueError):
            self.module().public_assertion(row)

    def test_lunar_endpoint_and_uninterpreted_component_labels_survive_export(self):
        row = self.fixture()
        row.update(
            subject="Moon western limb",
            reference="Mars",
            quantity="angular_separation",
            role="recorded_reading",
            flags=["limb_or_instrument_setting_unresolved"],
            source_component_label="inf.",
            source_pair_position=1,
        )
        result = self.module().public_assertion(row)
        self.assertEqual(result["subject"], "Moon western limb")
        self.assertEqual(result["reference"], "Mars")
        self.assertEqual(result["source_component_label"], "inf.")
        self.assertEqual(result["source_pair_position"], 1)
        row["source_component_label"] = "private narrative"
        with self.assertRaises(ValueError):
            self.module().public_assertion(row)

    def test_assertion_and_event_endpoints_cannot_dangle(self):
        row = self.module().public_assertion(self.fixture())
        self.module().validate_links([row], [])
        broken = copy.deepcopy(row)
        broken["event_id"] = "event-v10-0123456789abcdefabcd"
        with self.assertRaises(ValueError):
            self.module().validate_links([broken], [])

    def test_series_uses_reviewed_context_identity_and_requires_exported_group(self):
        row = self.fixture()
        row["series_id"] = "context-v10-0123456789abcdefabcd"
        row["ordinal"] = 1
        result = self.module().public_assertion(row)
        with self.assertRaises(ValueError):
            self.module().validate_links([result], [])
        self.module().validate_links(
            [result], [], [dict(id=row["series_id"], assertion_ids=[row["id"]])]
        )
        broken = copy.deepcopy(row)
        broken["variant_of_id"] = "assertion-v10-ffffffffffffffffffff"
        with self.assertRaises(ValueError):
            self.module().validate_links([broken], [])
