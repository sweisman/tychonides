import hashlib
import unittest

from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion


class ZodiacTests(unittest.TestCase):
    def assertion(self):
        return dict(
            quantity="ecliptic_longitude",
            components=dict(degree="20", arcminute="23"),
            zodiac_sign="Gemini",
            source_expression="20 23 ♊",
        )

    def test_source_sign_relative_magnitude_and_full_zodiac_angle_are_distinct(self):
        result = normalize_quantity(self.assertion())
        self.assertEqual(result["magnitude"], "73380")
        self.assertEqual(result["magnitude_degrees"], "1223/60")
        self.assertEqual(result["zodiac_longitude_degrees"], "4823/60")
        self.assertEqual(result["longitude_origin"], "start_of_named_sign")
        self.assertEqual(result["zodiac_sign"], "Gemini")
        self.assertIsNone(result["signed_magnitude"])

    def test_all_sign_offsets_and_fractional_degrees_are_exact(self):
        signs = (
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
        )
        for index, sign in enumerate(signs):
            row = dict(quantity="ecliptic_longitude", components=dict(degree="½"), zodiac_sign=sign)
            with self.subTest(sign=sign):
                self.assertEqual(
                    normalize_quantity(row)["zodiac_longitude_degrees"],
                    str(index * 30 * 2 + 1) + "/2",
                )

    def test_invalid_signs_quantities_and_hemispheres_fail(self):
        for change in (
            dict(zodiac_sign="unknown"),
            dict(quantity="declination"),
            dict(direction="north"),
        ):
            row = self.assertion()
            row.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                normalize_quantity(row)

    def fixture(self):
        text = "Longitude 20 23 ♊\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="span", volume=13, edition_sha256=sha, line_start=1, line_end=1)
        row = dict(
            self.assertion(),
            key="longitude",
            line=1,
            column=None,
            span_id="span",
            subject="Moon",
            role="reduction",
            reference=None,
            unit_basis="Explicit zodiac glyph and angular components",
            flags=[],
        )
        batch = dict(
            id="review",
            volume=13,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.strip().encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=5),
            span_decisions=[dict(span_id="span", decision="include", reason="Reviewed")],
            assertions=[row],
        )
        return text, span, batch

    def test_reviewed_zodiac_sign_requires_its_literal_source_glyph(self):
        text, span, batch = self.fixture()
        self.assertEqual(
            compile_catalogue([batch], {13: text}, [span])["assertions"][0]["normalized"][
                "zodiac_sign"
            ],
            "Gemini",
        )
        batch["assertions"][0]["zodiac_sign"] = "Taurus"
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {13: text}, [span])
        batch["assertions"][0]["zodiac_sign"] = "Gemini"
        batch["assertions"][0]["source_expression"] = "20 23"
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {13: text}, [span])

    def test_public_projection_retains_zodiac_origin_and_rejects_inconsistent_offsets(self):
        text, span, batch = self.fixture()
        row = compile_catalogue([batch], {13: text}, [span])["assertions"][0]
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["zodiac_longitude_degrees"], "4823/60")
        row["normalized"]["zodiac_longitude_degrees"] = "1223/60"
        with self.assertRaises(ValueError):
            public_assertion(row)
