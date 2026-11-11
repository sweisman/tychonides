import copy
import hashlib
import unittest
from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion, validate_links


class ClockComponentVariantTests(unittest.TestCase):
    def fixture(self, expression="7^h^ 40^m^¹ 40^s^", anchor="minute"):
        text = expression + "\nThe codex has 60.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=2)
        base = dict(
            key="clock",
            line=1,
            span_id="s",
            source_expression=expression,
            quantity="recorded_clock",
            role="printed_correction",
            subject="observing clock",
            reference=None,
            direction=None,
            components=dict(hour="7", minute="40", second="40"),
            source_note_marker_original="¹",
            unit_basis="Printed H/M/S and reviewed minute-note marker",
            flags=["source_annotation_variant"],
        )
        if anchor is not None:
            base["source_note_marker_after_unit"] = anchor
        note = dict(
            key="component",
            line=2,
            span_id="s",
            source_expression="60",
            quantity="clock_component",
            role="editorial_variant",
            subject="observing clock",
            reference=None,
            direction=None,
            components=dict(minute="60"),
            annotation_of_key="clock",
            unit_basis="Only the original minute component is reported",
            flags=[
                "source_annotation_variant",
                "not_an_observing_clock",
                "not_an_additional_raw_reading",
            ],
        )
        batch = dict(
            id="component-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=296),
            span_decisions=[
                dict(span_id="s", decision="context", reason="Reviewed component variant")
            ],
            assertions=[base, note],
            events=[],
        )
        return text, span, batch

    def compiled(self):
        text, span, batch = self.fixture()
        return compile_catalogue([batch], {12: text}, [span])

    def test_literal_minute_sixty_is_not_a_complete_clock_or_elapsed_hour(self):
        compiled = self.compiled()
        rows = [public_assertion(a) for a in compiled["assertions"]]
        validate_links(rows, [])
        note = next(a for a in rows if a["quantity"] == "clock_component")
        base = next(a for a in rows if a["quantity"] == "recorded_clock")
        self.assertEqual(note["normalized"]["magnitude"], "60")
        self.assertEqual(note["normalized"]["unit"], "source_clock_component")
        self.assertEqual(note["normalized"]["least_component_unit"], "minute")
        self.assertIsNone(note["normalized"]["magnitude_degrees"])
        self.assertIsNone(note["normalized"]["signed_magnitude"])
        self.assertEqual(note["annotation_of_id"], base["id"])
        self.assertIsNone(note["event_id"])
        self.assertEqual(base["normalized"]["magnitude"], "27640")
        self.assertEqual(
            next(a for a in compiled["assertions"] if a["quantity"] == "recorded_clock")[
                "source_expression"
            ],
            "7^h^ 40^m^¹ 40^s^",
        )
        with self.assertRaises(ValueError):
            normalize_quantity(
                dict(quantity="recorded_clock", components=dict(hour="7", minute="60", second="40"))
            )

    def test_component_scope_requires_a_linked_unclocked_editorial_annotation(self):
        note = next(
            public_assertion(a)
            for a in self.compiled()["assertions"]
            if a["quantity"] == "clock_component"
        )
        source = next(
            a for a in self.compiled()["assertions"] if a["quantity"] == "clock_component"
        )
        for change in (
            {"role": "recorded_clock"},
            {"subject": "Mars"},
            {"flags": []},
            {"annotation_of_id": None},
            {"event_id": "event-v12-" + "a" * 20},
        ):
            bad = copy.deepcopy(source)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
        bad = copy.deepcopy(source)
        bad["normalized"]["unit"] = "second_of_time"
        with self.assertRaises(ValueError):
            public_assertion(bad)
        with self.assertRaises(ValueError):
            normalize_quantity(dict(quantity="clock_component", components=dict(hour="1")))
        self.assertEqual(note["normalized"]["magnitude"], "60")

    def test_component_annotation_targets_a_clock_and_cannot_be_an_event_clock(self):
        rows = [public_assertion(a) for a in self.compiled()["assertions"]]
        base = next(a for a in rows if a["quantity"] == "recorded_clock")
        for change in ({"quantity": "meridian_distance"}, {"volume": 13}):
            wrong = copy.deepcopy(rows)
            next(a for a in wrong if a["id"] == base["id"]).update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_links(wrong, [])
        text, span, batch = self.fixture()
        batch["events"] = [dict(key="event", line=2, clock_key="component")]
        with self.assertRaisesRegex(ValueError, "clock"):
            compile_catalogue([batch], {12: text}, [span])

    def test_internal_superscript_requires_the_reviewed_minute_unit_anchor(self):
        for expression, anchor in [
            ("7^h^ 40¹^m^ 40^s^", "minute"),
            ("7^h^ 40^m^¹ 40^s^", "hour"),
            ("7^h^ 40^m^¹ 40^s^", None),
        ]:
            text, span, batch = self.fixture(expression, anchor)
            with self.subTest(expression=expression, anchor=anchor), self.assertRaises(ValueError):
                compile_catalogue([batch], {12: text}, [span])

    def test_detached_component_links_to_an_earlier_review_with_an_explicit_basis(self):
        text, span, batch = self.fixture()
        clock, note = copy.deepcopy(batch["assertions"])
        first = dict(span, id="s-clock", line_end=1)
        second = dict(span, id="s-note", line_start=2)
        clock["span_id"] = first["id"]
        note["span_id"] = second["id"]
        del note["annotation_of_key"]
        note["annotation_of_ref"] = dict(
            review_id="a-clock",
            key="clock",
            basis="Reviewed footnote marker after minute unit identifies its clock target",
        )
        raw = dict(
            batch,
            id="a-clock",
            line_end=1,
            assertions=[clock],
            span_decisions=[dict(span_id=first["id"], decision="context", reason="Reviewed clock")],
            interval_sha256=hashlib.sha256(text.splitlines()[0].encode()).hexdigest(),
        )
        detached = dict(
            batch,
            id="z-note",
            line_start=2,
            assertions=[note],
            span_decisions=[dict(span_id=second["id"], decision="context", reason="Reviewed note")],
            interval_sha256=hashlib.sha256(text.splitlines()[1].encode()).hexdigest(),
        )
        compiled = compile_catalogue([raw, detached], {12: text}, [first, second])
        public = [public_assertion(a) for a in compiled["assertions"]]
        validate_links(public, [])
        target = next(a for a in public if a["quantity"] == "recorded_clock")
        part = next(a for a in public if a["quantity"] == "clock_component")
        self.assertEqual(part["annotation_of_id"], target["id"])
        for ref in (
            dict(review_id="missing", key="clock", basis="Source scope"),
            dict(review_id="a-clock", key="missing", basis="Source scope"),
            dict(review_id="a-clock", key="clock", basis=""),
        ):
            bad = copy.deepcopy(detached)
            bad["assertions"][0]["annotation_of_ref"] = ref
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                compile_catalogue([raw, bad], {12: text}, [first, second])
        bad = copy.deepcopy(detached)
        bad["assertions"][0]["annotation_of_key"] = "component"
        with self.assertRaises(ValueError):
            compile_catalogue([raw, bad], {12: text}, [first, second])
