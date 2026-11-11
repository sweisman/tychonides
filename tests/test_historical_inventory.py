import tempfile
import unittest
from pathlib import Path

from src.historical_inventory import inventory_sources


class HistoricalInventoryTests(unittest.TestCase):
    def test_opted_angular_block_collects_marked_subunits_and_complete_fractions(self):
        import copy
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.prose_selection_fixture(
                Path(directory), "Angle 12° 30′; correction 18′ 51″; add 1/2″; another 7′ 42″."
            )
            review["assertion_defaults"].update(
                quantity="calculation_angle",
                role="calculation_intermediate",
                flags=["not_an_additional_raw_reading"],
                context_keys=["calculation"],
            )
            review["contexts"] = [
                dict(
                    key="calculation",
                    kind="source_observation_context",
                    lines=[1],
                    value=dict(record_type="source_worked_calculation"),
                )
            ]
            review["cell_groups"] = [
                dict(
                    calculation_angles=True,
                    line_range=[1, 1],
                    worded_component_sequences=[
                        ["arcminute", "arcsecond"],
                        ["arcminute"],
                        ["arcsecond"],
                    ],
                )
            ]
            _, old, _ = compile_reviews(work, [copy.deepcopy(review)])
            review["cell_groups"][0]["marked_subunits"] = True
            _, compiled, _ = compile_reviews(work, [review])
            rows = sorted(compiled["assertions"], key=lambda row: row["char_start"])
            self.assertEqual(
                [r["source_expression"] for r in rows], ["12° 30′", "18′ 51″", "1/2″", "7′ 42″"]
            )
            self.assertEqual(
                [r["normalized"]["magnitude"] for r in rows], ["45000", "1131", "1/2", "462"]
            )
            self.assertEqual(rows[0], old["assertions"][0])
            self.assertTrue(all("marked_subunits" not in row for row in rows))

    def test_marked_subunit_block_requires_review_of_clocks_sign_counts_and_partial_numbers(self):
        from src.historical_reviews import compile_reviews

        for literal in (
            "At hour 4, offset 18′ 51″.",
            "At 4h 30′, offset 18′.",
            "At 1^h^ 30^m^, offset 18′.",
            "Full 4 complete signs and 25°.",
            "Total 24,480°; correction 18′.",
            "12′ [recte: 13′]",
            "1 /2″",
        ):
            with self.subTest(literal=literal), tempfile.TemporaryDirectory() as directory:
                work, review = self.prose_selection_fixture(Path(directory), literal)
                review["assertion_defaults"].update(
                    quantity="calculation_angle",
                    role="historical_input",
                    flags=["not_an_additional_raw_reading"],
                    context_keys=["calculation"],
                )
                review["contexts"] = [
                    dict(
                        key="calculation",
                        kind="source_observation_context",
                        lines=[1],
                        value=dict(record_type="source_worked_calculation"),
                    )
                ]
                review["cell_groups"] = [
                    dict(
                        calculation_angles=True,
                        marked_subunits=True,
                        line_range=[1, 1],
                        worded_component_sequences=[["degree"], ["arcminute"], ["arcsecond"]],
                    )
                ]
                with self.assertRaisesRegex(ValueError, "explicit review"):
                    compile_reviews(work, [review])

    def test_reviewed_table_rows_preserve_labels_and_explicit_sign_column(self):
        import copy
        import hashlib
        from src.catalog import compile_catalogue
        from src.review_preparation import materialize_review

        text = "| 1 | Pole star [Stella polaris] | 6 | 42 | Aries |\n| 99 | Northern tail of Whale | 0 | 13 | Aries |\n"
        sid = "longomontanus-astronomia-danica"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", source_id=sid, edition_sha256=sha, line_start=1, line_end=2)]
        recipe = dict(
            id="transit-table",
            source_id=sid,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            basis=dict(kind="final_edition_review", printed_page=1),
            assertion_defaults=dict(
                quantity="ecliptic_longitude",
                role="historical_input",
                subject="ecliptic point",
                reference=None,
                direction=None,
                column=None,
                flags=["not_an_additional_raw_reading"],
                unit_basis="Reviewed degree/minute columns for calculated transit geometry",
            ),
            cell_groups=[
                dict(
                    source_columns=[3, 4],
                    component_units=["degree", "arcminute"],
                    line_range=[1, 2],
                    zodiac_sign="Aries",
                    row_context=dict(
                        key_prefix="transit-row",
                        columns={"native_index": 1, "reference_star_as_printed": 2},
                        zodiac_sign_column=5,
                    ),
                )
            ],
        )
        materialized = materialize_review(recipe, text, spans)
        self.assertEqual(len(materialized.get("contexts", [])), 4)
        context = next(c for c in materialized["contexts"] if c["key"] == "transit-row-1")
        self.assertEqual(context["lines"], [1])
        self.assertEqual(context["value"]["native_index"], "1")
        self.assertEqual(
            context["value"]["reference_star_as_printed"], "Pole star [Stella polaris]"
        )
        self.assertEqual(
            context["value"]["source_columns"], {"native_index": 1, "reference_star_as_printed": 2}
        )
        rows = compile_catalogue([materialized], {sid: text}, spans)["assertions"]
        rows.sort(key=lambda row: row["line"])
        self.assertEqual([r["normalized"]["magnitude"] for r in rows], ["24120", "780"])
        self.assertEqual(
            [r["normalized"]["zodiac_longitude_degrees"] for r in rows], ["67/10", "13/60"]
        )
        self.assertTrue(
            all(r["subject"] == "ecliptic point" and r["reference"] is None for r in rows)
        )
        self.assertTrue(all("row_context" not in r for r in rows))
        defaults = copy.deepcopy(recipe)
        defaults["assertion_defaults"]["row_context"] = defaults["cell_groups"][0].pop(
            "row_context"
        )
        self.assertEqual(materialize_review(defaults, text, spans), materialized)
        reused = copy.deepcopy(recipe)
        reused["contexts"] = copy.deepcopy(materialized["contexts"])
        self.assertEqual(materialize_review(reused, text, spans), materialized)
        conflicting = copy.deepcopy(reused)
        conflicting["contexts"][0]["value"]["reference_star_as_printed"] = "Other star"
        with self.assertRaisesRegex(ValueError, "Conflicting reviewed table row context"):
            materialize_review(conflicting, text, spans)
        baseline = copy.deepcopy(recipe)
        baseline["cell_groups"][0].pop("row_context")
        baseline["cell_groups"][0].pop("zodiac_sign")
        old = compile_catalogue([materialize_review(baseline, text, spans)], {sid: text}, spans)[
            "assertions"
        ]
        old.sort(key=lambda row: row["line"])
        for before, after in zip(old, rows, strict=True):
            for key in ("id", "key", "components", "source_expression", "char_start", "char_end"):
                self.assertEqual(before[key], after[key])
        for change in (
            {"columns": {"star": 9}},
            {"columns": {"record_type": 2}},
            {"key_prefix": "bad prefix"},
            {"zodiac_sign_column": True},
        ):
            bad = copy.deepcopy(recipe)
            bad["cell_groups"][0]["row_context"].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                materialize_review(bad, text, spans)
        bad = copy.deepcopy(recipe)
        bad["cell_groups"][0]["zodiac_sign"] = "Taurus"
        with self.assertRaises(ValueError):
            compile_catalogue([materialize_review(bad, text, spans)], {sid: text}, spans)

    def test_shared_literal_variant_is_independent_of_compiled_row_order(self):
        from unittest.mock import patch
        from src.catalog import compile_catalogue
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.prose_selection_fixture(Path(directory), "Position 18° 30′ [Leo].")
            review["assertion_defaults"].update(
                quantity="ecliptic_longitude",
                role="historical_input",
                flags=["not_an_additional_raw_reading"],
            )
            review["contexts"] = [
                dict(
                    key="frame",
                    kind="source_coordinate_frame",
                    lines=[1],
                    value=dict(
                        subject="Sun",
                        zodiac_sign="Leo",
                        line_start=1,
                        line_end=1,
                        source_expression="[Leo]",
                    ),
                )
            ]
            review["cell_groups"] = [
                dict(
                    cells=[
                        dict(
                            key="parent",
                            line=1,
                            column=None,
                            expression_index=0,
                            flags=["zodiac_sign_unstated"],
                        ),
                        dict(
                            key="variant",
                            line=1,
                            column=None,
                            expression_index=0,
                            role="editorial_variant",
                            variant_of_key="parent",
                            annotation_of_key="parent",
                            zodiac_sign="Leo",
                            zodiac_sign_basis_key="frame",
                            context_keys=["frame"],
                            flags=[
                                "source_annotation_variant",
                                "alternative_suggestion_not_applied",
                            ],
                        ),
                    ]
                )
            ]

            def has_variant(record):
                return bool(record.get("variant_of_id"))

            for variants_first in (False, True):

                def ordered(*args, first=variants_first, **kwargs):
                    result = compile_catalogue(*args, **kwargs)
                    result["assertions"].sort(key=has_variant, reverse=first)
                    return result

                with (
                    self.subTest(variants_first=variants_first),
                    patch("src.historical_reviews.compile_catalogue", side_effect=ordered),
                ):
                    _, compiled, _ = compile_reviews(work, [review])
                    rows = {r["key"]: r for r in compiled["assertions"]}
                    self.assertEqual(len(rows), 2)
                    self.assertEqual(rows["variant"]["variant_of_id"], rows["parent"]["id"])
                    self.assertIsNone(rows["parent"]["normalized"].get("zodiac_longitude_degrees"))
                    self.assertEqual(
                        rows["variant"]["normalized"]["zodiac_longitude_degrees"], "277/2"
                    )
            unlinked = review["cell_groups"][0]["cells"][1]
            unlinked.pop("variant_of_key")
            unlinked.pop("annotation_of_key")
            unlinked["role"] = "historical_input"
            with self.assertRaisesRegex(ValueError, "Repeated source occurrence"):
                compile_reviews(work, [review])

    def test_reviewed_table_ranges_match_explicit_column_selections(self):
        import copy
        import hashlib
        from src.assembly import cell_intervals
        from src.catalog import compile_catalogue
        from src.review_preparation import materialize_review

        text = "| 0 | 12 | 30½ | 12 | 30½ |\n| 1 | 13 | 15 | 13 | 15 |\n"
        sid = "snellius-observationes-hassiacae"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", source_id=sid, edition_sha256=sha, line_start=1, line_end=2)]
        recipe = dict(
            id="range",
            source_id=sid,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            basis=dict(kind="final_edition_review", printed_page=1),
            included_span_starts=[1],
            assertion_defaults=dict(
                quantity="right_ascension",
                role="historical_input",
                subject="ecliptic",
                reference=None,
                unit_basis="Reviewed degree/minute columns",
            ),
            cell_groups=[
                dict(
                    line_range=[1, 2],
                    source_columns=columns,
                    component_units=["degree", "arcminute"],
                )
                for columns in ([2, 3], [4, 5])
            ],
        )
        explicit = copy.deepcopy(recipe)
        for group in explicit["cell_groups"]:
            del group["line_range"]
            group["cells"] = []
            for line, literal in enumerate(text.splitlines(), 1):
                columns = group["source_columns"]
                intervals = cell_intervals(literal, declared_table=True)
                left, right = intervals[columns[0] - 1][0], intervals[columns[-1] - 1][1]
                group["cells"].append(
                    dict(
                        line=line,
                        column=None,
                        source_expression=literal[left:right],
                        char_start=left,
                        char_end=right,
                        key=f"right_ascension-{line}-columns-{'-'.join(map(str, columns))}",
                    )
                )
        expanded = materialize_review(recipe, text, spans)
        self.assertEqual(expanded, materialize_review(explicit, text, spans))
        self.assertNotIn("line_range", expanded["assertions"][0])
        compiled = compile_catalogue([expanded], {sid: text}, spans)["assertions"]
        self.assertEqual(len({r["id"] for r in compiled}), 4)
        self.assertEqual(
            next(r for r in compiled if r["line"] == 1)["normalized"]["magnitude"], "45030"
        )
        for change in (
            dict(line_range=[True, 2]),
            dict(line_range=[2, 1]),
            dict(line_range=[0, 2]),
            dict(line_range=[1, 3]),
            dict(line_range=[1, 2], cells=[[1, 2]]),
            dict(source_columns=[2, 4]),
            dict(source_columns=[0, 1]),
            dict(source_columns=[2, 3], column=2),
        ):
            with self.subTest(change=change):
                bad = copy.deepcopy(recipe)
                bad["cell_groups"][0].update(change)
                with self.assertRaises(ValueError):
                    materialize_review(bad, text, spans)

    def test_reviewed_single_column_range_matches_existing_cells(self):
        import copy
        from src.review_preparation import materialize_review

        with tempfile.TemporaryDirectory() as directory:
            _, recipe = self.historical_review_fixture(Path(directory))
            spans = [dict(id="s", source_id=recipe["source_id"], line_start=1, line_end=1)]
            explicit = materialize_review(recipe, "| Sun | 12° 30′ |\n", spans)
            ranged = copy.deepcopy(recipe)
            ranged["cell_groups"][0].update(line_range=[1, 1], column=2)
            del ranged["cell_groups"][0]["cells"]
            self.assertEqual(materialize_review(ranged, "| Sun | 12° 30′ |\n", spans), explicit)

    def test_correction_group_subjects_follow_their_quantities_without_changing_observing_groups(
        self,
    ):
        import copy
        from src.historical_reviews import project_historical_events

        events = [
            dict(id="a", kind="source_correction_group", subject="fixed stars"),
            dict(id="b", kind="source_correction_group", subject="fixed stars"),
            dict(id="c", kind="source_correction_group", subject="fixed stars"),
            dict(id="d", kind="source_observation_group", subject="Mars"),
        ]
        original = copy.deepcopy(events)
        quantities = [
            dict(event_id="a", subject="ecliptic"),
            dict(event_id="a", subject="ecliptic"),
            dict(event_id="b", subject="Sun"),
            dict(event_id="b", subject="Moon"),
            dict(event_id="d", subject="Jupiter"),
        ]
        out = project_historical_events(events, quantities)
        self.assertEqual([e["subject"] for e in out], ["ecliptic", None, None, "Mars"])
        self.assertEqual(events, original)

    def test_subject_classification_review_preserves_numbers_and_requires_source_binding(self):
        import copy
        import hashlib
        import json
        from src.historical_reviews import apply_classification_reviews
        from src.normalization import normalize_quantity

        row = dict(
            id="a",
            source_id="book",
            line=1,
            quantity="right_ascension",
            role="historical_input",
            subject="fixed stars",
            reference=None,
            direction=None,
            source_expression="122 11 53",
            components={"degree": "122", "arcminute": "11", "arcsecond": "53"},
            flags=["not_an_additional_raw_reading"],
        )
        row["normalized"] = normalize_quantity(row)
        decision = dict(
            id="subject-correction",
            assertion_id="a",
            reason="The source labels ecliptic degrees.",
            original_sha256=hashlib.sha256(
                json.dumps(row, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest(),
            before={"subject": "fixed stars"},
            after={"subject": "ecliptic"},
            evidence=[
                dict(line=1, source_expression="read 122 11 53"),
                dict(line=2, source_expression="degrees of the ecliptic"),
            ],
        )
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for change in (
                None,
                {"after": {"subject": "unregistered object"}},
                {"after": {"subject": "ecliptic", "components": {}}},
                {"evidence": [dict(line=2, source_expression="degrees of the ecliptic")]},
            ):
                current = copy.deepcopy(decision)
                if change:
                    current.update(change)
                (work / "classification_reviews.json").write_text(
                    json.dumps([current]), encoding="utf-8"
                )
                item = copy.deepcopy(row)
                if change:
                    with self.assertRaises(ValueError):
                        apply_classification_reviews(
                            work,
                            {"assertions": [item]},
                            {"book": "read 122 11 53\ndegrees of the ecliptic"},
                        )
                else:
                    proof = apply_classification_reviews(
                        work,
                        {"assertions": [item]},
                        {"book": "read 122 11 53\ndegrees of the ecliptic"},
                    )
                    self.assertEqual(item, dict(row, subject="ecliptic"))
                    self.assertEqual(proof["a"]["before"], row)

    def test_native_word_occurrence_correction_preserves_reading_and_history(self):
        import hashlib
        import json
        from src.historical_reviews import append, run

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "book.md"
            text = "The single planets: Moon in single months.\n"
            source.write_text(text, encoding="utf-8")
            sid = "origanus-ephemerides-brandenburgicae"
            work = root / "work"
            inventory_sources([dict(source_id=sid, path=str(source))], work)
            start = text.index("single")
            review = dict(
                id="native-month",
                source_id=sid,
                edition_sha256=hashlib.sha256(text.encode()).hexdigest(),
                line_start=1,
                line_end=1,
                basis=dict(kind="final_edition_review", printed_page=1),
                contexts=[],
                events=[],
                included_span_starts=[1],
                assertion_defaults=dict(
                    quantity="source_scalar",
                    subject="calendar calculation",
                    reference=None,
                    direction=None,
                    role="historical_input",
                    flags=["not_an_additional_raw_reading"],
                    source_parameter_kind="source_month_count",
                    source_word_numbers={"single": "1"},
                    unit_basis="Source lunar traversal in single months.",
                ),
                cell_groups=[
                    dict(
                        component_units=["scalar"],
                        cells=[
                            dict(
                                key="month",
                                line=1,
                                column=None,
                                source_expression="single",
                                char_start=start,
                                char_end=start + 6,
                            )
                        ],
                    )
                ],
            )
            append(work, review)
            run(work)
            frozen = (work / "reviews.json").read_bytes()
            snapshot = (work / "compiled_assertions.json").read_bytes()
            row = json.loads(snapshot)[0]
            target = text.index("single months")
            correction = dict(
                id="native-month-occurrence",
                assertion_id=row["id"],
                reason="The lunar period uses the second word occurrence.",
                original_sha256=hashlib.sha256(
                    json.dumps(row, sort_keys=True, ensure_ascii=False).encode()
                ).hexdigest(),
                source_sha256=hashlib.sha256(text.encode()).hexdigest(),
                before=dict(char_start=start, char_end=start + 6),
                after=dict(char_start=target, char_end=target + 6),
                evidence=[dict(line=1, source_expression="Moon in single months")],
            )
            (work / "classification_reviews.json").write_text(
                json.dumps([correction]), encoding="utf-8"
            )
            proof = run(work)
            self.assertEqual(proof, run(work))
            fixed = json.loads((work / "compiled_assertions.json").read_text(encoding="utf-8"))[0]
            self.assertEqual(fixed, dict(row, char_start=target, char_end=target + 6))
            self.assertEqual((work / "reviews.json").read_bytes(), frozen)
            archive = (
                work / "recovery" / ("assertions-" + hashlib.sha256(snapshot).hexdigest() + ".json")
            )
            self.assertEqual(archive.read_bytes(), snapshot)
            self.assertEqual(source.read_text(encoding="utf-8"), text)

    def test_native_word_occurrence_correction_rejects_unbound_or_changed_meaning(self):
        import copy
        import hashlib
        import json
        from src.historical_reviews import apply_classification_reviews

        text = "The single planets in single days; Moon in single months."
        start, target = text.index("single"), text.index("single months")
        row = dict(
            id="a",
            source_id="book",
            line=1,
            column=None,
            source_expression="single",
            source_word_numbers={"single": "1"},
            quantity="source_scalar",
            source_parameter_kind="source_month_count",
            char_start=start,
            char_end=start + 6,
            components={"scalar": "1"},
            normalized={"magnitude": "1"},
        )
        correction = dict(
            id="occurrence",
            assertion_id="a",
            reason="Explicit lunar month wording",
            original_sha256=hashlib.sha256(
                json.dumps(row, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest(),
            source_sha256=hashlib.sha256(text.encode()).hexdigest(),
            before=dict(char_start=start, char_end=start + 6),
            after=dict(char_start=target, char_end=target + 6),
            evidence=[dict(line=1, source_expression="Moon in single months")],
        )
        wrong_unit = text.index("single days")
        changes = [
            {"source_sha256": "0" * 64},
            {"after": dict(char_start=wrong_unit, char_end=wrong_unit + 6)},
            {"after": dict(char_start=target + 1, char_end=target + 6)},
            {"after": dict(char_start=target, char_end=target + 6, components={"scalar": "9"})},
            {"evidence": [dict(line=1, source_expression="single planets")]},
            {"after": dict(char_start=True, char_end=target + 6)},
        ]
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for change in changes:
                with self.subTest(change=change):
                    decision = dict(correction, **change)
                    (work / "classification_reviews.json").write_text(
                        json.dumps([decision]), encoding="utf-8"
                    )
                    with self.assertRaises(ValueError):
                        apply_classification_reviews(
                            work, {"assertions": [copy.deepcopy(row)]}, {"book": text}
                        )

    def test_source_qualification_review_adds_flags_without_changing_reading(self):
        import hashlib
        import json
        from src.historical_reviews import apply_classification_reviews

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            row = dict(
                id="a",
                source_id="book",
                line=1,
                source_expression="6",
                components={"scalar": "6"},
                normalized={"magnitude": "6"},
                flags=["not_an_additional_raw_reading"],
            )
            original = dict(row)
            decision = dict(
                id="source-bound",
                assertion_id="a",
                reason="Explicit native lower bound",
                original_sha256=hashlib.sha256(
                    json.dumps(row, sort_keys=True, ensure_ascii=False).encode()
                ).hexdigest(),
                before={"flags": row["flags"]},
                after={"flags": row["flags"] + ["source_lower_bound"]},
                evidence=[dict(line=1, source_expression="at least 6 times")],
            )
            (work / "classification_reviews.json").write_text(
                json.dumps([decision]), encoding="utf-8"
            )
            proof = apply_classification_reviews(
                work, {"assertions": [row]}, {"book": "at least 6 times"}
            )
            self.assertEqual(proof["a"]["before"], original)
            self.assertEqual(
                row, dict(original, flags=["not_an_additional_raw_reading", "source_lower_bound"])
            )

    def test_source_qualification_review_rejects_unbound_or_destructive_changes(self):
        import copy
        import hashlib
        import json
        from src.historical_reviews import apply_classification_reviews

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            row = dict(
                id="a",
                source_id="book",
                line=1,
                source_expression="6",
                components={"scalar": "6"},
                normalized={"magnitude": "6"},
                flags=["not_an_additional_raw_reading"],
            )
            base = dict(
                id="source-bound",
                assertion_id="a",
                reason="Explicit native bound",
                original_sha256=hashlib.sha256(
                    json.dumps(row, sort_keys=True, ensure_ascii=False).encode()
                ).hexdigest(),
                before={"flags": row["flags"]},
                after={"flags": row["flags"] + ["source_lower_bound"]},
                evidence=[dict(line=1, source_expression="at least 6 times")],
            )
            for change in (
                {"after": {"flags": ["source_lower_bound"]}},
                {"after": {"flags": row["flags"] + ["source_lower_bound", "source_lower_bound"]}},
                {"after": {"flags": row["flags"] + ["source_lower_bound", "source_upper_bound"]}},
                {"after": {"flags": row["flags"] + ["source_notation_unresolved"]}},
                {"after": {"flags": row["flags"] + ["unknown"]}},
                {"after": {"flags": "source_lower_bound"}},
                {
                    "after": {
                        "flags": row["flags"] + ["source_lower_bound"],
                        "normalized": {"magnitude": "999"},
                    }
                },
                {"original_sha256": "0" * 64},
                {"evidence": [dict(line=2, source_expression="at least 7 times")]},
                {"evidence": [dict(line=1, source_expression="at least")]},
            ):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    decision = copy.deepcopy(base)
                    decision.update(change)
                    (work / "classification_reviews.json").write_text(
                        json.dumps([decision]), encoding="utf-8"
                    )
                    apply_classification_reviews(
                        work,
                        {"assertions": [copy.deepcopy(row)]},
                        {"book": "at least 6 times\nat least 7 times"},
                    )

    def test_cross_leaf_paragraph_keeps_review_scoped_page_loci(self):
        import copy
        from src import historical_reviews
        from src.public_context_projection import project_contexts, validate_projection

        sid = "brahe-progymnasmata-erara"
        reviews = [
            dict(id=r, source_id=sid, line_start=100, line_end=100, basis=dict(printed_page=p))
            for r, p in (("first", 374), ("second", 375))
        ]
        before = copy.deepcopy(reviews)
        provenance = historical_reviews.review_provenance(reviews, {})
        contexts = [
            dict(
                id=r,
                review_id=r,
                source_id=sid,
                edition_sha256="a" * 64,
                kind="source_observation_context",
                lines=[100],
                value=dict(source_line=100),
            )
            for r in ("first", "second")
        ]
        quantities = [
            dict(id="q-" + r, review_id=r, source_id=sid, line=100, printed_page=p)
            for r, p in (("first", 374), ("second", 375))
        ]
        projected, loci = project_contexts(contexts, provenance, quantities=quantities)
        self.assertEqual(len(loci), 2)
        by_id = {row["id"]: row for row in loci}
        for context, page in zip(projected, (374, 375), strict=True):
            locus = by_id[context["value"]["source_locus_id"]]
            self.assertEqual(locus["printed_page"], page)
            self.assertEqual(locus["quantity_ids"], ["q-" + context["id"]])
            self.assertEqual([c["context_id"] for c in locus["context_ids"]], [context["id"]])
        validate_projection(projected, loci, quantities, [])
        self.assertEqual(reviews, before)
        unknown = dict(contexts[0], id="unknown", review_id="unknown")
        with self.assertRaises(ValueError):
            project_contexts([unknown], provenance, quantities=quantities)
        conflicting = [dict(q, review_id="first") for q in quantities]
        with self.assertRaises(ValueError):
            project_contexts(contexts[:1], provenance, quantities=conflicting)

    def test_locator_projection_review_allows_only_fingerprinted_locator_changes(self):
        import copy
        import hashlib
        import json
        from src.historical_reviews import apply_locator_projection_reviews

        before = dict(
            id="quantity-one",
            source_page_locator=dict(
                source_pdf_page=41, printed_page_label="1", later_hand_page_label=None
            ),
            normalized=dict(magnitude="60"),
            printed_page=2,
        )
        after = copy.deepcopy(before)
        after["source_page_locator"].update(source_pdf_page=42, printed_page_label="2")
        correction = dict(
            assertion_id=before["id"],
            original_sha256=hashlib.sha256(
                json.dumps(before, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest(),
            before=before["source_page_locator"],
            after=after["source_page_locator"],
        )
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            path = work / "locator_projection_reviews.json"
            self.assertEqual(apply_locator_projection_reviews(work, [after]), {})
            review = dict(
                id="correct-page-projection",
                reason="Use the reviewed page segment",
                corrections=[correction],
            )
            path.write_text(json.dumps(review), encoding="utf-8")
            changes = apply_locator_projection_reviews(work, [after])
            self.assertEqual(changes[before["id"]], dict(before=before, after=after))
            changed_number = copy.deepcopy(after)
            changed_number["normalized"]["magnitude"] = "999"
            with self.assertRaisesRegex(ValueError, "Locator projection review"):
                apply_locator_projection_reviews(work, [changed_number])
            for replacements in (
                [dict(correction, assertion_id="missing")],
                [dict(correction, after=before["source_page_locator"])],
                [correction, correction],
            ):
                with self.subTest(replacements=replacements):
                    path.write_text(
                        json.dumps(dict(review, corrections=replacements)), encoding="utf-8"
                    )
                    with self.assertRaisesRegex(ValueError, "Locator projection review"):
                        apply_locator_projection_reviews(work, [after])

    def test_explicit_notation_materializes_components_through_shared_parser(self):
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.prose_selection_fixture(Path(directory), "Sun altitude p. 41/35.")
            review["cell_groups"] = [
                dict(
                    source_unit_notation="parts_slash_minutes",
                    cells=[dict(line=1, column=None, source_expression="p. 41/35")],
                )
            ]
            _, compiled, _ = compile_reviews(work, [review])
            row = compiled["assertions"][0]
            self.assertEqual(row["components"], {"degree": "41", "arcminute": "35"})
            self.assertEqual(row["normalized"]["magnitude"], "149700")

    def test_decimal_degree_selection_materializes_without_retyping_components(self):
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.prose_selection_fixture(Path(directory), "Altitude 34.5 degrees.")
            review["cell_groups"] = [
                dict(
                    source_unit_notation="decimal_degrees",
                    cells=[dict(line=1, column=None, source_expression="34.5 degrees")],
                )
            ]
            _, compiled, _ = compile_reviews(work, [review])
            row = compiled["assertions"][0]
            self.assertEqual(row["source_expression"], "34.5 degrees")
            self.assertEqual(row["components"], {"degree": "69/2"})
            self.assertEqual(row["normalized"]["magnitude"], "124200")

    def test_review_selects_staged_prose_occurrences_without_retyping_values(self):
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work, review = self.prose_selection_fixture(
                root, "Sun altitude 12° 30′; later 13° 15′."
            )
            review["cell_groups"][0]["cells"].append(dict(line=1, column=None, expression_index=1))
            _, compiled, _ = compile_reviews(work, [review])
            rows = sorted(compiled["assertions"], key=lambda r: r["char_start"])
            self.assertEqual([r["source_expression"] for r in rows], ["12° 30′", "13° 15′"])
            self.assertEqual(len({r["id"] for r in rows}), 2)
            self.assertTrue(all("expression_index" not in r for r in rows))

    def test_staged_prose_selector_rejects_partial_numeric_continuations(self):
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.prose_selection_fixture(
                Path(directory), "Distance 81° 31′ 3⅚ seconds."
            )
            with self.assertRaisesRegex(ValueError, "complete numerical expression"):
                compile_reviews(work, [review])

    def test_opt_in_angle_sequence_keeps_word_units_and_exact_mixed_fractions(self):
        from src.historical_reviews import compile_reviews

        for literal, units, expected in (
            ("25° 25½ minutes", ["degree", "arcminute"], "91530"),
            ("19° 0 ⅔ minutes", ["degree", "arcminute"], "68440"),
            ("52° / 48′", ["degree", "arcminute"], "190080"),
            ("53° / 42½′", ["degree", "arcminute"], "193350"),
            ("81° 31′ 3⅚ seconds", ["degree", "arcminute", "arcsecond"], "1760783/6"),
        ):
            with self.subTest(literal=literal), tempfile.TemporaryDirectory() as directory:
                work, review = self.prose_selection_fixture(Path(directory), literal + ".")
                group = review["cell_groups"][0]
                group["component_units"] = units
                group["cells"][0]["complete_angle_sequence"] = True
                _, compiled, _ = compile_reviews(work, [review])
                row = compiled["assertions"][0]
                self.assertEqual(row["source_expression"], literal)
                self.assertEqual(row["normalized"]["magnitude"], expected)
                self.assertNotIn("complete_angle_sequence", row)

    def test_worded_angle_completion_uses_numeric_fragments_without_retyping_values(self):
        from src.historical_reviews import compile_reviews

        for literal, units, expected in (
            ("24 degrees 32 minutes", ["degree", "arcminute"], "88320"),
            ("12 1/2 degrees 15 minutes", ["degree", "arcminute"], "45900"),
            ("40½ degrees", ["degree"], "145800"),
            ("34 minutes", ["arcminute"], "2040"),
            ("20 minutes 15 seconds", ["arcminute", "arcsecond"], "1215"),
            ("12 degrees 30 seconds", ["degree", "arcsecond"], "43230"),
            ("81 degrees 31 minutes 3⅚ seconds", ["degree", "arcminute", "arcsecond"], "1760783/6"),
            (
                "12 degrees, 30 minutes and 1/2 second",
                ["degree", "arcminute", "arcsecond"],
                "90001/2",
            ),
        ):
            with self.subTest(literal=literal), tempfile.TemporaryDirectory() as directory:
                work, review = self.prose_selection_fixture(Path(directory), literal + ".")
                review["cell_groups"][0].update(
                    component_units=units,
                    cells=[
                        dict(line=1, column=None, fragment_index=0, complete_angle_sequence=True)
                    ],
                )
                _, compiled, _ = compile_reviews(work, [review])
                row = compiled["assertions"][0]
                self.assertEqual(row["source_expression"], literal)
                self.assertEqual(row["normalized"]["magnitude"], expected)
                self.assertNotIn("fragment_index", row)
                self.assertNotIn("complete_angle_sequence", row)

    def test_calculation_block_collects_angles_without_changing_existing_selectors(self):
        import copy
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.prose_selection_fixture(
                Path(directory),
                "At hour 5¼: first 12° 30′; then 24 degrees 32 minutes; "
                "another 12° 30′; finally 34 minutes.",
            )
            review["assertion_defaults"].update(
                quantity="calculation_angle",
                role="calculation_intermediate",
                flags=["not_an_additional_raw_reading"],
                context_keys=["calculation"],
            )
            review["contexts"] = [
                dict(
                    key="calculation",
                    kind="source_observation_context",
                    lines=[1],
                    value=dict(record_type="source_worked_calculation"),
                )
            ]
            review["cell_groups"] = [dict(cells=[dict(line=1, column=None, expression_index=1)])]
            _, baseline, _ = compile_reviews(work, [copy.deepcopy(review)])
            review["cell_groups"] = [
                dict(
                    calculation_angles=True,
                    line_range=[1, 1],
                    worded_component_sequences=[["degree", "arcminute"], ["arcminute"]],
                )
            ]
            _, compiled, _ = compile_reviews(work, [review])
            rows = sorted(compiled["assertions"], key=lambda r: r["char_start"])
            self.assertEqual(
                [r["source_expression"] for r in rows],
                ["12° 30′", "24 degrees 32 minutes", "12° 30′", "34 minutes"],
            )
            self.assertEqual(
                [r["normalized"]["magnitude"] for r in rows], ["45000", "88320", "45000", "2040"]
            )
            self.assertEqual(rows[0], baseline["assertions"][0])
            self.assertEqual(len({r["id"] for r in rows}), 4)
            self.assertTrue(
                all(
                    "calculation_angles" not in r and "worded_component_sequences" not in r
                    for r in rows
                )
            )

    def test_calculation_block_requires_explicit_review_of_queried_or_partial_angles(self):
        from src.historical_reviews import compile_reviews

        for literal in (
            "12 degrees 30 minutes[?]",
            "12° 30′[?]",
            "34.5 degrees",
            "1 /2 degrees",
            "1 /2°",
            "12 degrees 30 minutes 1/2 second",
            "12° 30′ [recte: 13° 30′]",
        ):
            with self.subTest(literal=literal), tempfile.TemporaryDirectory() as directory:
                work, review = self.prose_selection_fixture(Path(directory), literal)
                review["assertion_defaults"].update(
                    quantity="calculation_angle",
                    role="calculation_intermediate",
                    flags=["not_an_additional_raw_reading"],
                    context_keys=["calculation"],
                )
                review["contexts"] = [
                    dict(
                        key="calculation",
                        kind="source_observation_context",
                        lines=[1],
                        value=dict(record_type="source_worked_calculation"),
                    )
                ]
                review["cell_groups"] = [
                    dict(
                        calculation_angles=True,
                        line_range=[1, 1],
                        worded_component_sequences=[["degree", "arcminute"]],
                    )
                ]
                with self.assertRaisesRegex(ValueError, "explicit review"):
                    compile_reviews(work, [review])

    def test_calculation_block_cannot_assign_observations_or_choose_table_cells(self):
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.prose_selection_fixture(Path(directory), "Sun altitude 12° 30′.")
            review["cell_groups"] = [dict(calculation_angles=True, line_range=[1, 1])]
            with self.assertRaisesRegex(ValueError, "calculation block"):
                compile_reviews(work, [review])

    def test_worded_completion_cannot_start_at_a_decimal_tail_or_fraction_denominator(self):
        from src.historical_reviews import compile_reviews

        for literal, units in (
            ("34.5 degrees", ["degree"]),
            ("1 /2 degrees", ["degree"]),
            ("12 degrees 30 minutes", ["arcminute"]),
            ("12° 30 minutes", ["arcminute"]),
        ):
            with self.subTest(literal=literal), tempfile.TemporaryDirectory() as directory:
                work, review = self.prose_selection_fixture(Path(directory), literal)
                review["cell_groups"][0].update(
                    component_units=units,
                    cells=[
                        dict(line=1, column=None, fragment_index=1, complete_angle_sequence=True)
                    ],
                )
                with self.assertRaisesRegex(ValueError, "complete numerical"):
                    compile_reviews(work, [review])

    def test_calculation_block_keeps_spaced_vulgar_fraction_in_one_occurrence(self):
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.prose_selection_fixture(
                Path(directory), "Distance 12 ½ degrees 15 minutes."
            )
            review["assertion_defaults"].update(
                quantity="calculation_angle",
                role="historical_input",
                flags=["not_an_additional_raw_reading"],
                context_keys=["calculation"],
            )
            review["contexts"] = [
                dict(
                    key="calculation",
                    kind="source_observation_context",
                    lines=[1],
                    value=dict(record_type="source_worked_calculation"),
                )
            ]
            review["cell_groups"] = [
                dict(
                    calculation_angles=True,
                    line_range=[1, 1],
                    worded_component_sequences=[["degree", "arcminute"]],
                )
            ]
            _, compiled, _ = compile_reviews(work, [review])
            self.assertEqual(len(compiled["assertions"]), 1)
            row = compiled["assertions"][0]
            self.assertEqual(row["source_expression"], "12 ½ degrees 15 minutes")
            self.assertEqual(row["normalized"]["magnitude"], "45900")

    def test_worded_angle_completion_preserves_existing_staging_indices_and_identities(self):
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.prose_selection_fixture(
                Path(directory), "At hour 7, altitude 24 degrees 32 minutes; later 13° 15′."
            )
            review["cell_groups"][0]["cells"][0]["expression_index"] = 1
            _, before, _ = compile_reviews(work, [review])
            old = before["assertions"][0]
            review["cell_groups"].append(
                dict(
                    component_units=["degree", "arcminute"],
                    cells=[
                        dict(line=1, column=None, fragment_index=1, complete_angle_sequence=True)
                    ],
                )
            )
            _, after, _ = compile_reviews(work, [review])
            self.assertEqual(next(r for r in after["assertions"] if r["id"] == old["id"]), old)
            self.assertEqual(len({r["id"] for r in after["assertions"]}), 2)
            added = next(r for r in after["assertions"] if r["id"] != old["id"])
            self.assertEqual(added["source_expression"], "24 degrees 32 minutes")
            self.assertEqual(added["normalized"]["magnitude"], "88320")

    def test_worded_angle_completion_rejects_time_units_queries_and_partial_sequences(self):
        from src.historical_reviews import compile_reviews

        for literal, units in (
            ("12 degrees 30 hours", ["degree", "arcminute"]),
            ("12 degrees 30 minutes?", ["degree", "arcminute"]),
            ("12 degrees 30 minutes 2", ["degree", "arcminute"]),
            ("12 degrees 30 minutes 2 seconds", ["degree", "arcminute"]),
            ("12 degrees 30 minutes", ["degree", "arcsecond"]),
            ("34 minutes", ["arcsecond"]),
            ("hour 7", ["degree"]),
            ("1590 September 18", ["degree"]),
            ("12° 30′", ["degree", "arcminute"]),
        ):
            with self.subTest(literal=literal), tempfile.TemporaryDirectory() as directory:
                work, review = self.prose_selection_fixture(Path(directory), literal)
                review["cell_groups"][0].update(
                    component_units=units,
                    cells=[
                        dict(line=1, column=None, fragment_index=0, complete_angle_sequence=True)
                    ],
                )
                with self.assertRaises(ValueError):
                    compile_reviews(work, [review])

    def test_angle_sequence_rejects_conflicting_units_queries_and_unconsumed_numbers(self):
        from src.historical_reviews import compile_reviews

        for literal, units in (
            ("12° 30 hours", ["degree", "arcminute"]),
            ("12° 30 minutes?", ["degree", "arcminute"]),
            ("12° 30 minutes 2", ["degree", "arcminute"]),
            ("12° 30 minutes 2 hours", ["degree", "arcminute"]),
            ("12° 30 minutes -2 seconds", ["degree", "arcminute"]),
            ("12° 30 minutes, 2 seconds", ["degree", "arcminute"]),
            ("12° 30 minutes 2 seconds", ["degree", "arcsecond"]),
        ):
            with self.subTest(literal=literal), tempfile.TemporaryDirectory() as directory:
                work, review = self.prose_selection_fixture(Path(directory), literal)
                group = review["cell_groups"][0]
                group["component_units"] = units
                group["cells"][0]["complete_angle_sequence"] = True
                with self.assertRaises(ValueError):
                    compile_reviews(work, [review])

    def test_staged_prose_query_requires_an_explicit_unresolved_review(self):
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.prose_selection_fixture(Path(directory), "Sun altitude 12° 30′?")
            with self.assertRaisesRegex(ValueError, "unresolved"):
                compile_reviews(work, [review])
            group = review["cell_groups"][0]
            group.pop("component_units")
            group["cells"][0].update(components={}, flags=["source_notation_unresolved"])
            _, compiled, _ = compile_reviews(work, [review])
            row = compiled["assertions"][0]
            self.assertEqual(row["source_expression"], "12° 30′?")
            self.assertIsNone(row["normalized"]["magnitude"])

    def test_staged_prose_selector_rejects_invalid_or_conflicting_positions(self):
        import copy
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.prose_selection_fixture(Path(directory), "Sun altitude 12° 30′.")
            for change in (
                dict(expression_index=-1),
                dict(expression_index=True),
                dict(expression_index=2),
                dict(column=2),
                dict(source_expression="12° 30′"),
                dict(char_start=13),
                dict(complete_angle_sequence="true"),
                dict(complete_angle_sequence=1),
            ):
                candidate = copy.deepcopy(review)
                candidate["cell_groups"][0]["cells"][0].update(change)
                with self.subTest(change=change), self.assertRaises(ValueError):
                    compile_reviews(work, [candidate])

    def prose_selection_fixture(self, root, text):
        import hashlib

        source = root / "book.md"
        source.write_text(text + "\n", encoding="utf-8")
        work = root / "work"
        sid = "snellius-observationes-hassiacae"
        inventory_sources([dict(source_id=sid, path=str(source))], work)
        review = dict(
            id="prose-readings",
            source_id=sid,
            edition_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            line_start=1,
            line_end=1,
            basis=dict(kind="final_edition_review", printed_page=1),
            included_span_starts=[1],
            contexts=[],
            assertion_defaults=dict(
                quantity="altitude",
                role="recorded_reading",
                subject="Sun",
                reference=None,
                unit_basis="Reviewed prose units and endpoints",
            ),
            cell_groups=[
                dict(
                    component_units=["degree", "arcminute"],
                    cells=[dict(line=1, column=None, expression_index=0)],
                )
            ],
        )
        return work, review

    def historical_review_fixture(self, root):
        import hashlib

        source = root / "book.md"
        source.write_text("| Sun | 12° 30′ |\n", encoding="utf-8")
        sid = "snellius-observationes-hassiacae"
        work = root / "work"
        inventory_sources([dict(source_id=sid, path=str(source))], work)
        review = dict(
            id="solar-reading",
            source_id=sid,
            edition_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            line_start=1,
            line_end=1,
            basis=dict(kind="final_edition_review", printed_page=1),
            included_span_starts=[1],
            contexts=[],
            assertion_defaults=dict(
                quantity="altitude",
                role="recorded_reading",
                subject="Sun",
                reference=None,
                unit_basis="Explicit degree and minute marks",
            ),
            cell_groups=[dict(component_units=["degree", "arcminute"], cells=[[1, 2]])],
        )
        return work, review

    def test_combined_append_and_export_compiles_once_and_matches_separate_run(self):
        from unittest.mock import patch
        from src import historical_reviews as workflow

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.historical_review_fixture(Path(directory))
            with patch.object(
                workflow, "compile_reviews", wraps=workflow.compile_reviews
            ) as compile_:
                combined = workflow.run(work, additions=review)
            self.assertEqual(compile_.call_count, 1)
            self.assertEqual(combined["quantities"], 1)
            self.assertEqual(workflow.run(work), combined)
            self.assertEqual(workflow.run(work, additions=review), combined)

    def test_failed_combined_preflight_does_not_append_or_publish(self):
        from src.historical_reviews import run

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.historical_review_fixture(Path(directory))
            review["cell_groups"][0]["component_units"] = ["degree", "arcsecond"]
            with self.assertRaises(ValueError):
                run(work, additions=review)
            self.assertFalse((work / "reviews.json").exists())
            self.assertFalse((work / "catalogue/manifest.json").exists())

    def test_interrupted_combined_export_resumes_from_durable_ledger(self):
        import json
        from unittest.mock import patch
        from src import historical_reviews as workflow

        with tempfile.TemporaryDirectory() as directory:
            work, review = self.historical_review_fixture(Path(directory))
            with patch.object(workflow, "write_catalogue", side_effect=RuntimeError("interrupted")):
                with self.assertRaisesRegex(RuntimeError, "interrupted"):
                    workflow.run(work, additions=review)
            self.assertEqual(json.loads((work / "reviews.json").read_text()), [review])
            self.assertFalse((work / "verification.json").exists())
            self.assertEqual(workflow.run(work)["quantities"], 1)

    def test_named_source_inspection_reuses_staging_without_accepting_readings(self):
        from src.historical_reviews import inspect

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "book.md"
            text = "Venus declination 12° 30′.\n\n| Star | Declination |\n|---|---|\n| Sun | 13° 15′ |\n"
            source.write_text(text, encoding="utf-8")
            sid = "snellius-observationes-hassiacae"
            work = root / "work"
            inventory_sources([dict(source_id=sid, path=str(source))], work)
            out = inspect(work, sid, 1, 5)
            self.assertEqual(out["status"], "requires_source_review_not_accepted_observations")
            prose = next(
                x for x in out["staged_expressions"] if x["source_expression"] == "12° 30′"
            )
            self.assertEqual(prose["line"], 1)
            self.assertEqual(prose["components"], {"degree": "12", "arcminute": "30"})
            self.assertIn("quantity_role_and_target_unreviewed", prose["flags"])
            cell = next(x for x in out["staged_cells"] if x["source_expression"] == "13° 15′")
            self.assertEqual((cell["line"], cell["column"]), (5, 2))
            self.assertEqual(source.read_text(encoding="utf-8"), text)
            self.assertFalse((work / "reviews.json").exists())
            self.assertFalse((work / "verification.json").exists())

    def test_materialization_does_not_rescan_other_review_intervals(self):
        import copy
        import hashlib
        from unittest.mock import patch
        from src import historical_reviews as workflow

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "book.md"
            source.write_text("| Sun | 12° 30′ |\n\n| Sun | 13° 15′ |\n", encoding="utf-8")
            sid = "snellius-observationes-hassiacae"
            work = root / "work"
            inventory_sources([dict(source_id=sid, path=str(source))], work)
            reviews = []
            for line in (1, 3):
                reviews.append(
                    dict(
                        id=f"reading-{line}",
                        source_id=sid,
                        edition_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                        line_start=line,
                        line_end=line,
                        basis=dict(kind="final_edition_review", printed_page=1),
                        included_span_starts=[line],
                        contexts=[],
                        assertion_defaults=dict(
                            quantity="altitude",
                            role="recorded_reading",
                            subject="Sun",
                            reference=None,
                            unit_basis="Explicit degree and minute marks",
                        ),
                        cell_groups=[
                            dict(component_units=["degree", "arcminute"], cells=[[line, 2]])
                        ],
                    )
                )
            frozen = copy.deepcopy(reviews)
            with patch.object(
                workflow, "materialize_review", wraps=workflow.materialize_review
            ) as prepare:
                _, compiled, _ = workflow.compile_reviews(work, reviews)
            self.assertEqual(len(compiled["assertions"]), 2)
            self.assertEqual(reviews, frozen)
            self.assertEqual(prepare.call_count, len(reviews))
            for call in prepare.call_args_list:
                review, _, spans = call.args
                self.assertEqual([s["line_start"] for s in spans], [review["line_start"]])

    def test_reviewed_calculation_input_preserves_frozen_row(self):
        import hashlib
        import json
        from src.historical_reviews import apply_classification_reviews

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for event in (None, "observing-event"):
                row = dict(
                    id="a",
                    source_id="book",
                    role="calculation_intermediate",
                    flags=["not_an_additional_raw_reading"],
                    event_id=event,
                    source_expression="300",
                    components={"scalar": "300"},
                )
                original = dict(row)
                decision = dict(
                    id="scope-input",
                    assertion_id="a",
                    original_sha256=hashlib.sha256(
                        json.dumps(row, sort_keys=True, ensure_ascii=False).encode()
                    ).hexdigest(),
                    before={"role": "calculation_intermediate"},
                    after={"role": "historical_input"},
                    reason="Stated validity horizon, not an intermediate arithmetic result",
                    evidence=[{"line": 1, "source_expression": "within 300 years"}],
                )
                (work / "classification_reviews.json").write_text(
                    json.dumps([decision]), encoding="utf-8"
                )
                if event:
                    with self.assertRaises(ValueError):
                        apply_classification_reviews(
                            work, {"assertions": [row]}, {"book": "within 300 years"}
                        )
                else:
                    out = apply_classification_reviews(
                        work, {"assertions": [row]}, {"book": "within 300 years"}
                    )
                    self.assertEqual(out["a"]["before"], original)
                    self.assertEqual(row, dict(original, role="historical_input"))

    def test_page_binding_review_corrects_locator_without_rewriting_reading(self):
        import hashlib
        import json
        from src.historical_reviews import append, compile_reviews, run

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "book.md"
            source.write_text("| Sun | 12° 30′ |\n", encoding="utf-8")
            sid = "snellius-observationes-hassiacae"
            work = root / "work"
            inventory_sources([dict(source_id=sid, path=str(source))], work)
            review = dict(
                id="solar-reading",
                source_id=sid,
                edition_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                line_start=1,
                line_end=1,
                basis=dict(kind="final_edition_review", printed_page=2),
                included_span_starts=[1],
                contexts=[],
                assertion_defaults=dict(
                    quantity="altitude",
                    role="recorded_reading",
                    subject="Sun",
                    reference=None,
                    unit_basis="Explicit degree and minute marks",
                ),
                cell_groups=[dict(component_units=["degree", "arcminute"], cells=[[1, 2]])],
            )
            append(work, review)
            run(work)
            frozen = (work / "reviews.json").read_bytes()
            original = json.loads((work / "compiled_assertions.json").read_text())[0]
            correction = dict(
                id="folio-correction",
                source_id=sid,
                edition_sha256=review["edition_sha256"],
                review_id=review["id"],
                line_start=1,
                line_end=1,
                before_printed_page=2,
                after_printed_page=1,
                reason="First folio was assigned the next recto number",
                evidence=[dict(line=1, source_expression="12° 30′")],
            )
            path = work / "page_binding_reviews.json"
            path.write_text(json.dumps([correction]), encoding="utf-8")
            _, compiled, _ = compile_reviews(work, [review])
            updated = compiled["assertions"][0]
            self.assertEqual(updated["printed_page"], 1)
            self.assertEqual(updated["id"], original["id"])
            self.assertEqual(updated["normalized"], original["normalized"])
            run(work)
            self.assertEqual((work / "reviews.json").read_bytes(), frozen)
            self.assertEqual(
                json.loads((work / "compiled_assertions.json").read_text())[0]["printed_page"],
                1,
            )
            path.write_text(json.dumps([dict(correction, before_printed_page=3)]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Page binding review"):
                compile_reviews(work, [review])

    def test_source_bound_classification_repair_preserves_readings_and_history(self):
        import copy
        import hashlib
        import json
        from src.historical_reviews import append, compile_reviews, run

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "book.md"
            text = "| Mars | Third Star of Aries | 12° 30′ |\n"
            source.write_text(text, encoding="utf-8")
            work = root / "work"
            sid = "snellius-observationes-hassiacae"
            inventory_sources([dict(source_id=sid, path=str(source))], work)
            review = dict(
                id="planet-reading",
                source_id=sid,
                edition_sha256=hashlib.sha256(text.encode()).hexdigest(),
                line_start=1,
                line_end=1,
                basis=dict(kind="final_edition_review", printed_page=1),
                included_span_starts=[1],
                contexts=[],
                assertion_defaults=dict(
                    quantity="angular_separation",
                    role="repeated_reading",
                    subject="Mars",
                    reference="head of Andromeda",
                    unit_basis="Explicit degree and minute marks",
                ),
                cell_groups=[dict(component_units=["degree", "arcminute"], cells=[[1, 3]])],
            )
            append(work, review)
            run(work)
            frozen_ledger = (work / "reviews.json").read_bytes()
            old_snapshot = (work / "compiled_assertions.json").read_bytes()
            original = json.loads(old_snapshot)[0]
            correction = dict(
                id="correct-reference",
                assertion_id=original["id"],
                original_sha256=hashlib.sha256(
                    json.dumps(original, sort_keys=True, ensure_ascii=False).encode()
                ).hexdigest(),
                reason="Ordinal is part of a star name, not a repetition label",
                evidence=[dict(line=1, source_expression="Third Star of Aries")],
                before=dict(reference="head of Andromeda", role="repeated_reading"),
                after=dict(reference="third star of Aries", role="recorded_reading"),
            )
            path = work / "classification_reviews.json"
            path.write_text(json.dumps([correction]), encoding="utf-8")
            _, compiled, _ = compile_reviews(work, [review])
            fixed = compiled["assertions"][0]
            self.assertEqual(fixed["reference"], "third star of Aries")
            self.assertEqual(fixed["role"], "recorded_reading")
            self.assertEqual(fixed["normalized"], original["normalized"])
            self.assertEqual(fixed["id"], original["id"])
            proof = run(work)
            self.assertEqual(proof, run(work))
            self.assertIn("classification_review_sha256", proof)
            self.assertEqual((work / "reviews.json").read_bytes(), frozen_ledger)
            snapshot_hash = hashlib.sha256(old_snapshot).hexdigest()
            self.assertEqual(
                (work / "recovery" / f"assertions-{snapshot_hash}.json").read_bytes(),
                old_snapshot,
            )
            mutations = [
                dict(after=dict(correction["after"], normalized=dict(magnitude="999"))),
                dict(original_sha256="0" * 64),
                dict(evidence=[dict(line=1, source_expression="Fourth Star of Aries")]),
                dict(assertion_id="missing"),
            ]
            for changes in mutations:
                with self.subTest(changes=changes):
                    invalid = copy.deepcopy(correction)
                    invalid.update(changes)
                    path.write_text(json.dumps([invalid]), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "Classification review"):
                        compile_reviews(work, [review])

    def test_distinct_equal_literals_use_their_bound_source_positions(self):
        import copy
        import hashlib
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "book.md"
            text = "Mars 1°; Venus 1°; Sun 2°\n"
            source.write_text(text, encoding="utf-8")
            sid = "snellius-observationes-hassiacae"
            work = root / "work"
            inventory_sources([dict(source_id=sid, path=str(source))], work)
            cells = []
            for subject in ("Mars", "Venus"):
                start = text.index("1°", text.index(subject))
                cells.append(
                    dict(
                        key=subject,
                        line=1,
                        column=None,
                        source_expression="1°",
                        subject=subject,
                        components={"degree": "1"},
                        char_start=start,
                        char_end=start + len("1°"),
                    )
                )
            review = dict(
                id="two-planets",
                source_id=sid,
                edition_sha256=hashlib.sha256(text.encode()).hexdigest(),
                line_start=1,
                line_end=1,
                basis=dict(kind="final_edition_review", printed_page=1),
                included_span_starts=[1],
                assertion_defaults=dict(
                    quantity="altitude",
                    role="recorded_reading",
                    reference=None,
                    unit_basis="Distinct printed angular readings",
                ),
                cell_groups=[dict(cells=cells)],
            )
            _, compiled, _ = compile_reviews(work, [review])
            self.assertEqual(len(compiled["assertions"]), 2)
            duplicate = copy.deepcopy(review)
            duplicate["cell_groups"][0]["cells"].append(dict(cells[0], key="copied"))
            with self.assertRaisesRegex(ValueError, "Repeated source occurrence"):
                compile_reviews(work, [duplicate])
            # The same location also remains a duplicate when one recipe omits
            # explicit offsets and relies on its unique literal instead.
            start = text.index("2°")
            unique = dict(
                key="sun",
                line=1,
                column=None,
                source_expression="2°",
                subject="Sun",
                components={"degree": "2"},
            )
            duplicate["cell_groups"][0]["cells"] = [
                unique,
                dict(unique, key="sun-explicit", char_start=start, char_end=start + len("2°")),
            ]
            with self.assertRaisesRegex(ValueError, "Repeated source occurrence"):
                compile_reviews(work, [duplicate])

    def test_shared_component_reuse_is_distinct_from_reimporting_a_reading(self):
        import copy
        import hashlib
        from src.catalog import identity
        from src.historical_reviews import compile_reviews

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "book.md"
            text = "| 24° { |\n| 34′ |\n| 35′ |\n"
            source.write_text(text, encoding="utf-8")
            sha = hashlib.sha256(text.encode()).hexdigest()
            sid = "snellius-observationes-hassiacae"
            work = root / "work"
            inventory_sources([dict(source_id=sid, path=str(source))], work)
            cells = []
            for line, minutes in [(2, "34"), (3, "35")]:
                cells.append(
                    dict(
                        key=f"reading-{line}",
                        line=1,
                        column=1,
                        source_expression="24°",
                        components=dict(degree="24", arcminute=minutes),
                        source_fragments=[
                            dict(
                                line=n,
                                span_id=identity("span", sid, sha, n, "line"),
                                source_expression=expr,
                            )
                            for n, expr in [(1, "24°"), (line, minutes + "′")]
                        ],
                        source_continuation_context_key="brace",
                        context_keys=["brace"],
                    )
                )
            review = dict(
                id="shared-degrees",
                source_id=sid,
                edition_sha256=sha,
                line_start=1,
                line_end=3,
                basis=dict(kind="final_edition_review", printed_page=1),
                included_span_starts=[1, 2, 3],
                contexts=[
                    dict(
                        key="brace",
                        kind="source_observation_context",
                        lines=[1],
                        value=dict(record_type="source_continuation", source_expression="24° {"),
                    )
                ],
                assertion_defaults=dict(
                    quantity="altitude",
                    role="recorded_reading",
                    subject="Sun",
                    reference=None,
                    unit_basis="Shared printed degrees and distinct minutes",
                ),
                cell_groups=[dict(cells=cells)],
            )
            _, compiled, _ = compile_reviews(work, [review])
            self.assertEqual(
                {q["normalized"]["magnitude"] for q in compiled["assertions"]}, {"88440", "88500"}
            )
            duplicate = copy.deepcopy(review)
            duplicate["cell_groups"][0]["cells"].append(dict(cells[0], key="duplicate"))
            with self.assertRaisesRegex(ValueError, "Repeated source occurrence"):
                compile_reviews(work, [duplicate])

    def test_resumable_named_book_workflow_preserves_context_and_rejects_changed_sources(self):
        import hashlib
        import json
        import sqlite3
        from contextlib import closing
        from src.historical_reviews import append, run

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "book.md"
            text = "# Solar observations\nDecember 5, 1590, at midday, Julian\n| 12° 30′ |\n"
            source.write_text(text, encoding="utf-8")
            work = root / "work"
            sid = "snellius-observationes-hassiacae"
            inventory_sources([dict(source_id=sid, path=str(source))], work)
            review = dict(
                id="solar-1",
                source_id=sid,
                edition_sha256=hashlib.sha256(text.encode()).hexdigest(),
                line_start=1,
                line_end=3,
                basis=dict(kind="final_edition_review", printed_page=1),
                included_span_starts=[3],
                contexts=[
                    dict(
                        key="timing",
                        kind="source_observation_context",
                        lines=[2],
                        value=dict(clock_expression="midday", time_scale=None),
                    ),
                    dict(
                        key="date",
                        kind="recorded_date",
                        lines=[2],
                        value=dict(year=1590, month=12, day=5),
                        calendar="Julian",
                        day_origin=None,
                    ),
                ],
                assertion_defaults=dict(
                    quantity="altitude",
                    role="recorded_reading",
                    subject="Sun",
                    reference=None,
                    unit_basis="Explicit degree and minute marks",
                    context_keys=["timing", "date"],
                ),
                cell_groups=[dict(component_units=["degree", "arcminute"], cells=[[3, 1]])],
            )
            self.assertEqual(append(work, review)["appended"], 1)
            self.assertEqual(append(work, review)["appended"], 0)
            first = run(work)
            self.assertEqual(first, run(work))
            self.assertEqual((first["quantities"], first["reviewed_sections"]), (1, 1))
            with closing(sqlite3.connect(work / "catalogue/tychonides.sqlite")) as db:
                value = json.loads(
                    db.execute(
                        "SELECT value_json FROM contexts WHERE kind='source_observation_context'"
                    ).fetchone()[0]
                )
                self.assertEqual(value["clock_expression"], "midday")
                self.assertEqual(db.execute("SELECT count(*) FROM source_loci").fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT count(*) FROM quantity_dates").fetchone()[0], 1)
                claim = json.loads(db.execute("SELECT data_json FROM dates").fetchone()[0])
                self.assertEqual(claim["source_id"], sid)
                self.assertEqual(claim["calendar"], "Julian")
                self.assertIsNone(claim["absolute_timestamp"])
            source.write_text(text.replace("12°", "13°"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source changed"):
                run(work)

    def test_named_source_materialization_assembly_and_public_projection(self):
        import hashlib
        from src.catalog import compile_catalogue
        from src.review_preparation import materialize_review
        from src.assembly import assemble
        from src.public_assertions import public_assertion

        sid = "snellius-observationes-hassiacae"
        text = "# Altitudes\n| 12° 30′ |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", source_id=sid, edition_sha256=sha, line_start=2, line_end=2)]
        recipe = dict(
            id="r",
            source_id=sid,
            edition_sha256=sha,
            line_start=2,
            line_end=2,
            basis=dict(kind="final_edition_review", printed_page=1),
            included_span_starts=[2],
            assertion_defaults=dict(
                quantity="altitude",
                role="recorded_reading",
                subject="Mars",
                reference=None,
                unit_basis="Explicit degree and minute marks",
            ),
            cell_groups=[dict(component_units=["degree", "arcminute"], cells=[[2, 1]])],
        )
        review = materialize_review(recipe, text, spans)
        compiled = compile_catalogue([review], {sid: text}, spans)
        row = compiled["assertions"][0]
        assembly = assemble({sid: text}, [row], [], [], [])
        self.assertEqual(assembly["items"][0]["source_id"], sid)
        with self.assertRaisesRegex(ValueError, "source"):
            public_assertion(row)
        projected = public_assertion(row, source_registry={sid})
        self.assertEqual(projected["source_id"], sid)
        self.assertNotIn("volume", projected)
        self.assertEqual(projected["normalized"]["magnitude"], "45000")
        from contextlib import closing
        import sqlite3
        from src.catalog_release import write_catalogue
        from src.release_validation import validate_release

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_catalogue(
                output,
                [row],
                [projected],
                [],
                [],
                [],
                [],
                [],
                [{"id": sid, "author": "Willebrord Snellius", "title": "Observationes Hassiacae"}],
                [],
                {},
            )
            self.assertEqual(validate_release(output)["quantities"], 1)
            with closing(sqlite3.connect(output / "tychonides.sqlite")) as db:
                self.assertEqual(
                    db.execute("SELECT source_id,volume,value_exact FROM catalogue").fetchone(),
                    (sid, None, "45000"),
                )
                self.assertEqual(db.execute("SELECT id FROM sources").fetchall(), [(sid,)])

    def test_named_source_compiles_without_tycho_volume_or_identity_collision(self):
        from test_catalog import CatalogueTests
        from src.catalog import compile_catalogue

        fixture = CatalogueTests()
        text, spans, batch = fixture.explicit_clock_case(
            "1^h^ 30^m^", {"hour": "1", "minute": "30"}
        )
        legacy = compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        batch.pop("volume")
        batch["source_id"] = "snellius-hassiacae"
        for span in spans:
            span.pop("volume")
            span["source_id"] = batch["source_id"]
        result = compile_catalogue([batch], {batch["source_id"]: text}, spans)
        row = result["assertions"][0]
        self.assertEqual(row["source_id"], "snellius-hassiacae")
        self.assertNotIn("volume", row)
        self.assertNotEqual(row["id"], legacy["id"])
        self.assertEqual(row["normalized"], legacy["normalized"])
        batch["volume"] = 10
        with self.assertRaisesRegex(ValueError, "Tycho volume"):
            compile_catalogue([batch], {10: text}, spans)

    def test_inventory_is_complete_repeatable_and_source_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "book.md"
            source.write_text("Preface\n# Observations\n| angle |\n| 12° |\n", encoding="utf-8")
            entries = [{"source_id": "snellius-hassiacae", "path": str(source)}]
            result = inventory_sources(entries, root / "work")
            self.assertEqual(result, inventory_sources(entries, root / "work"))
            sections = result["sources"][0]["sections"]
            self.assertEqual([(s["line_start"], s["line_end"]) for s in sections], [(1, 1), (2, 4)])
            self.assertTrue(all(s["decision"] == "pending" for s in sections))
            source.write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed"):
                inventory_sources(entries, root / "work")

    def test_duplicate_sources_and_source_directory_outputs_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "book.md"
            source.write_text("# Book\n", encoding="utf-8")
            entry = {"source_id": "book", "path": str(source)}
            with self.assertRaises(ValueError):
                inventory_sources([entry, entry], root / "work")
            with self.assertRaises(ValueError):
                inventory_sources([entry], root)
