import hashlib
import unittest

from src.catalog import compile_catalogue
from src.public_checkpoint import public_assertion


class SourceClockCorrectionTests(unittest.TestCase):
    def test_unresolved_pair_does_not_select_a_preferred_event_clock(self):
        text = "9h36m; 9h40m"
        sha = hashlib.sha256(text.encode()).hexdigest()
        common = dict(
            line=1,
            span_id="s",
            quantity="recorded_clock",
            subject="observing clock",
            reference=None,
            role="recorded_clock",
            unit_basis="Source clock pair",
            event_key="pointing",
            flags=["clock_association_unresolved"],
        )
        assertions = [
            dict(
                common,
                key="first",
                source_expression="9h36m",
                components={"hour": "9", "minute": "36"},
            ),
            dict(
                common,
                key="second",
                source_expression="9h40m",
                components={"hour": "9", "minute": "40"},
            ),
        ]
        batch = dict(
            id="pair-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=sha,
            basis=dict(kind="scan_review", printed_page=144),
            span_decisions=[
                dict(span_id="s", decision="include", reason="Unlabelled pair retained")
            ],
            assertions=assertions,
            events=[dict(key="pointing", line=1, clock_key=None)],
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        result = compile_catalogue([batch], {12: text}, [span])
        self.assertIsNone(result["events"][0]["clock_assertion_id"])
        self.assertCountEqual(
            [r["normalized"]["magnitude"] for r in result["assertions"]], ["34560", "34800"]
        )
        batch["events"][0]["clock_key"] = "first"
        with self.assertRaisesRegex(ValueError, "Unresolved clock"):
            compile_catalogue([batch], {12: text}, [span])

    def test_disputed_endpoint_preserves_the_printed_editorial_alternative(self):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=139,
            quantity="angular_separation",
            role="recorded_reading",
            subject="Mars",
            reference="left knee of Ophiuchus",
            editorial_reference_alternative="southern scale-pan of Libra",
            flags=["source_endpoint_editorially_disputed"],
            normalized=dict(
                status="exact",
                magnitude="101490",
                unit="arcsecond",
                magnitude_degrees="3383/120",
                signed_magnitude=None,
                least_component_unit="arcminute",
            ),
        )
        result = public_assertion(row)
        self.assertEqual(result["reference"], "left knee of Ophiuchus")
        self.assertEqual(result["editorial_reference_alternative"], "southern scale-pan of Libra")
        row["editorial_reference_alternative"] = "private unchecked endpoint"
        with self.assertRaises(ValueError):
            public_assertion(row)

    def test_minute_only_correction_keeps_hour_absent_and_original_event_clock(self):
        text = "Clock 1h41⅙m; corrected 56¾m"
        sha = hashlib.sha256(text.encode()).hexdigest()
        common = dict(
            line=1,
            span_id="s",
            quantity="recorded_clock",
            subject="observing clock",
            reference=None,
            unit_basis="Source clock and correction labels",
        )
        raw = dict(
            common,
            key="raw",
            role="recorded_clock",
            source_expression="1h41⅙m",
            components={"hour": "1", "minute": "41⅙"},
            event_key="pointing",
        )
        corrected = dict(
            common,
            key="correction",
            role="printed_correction",
            source_expression="56¾m",
            components={"minute": "56¾"},
            variant_of_key="raw",
            flags=["clock_hour_unstated"],
        )
        batch = dict(
            id="review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=sha,
            basis=dict(kind="scan_review", printed_page=139),
            span_decisions=[
                dict(span_id="s", decision="include", reason="Both source clock forms checked")
            ],
            assertions=[raw, corrected],
            events=[dict(key="pointing", line=1, clock_key="raw")],
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        result = compile_catalogue([batch], {12: text}, [span])
        original, variant = result["assertions"]
        self.assertEqual(original["normalized"]["magnitude"], "6070")
        self.assertEqual(variant["normalized"]["magnitude"], "3405")
        self.assertNotIn("hour", variant["components"])
        self.assertEqual(variant["variant_of_id"], original["id"])
        self.assertEqual(result["events"][0]["clock_assertion_id"], original["id"])
