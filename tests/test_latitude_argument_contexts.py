import copy
import unittest

from src.catalog import normalize_quantity
from src.date_claims import public_date_claim
from src.public_checkpoint import public_assertion


class LatitudeArgumentContextsTests(unittest.TestCase):
    def row(self, quantity, components, **extra):
        row = dict(
            id="assertion-v12-" + "c" * 20,
            volume=12,
            printed_page=306,
            quantity=quantity,
            components=components,
            subject="Mars",
            reference=None,
            direction=None,
            role="historical_input",
            flags=["not_an_additional_raw_reading"],
        )
        row.update(extra)
        row["normalized"] = normalize_quantity(row)
        return row

    def test_following_midnight_preserves_completed_day_without_a_numeric_epoch(self):
        context = dict(
            id="context-v12-" + "a" * 20,
            volume=12,
            kind="recorded_date",
            source_date_role="calculation_target",
            calendar=None,
            day_origin=None,
            value=dict(
                year=1593,
                month=8,
                day=10,
                daypart_original="in M. N. ſeq.",
                day_number_basis="completed_time_uninterpreted",
            ),
        )
        try:
            out = public_date_claim(context)
        except ValueError as error:
            self.fail("Following-midnight source label must be retained: " + str(error))
        self.assertEqual(out["day"], 10)
        self.assertEqual(out["daypart"], "following_midnight")
        self.assertEqual(out["day_number_basis"], "completed_time_uninterpreted")
        self.assertIsNone(out["day_origin"])
        self.assertIsNone(out["absolute_timestamp"])
        self.assertNotIn("hour", out)

    def test_fractional_reconciliation_preserves_comparison_without_an_angle(self):
        for fraction, relation in (
            ("1/6", "greater_than_computed"),
            ("1/12", "less_than_computed"),
        ):
            row = self.row(
                "source_fraction",
                {"fraction": fraction},
                role="historical_correction",
                source_fraction_kind="latitude_reconciliation",
                comparison_relation=relation,
            )
            try:
                out = public_assertion(row)
            except ValueError as error:
                self.fail("Source reconciliation fraction must export: " + str(error))
            self.assertEqual(out["normalized"]["magnitude"], fraction)
            self.assertEqual(out["normalized"]["unit"], "source_fraction")
            self.assertEqual(out["comparison_relation"], relation)
            self.assertIsNone(out["normalized"]["magnitude_degrees"])
            for change in (
                {"role": "recorded_reading"},
                {"reference": "Sun"},
                {"model_name": "Copernicus"},
                {"comparison_relation": "measured_uncertainty"},
            ):
                bad = copy.deepcopy(row)
                bad.update(change)
                with self.subTest(change=change), self.assertRaises(ValueError):
                    public_assertion(bad)

    def test_latitude_arguments_and_offsets_cannot_become_recorded_coordinates(self):
        for name, role in (
            ("latitude_argument", "historical_input"),
            ("latitude_argument", "calculation_intermediate"),
            ("latitude_argument_correction", "historical_correction"),
            ("apogee_to_latitude_maximum", "historical_input"),
            ("apogee_to_latitude_maximum", "historical_correction"),
            ("apogee_to_latitude_maximum", "editorial_addition"),
        ):
            row = self.row(
                "calculation_angle",
                {"degree": "6", "arcminute": "45"},
                role=role,
                argument_name=name,
                **(
                    {"annotation_of_id": "assertion-v12-" + "d" * 20}
                    if role == "editorial_addition"
                    else {}
                ),
            )
            try:
                out = public_assertion(row)
            except ValueError as error:
                self.fail("Source argument and offset must export: " + str(error))
            self.assertEqual(out["argument_name"], name)
            self.assertEqual(out["normalized"]["magnitude"], "24300")
            for change in (
                {"role": "recorded_coordinate"},
                {"quantity": "ecliptic_latitude"},
                {"direction": "north"},
            ):
                bad = copy.deepcopy(row)
                bad.update(change)
                with self.subTest(change=change), self.assertRaises(ValueError):
                    public_assertion(bad)
