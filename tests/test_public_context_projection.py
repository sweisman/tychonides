import copy
import hashlib
import importlib
import importlib.util
import unittest


class PublicContextProjectionTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(
            importlib.util.find_spec("src.public_context_projection"),
            "Public source-location projection is missing",
        )
        return importlib.import_module("src.public_context_projection")

    def test_locations_are_public_references_and_geometry_numbers_stay_numeric(self):
        m = self.module()
        context = dict(
            id="c",
            review_id="r",
            volume=11,
            line=100,
            edition_sha256="a" * 64,
            kind="source_observation_context",
            value=dict(
                source_hour_line=100,
                instrument_by_line={"101": "mural quadrant"},
                source_section_headings=[[98, "### Mars[^ed1]"]],
                source_scope_line_range=[100, 101],
                line_below_reference_degrees_as_stated=2,
                line_offset_limit_arcminutes_as_stated=10,
            ),
        )
        before = copy.deepcopy(context)
        projected, loci = m.project_contexts(
            [context],
            {11: {100: dict(page=334), 101: dict(page=334)}},
            quantities=[dict(id="q", volume=11, line=100)],
        )
        value = projected[0]["value"]
        by_id = {r["id"]: r for r in loci}
        self.assertNotIn("source_hour_line", value)
        self.assertEqual(by_id[value["source_hour_locus_id"]]["printed_page"], 334)
        self.assertEqual(by_id[value["source_hour_locus_id"]]["quantity_ids"], ["q"])
        self.assertEqual(
            by_id[value["source_hour_locus_id"]]["context_ids"],
            [dict(context_id="c", scope_id=hashlib.sha256(b"r").hexdigest())],
        )
        self.assertEqual(value["line_below_reference_degrees_as_stated"], 2)
        self.assertEqual(value["line_offset_limit_arcminutes_as_stated"], 10)
        self.assertEqual(list(value["instrument_by_locus"].values()), ["mural quadrant"])
        self.assertEqual(value["source_section_headings"][0]["heading"], "### Mars")
        self.assertEqual(context, before)
        self.assertNotIn("source_scope_line_range", value)
        self.assertEqual(
            [by_id[p]["printed_page"] for p in value["source_scope_locus_range"]],
            [334, 334],
        )
        self.assertTrue(all("line" not in r for r in loci))

    def test_qualified_payloads_and_unknown_pages_are_not_collapsed_or_guessed(self):
        m = self.module()
        contexts = [
            dict(
                id="same",
                review_id=r,
                volume=11,
                kind="source_observation_context",
                value=dict(source_line=n),
            )
            for r, n in (("r1", 100), ("r2", 999))
        ]
        projected, loci = m.project_contexts(contexts, {11: {100: dict(page=334)}})
        self.assertEqual(len(projected), 2)
        self.assertEqual([c["review_id"] for c in projected], ["r1", "r2"])
        self.assertEqual({r["printed_page"] for r in loci}, {334, None})
        self.assertTrue(any(r["status"] == "page_unestablished" for r in loci))

    def test_note_attachment_page_is_qualified_without_paginating_the_note(self):
        from src.historical_reviews import review_provenance

        def review(name, start, end, page, **basis):
            return dict(
                id=name,
                source_id="book",
                line_start=start,
                line_end=end,
                basis=dict(printed_page=page, **basis),
            )

        reviews = [
            review("left", 100, 100, 306),
            review("right", 100, 100, 307),
            review("note", 200, 200, None),
            review(
                "citation",
                200,
                200,
                None,
                annotation_attachment_citations=[
                    dict(review_id="note", context_key="note", line=100, printed_page=306)
                ],
            ),
        ]
        provenance = review_provenance(reviews, {})
        context = dict(
            id="note",
            review_id="note",
            source_id="book",
            edition_sha256="a" * 64,
            kind="source_observation_context",
            lines=[200, 100],
            value=dict(
                record_type="edition_annotation",
                note_marker="[^ed1]",
                definition_line=200,
                attachment_lines=[100],
            ),
        )
        projected, loci = self.module().project_contexts([context], provenance)
        byid = {r["id"]: r for r in loci}
        value = projected[0]["value"]
        self.assertEqual(byid[value["attachment_locus_ids"][0]]["printed_page"], 306)
        self.assertIsNone(byid[value["definition_locus_id"]]["printed_page"])
        self.assertEqual(provenance["book"][100]["pages"], [306, 307])
        self.assertEqual(provenance[("book", "citation")][100]["page"], 306)
        self.assertEqual(provenance[("book", "left")][100]["page"], 306)
        self.assertEqual(provenance[("book", "right")][100]["page"], 307)
        conflicting = copy.deepcopy(reviews[-1])
        conflicting["id"] = "conflicting"
        conflicting["basis"]["annotation_attachment_citations"][0]["printed_page"] = 307
        with self.assertRaises(ValueError):
            review_provenance([*reviews, conflicting], {})

    def test_editorial_projection_requires_a_bound_approval(self):
        m = self.module()
        context = dict(
            id="c",
            review_id="r",
            volume=11,
            kind="source_observation_context",
            value=dict(limit="Scientific qualifier", source_evidence="recovery/private-note.json"),
        )
        with self.assertRaises(ValueError):
            m.project_contexts([context], {})
        approval = dict(
            context_id="c",
            review_id="r",
            original_value_sha256=m.value_hash(context["value"]),
            value=dict(limit="Scientific qualifier"),
            reason="Public citation replaces internal working reference.",
        )
        projected, _ = m.project_contexts([context], {}, approvals=[approval])
        self.assertEqual(projected[0]["value"], {"limit": "Scientific qualifier"})
        approval["original_value_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            m.project_contexts([context], {}, approvals=[approval])

    def test_source_relocation_is_review_scoped_and_does_not_move_numeric_angles(self):
        m = self.module()
        context = dict(
            id="c",
            review_id="old",
            volume=11,
            kind="source_observation_context",
            value=dict(source_line=102, line_offset_limit_arcminutes_as_stated=10),
        )
        binding = dict(
            review_id="old",
            original_interval=dict(line_start=100, line_end=110),
            line_offset=-2,
            supporting_lines=[],
        )
        projected, loci = m.project_contexts(
            [context], {11: {100: dict(page=334)}}, bindings=[binding]
        )
        self.assertEqual(loci[0]["printed_page"], 334)
        self.assertEqual(projected[0]["value"]["line_offset_limit_arcminutes_as_stated"], 10)

    def test_reviewed_quantity_page_is_not_overwritten_by_automatic_page_metadata(self):
        m = self.module()
        context = dict(
            id="c",
            review_id="r",
            volume=10,
            kind="source_observation_context",
            value=dict(source_line=100),
        )
        _, loci = m.project_contexts(
            [context],
            {10: {100: dict(page=17)}},
            quantities=[dict(id="q", volume=10, line=100, printed_page=283)],
        )
        self.assertEqual(loci[0]["printed_page"], 283)
        self.assertEqual(loci[0]["provisional_page_claim"], 17)
        self.assertEqual(loci[0]["page_basis"], "reviewed_quantity_citation")

    def test_reference_keys_resolve_with_their_declared_source_scope(self):
        m = self.module()
        context = dict(
            id="c",
            review_id="r",
            volume=11,
            kind="source_observation_context",
            value=dict(
                source_hour_clock_key="clock",
                source_log_clock_key="clock",
                source_log_review_id="other",
                source_minute_clock_key="absent",
            ),
        )
        quantities = [
            dict(id=identifier, key="clock", review_id=review, volume=11, line=n)
            for identifier, review, n in (("own", "r", 100), ("quoted", "other", 200))
        ]
        projected, _ = m.project_contexts([context], {}, quantities=quantities)
        value = projected[0]["value"]
        self.assertEqual(value["source_hour_clock_ref"], dict(kind="quantity", id="own"))
        self.assertEqual(value["source_log_clock_ref"], dict(kind="quantity", id="quoted"))
        self.assertEqual(value["source_minute_clock_ref"]["status"], "unresolved_source_reference")
        self.assertNotIn("source_log_review_id", value)


if __name__ == "__main__":
    unittest.main()
