import unittest
from src.public_checkpoint import public_assertion


class SourceCoordinateStateTests(unittest.TestCase):
    def fixture(self):
        return dict(
            id="assertion-v12-0123456789abcdefabcd",
            volume=12,
            printed_page=279,
            quantity="ecliptic_longitude",
            role="reduction",
            subject="Jupiter",
            reference=None,
            direction=None,
            event_id=None,
            variant_of_id=None,
            series_id=None,
            normalized=dict(
                status="exact",
                unit="arcsecond",
                magnitude="62600",
                magnitude_degrees="313/18",
                signed_magnitude=None,
                least_component_unit="arcminute",
            ),
            flags=[],
        )

    def test_source_labels_remain_distinct_without_changing_the_coordinate_number(self):
        for quantity in ("ecliptic_longitude", "ecliptic_latitude"):
            for state in ("refracted", "true"):
                row = self.fixture()
                row.update(quantity=quantity, source_coordinate_state=state)
                with self.subTest(quantity=quantity, state=state):
                    out = public_assertion(row)
                    self.assertEqual(out["source_coordinate_state"], state)
                    self.assertEqual(out["normalized"]["magnitude"], "62600")
        self.assertNotIn("source_coordinate_state", public_assertion(self.fixture()))

    def test_unknown_states_and_noncoordinate_quantities_are_rejected(self):
        for changes in (
            {"source_coordinate_state": "modern corrected"},
            {"source_coordinate_state": "true", "quantity": "recorded_clock"},
            {"source_coordinate_state": "refracted", "quantity": "longitude_correction"},
        ):
            row = self.fixture()
            row.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                public_assertion(row)
