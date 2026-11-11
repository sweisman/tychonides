"""Source labels, rather than measured angles, bind table endpoints and roles."""

import copy
import hashlib
import unittest

from src.assembly import assemble
from src.catalog import compile_catalogue
from src.public_assertions import public_assertion
from src.review_preparation import materialize_review


class TableRelationshipsTests(unittest.TestCase):
    def fixture(self):
        text = (
            "| A to B | *Tycho* | 10 | 30 | 0 |\n"
            "| | *&* | 10 | 31 | 0 |\n"
            "| A to C | *ex Tych. da.* | 11 | 0 | |\n"
        )
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=3)]
        review = dict(
            id="reviewed-table-relationships",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=3,
            basis=dict(kind="final_edition_review", printed_page=1),
            contexts=[
                dict(
                    key="tycho",
                    kind="source_observation_context",
                    lines=[1],
                    value=dict(authority="Tycho as quoted"),
                ),
                dict(
                    key="tycho-da",
                    kind="source_observation_context",
                    lines=[3],
                    value=dict(authority="Computed from Tycho's declination and RA difference"),
                ),
            ],
            assertion_defaults=dict(
                quantity="angular_separation",
                subject=None,
                reference=None,
                direction=None,
                column=None,
                role=None,
                flags=["not_an_additional_raw_reading"],
                source_columns=[3, 4, 5],
                component_units=["degree", "arcminute", "arcsecond"],
                incomplete_component_policy="unresolved",
                unit_basis="Reviewed physical G/M/S columns; endpoints and authorities by labels.",
                row_context=dict(key_prefix="distance-row", columns=dict(pair=1, authority=2)),
            ),
            table_authorities={
                "stellar": dict(
                    column=2,
                    repeat=["&"],
                    values={
                        "Tycho": dict(role="recorded_reading", context_keys=["tycho"]),
                        "ex Tych. da.": dict(
                            role="calculation_intermediate", context_keys=["tycho-da"]
                        ),
                    },
                ),
            },
            table_relationship_rules={
                "pairs": dict(
                    label_column=1,
                    authority_policy="stellar",
                    context_prefix="pair",
                    pairs={
                        "A to B": dict(subject="Aldebaran", reference="Regulus"),
                        "A to C": dict(subject="Aldebaran", reference="Spica"),
                    },
                ),
            },
            cell_groups=[dict(line_range=[1, 3], table_relationships="pairs")],
        )
        return text, spans, review

    def compile(self, text, spans, review):
        materialized = materialize_review(review, text, spans)
        rows = compile_catalogue([materialized], {10: text}, spans)["assertions"]
        return materialized, sorted(rows, key=lambda row: row["line"])

    def test_labels_bind_repeated_pairs_and_separate_calculated_values(self):
        text, spans, review = self.fixture()
        original = copy.deepcopy(review)
        materialized, rows = self.compile(text, spans, review)
        self.assertEqual(
            [(r["subject"], r["reference"], r["role"]) for r in rows],
            [
                ("Aldebaran", "Regulus", "recorded_reading"),
                ("Aldebaran", "Regulus", "recorded_reading"),
                ("Aldebaran", "Spica", "calculation_intermediate"),
            ],
        )
        self.assertEqual(rows[0]["normalized"]["magnitude"], "37800")
        self.assertEqual(rows[1]["normalized"]["magnitude"], "37860")
        self.assertIsNone(rows[2]["normalized"]["magnitude"])
        self.assertEqual(rows[2]["components"], {})
        self.assertEqual(review, original)
        for row in rows:
            public_assertion(row)
            self.assertNotIn("table_relationships", row)
        self.assertTrue(
            all(
                r["anchor_status"] == "unique_source_interval"
                for r in assemble({10: text}, rows, [], [], [])["items"]
            )
        )
        contexts = {c["key"]: c for c in materialized["contexts"]}
        self.assertEqual(contexts["pair-2"]["lines"], [1, 2])
        self.assertEqual(contexts["pair-2"]["value"]["authority_as_printed"], "*&*")
        self.assertEqual(contexts["pair-2"]["value"]["authority_basis_label"], "Tycho")

    def test_values_cannot_choose_the_endpoint_pair(self):
        text, spans, review = self.fixture()
        text = text.replace("10 | 30", "99 | 30")
        sha = hashlib.sha256(text.encode()).hexdigest()
        review["edition_sha256"] = spans[0]["edition_sha256"] = sha
        _, rows = self.compile(text, spans, review)
        self.assertEqual((rows[0]["subject"], rows[0]["reference"]), ("Aldebaran", "Regulus"))
        self.assertEqual(rows[0]["normalized"]["magnitude"], "358200")

    def test_unknown_labels_and_conflicting_explicit_fields_fail(self):
        for alteration in ("pair", "authority", "initial_blank", "subject", "role", "evidence"):
            text, spans, review = self.fixture()
            if alteration == "pair":
                del review["table_relationship_rules"]["pairs"]["pairs"]["A to B"]
            elif alteration == "authority":
                del review["table_authorities"]["stellar"]["values"]["Tycho"]
            elif alteration == "initial_blank":
                text = text.replace("A to B", "", 1)
            elif alteration == "subject":
                review["assertion_defaults"]["subject"] = "Mars"
            elif alteration == "role":
                review["assertion_defaults"]["role"] = "recorded_reading"
            else:
                review["assertion_defaults"]["row_context"]["columns"] = dict(pair=1)
            sha = hashlib.sha256(text.encode()).hexdigest()
            review["edition_sha256"] = spans[0]["edition_sha256"] = sha
            with self.subTest(alteration=alteration), self.assertRaises(ValueError):
                self.compile(text, spans, review)

    def test_source_authority_can_select_an_adopted_value(self):
        text, spans, review = self.fixture()
        review["table_authorities"]["stellar"]["values"]["Tycho"]["role"] = "adopted_value"
        _, rows = self.compile(text, spans, review)
        self.assertEqual(rows[0]["role"], "adopted_value")
        public_assertion(rows[0])

    def test_inheritance_cannot_cross_a_new_source_heading(self):
        text, spans, review = self.fixture()
        text = text.replace("\n", "\n## New source block\n", 1)
        review["line_end"] = spans[0]["line_end"] = 4
        review["cell_groups"] = [
            dict(line_range=[1, 1], table_relationships="pairs"),
            dict(line_range=[3, 4], table_relationships="pairs"),
        ]
        sha = hashlib.sha256(text.encode()).hexdigest()
        review["edition_sha256"] = spans[0]["edition_sha256"] = sha
        with self.assertRaises(ValueError):
            self.compile(text, spans, review)

    def test_explicit_pair_and_authority_can_restart_after_a_heading(self):
        text, spans, review = self.fixture()
        text = text.replace("| A to C", "## Continued table\n| A to C")
        review["line_end"] = spans[0]["line_end"] = 4
        review["contexts"][1]["lines"] = [4]
        review["cell_groups"] = [
            dict(line_range=[1, 2], table_relationships="pairs"),
            dict(line_range=[4, 4], table_relationships="pairs"),
        ]
        sha = hashlib.sha256(text.encode()).hexdigest()
        review["edition_sha256"] = spans[0]["edition_sha256"] = sha
        materialized, rows = self.compile(text, spans, review)
        self.assertEqual(rows[-1]["reference"], "Spica")
        context = next(c for c in materialized["contexts"] if c["key"] == "pair-4")
        self.assertEqual(context["lines"], [4])

    def test_fixed_principal_star_retains_literal_reference_labels(self):
        text, spans, review = self.fixture()
        review["table_relationship_rules"]["pairs"].pop("pairs")
        review["table_relationship_rules"]["pairs"].update(
            subject="Aldebaran", reference_labels={"A to B": "Regulus", "A to C": "Spica"}
        )
        _, rows = self.compile(text, spans, review)
        self.assertEqual([r["reference"] for r in rows], ["Regulus", "Regulus", "Spica"])

    def test_literal_reference_mode_retains_qualification_and_numbered_names(self):
        text, spans, review = self.fixture()
        text = text.replace("A to B", "1 Cassiopeae [uncertain]").replace(
            "A to C", "11 & 12 Cassiopeae"
        )
        rule = review["table_relationship_rules"]["pairs"]
        rule.pop("pairs")
        rule.update(subject="Aldebaran", literal_references=True)
        sha = hashlib.sha256(text.encode()).hexdigest()
        review["edition_sha256"] = spans[0]["edition_sha256"] = sha
        _, rows = self.compile(text, spans, review)
        self.assertEqual(
            [r["reference"] for r in rows],
            ["1 Cassiopeae [uncertain]", "1 Cassiopeae [uncertain]", "11 & 12 Cassiopeae"],
        )

    def test_heading_authority_applies_without_an_observer_column(self):
        _, spans, review = self.fixture()
        text = (
            "Pétau computed distances from Tycho's coordinates.\n"
            "| A to B | 10 | 30 | 0 |\n"
            "| | 10 | 31 | 0 |\n"
            "| A to C | 11 | 0 | 0 |\n"
        )
        sha = hashlib.sha256(text.encode()).hexdigest()
        review["edition_sha256"] = spans[0]["edition_sha256"] = sha
        review["line_end"] = spans[0]["line_end"] = 4
        review["contexts"] = [review["contexts"][1]]
        review["contexts"][0]["lines"] = [1]
        review["assertion_defaults"]["source_columns"] = [2, 3, 4]
        review["cell_groups"][0]["line_range"] = [2, 4]
        review["table_authorities"]["stellar"] = dict(
            column=None,
            repeat=[],
            values={"": dict(role="calculation_intermediate", context_keys=["tycho-da"])},
        )
        review["assertion_defaults"]["row_context"]["columns"] = dict(pair=1)
        materialized, rows = self.compile(text, spans, review)
        self.assertEqual([r["role"] for r in rows], ["calculation_intermediate"] * 3)
        for row in rows:
            self.assertEqual(row["subject"], "Aldebaran")
            public_assertion(row)
        context = next(c for c in materialized["contexts"] if c["key"] == "pair-3")
        self.assertIsNone(context["value"]["authority_as_printed"])
        self.assertIsNone(context["value"]["authority_basis_label"])
        self.assertFalse(context["value"]["authority_inherited"])
        self.assertEqual(context["lines"], [2, 3])
        for alteration in ("repeat", "extra_value", "missing_context"):
            invalid = copy.deepcopy(review)
            policy = invalid["table_authorities"]["stellar"]
            if alteration == "repeat":
                policy["repeat"] = ["&"]
            elif alteration == "extra_value":
                policy["values"]["Tycho"] = policy["values"][""]
            else:
                policy["values"][""]["context_keys"] = []
            with self.subTest(alteration=alteration), self.assertRaises(ValueError):
                self.compile(text, spans, invalid)


if __name__ == "__main__":
    unittest.main()
