import hashlib
import unittest
from src.catalog import compile_catalogue
from src.public_checkpoint import public_assertion


class SourcePerigeeAngleTests(unittest.TestCase):
    def test_approximate_source_angle_from_perigee_does_not_become_orbital_longitude(self):
        text = "Mars was about 26° from the perigee of the annual orb.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="perigee-span", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        row = dict(
            key="angle",
            line=1,
            span_id=span["id"],
            source_expression="about 26°",
            quantity="calculation_angle",
            role="historical_input",
            subject="Mars",
            reference="perigee of annual orb",
            direction=None,
            components={"degree": "26"},
            flags=[
                "source_approximate",
                "not_an_additional_raw_reading",
                "geometry_interpretation_unestablished",
            ],
            unit_basis="Source degrees; annual-orb geometry not reconstructed",
        )
        batch = dict(
            id="perigee-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=293),
            span_decisions=[
                dict(span_id=span["id"], decision="include", reason="Source historical geometry")
            ],
            assertions=[row],
            contexts=[],
            events=[],
        )
        out = public_assertion(compile_catalogue([batch], {12: text}, [span])["assertions"][0])
        self.assertEqual(
            (out["quantity"], out["role"], out["reference"]),
            ("calculation_angle", "historical_input", "perigee of annual orb"),
        )
        self.assertEqual(out["normalized"]["magnitude"], "93600")
        self.assertIn("source_approximate", out["flags"])
        self.assertNotIn("source_coordinate_frame", out)
        self.assertIsNone(out["event_id"])
        self.assertNotIn("heliocentric", out)
