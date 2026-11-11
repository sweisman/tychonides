import hashlib
import contextlib
import io
import importlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src import publication


class InventoryTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec("src.inventory"), "Missing inventory module")
        return importlib.import_module("src.inventory")

    def screen(self, text, provenance=None):
        return self.module().inventory_text(
            text, 12, hashlib.sha256(text.encode()).hexdigest(), provenance or {}
        )

    def test_numeric_continuations_stay_in_mars_section_and_stop_at_saturn(self):
        text = "## Observations of Mars\n\n### 4 March\n| Time | Declination |\n|---|---|\n| 7 | 9° 1′ |\n\n### 5 March\n| | |\n|---|---|\n| 8 | 9° 2′ |\n\n## Observations of Saturn\n| Time | Declination |\n|---|---|\n| 9 | 10° 2′ |\n"
        spans = self.screen(text)["spans"]
        self.assertTrue(any("9° 2′" in s["text_original"] for s in spans))
        self.assertFalse(any("10° 2′" in s["text_original"] for s in spans))

    def test_mixed_target_reference_and_following_table_are_screened_independently_of_pafko(self):
        text = "## Observations of Jupiter\n\nThe distance between Jupiter and Mars was observed.\n\n| Time | Distance |\n|---|---|\n| 7 | 20° 1′ |\n\nJupiter was observed again.\n\n| Time | Altitude |\n|---|---|\n| 8 | 30° 1′ |\n"
        spans = self.screen(text)["spans"]
        self.assertTrue(any("20° 1′" in s["text_original"] for s in spans))
        self.assertFalse(any("30° 1′" in s["text_original"] for s in spans))

    def test_weekday_words_and_symbols_do_not_create_planetary_readings(self):
        result = self.screen(
            "## Observations of Saturn\n\n### Tuesday 10 November [DIE MARTIS 10 NOUEMBRIS.]\n\n**DIE 15 MAIJ, QUI ERAT ♂.** [15 May, which was ♂]\n\n| Time | Altitude |\n|---|---|\n| 7 | 20° 1′ |\n"
        )
        self.assertEqual(result["spans"], [])
        self.assertEqual(result["coverage"]["weekday_marker_lines"], 2)

    def test_full_text_audit_reports_unselected_long_s_reference_without_inventing_readings(self):
        mod = self.module()
        text = "## Saturn\n\nDIE MARTIS\n\nMarſ was compared with a star.\n"
        report = mod.audit_screening(text, [])
        self.assertEqual(report["unselected_reference_lines"], [5])
        self.assertEqual(report["weekday_only_lines"], [3])
        self.assertEqual(report["status"], "additional_reference_review_needed")
        self.assertNotIn("measurements", report)

    def test_diagram_is_a_candidate_context_not_a_verified_measurement(self):
        result = self.screen("**Diagram.** A line connects Mars to a comparison star.\n")
        self.assertEqual(result["spans"][0]["block_kind"], "diagram")
        self.assertEqual(result["spans"][0]["review_status"], "unreviewed")
        self.assertEqual(result["coverage"]["reviewed_spans"], 0)
        self.assertNotIn("measurements", result)

    def test_page_coverage_preserves_unmapped_lines_and_does_not_claim_inspection(self):
        text = "Mars was observed.\nThe instrument was changed.\n\nAn unrelated paragraph.\n"
        mapping = {1: dict(page=44, pdf_page=58), 2: dict(page=45, pdf_page=59)}
        result = self.screen(text, mapping)
        self.assertEqual(result["spans"][0]["printed_pages"], [44, 45])
        self.assertEqual(result["coverage"]["screened_lines"], len(text.splitlines()))
        self.assertEqual(result["coverage"]["unmapped_nonblank_lines"], 1)
        self.assertTrue(
            all(p["inspection_status"] == "unreviewed" for p in result["coverage"]["pages"])
        )
        self.assertEqual(result, self.screen(text, mapping))

    def test_benchmark_links_use_source_location_not_angle_or_missing_control_insertion(self):
        mod = self.module()
        text = "Mars was observed.\n\n| Time | Declination |\n|---|---|\n| 7 | 9° 1′ |\n"
        spans = self.screen(text)["spans"]
        before = list(spans)
        obs = [dict(id="book:5:2", volume=12, line=5, magnitude_arcsec="32460")]
        outcomes = [dict(pafko_id="Sheet1:1", candidate_ids=["book:5:2"])]
        first = mod.benchmark_links(spans, obs, outcomes)
        obs[0]["magnitude_arcsec"] = "99999"
        self.assertEqual(first, mod.benchmark_links(spans, obs, outcomes))
        self.assertEqual(first[0]["coverage_status"], "covered")
        obs[0]["line"] = 99
        self.assertEqual(
            mod.benchmark_links(spans, obs, outcomes)[0]["coverage_status"],
            "outside_selected_spans",
        )
        self.assertEqual(spans, before)

    def test_publication_loader_preserves_final_text_and_separate_provenance(self):
        self.assertTrue(
            hasattr(publication, "load_publication"), "Missing reusable publication loader"
        )
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            directory = root / "brahe/thesaurus_observationum_vol3/translation"
            directory.mkdir(parents=True)
            text = "### 4 March\nMars was observed.\n| Time | Declination |\n|---|---|\n| 7 | 9° 1′ |\n"
            (directory / "brahe_thesaurus_observationum_vol3_prepub.md").write_text(text)
            (directory / "batch_029.md").write_text(
                "[Running header: 1590 44]\n<!-- PDF p. 58 (printed p. 44) -->\n" + text
            )
            loaded = publication.load_publication(root, 12)
            self.assertEqual(loaded["text"], text)
            self.assertEqual(loaded["provenance"][5]["page"], 44)
            self.assertEqual(loaded["sha256"], hashlib.sha256(text.encode()).hexdigest())

    def test_inventory_command_preserves_benchmark_and_exports_only_aggregate_screening(self):
        cli = importlib.import_module("src.__main__")
        self.assertTrue(hasattr(cli, "inventory"), "Missing inventory command")
        with tempfile.TemporaryDirectory() as name:
            base = Path(name)
            root = base / "library"
            d = root / "brahe/thesaurus_observationum_vol3/translation"
            d.mkdir(parents=True)
            text = "Mars was observed. PRIVATE SOURCE MARKER\n\n| Time | Declination |\n|---|---|\n| 7 | 9° 1′ |\n"
            source = "brahe/thesaurus_observationum_vol3/translation/brahe_thesaurus_observationum_vol3_prepub.md"
            (root / source).write_text(text)
            (d / "batch_001.md").write_text("[Running header: 1590 44]\n" + text)
            bench = base / "benchmark"
            bench.mkdir()
            payloads = {
                "source_hashes.json": {source: hashlib.sha256(text.encode()).hexdigest()},
                "observations.json": [dict(id=source + ":5:2", source=source, volume=12, line=5)],
                "record_outcomes.json": [
                    dict(pafko_id="Sheet1:1", volume=12, candidate_ids=[source + ":5:2"])
                ],
            }
            for n, payload in payloads.items():
                (bench / n).write_text(json.dumps(payload))
            before = {n: (bench / n).read_bytes() for n in payloads}
            args = SimpleNamespace(
                source_root=str(root), output=str(base / "out"), benchmark=str(bench), volumes=[12]
            )
            with contextlib.redirect_stdout(io.StringIO()):
                cli.inventory(args)
            report = json.loads((base / "out" / "public_inventory_summary.json").read_text())
            self.assertEqual(report["benchmark_controls_covered"], 1)
            self.assertEqual(report["reviewed_spans"], 0)
            self.assertNotIn("PRIVATE SOURCE MARKER", json.dumps(report))
            self.assertNotIn(name, json.dumps(report))
            self.assertEqual(before, {n: (bench / n).read_bytes() for n in payloads})
            args.output = str(bench)
            with self.assertRaises(ValueError):
                cli.inventory(args)
            args.output = str(root / "out")
            with self.assertRaises(ValueError):
                cli.inventory(args)


if __name__ == "__main__":
    unittest.main()
