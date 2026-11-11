import copy
import hashlib
import unittest

from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion, validate_links


class AngleComponentVariantTests(unittest.TestCase):
    def fixture(self, expression="43² 42", anchor="degree"):
        text = expression + "\nThe codex has 35.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=2)
        parent = dict(
            key="angle",
            line=1,
            span_id="s",
            source_expression=expression,
            quantity="meridian_distance",
            role="printed_correction",
            subject="mouth of Pegasus",
            reference=None,
            direction="west",
            components=dict(degree="43", arcminute="42"),
            source_note_marker_original="²",
            unit_basis="Reviewed degree/minute columns and native note marker",
            flags=["source_annotation_variant"],
        )
        if anchor is not None:
            parent["source_note_marker_after_unit"] = anchor
        note = dict(
            key="component",
            line=2,
            span_id="s",
            source_expression="35",
            quantity="angle_component",
            role="editorial_variant",
            subject="mouth of Pegasus",
            reference=None,
            direction=None,
            components=dict(degree="35"),
            annotation_of_key="angle",
            unit_basis="The note reports only the original degree component",
            flags=[
                "source_annotation_variant",
                "not_a_complete_angle",
                "not_an_additional_raw_reading",
            ],
        )
        batch = dict(
            id="angle-component-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=296),
            span_decisions=[
                dict(span_id="s", decision="context", reason="Reviewed note and marked angle")
            ],
            assertions=[parent, note],
            events=[],
        )
        return text, span, batch

    def compiled(self):
        text, span, batch = self.fixture()
        try:
            return compile_catalogue([batch], {12: text}, [span])
        except ValueError as error:
            self.fail("A reviewed degree-component annotation must compile: " + str(error))

    def test_degree_only_note_does_not_inherit_minutes_or_become_a_second_angle(self):
        compiled = self.compiled()
        rows = [public_assertion(a) for a in compiled["assertions"]]
        validate_links(rows, [])
        parent = next(a for a in rows if a["quantity"] == "meridian_distance")
        note = next(a for a in rows if a["quantity"] == "angle_component")
        self.assertEqual(parent["normalized"]["magnitude"], "157320")
        self.assertEqual(note["normalized"]["magnitude"], "35")
        self.assertEqual(note["normalized"]["unit"], "source_angle_component")
        self.assertEqual(note["normalized"]["least_component_unit"], "degree")
        self.assertIsNone(note["normalized"]["magnitude_degrees"])
        self.assertIsNone(note["normalized"]["signed_magnitude"])
        self.assertIsNone(note["event_id"])
        self.assertEqual(note["annotation_of_id"], parent["id"])
        self.assertEqual(
            next(a for a in compiled["assertions"] if a["quantity"] == "meridian_distance")[
                "source_expression"
            ],
            "43² 42",
        )

    def test_degree_annotation_requires_its_role_scope_and_component_unit(self):
        source = next(
            a for a in self.compiled()["assertions"] if a["quantity"] == "angle_component"
        )
        for change in (
            {"role": "recorded_reading"},
            {"annotation_of_id": None},
            {"flags": []},
            {"direction": "west"},
            {"event_id": "event-v12-" + "a" * 20},
        ):
            bad = copy.deepcopy(source)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
        for components in ({"arcsecond": "35"}, {"degree": "35", "arcminute": "42"}):
            with self.subTest(components=components), self.assertRaises(ValueError):
                normalize_quantity(dict(quantity="angle_component", components=components))
        bad = copy.deepcopy(source)
        bad["normalized"]["unit"] = "arcsecond"
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_degree_annotation_target_must_be_an_angle_with_matching_endpoints_and_volume(self):
        rows = [public_assertion(a) for a in self.compiled()["assertions"]]
        parent = next(a for a in rows if a["quantity"] == "meridian_distance")
        for change in (
            {"quantity": "recorded_clock"},
            {"volume": 13},
            {"subject": "Mars"},
            {"reference": "Aldebaran"},
            {"normalized": dict(parent["normalized"], unit="second_of_time")},
        ):
            wrong = copy.deepcopy(rows)
            next(a for a in wrong if a["id"] == parent["id"]).update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_links(wrong, [])

    def test_bare_degree_note_marker_is_removed_only_at_its_reviewed_anchor(self):
        for expression, anchor in [
            ("43² 42", None),
            ("43² 42", "minute"),
            ("43 42²", "degree"),
            ("43² 42 10", "degree"),
            ("43 ²42", "degree"),
        ]:
            text, span, batch = self.fixture(expression, anchor)
            with self.subTest(expression=expression, anchor=anchor), self.assertRaises(ValueError):
                compile_catalogue([batch], {12: text}, [span])
        text, span, batch = self.fixture()
        del batch["assertions"][0]["source_note_marker_original"]
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {12: text}, [span])

    def test_degree_unit_before_note_preserves_full_angle_and_annotation_target(self):
        text, span, batch = self.fixture("43°² 42′")
        try:
            compiled = compile_catalogue([batch], {12: text}, [span])
        except ValueError as error:
            self.fail("A degree mark must not prevent its reviewed note binding: " + str(error))
        rows = [public_assertion(a) for a in compiled["assertions"]]
        validate_links(rows, [])
        parent = next(a for a in compiled["assertions"] if a["key"] == "angle")
        note = next(a for a in rows if a["quantity"] == "angle_component")
        self.assertEqual(parent["source_expression"], "43°² 42′")
        self.assertEqual(parent["normalized"]["magnitude"], "157320")
        self.assertEqual(note["annotation_of_id"], parent["id"])
        self.assertEqual(note["normalized"]["unit"], "source_angle_component")

    def test_suggested_degree_remains_an_unapplied_component(self):
        text, span, batch = self.fixture()
        text = text.replace("The codex has 35.", "The editor suggests 35.")
        sha = hashlib.sha256(text.encode()).hexdigest()
        span["edition_sha256"] = batch["edition_sha256"] = sha
        batch["interval_sha256"] = hashlib.sha256(text.rstrip("\n").encode()).hexdigest()
        batch["assertions"][1]["role"] = "editorial_suggestion"
        batch["assertions"][1]["flags"].append("alternative_suggestion_not_applied")
        compiled = compile_catalogue([batch], {12: text}, [span])
        try:
            rows = [public_assertion(a) for a in compiled["assertions"]]
        except ValueError as error:
            self.fail(
                "An unapplied degree suggestion must retain its component role: " + str(error)
            )
        validate_links(rows, [])
        parent, note = rows
        self.assertEqual(parent["normalized"]["magnitude"], "157320")
        self.assertEqual(note["normalized"]["magnitude"], "35")
        self.assertEqual(note["normalized"]["unit"], "source_angle_component")
        self.assertIsNone(note["normalized"]["magnitude_degrees"])
        self.assertEqual(note["role"], "editorial_suggestion")
        bad = copy.deepcopy(compiled["assertions"][1])
        bad["flags"].remove("alternative_suggestion_not_applied")
        with self.assertRaises(ValueError):
            public_assertion(bad)


if __name__ == "__main__":
    unittest.main()
