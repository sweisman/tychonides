import copy
import unittest

from src.normalization import normalize_quantity


class TemporalHourTests(unittest.TestCase):
    def test_calendar_parts_keep_native_month_and_year_counts(self):
        from src.catalog import compile_catalogue
        from src.public_assertions import public_assertion
        from tests.test_catalog import CatalogueTests

        for literal, kind, component, expected in (
            ("four years & a half", "source_year_count", "4 1/2", "9/2"),
            ("a full month", "source_month_count", "1", "1"),
        ):
            text, spans, batch = CatalogueTests().explicit_clock_case(literal, {})
            batch["assertions"][0].update(
                quantity="source_scalar",
                role="historical_input",
                subject="calendar calculation",
                source_parameter_kind=kind,
                source_word_numbers={literal: component},
                components=dict(scalar=component),
                flags=["not_an_additional_raw_reading"],
            )
            with self.subTest(literal=literal):
                row = compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                output = public_assertion(row)
                self.assertEqual(output["normalized"]["magnitude"], expected)
                self.assertEqual(output["normalized"]["unit"], "source_scalar")
                self.assertEqual(output["source_parameter_kind"], kind)

    def test_native_hours_keep_exact_count_without_seconds_conversion(self):
        parts = dict(hour="3", minute="20", second="39")
        native = normalize_quantity(dict(quantity="temporal_hour_count", components=parts))
        self.assertEqual((native["status"], native["unit"]), ("exact", "source_temporal_hour"))
        self.assertEqual(native["magnitude"], "4013/1200")
        self.assertIsNone(native["magnitude_degrees"])
        self.assertIsNone(native["signed_magnitude"])
        ordinary = normalize_quantity(dict(quantity="clock_elapsed_time", components=parts))
        self.assertEqual((ordinary["unit"], ordinary["magnitude"]), ("second_of_time", "12039"))

    def test_fractional_and_subhour_components_remain_native_counts(self):
        for parts, expected in (
            (dict(hour="0", minute="1/2", second="1/3"), "91/10800"),
            (dict(minute="60"), "1"),
            (dict(hour="25"), "25"),
            (dict(hour="0"), "0"),
        ):
            with self.subTest(parts=parts):
                result = normalize_quantity(dict(quantity="temporal_hour_count", components=parts))
                self.assertEqual(result["magnitude"], expected)
                self.assertEqual(result["unit"], "source_temporal_hour")

    def test_invalid_units_orientation_and_lower_components_are_rejected(self):
        base = dict(quantity="temporal_hour_count", components=dict(hour="3"))
        for changes in (
            dict(components=dict(degree="3")),
            dict(components=dict(day="1")),
            dict(components=dict(hour="3", minute="60")),
            dict(components=dict(hour="-1")),
            dict(direction="north"),
            dict(zodiac_sign="Aries"),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                normalize_quantity(dict(base, **changes))

    def test_missing_and_queried_values_do_not_become_zero(self):
        for changes, status in (
            ({}, "unsupported"),
            (dict(incomplete=True), "incomplete"),
            (dict(flags=["source_notation_unresolved"]), "unsupported"),
        ):
            result = normalize_quantity(
                dict(quantity="temporal_hour_count", components={}, **changes)
            )
            self.assertEqual((result["status"], result["unit"]), (status, "source_temporal_hour"))
            self.assertIsNone(result["magnitude"])

    def test_public_projection_rejects_unit_and_value_substitution(self):
        from src.public_assertions import public_assertion
        from tests.test_public_checkpoint import PublicCheckpointTests

        row = dict(
            PublicCheckpointTests().fixture(),
            quantity="temporal_hour_count",
            subject="ecliptic point",
            role="calculation_intermediate",
            source_expression="3^h^ 20^m^ 39^s^",
            components=dict(hour="3", minute="20", second="39"),
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "4013/1200")
        for changes in (
            dict(unit="second_of_time", magnitude="12039"),
            dict(magnitude="999"),
        ):
            bad = copy.deepcopy(row)
            bad["normalized"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_compiler_and_materializer_preserve_full_native_unit_sequence(self):
        from src.catalog import compile_catalogue
        from src.review_preparation import materialize_review
        from tests.test_catalog import CatalogueTests

        for literal, valid in (("3^h^ 20^m^ 39^s^", True), ("3° 20′ 39″", False)):
            text, spans, batch = CatalogueTests().explicit_clock_case(literal, {})
            row = batch.pop("assertions")[0]
            row.update(
                quantity="temporal_hour_count",
                role="calculation_intermediate",
                subject="ecliptic point",
                column=None,
                flags=["not_an_additional_raw_reading"],
            )
            row.pop("components")
            batch["cell_groups"] = [dict(cells=[row])]
            if valid:
                prepared = materialize_review(batch, text, spans)
                compiled = compile_catalogue([prepared], {10: text}, spans)["assertions"][0]
                self.assertEqual(compiled["source_expression"], literal)
                self.assertEqual(compiled["normalized"]["magnitude"], "4013/1200")
            else:
                row["component_units"] = ["hour", "minute", "second"]
                with self.assertRaises(ValueError):
                    prepared = materialize_review(batch, text, spans)
                    compile_catalogue([prepared], {10: text}, spans)
