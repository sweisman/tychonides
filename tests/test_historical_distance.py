import hashlib
import unittest

from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion


class HistoricalDistanceTests(unittest.TestCase):
    def test_sexagesimal_semidiameter_fractions_keep_native_distance_units(self):
        for parts, expected, precision in (
            ({"semidiameter": "60", "semidiameter_minute": "36"}, "303/5", "semidiameter_minute"),
            ({"semidiameter": "30", "semidiameter_minute": "37"}, "1837/60", "semidiameter_minute"),
            ({"semidiameter": "52 2/5"}, "262/5", "semidiameter"),
        ):
            row = dict(
                id="assertion-v12-" + "a" * 20,
                volume=12,
                printed_page=119,
                quantity="distance_in_semidiameters",
                subject="Moon",
                reference="Earth",
                role="historical_input",
                components=parts,
                source_semidiameter_body="Earth",
                flags=["not_an_additional_raw_reading"],
            )
            row["normalized"] = normalize_quantity(row)
            out = public_assertion(row)["normalized"]
            self.assertEqual(out["magnitude"], expected)
            self.assertEqual(out["unit"], "source_semidiameter")
            self.assertEqual(out["least_component_unit"], precision)
            self.assertIsNone(out["magnitude_degrees"])
        with self.assertRaises(ValueError):
            normalize_quantity(
                dict(row, components={"semidiameter": "52", "semidiameter_minute": "60"})
            )

    def test_queried_native_distance_has_no_adopted_scalar(self):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=119,
            quantity="distance_in_semidiameters",
            subject="Moon",
            reference="Earth",
            role="historical_input",
            source_expression="60⅗ [?]",
            components={},
            source_semidiameter_body="Earth",
            flags=["not_an_additional_raw_reading", "source_notation_unresolved"],
        )
        row["normalized"] = normalize_quantity(row)
        out = public_assertion(row)["normalized"]
        self.assertIsNone(out["magnitude"])
        self.assertEqual(out["unit"], "source_semidiameter")
        for changes in (
            {"source_expression": "60⅗"},
            {"reference": "Sun"},
            {"source_semidiameter_body": None},
            {"components": {"semidiameter": "60 3/5"}},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                altered = dict(row, **changes)
                altered["normalized"] = normalize_quantity(altered)
                public_assertion(altered)

    def test_leading_angular_minutes_are_not_lower_sexagesimal_digits(self):
        for parts, expected in (
            ({"arcminute": "66", "arcsecond": "6"}, "3966"),
            ({"arcminute": "92", "arcsecond": "21"}, "5541"),
            ({"arcsecond": "85"}, "85"),
        ):
            row = dict(quantity="parallax_angle", components=parts)
            self.assertEqual(normalize_quantity(row)["magnitude"], expected)
        for parts in (
            {"arcminute": "0", "arcsecond": "85"},
            {"degree": "0", "arcminute": "66"},
            {"arcminute": "66", "arcsecond": "60"},
        ):
            with self.subTest(parts=parts), self.assertRaises(ValueError):
                normalize_quantity(dict(quantity="parallax_angle", components=parts))

    def test_compiler_binds_distance_number_to_the_source(self):
        text = "Distance from Earth in semidiameters 2756"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s1", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        assertion = dict(
            key="distance",
            line=1,
            span_id="s1",
            source_expression="2756",
            quantity="distance_in_semidiameters",
            subject="Mars",
            reference="Earth",
            role="historical_input",
            components={"semidiameter": "2756"},
            unit_basis="Printed semidiameters; reference scale unresolved",
        )
        batch = dict(
            id="review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=sha,
            basis=dict(kind="scan_review", printed_page=46),
            span_decisions=[
                dict(span_id="s1", decision="include", reason="Printed distance reviewed")
            ],
            assertions=[assertion],
        )
        result = compile_catalogue([batch], {12: text}, [span])
        self.assertEqual(result["assertions"][0]["normalized"]["magnitude"], "2756")
        assertion["components"]["semidiameter"] = "2757"
        with self.assertRaisesRegex(ValueError, "complete source number"):
            compile_catalogue([batch], {12: text}, [span])

    def test_source_semidiameters_preserve_scale_without_angular_conversion(self):
        row = dict(quantity="distance_in_semidiameters", components={"semidiameter": "2756"})
        norm = normalize_quantity(row)
        self.assertEqual(norm["status"], "exact")
        self.assertEqual(norm["magnitude"], "2756")
        self.assertEqual(norm["unit"], "source_semidiameter")
        self.assertIsNone(norm["magnitude_degrees"])
        self.assertIsNone(norm["signed_magnitude"])
        public = dict(
            row,
            normalized=norm,
            id="assertion-v12-" + "a" * 20,
            subject="Mars",
            reference="Earth",
            role="historical_input",
            volume=12,
            printed_page=46,
            flags=["distance_scale_unestablished"],
        )
        self.assertEqual(public_assertion(public)["normalized"], norm)
        public["quantity"] = "parallax_angle"
        with self.assertRaises(ValueError):
            public_assertion(public)

    def test_distance_cannot_mix_units_invent_a_sign_or_zodiac_origin(self):
        for extra in (
            {"components": {"semidiameter": "2756", "degree": "1"}},
            {"components": {"semidiameter": "-2"}},
            {"direction": "north"},
            {"zodiac_sign": "Aries"},
        ):
            row = dict(quantity="distance_in_semidiameters", components={"semidiameter": "2756"})
            row.update(extra)
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                normalize_quantity(row)

    def test_parallax_and_refraction_angles_remain_separate_quantities(self):
        for quantity in ("parallax_angle", "refraction_angle", "net_refraction_parallax"):
            row = dict(quantity=quantity, components={"arcminute": "1", "arcsecond": "13"})
            norm = normalize_quantity(row)
            self.assertEqual(norm["magnitude"], "73")
            self.assertEqual(norm["unit"], "arcsecond")
