import copy
import hashlib
import unittest

from src.catalog import compile_catalogue
from src.public_checkpoint import public_assertion


class CompletedHourClaimTests(unittest.TestCase):
    def fixture(self):
        text = "For the completed 12th equinoctial hour.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        row = dict(
            key="epoch",
            line=1,
            span_id="s",
            source_expression="12th equinoctial hour",
            quantity="calculation_epoch",
            role="calculation_epoch",
            subject="calculation epoch",
            reference=None,
            direction=None,
            components={"hour": "12"},
            unit_basis="Source equinoctial hour; completed-hour interpretation unresolved",
            flags=["absolute_time_unestablished", "source_completed_hour_uninterpreted"],
        )
        batch = dict(
            id="completed",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=279),
            span_decisions=[
                dict(span_id="s", decision="include", reason="Completed-hour wording preserved")
            ],
            assertions=[row],
        )
        return compile_catalogue([batch], {12: text}, [span])["assertions"][0]

    def test_completed_hour_keeps_source_component_without_becoming_an_observing_clock(self):
        row = self.fixture()
        out = public_assertion(row)
        self.assertEqual(out["quantity"], "calculation_epoch")
        self.assertEqual(out["normalized"]["magnitude"], "43200")
        self.assertEqual(out["normalized"]["least_component_unit"], "hour")
        self.assertIn("source_completed_hour_uninterpreted", out["flags"])
        self.assertIsNone(out["event_id"])

    def test_completed_hour_qualification_cannot_be_applied_to_angles_or_raw_clocks(self):
        row = self.fixture()
        for quantity, role in [
            ("altitude", "historical_input"),
            ("recorded_clock", "recorded_clock"),
        ]:
            bad = copy.deepcopy(row)
            bad.update(quantity=quantity, role=role)
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                public_assertion(bad)
