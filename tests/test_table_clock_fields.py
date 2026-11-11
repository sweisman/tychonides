"""Reviewed date/time cells retain complete native clocks and literal bounds."""

import copy
import hashlib
import unittest

from src.assembly import assemble
from src.catalog import compile_catalogue
from src.public_assertions import public_assertion
from src.review_preparation import materialize_review


class TableClockFieldsTests(unittest.TestCase):
    def fixture(self, values, quantity="recorded_clock", absent=()):
        text = "\n".join(f"| entry | {value} |" for value in values)
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [
            dict(id="clock-span", volume=10, edition_sha256=sha, line_start=1, line_end=len(values))
        ]
        review = dict(
            id="reviewed-table-clocks",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=len(values),
            basis=dict(kind="final_edition_review", printed_page=1),
            assertion_defaults=dict(
                subject="Mars",
                reference=None,
                direction=None,
                role="recorded_reading" if quantity == "recorded_clock" else "historical_input",
                flags=[] if quantity == "recorded_clock" else ["not_an_additional_raw_reading"],
                context_keys=["header"],
                unit_basis="Reviewed Month/Day/Hour/Minute column; no absolute date inferred.",
            ),
            contexts=[
                dict(
                    key="header",
                    kind="source_observation_context",
                    lines=[1],
                    value=dict(record_type="reviewed_time_column", units=["hour", "minute"]),
                )
            ],
            cell_groups=[
                dict(
                    line_range=[1, len(values)],
                    column=2,
                    quantity=quantity,
                    component_units=["hour", "minute"],
                    clock_fields=dict(separator="·", absent_values=list(absent)),
                    row_context=dict(key_prefix="native-time", columns=dict(native_date_clock=2)),
                )
            ],
        )
        return text, spans, review

    def compile(self, text, spans, review):
        materialized = materialize_review(review, text, spans)
        compiled = compile_catalogue([materialized], {10: text}, spans)
        assembly = assemble({10: text}, compiled["assertions"], [], [], [])
        self.assertTrue(
            all(r["anchor_status"] == "unique_source_interval" for r in assembly["items"])
        )
        for row in compiled["assertions"]:
            public_assertion(row)
            self.assertNotIn("clock_fields", row)
        return materialized, sorted(compiled["assertions"], key=lambda row: row["line"])

    def test_complete_suffixes_preserve_native_dates_without_consuming_the_day(self):
        values = ["Nou. 18 · 1 · 30", "8 · 30", "30 · 8 · 10", "Iunij 8 · 7 · 45"]
        text, spans, review = self.fixture(values)
        materialized, rows = self.compile(text, spans, review)
        self.assertEqual(
            [r["source_expression"] for r in rows], ["1 · 30", "8 · 30", "8 · 10", "7 · 45"]
        )
        self.assertEqual(
            [r["normalized"]["magnitude"] for r in rows], ["5400", "30600", "29400", "27900"]
        )
        contexts = [c for c in materialized["contexts"] if c["key"].startswith("native-time-")]
        self.assertEqual([c["value"]["native_date_clock"] for c in contexts], values)

    def test_repeated_suffix_is_bound_to_its_last_occurrence(self):
        text, spans, review = self.fixture(["1 · 1 · 1"])
        _, rows = self.compile(text, spans, review)
        self.assertEqual(rows[0]["char_start"], text.rindex("1 · 1"))
        self.assertEqual(rows[0]["normalized"]["magnitude"], "3660")

    def test_fractional_components_and_calculated_epochs_use_the_same_selector(self):
        for quantity in ("calculation_epoch", "annotated_time"):
            text, spans, review = self.fixture(["Dec. 17 · 8 · ½"], quantity)
            _, rows = self.compile(text, spans, review)
            self.assertEqual(rows[0]["quantity"], quantity)
            self.assertEqual(rows[0]["normalized"]["magnitude"], "28830")

    def test_only_explicit_absence_labels_are_omitted(self):
        text, spans, review = self.fixture(
            ["Oct. 20", "of the night", "0 · 40"], absent=["Oct. 20", "of the night"]
        )
        _, rows = self.compile(text, spans, review)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["normalized"]["magnitude"], "2400")
        for label in ["Oct. 21", "unknown", "Nou. 18 · 1 · 30 [?]", "18 · 1 · 30 · 4"]:
            text, spans, review = self.fixture([label], absent=["Oct. 20", "of the night"])
            with self.subTest(label=label), self.assertRaises(ValueError):
                materialize_review(review, text, spans)

    def test_angular_units_or_unretained_column_cannot_be_used_as_a_clock(self):
        for change in ["quantity", "units", "column"]:
            text, spans, review = self.fixture(["Nou. 18 · 1 · 30"])
            group = review["cell_groups"][0]
            if change == "quantity":
                group["quantity"] = "ecliptic_longitude"
            elif change == "units":
                group["component_units"] = ["degree", "arcminute"]
            else:
                group["row_context"]["columns"] = dict(label=1)
            with self.subTest(change=change), self.assertRaises(ValueError):
                materialize_review(review, text, spans)

    def test_a_numeric_clock_cannot_be_declared_absent(self):
        for value in ("1 · 30", "hour 13", "13h", "M. 30"):
            text, spans, review = self.fixture([value], absent=[value])
            with self.subTest(value=value), self.assertRaises(ValueError):
                materialize_review(review, text, spans)

    def test_an_anomalous_native_day_does_not_change_the_clock(self):
        text, spans, review = self.fixture(["Feb. 32 · 1 · 30"])
        materialized, rows = self.compile(text, spans, review)
        self.assertEqual(rows[0]["source_expression"], "1 · 30")
        self.assertEqual(rows[0]["normalized"]["magnitude"], "5400")
        context = next(c for c in materialized["contexts"] if c["key"] == "native-time-1")
        self.assertEqual(context["value"]["native_date_clock"], "Feb. 32 · 1 · 30")

    def test_unsupported_prefix_or_extra_manual_binding_is_rejected(self):
        for value in ["12° · 1 · 30", "1580 · 1 · 30", "Nou. 18 · 1 · 30"]:
            text, spans, review = self.fixture([value])
            if value.startswith("Nou"):
                review = copy.deepcopy(review)
                review["cell_groups"][0]["cells"] = [dict(line=1, char_start=0, char_end=1)]
                del review["cell_groups"][0]["line_range"]
            with self.subTest(value=value), self.assertRaises(ValueError):
                materialize_review(review, text, spans)
