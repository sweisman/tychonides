import copy, unittest
from src.catalog import normalize_quantity
from src.date_claims import public_date_claim
from src.public_checkpoint import public_assertion


class PlannedDatesAndSteelQuadrantTests(unittest.TestCase):
    def test_conditional_observation_plan_keeps_its_source_label_without_an_epoch(self):
        context = dict(
            id="context-v12-" + "7" * 20,
            volume=12,
            kind="recorded_date",
            value=dict(year=1594, month=11, day=29, daypart_original="MANE"),
            calendar=None,
            day_origin=None,
            source_date_role="planned_observation_label",
        )
        try:
            out = public_date_claim(context)
        except ValueError as error:
            self.fail("A planned source date must not become an observation claim: " + str(error))
        self.assertEqual(out["source_date_role"], "planned_observation_label")
        self.assertEqual(out["daypart"], "morning")
        self.assertIsNone(out["accepted_observing_date"])
        self.assertIsNone(out["absolute_timestamp"])
        self.assertIsNone(out["day_origin"])

    def test_explicit_steel_quadrant_label_applies_to_raw_altitude(self):
        row = dict(
            id="assertion-v12-" + "8" * 20,
            volume=12,
            printed_page=346,
            quantity="altitude",
            components=dict(degree="41", arcminute="50"),
            subject="Mars",
            reference=None,
            direction=None,
            role="recorded_reading",
            flags=["observing_clock_unstated"],
            source_instrument_label="steel quadrant",
        )
        row["normalized"] = normalize_quantity(row)
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("An explicitly named steel quadrant must retain its label: " + str(error))
        self.assertEqual(out["source_instrument_label"], "steel quadrant")
        self.assertEqual(out["normalized"]["magnitude"], "150600")
        bad = copy.deepcopy(row)
        bad["role"] = "historical_input"
        with self.assertRaises(ValueError):
            public_assertion(bad)
