import copy, hashlib, unittest
from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion, public_derivation


class HistoricalScaleCyclesTests(unittest.TestCase):
    def difference_fixture(self):
        text = "40 19 35\n40 20 0\n359 59 35\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=3)
        assertions = [
            dict(
                key=key,
                line=line,
                span_id="s",
                source_expression=text.splitlines()[line - 1],
                quantity="right_ascension",
                subject="Jupiter",
                reference=None,
                direction=None,
                role="reduction",
                components=dict(
                    zip(
                        ("degree", "arcminute", "arcsecond"),
                        text.splitlines()[line - 1].split(),
                        strict=True,
                    )
                ),
                flags=["not_an_additional_raw_reading"],
                unit_basis="Printed angular right ascensions",
            )
            for key, line in [("first", 1), ("second", 2), ("result", 3)]
        ]
        batch = dict(
            id="difference-wrap-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=3,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=432),
            span_decisions=[
                dict(span_id="s", decision="include", reason="Source circular subtraction")
            ],
            assertions=assertions,
            events=[],
            derivations=[
                dict(
                    key="wrap",
                    input_keys=["first", "second"],
                    output_key="result",
                    operation="difference_modulo_360_degrees",
                    basis="Explicit circular right-ascension subtraction",
                )
            ],
        )
        return text, span, batch

    def test_right_ascension_subtraction_can_wrap_without_changing_printed_values(self):
        text, span, batch = self.difference_fixture()
        compiled = compile_catalogue([batch], {12: text}, [span])
        d = compiled["derivations"][0]
        self.assertEqual((d["computed_magnitude"], d["arithmetic_agrees"]), ("1295975", True))
        public_derivation(d, {a["id"]: a for a in compiled["assertions"]})
        batch["derivations"][0]["operation"] = "difference"
        linear = compile_catalogue([batch], {12: text}, [span])["derivations"][0]
        self.assertEqual(
            (linear["computed_magnitude"], linear["arithmetic_agrees"]), ("-25", False)
        )
        self.assertEqual(batch["assertions"][-1]["source_expression"], "359 59 35")

    def test_circular_subtraction_requires_two_angular_inputs_and_verified_arithmetic(self):
        text, span, batch = self.difference_fixture()
        invalid = copy.deepcopy(batch)
        invalid["derivations"][0]["input_keys"] = ["first"]
        with self.assertRaises(ValueError):
            compile_catalogue([invalid], {12: text}, [span])
        invalid = copy.deepcopy(batch)
        for a in invalid["assertions"]:
            a.update(
                quantity="recorded_clock",
                components=dict(
                    zip(("hour", "minute", "second"), a["source_expression"].split(), strict=True)
                ),
            )
        with self.assertRaises(ValueError):
            compile_catalogue([invalid], {12: text}, [span])
        compiled = compile_catalogue([batch], {12: text}, [span])
        d = compiled["derivations"][0]
        aa = {a["id"]: a for a in compiled["assertions"]}
        with self.assertRaises(ValueError):
            public_derivation(dict(d, computed_magnitude="25"), aa)
        with self.assertRaises(ValueError):
            public_derivation(dict(d, input_ids=d["input_ids"][:1]), aa)
        clocks = copy.deepcopy(aa)
        for a in clocks.values():
            a["normalized"]["unit"] = "second_of_time"
        with self.assertRaises(ValueError):
            public_derivation(d, clocks)

    def row(self, q, parts, **extra):
        row = dict(
            id="assertion-v12-" + "1" * 20,
            volume=12,
            printed_page=308,
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

    def test_eccentricity_scale_retains_both_printed_operands(self):
        for part, want in (("12", "1/5"), ("9 1/2", "19/120")):
            row = self.row(
                "source_scale_ratio",
                dict(source_part=part, reference_scale="60"),
                subject="Mars calculation",
                source_parameter_kind="eccentricity_as_stated",
            )
            try:
                out = public_assertion(row)
            except ValueError as error:
                self.fail("Explicit historical eccentricity scale must export: " + str(error))
            self.assertEqual(out["normalized"]["magnitude"], want)
            self.assertEqual(out["normalized"]["source_reference_scale"], "60")
            self.assertIsNone(out["normalized"]["magnitude_degrees"])
            bad = copy.deepcopy(row)
            bad["reference"] = "Earth"
            with self.assertRaises(ValueError):
                public_assertion(bad)

    def test_source_count_wrap_is_checked_only_as_an_explicit_circular_sum(self):
        text = "11 27 44 23\n6 45\n0 4 29 23\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=3)
        base = dict(
            span_id="s",
            quantity="calculation_angle",
            subject="Mars",
            reference=None,
            direction=None,
            role="calculation_intermediate",
            flags=["not_an_additional_raw_reading"],
            unit_basis="Native circular count wrap",
        )
        specs = [
            ("original", 1, dict(sign_count="11", degree="27", arcminute="44", arcsecond="23")),
            ("offset", 2, dict(degree="6", arcminute="45")),
            ("result", 3, dict(sign_count="0", degree="4", arcminute="29", arcsecond="23")),
        ]
        assertions = [
            dict(
                base,
                key=key,
                line=line,
                source_expression=text.splitlines()[line - 1],
                components=parts,
                **(
                    dict(argument_name="latitude_argument", source_angular_count_unit="sign_count")
                    if "sign_count" in parts
                    else {}
                ),
            )
            for key, line, parts in specs
        ]
        batch = dict(
            id="wrap-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=3,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=308),
            span_decisions=[dict(span_id="s", decision="include", reason="Native wrap")],
            assertions=assertions,
            events=[],
            derivations=[
                dict(
                    key="wrap",
                    input_keys=["original", "offset"],
                    output_key="result",
                    operation="sum_modulo_360_degrees",
                    basis="Explicit source cyclic addition",
                )
            ],
        )
        compiled = compile_catalogue([batch], {12: text}, [span])
        self.assertIs(compiled["derivations"][0]["arithmetic_agrees"], True)
        self.assertEqual(compiled["derivations"][0]["computed_magnitude"], "16163")
        try:
            out = public_assertion(
                next(a for a in compiled["assertions"] if "sign_count" in a["components"])
            )
            public_derivation(
                compiled["derivations"][0], {a["id"]: a for a in compiled["assertions"]}
            )
        except ValueError as error:
            self.fail("Source count arguments must export: " + str(error))
        self.assertEqual(out["source_angular_count_unit"], "sign_count")
        self.assertEqual(
            normalize_quantity(
                dict(quantity="calculation_angle", components={"sign_count": "10", "degree": "30"})
            )["magnitude_degrees"],
            "330",
        )
        batch["derivations"][0]["operation"] = "sum"
        self.assertIs(
            compile_catalogue([batch], {12: text}, [span])["derivations"][0]["arithmetic_agrees"],
            False,
        )

    def test_uncertain_sign_and_unquantified_parallax_remain_explicit(self):
        candidate = self.row(
            "ecliptic_longitude",
            dict(degree="3", arcminute="55"),
            source_zodiac_candidate="Scorpio",
            flags=["not_an_additional_raw_reading", "source_zodiac_identification_uncertain"],
        )
        pending = self.row(
            "ecliptic_latitude",
            dict(degree="3", arcminute="37 1/2"),
            direction="north",
            source_coordinate_state="parallax_adjustment_pending_as_stated",
            flags=["not_an_additional_raw_reading", "historical_parallax_not_detection"],
        )
        try:
            c, p = public_assertion(candidate), public_assertion(pending)
        except ValueError as error:
            self.fail("Source qualifications must export: " + str(error))
        self.assertEqual(c["source_zodiac_candidate"], "Scorpio")
        self.assertNotIn("zodiac_longitude_degrees", c["normalized"])
        self.assertEqual(p["source_coordinate_state"], "parallax_adjustment_pending_as_stated")
        self.assertNotIn("correction_value", p)
        for row, change in (
            (candidate, {"role": "recorded_coordinate"}),
            (pending, {"role": "reduction"}),
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
