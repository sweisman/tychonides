import copy
import hashlib
import unittest

from src.catalog import compile_catalogue
from src.public_checkpoint import public_assertion, validate_links


class CrossReviewCalculations(unittest.TestCase):
    def fixture(self):
        text = "H.5 M.44\nMercury decl.4 19½\nAdd refraction4\nTrue decl.4 23½\nMars decl.8 31½\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [
            dict(id="s" + str(i), volume=12, edition_sha256=sha, line_start=i, line_end=i)
            for i in range(1, 6)
        ]

        def assertion(key, line, expr, quantity, components, subject="Mercury"):
            return dict(
                key=key,
                line=line,
                span_id="s" + str(line),
                source_expression=expr,
                quantity=quantity,
                components=components,
                subject=subject,
                reference=None,
                role="historical_input",
                direction=None,
                flags=[],
                unit_basis="Reviewed calculation units",
            )

        epoch = assertion(
            "epoch",
            1,
            "H.5 M.44",
            "calculation_epoch",
            {"hour": "5", "minute": "44"},
            "calculation epoch",
        )
        original = assertion(
            "original", 2, "4 19½", "declination", {"degree": "4", "arcminute": "19½"}
        )
        correction = assertion("correction", 3, "4", "refraction_angle", {"arcminute": "4"})
        result = assertion("result", 4, "4 23½", "declination", {"degree": "4", "arcminute": "23½"})
        result["role"] = "reduction"
        result["calculation_epoch_ref"] = dict(
            review_id="a-prior",
            key="epoch",
            basis="Explicit continuation of the preceding reduction",
        )
        result["event_key"] = "continued"
        mars = assertion(
            "mars", 5, "8 31½", "declination", {"degree": "8", "arcminute": "31½"}, "Mars"
        )

        def batch(rid, start, end, assertions):
            return dict(
                id=rid,
                volume=12,
                edition_sha256=sha,
                line_start=start,
                line_end=end,
                interval_sha256=hashlib.sha256(
                    "\n".join(text.splitlines()[start - 1 : end]).encode()
                ).hexdigest(),
                basis=dict(kind="scan_review", printed_page=225 if start == 1 else 226),
                span_decisions=[
                    dict(
                        span_id="s" + str(i),
                        decision="include",
                        reason="Source units and continuation reviewed",
                    )
                    for i in range(start, end + 1)
                ],
                assertions=assertions,
                contexts=[],
                events=[],
                derivations=[],
            )

        prior = batch("a-prior", 1, 2, [epoch, original])
        following = batch("b-following", 3, 5, [correction, result, mars])
        following["events"] = [
            dict(
                key="continued",
                line=4,
                clock_key=None,
                epoch_ref=copy.deepcopy(result["calculation_epoch_ref"]),
            )
        ]
        following["derivations"] = [
            dict(
                key="continued-sum",
                operation="sum",
                output_key="result",
                input_refs=[
                    dict(
                        review_id="a-prior",
                        key="original",
                        basis="Same continued declination calculation",
                    ),
                    dict(key="correction"),
                ],
            )
        ]
        return text, spans, prior, following

    def test_continuation_links_the_original_epoch_without_repeating_it(self):
        text, spans, prior, following = self.fixture()
        result = compile_catalogue([following, prior], {12: text}, spans)
        epoch = next(a for a in result["assertions"] if a["key"] == "epoch")
        output = next(a for a in result["assertions"] if a["key"] == "result")
        self.assertEqual(len(result["assertions"]), 5)
        self.assertEqual(output["calculation_epoch_id"], epoch["id"])
        self.assertEqual(result["events"][0]["epoch_assertion_id"], epoch["id"])
        self.assertIsNone(result["events"][0]["clock_assertion_id"])
        validate_links([public_assertion(a) for a in result["assertions"]], result["events"])

    def test_cross_review_arithmetic_uses_the_existing_quantity_identity(self):
        text, spans, prior, following = self.fixture()
        result = compile_catalogue([prior, following], {12: text}, spans)
        original = next(a for a in result["assertions"] if a["key"] == "original")
        derivation = result["derivations"][0]
        self.assertEqual(derivation["input_ids"][0], original["id"])
        self.assertEqual(derivation["computed_magnitude"], "15810")
        self.assertIs(derivation["arithmetic_agrees"], True)

    def validation_fixture(self):
        text, spans, prior, following = self.fixture()
        validation = copy.deepcopy(following)
        validation.update(
            id="z-validation", assertions=[], events=[], contexts=[], span_decisions=[]
        )
        validation["derivations"] = [
            dict(
                key="validate-existing-result",
                operation="sum",
                input_refs=[
                    dict(review_id="a-prior", key="original", basis="Reviewed original input"),
                    dict(
                        review_id="b-following",
                        key="correction",
                        basis="Reviewed correction amount",
                    ),
                ],
                output_ref=dict(
                    review_id="b-following",
                    key="result",
                    basis="Existing printed corrected result; do not duplicate it",
                ),
            )
        ]
        return text, spans, prior, following, validation

    def test_later_validation_can_reference_an_existing_output_without_rewriting_reviews(self):
        text, spans, prior, following, validation = self.validation_fixture()
        before = copy.deepcopy([prior, following])
        compiled = compile_catalogue([prior, following, validation], {12: text}, spans)
        self.assertEqual(len(compiled["assertions"]), 5)
        result = next(a for a in compiled["assertions"] if a["key"] == "result")
        check = next(d for d in compiled["derivations"] if d["review_id"] == "z-validation")
        self.assertEqual(check["output_id"], result["id"])
        self.assertEqual(check["computed_magnitude"], "15810")
        self.assertIs(check["arithmetic_agrees"], True)
        self.assertEqual([prior, following], before)
        from src.public_checkpoint import public_derivation

        public_derivation(check, {a["id"]: a for a in compiled["assertions"]})

    def test_external_output_requires_one_bound_explained_same_edition_reference(self):
        text, spans, prior, following, validation = self.validation_fixture()
        for change in [dict(review_id="missing"), dict(key="missing"), dict(basis="")]:
            bad = copy.deepcopy(validation)
            bad["derivations"][0]["output_ref"].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                compile_catalogue([prior, following, bad], {12: text}, spans)
        bad = copy.deepcopy(validation)
        bad["derivations"][0]["output_key"] = "result"
        with self.assertRaises(ValueError):
            compile_catalogue([prior, following, bad], {12: text}, spans)
        bad = copy.deepcopy(validation)
        bad["volume"] = 11
        local = copy.deepcopy(following["assertions"][0])
        local["span_id"] = "other-s3"
        bad["assertions"] = [local]
        bad["derivations"][0]["input_refs"] = [dict(key="correction")]
        other_spans = [dict(s, volume=11, id="other-" + s["id"]) for s in spans[2:]]
        with self.assertRaises(ValueError):
            compile_catalogue([prior, following, bad], {11: text, 12: text}, [*spans, *other_spans])

    def test_unbound_or_unexplained_external_references_are_rejected(self):
        text, spans, prior, following = self.fixture()
        for mutation in ({"review_id": "missing"}, {"key": "missing"}, {"basis": ""}):
            bad = copy.deepcopy(following)
            bad["assertions"][1]["calculation_epoch_ref"].update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                compile_catalogue([prior, bad], {12: text}, spans)

    def test_a_declination_cannot_supply_the_continuation_epoch(self):
        text, spans, prior, following = self.fixture()
        following["assertions"][1]["calculation_epoch_ref"]["key"] = "original"
        with self.assertRaises(ValueError):
            compile_catalogue([prior, following], {12: text}, spans)

    def test_competing_local_and_external_epoch_links_are_rejected(self):
        text, spans, prior, following = self.fixture()
        following["assertions"][1]["calculation_epoch_key"] = "correction"
        with self.assertRaises(ValueError):
            compile_catalogue([prior, following], {12: text}, spans)

    def test_references_cannot_silently_cross_edition_or_volume_boundaries(self):
        text, spans, prior, following = self.fixture()
        other = copy.deepcopy(prior)
        other["volume"] = 11
        other_spans = [dict(s, volume=11, id="other-" + s["id"]) for s in spans[:2]]
        for a in other["assertions"]:
            a["span_id"] = "other-" + a["span_id"]
        for d in other["span_decisions"]:
            d["span_id"] = "other-" + d["span_id"]
        with self.assertRaises(ValueError):
            compile_catalogue([other, following], {11: text, 12: text}, [*other_spans, *spans[2:]])

    def test_incomplete_angular_value_exports_a_known_unit_and_no_guessed_number(self):
        text = "Mercury latitude1 34 2/[numeral:?]\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="incomplete", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        assertion = dict(
            key="latitude",
            line=1,
            span_id="incomplete",
            source_expression="1 34 2/[numeral:?]",
            quantity="ecliptic_latitude",
            role="reduction",
            subject="Mercury",
            reference=None,
            direction="north",
            components=None,
            incomplete=True,
            flags=[],
            unit_basis="Degrees and arcminutes; denominator unresolved",
        )
        batch = dict(
            id="incomplete",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="scan_review", printed_page=226),
            span_decisions=[
                dict(
                    span_id="incomplete",
                    decision="include",
                    reason="Retain incomplete source value",
                )
            ],
            assertions=[assertion],
            events=[],
            contexts=[],
            derivations=[],
        )
        result = compile_catalogue([batch], {12: text}, [span])["assertions"][0]
        self.assertEqual(result["normalized"]["unit"], "arcsecond")
        exported = public_assertion(result)
        self.assertEqual(exported["normalized"]["status"], "incomplete")
        for key in ("magnitude", "magnitude_degrees", "signed_magnitude"):
            self.assertIsNone(exported["normalized"][key])
        guessed = copy.deepcopy(result)
        guessed["normalized"]["magnitude"] = "5680"
        with self.assertRaises(ValueError):
            public_assertion(guessed)
