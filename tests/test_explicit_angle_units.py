import hashlib
import unittest

from src.catalog import compile_catalogue


class ExplicitAngleUnitTests(unittest.TestCase):
    def test_omitted_degree_and_approximate_whole_hour_keep_their_limits(self):
        cases = [
            (
                "11⅚′",
                dict(
                    quantity="angular_separation",
                    reference="Sun",
                    components={"arcminute": "11 5/6"},
                    incomplete=True,
                ),
                "incomplete",
                None,
            ),
            (
                "whole hour",
                dict(
                    quantity="clock_elapsed_time",
                    components={"hour": "1"},
                    source_word_numbers={"whole": "1"},
                    flags=["source_approximate"],
                ),
                "exact",
                "3600",
            ),
        ]
        for text, fields, status, magnitude in cases:
            with self.subTest(text=text):
                sha = hashlib.sha256(text.encode()).hexdigest()
                assertion = dict(
                    key="value",
                    line=1,
                    span_id="s",
                    source_expression=text,
                    subject="Mars",
                    role="recorded_reading",
                    unit_basis="Printed unit; absent degree not supplied",
                    **fields,
                )
                batch = dict(
                    id="review",
                    volume=12,
                    edition_sha256=sha,
                    line_start=1,
                    line_end=1,
                    interval_sha256=sha,
                    basis=dict(kind="source_review", printed_page=148),
                    assertions=[assertion],
                    span_decisions=[
                        dict(span_id="s", decision="include", reason="Explicit source limit")
                    ],
                )
                span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
                row = compile_catalogue([batch], {12: text}, [span])["assertions"][0]
                self.assertEqual(row["normalized"]["status"], status)
                self.assertEqual(row["normalized"]["magnitude"], magnitude)
                self.assertEqual(row["components"], fields["components"])

    def test_literal_arcminute_cannot_be_reviewed_as_degree(self):
        text = "3′"
        sha = hashlib.sha256(text.encode()).hexdigest()
        assertion = dict(
            key="correction",
            line=1,
            span_id="s",
            source_expression=text,
            quantity="separation_correction",
            subject="Mars",
            role="historical_correction",
            unit_basis="Explicit prime",
            components={"arcminute": "3"},
        )
        batch = dict(
            id="review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=sha,
            basis=dict(kind="source_review", printed_page=148),
            assertions=[assertion],
            span_decisions=[dict(span_id="s", decision="include", reason="Explicit angular unit")],
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        self.assertEqual(
            compile_catalogue([batch], {12: text}, [span])["assertions"][0]["normalized"][
                "magnitude"
            ],
            "180",
        )
        assertion["components"] = {"degree": "3"}
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {12: text}, [span])
