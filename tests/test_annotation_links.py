import hashlib
import unittest

from src.catalog import compile_catalogue
from src.public_checkpoint import public_assertion, validate_links


class AnnotationLinkTests(unittest.TestCase):
    def zodiac_fixture(self, expression):
        text = expression + "\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="z", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        row = dict(
            key="longitude",
            line=1,
            span_id="z",
            source_expression=expression,
            source_note_marker_original="²",
            quantity="ecliptic_longitude",
            role="reduction",
            subject="Jupiter",
            reference=None,
            direction=None,
            zodiac_sign="Capricorn",
            components=dict(degree="17", arcminute="21", arcsecond="15"),
            unit_basis="Explicit degree/minute/second components and Capricorn glyph",
        )
        batch = dict(
            id="zodiac",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(expression.encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=279),
            span_decisions=[
                dict(
                    span_id="z",
                    decision="include",
                    reason="Source glyph and attached note reviewed",
                )
            ],
            assertions=[row],
        )
        return text, span, batch

    def test_note_before_zodiac_glyph_keeps_the_sign_and_excludes_the_note_number(self):
        text, span, batch = self.zodiac_fixture("17°21′15″² ♑")
        result = compile_catalogue([batch], {12: text}, [span])["assertions"][0]
        self.assertEqual(result["source_expression"], "17°21′15″² ♑")
        self.assertEqual(result["normalized"]["magnitude"], "62475")
        self.assertEqual(result["normalized"]["zodiac_sign"], "Capricorn")
        self.assertEqual(result["normalized"]["zodiac_longitude_degrees"], "13793/48")
        self.assertEqual(public_assertion(result)["normalized"]["magnitude"], "62475")

    def test_note_metadata_cannot_remove_a_superscript_inside_the_number(self):
        text, span, batch = self.zodiac_fixture("17°²21′15″ ♑")
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {12: text}, [span])

    def fixture(self):
        text = "9°17′²; Response H. 6 M. 7\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        base = dict(
            key="base",
            line=1,
            span_id="s",
            source_expression="9°17′",
            quantity="meridian_distance",
            role="recorded_reading",
            subject="heart of Leo",
            reference="meridian",
            components=dict(degree="9", arcminute="17"),
            unit_basis="Source angle",
            flags=[],
        )
        note = dict(
            key="note",
            line=1,
            span_id="s",
            source_expression="H. 6 M. 7",
            quantity="annotated_time",
            role="editorial_addition",
            subject="observing clock",
            reference=None,
            components=dict(hour="6", minute="7"),
            unit_basis="Manuscript addition in printed annotation",
            flags=["source_annotation_variant"],
            annotation_of_key="base",
        )
        batch = dict(
            id="review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.strip().encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=44),
            span_decisions=[dict(span_id="s", decision="include", reason="Reviewed")],
            assertions=[base, note],
        )
        return text, span, batch

    def test_annotation_can_link_different_quantity_without_becoming_an_event_clock(self):
        text, span, batch = self.fixture()
        result = compile_catalogue([batch], {12: text}, [span])
        rows = [public_assertion(r) for r in result["assertions"]]
        base = next(r for r in rows if r["quantity"] == "meridian_distance")
        note = next(r for r in rows if r["quantity"] == "annotated_time")
        self.assertEqual(note["annotation_of_id"], base["id"])
        validate_links(rows, [])
        batch["events"] = [dict(key="event", line=1, clock_key="note")]
        with self.assertRaisesRegex(ValueError, "clock"):
            compile_catalogue([batch], {12: text}, [span])

    def test_invalid_or_missing_annotation_targets_are_rejected(self):
        text, span, batch = self.fixture()
        batch["assertions"][1]["annotation_of_key"] = "missing"
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {12: text}, [span])
        batch["assertions"][1]["annotation_of_key"] = "base"
        rows = [
            public_assertion(r)
            for r in compile_catalogue([batch], {12: text}, [span])["assertions"]
        ]
        note = next(r for r in rows if r["quantity"] == "annotated_time")
        with self.assertRaises(ValueError):
            validate_links([note], [])

    def test_attached_footnote_marker_is_preserved_but_not_a_numeric_component(self):
        from src.assembly import assemble

        for expression, quantity, components, value in [
            ("9°17′²", "meridian_distance", dict(degree="9", arcminute="17"), "33420"),
            ("H. 6 M. 6⅖¹", "recorded_clock", dict(hour="6", minute="6⅖"), "21984"),
        ]:
            text = expression + "\n"
            sha = hashlib.sha256(text.encode()).hexdigest()
            span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
            row = dict(
                key="a",
                line=1,
                span_id="s",
                source_expression=expression,
                source_note_marker_original=expression[-1],
                quantity=quantity,
                role="recorded_reading",
                subject="Mars",
                components=components,
                unit_basis="Printed units",
            )
            batch = dict(
                id="review",
                volume=12,
                edition_sha256=sha,
                line_start=1,
                line_end=1,
                interval_sha256=hashlib.sha256(expression.encode()).hexdigest(),
                basis=dict(kind="source_review", printed_page=44),
                span_decisions=[dict(span_id="s", decision="include", reason="Reviewed")],
                assertions=[row],
            )
            with self.subTest(expression=expression):
                compiled = compile_catalogue([batch], {12: text}, [span])["assertions"]
                self.assertEqual(compiled[0]["normalized"]["magnitude"], value)
                self.assertEqual(
                    assemble({12: text}, compiled, [], [], [])["items"][0]["source_expression"],
                    expression,
                )
                row["source_note_marker_original"] = "³"
                with self.assertRaises(ValueError):
                    compile_catalogue([batch], {12: text}, [span])
