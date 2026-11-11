import copy
import hashlib
import json
import unittest

from src.catalog import compile_catalogue


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def review_sha(review):
    return sha(json.dumps(review, sort_keys=True, ensure_ascii=False, separators=(",", ":")))


class SourceBindingTests(unittest.TestCase):
    def fixture(self):
        old = (
            "Mars north 1° 2′; adopted north 2° 4′\nThe clock behaved well enough [unchanged Latin]"
        )
        current = "New heading\n" + old.replace("well enough", "fairly well")
        original_span = dict(
            id="s",
            volume=11,
            edition_sha256=sha(old),
            line_start=1,
            line_end=2,
            text_original=old,
            block_kind="paragraph",
        )
        current_span = dict(
            original_span,
            id="t",
            line_start=2,
            line_end=3,
            text_original="\n".join(current.splitlines()[1:]),
        )
        assertion = dict(
            key="first",
            line=1,
            span_id="s",
            source_expression="1° 2′",
            quantity="declination",
            role="recorded_coordinate",
            subject="Mars",
            reference=None,
            direction="north",
            components=dict(degree="1", arcminute="2"),
            flags=[],
            unit_basis="Printed degrees and minutes",
            event_key="event",
        )
        second = dict(
            assertion,
            key="second",
            source_expression="2° 4′",
            role="reduction",
            components=dict(degree="2", arcminute="4"),
        )
        batch = dict(
            id="review",
            volume=11,
            edition_sha256=sha(old),
            line_start=1,
            line_end=2,
            interval_sha256=sha(old),
            basis=dict(kind="final_edition_review", printed_page=178),
            assertions=[assertion, second],
            contexts=[
                dict(
                    key="quality",
                    lines=[2],
                    kind="source_observation_context",
                    value=dict(quality="as stated"),
                )
            ],
            events=[dict(key="event", line=1, clock_key=None, context_keys=["quality"])],
            derivations=[
                dict(
                    key="double",
                    operation="sum",
                    input_keys=["first", "first"],
                    output_key="second",
                )
            ],
            span_decisions=[dict(span_id="s", decision="include", reason="Reviewed source")],
        )
        binding = dict(
            id="binding",
            volume=11,
            review_id="review",
            identity_edition_sha256=sha(old),
            original_source_sha256=sha(old),
            current_source_sha256=sha(current),
            original_review_sha256=review_sha(batch),
            line_offset=1,
            original_interval=dict(line_start=1, line_end=2, text=old, sha256=sha(old)),
            current_interval=dict(
                line_start=2, line_end=3, sha256=sha(current_span["text_original"])
            ),
            line_changes=[
                dict(
                    original_line=2,
                    current_line=3,
                    original_text=old.splitlines()[1],
                    current_text=current.splitlines()[2],
                    kind="translation_wording",
                )
            ],
            supporting_lines=[],
            span_bindings=[
                dict(
                    original_id="s",
                    current_generated_id="t",
                    original_line_start=1,
                    original_line_end=2,
                    current_line_start=2,
                    current_line_end=3,
                    current_text_sha256=sha(current_span["text_original"]),
                )
            ],
            prior_source_rows=[original_span],
        )
        return old, current, batch, original_span, current_span, binding

    def test_relocation_preserves_ids_values_and_relationships(self):
        old, current, batch, before, after, binding = self.fixture()
        frozen = copy.deepcopy(batch)
        original = compile_catalogue([batch], {11: old}, [before])
        migrated = compile_catalogue(
            [batch],
            {11: current},
            [after],
            edition_hashes={11: sha(old)},
            source_bindings=[binding],
        )
        self.assertEqual(batch, frozen)
        for kind in ("assertions", "events", "contexts", "derivations"):
            self.assertEqual([r["id"] for r in migrated[kind]], [r["id"] for r in original[kind]])
        for a, b in zip(original["assertions"], migrated["assertions"], strict=True):
            for key in ("normalized", "source_expression", "components", "context_ids", "event_id"):
                self.assertEqual(a[key], b[key])
            self.assertEqual(b["line"], a["line"] + 1)
        self.assertEqual(
            {a["normalized"]["magnitude"] for a in migrated["assertions"]}, {"3720", "7440"}
        )
        self.assertTrue(migrated["derivations"][0]["arithmetic_agrees"])

    def test_unreviewed_source_or_original_review_changes_fail(self):
        old, current, batch, _before, after, binding = self.fixture()
        for changed, review in (
            (current + "\nextra", batch),
            (current, dict(batch, basis=dict(batch["basis"], printed_page=179))),
        ):
            with self.subTest(source=changed[-10:]), self.assertRaises(ValueError):
                compile_catalogue(
                    [review],
                    {11: changed},
                    [after],
                    edition_hashes={11: sha(old)},
                    source_bindings=[binding],
                )

    def test_unlisted_edit_or_changed_latin_fails(self):
        old, current, batch, _before, after, binding = self.fixture()
        missing = copy.deepcopy(binding)
        missing["line_changes"] = []
        with self.assertRaises(ValueError):
            compile_catalogue(
                [batch],
                {11: current},
                [after],
                edition_hashes={11: sha(old)},
                source_bindings=[missing],
            )
        changed = current.replace("unchanged Latin", "different Latin")
        bad = copy.deepcopy(binding)
        bad["current_source_sha256"] = sha(changed)
        bad["current_interval"]["sha256"] = sha("\n".join(changed.splitlines()[1:]))
        bad["line_changes"][0]["current_text"] = changed.splitlines()[2]
        bad["span_bindings"][0]["current_text_sha256"] = bad["current_interval"]["sha256"]
        altered = dict(after, text_original="\n".join(changed.splitlines()[1:]))
        with self.assertRaises(ValueError):
            compile_catalogue(
                [batch],
                {11: changed},
                [altered],
                edition_hashes={11: sha(old)},
                source_bindings=[bad],
            )

    def test_span_aliases_are_unique_and_idempotent(self):
        from src.source_bindings import apply_span_bindings

        _old, _current, _batch, before, after, binding = self.fixture()
        collision = dict(after, id="s", line_start=1, line_end=1, text_original="New heading")
        unrelated = dict(before, id="unrelated", volume=10)
        first = apply_span_bindings([collision, after, unrelated], [binding])
        self.assertEqual(len({s["id"] for s in first}), 3)
        self.assertEqual(next(s for s in first if s["id"] == "s")["line_start"], 2)
        self.assertEqual(first[-1], unrelated)
        self.assertEqual(apply_span_bindings(first, [binding]), first)

    def test_relocation_does_not_rewrite_geometry_or_other_context_values(self):
        old, current, batch, _before, after, binding = self.fixture()
        value = dict(
            line=17, lines=["Mars", "reference star"], native=dict(line_start=1, line_end=2)
        )
        batch["contexts"][0]["value"] = copy.deepcopy(value)
        binding["original_review_sha256"] = review_sha(batch)
        migrated = compile_catalogue(
            [batch],
            {11: current},
            [after],
            edition_hashes={11: sha(old)},
            source_bindings=[binding],
        )
        self.assertEqual(migrated["contexts"][0]["value"], value)
        self.assertEqual(migrated["contexts"][0]["lines"], [3])

    def test_extraction_views_keep_legacy_ids_and_move_explicit_source_pointers(self):
        from src.source_bindings import rebind_extraction_inputs

        old, current, _batch, _before, _after, binding = self.fixture()
        observation = dict(
            id="book.md:1:prose1",
            source="book.md",
            volume=11,
            line=1,
            column=None,
            row_original=old.splitlines()[0],
            value_original="1° 2′",
            time_locus="book.md:1:1",
            hemisphere_locus="book.md:1:2",
            flags=[],
        )
        classification = dict(
            id="classification",
            volume=11,
            line=1,
            source_record_id=observation["id"],
            evidence_start=1,
            evidence_end=1,
            evidence_sha256=sha(old.splitlines()[0]),
            reviewed_target="Mars",
        )
        binding["observation_record_bindings"] = [
            dict(
                id=observation["id"],
                original_record_sha256=review_sha(observation),
                original_line=1,
                current_line=2,
                current_row_original=current.splitlines()[1],
                kind="unchanged",
                current_source_record_id="book.md:2:prose1",
                current_source_loci=dict(time_locus="book.md:2:1", hemisphere_locus="book.md:2:2"),
            )
        ]
        binding["coordinate_classification_bindings"] = [
            dict(
                id="classification",
                original_sha256=review_sha(classification),
                line_offset=1,
                original_source_record_id=observation["id"],
                current_source_record_id="book.md:2:prose1",
            )
        ]
        untouched = copy.deepcopy(observation)
        observations, classifications = rebind_extraction_inputs(
            [observation], [classification], {11: current}, [binding]
        )
        self.assertEqual(observation, untouched)
        self.assertEqual(observations[0]["id"], observation["id"])
        self.assertEqual(observations[0]["line"], 2)
        self.assertEqual(observations[0]["time_locus"], "book.md:2:1")
        self.assertEqual(classifications[0]["source_record_id"], observation["id"])
        self.assertEqual(classifications[0]["line"], 2)
        self.assertEqual(classifications[0]["evidence_sha256"], classification["evidence_sha256"])
        only_observations, omitted = rebind_extraction_inputs(
            [observation], None, {11: current}, [binding]
        )
        self.assertEqual(only_observations, observations)
        self.assertIsNone(omitted)
        bad = dict(observation, row_original="different original row")
        with self.assertRaises(ValueError):
            rebind_extraction_inputs([bad], [classification], {11: current}, [binding])

    def test_revised_uncertain_notation_cannot_reuse_a_legacy_scalar_or_change_a_control(self):
        from src.source_bindings import rebind_extraction_inputs
        from src.coordinate_staging import stage_coordinates

        _old, _current, batch, before, _after, binding = self.fixture()
        previous = "| time | declination | 17° 23¾′ |"
        text = "| time | declination | 17° 23 8/4′ [?] |"
        expression = "17° 23 8/4′ [?]"
        observation = dict(
            id="book.md:1:3",
            source="book.md",
            volume=11,
            line=1,
            column=3,
            row_original=previous,
            value_original="17° 23¾′",
            flags=[],
            arcsec="-62625",
            magnitude_arcsec="62625",
        )
        binding.update(current_source_sha256=sha(text), line_offset=0)
        binding["observation_record_bindings"] = [
            dict(
                id=observation["id"],
                original_record_sha256=review_sha(observation),
                original_line=1,
                current_line=1,
                current_row_original=text,
                kind="notation_revision",
                current_expression=expression,
                normalization_status="unresolved",
                workbook_source_membership="not_selected",
                current_source_record_id=observation["id"],
                current_source_loci={},
            )
        ]
        binding["coordinate_classification_bindings"] = []
        views, _ = rebind_extraction_inputs([observation], [], {11: text}, [binding])
        self.assertIsNone(views[0]["arcsec"])
        self.assertIsNone(views[0]["magnitude_arcsec"])
        self.assertEqual(views[0]["value_original"], "17° 23¾′")
        self.assertEqual(views[0]["legacy_normalization"]["magnitude_arcsec"], "62625")
        staged = stage_coordinates(
            views,
            {11: text},
            [dict(before, line_end=1)],
            [],
            [],
            edition_hashes={11: batch["edition_sha256"]},
        )
        self.assertIsNone(staged["coordinates"][0]["normalized"]["magnitude"])
        self.assertEqual(staged["coordinates"][0]["source_expression"], expression)
        with self.assertRaises(ValueError):
            rebind_extraction_inputs(
                [observation], [], {11: text}, [binding], control_source_ids={observation["id"]}
            )
