import copy
import hashlib
import unittest
from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion


class ParallaxSourceMetadataTests(unittest.TestCase):
    def row(self, quantity, components, **kwargs):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=280,
            quantity=quantity,
            role="historical_input",
            subject="Jupiter",
            reference="Earth",
            direction=None,
            flags=[],
            components=components,
        )
        row.update(kwargs)
        row["normalized"] = normalize_quantity(row)
        return row

    def test_source_third_part_is_a_ratio_with_sun_reference_not_a_solar_angle(self):
        text = "A third part of the mean solar parallax."
        sha = hashlib.sha256(text.encode()).hexdigest()
        row = self.row(
            "correction_ratio",
            {"ratio": "1/3"},
            reference="Sun",
            correction_ratio_kind="jupiter_to_mean_solar_parallax",
        )
        for key in ("id", "volume", "printed_page", "normalized"):
            row.pop(key)
        row.update(
            key="ratio",
            line=1,
            span_id="s",
            source_expression="third part",
            source_word_numbers={"third part": "1/3"},
            unit_basis="Source dimensionless parallax proportion",
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        batch = dict(
            id="ratio",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=sha,
            basis=dict(kind="source_review", printed_page=280),
            assertions=[row],
            span_decisions=[
                dict(span_id="s", decision="include", reason="Fraction phrase explicitly reviewed")
            ],
        )
        result = public_assertion(compile_catalogue([batch], {12: text}, [span])["assertions"][0])
        self.assertEqual(result["normalized"]["magnitude"], "1/3")
        self.assertEqual(result["normalized"]["unit"], "ratio")
        self.assertIsNone(result["normalized"]["magnitude_degrees"])
        self.assertEqual(result["reference"], "Sun")
        self.assertEqual(result["correction_ratio_kind"], "jupiter_to_mean_solar_parallax")

    def test_parallax_ratio_rejects_a_different_body_or_unreviewed_ratio_kind(self):
        row = self.row(
            "correction_ratio",
            {"ratio": "1/3"},
            reference="Sun",
            correction_ratio_kind="jupiter_to_mean_solar_parallax",
        )
        for change in (
            {"reference": "mean Sun"},
            {"reference": "Earth"},
            {"subject": "Mars"},
            {"correction_ratio_kind": "unreviewed ratio"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_earth_semidiameter_unit_can_be_inherited_without_becoming_degrees_or_kilometres(self):
        row = self.row(
            "distance_in_semidiameters",
            {"semidiameter": "575"},
            subject="annual orb",
            reference=None,
            source_semidiameter_body="Earth",
            flags=["source_unit_inherited"],
        )
        out = public_assertion(row)
        self.assertEqual(out["source_semidiameter_body"], "Earth")
        self.assertEqual(out["normalized"]["magnitude"], "575")
        self.assertEqual(out["normalized"]["unit"], "source_semidiameter")
        self.assertIsNone(out["normalized"]["magnitude_degrees"])
        self.assertIn("source_unit_inherited", out["flags"])
        for change in ({"source_semidiameter_body": "Moon"}, {"quantity": "altitude"}):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_horizontal_parallax_flag_cannot_label_an_altitude_argument(self):
        row = self.row(
            "parallax_angle",
            {"arcminute": "1"},
            role="reduction",
            flags=["source_horizontal_parallax", "historical_parallax_not_detection"],
        )
        out = public_assertion(row)
        self.assertEqual(out["normalized"]["magnitude"], "60")
        self.assertIn("source_horizontal_parallax", out["flags"])
        bad = copy.deepcopy(row)
        bad["quantity"] = "altitude"
        with self.assertRaises(ValueError):
            public_assertion(bad)
