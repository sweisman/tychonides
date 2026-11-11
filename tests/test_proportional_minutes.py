import copy
import hashlib
import unittest
from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion, validate_links


class ProportionalMinuteTests(unittest.TestCase):
    def restored_coefficient(self, expression="5[4]′ 23″", **changes):
        text = expression + "\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        row = dict(
            key="coefficient",
            line=1,
            span_id="s",
            source_expression=expression,
            quantity="proportional_minutes",
            role="historical_input",
            subject="Moon",
            reference=None,
            direction=None,
            components={"proportional_minute": "54", "proportional_second": "23"},
            source_component_order=["proportional_minute", "proportional_second"],
            source_digit_restorations=["5[4]"],
            flags=["not_an_additional_raw_reading"],
            unit_basis="Explicit restored digit in coefficient column",
        )
        row.update(changes)
        batch = dict(
            id="restored-coefficient",
            volume=12,
            edition_sha256=sha,
            interval_sha256=hashlib.sha256(expression.encode()).hexdigest(),
            line_start=1,
            line_end=1,
            basis=dict(kind="final_edition_review", printed_page=28),
            assertions=[row],
            span_decisions=[
                dict(span_id="s", decision="include", reason="Source digit restoration")
            ],
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        return compile_catalogue([batch], {12: text}, [span])["assertions"][0]

    def test_explicit_editorial_digit_completion_preserves_the_literal(self):
        row = self.restored_coefficient()
        out = public_assertion(row)
        self.assertEqual(row["source_expression"], "5[4]′ 23″")
        self.assertEqual(out["normalized"]["magnitude"], "3263/3600")
        self.assertEqual(out["source_digit_restorations"], ["5[4]"])
        tampered = copy.deepcopy(row)
        tampered["components"]["proportional_minute"] = "55"
        tampered["normalized"] = normalize_quantity(tampered)
        with self.assertRaises(ValueError):
            public_assertion(tampered)
        for expression, changes in (
            ("5[?]′ 23″", {}),
            ("5[4]′ 23″", {"source_digit_restorations": ["6[4]"]}),
            ("5[4]′ 23″", {"source_digit_restorations": []}),
            ("15[4]′ 23″", {}),
            ("5[4]° 23″", {}),
        ):
            with (
                self.subTest(expression=expression, changes=changes),
                self.assertRaises(ValueError),
            ):
                self.restored_coefficient(expression, **changes)

    def compiled(self):
        text = "22 46\n20° 10′\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=2)
        base = dict(
            span_id="s",
            subject="Mars",
            reference=None,
            direction=None,
            flags=["not_an_additional_raw_reading"],
            unit_basis="Reviewed proportional-minute coefficient and node-angle columns",
        )
        coefficient = dict(
            base,
            key="coefficient",
            line=1,
            source_expression="22 46",
            quantity="proportional_minutes",
            role="calculation_intermediate",
            components=dict(proportional_minute="22", proportional_second="46"),
        )
        node = dict(
            base,
            key="node",
            line=2,
            source_expression="20° 10′",
            quantity="calculation_angle",
            role="historical_input",
            argument_name="node_distance",
            components=dict(degree="20", arcminute="10"),
        )
        batch = dict(
            id="proportional-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=305),
            span_decisions=[dict(span_id="s", decision="include", reason="Reviewed table")],
            assertions=[coefficient, node],
            events=[],
        )
        try:
            return compile_catalogue([batch], {12: text}, [span])
        except ValueError as error:
            self.fail("Reviewed proportional-minute source must compile: " + str(error))

    def test_proportional_scruples_compile_as_a_ratio_not_angle_or_time(self):
        compiled = self.compiled()
        try:
            rows = [public_assertion(a) for a in compiled["assertions"]]
        except ValueError as error:
            self.fail("Reviewed coefficient must export: " + str(error))
        validate_links(rows, [])
        coefficient = next(a for a in rows if a["quantity"] == "proportional_minutes")
        self.assertEqual(coefficient["normalized"]["magnitude"], "683/1800")
        self.assertEqual(coefficient["normalized"]["unit"], "ratio")
        self.assertEqual(coefficient["normalized"]["least_component_unit"], "proportional_second")
        self.assertIsNone(coefficient["normalized"]["magnitude_degrees"])
        self.assertIsNone(coefficient["normalized"]["signed_magnitude"])
        node = next(a for a in rows if a["quantity"] == "calculation_angle")
        self.assertEqual(node["argument_name"], "node_distance")
        self.assertEqual(node["normalized"]["magnitude"], "72600")

    def test_proportional_scale_and_omitted_seconds_have_exact_distinct_meanings(self):
        for parts, want, last in (
            (
                dict(proportional_minute="53", proportional_second="20"),
                "8/9",
                "proportional_second",
            ),
            (dict(proportional_minute="60", proportional_second="0"), "1", "proportional_second"),
            (dict(proportional_minute="54"), "9/10", "proportional_minute"),
        ):
            norm = normalize_quantity(dict(quantity="proportional_minutes", components=parts))
            self.assertEqual(norm["magnitude"], want)
            self.assertEqual(norm["least_component_unit"], last)
        for parts in (
            dict(minute="22", second="46"),
            dict(arcminute="22", arcsecond="46"),
            dict(proportional_minute="60", proportional_second="1"),
            dict(proportional_minute="22", proportional_second="60"),
        ):
            with self.subTest(parts=parts), self.assertRaises(ValueError):
                normalize_quantity(dict(quantity="proportional_minutes", components=parts))

    def test_coefficient_and_node_scopes_cannot_become_observations_or_coordinates(self):
        source = next(
            a for a in self.compiled()["assertions"] if a["quantity"] == "proportional_minutes"
        )
        for change in (
            {"role": "recorded_reading"},
            {"subject": "observing clock"},
            {"reference": "Earth"},
            {"direction": "north"},
        ):
            bad = copy.deepcopy(source)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
        node = next(
            a for a in self.compiled()["assertions"] if a["quantity"] == "calculation_angle"
        )
        for change in (
            {"subject": "Jupiter"},
            {"quantity": "ecliptic_longitude"},
            {"role": "recorded_coordinate"},
            {"direction": "north"},
        ):
            bad = copy.deepcopy(node)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
