import copy
import hashlib
import unittest

from src.catalog import compile_catalogue
from src.review_preparation import materialize_review


class TableItemTests(unittest.TestCase):
    def fixture(self, text=None):
        text = text or (
            "| G. | M. | Reference |\n"
            "|---|---|---|\n"
            "| 18<br>18 | 30½<br>5 | A<br>B |\n"
            "| 18<br>18 | 40<br>45 | A<br>B |\n"
        )
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [
            dict(id=f"s{line}", volume=10, edition_sha256=sha, line_start=line, line_end=line)
            for line in range(1, len(text.splitlines()) + 1)
        ]
        recipe = dict(
            id="parallel-components",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=len(text.splitlines()),
            basis=dict(kind="final_edition_review", printed_page=1),
            assertion_defaults=dict(
                subject="Saturn",
                reference=None,
                direction=None,
                column=None,
                role="recorded_reading",
                flags=[],
                context_keys=[],
                unit_basis="Reviewed parallel degree/minute and reference lists",
            ),
            cell_groups=[
                dict(
                    quantity="angular_separation",
                    source_columns=[1, 2],
                    component_units=["degree", "arcminute"],
                    table_items=dict(
                        indices=[0, 1],
                        label_column=3,
                        reference_labels={"A": "Regulus", "B": "Spica"},
                    ),
                    line_range=[3, len(text.splitlines())],
                )
            ],
        )
        return text, spans, recipe

    def test_parallel_items_preserve_fractions_references_and_distinct_equal_literals(self):
        text, spans, recipe = self.fixture()
        before = copy.deepcopy(recipe)
        batch = materialize_review(recipe, text, spans)
        rows = compile_catalogue([batch], {10: text}, spans)["assertions"]
        rows.sort(key=lambda row: (row["line"], row["char_start"]))
        self.assertEqual(
            [row["normalized"]["magnitude"] for row in rows],
            ["66630", "65100", "67200", "67500"],
        )
        self.assertEqual([row["reference"] for row in rows], ["Regulus", "Spica"] * 2)
        self.assertEqual(
            [
                [fragment["source_expression"] for fragment in row["source_fragments"]]
                for row in rows
            ],
            [["18", "30½"], ["18", "5"], ["18", "40"], ["18", "45"]],
        )
        self.assertNotEqual(rows[0]["char_start"], rows[1]["char_start"])
        self.assertEqual(len({row["id"] for row in rows}), 4)
        self.assertEqual(recipe, before)

    def test_parallel_items_reject_misaligned_missing_or_unidentified_entries(self):
        for row in (
            "| 18<br>18 | 30<br>5<br>7 | A<br>B |",
            "| 18<br>18 | 30<br>5 | A |",
            "| 18<br>18 | 30<br> | A<br>B |",
            "| 18<br>18 | 30<br>5 | A<br>unreviewed |",
        ):
            with self.subTest(row=row):
                text, spans, recipe = self.fixture("| G. | M. | Reference |\n|---|---|---|\n" + row)
                with self.assertRaises(ValueError):
                    materialize_review(recipe, text, spans)

    def test_parallel_item_selection_rejects_duplicate_negative_and_missing_indices(self):
        for indices in ([0, 0], [-1], [2], [True], []):
            with self.subTest(indices=indices):
                text, spans, recipe = self.fixture()
                recipe["cell_groups"][0]["table_items"]["indices"] = indices
                with self.assertRaises(ValueError):
                    materialize_review(recipe, text, spans)

    def test_parallel_items_keep_explicit_unit_marks_subject_to_compiler_checks(self):
        text, _, _ = self.fixture()
        text = text.replace("18<br>18", "18°<br>18°").replace("30½<br>5", "30½′<br>5′")
        text = text.replace("40<br>45", "40′<br>45′")
        text, spans, recipe = self.fixture(text)
        batch = materialize_review(recipe, text, spans)
        rows = compile_catalogue([batch], {10: text}, spans)["assertions"]
        rows.sort(key=lambda row: (row["line"], row["char_start"]))
        self.assertEqual(rows[0]["normalized"]["magnitude"], "66630")
        recipe["cell_groups"][0]["component_units"] = ["degree", "arcsecond"]
        changed = materialize_review(recipe, text, spans)
        with self.assertRaises(ValueError):
            compile_catalogue([changed], {10: text}, spans)
