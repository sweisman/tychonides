import hashlib
import unittest

from src.catalog import compile_catalogue, normalize_quantity


class MeasurementSemanticsTests(unittest.TestCase):
    def fixture(self, output="24 57¾"):
        text = f"49 2½ | 24 4¾ | {output}\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="span", volume=11, edition_sha256=sha, line_start=1, line_end=1)
        assertions = []
        for key, expression, components in [
            ("mars", "49 2½", dict(degree="49", arcminute="2½")),
            ("arcturus", "24 4¾", dict(degree="24", arcminute="4¾")),
            ("difference", output, dict(zip(("degree", "arcminute"), output.split(), strict=True))),
        ]:
            assertions.append(
                dict(
                    key=key,
                    line=1,
                    span_id="span",
                    source_expression=expression,
                    quantity="right_ascension_difference"
                    if key == "difference"
                    else "meridian_distance",
                    role="reduction" if key == "difference" else "recorded_reading",
                    subject="Mars",
                    components=components,
                    unit_basis="Reviewed angular columns",
                )
            )
        batch = dict(
            id="review",
            volume=11,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.strip().encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=178),
            span_decisions=[dict(span_id="span", decision="include", reason="Reviewed")],
            assertions=assertions,
            derivations=[
                dict(
                    key="difference",
                    input_keys=["mars", "arcturus"],
                    output_key="difference",
                    operation="difference",
                )
            ],
        )
        return text, span, batch

    def test_same_side_meridian_difference_is_checked_as_subtraction(self):
        text, span, batch = self.fixture()
        result = compile_catalogue([batch], {11: text}, [span])
        self.assertTrue(result["derivations"][0]["arithmetic_agrees"])
        self.assertEqual(result["derivations"][0]["computed_magnitude"], "89865")

    def test_failed_difference_preserves_source_output(self):
        text, span, batch = self.fixture("24 57½")
        result = compile_catalogue([batch], {11: text}, [span])
        self.assertFalse(result["derivations"][0]["arithmetic_agrees"])
        self.assertEqual(
            next(r for r in result["assertions"] if r["key"] == "difference")["normalized"][
                "magnitude"
            ],
            "89850",
        )
        batch["derivations"][0]["input_keys"] = ["mars"]
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {11: text}, [span])

    def test_elapsed_minutes_are_not_a_clock_epoch(self):
        result = normalize_quantity(
            dict(quantity="clock_elapsed_time", components=dict(minute="3½"))
        )
        self.assertEqual(result["magnitude"], "210")
        self.assertEqual(result["unit"], "second_of_time")
        text, span, batch = self.fixture()
        batch["assertions"][0]["quantity"] = "clock_elapsed_time"
        batch["assertions"][0]["components"] = dict(hour="49", minute="2½")
        batch["events"] = [dict(key="event", line=1, clock_key="mars")]
        with self.assertRaisesRegex(ValueError, "clock"):
            compile_catalogue([batch], {11: text}, [span])
