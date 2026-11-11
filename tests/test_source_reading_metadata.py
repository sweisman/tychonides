import copy
import unittest
from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class SourceReadingMetadataTests(unittest.TestCase):
    def test_with_the_other_keeps_an_unresolved_setting_without_pinnule_inference(self):
        row = self.row(
            "declination",
            {"degree": "1", "arcminute": "45 2/3"},
            role="repeated_reading",
            source_component_label="with the other",
            flags=["limb_or_instrument_setting_unresolved", "hemisphere_unspecified"],
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_component_label"), "with the other")
        self.assertEqual(out["normalized"]["magnitude"], "6340")
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        for change in ({"quantity": "altitude"}, {"flags": []}, {"role": "historical_input"}):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_largest_armillae_is_source_qualifier_without_a_physical_size_or_precision(self):
        row = self.row(
            "declination",
            {"degree": "1", "arcminute": "45 1/2"},
            role="recorded_coordinate",
            source_instrument_label="armillae",
            source_instrument_qualifier="largest",
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_instrument_qualifier"), "largest")
        self.assertNotIn("instrument_diameter", out)
        self.assertNotIn("accuracy", out)
        for change in (
            {"source_instrument_label": None},
            {"source_instrument_label": "steel instrument"},
            {"source_instrument_qualifier": "private description"},
            {"quantity": "altitude"},
            {"role": "historical_input"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_with_one_preserves_an_unresolved_component_without_naming_a_pinnule(self):
        row = self.row(
            "declination",
            {"degree": "10", "arcminute": "14 1/2"},
            role="recorded_coordinate",
            source_component_label="with one",
            flags=["limb_or_instrument_setting_unresolved"],
        )
        result = public_assertion(row)
        self.assertEqual(result.get("source_component_label"), "with one")
        self.assertEqual(result["normalized"]["magnitude"], "36870")
        self.assertIsNone(result["direction"])
        row["flags"] = []
        with self.assertRaises(ValueError):
            public_assertion(row)

    def row(self, quantity, components, **extra):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=282,
            subject="Mars",
            reference=None,
            quantity=quantity,
            role="recorded_reading",
            direction=None,
            components=components,
            flags=[],
        )
        row.update(extra)
        row["normalized"] = normalize_quantity(row)
        return row

    def test_with_both_retains_one_value_without_naming_unknown_pinnules(self):
        row = self.row(
            "declination",
            {"degree": "12", "arcminute": "17"},
            role="recorded_coordinate",
            source_component_label="with both",
            flags=["limb_or_instrument_setting_unresolved", "hemisphere_unspecified"],
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_component_label"), "with both")
        self.assertEqual(out["normalized"]["magnitude"], "44220")
        self.assertIsNone(out["direction"])
        self.assertIsNone(out["normalized"]["signed_magnitude"])
        for change in (
            {"quantity": "angular_separation", "reference": "Vulture"},
            {"flags": []},
            {"role": "historical_prediction"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_explicit_altitude_instrument_cannot_be_assigned_to_the_nearby_declination(self):
        row = self.row(
            "altitude",
            {"degree": "19", "arcminute": "56"},
            source_instrument_label="revolving quadrant",
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_instrument_label"), "revolving quadrant")
        self.assertEqual(out["normalized"]["magnitude"], "71760")
        row["source_instrument_label"] = "lesser quadrant"
        self.assertEqual(public_assertion(row).get("source_instrument_label"), "lesser quadrant")
        row["source_instrument_label"] = "steel instrument"
        self.assertEqual(public_assertion(row).get("source_instrument_label"), "steel instrument")
        for change in (
            {"quantity": "declination"},
            {"source_instrument_label": "private note"},
            {"role": "historical_input"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
