import copy
import hashlib
import unittest

from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion


class BrokenClockAndModelComparisonTests(unittest.TestCase):
    def compiled(self, expression, quantity, components, **extra):
        text = expression
        sha = hashlib.sha256(text.encode()).hexdigest()
        assertion = dict(
            key="value",
            line=1,
            span_id="span",
            source_expression=expression,
            quantity=quantity,
            components=components,
            role="reduction",
            subject="Mars",
            reference=None,
            direction=None,
            flags=[],
            unit_basis="Reviewed source units.",
            **extra,
        )
        batch = dict(
            id="fixture",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=sha,
            basis=dict(kind="fixture", printed_page=284),
            span_decisions=[dict(span_id="span", decision="include", reason="Fixture.")],
            assertions=[assertion],
            contexts=[],
            events=[],
        )
        span = dict(id="span", volume=12, line_start=1, line_end=1, edition_sha256=sha)
        return batch, text, span

    def test_inferred_time_is_exact_but_cannot_select_an_event_clock(self):
        batch, text, span = self.compiled(
            "1^h^ 16¼^m^",
            "inferred_time",
            dict(hour="1", minute="16 1/4"),
            time_reference="source_clock_origin_unstated",
            time_inference_basis="equatorial_distance",
        )
        a = compile_catalogue([batch], {12: text}, [span])["assertions"][0]
        self.assertEqual(a["normalized"]["magnitude"], "4575")
        self.assertEqual(a["normalized"]["unit"], "second_of_time")
        out = public_assertion(a)
        self.assertEqual(out.get("time_inference_basis"), "equatorial_distance")
        self.assertEqual(out["quantity"], "inferred_time")
        self.assertIsNone(out["event_id"])
        eclipse_midpoint = copy.deepcopy(a)
        eclipse_midpoint["time_inference_basis"] = "eclipse_midpoint"
        eclipse_midpoint["time_reference"] = "source_after_noon"
        midpoint_out = public_assertion(eclipse_midpoint)
        self.assertEqual(midpoint_out["time_inference_basis"], "eclipse_midpoint")
        self.assertEqual(midpoint_out["time_reference"], "source_after_noon")
        after_midnight = copy.deepcopy(a)
        after_midnight["time_reference"] = "source_after_midnight_label"
        self.assertEqual(
            public_assertion(after_midnight)["time_reference"], "source_after_midnight_label"
        )
        eclipse_midpoint["time_reference"] = "source_after_midnight_label"
        self.assertEqual(
            public_assertion(eclipse_midpoint)["time_reference"], "source_after_midnight_label"
        )
        for change in (
            {"role": "recorded_clock"},
            {"quantity": "recorded_clock"},
            {"time_inference_basis": "private method"},
        ):
            bad = copy.deepcopy(a)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
        bad = copy.deepcopy(a)
        bad.pop("time_inference_basis")
        with self.assertRaises(ValueError):
            public_assertion(bad)
        batch["assertions"][0]["event_key"] = "event"
        batch["events"] = [dict(key="event", line=1, clock_key="value")]
        with self.assertRaisesRegex(ValueError, "Event clock must be a recorded clock"):
            compile_catalogue([batch], {12: text}, [span])

    def test_angular_model_comparisons_preserve_relation_without_a_timing_bound(self):
        for quantity, relation, components in [
            ("longitude_difference", "coordinate_difference", dict(degree="4", arcminute="7 1/2")),
            ("latitude_difference", "coordinate_difference", dict(arcminute="11")),
            ("latitude_difference", "latitude_change_over_source_interval", dict(degree="1/2")),
        ]:
            row = dict(
                id="assertion-v12-" + "a" * 20,
                volume=12,
                printed_page=285,
                subject="Mars",
                reference=None,
                quantity=quantity,
                role="historical_comparison",
                model_name="Copernicus",
                comparison_relation=relation,
                normalized=normalize_quantity(dict(quantity=quantity, components=components)),
            )
            with self.subTest(quantity=quantity, relation=relation):
                out = public_assertion(row)
                self.assertEqual(out.get("comparison_relation"), relation)
                self.assertEqual(out.get("model_name"), "Copernicus")
                self.assertNotIn("lower_bound_inclusive", out)
                self.assertIsNone(out["direction"])
                for change in (
                    {"comparison_relation": "earlier_than_author"},
                    {"role": "recorded_coordinate"},
                    {"model_name": "private name"},
                    {"event_id": "event-v12-" + "b" * 20},
                ):
                    bad = copy.deepcopy(row)
                    bad.update(change)
                    with self.subTest(change=change), self.assertRaises(ValueError):
                        public_assertion(bad)

    def test_armillae_label_scopes_to_declinations_without_supplying_a_hemisphere(self):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=284,
            subject="Mars",
            reference=None,
            quantity="declination",
            role="recorded_coordinate",
            source_instrument_label="armillae",
            normalized=normalize_quantity(
                dict(quantity="declination", components=dict(degree="11", arcminute="17 1/3"))
            ),
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_instrument_label"), "armillae")
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        for change in (
            {"quantity": "altitude"},
            {"role": "historical_input"},
            {"source_instrument_label": "private label"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_worded_ten_days_preserves_source_interval_without_accepting_dates(self):
        batch, text, span = self.compiled(
            "ten days", "clock_elapsed_time", dict(day="10"), source_word_numbers={"ten": "10"}
        )
        a = compile_catalogue([batch], {12: text}, [span])["assertions"][0]
        self.assertEqual(a["normalized"]["magnitude"], "864000")
        self.assertEqual(a["normalized"]["least_component_unit"], "day")
        self.assertNotIn("absolute_timestamp", a)
        batch["assertions"][0]["source_word_numbers"] = {"ten": "11"}
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {12: text}, [span])
