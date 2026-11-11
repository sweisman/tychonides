"""Source-bound leading components must not become guessed numerical values."""

import copy
import hashlib
import unittest

from src.catalog import compile_catalogue
from src.public_assertions import public_assertion
from src.review_preparation import materialize_review


class TableCarryTests(unittest.TestCase):
    def fixture(self, leader="27"):
        text = (
            "Empty leading cells carry the figure above.\n"
            "| Alt. | Seconds | Thirds |\n"
            "|---|---|---|\n"
            f"| 0 | {leader} | 8 |\n"
            "| 5 | | 10 |\n"
            "| 10 | 28 | 0 |\n"
            "| 15 | | 6 |\n"
        )
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [
            dict(id=f"s{n}", volume=10, edition_sha256=sha, line_start=n, line_end=n)
            for n in range(1, 8)
        ]
        review = dict(
            id="explicit-carry",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=7,
            basis=dict(kind="final_edition_review", printed_page=47),
            contexts=[
                dict(
                    key="carry",
                    kind="source_observation_context",
                    lines=[1],
                    value=dict(
                        record_type="source_table_carry_rule",
                        line_start=4,
                        line_end=7,
                        source_expression="Empty leading cells carry the figure above.",
                    ),
                )
            ],
            cell_groups=[
                dict(
                    quantity="parallax_angle",
                    role="historical_input",
                    subject="Sun",
                    reference="Earth",
                    direction=None,
                    column=None,
                    flags=["not_an_additional_raw_reading"],
                    context_keys=["carry"],
                    unit_basis="The seconds/thirds columns and explicit carry instruction",
                    component_units=["arcsecond", "arcsexagesimal_third"],
                    source_columns=[2, 3],
                    line_range=[4, 7],
                    table_carry=dict(rule_key="carry", unit="arcsecond", column=2),
                )
            ],
        )
        return text, spans, review

    def test_explicit_carry_preserves_literal_and_changes_at_next_printed_component(self):
        text, spans, review = self.fixture()
        try:
            batch = materialize_review(review, text, spans)
        except ValueError as exc:
            self.fail(f"An explicit source carry rule should compile: {exc}")
        rows = sorted(
            compile_catalogue([batch], {10: text}, spans)["assertions"], key=lambda r: r["line"]
        )
        self.assertEqual(
            [r["normalized"]["magnitude"] for r in rows], ["407/15", "163/6", "28", "281/10"]
        )
        self.assertNotIn("27", rows[1]["source_expression"])
        public = public_assertion(rows[1])
        evidence = public["source_component_carry"]
        self.assertEqual(evidence["source_line"], 4)
        self.assertEqual(evidence["source_column"], 2)
        self.assertEqual(evidence["source_expression"], "27")
        self.assertIn(evidence["rule_context_id"], rows[1]["context_ids"])
        self.assertIn("rule_scope_id", evidence)
        self.assertEqual(evidence["rule_scope_id"], hashlib.sha256(b"explicit-carry").hexdigest())

    def test_compiler_recomputes_carried_component_instead_of_trusting_review(self):
        text, spans, review = self.fixture()
        batch = materialize_review(review, text, spans)
        target = next(r for r in batch["assertions"] if r["line"] == 5)
        target["components"]["arcsecond"] = "999"
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {10: text}, spans)

    def test_carry_requires_explicit_scoped_rule_and_the_first_physical_column(self):
        text, spans, review = self.fixture()
        for change in ("no_rule", "wrong_column", "outside_scope", "wrong_kind"):
            altered = copy.deepcopy(review)
            group = altered["cell_groups"][0]
            if change == "no_rule":
                del group["table_carry"]
            elif change == "wrong_column":
                group["table_carry"]["column"] = 3
            elif change == "outside_scope":
                altered["contexts"][0]["value"]["line_start"] = 5
            else:
                altered["contexts"][0]["value"]["record_type"] = "ordinary_comment"
            with self.subTest(change=change), self.assertRaises(ValueError):
                batch = materialize_review(altered, text, spans)
                compile_catalogue([batch], {10: text}, spans)

    def test_queried_leader_cannot_be_skipped_to_find_an_earlier_number(self):
        text, spans, review = self.fixture("27 [?]")
        with self.assertRaises(ValueError):
            batch = materialize_review(review, text, spans)
            compile_catalogue([batch], {10: text}, spans)

    def proportional_fixture(self, leader="27"):
        text, spans, review = self.fixture(leader)
        group = review["cell_groups"][0]
        group.update(
            quantity="proportional_minutes",
            subject="Mercury",
            reference=None,
            component_units=["proportional_minute", "proportional_second"],
            table_carry=dict(rule_key="carry", unit="proportional_minute", column=2),
            unit_basis="Whole/subplace native coefficient on an explicit60scale",
        )
        return text, spans, review

    def test_native_proportional_carry_retains_scale_and_rejects_tampering(self):
        text, spans, review = self.proportional_fixture()
        batch = materialize_review(review, text, spans)
        rows = sorted(
            compile_catalogue([batch], {10: text}, spans)["assertions"], key=lambda r: r["line"]
        )
        self.assertEqual(
            [r["normalized"]["magnitude"] for r in rows],
            ["407/900", "163/360", "7/15", "281/600"],
        )
        public = public_assertion(rows[1])
        self.assertEqual(public["normalized"]["unit"], "ratio")
        self.assertEqual(public["source_component_carry"]["unit"], "proportional_minute")
        altered = copy.deepcopy(batch)
        next(r for r in altered["assertions"] if r["line"] == 5)["components"][
            "proportional_minute"
        ] = "26"
        with self.assertRaisesRegex(ValueError, "Carried component differs"):
            compile_catalogue([altered], {10: text}, spans)
        for quantity, unit in (
            ("proportional_minutes", "degree"),
            ("calculation_angle", "proportional_minute"),
        ):
            altered = copy.deepcopy(review)
            altered["cell_groups"][0]["quantity"] = quantity
            altered["cell_groups"][0]["table_carry"]["unit"] = unit
            with self.subTest(quantity=quantity, unit=unit), self.assertRaises(ValueError):
                materialize_review(altered, text, spans)

    def test_annotated_carry_origin_uses_printed_value_and_blocks_queries(self):
        for native in (False, True):
            fixture = self.proportional_fixture if native else self.fixture
            text, spans, review = fixture("27 [recte: 29]")
            review["cell_groups"][0]["line_range"] = [5, 5]
            with self.subTest(native=native):
                batch = materialize_review(review, text, spans)
                row = compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                self.assertEqual(row["normalized"]["magnitude"], "163/360" if native else "163/6")
                self.assertEqual(
                    public_assertion(row)["source_component_carry"]["source_expression"], "27"
                )
            for leader in ("27 [?]", "27 [recte: 29 [?]]", "27 [?] [recte: 29]"):
                text, spans, review = fixture(leader)
                review["cell_groups"][0]["line_range"] = [5, 5]
                with self.subTest(native=native, leader=leader), self.assertRaises(ValueError):
                    materialize_review(review, text, spans)

    def test_missing_leading_component_remains_unresolved_without_changing_full_pairs(self):
        text = "| Arg. | G. M. |\n|---|---|\n| 0 | 0 59 |\n| 1 | 2 |\n| 2 | 1 2 |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [
            dict(id=f"p{n}", volume=10, edition_sha256=sha, line_start=n, line_end=n)
            for n in range(1, 6)
        ]
        review = dict(
            id="missing-degrees",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=5,
            basis=dict(kind="final_edition_review", printed_page=53),
            contexts=[
                dict(
                    key="table",
                    kind="source_observation_context",
                    lines=[1],
                    value=dict(interpretation="A bare minute lacks an established degree"),
                )
            ],
            cell_groups=[
                dict(
                    quantity="calculation_angle",
                    role="historical_input",
                    subject="Moon calculation",
                    reference=None,
                    direction=None,
                    column=2,
                    line_range=[3, 5],
                    flags=["not_an_additional_raw_reading"],
                    context_keys=["table"],
                    unit_basis="The header states G.M.; omitted degrees are not supplied",
                    component_units=["degree", "arcminute"],
                    incomplete_component_policy="unresolved",
                )
            ],
        )
        try:
            batch = materialize_review(review, text, spans)
        except ValueError as exc:
            self.fail(f"Partial notation should be preserved without a guessed degree: {exc}")
        rows = sorted(
            compile_catalogue([batch], {10: text}, spans)["assertions"], key=lambda r: r["line"]
        )
        self.assertEqual(rows[0]["normalized"]["magnitude"], "3540")
        self.assertEqual(rows[2]["normalized"]["magnitude"], "3720")
        partial = public_assertion(rows[1])
        self.assertEqual(rows[1]["source_expression"], "2")
        self.assertEqual(rows[1]["components"], {})
        self.assertIsNone(partial["normalized"]["magnitude"])
        self.assertIn("source_notation_unresolved", partial["flags"])
        for policy in (None, "assume_zero"):
            altered = copy.deepcopy(review)
            if policy is None:
                del altered["cell_groups"][0]["incomplete_component_policy"]
            else:
                altered["cell_groups"][0]["incomplete_component_policy"] = policy
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                materialize_review(altered, text, spans)
