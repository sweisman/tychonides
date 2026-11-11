import copy
import unittest

from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class SignedModelComparisonTests(unittest.TestCase):
    def row(self, quantity, components, **extra):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=286,
            subject="Mars",
            reference=None,
            quantity=quantity,
            role="reduction",
            flags=[],
        )
        row.update(extra)
        row["normalized"] = normalize_quantity(dict(quantity=quantity, components=components))
        return row

    def test_two_favored_routes_are_preserved_without_ordered_weights(self):
        refs = ["left shoulder of Aquarius", "bright star of Aries"]
        row = self.row(
            "right_ascension",
            dict(degree="348", arcminute="12", arcsecond="10"),
            role="adopted_value",
            source_reduction_method="adoption",
            source_reduction_references=[],
            source_adoption_preferences=refs,
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_adoption_preferences"), refs)
        self.assertIsNone(out["reference"])
        self.assertEqual(out["source_reduction_references"], [])
        self.assertNotIn("weights", out)
        for change in (
            {"role": "recorded_reading"},
            {"source_adoption_preferences": ["private name", refs[0]]},
            {"source_adoption_preferences": [refs[0], refs[0]]},
            {"source_adoption_preferences": [refs[0]]},
            {"source_adoption_preference": refs[0]},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_model_difference_sign_does_not_supply_a_celestial_hemisphere(self):
        for quantity, comp in [
            ("longitude_difference", dict(degree="4", arcminute="18")),
            ("latitude_difference", dict(arcminute="24")),
        ]:
            row = self.row(
                quantity,
                comp,
                role="historical_comparison",
                model_name="Copernicus",
                comparison_relation="coordinate_difference",
                source_comparison_sign="minus",
            )
            out = public_assertion(row)
            self.assertEqual(out.get("source_comparison_sign"), "minus")
            self.assertIsNone(out["direction"])
            self.assertIsNone(out["normalized"]["signed_magnitude"])
            for change in (
                {"source_comparison_sign": "private label"},
                {"role": "reduction"},
                {"comparison_relation": "latitude_change_over_source_interval"},
            ):
                bad = copy.deepcopy(row)
                bad.update(change)
                with self.subTest(change=change), self.assertRaises(ValueError):
                    public_assertion(bad)

    def test_first_and_outermost_pegasus_stars_keep_distinct_target_labels(self):
        for name, direction in [
            ("first star in wing of Pegasus", "west"),
            ("outermost star in wing of Pegasus", "east"),
        ]:
            row = self.row(
                "meridian_distance",
                dict(degree="0", arcminute="46"),
                role="recorded_reading",
                subject=name,
                direction=direction,
            )
            out = public_assertion(row)
            self.assertEqual(out["subject"], name)
            self.assertEqual(out["direction"], direction)
