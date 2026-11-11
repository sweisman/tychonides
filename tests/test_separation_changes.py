import copy
import hashlib
import unittest

from src.catalog import compile_catalogue
from src.public_checkpoint import public_assertion


class SeparationChangeTests(unittest.TestCase):
    def fixture(self):
        text = "Mars–left shoulder of Aquarius changed by about 5′\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="change-span", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        row = dict(
            key="change",
            line=1,
            span_id=span["id"],
            source_expression="about 5′",
            quantity="separation_difference",
            role="historical_input",
            subject="Mars",
            reference="left shoulder of Aquarius",
            components={"arcminute": "5"},
            unit_basis="Source angular-minute change, not rate or correction",
            flags=["source_approximate"],
        )
        batch = dict(
            id="change-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=292),
            span_decisions=[
                dict(span_id=span["id"], decision="include", reason="Change and endpoints reviewed")
            ],
            assertions=[row],
            events=[],
            contexts=[],
        )
        return text, [span], batch

    def test_change_is_an_unsigned_angle_with_its_two_endpoints_and_qualification(self):
        text, spans, batch = self.fixture()
        r = compile_catalogue([batch], {12: text}, spans)
        row = public_assertion(r["assertions"][0])
        self.assertEqual((row["subject"], row["reference"]), ("Mars", "left shoulder of Aquarius"))
        self.assertEqual(row["normalized"]["magnitude"], "300")
        self.assertEqual(row["normalized"]["unit"], "arcsecond")
        self.assertIsNone(row["normalized"]["signed_magnitude"])
        self.assertEqual(row["role"], "historical_input")
        self.assertIn("source_approximate", row["flags"])
        self.assertIsNone(row["event_id"])

    def test_missing_endpoint_self_separation_or_raw_reading_role_is_rejected(self):
        text, spans, batch = self.fixture()
        for change in ({"reference": None}, {"reference": "Mars"}, {"role": "recorded_reading"}):
            bad = copy.deepcopy(batch)
            bad["assertions"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                r = compile_catalogue([bad], {12: text}, spans)
                public_assertion(r["assertions"][0])
