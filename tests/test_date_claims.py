import copy
import unittest


class DateClaimTests(unittest.TestCase):
    def test_forenoon_keeps_a_lexical_daypart_without_a_clock_origin(self):
        context = self.context()
        context["value"]["daypart_original"] = "forenoon"
        context["day_origin"] = None
        claim = self.module().public_date_claim(context)
        self.assertEqual(claim["daypart"], "before_noon")
        self.assertEqual(context["value"]["daypart_original"], "forenoon")
        self.assertIsNone(claim["absolute_timestamp"])
        self.assertIsNone(claim["day_origin"])

    def test_unpunctuated_am_pm_keep_the_source_daypart_without_an_epoch(self):
        for original, expected in (("AM", "before_noon"), ("PM", "after_noon")):
            with self.subTest(original=original):
                context = self.context()
                context["value"]["daypart_original"] = original
                context["day_origin"] = None
                claim = self.module().public_date_claim(context)
                self.assertEqual(claim["daypart"], expected)
                self.assertEqual(context["value"]["daypart_original"], original)
                self.assertIsNone(claim["absolute_timestamp"])
                self.assertIsNone(claim["day_origin"])

    def test_solar_ingress_date_uses_its_linked_review_attribution(self):
        date = self.context()
        date.update(review_id="review", source_date_role="model_prediction")
        date["value"] = dict(year=1600, month=6, day=11)
        attribution = dict(
            id="model-context",
            volume=date["volume"],
            review_id="review",
            kind="source_observation_context",
            value=dict(
                record_type="historical_model_ingress_row",
                model="Copernicus",
                sign="Cancer",
                year_label=1600,
                month=6,
                day=11,
            ),
        )
        row = dict(
            id="q",
            volume=date["volume"],
            review_id="review",
            subject="Sun",
            context_ids=[date["id"], attribution["id"]],
        )
        before = copy.deepcopy(date)
        claim = self.module().project_date_claims([date, attribution], [row], [])["date_claims"][0]
        self.assertEqual(claim["model_name"], "Copernicus")
        self.assertEqual(claim["model_date_relation"], "solar_ingress_on_named_day")
        self.assertIsNone(claim["absolute_timestamp"])
        self.assertEqual(date, before)
        for change in (dict(review_id="other"), dict(value=dict(attribution["value"], day=10))):
            bad = dict(attribution, **change)
            with self.assertRaises(ValueError):
                self.module().project_date_claims([date, bad], [row], [])
        with self.assertRaises(ValueError):
            self.module().project_date_claims([date], [row], [])

    def test_structured_labels_keep_qualifications_without_becoming_observing_dates(self):
        c = self.context()
        c.update(
            kind="source_observation_context",
            value=dict(
                year=1462,
                month_name="June",
                day=11,
                calendar=None,
                date_expression="night following 1462 June 11",
                clock_convention="after noon",
                record_type="historical_calculation",
                absolute_epoch=None,
            ),
        )
        before = copy.deepcopy(c)
        row = dict(id="q", volume=c["volume"], context_ids=[c["id"]])
        projected = self.module().project_date_claims(
            [c], [row], [], include_structured_contexts=True
        )
        claim = projected["date_claims"][0]
        self.assertEqual((claim["year"], claim["month"], claim["day"]), (1462, 6, 11))
        self.assertEqual(claim["source_date_expression"], "night following 1462 June 11")
        self.assertEqual(claim["source_context_record_type"], "historical_calculation")
        self.assertNotIn("source_date_role", claim)
        for field in ("accepted_observing_date", "absolute_timestamp", "calendar", "day_origin"):
            self.assertIsNone(claim[field])
        self.assertEqual(projected["assertion_date_ids"]["q"], [c["id"]])
        self.assertEqual(c, before)
        self.assertEqual(self.module().project_date_claims([c], [row], [])["date_claims"], [])
        partial = copy.deepcopy(c)
        partial["value"].update(day=None, date_expression="June [?]2")
        self.assertIsNone(
            self.module().project_date_claims([partial], [], [], include_structured_contexts=True)[
                "date_claims"
            ][0]["day"]
        )
        conflict = copy.deepcopy(c)
        conflict["value"]["date_expression"] = "night preceding June11"
        with self.assertRaises(ValueError):
            self.module().project_date_claims(
                [c, conflict], [], [], include_structured_contexts=True
            )

    def test_in_the_morning_retains_daypart_without_clock_or_day_origin(self):
        c = self.context()
        c["value"] = dict(year=1595, month=8, day=23, daypart_original="in the morning")
        out = self.module().public_date_claim(c)
        self.assertEqual(out["daypart"], "morning")
        self.assertIsNone(out["absolute_timestamp"])
        self.assertIsNone(out["day_origin"])

    def test_named_book_dates_retain_source_and_reject_cross_source_links(self):
        c = self.context()
        c.pop("volume")
        c.update(
            source_id="snellius-hassiacae",
            id="context-ssnellius-hassiacae-0123456789abcdefabcd",
            calendar="Julian",
        )
        claim = self.module().public_date_claim(c)
        self.assertEqual(claim["source_id"], c["source_id"])
        self.assertEqual(claim["calendar"], "Julian")
        self.assertNotIn("volume", claim)
        self.assertIsNone(claim["absolute_timestamp"])
        row = dict(id="q", source_id=c["source_id"], context_ids=[c["id"]])
        projected = self.module().project_date_claims([c], [row], [])
        self.assertEqual(projected["assertion_date_ids"]["q"], [c["id"]])
        wrong = dict(row, source_id="ursus-fundamentum")
        with self.assertRaisesRegex(ValueError, "source"):
            self.module().project_date_claims([c], [wrong], [])
        with self.assertRaisesRegex(ValueError, "source"):
            self.module().validate_date_links(
                [dict(wrong, source_date_claim_ids=[c["id"]])], [], [claim]
            )
        with self.assertRaisesRegex(ValueError, "identity"):
            self.module().public_date_claim(dict(c, source_id="other-book"))

    def test_after_midday_label_does_not_establish_a_timestamp(self):
        for label, daypart in (("after midday", "after_noon"), ("before midday", "before_noon")):
            with self.subTest(label=label):
                c = self.context()
                c["value"] = dict(year=1582, month=12, day=28, daypart_original=label)
                out = self.module().public_date_claim(c)
                self.assertEqual(out["daypart"], daypart)
                self.assertIsNone(out["absolute_timestamp"])
                self.assertIsNone(out["day_origin"])

    def test_ad_vesperem_retains_evening_without_accepting_absolute_time(self):
        c = self.context()
        c["value"] = dict(year=1582, month=12, day=30, daypart_original="AD VESPEREM")
        out = self.module().public_date_claim(c)
        self.assertEqual(
            (out["year"], out["month"], out["day"], out["daypart"]), (1582, 12, 30, "evening")
        )
        self.assertEqual(c["value"]["daypart_original"], "AD VESPEREM")
        for key in ("absolute_timestamp", "accepted_observing_date", "calendar", "day_origin"):
            self.assertIsNone(out[key])

    def test_model_opposition_dates_preserve_attribution_without_becoming_observations(self):
        for model, day in [("Alphonsine", 10), ("Prutenic", 15)]:
            c = self.context()
            c["value"] = dict(year=1570, month=2, day=day)
            c.update(
                source_date_role="model_prediction",
                subject="Mars",
                model_name=model,
                model_date_relation="opposition_on_named_day",
            )
            out = self.module().public_date_claim(c)
            self.assertEqual(
                (out["model_name"], out["day"], out["model_date_relation"]),
                (model, day, "opposition_on_named_day"),
            )
            self.assertIsNone(out["absolute_timestamp"])
            self.assertIsNone(out["accepted_observing_date"])
            with self.assertRaises(ValueError):
                self.module().public_date_claim(dict(c, source_date_role="observation_label"))

    def test_tychonic_lunar_eclipse_date_remains_a_prediction(self):
        c = self.context()
        c["value"] = dict(year=1607, month=8, day=26)
        c.update(
            source_date_role="model_prediction",
            subject="Moon",
            model_name="Tycho Brahe",
            model_date_relation="middle_lunar_eclipse_on_named_day",
            calendar="Julian",
            day_origin="noon",
        )
        out = self.module().public_date_claim(c)
        self.assertEqual(out["model_name"], "Tycho Brahe")
        self.assertEqual(out["model_date_relation"], "middle_lunar_eclipse_on_named_day")
        self.assertEqual((out["year"], out["month"], out["day"]), (1607, 8, 26))
        self.assertIsNone(out["accepted_observing_date"])
        self.assertIsNone(out["absolute_timestamp"])
        for change in (
            dict(subject="Sun"),
            dict(model_name="unspecified"),
            dict(source_date_role="observation_label"),
            dict(model_date_relation="observed eclipse"),
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_date_claim(dict(c, **change))

    def test_relative_night_relation_keeps_the_named_day_without_accepting_a_timestamp(self):
        for relation in ("following_night", "preceding_night"):
            c = self.context()
            c["value"] = dict(year=1599, month=12, day=13, daypart_original="night")
            c.update(source_date_role="observation_label", source_day_relation=relation)
            out = self.module().public_date_claim(c)
            self.assertEqual(
                (out["day"], out["daypart"], out["source_day_relation"]), (13, "night", relation)
            )
            self.assertIsNone(out["absolute_timestamp"])
            self.assertIsNone(out["accepted_observing_date"])
            for change in (
                dict(source_day_relation="next calendar day"),
                dict(source_date_role="calculation_target"),
                dict(value=dict(year=1599, month=12, day=13, daypart_original="morning")),
                dict(value=dict(year=1599, month=12, daypart_original="night")),
            ):
                bad = copy.deepcopy(c)
                bad.update(change)
                with self.subTest(change=change), self.assertRaises(ValueError):
                    self.module().public_date_claim(bad)

    def test_editor_reported_calculation_year_variant_does_not_replace_printed_year(self):
        printed = self.context()
        printed.update(source_date_role="calculation_target")
        printed["value"] = dict(year=1593, month=8, day=10, daypart_original="P.M.")
        variant = copy.deepcopy(printed)
        variant["id"] = "context-v12-fedcba9876543210abcd"
        variant["value"] = dict(year=1583, month=8, day=10, daypart_original="P.M.")
        variant.update(
            source_date_role="calculation_target_variant",
            source_date_witness="manuscript_reported_by_editor",
        )
        try:
            result = self.module().project_date_claims(
                [printed, variant],
                [dict(id="input", context_ids=[printed["id"], variant["id"]])],
                [],
            )
        except ValueError as error:
            self.fail("Reported calculation-year variant must project: " + str(error))
        self.assertEqual(len(result["assertion_date_ids"]["input"]), 2)
        self.assertEqual({c["year"] for c in result["date_claims"]}, {1583, 1593})
        self.assertTrue(
            all(
                c["absolute_timestamp"] is None and c["accepted_observing_date"] is None
                for c in result["date_claims"]
            )
        )
        for witness in (None, "printed_heading"):
            bad = copy.deepcopy(variant)
            bad["source_date_witness"] = witness
            with self.subTest(witness=witness), self.assertRaises(ValueError):
                self.module().public_date_claim(bad)

    def test_reported_manuscript_date_variant_stays_distinct_from_printed_heading(self):
        heading = self.context()
        heading["value"] = dict(year=1593, month=10, day=3, daypart_original="VESPERI")
        heading.update(source_date_role="observation_label", source_date_witness="printed_heading")
        variant = copy.deepcopy(heading)
        variant["id"] = "context-v12-fedcba9876543210abcd"
        variant["value"] = dict(year=1593, month=10, day=1)
        variant.update(
            source_date_role="observation_label_variant",
            source_date_witness="manuscript_reported_by_editor",
        )
        result = self.module().project_date_claims(
            [heading, variant], [dict(id="reading", context_ids=[heading["id"], variant["id"]])], []
        )
        self.assertEqual(
            set(result["assertion_date_ids"]["reading"]), {heading["id"], variant["id"]}
        )
        claims = {c["day"]: c for c in result["date_claims"]}
        self.assertEqual(claims[3].get("source_date_witness"), "printed_heading")
        self.assertEqual(claims[1].get("source_date_witness"), "manuscript_reported_by_editor")
        self.assertEqual(claims[1]["source_date_role"], "observation_label_variant")
        self.assertEqual(claims[3]["daypart"], "evening")
        self.assertIsNone(claims[1]["daypart"])
        for c in claims.values():
            for key in ("accepted_observing_date", "absolute_timestamp", "calendar", "day_origin"):
                self.assertIsNone(c[key])

    def test_date_witness_requires_reviewed_attribution_and_matching_role(self):
        c = self.context()
        c.update(
            source_date_role="observation_label_variant",
            source_date_witness="manuscript_reported_by_editor",
        )
        for update in (
            {"source_date_witness": "private claim"},
            {"source_date_witness": None},
            {"source_date_witness": "printed_heading"},
            {"source_date_role": "calculation_target"},
            {"source_date_role": "observation_label"},
        ):
            bad = copy.deepcopy(c)
            bad.update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.module().public_date_claim(bad)
        del c["source_date_witness"]
        with self.assertRaises(ValueError):
            self.module().public_date_claim(c)

    def test_model_date_claims_do_not_become_observed_station_dates(self):
        for model, day, relation in [
            ("Prutenic", 21, "retrograde_motion_begins"),
            ("Alphonsine", 27, "direct_motion_until_date"),
        ]:
            c = self.context()
            c["value"] = dict(year=1593, month=7, day=day)
            c.update(
                source_date_role="model_prediction",
                subject="Mars",
                model_name=model,
                model_date_relation=relation,
            )
            result = self.module().public_date_claim(c)
            self.assertEqual(result.get("model_name"), model)
            self.assertEqual(result.get("model_date_relation"), relation)
            self.assertEqual(result.get("subject"), "Mars")
            self.assertEqual(result["day"], day)
            self.assertIsNone(result["accepted_observing_date"])
            self.assertIsNone(result["absolute_timestamp"])
            self.assertIsNone(result["calendar"])
            self.assertIsNone(result["day_origin"])
        for update in (
            {"model_name": "private note"},
            {"model_date_relation": "observed station"},
            {"source_date_role": "observation_label"},
            {"model_name": None},
            {"subject": "private object"},
        ):
            bad = copy.deepcopy(c)
            bad.update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.module().public_date_claim(bad)

    def test_predicted_near_station_dates_remain_model_claims_without_an_observed_epoch(self):
        for model, day in (("Prutenic", 21), ("Alphonsine", 28)):
            c = self.context()
            c["value"] = dict(year=1593, month=9, day=day)
            c.update(
                source_date_role="model_prediction",
                subject="Mars",
                model_name=model,
                model_date_relation="station_near_date",
            )
            out = self.module().public_date_claim(c)
            self.assertEqual(
                (out["model_name"], out["day"], out["model_date_relation"]),
                (model, day, "station_near_date"),
            )
            self.assertIsNone(out["accepted_observing_date"])
            self.assertIsNone(out["absolute_timestamp"])
            self.assertIsNone(out["calendar"])
            self.assertIsNone(out["day_origin"])

    def test_station_before_named_day_preserves_bound_without_assigning_the_station_date(self):
        c = self.context()
        c["value"] = dict(year=1595, month=12, day=1)
        c.update(
            source_date_role="model_prediction",
            subject="Mars",
            model_name="Prutenic",
            model_date_relation="station_before_named_day",
        )
        out = self.module().public_date_claim(c)
        self.assertEqual((out["day"], out["model_date_relation"]), (1, "station_before_named_day"))
        self.assertIsNone(out["accepted_observing_date"])
        self.assertIsNone(out["absolute_timestamp"])

    def test_station_on_named_day_keeps_day_precision_without_inventing_an_instant(self):
        for model, year, month in [("Alphonsine", 1593, 9), ("Stadius", 1570, 3)]:
            c = self.context()
            c["value"] = dict(year=year, month=month, day=28)
            c.update(
                source_date_role="model_prediction",
                subject="Mars",
                model_name=model,
                model_date_relation="station_on_named_day",
            )
            out = self.module().public_date_claim(c)
            self.assertEqual(
                (out["model_name"], out["day"], out["model_date_relation"]),
                (model, 28, "station_on_named_day"),
            )
            self.assertIsNone(out["absolute_timestamp"])
            self.assertIsNone(out["accepted_observing_date"])
            self.assertIsNone(out["daypart"])
            self.assertIsNone(out["day_origin"])

    def test_last_day_of_month_is_a_source_rule_without_a_computed_day(self):
        c = self.context()
        c["value"] = dict(year=1592, month=2, day=None, day_rule="last_day_of_month")
        result = self.module().public_date_claim(c)
        self.assertEqual(result.get("day_rule"), "last_day_of_month")
        self.assertIsNone(result["day"])
        self.assertIsNone(result["calendar"])
        self.assertIsNone(result["accepted_observing_date"])
        self.assertEqual(result["component_status"], "partial_named_components")
        for update in (
            dict(day=29),
            dict(month=None),
            dict(day_rule="private interpretation"),
            dict(day_number_basis="completed_time_uninterpreted"),
        ):
            wrong = copy.deepcopy(c)
            wrong["value"].update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.module().public_date_claim(wrong)

    def test_completed_time_day_label_stays_uninterpreted(self):
        c = self.context()
        c["value"] = dict(
            year=1591, month=6, day=7, day_number_basis="completed_time_uninterpreted"
        )
        result = self.module().public_date_claim(c)
        self.assertEqual(result.get("day_number_basis"), "completed_time_uninterpreted")
        self.assertIsNone(result["accepted_observing_date"])
        c["value"]["day_number_basis"] = "private interpretation"
        with self.assertRaises(ValueError):
            self.module().public_date_claim(c)

    def module(self):
        from src import date_claims

        return date_claims

    def context(self):
        return dict(
            id="context-v12-0123456789abcdefabcd",
            volume=12,
            kind="recorded_date",
            value=dict(
                year=1590,
                month_original="MARTIJ",
                day=4,
                daypart_original="VESPERI",
                private_note="PRIVATE",
            ),
            calendar=None,
            day_origin=None,
            text_original="PRIVATE SOURCE TEXT",
            lines=[1, 2],
        )

    def test_latin_month_and_daypart_project_without_private_fields(self):
        result = self.module().public_date_claim(self.context())
        self.assertEqual(
            (result["year"], result["month"], result["day"], result["daypart"]),
            (1590, 3, 4, "evening"),
        )
        self.assertIsNone(result["calendar"])
        self.assertIsNone(result["day_origin"])
        self.assertIsNone(result["accepted_observing_date"])
        self.assertIsNone(result["absolute_timestamp"])
        self.assertNotIn("PRIVATE", str(result))
        self.assertNotIn("lines", result)

    def test_month_aliases_and_am_do_not_add_twelve_hours_or_a_calendar(self):
        c = self.context()
        c["value"] = dict(
            year=1585, month=1, month_original="JANUARIJ", day=22, daypart_original="A. M."
        )
        result = self.module().public_date_claim(c)
        self.assertEqual(result["daypart"], "before_noon")
        self.assertNotIn("hour", result)
        self.assertNotIn("julian_day", result)
        self.assertIsNone(result["calendar"])
        translated = copy.deepcopy(c)
        translated["value"]["daypart_original"] = "before noon"
        self.assertEqual(self.module().public_date_claim(translated), result)
        for change in (
            dict(month=2),
            dict(month_original="private narrative"),
            dict(year=True),
            dict(day=0),
            dict(daypart_original="secret"),
        ):
            wrong = copy.deepcopy(c)
            wrong["value"].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_date_claim(wrong)

    def test_partial_and_calendar_unvalidated_components_remain_claims(self):
        c = self.context()
        c["value"] = dict(month=2, day=29)
        result = self.module().public_date_claim(c)
        self.assertIsNone(result["year"])
        self.assertEqual(result["component_status"], "partial_named_components")
        c["value"]["year"] = 1500
        result = self.module().public_date_claim(c)
        self.assertEqual(result["day"], 29)
        self.assertIsNone(result["calendar"])
        self.assertEqual(result["calendar_validation"], "not_performed")
        c["calendar"] = "Julian"
        self.assertEqual(self.module().public_date_claim(c)["calendar"], "Julian")

    def test_after_midnight_is_a_label_without_changing_the_named_day(self):
        c = self.context()
        c["value"] = dict(year=1591, month=4, day=29, daypart_original="Poſt mediam noctem")
        # Structured review uses normalized Latin spelling, preserving the literal source privately.
        c["value"]["daypart_original"] = "POST MEDIAM NOCTEM"
        result = self.module().public_date_claim(c)
        self.assertEqual((result["day"], result["daypart"]), (29, "after_midnight"))
        self.assertIsNone(result["day_origin"])
        self.assertIsNone(result["calendar"])
        self.assertIsNone(result["absolute_timestamp"])

    def test_afternoon_opposition_claim_does_not_supply_an_absolute_time(self):
        for label in ("afternoon", "pomerid.", "after noon"):
            c = self.context()
            c["value"] = dict(year=1593, month=8, day=24, daypart_original=label)
            c["source_date_role"] = "calculation_target"
            result = self.module().public_date_claim(c)
            self.assertEqual((result["day"], result["daypart"]), (24, "after_noon"))
            self.assertIsNone(result["calendar"])
            self.assertIsNone(result["day_origin"])
            self.assertIsNone(result["absolute_timestamp"])
            self.assertIsNone(result["accepted_observing_date"])

    def test_before_midnight_does_not_shift_the_date_or_choose_a_day_origin(self):
        c = self.context()
        c["value"] = dict(year=1591, month=6, day=10, daypart_original="ANTE MEDIAM NOCTEM")
        result = self.module().public_date_claim(c)
        self.assertEqual((result["day"], result["daypart"]), (10, "before_midnight"))
        self.assertIsNone(result["calendar"])
        self.assertIsNone(result["day_origin"])
        self.assertIsNone(result["absolute_timestamp"])

    def test_duplicate_claims_merge_only_when_projected_claims_agree(self):
        c = self.context()
        r = self.module().project_date_claims([c, c], [], [])
        self.assertEqual(len(r["date_claims"]), 1)
        other = copy.deepcopy(c)
        other["value"]["day"] = 5
        with self.assertRaises(ValueError):
            self.module().project_date_claims([c, other], [], [])

    def test_links_follow_explicit_review_contexts_without_event_date_inheritance(self):
        c = self.context()
        other = copy.deepcopy(c)
        other["id"] = "context-v12-fedcba9876543210abcd"
        other["value"]["day"] = 5
        rows = [
            dict(id="a", context_ids=[c["id"], other["id"]], quantity="calculation_epoch"),
            dict(id="b", context_ids=[]),
        ]
        events = [dict(id="e", context_ids=[c["id"]])]
        r = self.module().project_date_claims([c, other], rows, events)
        self.assertEqual(r["assertion_date_ids"]["a"], sorted([c["id"], other["id"]]))
        self.assertEqual(r["assertion_date_ids"]["b"], [])
        self.assertEqual(r["event_date_ids"]["e"], [c["id"]])
        rows[0]["context_ids"] = ["missing"]
        with self.assertRaises(ValueError):
            self.module().project_date_claims([c], rows, events)

    def test_nondate_contexts_are_not_exported_and_public_references_must_resolve(self):
        c = self.context()
        quality = dict(id="quality", kind="quality", value="PRIVATE")
        r = self.module().project_date_claims(
            [c, quality], [dict(id="a", context_ids=["quality"])], []
        )
        self.assertEqual(r["assertion_date_ids"]["a"], [])
        self.module().validate_date_links(
            [dict(source_date_claim_ids=[c["id"]])], [], r["date_claims"]
        )
        with self.assertRaises(ValueError):
            self.module().validate_date_links(
                [dict(source_date_claim_ids=["missing"])], [], r["date_claims"]
            )
