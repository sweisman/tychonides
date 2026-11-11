import unittest

from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class MarsQuantityTypeTests(unittest.TestCase):
    def test_diameter_drift_and_annotated_times_have_explicit_units(self):
        cases = [
            ("angular_diameter", dict(arcminute="1"), "60", "arcsecond"),
            ("clock_drift", dict(minute="0", second="40"), "40", "second_of_time"),
            ("annotated_time", dict(hour="6", minute="7"), "22020", "second_of_time"),
        ]
        for quantity, components, value, unit in cases:
            with self.subTest(quantity=quantity):
                result = normalize_quantity(dict(quantity=quantity, components=components))
                self.assertEqual(result["magnitude"], value)
                self.assertEqual(result["unit"], unit)

    def test_approximate_diameter_and_qualified_clock_drift_survive_public_projection(self):
        for quantity, components, flags in [
            ("angular_diameter", dict(arcminute="1"), ["source_approximate"]),
            (
                "clock_drift",
                dict(second="40"),
                ["clock_runs_fast", "clock_drift_not_applied_to_times"],
            ),
        ]:
            row = dict(
                id="assertion-v12-0123456789abcdefabcd",
                volume=12,
                printed_page=44,
                quantity=quantity,
                role="calibration" if quantity == "clock_drift" else "recorded_reading",
                subject="observing clock" if quantity == "clock_drift" else "Mars",
                reference=None,
                flags=flags,
                normalized=normalize_quantity(dict(quantity=quantity, components=components)),
            )
            with self.subTest(quantity=quantity):
                result = public_assertion(row)
                self.assertEqual(result["flags"], flags)
                self.assertEqual(
                    result["normalized"]["magnitude"],
                    normalize_quantity(dict(quantity=quantity, components=components))["magnitude"],
                )
