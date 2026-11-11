import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path


class TableStagingTests(unittest.TestCase):
    def module(self):
        try:
            return importlib.import_module("src.table_staging")
        except ModuleNotFoundError:
            self.fail("Table-cell staging is not implemented")

    def span(self, text):
        return dict(
            id="table-1",
            volume=12,
            edition_sha256=hashlib.sha256(text.encode()).hexdigest(),
            line_start=1,
            line_end=len(text.splitlines()),
            text_original=text,
            block_kind="table",
            printed_pages=[120],
        )

    def test_wide_table_preserves_all_cells_and_separates_quantities(self):
        text = "| H. M. | Distance of Mars from star A | Altitude of Mars | Azimuth of Mars |\n|---|---|---|---|\n| 8 20 | 12 30¼ | 14 10 | 76 20 |\n| | 12 31 | | 77 0 |"
        r = self.module().stage_table(self.span(text))
        self.assertEqual(len(r["cells"]), 16)
        numeric = [c for c in r["cells"] if c["row_kind"] == "data" and c["contains_number"]]
        self.assertEqual(len(numeric), 6)
        altitude = next(c for c in numeric if c["quantity_claim"] == "altitude")
        self.assertEqual(altitude["normalized"]["magnitude"], "51000")
        distance = next(c for c in numeric if c["quantity_claim"] == "angular_separation")
        self.assertEqual(distance["normalized"]["magnitude"], "45015")
        self.assertEqual(distance["endpoints"], ["Mars", "star A"])
        self.assertEqual(r["events"][1]["clock_cell_id"], None)
        self.assertEqual(r["summary"]["inspected_spans_added"], 0)

    def test_reading_value_rows_resolve_labels_without_target_leakage(self):
        text = "| Time | Reading | Value |\n|---|---|---|\n| 5^h^ 12^m^ | Declination of Mars | 18°5½′ |\n| | With the other pinnule | 18°5¼′ |\n| | Altitude of the Moon | 31°20′ |\n| | Declination of the Moon | 27°21′ |"
        r = self.module().stage_table(self.span(text))
        rows = [c for c in r["cells"] if c["row_kind"] == "data" and c["column"] == 3]
        self.assertEqual(
            [c["quantity_claim"] for c in rows],
            ["declination", "declination", "altitude", "declination"],
        )
        self.assertEqual([c["subject_claim"] for c in rows], ["Mars", "Mars", "Moon", "Moon"])
        self.assertIn("inherited_row_label", rows[1]["flags"])

    def test_unlabelled_numbers_and_short_hms_clock_stay_unresolved(self):
        text = "| H. M. S. | Reading | Value |\n|---|---|---|\n| 51 20 | unexplained | 17 30 |"
        r = self.module().stage_table(self.span(text))
        clock = next(c for c in r["cells"] if c["row_kind"] == "data" and c["column"] == 1)
        self.assertIsNone(clock["normalized"]["magnitude"])
        value = next(c for c in r["cells"] if c["row_kind"] == "data" and c["column"] == 3)
        self.assertIsNone(value["quantity_claim"])
        self.assertIsNone(value["normalized"]["magnitude"])

    def test_width_changes_are_retained_without_assigning_shifted_columns(self):
        text = "| H. M. | Declination of Mars |\n|---|---|\n| 8 20 | extra | 17 30 |"
        r = self.module().stage_table(self.span(text))
        last = r["cells"][-1]
        self.assertEqual(last["source_expression"], "17 30")
        self.assertIn("row_width_differs", last["flags"])
        self.assertIsNone(last["quantity_claim"])

    def test_bilingual_disagreement_and_comparative_model_roles_are_preserved(self):
        text = "| Reading | Observation | Copernicus |\n|---|---|---|\n| Declination of Mars | 17°23¾′ [17 23⁸⁄₄] | 17 25 |"
        r = self.module().stage_table(self.span(text))
        observed = next(c for c in r["cells"] if c["row_kind"] == "data" and c["column"] == 2)
        predicted = r["cells"][-1]
        self.assertIn("parallel_numeric_expressions_disagree", observed["flags"])
        self.assertIsNone(observed["normalized"]["magnitude"])
        self.assertEqual(predicted["role_claim"], "model_prediction")

    def test_ids_and_source_expressions_are_bound_without_using_benchmark(self):
        text = "| Reading | Value |\n|---|---|\n| Declination | 17 30 |"
        span = self.span(text)
        m = self.module()
        r = m.stage_table(span)
        self.assertIsNone(r["cells"][-1]["subject_claim"])
        self.assertIn("target_unresolved", r["cells"][-1]["flags"])
        self.assertEqual(r, m.stage_table(span))

    def test_explicit_other_planet_in_cell_cannot_silently_inherit_mars_target(self):
        text = "| Declination of Mars |\n|---|\n| ♀ 14 40 |"
        row = self.module().stage_table(self.span(text))["cells"][-1]
        self.assertIsNone(row["subject_claim"])
        self.assertIn("source_target_conflict", row["flags"])
        self.assertEqual(row["target_candidates"], ["Mars", "Venus"])

    def test_missing_numeric_placeholder_is_distinct_from_blank_cell(self):
        text = "| Declination of Mars |\n|---|\n| ? |\n| |"
        rows = self.module().stage_table(self.span(text))["cells"][-2:]
        self.assertEqual(rows[0]["normalized"]["status"], "incomplete")
        self.assertIsNone(rows[0]["normalized"]["magnitude"])
        self.assertIn("blank_source_cell", rows[1]["flags"])
        clock = "| H. M. |\n|---|\n| 10^h^ 47 2/[?]^m^ |"
        row = self.module().stage_table(self.span(clock))["cells"][-1]
        self.assertEqual(row["normalized"]["status"], "incomplete")
        self.assertIsNone(row["normalized"]["magnitude"])

    def test_explicit_quantity_in_cell_overrides_conflicting_column_label(self):
        text = "| Longitude |\n|---|\n| Latitude 2 26 B |"
        row = self.module().stage_table(self.span(text))["cells"][-1]
        self.assertEqual(row["quantity_claim"], "ecliptic_latitude")
        self.assertEqual(row["quantity_basis"], "cell_label")
        self.assertIn("cell_quantity_differs_from_header", row["flags"])

    def test_workspace_requires_current_source_and_keeps_raw_tables_private(self):
        m = self.module()
        text = "| Reading | Value |\n|---|---|\n| Altitude of Mars | 14 10 |"
        span = self.span(text)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            work = root / "mars"
            work.mkdir()
            source.mkdir()
            rel = "brahe/thesaurus_observationum_vol3/translation/brahe_thesaurus_observationum_vol3_prepub.md"
            path = source / rel
            path.parent.mkdir(parents=True)
            path.write_text(text)
            (work / "witnesses.json").write_text(
                json.dumps(
                    [dict(volume=12, private_source=rel, edition_sha256=span["edition_sha256"])]
                )
            )
            (work / "inventory_manifest.json").write_text(
                json.dumps(dict(source_hashes={rel: span["edition_sha256"]}))
            )
            (work / "inventory_spans.jsonl").write_text(json.dumps(span) + "\n")
            m.build_tables(source, work)
            public = json.loads((work / "public_table_staging_summary.json").read_text())
            self.assertEqual(public["table_spans"], 1)
            self.assertNotIn("source_expression", str(public))
            self.assertEqual(path.read_text(), text)
            path.write_text(text + "changed")
            with self.assertRaisesRegex(ValueError, "[Ff]ingerprint"):
                m.build_tables(source, work)


if __name__ == "__main__":
    unittest.main()
