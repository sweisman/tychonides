import hashlib
import unittest

from src.catalog import compile_catalogue


class ReviewPageSegmentsTests(unittest.TestCase):
    def test_cross_page_paragraph_keeps_each_assertions_physical_page(self):
        text = "3′\n4′"
        sha = hashlib.sha256(text.encode()).hexdigest()
        assertions = [
            dict(
                key=str(line),
                line=line,
                span_id="s",
                source_expression=expr,
                quantity="separation_correction",
                subject="Mars",
                role="historical_correction",
                unit_basis="Explicit arcminutes",
                components={"arcminute": value},
            )
            for line, expr, value in [(1, "3′", "3"), (2, "4′", "4")]
        ]
        segments = [
            dict(line_start=1, line_end=1, printed_page=148, pdf_page=162, witness_sha256="a" * 64),
            dict(line_start=2, line_end=2, printed_page=149, pdf_page=163, witness_sha256="b" * 64),
        ]
        batch = dict(
            id="cross-page-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            interval_sha256=sha,
            basis=dict(kind="scan_review", printed_page=149, page_segments=segments),
            assertions=assertions,
            span_decisions=[
                dict(span_id="s", decision="include", reason="Both native pages inspected")
            ],
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=2)
        rows = compile_catalogue([batch], {12: text}, [span])["assertions"]
        self.assertEqual({r["line"]: r["printed_page"] for r in rows}, {1: 148, 2: 149})
        for invalid in [
            segments[:1],
            [dict(segments[0], line_end=2), segments[1]],
            [dict(segments[0], printed_page=True), segments[1]],
            [dict(segments[0], witness_sha256="missing"), segments[1]],
        ]:
            batch["basis"]["page_segments"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                compile_catalogue([batch], {12: text}, [span])
