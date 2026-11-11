import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path


class ProvenanceTests(unittest.TestCase):
    def module(self):
        try:
            return importlib.import_module("src.provenance")
        except ModuleNotFoundError:
            self.fail("Reference provenance resolver is not implemented")

    def item(self, text, line, volume=10):
        return dict(
            id="item",
            volume=volume,
            line=line,
            edition_sha256=hashlib.sha256(text.encode()).hexdigest(),
            bibliographic_pages=[],
            candidate_intervals=[],
            anchor_status="unique_source_interval",
        )

    def test_footnote_reference_pages_remain_claims_not_invented_note_pages(self):
        text = "Observation[^n].\n\n[^n]: Time H. 8 M. 50.\n"
        item = self.item(text, 3)
        r = self.module().enrich([item], {10: text}, {10: {1: {"page": 48}, 3: {"page": None}}})
        claim = r["provenance"][0]
        self.assertEqual(item["bibliographic_pages"], [])
        self.assertEqual(claim["upstream_bibliographic_pages"], [])
        self.assertEqual(claim["note_reference_pages"], [48])
        self.assertEqual(claim["citation_status"], "note_reference_locus_only")
        self.assertEqual(claim["note_key"], "n")

    def test_note_keys_do_not_cross_volumes(self):
        first = "Value[^n].\n\n[^n]: 12°.\n"
        second = "Value[^n].\n\n[^n]: 15°.\n"
        a = self.item(first, 3)
        b = dict(self.item(second, 3, 11), id="second")
        r = self.module().enrich(
            [a, b], {10: first, 11: second}, {10: {1: {"page": 48}}, 11: {1: {"page": 125}}}
        )
        self.assertEqual([c["note_reference_pages"] for c in r["provenance"]], [[48], [125]])

    def test_nested_references_resolve_but_cycles_do_not_invent_locations(self):
        text = "Value[^a].\n\n[^a]: See note[^b].\n\n[^b]: 12°.\n"
        r = self.module().enrich([self.item(text, 5)], {10: text}, {10: {1: {"page": 48}}})
        self.assertEqual(r["provenance"][0]["note_reference_pages"], [48])
        self.assertTrue(r["provenance"][0]["note_resolution"]["used_nested_reference"])
        cycle = "[^a]: Note[^b].\n\n[^b]: Note[^a].\n"
        r = self.module().enrich([self.item(cycle, 1)], {10: cycle}, {10: {}})
        self.assertEqual(r["provenance"][0]["note_reference_pages"], [])
        self.assertIn("reference_cycle", r["provenance"][0]["note_resolution"]["flags"])

    def test_duplicate_definition_keys_keep_the_reference_ambiguous(self):
        text = "Value[^n].\n\n[^n]: First.\n\n[^n]: Other.\n"
        r = self.module().enrich([self.item(text, 3)], {10: text}, {10: {1: {"page": 48}}})
        self.assertEqual(r["provenance"][0]["note_reference_pages"], [])
        self.assertIn("duplicate_definition_key", r["provenance"][0]["note_resolution"]["flags"])
        self.assertEqual(len(r["definitions"]), 2)

    def test_standalone_reference_can_retain_its_preceding_block_as_context_only(self):
        text = "| Reading | Value |\n|---|---|\n| Declination | 12 30 |\n\n[^n]\n\n[^n]: 12°.\n"
        r = self.module().enrich([self.item(text, 7)], {10: text}, {10: {3: {"page": 48}}})
        claim = r["provenance"][0]
        self.assertEqual(claim["note_reference_pages"], [])
        self.assertEqual(claim["note_reference_context_pages"], [48])
        self.assertEqual(claim["citation_status"], "reference_context_only")
        self.assertIsNone(claim["accepted_note_printed_page"])
        self.assertEqual(
            r["references"][0]["attachment"]["relation"], "standalone_reference_after_block"
        )

    def test_reference_attachment_does_not_search_past_a_heading_for_a_page(self):
        text = "Known body\n\n## New section\n\n[^n]\n\n[^n]: 12°.\n"
        r = self.module().enrich([self.item(text, 7)], {10: text}, {10: {1: {"page": 48}}})
        self.assertEqual(r["provenance"][0]["note_reference_context_pages"], [])

    def test_parallel_locations_are_classified_without_choosing_one(self):
        text = "17 20 [17 20]"
        row = dict(
            candidate_intervals=[dict(char_start=0, char_end=5), dict(char_start=7, char_end=12)]
        )
        r = self.module().analyze_anchor(row, text)
        self.assertEqual(r["layer_counts"], {"main": 1, "bracketed": 1})
        self.assertEqual(r["diagnosis"], "main_and_bracketed_locations")
        self.assertIsNone(r["selected_interval"])

    def test_repeated_and_parallel_locations_are_not_collapsed(self):
        text = "17 20; repeated 17 20 [17 20; repeated 17 20]"
        import re

        row = dict(
            candidate_intervals=[
                dict(char_start=m.start(), char_end=m.end()) for m in re.finditer("17 20", text)
            ]
        )
        r = self.module().analyze_anchor(row, text)
        self.assertEqual(r["layer_counts"], {"main": 2, "bracketed": 2})
        self.assertEqual(r["diagnosis"], "repetition_and_parallel_locations")
        self.assertIsNone(r["selected_interval"])

    def test_workspace_keeps_assembly_immutable_and_reproduces_claims(self):
        m = self.module()
        text = "Observation[^n].\n\n[^n]: 12°.\n"
        item = self.item(text, 3)
        sha = item["edition_sha256"]
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            work = base / "mars"
            source.mkdir()
            work.mkdir()
            relative = "brahe/thesaurus_observationum_vol1/translation/brahe_thesaurus_observationum_vol1_prepub.md"
            path = source / relative
            path.parent.mkdir(parents=True)
            path.write_text(text)
            (work / "witnesses.json").write_text(
                json.dumps([dict(volume=10, private_source=relative, edition_sha256=sha)])
            )
            (work / "inventory_manifest.json").write_text(
                json.dumps(dict(source_hashes={relative: sha}))
            )
            (work / "catalogue_items.jsonl").write_text(json.dumps(item) + "\n")
            (work / "provenance_v10.json").write_text(json.dumps({"1": {"page": 48}}))
            (work / "assembly_manifest.json").write_text(
                json.dumps(
                    dict(
                        output_hashes={
                            "catalogue_items.jsonl": hashlib.sha256(
                                (work / "catalogue_items.jsonl").read_bytes()
                            ).hexdigest()
                        }
                    )
                )
            )
            original = (work / "catalogue_items.jsonl").read_bytes()
            m.build_provenance(source, work)
            names = [
                "catalogue_provenance.jsonl",
                "note_definitions.csv",
                "provenance_manifest.json",
            ]
            snapshot = {name: (work / name).read_bytes() for name in names}
            m.build_provenance(source, work)
            self.assertEqual(snapshot, {name: (work / name).read_bytes() for name in names})
            self.assertEqual((work / "catalogue_items.jsonl").read_bytes(), original)
            self.assertEqual(path.read_text(), text)
            self.assertNotIn("text_original", (work / "public_provenance_summary.json").read_text())
            path.write_text(text + "changed")
            with self.assertRaisesRegex(ValueError, "[Ff]ingerprint"):
                m.build_provenance(source, work)


if __name__ == "__main__":
    unittest.main()
