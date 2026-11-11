import unittest

from src.public_checkpoint import public_assertion


class PublicHistoricalAttributionTests(unittest.TestCase):
    def test_attached_editorial_scalar_calculations_keep_their_role_and_native_scale(self):
        import copy
        from src.normalization import normalize_quantity

        for kind, literal in (
            ("arithmetic_intermediate", "1017"),
            ("scaled_sine", "5461019"),
            ("sine_increment_per_source_second", "17"),
        ):
            with self.subTest(kind=kind):
                row = self.row()
                row.update(
                    quantity="source_scalar",
                    subject="planetary motion calculation",
                    role="editorial_addition",
                    source_parameter_kind=kind,
                    source_expression=literal,
                    components={"scalar": literal},
                    annotation_of_id="assertion-v12-" + "b" * 20,
                    edition_note_marker="[^ed65]",
                    printed_page=None,
                    flags=["source_annotation_variant", "not_an_additional_raw_reading"],
                )
                row.pop("model_name", None)
                if kind != "arithmetic_intermediate":
                    row["source_scalar_scale"] = "10000000"
                row["normalized"] = normalize_quantity(row)
                result = public_assertion(row)
                self.assertEqual(result["role"], "editorial_addition")
                self.assertEqual(result["normalized"], row["normalized"])
                self.assertEqual(result["annotation_of_id"], row["annotation_of_id"])
                for changes in (
                    {"annotation_of_id": None},
                    {"edition_note_marker": "ed65"},
                    {"flags": ["not_an_additional_raw_reading"]},
                    {"role": "recorded_reading"},
                    {"model_name": "Copernicus"},
                ):
                    with self.subTest(changes=changes), self.assertRaises(ValueError):
                        public_assertion(dict(copy.deepcopy(row), **changes))

    def test_zodiac_calibration_star_labels_can_occupy_either_endpoint(self):
        for star in (
            "Antares",
            "Pollux",
            "northern eye of Taurus",
            "northern Ass",
            "middle star in head of Sagittarius",
            "preceding star in tail of Capricorn",
            "upper horn of Capricorn",
            "last or brighter star of Pleiades",
            "more northerly of three stars in forehead of Scorpio",
        ):
            for subject, reference in ((star, "Regulus"), ("Regulus", star)):
                with self.subTest(subject=subject, reference=reference):
                    row = self.row()
                    row.update(
                        subject=subject,
                        reference=reference,
                        quantity="angular_separation",
                        role="historical_input",
                        flags=["not_an_additional_raw_reading"],
                    )
                    out = public_assertion(row)
                    self.assertEqual((out["subject"], out["reference"]), (subject, reference))

    def test_draco_polar_star_label_can_occupy_either_separation_endpoint(self):
        star = "small star of Draco near ecliptic pole"
        for subject, reference in ((star, "Spica"), ("Spica", star)):
            row = self.row()
            row.update(
                subject=subject,
                reference=reference,
                quantity="angular_separation",
                role="historical_input",
                flags=["not_an_additional_raw_reading"],
            )
            out = public_assertion(row)
            self.assertEqual((out["subject"], out["reference"]), (subject, reference))

    def test_ophiuchus_reference_star_can_be_the_subject_of_a_linked_separation(self):
        row = self.row()
        row.update(
            subject="northern star of left hand of Ophiuchus",
            reference="Flying Vulture",
            quantity="angular_separation",
            role="historical_input",
            flags=["not_an_additional_raw_reading"],
        )
        out = public_assertion(row)
        self.assertEqual(out["subject"], row["subject"])
        self.assertEqual(out["reference"], "Flying Vulture")
        self.assertEqual(out["role"], "historical_input")

    def test_solar_predictions_retain_named_models_and_reject_observation_roles(self):
        row = self.row()
        row["subject"] = "Sun"
        for model in ("Copernicus", "Alphonsine"):
            row["model_name"] = model
            self.assertEqual(public_assertion(row)["model_name"], model)
        row["role"] = "recorded_reading"
        with self.assertRaises(ValueError):
            public_assertion(row)

    def test_jupiter_predictions_keep_model_and_epoch_without_becoming_observations(self):
        row = self.row()
        row.update(subject="Jupiter", calculation_epoch_id="assertion-v12-" + "b" * 20)
        for model in ("Copernicus", "Alphonsine"):
            row["model_name"] = model
            result = public_assertion(row)
            self.assertEqual(result["subject"], "Jupiter")
            self.assertEqual(result["model_name"], model)
            self.assertEqual(result["calculation_epoch_id"], "assertion-v12-" + "b" * 20)
            self.assertIsNone(result["event_id"])
        row["event_id"] = "event-v12-" + "c" * 20
        with self.assertRaises(ValueError):
            public_assertion(row)
        row.pop("event_id")
        row["role"] = "recorded_coordinate"
        with self.assertRaises(ValueError):
            public_assertion(row)

    def test_model_timing_comparison_preserves_direction_and_bound(self):
        row = self.row()
        row.update(
            role="historical_comparison",
            quantity="clock_elapsed_time",
            model_name="Copernicus",
            comparison_relation="earlier_than_author",
            lower_bound_inclusive=True,
            flags=["source_lower_bound"],
            normalized=dict(
                status="exact",
                magnitude="10800",
                unit="second_of_time",
                magnitude_degrees=None,
                signed_magnitude=None,
                least_component_unit="hour",
            ),
        )
        result = public_assertion(row)
        self.assertEqual(result.get("model_name"), "Copernicus")
        self.assertEqual(result.get("comparison_relation"), "earlier_than_author")
        self.assertIs(result.get("lower_bound_inclusive"), True)
        row["lower_bound_inclusive"] = False
        self.assertIs(public_assertion(row).get("lower_bound_inclusive"), False)
        row["normalized"]["unit"] = "arcsecond"
        with self.assertRaises(ValueError):
            public_assertion(row)
        row["normalized"]["unit"] = "second_of_time"
        row["comparison_relation"] = "unreviewed assertion"
        with self.assertRaises(ValueError):
            public_assertion(row)

    def row(self):
        return dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=147,
            subject="Mars",
            reference=None,
            quantity="ecliptic_longitude",
            role="historical_prediction",
            normalized=dict(
                status="exact",
                magnitude="34320",
                unit="arcsecond",
                magnitude_degrees="143/15",
                signed_magnitude=None,
                least_component_unit="arcminute",
            ),
        )

    def test_predictions_keep_model_identity_and_reject_missing_attribution(self):
        row = self.row()
        row["model_name"] = "Copernicus"
        result = public_assertion(row)
        self.assertEqual(result.get("model_name"), "Copernicus")
        self.assertEqual(result["role"], "historical_prediction")
        for name in (None, "unreviewed model"):
            row["model_name"] = name
            with self.assertRaises(ValueError):
                public_assertion(row)
        row["model_name"] = "Copernicus"
        row["role"] = "recorded_reading"
        with self.assertRaises(ValueError):
            public_assertion(row)

    def test_padua_observer_claims_survive_export_without_accepting_arbitrary_text(self):
        row = self.row()
        row.update(
            role="recorded_reading",
            quantity="angular_separation",
            reference="heart of Scorpio",
            observing_site="Padua",
            observer_names=["Magini", "Gellius Sascerides"],
        )
        result = public_assertion(row)
        self.assertEqual(result.get("observing_site"), "Padua")
        self.assertEqual(result.get("observer_names"), ["Magini", "Gellius Sascerides"])
        row["observer_names"] = ["Magini"]
        self.assertEqual(public_assertion(row).get("observer_names"), ["Magini"])
        row["observing_site"] = "unreviewed location"
        with self.assertRaises(ValueError):
            public_assertion(row)
        row["observing_site"] = "Padua"
        row["observer_names"] = ["private production note"]
        with self.assertRaises(ValueError):
            public_assertion(row)


if __name__ == "__main__":
    unittest.main()
