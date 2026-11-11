import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path


class NarrativeStagingTests(unittest.TestCase):
    def module(self):
        try:
            return importlib.import_module("src.narrative_staging")
        except ModuleNotFoundError:
            self.fail("Narrative expression staging is not implemented")

    def span(self, text, kind="paragraph", start=1):
        return dict(
            id=f"s-{start}",
            volume=10,
            edition_sha256=hashlib.sha256(text.encode()).hexdigest(),
            line_start=start,
            line_end=start + len(text.splitlines()) - 1,
            block_kind=kind,
            text_original=text,
            printed_pages=[385],
        )

    def test_prose_hour_angle_is_not_an_observing_clock(self):
        text = "When Regulus was distant from the meridian H. 8 M. 22, the declination of Mars was 17 20¼."
        r = self.module().stage_span(self.span(text))
        temporal = next(e for e in r["expressions"] if e["expression_kind"] == "time")
        decl = next(e for e in r["expressions"] if e["quantity_claim"] == "declination")
        self.assertEqual(temporal["temporal_role_claim"], "hour_angle_candidate")
        self.assertEqual(temporal["normalized"]["magnitude"], "30120")
        self.assertEqual(decl["normalized"]["magnitude"], "62415")
        self.assertIsNone(temporal["absolute_timestamp"])

    def test_unit_adjacent_dots_keep_complete_prose_expressions(self):
        text = "Declination 13°.0⅔′ North; right ascension 22°.43′.50″."
        result = self.module().stage_span(self.span(text))
        expressions = result["expressions"]
        self.assertEqual(
            [row["source_expression"] for row in expressions],
            ["13°.0⅔′", "22°.43′.50″"],
        )
        self.assertEqual(
            [row["normalized"]["magnitude"] for row in expressions], ["46840", "81830"]
        )
        for row in expressions:
            self.assertNotIn("possible_numeric_continuation_unresolved", row["flags"])
            self.assertEqual(text[row["char_start"] : row["char_end"]], row["source_expression"])

    def test_dotted_component_support_keeps_decimal_and_partial_guards(self):
        self.assertEqual(
            self.module().stage_span(self.span("Declination 13.5°."))["expressions"], []
        )
        for text in ("Declination 13°.2′.50", "Declination 13°.2′.5.5″"):
            with self.subTest(text=text):
                row = self.module().stage_span(self.span(text))["expressions"][0]
                self.assertIsNone(row["components"])
                self.assertIn("possible_numeric_continuation_unresolved", row["flags"])

    def test_explicit_list_label_and_clock_units_have_bounded_scope(self):
        m = self.module()
        label = dict(
            text="Distance between Mars and star A",
            line=10,
            spec=m.descriptor("Distance between Mars and star A"),
        )
        text = "- H.2 24 — 3 2⅔ — I — Alt. of Mars 47 50\n- 2 31¾ — 3 4¼ — II"
        r = m.stage_span(self.span(text, "list", 11), label)
        sep = [e for e in r["expressions"] if e["quantity_claim"] == "angular_separation"]
        self.assertEqual(len(sep), 2)
        self.assertEqual(sep[0]["normalized"]["magnitude"], "10960")
        self.assertEqual(sep[0]["endpoints"], ["Mars", "star A"])
        self.assertTrue(any(e["quantity_claim"] == "altitude" for e in r["expressions"]))
        clocks = [e for e in r["expressions"] if e["expression_kind"] == "time"]
        self.assertEqual(clocks[1]["normalized"]["magnitude"], "9105")
        self.assertIn("list_clock_units_from_prior_row", clocks[1]["flags"])

    def test_bare_list_without_a_label_is_preserved_without_guessed_measurements(self):
        r = self.module().stage_span(self.span("- 6 16 — 37 36", "list"))
        self.assertEqual(r["expressions"], [])
        self.assertEqual(r["material"]["text_original"], "- 6 16 — 37 36")
        self.assertGreater(len(r["material"]["numeric_fragments"]), 0)

    def test_metadata_and_reference_markers_are_not_numeric_observations(self):
        for text in (
            "<!-- (printed p. 385) -->",
            "[^ed1357]",
            "<!-- diagram id=fig-p129-1 source-page=129 -->",
        ):
            with self.subTest(text=text):
                r = self.module().stage_span(self.span(text, "annotation"))
                self.assertEqual(r["expressions"], [])
                self.assertEqual(r["material"]["numeric_fragments"], [])
                self.assertIn(
                    r["material"]["material_role"], ("structural_metadata", "reference_marker")
                )

    def test_bilingual_renderings_keep_distinct_locations_and_layers(self):
        text = "Altitude of Mars 14°20′ [Alt. Mars 14°20′]."
        r = self.module().stage_span(self.span(text))
        self.assertEqual(len(r["expressions"]), 2)
        self.assertEqual({e["rendering_layer"] for e in r["expressions"]}, {"main", "bracketed"})
        self.assertEqual(len({e["id"] for e in r["expressions"]}), 2)
        for e in r["expressions"]:
            self.assertEqual(text[e["char_start"] : e["char_end"]], e["source_expression"])

    def test_adopted_epoch_and_historical_degree_marks_are_retained(self):
        text = "Use the distance of Mars from star A, P. 2 M. 47½, for hour 6¾. Altitude of Mars 8^g^ 35′."
        r = self.module().stage_span(self.span(text))
        angle = next(e for e in r["expressions"] if e["source_expression"].startswith("P."))
        epoch = next(e for e in r["expressions"] if e["expression_kind"] == "time")
        altitude = next(e for e in r["expressions"] if "^g^" in e["source_expression"])
        self.assertEqual(angle["normalized"]["magnitude"], "10050")
        self.assertEqual(epoch["normalized"]["magnitude"], "24300")
        self.assertEqual(epoch["temporal_role_claim"], "calculation_epoch_candidate")
        self.assertEqual(altitude["normalized"]["magnitude"], "30900")

    def test_heading_breaks_list_label_even_if_heading_was_not_selected(self):
        m = self.module()
        text = "Distance between Mars and star A\n\n- H.2 24 — 3 2⅔ — I\n\n## Saturn\n\n- 4 12 — 5 20 — I"
        lines = text.splitlines()
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [
            dict(self.span(lines[i], kind, i + 1), edition_sha256=sha)
            for i, kind in [(0, "paragraph"), (2, "list"), (6, "list")]
        ]
        r = m.stage_narratives(spans, {10: text})
        last = next(x for x in r["materials"] if x["line_start"] == 7)
        self.assertIsNone(last["inherited_label"])
        self.assertFalse(any(e["line"] == 7 for e in r["expressions"]))

    def test_partial_and_decimal_forms_cannot_be_truncated_into_exact_values(self):
        for text in (
            "Altitude 17.25°.",
            "At H. 10 47 2/[?] the observation was uncertain.",
            "At 10^h^ 47 2/[?]^m^ it was cloudy.",
        ):
            with self.subTest(text=text):
                r = self.module().stage_span(self.span(text))
                self.assertFalse(
                    any(e["normalized"]["status"] == "exact" for e in r["expressions"])
                )

    def test_workspace_binds_sources_and_writes_only_private_raw_outputs(self):
        m = self.module()
        text = "Altitude of Mars 14°20′."
        span = self.span(text)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            work = root / "mars"
            source.mkdir()
            work.mkdir()
            relative = "brahe/thesaurus_observationum_vol1/translation/brahe_thesaurus_observationum_vol1_prepub.md"
            path = source / relative
            path.parent.mkdir(parents=True)
            path.write_text(text)
            (work / "witnesses.json").write_text(
                json.dumps(
                    [
                        dict(
                            volume=10,
                            private_source=relative,
                            edition_sha256=span["edition_sha256"],
                        )
                    ]
                )
            )
            (work / "inventory_manifest.json").write_text(
                json.dumps(dict(source_hashes={relative: span["edition_sha256"]}))
            )
            (work / "inventory_spans.jsonl").write_text(json.dumps(span) + "\n")
            m.build_narratives(source, work)
            summary = (work / "public_narrative_staging_summary.json").read_text()
            self.assertNotIn("source_expression", summary)
            names = [
                "narrative_materials.jsonl",
                "narrative_expressions.csv",
                "narrative_staging_manifest.json",
            ]
            snapshot = {n: (work / n).read_bytes() for n in names}
            m.build_narratives(source, work)
            self.assertEqual(snapshot, {n: (work / n).read_bytes() for n in names})
            self.assertEqual(path.read_text(), text)
            path.write_text(text + "changed")
            with self.assertRaisesRegex(ValueError, "[Ff]ingerprint"):
                m.build_narratives(source, work)


if __name__ == "__main__":
    unittest.main()
