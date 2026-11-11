import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src import inventory
from src.__main__ import inventory as run_inventory


class InventoryReferenceTests(unittest.TestCase):
    def research_calibration_fixture(self, text=None):
        text = text or (
            "### Table of refractions\n\nSpica adopted declination 8°57½′.\n\n"
            "| Altitude | Refraction |\n|---|---|\n| 1° | 22′0″ |\n\n"
            "### Sun\n\nSun altitude 30°.\n\n### Mars\n\nMars distant from Spica 24°26½′.\n"
        )
        lines = text.splitlines()
        h = lambda s: hashlib.sha256(s.encode()).hexdigest()
        sha = h(text)
        refs = [
            dict(
                id="research-" + str(a),
                volume=11,
                edition_sha256=sha,
                line_start=a,
                line_end=b,
                interval_sha256=h("\n".join(lines[a - 1 : b])),
                reference_parent_line=15,
                parent_line_sha256=h(lines[14]),
                reference_kind="research_calibration",
                research_basis="shared_comparison_star",
                historical_application_established=False,
                scope_heading_line=1,
                scope_heading_sha256=h(lines[0]),
                scope_end_line=7,
                calibration_anchor_line=3,
                calibration_anchor_sha256=h(lines[2]),
                shared_reference_name="Spica",
                parent_endpoint_literal="Spica",
                calibration_endpoint_literal="Spica",
                reason="Supporting refraction research; no printed Mars cross-reference asserted.",
            )
            for a, b in ((1, 1), (3, 3), (5, 7))
        ]
        return text, sha, refs

    def test_research_calibration_admits_only_reviewed_blocks_without_claiming_historical_use(self):
        for source in (
            None,
            self.research_calibration_fixture()[0]
            .replace("22′0″", "47′9″")
            .replace("24°26½′", "9°1′"),
        ):
            text, sha, refs = self.research_calibration_fixture(source)
            try:
                out = inventory.inventory_text(text, 11, sha, reference_reviews=refs)
            except ValueError as error:
                self.fail("Reviewed research calibration must be selectable: " + str(error))
            self.assertEqual([s["line_start"] for s in out["spans"]], [1, 3, 5, 13, 15])
            for span in out["spans"][:3]:
                self.assertEqual(span["selection_reasons"], ["reviewed_research_calibration"])
                self.assertEqual(span["research_support_parent_span_id"], out["spans"][-1]["id"])
                self.assertFalse(span["historical_application_established"])
                self.assertNotIn("source_reference_parent_span_id", span)
                self.assertNotEqual(span["section_subject"], "Mars")

    def test_research_calibration_rejects_stale_or_unrelated_evidence(self):
        text, sha, refs = self.research_calibration_fixture()
        for change in (
            dict(historical_application_established=True),
            dict(research_basis="printed_cross_reference"),
            dict(scope_heading_sha256="0" * 64),
            dict(calibration_anchor_sha256="0" * 64),
            dict(parent_endpoint_literal="Jupiter"),
            dict(calibration_endpoint_literal="Jupiter"),
            dict(shared_reference_name=""),
            dict(scope_end_line=15),
            dict(scope_end_line=5),
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                inventory.inventory_text(text, 11, sha, reference_reviews=[dict(refs[2], **change)])
        text, sha, refs = self.research_calibration_fixture(
            text.replace("Mars distant", "Sun distant")
        )
        with self.assertRaises(ValueError):
            inventory.inventory_text(text, 11, sha, reference_reviews=refs)

    def test_named_instrument_input_crosses_only_its_bound_comparison_heading(self):
        def fixture(text=None):
            text = text or (
                "#### DIE 6 FEBRUARIJ.\n\n- Canis Major 8 27 4 by mural.\n\n"
                "#### Ratio differentiarum inter muralem et quadratum.\n\n"
                "- Canis Major 1 24\n- Mars 0 36\n"
            )
            lines = text.splitlines()
            h = lambda s: hashlib.sha256(s.encode()).hexdigest()
            ref = dict(
                id="input",
                volume=10,
                edition_sha256=h(text),
                line_start=3,
                line_end=3,
                interval_sha256=h(lines[2]),
                reference_parent_line=7,
                parent_line_sha256=h(lines[6]),
                reference_kind="following_context",
                reference_phrase="Canis Major",
                reference_parent_phrase="Canis Major",
                comparison_heading_line=5,
                comparison_heading_sha256=h(lines[4]),
                source_input_date_line=1,
                source_input_date_sha256=h(lines[0]),
                reason="Named input to the following comparison",
            )
            return text, ref

        for source in (None, fixture()[0].replace("8 27 4", "11 51 20").replace("1 24", "9 42")):
            text, ref = fixture(source)
            result = inventory.inventory_text(
                text, 10, ref["edition_sha256"], reference_reviews=[ref]
            )
            self.assertEqual([s["line_start"] for s in result["spans"]], [3, 7])
            self.assertEqual(
                result["spans"][0]["source_reference_parent_span_id"], result["spans"][1]["id"]
            )
        text, ref = fixture()
        for changes in (
            dict(comparison_heading_sha256="0" * 64),
            dict(source_input_date_sha256="0" * 64),
            dict(reference_parent_phrase="Jupiter"),
            dict(reference_phrase="Jupiter"),
            dict(source_input_date_line=3),
            dict(comparison_heading_line=1),
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                inventory.inventory_text(
                    text, 10, ref["edition_sha256"], reference_reviews=[dict(ref, **changes)]
                )
        for source in (
            text.replace("Ratio differentiarum inter muralem et quadratum.", "DIE 7 FEBRUARIJ."),
            text.replace(
                "Canis Major 8 27 4 by mural.", "### Other date\n- Canis Major 8 27 4 by mural."
            ),
        ):
            altered, review = fixture(source)
            with self.assertRaises(ValueError):
                inventory.inventory_text(
                    altered, 10, review["edition_sha256"], reference_reviews=[review]
                )

    def eclipse_back_reference_fixture(self, text=None):
        text = text or (
            "### ECLIPSIS ☽ ANNO 78 15 SEPTEMB.\n\nMoon clocks: 13 35.\n\n"
            "### N. B. DE ECLIPSI ☽ ANTECEDENTE.\n\nMoon timing explanation.\n\n"
            "Mars calculation, as can be gathered from what precedes.\n"
        )
        ls = text.splitlines()
        sha = hashlib.sha256(text.encode()).hexdigest()
        ref = dict(
            id="eclipse-back-reference",
            volume=10,
            edition_sha256=sha,
            line_start=3,
            line_end=3,
            interval_sha256=hashlib.sha256(ls[2].encode()).hexdigest(),
            reference_kind="report_back_reference",
            reference_parent_line=9,
            parent_line_sha256=hashlib.sha256(ls[8].encode()).hexdigest(),
            scope_start_line=1,
            scope_start_sha256=hashlib.sha256(ls[0].encode()).hexdigest(),
            scope_heading_line=5,
            scope_heading_sha256=hashlib.sha256(ls[4].encode()).hexdigest(),
            scope_end_line=7,
            reference_parent_phrase="as can be gathered from what precedes",
            reference_phrase="Moon clocks",
            reason="Explicit lunar eclipse input to the following Mars calculation.",
        )
        return text, sha, ref

    def test_eclipse_back_reference_admits_only_its_bound_block(self):
        for text in (None, self.eclipse_back_reference_fixture()[0].replace("13 35", "14 55")):
            t, sha, ref = self.eclipse_back_reference_fixture(text)
            out = inventory.inventory_text(t, 10, sha, reference_reviews=[ref])
            self.assertEqual([s["line_start"] for s in out["spans"]], [3, 9])
            self.assertEqual(
                out["spans"][0]["source_reference_parent_span_id"], out["spans"][1]["id"]
            )
            self.assertNotEqual(out["spans"][0]["section_subject"], "Mars")
            self.assertEqual(out["spans"][0]["review_status"], "unreviewed")

    def test_eclipse_back_reference_rejects_unrelated_or_unbound_scope(self):
        t, sha, ref = self.eclipse_back_reference_fixture()
        for change in (
            dict(scope_start_sha256="0" * 64),
            dict(scope_heading_sha256="0" * 64),
            dict(scope_end_line=3),
            dict(reference_parent_phrase="some earlier material"),
            dict(scope_start_line=3),
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                inventory.inventory_text(t, 10, sha, reference_reviews=[dict(ref, **change)])
        for text in (
            t.replace("DE ECLIPSI ☽ ANTECEDENTE", "DIE 16 SEPTEMBRIS"),
            t.replace("Mars calculation", "Moon calculation"),
            t.replace("as can be gathered from what precedes", "a separate later calculation"),
        ):
            tt, ss, rr = self.eclipse_back_reference_fixture(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                inventory.inventory_text(tt, 10, ss, reference_reviews=[rr])

    def column_context_fixture(self, text=None):
        text = text or (
            "Mars and Venus: 8°28′.\n\n### Right column\n\n"
            "This observation was repeated and once varied by one minute.\n\n**DIE 26 APRILIS.**\n"
        )
        ls = text.splitlines()
        sha = hashlib.sha256(text.encode()).hexdigest()
        ref = dict(
            id="column-repetition",
            volume=10,
            edition_sha256=sha,
            line_start=5,
            line_end=5,
            interval_sha256=hashlib.sha256(ls[4].encode()).hexdigest(),
            reference_kind="column_context",
            reference_parent_line=1,
            parent_line_sha256=hashlib.sha256(ls[0].encode()).hexdigest(),
            scope_heading_line=3,
            scope_heading_sha256=hashlib.sha256(ls[2].encode()).hexdigest(),
            reference_phrase="This observation was repeated",
            reason="Bound anaphoric note across one column heading",
        )
        return text, sha, ref

    def test_column_context_admits_repetition_without_assigning_a_target_or_value(self):
        for text in (None, self.column_context_fixture()[0].replace("8°28′", "19°10′")):
            t, sha, ref = self.column_context_fixture(text)
            try:
                out = inventory.inventory_text(t, 10, sha, reference_reviews=[ref])
            except ValueError as error:
                self.fail(f"Bound column continuation must be retained: {error}")
            self.assertEqual([s["line_start"] for s in out["spans"]], [1, 5])
            self.assertEqual(
                out["spans"][1]["source_reference_parent_span_id"], out["spans"][0]["id"]
            )
            self.assertIsNone(out["spans"][1]["section_subject"])

    def test_column_context_rejects_unbound_headings_dates_and_repetition_wording(self):
        t, sha, ref = self.column_context_fixture()
        for change in (
            dict(scope_heading_sha256="0" * 64),
            dict(reference_phrase="a later observation"),
            dict(scope_heading_line=7),
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                inventory.inventory_text(t, 10, sha, reference_reviews=[dict(ref, **change)])
        for tt in (
            t.replace("Right column", "DIE 25 APRILIS."),
            t.replace("This observation was repeated", "Some other observation"),
            t.replace("Mars and Venus", "Sun and Jupiter"),
        ):
            tt, ss, rr = self.column_context_fixture(tt)
            with self.subTest(text=tt), self.assertRaises(ValueError):
                inventory.inventory_text(tt, 10, ss, reference_reviews=[rr])

    def markdown_note_fixture(self, text=None):
        text = text or (
            "Mars and Venus 4°18′[^p46-1].\n\n## Another date\n\n"
            "Sun observed.\n\n[^p46-1]: These two distances were not observed on 20 March.\n"
        )
        ls = text.splitlines()
        sha = hashlib.sha256(text.encode()).hexdigest()
        ref = dict(
            id="dated-marked-note",
            volume=10,
            edition_sha256=sha,
            line_start=7,
            line_end=7,
            interval_sha256=hashlib.sha256(ls[6].encode()).hexdigest(),
            reference_kind="marked_note",
            reference_marker="[^p46-1]",
            reference_parent_line=1,
            parent_line_sha256=hashlib.sha256(ls[0].encode()).hexdigest(),
            reason="Explicit page-qualified note marker preserves the date warning across headings.",
        )
        return text, sha, ref

    def test_page_qualified_markdown_note_binds_across_headings_without_value_matching(self):
        for text in (None, self.markdown_note_fixture()[0].replace("4°18′", "99°1′")):
            t, sha, ref = self.markdown_note_fixture(text)
            try:
                out = inventory.inventory_text(t, 10, sha, reference_reviews=[ref])
            except ValueError as error:
                self.fail(f"Explicit Markdown note must retain its parent: {error}")
            self.assertEqual([s["line_start"] for s in out["spans"]], [1, 7])
            self.assertEqual(
                out["spans"][1]["source_reference_parent_span_id"], out["spans"][0]["id"]
            )

    def test_markdown_note_requires_the_full_marker_and_definition(self):
        t, sha, ref = self.markdown_note_fixture()
        for change in (
            dict(reference_marker="[^p47-1]"),
            dict(reference_parent_marker="[^p47-1]"),
            dict(reference_marker="[^p46-2]"),
            dict(reference_marker="[^unknown]"),
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                inventory.inventory_text(t, 10, sha, reference_reviews=[dict(ref, **change)])
        tt, ss, rr = self.markdown_note_fixture(t.replace("[^p46-1]:", "[^p46-1]"))
        with self.assertRaises(ValueError):
            inventory.inventory_text(tt, 10, ss, reference_reviews=[rr])

    def column_fixture(self, text=None):
        text = text or (
            "**DIE 1 MARTIJ.**\n\n| Mars and Taurus | 21 5 |\n\n"
            "### Right column[^ed7]\n\n| Venus and Aries | 8 2 |\n| Jupiter and Regulus | 13 14 |\n\n"
            "**DIE 5 MARTIJ.**\n\n[^ed7]: The entry for 1 March resumes at the top of this column.\n"
        )
        ls = text.splitlines()
        sha = hashlib.sha256(text.encode()).hexdigest()
        ref = dict(
            id="continued-column",
            volume=10,
            edition_sha256=sha,
            line_start=7,
            line_end=8,
            interval_sha256=hashlib.sha256("\n".join(ls[6:8]).encode()).hexdigest(),
            reference_kind="column_continuation",
            reference_parent_line=3,
            parent_line_sha256=hashlib.sha256(ls[2].encode()).hexdigest(),
            date_heading_line=1,
            date_heading_sha256=hashlib.sha256(ls[0].encode()).hexdigest(),
            scope_heading_line=5,
            scope_heading_sha256=hashlib.sha256(ls[4].encode()).hexdigest(),
            reference_note_line=12,
            reference_note_sha256=hashlib.sha256(ls[11].encode()).hexdigest(),
            reference_marker="[^ed7]",
            reference_date=dict(month=3, day=1),
            reference_phrase="The entry for 1 March resumes at the top of this column.",
            reason="Explicit edition layout note resumes the same recorded date.",
        )
        return text, sha, ref

    def test_column_note_selects_continued_table_without_numerical_matching(self):
        for text in (None, self.column_fixture()[0].replace("8 2", "99 1")):
            t, sha, ref = self.column_fixture(text)
            try:
                out = inventory.inventory_text(t, 10, sha, reference_reviews=[ref])
            except ValueError as error:
                self.fail(f"Explicit column note must retain its date link: {error}")
            self.assertEqual([s["line_start"] for s in out["spans"]], [3, 7])
            self.assertEqual(
                out["spans"][1]["source_reference_parent_span_id"], out["spans"][0]["id"]
            )
            self.assertEqual(out["spans"][1]["selection_reasons"], ["reviewed_reference_scope"])

    def test_column_note_rejects_stale_dates_markers_and_intervening_headings(self):
        t, sha, ref = self.column_fixture()
        for change in (
            dict(reference_date=dict(month=3, day=5)),
            dict(reference_marker="[^ed8]"),
            dict(reference_note_sha256="0" * 64),
            dict(date_heading_sha256="0" * 64),
            dict(scope_heading_sha256="0" * 64),
            dict(reference_parent_line=7),
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                inventory.inventory_text(t, 10, sha, reference_reviews=[dict(ref, **change)])
        for text in (
            t.replace("DIE 1", "DIE 2"),
            t.replace("for 1 March", "for 5 March"),
            t.replace("Right column", "Saturn"),
            t.replace("Mars and", "Sun and"),
            t.replace("| Venus and Aries | 8 2 |", "### Another date"),
        ):
            tt, ss, rr = self.column_fixture(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                inventory.inventory_text(tt, 10, ss, reference_reviews=[rr])

    def test_explicit_reference_to_existing_region_preserves_selection_and_still_validates(self):
        text = "Mars calibration^1^.\n\n^1^ Later witness.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        lines = text.splitlines()
        ref = dict(
            id="existing-note",
            volume=10,
            edition_sha256=sha,
            line_start=3,
            line_end=3,
            interval_sha256=hashlib.sha256(lines[2].encode()).hexdigest(),
            reference_kind="marked_note",
            reference_marker="^1^",
            reference_parent_line=1,
            parent_line_sha256=hashlib.sha256(lines[0].encode()).hexdigest(),
            reason="Retain exact parent even though the note is already independently selected.",
        )
        original = inventory.inventory_text(text, 10, sha)
        linked = inventory.inventory_text(text, 10, sha, reference_reviews=[ref])
        self.assertEqual(original, linked)
        for change in (dict(parent_line_sha256="0" * 64), dict(reference_marker="^2^")):
            with self.subTest(change=change), self.assertRaises(ValueError):
                inventory.inventory_text(text, 10, sha, reference_reviews=[dict(ref, **change)])

    def dated_fixture(self, text=None):
        text = text or (
            "# ANNO 1570\n\n### DIE 3 MARTIJ\n\nMars timed this comparison.\n\n"
            "Aldebaran and the northern horn: 16°55′.\n\n### DIE 25 MARTIJ\n\nMars observed.\n\n"
            "### INSTRUMENT CALIBRATION\n\nAbove, on 3 March, Aldebor. and the bor. horn: 16.53.\n\n"
            "| Pair | Old | Later |\n|---|---|---|\n| stars | 4 45 | 4 49 |\n\n"
            "These apply to this instrument^2^.\n\n### DIE 28 MARTIJ\n\nSaturn elsewhere.\n\n^2^ Only in another witness.\n"
        )
        ls = text.splitlines()
        sha = hashlib.sha256(text.encode()).hexdigest()
        refs = []
        for a, b in [(15, 15), (17, 19), (21, 21)]:
            refs.append(
                dict(
                    id="dated-" + str(a),
                    volume=10,
                    edition_sha256=sha,
                    line_start=a,
                    line_end=b,
                    interval_sha256=hashlib.sha256("\n".join(ls[a - 1 : b]).encode()).hexdigest(),
                    reference_kind="dated_source_companion",
                    reference_parent_line=7,
                    parent_line_sha256=hashlib.sha256(ls[6].encode()).hexdigest(),
                    scope_year_line=1,
                    scope_year_sha256=hashlib.sha256(ls[0].encode()).hexdigest(),
                    parent_date_heading_line=3,
                    parent_date_heading_sha256=hashlib.sha256(ls[2].encode()).hexdigest(),
                    scope_heading_line=13,
                    scope_heading_sha256=hashlib.sha256(ls[12].encode()).hexdigest(),
                    reference_anchor_line=15,
                    reference_anchor_sha256=hashlib.sha256(ls[14].encode()).hexdigest(),
                    reference_phrase="Above, on 3 March",
                    reference_date=dict(year=1570, month=3, day=3),
                    scope_end_line=21,
                    endpoint_pairs=[
                        dict(
                            object="Aldebaran",
                            parent_expression="Aldebaran",
                            anchor_expression="Aldebor.",
                        ),
                        dict(
                            object="northern horn",
                            parent_expression="northern horn",
                            anchor_expression="bor. horn",
                        ),
                    ],
                    reason="Explicit date and endpoints identify an earlier calibration, despite unequal numbers.",
                )
            )
        refs.append(
            dict(
                id="dated-note",
                volume=10,
                edition_sha256=sha,
                line_start=27,
                line_end=27,
                interval_sha256=hashlib.sha256(ls[26].encode()).hexdigest(),
                reference_marker="^2^",
                reference_parent_line=21,
                parent_line_sha256=hashlib.sha256(ls[20].encode()).hexdigest(),
                reason="Explicit note parent",
            )
        )
        return text, sha, refs

    def test_dated_companions_keep_values_out_of_selection_and_preserve_note_chain(self):
        for text in [None, self.dated_fixture()[0].replace("16.53", "0.01")]:
            t, sha, refs = self.dated_fixture(text)
            out = inventory.inventory_text(t, 10, sha, reference_reviews=refs)
            self.assertEqual([s["line_start"] for s in out["spans"]], [5, 7, 11, 15, 17, 21, 27])
            self.assertEqual(
                out["spans"][-1]["source_reference_parent_span_id"], out["spans"][-2]["id"]
            )
            self.assertEqual(out, inventory.inventory_text(t, 10, sha, reference_reviews=refs))

    def test_dated_companions_reject_unbound_dates_endpoints_and_scope(self):
        t, sha, refs = self.dated_fixture()
        for changes in [
            dict(reference_date=dict(year=1571, month=3, day=3)),
            dict(reference_date=dict(year=1570, month=3, day=4)),
            dict(reference_anchor_sha256="bad"),
            dict(scope_end_line=14),
            dict(
                endpoint_pairs=[
                    dict(object="angle", parent_expression="16°55′", anchor_expression="16.53")
                ]
            ),
        ]:
            bad = json.loads(json.dumps(refs))
            bad[0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                inventory.inventory_text(t, 10, sha, reference_reviews=bad)
        for text in [
            t.replace("### DIE 3 MARTIJ", "### DIE 4 MARTIJ"),
            t.replace("### DIE 25 MARTIJ", "# ANNO 1571"),
            t.replace("16.53.\n\n", "16.53.\n### Saturn\n"),
            t.replace("Mars timed", "Sun timed"),
        ]:
            tt, ss, rr = self.dated_fixture(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                inventory.inventory_text(tt, 10, ss, reference_reviews=rr)

    def test_report_continuation_and_its_marked_note_keep_an_explicit_chain(self):
        text = (
            "### Calculation of the preceding observation\n\nMars altitude 23½.\n\n"
            "### FROM THE PRECEDING OBSERVATION\n\nIn the first observation, a value was omitted¹.\n\n"
            "### Another date\n\n^1^ The rest is missing.\n"
        )
        lines = text.splitlines()
        sha = hashlib.sha256(text.encode()).hexdigest()
        refs = [
            dict(
                id="continued-report",
                volume=10,
                edition_sha256=sha,
                line_start=7,
                line_end=7,
                interval_sha256=hashlib.sha256(lines[6].encode()).hexdigest(),
                reference_kind="report_continuation",
                reference_parent_line=3,
                parent_line_sha256=hashlib.sha256(lines[2].encode()).hexdigest(),
                scope_start_line=1,
                scope_start_sha256=hashlib.sha256(lines[0].encode()).hexdigest(),
                scope_heading_line=5,
                scope_heading_sha256=hashlib.sha256(lines[4].encode()).hexdigest(),
                scope_heading_phrase="FROM THE PRECEDING OBSERVATION",
                scope_end_line=7,
                reference_phrase="In the first observation",
                reason="Explicitly continued report",
            ),
            dict(
                id="continued-note",
                volume=10,
                edition_sha256=sha,
                line_start=11,
                line_end=11,
                interval_sha256=hashlib.sha256(lines[10].encode()).hexdigest(),
                reference_marker="^1^",
                reference_parent_marker="¹",
                reference_parent_line=7,
                parent_line_sha256=hashlib.sha256(lines[6].encode()).hexdigest(),
                reason="Explicit marked note",
            ),
        ]
        try:
            out = inventory.inventory_text(text, 10, sha, reference_reviews=refs)
        except ValueError as error:
            self.fail(f"Bound report and note must retain their source chain: {error}")
        self.assertEqual([s["line_start"] for s in out["spans"]], [3, 7, 11])
        self.assertEqual(out["spans"][2]["source_reference_parent_span_id"], out["spans"][1]["id"])
        bad = json.loads(json.dumps(refs))
        bad[1]["reference_parent_marker"] = "²"
        with self.assertRaises(ValueError):
            inventory.inventory_text(text, 10, sha, reference_reviews=bad)

    def test_caret_note_marker_preserves_explicit_late_mars_note(self):
        text = "Mars: 40^1^ minutes of Virgo.\n\n## Saturn\n\nSaturn observed.\n\n^1^ In the margin: or 10.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        lines = text.splitlines()
        ref = dict(
            id="caret-note",
            volume=10,
            edition_sha256=sha,
            line_start=7,
            line_end=7,
            interval_sha256=hashlib.sha256(lines[6].encode()).hexdigest(),
            reference_marker="^1^",
            reference_parent_line=1,
            parent_line_sha256=hashlib.sha256(lines[0].encode()).hexdigest(),
            reason="Explicit source note marker, not inherited planetary scope",
        )
        try:
            result = inventory.inventory_text(text, 10, sha, reference_reviews=[ref])
        except ValueError as error:
            self.fail(f"Final-edition caret note must retain its explicit link: {error}")
        self.assertEqual([s["line_start"] for s in result["spans"]], [1, 7])
        self.assertEqual(result, inventory.inventory_text(text, 10, sha, reference_reviews=[ref]))

    def headed_fixture(self, text=None):
        text = text or (
            "Mars: this instrument needs another correction, as may be seen below.\n\n"
            "### IN DISTANTIJS.\n\nAt about 20 degrees the parallax is one minute.\n\n"
            "At 10 degrees add four minutes for parallax.\n\n### ANNO 1570\n\nA separate star table.\n"
        )
        lines = text.splitlines()
        sha = hashlib.sha256(text.encode()).hexdigest()
        reviews = []
        for start in (5, 7):
            reviews.append(
                dict(
                    id="headed-" + str(start),
                    volume=10,
                    edition_sha256=sha,
                    line_start=start,
                    line_end=start,
                    interval_sha256=hashlib.sha256(lines[start - 1].encode()).hexdigest(),
                    reference_parent_line=1,
                    parent_line_sha256=hashlib.sha256(lines[0].encode()).hexdigest(),
                    reference_kind="headed_continuation",
                    reference_parent_phrase="as may be seen below",
                    scope_heading_line=3,
                    scope_heading_sha256=hashlib.sha256(lines[2].encode()).hexdigest(),
                    scope_end_line=7,
                    reference_phrase="parallax",
                    reason="Explicit forward reference into a bounded subsection",
                )
            )
        return text, sha, reviews

    def test_explicit_headed_continuation_selects_only_bound_calibration_paragraphs(self):
        text, sha, reviews = self.headed_fixture()
        self.assertEqual(
            [s["line_start"] for s in inventory.inventory_text(text, 10, sha)["spans"]], [1]
        )
        try:
            result = inventory.inventory_text(text, 10, sha, reference_reviews=reviews)
        except ValueError as error:
            self.fail("Explicit bounded forward reference must admit calibration: " + str(error))
        self.assertEqual([s["line_start"] for s in result["spans"]], [1, 5, 7])
        for span in result["spans"][1:]:
            self.assertEqual(span["source_reference_parent_span_id"], result["spans"][0]["id"])
            self.assertEqual(span["review_status"], "unreviewed")
            self.assertIsNone(span["section_subject"])

    def test_headed_continuation_requires_forward_phrase_one_bound_heading_and_independent_parent(
        self,
    ):
        for change in (
            "wrong-phrase",
            "stale-heading",
            "outside-scope",
            "extra-heading",
            "unselected-parent",
            "ordinary-context",
        ):
            text, sha, reviews = self.headed_fixture()
            if change == "extra-heading":
                text, sha, reviews = self.headed_fixture(
                    text.replace("\n\nAt 10", "\n### Another subsection\nAt 10")
                )
            elif change == "unselected-parent":
                text, sha, reviews = self.headed_fixture(text.replace("Mars:", "Jupiter:"))
            elif change == "wrong-phrase":
                reviews[0]["reference_parent_phrase"] = "as may be seen above"
            elif change == "stale-heading":
                reviews[0]["scope_heading_sha256"] = "0" * 64
            elif change == "outside-scope":
                reviews[1]["scope_end_line"] = 5
            else:
                reviews[0]["reference_kind"] = "preceding_context"
            with self.subTest(change=change), self.assertRaises(ValueError):
                inventory.inventory_text(text, 10, sha, reference_reviews=reviews)
        text, sha, reviews = self.headed_fixture()
        reviews[0]["scope_end_line"] = 11
        with self.assertRaises(ValueError):
            inventory.inventory_text(text, 10, sha, reference_reviews=reviews)

    text = "## Mars\n\nThe apogee requires at least 1½°¹.\n\n## Venus\n\nVenus was observed¹.\n\n¹ That is, 2ˢ 0°36′ minus 1ˢ 58°56′ equals 1°40′.\n"

    def review(self):
        lines = self.text.splitlines()
        return dict(
            id="mars-note",
            volume=12,
            edition_sha256=hashlib.sha256(self.text.encode()).hexdigest(),
            line_start=9,
            line_end=9,
            interval_sha256=hashlib.sha256(lines[8].encode()).hexdigest(),
            reference_parent_line=3,
            parent_line_sha256=hashlib.sha256(lines[2].encode()).hexdigest(),
            reference_marker="¹",
            reason="Scan shows the note refers to the marked Mars apogee claim.",
        )

    def screen(self, reviews):
        return inventory.inventory_text(
            self.text,
            12,
            self.review()["edition_sha256"],
            {n: dict(page=152) for n in range(1, 10)},
            reference_reviews=reviews,
        )

    def test_marked_mars_note_survives_a_different_planet_heading(self):
        plain = inventory.inventory_text(self.text, 12, self.review()["edition_sha256"])
        self.assertFalse(any(s["line_start"] == 9 for s in plain["spans"]))
        result = self.screen([self.review()])
        note = next(s for s in result["spans"] if s["line_start"] == 9)
        self.assertEqual(note["text_original"], self.text.splitlines()[8])
        self.assertIn("reviewed_reference_scope", note["selection_reasons"])
        self.assertEqual(note["source_reference_review_id"], "mars-note")
        self.assertEqual(note["review_status"], "unreviewed")
        self.assertEqual(note["section_subject"], "other")
        self.assertFalse(any(s["line_start"] in (5, 7) for s in result["spans"]))
        self.assertEqual(result["coverage"]["candidate_spans"], len(plain["spans"]) + 1)
        self.assertEqual(result["coverage"]["reviewed_spans"], 0)
        self.assertEqual(result, self.screen([self.review()]))

    def test_reference_selection_rejects_stale_or_unbound_evidence(self):
        for update in [
            dict(edition_sha256="0" * 64),
            dict(interval_sha256="0" * 64),
            dict(parent_line_sha256="0" * 64),
            dict(reference_marker="²"),
            dict(
                reference_parent_line=7,
                parent_line_sha256=hashlib.sha256("Venus was observed¹.".encode()).hexdigest(),
            ),
            dict(line_start=8),
            dict(line_end=10),
        ]:
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.screen([{**self.review(), **update}])
        with self.assertRaises(ValueError):
            self.screen([self.review(), self.review()])

    def test_inventory_command_reuses_the_version_bound_reference_ledger(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / "library"
            bench = Path(name) / "benchmark"
            out = Path(name) / "output"
            relative = "brahe/thesaurus_observationum_vol3/translation/brahe_thesaurus_observationum_vol3_prepub.md"
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_text(self.text)
            bench.mkdir()
            out.mkdir()
            (bench / "source_hashes.json").write_text(
                json.dumps({relative: self.review()["edition_sha256"]})
            )
            (bench / "observations.json").write_text("[]")
            (bench / "record_outcomes.json").write_text("[]")
            ledger = out / "source_reference_reviews.json"
            ledger.write_text(json.dumps([self.review()]))
            args = SimpleNamespace(
                source_root=str(root), benchmark=str(bench), output=str(out), volumes=[12]
            )
            with contextlib.redirect_stdout(io.StringIO()):
                run_inventory(args)
            spans = [
                json.loads(s) for s in (out / "inventory_spans.jsonl").read_text().splitlines()
            ]
            self.assertTrue(any(s["line_start"] == 9 for s in spans))
            manifest = json.loads((out / "inventory_manifest.json").read_text())
            self.assertEqual(
                manifest.get("source_reference_reviews_sha256"),
                hashlib.sha256(ledger.read_bytes()).hexdigest(),
            )
            first = (out / "inventory_spans.jsonl").read_bytes()
            with contextlib.redirect_stdout(io.StringIO()):
                run_inventory(args)
            self.assertEqual(first, (out / "inventory_spans.jsonl").read_bytes())

    def following_fixture(self, text=None, parent=5, phrase="following"):
        text = (
            text
            or "## Venus\n\nThe clock was ten minutes fast in the following observations.\n\n| Between Venus and Mars |\n|---|\n| 43°6′ |\n"
        )
        lines = text.splitlines()
        sha = hashlib.sha256(text.encode()).hexdigest()
        review = dict(
            id="clock-context",
            volume=12,
            edition_sha256=sha,
            line_start=3,
            line_end=3,
            interval_sha256=hashlib.sha256(lines[2].encode()).hexdigest(),
            reference_parent_line=parent,
            parent_line_sha256=hashlib.sha256(lines[parent - 1].encode()).hexdigest(),
            reference_kind="following_context",
            reference_phrase=phrase,
            reason="Clock statement scopes the following pointings.",
        )
        return text, sha, review

    def test_clock_context_can_link_forward_to_independently_selected_pointings(self):
        text, sha, review = self.following_fixture()
        result = inventory.inventory_text(text, 12, sha, reference_reviews=[review])
        context = next(s for s in result["spans"] if s["line_start"] == 3)
        parent = next(s for s in result["spans"] if s["line_start"] == 5)
        self.assertEqual(context["source_reference_parent_span_id"], parent["id"])
        self.assertEqual(context["review_status"], "unreviewed")
        self.assertEqual(context["section_subject"], "other")
        self.assertEqual(len(result["spans"]), 2)

    def test_forward_context_cannot_cross_a_heading_or_use_an_absent_phrase(self):
        text = "## Venus\n\nThe clock was ten minutes fast in the following observations.\n\n### 10 November\n\n| Between Venus and Mars |\n|---|\n| 43°6′ |\n"
        for args in [dict(text=text, parent=7), dict(phrase="previous")]:
            text, sha, review = self.following_fixture(**args)
            with self.subTest(args=args), self.assertRaises(ValueError):
                inventory.inventory_text(text, 12, sha, reference_reviews=[review])

    def preceding_fixture(self, text=None, parent=3, start=5):
        text = (
            text
            or "## Calibration\n\nMars crossed the meridian.\n\nVenus provided a later instrument check.\n"
        )
        lines = text.splitlines()
        sha = hashlib.sha256(text.encode()).hexdigest()
        review = dict(
            id="later-calibration",
            volume=12,
            edition_sha256=sha,
            line_start=start,
            line_end=start,
            interval_sha256=hashlib.sha256(lines[start - 1].encode()).hexdigest(),
            reference_parent_line=parent,
            parent_line_sha256=hashlib.sha256(lines[parent - 1].encode()).hexdigest(),
            reference_kind="preceding_context",
            reference_phrase="instrument check",
            reason="Scan review connects the later calibration to the preceding Mars transit.",
        )
        return text, sha, review

    def test_later_calibration_links_to_independent_mars_context_without_selecting_a_planet_section(
        self,
    ):
        text, sha, review = self.preceding_fixture()
        self.assertFalse(
            any(s["line_start"] == 5 for s in inventory.inventory_text(text, 12, sha)["spans"])
        )
        result = inventory.inventory_text(text, 12, sha, reference_reviews=[review])
        source = next(s for s in result["spans"] if s["line_start"] == 5)
        parent = next(s for s in result["spans"] if s["line_start"] == 3)
        self.assertEqual(source["source_reference_parent_span_id"], parent["id"])
        self.assertEqual(source["review_status"], "unreviewed")
        self.assertEqual(source["text_original"], text.splitlines()[4])
        self.assertEqual(len(result["spans"]), 2)

    def test_later_context_rejects_heading_crossing_wrong_order_and_chained_reviews(self):
        text = "## Calibration\n\nMars crossed the meridian.\n\n## Venus\n\nVenus provided a later instrument check.\n"
        for args in [dict(text=text, start=7), dict(parent=5, start=3)]:
            text, sha, review = self.preceding_fixture(**args)
            with self.subTest(args=args), self.assertRaises(ValueError):
                inventory.inventory_text(text, 12, sha, reference_reviews=[review])
        text = "## Calibration\n\nMars crossed the meridian.\n\nVenus provided a later instrument check.\n\nVenus provided another instrument check.\n"
        text, sha, first = self.preceding_fixture(text=text)
        _, _, second = self.preceding_fixture(text=text, parent=5, start=7)
        second["id"] = "chained-calibration"
        with self.assertRaises(ValueError):
            inventory.inventory_text(text, 12, sha, reference_reviews=[first, second])

    def report_fixture(self):
        text = "## Observations sent by Fabricius\n\n## Mars\n\nMars was observed at 10 degrees.\n\n## Mercury\n\nMercury was observed.\n\nAll these observations were made at Resterhafe.\n\n## Another report\n\nMars was observed elsewhere.\n"
        lines = text.splitlines()
        sha = hashlib.sha256(text.encode()).hexdigest()
        review = dict(
            id="report-site",
            volume=12,
            edition_sha256=sha,
            line_start=11,
            line_end=11,
            interval_sha256=hashlib.sha256(lines[10].encode()).hexdigest(),
            reference_parent_line=5,
            parent_line_sha256=hashlib.sha256(lines[4].encode()).hexdigest(),
            reference_kind="report_scope",
            reference_phrase="All these observations",
            scope_start_line=1,
            scope_start_sha256=hashlib.sha256(lines[0].encode()).hexdigest(),
            scope_end_line=11,
            reason="Explicit closing site declaration scopes the named report, including its Mars section.",
        )
        return text, sha, review

    def test_explicit_report_scope_admits_only_the_closing_statement_across_planet_headings(self):
        text, sha, review = self.report_fixture()
        prior = inventory.inventory_text(text, 12, sha)["spans"]
        current = inventory.inventory_text(text, 12, sha, reference_reviews=[review])["spans"]
        self.assertEqual([s for s in current if s["line_start"] != 11], prior)
        added = next(s for s in current if s["line_start"] == 11)
        self.assertEqual(
            added["source_reference_parent_span_id"],
            next(s["id"] for s in prior if s["line_start"] == 5),
        )
        self.assertEqual(added["source_reference_review_id"], review["id"])
        self.assertEqual(added["review_status"], "unreviewed")
        self.assertFalse(any(s["line_start"] == 9 for s in current))

    def test_report_scope_rejects_unbound_header_outside_parent_and_missing_scope_language(self):
        text, sha, review = self.report_fixture()
        lines = text.splitlines()
        for change in (
            dict(scope_start_sha256="0" * 64),
            dict(scope_start_line=0),
            dict(
                scope_start_line=5, scope_start_sha256=hashlib.sha256(lines[4].encode()).hexdigest()
            ),
            dict(scope_end_line=15),
            dict(reference_phrase="these"),
            dict(
                reference_parent_line=15,
                parent_line_sha256=hashlib.sha256(lines[14].encode()).hexdigest(),
            ),
            dict(
                reference_parent_line=9,
                parent_line_sha256=hashlib.sha256(lines[8].encode()).hexdigest(),
            ),
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                inventory.inventory_text(text, 12, sha, reference_reviews=[dict(review, **change)])
