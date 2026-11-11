import hashlib
import unittest

from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion


class CorrectionRatioTests(unittest.TestCase):
    def row(self):
        return dict(
            id="assertion-v12-" + "c" * 20,
            volume=12,
            printed_page=155,
            quantity="correction_ratio",
            role="historical_input",
            subject="Venus",
            reference="Mars",
            components={"ratio": "1/2"},
            correction_ratio_kind="separation_to_declination_refraction",
        )

    def test_half_is_dimensionless_and_retains_the_correction_relationship(self):
        row = self.row()
        row["normalized"] = normalize_quantity(row)
        self.assertEqual(row["normalized"]["status"], "exact")
        self.assertEqual(row["normalized"]["unit"], "ratio")
        self.assertEqual(row["normalized"]["magnitude"], "1/2")
        self.assertIsNone(row["normalized"]["magnitude_degrees"])
        out = public_assertion(row)
        self.assertEqual(out.get("correction_ratio_kind"), "separation_to_declination_refraction")
        self.assertEqual(out["normalized"]["least_component_unit"], "ratio")

    def test_ratio_cannot_be_an_angle_or_an_unreviewed_relationship(self):
        row = self.row()
        row["direction"] = "south"
        with self.assertRaises(ValueError):
            normalize_quantity(row)
        row = self.row()
        row["components"]["degree"] = "1"
        with self.assertRaises(ValueError):
            normalize_quantity(row)
        row = self.row()
        row["normalized"] = normalize_quantity(row)
        for update in [
            dict(correction_ratio_kind="private note"),
            dict(correction_ratio_kind=None),
            dict(role="recorded_coordinate"),
            dict(reference=None),
        ]:
            with self.subTest(update=update), self.assertRaises(ValueError):
                public_assertion({**row, **update})

    def test_source_word_half_requires_a_checked_literal_mapping(self):
        text = "Use half the declination correction."
        sha = hashlib.sha256(text.encode()).hexdigest()
        assertion = {
            **self.row(),
            "key": "ratio",
            "line": 1,
            "span_id": "s",
            "source_expression": "half",
            "unit_basis": "Source states a ratio, not an angle.",
            "source_word_numbers": {"half": "1/2"},
        }
        for key in ("id", "volume", "printed_page"):
            assertion.pop(key)
        batch = dict(
            id="review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=sha,
            basis=dict(kind="source_review", printed_page=155),
            assertions=[assertion],
            span_decisions=[dict(span_id="s", decision="include", reason="Printed half rule")],
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        compiled = compile_catalogue([batch], {12: text}, [span])["assertions"][0]
        self.assertEqual(compiled["source_expression"], "half")
        self.assertEqual(compiled["normalized"]["magnitude"], "1/2")
        assertion["source_word_numbers"] = {}
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {12: text}, [span])
