import copy
import hashlib
import unittest

from src.catalog import compile_catalogue
from src.public_checkpoint import public_assertion


class SourceOrbitalLongitudeTests(unittest.TestCase):
    def fixture(self):
        text = "True longitude in its own orbit: 7° 15′ ♓\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="orbit-span", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        row = dict(
            key="longitude",
            line=1,
            span_id=span["id"],
            source_expression="7° 15′ ♓",
            quantity="orbital_longitude",
            role="reduction",
            subject="Mars",
            reference=None,
            direction=None,
            zodiac_sign="Pisces",
            components={"degree": "7", "arcminute": "15"},
            source_coordinate_frame="own_orbit_as_stated",
            source_coordinate_state="true",
            unit_basis="Source own-orbit longitude, no ecliptic conversion",
            flags=["not_an_additional_raw_reading"],
        )
        batch = dict(
            id="orbit-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=292),
            span_decisions=[
                dict(
                    span_id=span["id"],
                    decision="include",
                    reason="Source frame explicitly reviewed",
                )
            ],
            assertions=[row],
            contexts=[],
            events=[],
        )
        return text, [span], batch

    def test_source_orbit_frame_and_nominal_sign_notation_remain_distinct_from_ecliptic(self):
        text, spans, batch = self.fixture()
        r = compile_catalogue([batch], {12: text}, spans)
        a = r["assertions"][0]
        out = public_assertion(a)
        self.assertEqual(a["source_expression"], "7° 15′ ♓")
        self.assertEqual(out["quantity"], "orbital_longitude")
        self.assertEqual(out.get("source_coordinate_frame"), "own_orbit_as_stated")
        self.assertEqual(out.get("source_coordinate_state"), "true")
        self.assertEqual(out["normalized"]["magnitude"], "26100")
        self.assertEqual(out["normalized"]["zodiac_longitude_degrees"], "1349/4")
        self.assertNotIn("heliocentric", out)
        self.assertIsNone(out["event_id"])

    def test_unstated_frame_or_relabelled_coordinate_cannot_export(self):
        text, spans, batch = self.fixture()
        for change in (
            {"source_coordinate_frame": None},
            {"source_coordinate_frame": "heliocentric"},
            {"quantity": "ecliptic_longitude"},
            {"role": "recorded_coordinate"},
            {"source_coordinate_state": "apparent"},
            {"model_name": "Copernicus"},
            {"direction": "south"},
        ):
            bad = copy.deepcopy(batch)
            bad["assertions"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                r = compile_catalogue([bad], {12: text}, spans)
                public_assertion(r["assertions"][0])
        bad = copy.deepcopy(batch)
        del bad["assertions"][0]["source_coordinate_frame"]
        with self.assertRaises(ValueError):
            r = compile_catalogue([bad], {12: text}, spans)
            public_assertion(r["assertions"][0])
