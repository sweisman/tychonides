import hashlib
import unittest

from src.catalog import compile_catalogue


class SourceWordNumberTests(unittest.TestCase):
    def test_stated_hundreds_and_fraction_keep_complete_word_values(self):
        for expression, quantity, unit, value, expected in (
            ("three hundred", "source_scalar", "scalar", "300", "300"),
            ("four hundred", "source_scalar", "scalar", "400", "400"),
            ("six hundred", "source_scalar", "scalar", "600", "600"),
            ("ten thousand", "source_scalar", "scalar", "10000", "10000"),
            ("two thousand", "source_scalar", "scalar", "2000", "2000"),
            ("a million", "source_scalar", "scalar", "1000000", "1000000"),
            ("two million", "source_scalar", "scalar", "2000000", "2000000"),
            ("two hundred and sixty", "source_scalar", "scalar", "260", "260"),
            ("three hundred and sixty", "source_scalar", "scalar", "360", "360"),
            ("fifty thousand", "source_scalar", "scalar", "50000", "50000"),
            ("every other year", "source_scalar", "scalar", "2", "2"),
            ("a whole month", "source_scalar", "scalar", "1", "1"),
            ("twenty-fourth", "source_scalar", "scalar", "24", "24"),
            ("one degree and a quarter", "calculation_angle", "degree", "1 1/4", "4500"),
            ("three-and-a-half", "source_scalar", "scalar", "3 1/2", "7/2"),
            ("three quarters", "calculation_angle", "degree", "3/4", "2700"),
            ("three-quarters", "clock_elapsed_time", "hour", "3/4", "2700"),
            ("right angle", "calculation_angle", "degree", "90", "324000"),
            ("semicircle", "calculation_angle", "degree", "180", "648000"),
            ("eleven-twelfths", "calculation_angle", "degree", "11/12", "3300"),
            ("one degree less a twelfth", "calculation_angle", "degree", "11/12", "3300"),
            ("one degree and two fifths", "calculation_angle", "degree", "1 2/5", "5040"),
            ("a fifth", "calculation_angle", "degree", "1/5", "720"),
            ("a tenth", "calculation_angle", "degree", "1/10", "360"),
            ("half a quadrant", "altitude", "degree", "45", "162000"),
            ("a hundred and five", "source_scalar", "scalar", "105", "105"),
            ("ten and a half", "calculation_angle", "degree", "10 1/2", "37800"),
            ("a full year", "source_scalar", "scalar", "1", "1"),
            ("a full degree", "calculation_angle", "degree", "1", "3600"),
            ("1st", "recorded_clock", "hour", "1", "3600"),
            ("10th", "recorded_clock", "hour", "10", "36000"),
            ("23rd", "source_scalar", "scalar", "23", "23"),
            ("25th", "source_scalar", "scalar", "25", "25"),
            ("29th", "source_scalar", "scalar", "29", "29"),
            ("48th", "source_scalar", "scalar", "48", "48"),
            ("57th", "source_scalar", "scalar", "57", "57"),
            ("two ells with a half", "source_scalar", "scalar", "5/2", "5/2"),
            ("eightfold", "source_scalar", "scalar", "8", "8"),
            ("three and a half", "calculation_angle", "arcminute", "3 1/2", "210"),
            ("a third part of a quadrant", "calculation_angle", "degree", "30", "108000"),
        ):
            with self.subTest(expression=expression):
                text = "The source states " + expression + "."
                sha = hashlib.sha256(text.encode()).hexdigest()
                row = dict(
                    key="stated-value",
                    line=1,
                    span_id="s",
                    quantity=quantity,
                    role="historical_input",
                    subject="New Star calculation",
                    reference=None,
                    source_expression=expression,
                    components={unit: value},
                    source_word_numbers={expression: value},
                    unit_basis="Explicitly reviewed native count or angular fraction",
                )
                batch = dict(
                    id="review",
                    volume=10,
                    edition_sha256=sha,
                    line_start=1,
                    line_end=1,
                    interval_sha256=sha,
                    basis=dict(kind="source_review", printed_page=1),
                    assertions=[row],
                    span_decisions=[dict(span_id="s", decision="include", reason="Stated value")],
                )
                span = dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=1)
                out = compile_catalogue([batch], {10: text}, [span])["assertions"][0]
                self.assertEqual(out["normalized"]["magnitude"], expected)
                self.assertEqual(out["source_expression"], expression)
                row["source_word_numbers"] = {expression: "2" if value == "1" else "1"}
                with self.assertRaises(ValueError):
                    compile_catalogue([batch], {10: text}, [span])

    def test_minute_and_half_phrase_is_a_relative_interval_not_a_clock(self):
        text = "About a minute and a half before the observation."
        sha = hashlib.sha256(text.encode()).hexdigest()
        row = dict(
            key="interval",
            line=1,
            span_id="s",
            quantity="clock_elapsed_time",
            role="calibration",
            subject="bright star of Aries",
            reference=None,
            source_expression="a minute and a half",
            components={"minute": "1 1/2"},
            source_word_numbers={"a minute and a half": "1 1/2"},
            flags=["source_approximate", "not_an_observing_clock"],
            unit_basis="Explicit relative time interval",
        )
        batch = dict(
            id="review",
            volume=13,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=sha,
            basis=dict(kind="source_review", printed_page=112),
            assertions=[row],
            span_decisions=[dict(span_id="s", decision="include", reason="Relative interval")],
        )
        span = dict(id="s", volume=13, edition_sha256=sha, line_start=1, line_end=1)
        result = compile_catalogue([batch], {13: text}, [span])["assertions"][0]
        self.assertEqual(
            (result["normalized"]["magnitude"], result["normalized"]["unit"]),
            ("90", "second_of_time"),
        )
        self.assertIsNone(result["event_id"])
        row["source_word_numbers"] = {"a minute and a half": "1/2"}
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {13: text}, [span])

    def test_single_minute_in_an_instrument_claim_is_one_angular_minute(self):
        text = "It exceeds by almost a single minute."
        sha = hashlib.sha256(text.encode()).hexdigest()
        row = dict(
            key="excess",
            line=1,
            span_id="s",
            quantity="separation_correction",
            role="calibration",
            subject="Aldebaran",
            reference="bright star of Aries",
            source_expression="almost a single minute",
            components={"arcminute": "1"},
            source_word_numbers={"single": "1"},
            unit_basis="Angular instrument excess",
        )
        batch = dict(
            id="review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=sha,
            basis=dict(kind="source_review", printed_page=220),
            assertions=[row],
            span_decisions=[dict(span_id="s", decision="include", reason="Angular excess")],
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        result = compile_catalogue([batch], {12: text}, [span])["assertions"][0]
        self.assertEqual(
            (result["normalized"]["magnitude"], result["normalized"]["unit"]), ("60", "arcsecond")
        )
        row["source_word_numbers"] = {"single": "2"}
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {12: text}, [span])

    def test_a_spelled_instrument_excess_keeps_angular_minutes_and_requires_its_word_mapping(self):
        text = "The instrument gives an excess of about one minute."
        sha = hashlib.sha256(text.encode()).hexdigest()
        row = dict(
            key="excess",
            line=1,
            span_id="s",
            quantity="separation_correction",
            role="calibration",
            subject="Aldebaran",
            reference="bright star of Aries",
            source_expression="about one minute",
            components={"arcminute": "1"},
            source_word_numbers={"one": "1"},
            unit_basis="Angular instrument excess",
        )
        batch = dict(
            id="review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=sha,
            basis=dict(kind="source_review", printed_page=219),
            assertions=[row],
            span_decisions=[
                dict(span_id="s", decision="include", reason="Angular correction claim")
            ],
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        result = compile_catalogue([batch], {12: text}, [span])["assertions"][0]
        self.assertEqual(
            (result["normalized"]["magnitude"], result["normalized"]["unit"]), ("60", "arcsecond")
        )
        row.pop("source_word_numbers")
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {12: text}, [span])

    def test_spelled_clock_and_elapsed_units_require_checked_literal_word_values(self):
        text = "At the third hour, six minutes later, two hours."
        sha = hashlib.sha256(text.encode()).hexdigest()
        common = dict(
            line=1,
            span_id="s",
            subject="observing clock",
            reference=None,
            role="calibration",
            unit_basis="Explicit source word and time unit",
        )
        rows = [
            dict(
                common,
                key="clock",
                quantity="recorded_clock",
                source_expression="third hour",
                components={"hour": "3"},
                source_word_numbers={"third": "3"},
            ),
            dict(
                common,
                key="elapsed",
                quantity="clock_elapsed_time",
                source_expression="six minutes",
                components={"minute": "6"},
                source_word_numbers={"six": "6"},
            ),
            dict(
                common,
                key="two-hours",
                quantity="clock_elapsed_time",
                source_expression="two hours",
                components={"hour": "2"},
                source_word_numbers={"two": "2"},
            ),
        ]
        batch = dict(
            id="review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=sha,
            basis=dict(kind="source_review", printed_page=147),
            assertions=rows,
            span_decisions=[
                dict(span_id="s", decision="include", reason="Two explicit word numbers")
            ],
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        result = compile_catalogue([batch], {12: text}, [span])
        self.assertEqual(
            {r["key"]: r["normalized"]["magnitude"] for r in result["assertions"]},
            {"clock": "10800", "elapsed": "360", "two-hours": "7200"},
        )
        rows[0]["source_word_numbers"] = {"third": "4"}
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {12: text}, [span])
        rows[0]["source_word_numbers"] = {"six": "6"}
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {12: text}, [span])


if __name__ == "__main__":
    unittest.main()
