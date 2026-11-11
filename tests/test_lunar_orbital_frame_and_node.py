import unittest
from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class LunarOrbitalFrameAndNodeTests(unittest.TestCase):
    def row(self, q, components, **extra):
        row = dict(
            id="assertion-v12-" + "e" * 20,
            volume=12,
            printed_page=413,
            quantity=q,
            components=components,
            subject="Moon centre",
            reference=None,
            direction=None,
            role="reduction",
            flags=["not_an_additional_raw_reading"],
            **extra,
        )
        row["normalized"] = normalize_quantity(row)
        return row

    def test_lunar_own_orbit_frame_does_not_require_an_unstated_true_label(self):
        row = self.row(
            "orbital_longitude",
            dict(degree="2", arcminute="15 2/3"),
            zodiac_sign="Leo",
            source_coordinate_frame="own_orbit_as_stated",
        )
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Lunar source frame must survive without an invented state: " + str(error))
        self.assertEqual(out["source_coordinate_frame"], "own_orbit_as_stated")
        self.assertNotIn("source_coordinate_state", out)
        self.assertEqual(out["normalized"]["magnitude"], "8140")
        for change in (
            dict(role="recorded_reading"),
            dict(source_coordinate_frame="ecliptic"),
            dict(flags=[]),
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion({**row, **change})

    def test_lunar_source_node_distance_is_a_historical_input(self):
        row = self.row(
            "calculation_angle", dict(degree="100", arcminute="8"), argument_name="node_distance"
        )
        row["role"] = "historical_input"
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Lunar node distance must retain source argument identity: " + str(error))
        self.assertEqual(out["argument_name"], "node_distance")
        self.assertEqual(out["normalized"]["magnitude"], "360480")
        for change in (dict(role="recorded_reading"), dict(flags=[]), dict(quantity="altitude")):
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion({**row, **change})


if __name__ == "__main__":
    unittest.main()
