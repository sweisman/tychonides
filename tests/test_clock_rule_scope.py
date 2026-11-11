import copy
import unittest

from src.catalog import normalize_quantity
from src.public_checkpoint import public_assertion


class ClockRuleScopeTests(unittest.TestCase):
    def test_clock_fast_rule_retains_sequence_scope_without_correcting_a_reading(self):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=289,
            subject="observing clock",
            reference=None,
            quantity="clock_correction",
            role="historical_correction",
            source_correction_scope="current_observing_sequence",
            flags=["clock_runs_fast", "clock_correction_not_applied"],
            normalized=normalize_quantity(
                dict(quantity="clock_correction", components=dict(minute="8 1/2"))
            ),
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_correction_scope"), "current_observing_sequence")
        self.assertEqual(out["normalized"]["magnitude"], "510")
        self.assertIsNone(out["variant_of_id"])
        for change in (
            {"quantity": "recorded_clock"},
            {"role": "printed_correction"},
            {"source_correction_scope": "whole catalogue"},
            {"flags": ["clock_runs_fast"]},
            {"subject": "Mars"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_mural_label_is_an_altitude_instrument_without_a_declination_assignment(self):
        row = dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=289,
            subject="Mars",
            reference=None,
            quantity="altitude",
            role="recorded_reading",
            source_instrument_label="mural quadrant",
            normalized=normalize_quantity(
                dict(quantity="altitude", components=dict(degree="21", arcminute="37 5/6"))
            ),
        )
        out = public_assertion(row)
        self.assertEqual(out.get("source_instrument_label"), "mural quadrant")
        self.assertEqual(out["normalized"]["magnitude"], "77870")
        bad = copy.deepcopy(row)
        bad.update(quantity="declination", role="recorded_coordinate")
        with self.assertRaises(ValueError):
            public_assertion(bad)
