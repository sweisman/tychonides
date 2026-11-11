import copy
import hashlib
import unittest

from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion, validate_links


class SourceContinuationTests(unittest.TestCase):
    def test_positioned_fragments_resolve_repeated_table_numerals(self):
        text = "0 | 0 [recte: 1?]° 3′ 50″ | 0\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        start = text.index("0 [recte")
        tail = text.index("°")
        assertion = dict(
            key="original",
            line=1,
            span_id="s",
            column=2,
            source_expression="0",
            char_start=start,
            char_end=start + 1,
            source_fragments=[
                dict(
                    line=1, span_id="s", source_expression="0", char_start=start, char_end=start + 1
                ),
                dict(
                    line=1,
                    span_id="s",
                    source_expression="° 3′ 50″",
                    char_start=tail,
                    char_end=tail + len("° 3′ 50″"),
                ),
            ],
            source_continuation_context_key="continuation",
            context_keys=["continuation"],
            quantity="declination",
            role="calculation_intermediate",
            subject="Sun",
            reference=None,
            direction=None,
            components={"degree": "0", "arcminute": "3", "arcsecond": "50"},
            flags=["not_an_additional_raw_reading"],
            unit_basis="Literal source units",
        )
        batch = dict(
            id="positioned",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip().encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=81),
            contexts=[
                dict(
                    key="continuation",
                    kind="source_observation_context",
                    lines=[1],
                    value={
                        "record_type": "source_continuation",
                        "source_expression": text.rstrip(),
                    },
                )
            ],
            assertions=[assertion],
            span_decisions=[
                dict(
                    span_id="s", decision="include", reason="Original around editorial alternative"
                )
            ],
        )
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=1)]
        row = compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "230")
        for changes in (
            {"char_end": start + 2},
            {"char_start": True},
            {"char_start": 0, "char_end": 1},
        ):
            bad = copy.deepcopy(batch)
            bad["assertions"][0]["source_fragments"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                compile_catalogue([bad], {10: text}, spans)
        bad = copy.deepcopy(batch)
        del bad["assertions"][0]["source_fragments"][0]["char_start"]
        del bad["assertions"][0]["source_fragments"][0]["char_end"]
        with self.assertRaises(ValueError):
            compile_catalogue([bad], {10: text}, spans)

    def test_repeated_same_reading_keeps_exact_or_unresolved_original(self):
        for expression, components, flags, expected in [
            ("9° 24′", {"degree": "9", "arcminute": "24"}, [], "33840"),
            ("9° 24 1/[?]′", {}, ["source_notation_unresolved"], None),
        ]:
            text = expression + "\nsecond: the same\n"
            sha = hashlib.sha256(text.encode()).hexdigest()
            spans = [
                dict(id=str(n), volume=10, edition_sha256=sha, line_start=n, line_end=n)
                for n in (1, 2)
            ]
            first = dict(
                key="first",
                line=1,
                span_id="1",
                source_expression=expression,
                quantity="angular_separation",
                role="recorded_reading",
                subject="Saturn",
                reference="Capella",
                components=components,
                flags=flags,
                context_keys=["session"],
                unit_basis="Printed D/M",
            )
            second = dict(
                first,
                key="second",
                line=2,
                span_id="2",
                source_expression="the same",
                role="repeated_reading",
                components={},
                flags=[*flags, "source_value_stated_equal"],
                source_value_equal_to_key="first",
            )
            batch = dict(
                id="repeat",
                volume=10,
                edition_sha256=sha,
                line_start=1,
                line_end=2,
                interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
                basis=dict(kind="final_edition_review", printed_page=32),
                contexts=[
                    dict(
                        key="session",
                        kind="source_observation_context",
                        lines=[1, 2],
                        value="Same observing group",
                    )
                ],
                assertions=[first, second],
                span_decisions=[
                    dict(span_id=str(n), decision="include", reason="Explicit repetition")
                    for n in (1, 2)
                ],
            )
            with self.subTest(expression=expression):
                compiled = compile_catalogue([batch], {10: text}, spans)["assertions"]
                compiled.sort(key=lambda row: row["key"])
                public = [public_assertion(a) for a in compiled]
                validate_links(public, [], [])
                self.assertEqual(public[1]["normalized"]["magnitude"], expected)
                self.assertEqual(public[1]["source_equality_kind"], "repeated_measurement")
                self.assertEqual(compiled[1]["components"], {})
                bad = copy.deepcopy(batch)
                bad["assertions"][1]["reference"] = "Spica"
                with self.assertRaises(ValueError):
                    compile_catalogue([bad], {10: text}, spans)
                bad_public = copy.deepcopy(public)
                bad_public[1]["reference"] = "Spica"
                with self.assertRaises(ValueError):
                    validate_links(bad_public, [], [])

    def test_fragment_binding_distinguishes_whole_numbers_from_numeric_suffixes(self):
        for first, accepted in [
            ("| 4′ | 24′ |", True),
            ("| 24′ |", False),
            ("| 1/4′ |", False),
            ("| 4′ | 4′ |", False),
        ]:
            text = first + "\n| 17° { |\n"
            sha = hashlib.sha256(text.encode()).hexdigest()
            spans = [
                dict(id=str(n), volume=10, edition_sha256=sha, line_start=n, line_end=n)
                for n in (1, 2)
            ]
            batch = dict(
                id="shared-degree",
                volume=10,
                edition_sha256=sha,
                line_start=1,
                line_end=2,
                interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
                basis=dict(kind="final_edition_review", printed_page=8),
                contexts=[
                    dict(
                        key="brace",
                        kind="source_observation_context",
                        lines=[2],
                        value=dict(record_type="source_continuation", source_expression="17° {"),
                    )
                ],
                span_decisions=[
                    dict(span_id=str(n), decision="include", reason="Shared degree brace")
                    for n in (1, 2)
                ],
                assertions=[
                    dict(
                        key="altitude",
                        line=1,
                        span_id="1",
                        source_expression="4′",
                        source_fragments=[
                            dict(line=1, span_id="1", source_expression="4′"),
                            dict(line=2, span_id="2", source_expression="17°"),
                        ],
                        source_continuation_context_key="brace",
                        context_keys=["brace"],
                        quantity="altitude",
                        role="recorded_reading",
                        subject="Sun",
                        reference=None,
                        components=dict(degree="17", arcminute="4"),
                        source_component_order=["arcminute", "degree"],
                        unit_basis="Explicit degree and minute marks across a brace",
                    )
                ],
            )
            with self.subTest(first=first):
                if accepted:
                    row = compile_catalogue([batch], {10: text}, spans)["assertions"][0]
                    self.assertEqual(public_assertion(row)["normalized"]["magnitude"], "61440")
                else:
                    with self.assertRaises(ValueError):
                        compile_catalogue([batch], {10: text}, spans)

    def test_explicit_same_hour_keeps_its_own_date_and_no_invented_components(self):
        from src.date_claims import project_date_claims

        text = "At about hour 8 in the evening.\n### March 4\nThe hour as above.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [
            dict(id=str(n), volume=10, edition_sha256=sha, line_start=n, line_end=n) for n in [1, 3]
        ]
        contexts = [
            dict(
                key="scope",
                kind="source_observation_context",
                lines=[1, 3],
                value={"record_type": "explicit_clock_reference"},
            )
        ]
        for key, line, day in [("day3", 1, 3), ("day4", 2, 4)]:
            contexts.append(
                dict(
                    key=key,
                    kind="recorded_date",
                    lines=[line],
                    value=dict(year=1570, month=3, day=day),
                    calendar=None,
                    day_origin=None,
                    source_date_role="observation_label",
                )
            )
        first = dict(
            key="first",
            line=1,
            span_id="1",
            source_expression="hour 8",
            quantity="recorded_clock",
            role="recorded_clock",
            subject="observing clock",
            reference=None,
            direction=None,
            components={"hour": "8"},
            context_keys=["scope", "day3"],
            flags=["source_approximate"],
            unit_basis="Recorded clock hours",
        )
        second = dict(
            first,
            key="second",
            line=3,
            span_id="3",
            source_expression="The hour as above.",
            components={},
            source_value_equal_to_key="first",
            context_keys=["scope", "day4"],
            flags=["source_approximate", "source_value_stated_equal"],
        )
        batch = dict(
            id="clock-reference",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=3,
            interval_sha256=hashlib.sha256(text.rstrip().encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=27),
            contexts=contexts,
            assertions=[first, second],
            span_decisions=[
                dict(span_id=s["id"], decision="include", reason="Explicit same clock value")
                for s in spans
            ],
        )
        c = compile_catalogue([batch], {10: text}, spans)
        bykey = {a["key"]: a for a in c["assertions"]}
        out = [public_assertion(a) for a in c["assertions"]]
        validate_links(out, [], [])
        self.assertEqual(bykey["second"]["normalized"]["magnitude"], "28800")
        self.assertEqual(bykey["second"]["components"], {})
        self.assertEqual(bykey["second"]["source_value_equal_to_id"], bykey["first"]["id"])
        dates = project_date_claims(c["contexts"], c["assertions"], [])["assertion_date_ids"]
        self.assertNotEqual(dates[bykey["first"]["id"]], dates[bykey["second"]["id"]])
        for changes in [
            dict(components={"hour": "8"}),
            dict(source_expression="The hour"),
            dict(context_keys=["day4"]),
        ]:
            bad = copy.deepcopy(batch)
            bad["assertions"][1].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                compile_catalogue([bad], {10: text}, spans)

    def test_same_line_shared_hour_can_supply_the_explicit_equal_time_minutes(self):
        text = "At hour 7, minute 5½ in apparent time — minute 12 in equal time.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=1)
        c = dict(
            key="shared-hour",
            kind="source_observation_context",
            lines=[1],
            value=dict(
                record_type="source_continuation", source_expression="minute 12 in equal time"
            ),
        )
        a = dict(
            key="equal",
            line=1,
            span_id="s",
            source_expression="hour 7",
            source_fragments=[
                dict(line=1, span_id="s", source_expression="hour 7"),
                dict(line=1, span_id="s", source_expression="minute 12"),
            ],
            source_continuation_context_key="shared-hour",
            context_keys=["shared-hour"],
            quantity="calculation_epoch",
            role="calculation_epoch",
            subject="Moon",
            reference=None,
            direction=None,
            components={"hour": "7", "minute": "12"},
            source_time_scale="equal",
            flags=["not_an_observing_clock", "not_an_additional_raw_reading"],
            unit_basis="Explicit shared source hour",
        )
        batch = dict(
            id="shared-hour",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip().encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=25),
            contexts=[c],
            assertions=[a],
            span_decisions=[
                dict(span_id="s", decision="include", reason="Two source time representations")
            ],
        )
        try:
            row = public_assertion(compile_catalogue([batch], {10: text}, [span])["assertions"][0])
        except ValueError as error:
            self.fail(f"Shared printed hour must retain the equal-time representation: {error}")
        self.assertEqual(row["normalized"]["magnitude"], "25920")
        self.assertEqual(row.get("source_time_scale"), "equal")

    def fixture(self):
        text = (
            "Mars is at 13^g^ and\n"
            "[The sentence continues on the next page.]\n"
            "40^1^ minutes of ♍.\n"
            "In the margin: or 10, the figure is ambiguous.\n"
        )
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=4)]
        context = dict(
            key="continuation",
            kind="source_observation_context",
            lines=[2],
            value=dict(
                record_type="source_continuation",
                source_expression="The sentence continues on the next page.",
            ),
        )
        original = dict(
            key="position",
            line=1,
            span_id="s",
            source_expression="13^g^",
            source_fragments=[
                dict(line=1, span_id="s", source_expression="13^g^"),
                dict(line=3, span_id="s", source_expression="40"),
                dict(line=3, span_id="s", source_expression="minutes of ♍"),
            ],
            source_continuation_context_key="continuation",
            context_keys=["continuation"],
            quantity="ecliptic_longitude",
            role="reduction",
            subject="Mars",
            reference=None,
            direction=None,
            components=dict(degree="13", arcminute="40"),
            zodiac_sign="Virgo",
            unit_basis="Explicit continuation of the same source coordinate",
            flags=["not_an_additional_raw_reading"],
        )
        alternative = dict(
            key="alternative",
            line=4,
            span_id="s",
            source_expression="10",
            quantity="ecliptic_longitude",
            role="source_alternative",
            subject="Mars",
            reference=None,
            direction=None,
            components=dict(degree="13", arcminute="10"),
            variant_of_key="position",
            inherited_components={"degree": "position"},
            zodiac_sign="Virgo",
            zodiac_sign_inherited_from_key="position",
            context_keys=["continuation"],
            unit_basis="Margin changes only the minute component of the linked position",
            flags=["alternative_suggestion_not_applied", "not_an_additional_raw_reading"],
        )
        batch = dict(
            id="continued",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=4,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(
                kind="final_edition_review",
                printed_page=21,
                page_segments=[
                    dict(line_start=1, line_end=2, printed_page=21, witness_sha256=sha),
                    dict(line_start=3, line_end=4, printed_page=22, witness_sha256=sha),
                ],
            ),
            contexts=[context],
            span_decisions=[
                dict(span_id="s", decision="include", reason="Coordinate and source alternative")
            ],
            assertions=[original, alternative],
        )
        return text, spans, batch

    def test_bound_fragments_form_one_longitude_with_an_unapplied_alternative(self):
        text, spans, batch = self.fixture()
        try:
            result = compile_catalogue([batch], {10: text}, spans)
        except ValueError as error:
            self.fail(f"Explicit continuation must retain the complete source coordinate: {error}")
        rows = {a["key"]: a for a in result["assertions"]}
        self.assertEqual(rows["position"]["normalized"]["magnitude"], "49200")
        self.assertEqual(rows["position"]["normalized"]["zodiac_longitude_degrees"], "491/3")
        self.assertEqual(rows["alternative"]["normalized"]["magnitude"], "47400")
        self.assertEqual(rows["alternative"]["variant_of_id"], rows["position"]["id"])
        public = [public_assertion(a) for a in result["assertions"]]
        self.assertEqual(public[0].get("source_fragment_pages"), [21, 22])
        validate_links(public, [], [])

    def test_changed_unordered_unbound_or_heading_crossing_fragments_fail(self):
        for change in ("value", "order", "span", "context", "heading"):
            text, spans, batch = self.fixture()
            if change == "value":
                batch["assertions"][0]["source_fragments"][1]["source_expression"] = "41"
            elif change == "order":
                batch["assertions"][0]["source_fragments"][1:] = reversed(
                    batch["assertions"][0]["source_fragments"][1:]
                )
            elif change == "span":
                batch["assertions"][0]["source_fragments"][1]["span_id"] = "missing"
            elif change == "context":
                batch["contexts"][0]["value"]["source_expression"] = "an invented continuation"
            else:
                text = text.replace(
                    "[The sentence continues on the next page.]", "# Another observation"
                )
                sha = hashlib.sha256(text.encode()).hexdigest()
                spans[0]["edition_sha256"] = batch["edition_sha256"] = sha
                batch["interval_sha256"] = hashlib.sha256(text.rstrip("\n").encode()).hexdigest()
                for segment in batch["basis"]["page_segments"]:
                    segment["witness_sha256"] = sha
                batch["contexts"][0]["value"]["source_expression"] = "Another observation"
            with self.subTest(change=change), self.assertRaises(ValueError):
                compile_catalogue([batch], {10: text}, spans)

    def test_written_half_degree_keeps_literal_addends_and_exact_value(self):
        text, spans, batch = self.fixture()
        text = "20^g^ and a half\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans[0].update(edition_sha256=sha, line_end=1)
        batch.update(
            edition_sha256=sha,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip().encode()).hexdigest(),
            contexts=[],
        )
        batch["basis"] = dict(kind="final_edition_review", printed_page=21)
        a = dict(
            key="distance",
            line=1,
            span_id="s",
            source_expression="20^g^ and a half",
            quantity="angular_separation",
            role="recorded_reading",
            subject="Mars",
            reference="Regulus",
            direction=None,
            components={"degree": "20 1/2"},
            source_word_numbers={"half": "1/2"},
            source_component_addends={"degree": ["20", "1/2"]},
            unit_basis="Whole degrees and a stated half degree",
        )
        batch["assertions"] = [a]
        try:
            result = compile_catalogue([batch], {10: text}, spans)
        except ValueError as error:
            self.fail(f"Written mixed fraction must stay exact: {error}")
        self.assertEqual(result["assertions"][0]["normalized"]["magnitude"], "73800")
        for addends in (
            {"degree": ["20", "1/3"]},
            {"arcminute": ["20", "1/2"]},
            {"degree": ["20"]},
            {},
        ):
            bad = copy.deepcopy(batch)
            bad["assertions"][0]["source_component_addends"] = addends
            with self.subTest(addends=addends), self.assertRaises(ValueError):
                compile_catalogue([bad], {10: text}, spans)

    def test_leovitius_latitude_keeps_named_ephemeris_attribution(self):
        row = dict(
            id="assertion-v10-00000000000000000000",
            volume=10,
            printed_page=22,
            quantity="ecliptic_latitude",
            role="historical_prediction",
            subject="Mars",
            reference=None,
            direction="north",
            model_name="Leovitius",
            event_id=None,
            components={"degree": "3", "arcminute": "30"},
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        try:
            result = public_assertion(row)
        except ValueError as error:
            self.fail(f"Named source ephemeris must retain its attribution: {error}")
        self.assertEqual(result["model_name"], "Leovitius")
        self.assertEqual(result["normalized"]["signed_magnitude"], "12600")

    def test_continued_upper_bound_is_a_complete_angle_without_becoming_a_reading(self):
        text = "| Mars | 19 40 |\n— or a little more, yet not beyond 45.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=2)]
        context = dict(
            key="bound",
            kind="source_observation_context",
            lines=[2],
            value=dict(record_type="source_continuation", source_expression="not beyond 45"),
        )
        row = dict(
            key="upper",
            line=1,
            span_id="s",
            source_expression="19",
            source_fragments=[
                dict(line=1, span_id="s", source_expression="19"),
                dict(line=2, span_id="s", source_expression="45"),
            ],
            source_continuation_context_key="bound",
            context_keys=["bound"],
            quantity="angular_separation",
            role="historical_input",
            subject="Mars",
            reference="heart of Leo",
            direction=None,
            components={"degree": "19", "arcminute": "45"},
            unit_basis="Continued degree/minute bound",
            flags=["source_upper_bound", "not_an_additional_raw_reading"],
        )
        batch = dict(
            id="bound",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            interval_sha256=hashlib.sha256(text.rstrip().encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=22),
            contexts=[context],
            assertions=[row],
            span_decisions=[
                dict(span_id="s", decision="include", reason="Explicit source upper bound")
            ],
        )
        try:
            result = compile_catalogue([batch], {10: text}, spans)
        except ValueError as error:
            self.fail(f"Tail continuation must preserve the complete bound: {error}")
        out = public_assertion(result["assertions"][0])
        self.assertEqual(out["normalized"]["magnitude"], "71100")
        self.assertEqual(out["role"], "historical_input")


if __name__ == "__main__":
    unittest.main()
