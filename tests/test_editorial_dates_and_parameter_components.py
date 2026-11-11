import copy, unittest
from src.catalog import normalize_quantity
from src.date_claims import public_date_claim, project_date_claims
from src.public_checkpoint import public_assertion


class EditorialDateAndParameterTests(unittest.TestCase):
    def date(self, token, year, month, editor=False):
        return dict(
            id="context-v12-" + token * 20,
            volume=12,
            kind="recorded_date",
            value=dict(year=year, month=month, day=None, month_part="end"),
            calendar=None,
            day_origin=None,
            source_date_role="editorial_date_comment" if editor else "calculation_target",
            **(dict(source_date_witness="editorial_comment") if editor else {}),
        )

    def row(self, q, parts, **extra):
        row = dict(
            id="assertion-v12-" + "6" * 20,
            volume=12,
            printed_page=310,
            quantity=q,
            components=parts,
            subject="Mars",
            reference=None,
            direction=None,
            role="historical_input",
            flags=["not_an_additional_raw_reading"],
        )
        row.update(extra)
        row["normalized"] = normalize_quantity(row)
        return row

    def test_editorial_date_comments_do_not_relabel_a_source_assumption(self):
        assumption = self.date("1", 1585, 10)
        comments = [self.date("2", 1585, 1, True), self.date("3", 1595, 10, True)]
        try:
            out = project_date_claims(
                [assumption, *comments],
                [dict(id="a", volume=12, context_ids=[assumption["id"]])],
                [],
            )
        except ValueError as error:
            self.fail("Partial end-month dates and editorial comments must project: " + str(error))
        self.assertEqual(out["assertion_date_ids"]["a"], [assumption["id"]])
        self.assertEqual(len(out["date_claims"]), 3)
        for claim in out["date_claims"]:
            self.assertEqual(claim["month_part"], "end")
            self.assertIsNone(claim["day"])
            self.assertIsNone(claim["absolute_timestamp"])
        for change in ({"day": 31}, {"month": None}, {"day_rule": "last_day_of_month"}):
            bad = copy.deepcopy(assumption)
            bad["value"].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_date_claim(bad)

    def test_editorial_count_prefix_and_northern_node_are_parameters(self):
        node = self.row(
            "ecliptic_longitude",
            {"degree": "17", "arcminute": "0"},
            zodiac_sign="Taurus",
            source_parameter_kind="northern_node_longitude",
        )
        distance = self.row(
            "calculation_angle",
            {"sign_count": "3", "degree": "6", "arcminute": "40"},
            argument_name="node_before_apogee_distance",
            source_angular_count_unit="sign_count",
            source_editorial_component_units=["sign_count"],
        )
        try:
            n, d = public_assertion(node), public_assertion(distance)
        except ValueError as error:
            self.fail("Node hypothesis and partly editorial distance must export: " + str(error))
        self.assertEqual(n["normalized"]["zodiac_longitude_degrees"], "47")
        self.assertEqual(d["normalized"]["magnitude"], "348000")
        self.assertEqual(d["source_editorial_component_units"], ["sign_count"])
        self.assertEqual(d["role"], "historical_input")
        bad = copy.deepcopy(distance)
        bad["source_editorial_component_units"] = ["degree"]
        with self.assertRaises(ValueError):
            public_assertion(bad)

    def test_included_parallax_parameter_and_claimed_record_count_are_not_raw_data(self):
        row = self.row(
            "ecliptic_latitude",
            {"degree": "4", "arcminute": "34"},
            direction="north",
            source_parameter_kind="greatest_northern_latitude",
            source_coordinate_state="parallax_included_as_stated",
            flags=["not_an_additional_raw_reading", "historical_parallax_not_detection"],
        )
        count = self.row(
            "source_scalar",
            {"scalar": "2"},
            subject="Mars calculation",
            source_parameter_kind="source_record_count",
        )
        try:
            out, c = public_assertion(row), public_assertion(count)
        except ValueError as error:
            self.fail(
                "Historical parameter and source count must retain their roles: " + str(error)
            )
        self.assertEqual(out["source_coordinate_state"], "parallax_included_as_stated")
        self.assertNotIn("correction_value", out)
        self.assertEqual(c["normalized"]["unit"], "source_scalar")
        bad = copy.deepcopy(row)
        bad["role"] = "recorded_coordinate"
        with self.assertRaises(ValueError):
            public_assertion(bad)
