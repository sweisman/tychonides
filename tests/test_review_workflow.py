import copy
import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path


class ReviewWorkflowTests(unittest.TestCase):
    def test_complete_grouped_native_fragment_requires_explicit_grouping_review(self):
        from src.catalog import compile_catalogue
        from src.narrative_staging import stage_span

        text = "Distance 14,000 semidiameters."
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(
            id="s",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            block_kind="paragraph",
            text_original=text,
        )
        fragments = stage_span(span)["material"]["numeric_fragments"]
        self.assertEqual([f["source_expression"] for f in fragments], ["14,000"])
        recipe = dict(
            id="grouped-native",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            basis=dict(kind="final_edition_review", printed_page=1),
            included_span_starts=[1],
            cell_groups=[
                dict(
                    quantity="distance_in_semidiameters",
                    role="historical_input",
                    subject="Saturn",
                    reference="Earth",
                    direction=None,
                    flags=["not_an_additional_raw_reading"],
                    context_keys=[],
                    component_units=["semidiameter"],
                    source_number_grouping="comma_thousands",
                    unit_basis="Reviewed native distance and comma grouping",
                    cells=[dict(line=1, column=None, fragment_index=0)],
                )
            ],
        )
        batch = self.module().materialize_review(recipe, text, [span])
        row = compile_catalogue([batch], {10: text}, [span])["assertions"][0]
        self.assertEqual(row["source_expression"], "14,000")
        self.assertEqual(row["normalized"]["magnitude"], "14000")
        unreviewed = copy.deepcopy(recipe)
        del unreviewed["cell_groups"][0]["source_number_grouping"]
        with self.assertRaises(ValueError):
            self.module().materialize_review(unreviewed, text, [span])
        for literal in ("14,00", "14,000,00", "-14,000", "14,000.5", "1,2"):
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                self.module().materialize_review(recipe, literal, [span])

    def test_native_fragment_selector_preserves_fractions_and_distinct_occurrences(self):
        from src.catalog import compile_catalogue

        text = "Lengths 166⅜ and 2; a second pair 11 to 2.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=1)]
        recipe = dict(
            id="native-fragments",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            basis=dict(kind="final_edition_review", printed_page=1),
            included_span_starts=[1],
            assertion_defaults=dict(
                role="historical_input",
                subject="Sun calculation",
                reference=None,
                direction=None,
                context_keys=[],
                flags=["not_an_additional_raw_reading"],
                unit_basis="Reviewed independent model-length operands",
            ),
            cell_groups=[
                dict(
                    quantity="source_scalar",
                    source_parameter_kind="model_length",
                    component_units=["scalar"],
                    cells=[dict(line=1, column=None, fragment_index=i) for i in (0, 1, 3)],
                )
            ],
        )
        batch = self.module().materialize_review(recipe, text, spans)
        compiled = compile_catalogue([batch], {10: text}, spans)["assertions"]
        self.assertEqual([r["source_expression"] for r in compiled], ["166⅜", "2", "2"])
        self.assertEqual([r["normalized"]["magnitude"] for r in compiled], ["1331/8", "2", "2"])
        self.assertNotEqual(compiled[1]["char_start"], compiled[2]["char_start"])
        self.assertEqual(len({r["id"] for r in compiled}), 3)
        changed = text.replace("166⅜", "167⅜")
        changed_recipe = dict(recipe, edition_sha256=hashlib.sha256(changed.encode()).hexdigest())
        changed_spans = [dict(spans[0], edition_sha256=changed_recipe["edition_sha256"])]
        new = self.module().materialize_review(changed_recipe, changed, changed_spans)
        self.assertEqual(
            [r["key"] for r in batch["assertions"]], [r["key"] for r in new["assertions"]]
        )
        self.assertEqual([r["source_expression"] for r in new["assertions"]], ["167⅜", "2", "2"])
        for change in (
            {"fragment_index": True},
            {"fragment_index": -1},
            {"fragment_index": 9},
            {"column": 1},
            {"expression_index": 0},
            {"source_expression": "166⅜"},
            {"components": {"scalar": "999"}},
            {"component_units": []},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                bad = copy.deepcopy(recipe)
                bad["cell_groups"][0]["cells"] = [dict(line=1, column=None, fragment_index=0, **{})]
                bad["cell_groups"][0]["cells"][0].update(change)
                self.module().materialize_review(bad, text, spans)

    def test_native_fragment_selector_rejects_partial_or_unit_bearing_tokens(self):
        for text in (
            "20° 15′",
            "1^h^ 30^m^",
            "1,720",
            "3.15",
            "10 000",
            "52 17",
            "-12",
            "12?",
            "17…",
            "12[1/2]",
            "12 minutes",
            "12′",
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                sha = hashlib.sha256(text.encode()).hexdigest()
                spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=1)]
                recipe = dict(
                    id="partial",
                    volume=10,
                    edition_sha256=sha,
                    line_start=1,
                    line_end=1,
                    basis=dict(kind="final_edition_review", printed_page=1),
                    cell_groups=[
                        dict(
                            quantity="source_scalar",
                            component_units=["scalar"],
                            cells=[dict(line=1, column=None, fragment_index=0)],
                        )
                    ],
                )
                self.module().materialize_review(recipe, text, spans)

    def test_fragment_selector_keeps_and_checks_one_explicit_unit(self):
        from src.catalog import compile_catalogue

        text = "Diameter 31½ minutes.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=1)]
        recipe = dict(
            id="native-unit",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            basis=dict(kind="final_edition_review", printed_page=1),
            included_span_starts=[1],
            cell_groups=[
                dict(
                    quantity="angular_diameter",
                    role="historical_input",
                    subject="Sun",
                    reference=None,
                    direction=None,
                    context_keys=[],
                    flags=[],
                    unit_basis="Printed minutes",
                    component_units=["arcminute"],
                    cells=[dict(line=1, column=None, fragment_index=0)],
                )
            ],
        )
        batch = self.module().materialize_review(recipe, text, spans)
        row = compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(row["source_expression"], "31½ minutes")
        self.assertEqual(row["normalized"]["magnitude"], "1890")
        wrong = copy.deepcopy(recipe)
        wrong["cell_groups"][0]["component_units"] = ["degree"]
        with self.assertRaises(ValueError):
            self.module().materialize_review(wrong, text, spans)
        for literal, index in (
            ("31 minutes 40 seconds", 0),
            ("31 minutes 40 seconds", 1),
            ("31 minutes and 40 seconds", 0),
            ("31 minutes and 40 seconds", 1),
        ):
            with self.subTest(literal=literal, index=index), self.assertRaises(ValueError):
                changed = copy.deepcopy(recipe)
                changed["cell_groups"][0]["cells"][0]["fragment_index"] = index
                changed["edition_sha256"] = hashlib.sha256(literal.encode()).hexdigest()
                self.module().materialize_review(
                    changed, literal, [dict(spans[0], edition_sha256=changed["edition_sha256"])]
                )

    def test_explicit_middot_integer_grouping_is_not_a_distance_fraction_or_decimal(self):
        from src.normalization import source_numeric_text

        row = dict(quantity="source_scalar", source_number_grouping="middot_integer_digits")
        self.assertEqual(source_numeric_text(row, "1068·57"), "106857")
        for literal in ("1068.57", "1068·1/2", "+1068·57", "·106857", "106857·"):
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                source_numeric_text(row, literal)
        with self.assertRaises(ValueError):
            source_numeric_text(dict(row, quantity="distance_in_semidiameters"), "52·25")

    def test_declared_units_materialize_ordered_fragments_around_a_correction(self):
        from src.catalog import compile_catalogue

        text = "95 [recte: 59]′ 17″\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=1)]
        suffix = "′ 17″"
        cell = dict(
            key="original",
            line=1,
            column=None,
            source_expression="95",
            source_fragments=[
                dict(line=1, span_id="s", source_expression="95"),
                dict(line=1, span_id="s", source_expression=suffix),
            ],
            source_continuation_context_key="correction",
            context_keys=["correction"],
            quantity="parallax_angle",
            role="historical_input",
            subject="Moon",
            reference="Earth",
            flags=["not_an_additional_raw_reading"],
            unit_basis="M/S header; original interrupted by correction",
            component_units=["arcminute", "arcsecond"],
        )
        recipe = dict(
            id="fragment-units",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            basis=dict(kind="final_edition_review", printed_page=120),
            included_span_starts=[1],
            contexts=[
                dict(
                    key="correction",
                    kind="source_observation_context",
                    lines=[1],
                    value=dict(record_type="source_continuation", source_expression=text.strip()),
                )
            ],
            cell_groups=[dict(cells=[cell])],
        )
        batch = self.module().materialize_review(recipe, text, spans)
        row = compile_catalogue([batch], {10: text}, spans)["assertions"][0]
        self.assertEqual(row["components"], {"arcminute": "95", "arcsecond": "17"})
        self.assertEqual(row["normalized"]["magnitude"], "5717")
        self.assertEqual(row["source_expression"], "95")
        tampered = copy.deepcopy(recipe)
        tampered["cell_groups"][0]["cells"][0]["source_fragments"][1]["source_expression"] = "′ 18″"
        altered = self.module().materialize_review(tampered, text, spans)
        with self.assertRaises(ValueError):
            compile_catalogue([altered], {10: text}, spans)

    def test_explicit_prose_expression_does_not_read_a_table_column(self):
        from unittest.mock import patch

        text = "- left | 3′ 41″ | right\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=1)]
        cell = dict(
            key="input",
            line=1,
            column=None,
            source_expression="3′ 41″",
            quantity="parallax_angle",
            component_units=["arcminute", "arcsecond"],
            role="historical_input",
            subject="Mars",
            reference="Earth",
            flags=["not_an_additional_raw_reading"],
            unit_basis="Explicit prose expression",
        )
        recipe = dict(
            id="prose",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            basis=dict(kind="final_edition_review", printed_page=1),
            cell_groups=[dict(cells=[cell])],
        )
        with patch(
            "src.table_staging.split_cells",
            side_effect=AssertionError("Table fallback must not run"),
        ):
            batch = self.module().materialize_review(recipe, text, spans)
        self.assertIsNone(batch["assertions"][0]["column"])
        self.assertEqual(batch["assertions"][0]["components"], dict(arcminute="3", arcsecond="41"))

    def test_reviewed_spaced_scalar_digits_preserve_literals_and_do_not_change_angles(self):
        from src.catalog import compile_catalogue
        from src.public_checkpoint import public_assertion

        text = "10 000\n11 181½\n78 387\n100 000\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=4)]
        cells = []
        for n, expression, kind, scale in [
            (1, "10 000", "model_length", "10000"),
            (2, "11 181½", "model_length", "10000"),
            (3, "78 387", "scaled_sine", "100000"),
            (4, "100 000", "trigonometric_radius", None),
        ]:
            cell = dict(
                key=str(n),
                line=n,
                column=1,
                source_expression=expression,
                quantity="source_scalar",
                component_units=["scalar"],
                source_number_grouping="spaced_thousands",
                source_parameter_kind=kind,
                role="historical_input",
                subject="Mars calculation",
                reference=None,
                direction=None,
                flags=["not_an_additional_raw_reading"],
                unit_basis="Reviewed spaced integer groups",
                uncertainty=dict(numeric=None, basis="Source notation retained"),
            )
            if scale:
                cell["source_scalar_scale"] = scale
            cells.append(cell)
        recipe = dict(
            id="grouped",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=4,
            basis=dict(kind="final_edition_review", printed_page=1),
            cell_groups=[dict(cells=cells)],
        )
        batch = self.module().materialize_review(recipe, text, spans)
        compiled = sorted(
            compile_catalogue([batch], {10: text}, spans)["assertions"], key=lambda r: int(r["key"])
        )
        published = [public_assertion(r) for r in compiled]
        self.assertEqual(
            [r["normalized"]["magnitude"] for r in published],
            ["10000", "22363/2", "78387", "100000"],
        )
        self.assertEqual([r["source_expression"] for r in compiled], text.splitlines())
        self.assertTrue(all(r["source_number_grouping"] == "spaced_thousands" for r in published))
        bad = copy.deepcopy(recipe)
        bad["cell_groups"][0]["cells"][0].update(
            quantity="altitude", subject="Mars", component_units=["degree", "arcminute"]
        )
        with self.assertRaises(ValueError):
            self.module().materialize_review(bad, text, spans)
        bad = copy.deepcopy(compiled[0])
        bad["source_number_grouping"] = "unreviewed"
        with self.assertRaises(ValueError):
            public_assertion(bad)
        # Without explicit grouping, the same two numerals remain separate angle places.
        angle = copy.deepcopy(recipe)
        angle["cell_groups"][0]["cells"] = cells[:1]
        c = angle["cell_groups"][0]["cells"][0]
        for k in ("source_number_grouping", "source_parameter_kind", "source_scalar_scale"):
            c.pop(k, None)
        c.update(quantity="altitude", subject="Mars", component_units=["degree", "arcminute"])
        rows = compile_catalogue(
            [self.module().materialize_review(angle, text, spans)], {10: text}, spans
        )["assertions"]
        self.assertEqual(rows[0]["normalized"]["magnitude"], "36000")

    def test_declared_component_units_extract_literals_without_guessing_dimensions(self):
        from src.catalog import compile_catalogue

        text = "45 20\n45 20\n7 24¹\ntwo hours\nninetieth degree\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=5)]
        common = dict(
            column=1,
            role="recorded_reading",
            subject="Mars",
            reference=None,
            unit_basis="Reviewed unit scope",
        )
        cells = [
            dict(
                common,
                key="time",
                line=1,
                source_expression="45 20",
                quantity="recorded_clock",
                role="recorded_clock",
                subject="observing clock",
                component_units=["minute", "second"],
                flags=["clock_hour_unstated"],
            ),
            dict(
                common,
                key="angle",
                line=2,
                source_expression="45 20",
                quantity="altitude",
                component_units=["degree", "arcminute"],
            ),
            dict(
                common,
                key="marked",
                line=3,
                source_expression="7 24¹",
                quantity="altitude",
                component_units=["degree", "arcminute"],
                source_note_marker_original="¹",
            ),
            dict(
                common,
                key="word",
                line=4,
                source_expression="two hours",
                quantity="clock_drift",
                role="calibration",
                subject="observing clock",
                component_units=["hour"],
                source_word_numbers={"two": "2"},
            ),
            dict(
                common,
                key="ordinal",
                line=5,
                source_expression="ninetieth degree",
                quantity="unclassified_angle",
                component_units=["degree"],
                source_word_numbers={"ninetieth": "90"},
                flags=["measurement_type_unresolved"],
            ),
        ]
        recipe = dict(
            id="units",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=5,
            basis=dict(kind="final_edition_review", printed_page=1),
            cell_groups=[dict(cells=cells)],
        )
        batch = self.module().materialize_review(recipe, text, spans)
        out = compile_catalogue([batch], {10: text}, spans)["assertions"]
        self.assertEqual(
            {r["key"]: (r["normalized"]["magnitude"], r["normalized"]["unit"]) for r in out},
            {
                "time": ("2720", "second_of_time"),
                "angle": ("163200", "arcsecond"),
                "marked": ("26640", "arcsecond"),
                "word": ("7200", "second_of_time"),
                "ordinal": ("324000", "arcsecond"),
            },
        )
        self.assertTrue(all("component_units" not in r for r in batch["assertions"]))
        for units in ([], ["minute", "minute"], ["hour"], ["hour", "minute", "second"]):
            bad = copy.deepcopy(recipe)
            bad["cell_groups"][0]["cells"][0]["component_units"] = units
            with self.subTest(units=units), self.assertRaises(ValueError):
                self.module().materialize_review(bad, text, spans)
        bad = copy.deepcopy(recipe)
        bad["cell_groups"][0]["cells"][0]["source_expression"] = "45"
        with self.assertRaises(ValueError):
            self.module().materialize_review(bad, text, spans)

    def test_reviewed_source_binding_refresh_recovers_without_rewriting_reviews(self):
        from unittest.mock import patch
        from tests.test_source_bindings import SourceBindingTests
        from src.catalog import compile_catalogue
        from src.public_checkpoint import public_assertion
        from src.source_bindings import apply_span_bindings

        old, current, batch, before, after, binding = SourceBindingTests().fixture()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "source"
            work = base / "work"
            public = base / "public"
            for p in (root, work, public):
                p.mkdir()
            (root / "source.md").write_text(current)
            original_witness = dict(
                id="w",
                volume=11,
                edition_sha256=hashlib.sha256(old.encode()).hexdigest(),
                witness_type="final_prepub",
                private_source="source.md",
            )
            values = {
                "witnesses.json": [original_witness],
                "review_batches.json": [batch],
                "source_reference_reviews.json": [],
                "inventory_manifest.json": dict(
                    volumes=[11],
                    source_hashes={"source.md": original_witness["edition_sha256"]},
                    benchmark_artifact_sha256={},
                ),
                "recovery_checkpoint.json": dict(
                    checkpoint_status="verified_resume_ready", last_verified={}
                ),
            }
            for name, value in values.items():
                (work / name).write_text(json.dumps(value))
            (work / "inventory_spans.jsonl").write_text(json.dumps(before) + "\n")
            original = compile_catalogue([batch], {11: old}, [before])
            (public / "reviewed_assertions.jsonl").write_text(
                "".join(json.dumps(public_assertion(a)) + "\n" for a in original["assertions"])
            )
            frozen = (work / "review_batches.json").read_bytes()
            book = dict(
                source="source.md",
                sha256=hashlib.sha256(current.encode()).hexdigest(),
                text=current,
                provenance={},
                source_hashes={"source.md": hashlib.sha256(current.encode()).hexdigest()},
            )
            m = self.module()
            with (
                patch("src.publication.load_publication", return_value=book),
                patch("src.inventory.inventory_text", return_value=dict(spans=[after])),
            ):
                result = m.begin_source_refresh(work, root, public, 11, binding=binding)
                self.assertEqual(result["status"], "source_refresh_ready")
                self.assertEqual(result["reviewed_source_span_identities_preserved"], 1)
                self.assertEqual(result["current_candidate_regions"], 1)
                self.assertNotIn("unchanged_candidate_regions", result)
                cp = read_json(work / "recovery_checkpoint.json")
                revision = cp["in_progress"]["source_revision"]
                self.assertEqual(revision["kind"], "reviewed_bindings")
                (work / "source_binding_reviews.json").unlink()
                (work / "witnesses.json").write_text(json.dumps([original_witness]))
                m.begin_source_refresh(work, root, public, 11, binding=binding)
                self.assertEqual(read_json(work / "source_binding_reviews.json"), [binding])
                self.assertEqual((work / "review_batches.json").read_bytes(), frozen)
                spans = apply_span_bindings([after], [binding])
                (work / "inventory_spans.jsonl").write_text(
                    "".join(json.dumps(s) + "\n" for s in spans)
                )
                manifest = dict(
                    values["inventory_manifest.json"],
                    source_hashes=revision["expected_source_hashes"],
                )
                (work / "inventory_manifest.json").write_text(json.dumps(manifest))
                checked = m.verify_reference_refresh(work)
                self.assertEqual(checked["reviewed_source_span_identities_preserved"], 1)
                spans[0]["text_original"] = "unreviewed change"
                (work / "inventory_spans.jsonl").write_text(json.dumps(spans[0]) + "\n")
                with self.assertRaises(ValueError):
                    m.verify_reference_refresh(work)
                restored = apply_span_bindings([after], [binding])
                (work / "inventory_spans.jsonl").write_text(json.dumps(restored[0]) + "\n")
                cp = read_json(work / "recovery_checkpoint.json")
                cp.pop("in_progress")
                cp["checkpoint_status"] = "verified_resume_ready"
                (work / "recovery_checkpoint.json").write_text(json.dumps(cp))
                added = dict(
                    id="new-header",
                    volume=11,
                    edition_sha256=batch["edition_sha256"],
                    line_start=1,
                    line_end=1,
                    interval_sha256=hashlib.sha256(b"New heading").hexdigest(),
                    basis=dict(kind="final_edition_review", printed_page=178),
                    span_decisions=[],
                    assertions=[],
                    events=[],
                    contexts=[],
                )
                m.append_review(work, root, public, added)
                self.assertEqual(
                    read_json(work / "recovery_checkpoint.json")["in_progress"][
                        "new_inspected_source_lines"
                    ],
                    1,
                )

    def test_provenance_refresh_requires_identical_canonical_text_and_selected_bindings(self):
        from unittest.mock import patch
        from src.inventory import inventory_text

        with tempfile.TemporaryDirectory() as d:
            m, root, work, public, reference, text, _ = self.reference_fixture(Path(d))
            batch = root / "batch_001.md"
            batch.write_text("earlier provenance wording")
            manifest = read_json(work / "inventory_manifest.json")
            manifest["source_hashes"]["batch_001.md"] = m.digest(batch)
            (work / "inventory_manifest.json").write_text(json.dumps(manifest))
            (work / "provenance_v12.json").write_text("{}")
            m.begin_reference_refresh(work, root, public, [reference])
            enlarged = inventory_text(
                text, 12, reference["edition_sha256"], reference_reviews=[reference]
            )["spans"]
            (work / "inventory_spans.jsonl").write_text(
                "".join(json.dumps(s) + "\n" for s in enlarged)
            )
            batch.write_text("updated wording with unchanged selected page bindings")
            book = dict(
                volume=12,
                source="source.md",
                sha256=m.digest(root / "source.md"),
                text=text,
                provenance={},
                source_hashes={
                    "source.md": m.digest(root / "source.md"),
                    "batch_001.md": m.digest(batch),
                },
            )
            before = (work / "recovery_checkpoint.json").read_bytes()
            with (
                patch("src.publication.load_publication", return_value=dict(book, sha256="0" * 64)),
                self.assertRaisesRegex(ValueError, "canonical"),
            ):
                m.begin_source_refresh(work, root, public, 12)
            self.assertEqual((work / "recovery_checkpoint.json").read_bytes(), before)
            changed = dict(book, provenance={5: dict(page=999)})
            with patch("src.publication.load_publication", return_value=changed):
                with self.assertRaises(ValueError):
                    m.begin_source_refresh(work, root, public, 12)
            self.assertEqual((work / "recovery_checkpoint.json").read_bytes(), before)
            with patch("src.publication.load_publication", return_value=book):
                result = m.begin_source_refresh(work, root, public, 12)
            self.assertEqual(result["status"], "provenance_refresh_ready")
            cp = read_json(work / "recovery_checkpoint.json")
            revision = cp["in_progress"]["source_revision"]
            self.assertEqual(revision["kind"], "provenance_inputs_only")
            self.assertEqual(
                read_json(work / revision["proof"])["changed_provenance_inputs"][0]["after"],
                m.digest(batch),
            )
            manifest["source_hashes"] = revision["expected_source_hashes"]
            (work / "inventory_manifest.json").write_text(json.dumps(manifest))
            m.verify_reference_refresh(work)
            (work / "inventory_manifest.json").write_text(
                json.dumps(dict(manifest, source_hashes={"source.md": "0" * 64}))
            )
            with self.assertRaises(ValueError):
                m.verify_reference_refresh(work)

    def test_column_repair_preserves_published_date_and_control_enrichment(self):
        from src.catalog import compile_catalogue
        from src.date_claims import project_date_claims
        from src.public_checkpoint import public_assertion

        m = self.module()
        with tempfile.TemporaryDirectory() as directory:
            root, work, public, batches = self.disjoint_fixture(Path(directory))
            first, second = batches
            first["contexts"] = [
                dict(key="date", kind="recorded_date", lines=[1], value={"month": 9, "day": 30})
            ]
            first["assertions"][0]["context_keys"] = ["date"]
            second["assertions"][0]["column"] = 1
            m.append_review(work, root, public, batches)
            compiled = compile_catalogue(
                [first], m.source_texts(work, root), m.rows(work / "inventory_spans.jsonl")
            )
            dates = project_date_claims(
                compiled["contexts"], compiled["assertions"], compiled["events"]
            )
            a = compiled["assertions"][0]
            published = public_assertion(
                dict(
                    a,
                    source_date_claim_ids=dates["assertion_date_ids"][a["id"]],
                    workbook_control_id="Sheet1:1",
                )
            )
            cp = json.loads((work / "recovery_checkpoint.json").read_text())
            p = cp["in_progress"]
            (work / p["prior_review_ledger_backup"]).write_text(json.dumps([first]))
            (work / p["prior_public_snapshot"]).write_text(json.dumps(published) + "\n")
            bad = copy.deepcopy(second)
            bad["assertions"][0]["column"] = 2
            (work / "review_batches.json").write_text(json.dumps([first, bad]))
            p.update(
                review_ids=[second["id"]],
                review_ledger_sha256=hashlib.sha256(
                    (work / "review_batches.json").read_bytes()
                ).hexdigest(),
            )
            (work / "recovery_checkpoint.json").write_text(json.dumps(cp))
            try:
                m.repair_pending_columns(work, root, public, [second])
            except ValueError as error:
                self.fail(f"Published enrichment must survive a pending binding repair: {error}")
            self.assertEqual(
                json.loads((work / "review_batches.json").read_text()), [first, second]
            )

    def test_pending_column_repair_can_bind_inline_proportion_as_prose_but_not_a_table(self):
        m = self.module()
        for raw, allowed in [("- `17° 20¼′ | 8 | 9`", True), ("|17° 20¼′|8|9|", False)]:
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as directory:
                root, work, public, batch = self.fixture(Path(directory))
                text = "30 September\n" + raw + "\n"
                sha = hashlib.sha256(text.encode()).hexdigest()
                (root / "source.md").write_text(text)
                witnesses = json.loads((work / "witnesses.json").read_text())
                witnesses[0]["edition_sha256"] = sha
                (work / "witnesses.json").write_text(json.dumps(witnesses))
                span = json.loads((work / "inventory_spans.jsonl").read_text())
                span["edition_sha256"] = sha
                (work / "inventory_spans.jsonl").write_text(json.dumps(span) + "\n")
                batch.update(
                    edition_sha256=sha, interval_sha256=hashlib.sha256(raw.encode()).hexdigest()
                )
                batch["assertions"][0]["column"] = 1
                m.append_review(work, root, public, batch)
                repaired = copy.deepcopy(batch)
                repaired["assertions"][0]["column"] = None
                if allowed:
                    result = m.repair_pending_columns(work, root, public, [repaired])
                    self.assertEqual(
                        json.loads((work / "review_batches.json").read_text()), [repaired]
                    )
                    self.assertEqual(
                        json.loads((work / result["prior_attempt"]).read_text()), [batch]
                    )
                else:
                    with self.assertRaises(ValueError):
                        m.repair_pending_columns(work, root, public, [repaired])

    def test_pending_column_repair_retains_attempt_and_refuses_numeric_changes(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as directory:
            root, work, public, good = self.fixture(Path(directory))
            good["assertions"][0]["column"] = 1
            m.append_review(work, root, public, good)
            bad = copy.deepcopy(good)
            bad["assertions"][0]["column"] = 2
            (work / "review_batches.json").write_text(json.dumps([bad]))
            cp = json.loads((work / "recovery_checkpoint.json").read_text())
            cp["in_progress"]["review_ledger_sha256"] = hashlib.sha256(
                (work / "review_batches.json").read_bytes()
            ).hexdigest()
            (work / "recovery_checkpoint.json").write_text(json.dumps(cp))
            try:
                result = m.repair_pending_columns(work, root, public, [good])
            except AttributeError as error:
                self.fail(f"Unverified bindings need a retained repair operation: {error}")
            self.assertEqual(json.loads((work / "review_batches.json").read_text()), [good])
            self.assertEqual(json.loads((work / result["prior_attempt"]).read_text()), [bad])
            self.assertEqual(
                m.repair_pending_columns(work, root, public, [good])["status"], "already_repaired"
            )
            cp = json.loads((work / "recovery_checkpoint.json").read_text())
            cp["in_progress"]["column_repair_plan"]["status"] = "prepared"
            cp["in_progress"]["stage"] = "column_repair_ready"
            (work / "recovery_checkpoint.json").write_text(json.dumps(cp))
            (work / "review_batches.json").write_text(json.dumps([bad]))
            m.repair_pending_columns(work, root, public, [good])
            self.assertEqual(json.loads((work / "review_batches.json").read_text()), [good])
            changed = copy.deepcopy(good)
            changed["assertions"][0]["components"]["degree"] = "18"
            with self.assertRaises(ValueError):
                m.repair_pending_columns(work, root, public, [changed])

    def test_only_reviewed_direction_and_signed_magnitude_can_change(self):
        old = dict(
            id="quantity",
            direction="south",
            normalized=dict(magnitude="12", signed_magnitude="-12", unit="arcsecond"),
            role="reduction",
        )
        new = copy.deepcopy(old)
        new.update(direction="north")
        new["normalized"]["signed_magnitude"] = "12"
        review = {"quantity": dict(old_direction="south", new_direction="north")}
        self.assertEqual(self.module().preserve_rows([old], [new], review), ["quantity"])
        for changed in [
            dict(new, role="recorded_reading"),
            dict(new, normalized=dict(new["normalized"], magnitude="13")),
        ]:
            with self.assertRaises(ValueError):
                self.module().preserve_rows([old], [changed], review)
        with self.assertRaises(ValueError):
            self.module().preserve_rows([old], [new])
        with self.assertRaises(ValueError):
            self.module().preserve_rows([old], [new], {"missing": review["quantity"]})

    def module(self):
        try:
            return importlib.import_module("src.review_workflow")
        except ModuleNotFoundError:
            self.fail("Shared review workflow is not implemented")

    def fixture(self, base):
        root, work, public = [base / n for n in ("sources", "work", "public")]
        for p in (root, work, public):
            p.mkdir()
        text = "30 September\n17° 20¼′\n"
        (root / "source.md").write_text(text)
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=2, line_end=2)
        (work / "inventory_spans.jsonl").write_text(json.dumps(span) + "\n")
        (work / "witnesses.json").write_text(
            json.dumps([dict(volume=12, private_source="source.md", edition_sha256=sha)])
        )
        (work / "review_batches.json").write_text("[]\n")
        (work / "recovery_checkpoint.json").write_text(
            json.dumps(dict(checkpoint_status="verified_resume_ready", last_verified={}))
        )
        (public / "reviewed_assertions.jsonl").write_text("")
        (work / "evidence.pdf").write_bytes(b"retained scan witness")
        batch = dict(
            id="review-example",
            volume=12,
            edition_sha256=sha,
            line_start=2,
            line_end=2,
            interval_sha256=hashlib.sha256("17° 20¼′".encode()).hexdigest(),
            basis=dict(
                kind="scan_review",
                printed_page=445,
                evidence_hashes={
                    "evidence.pdf": hashlib.sha256(b"retained scan witness").hexdigest()
                },
            ),
            span_decisions=[dict(span_id="s", decision="include", reason="Source inspected")],
            contexts=[],
            events=[],
            assertions=[
                dict(
                    key="decl",
                    line=2,
                    span_id="s",
                    source_expression="17° 20¼′",
                    quantity="declination",
                    role="recorded_coordinate",
                    subject="Mars",
                    reference=None,
                    direction=None,
                    components={"degree": "17", "arcminute": "20¼"},
                    unit_basis="Printed units",
                    flags=["hemisphere_unspecified"],
                )
            ],
        )
        return root, work, public, batch

    def test_repeated_append_and_interrupted_checkpoint_do_not_duplicate_review(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            root, work, public, batch = self.fixture(Path(d))
            m.append_review(work, root, public, batch)
            cp = json.loads((work / "recovery_checkpoint.json").read_text())
            cp["in_progress"]["stage"] = "review_ledger_append_ready"
            (work / "recovery_checkpoint.json").write_text(json.dumps(cp))
            m.append_review(work, root, public, batch)
            self.assertEqual(json.loads((work / "review_batches.json").read_text()), [batch])
            cp = json.loads((work / "recovery_checkpoint.json").read_text())
            self.assertEqual(cp["in_progress"]["stage"], "review_ledger_committed_builds_pending")

    def disjoint_fixture(self, base):
        root, work, public, first = self.fixture(base)
        text = "30 September\n17° 20¼′\nUnreviewed gap\n20° 10′\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        (root / "source.md").write_text(text)
        (work / "witnesses.json").write_text(
            json.dumps([dict(volume=12, private_source="source.md", edition_sha256=sha)])
        )
        spans = [
            dict(id="s", volume=12, edition_sha256=sha, line_start=2, line_end=2),
            dict(id="s2", volume=12, edition_sha256=sha, line_start=4, line_end=4),
        ]
        (work / "inventory_spans.jsonl").write_text("".join(json.dumps(s) + "\n" for s in spans))
        first["edition_sha256"] = sha
        second = copy.deepcopy(first)
        second.update(
            id="review-second",
            line_start=4,
            line_end=4,
            interval_sha256=hashlib.sha256("20° 10′".encode()).hexdigest(),
        )
        second["span_decisions"][0]["span_id"] = "s2"
        second["assertions"][0].update(
            line=4,
            span_id="s2",
            source_expression="20° 10′",
            components={"degree": "20", "arcminute": "10"},
        )
        return root, work, public, [first, second]

    def test_disjoint_review_list_appends_once_and_resumes_all_supplements(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            root, work, public, batches = self.disjoint_fixture(Path(d))
            target = work / "edition_issues.json"
            target.write_text("[]")
            for index, batch in enumerate(batches):
                batch["record_updates"] = {
                    "edition_issues.json": [dict(id=f"issue-{index}", finding="Reviewed")]
                }
            try:
                result = m.append_review(work, root, public, batches)
            except (ValueError, TypeError, AttributeError) as error:
                self.fail(f"Disjoint reviewed packets must append together: {error}")
            self.assertEqual(result["review_ids"], ["review-example", "review-second"])
            cp = read_json(work / "recovery_checkpoint.json")
            self.assertEqual(cp["in_progress"]["source_intervals"], [[2, 2], [4, 4]])
            self.assertEqual(cp["in_progress"]["new_inspected_source_lines"], 2)
            self.assertEqual(cp["in_progress"]["new_inspected_regions"], 2)
            self.assertEqual(len(read_json(target)), 2)
            cp["in_progress"]["stage"] = "review_ledger_append_ready"
            (work / "recovery_checkpoint.json").write_text(json.dumps(cp))
            target.write_text("[]")
            m.append_review(work, root, public, batches)
            self.assertEqual(read_json(work / "review_batches.json"), batches)
            self.assertEqual(len(read_json(target)), 2)
            self.assertEqual(
                read_json(work / "recovery_checkpoint.json")["in_progress"]["stage"],
                "review_ledger_committed_builds_pending",
            )

    def test_invalid_second_packet_cannot_partially_append_or_apply_supplements(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            root, work, public, batches = self.disjoint_fixture(Path(d))
            target = work / "edition_issues.json"
            target.write_text("[]")
            batches[0]["record_updates"] = {
                "edition_issues.json": [dict(id="issue", finding="Reviewed")]
            }
            batches[1]["assertions"][0]["components"]["degree"] = "21"
            paths = [work / "review_batches.json", work / "recovery_checkpoint.json", target]
            before = [p.read_bytes() for p in paths]
            with self.assertRaises(ValueError):
                m.append_review(work, root, public, batches)
            self.assertEqual([p.read_bytes() for p in paths], before)

    def test_review_list_rejects_duplicate_ids_and_mixed_replays(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            root, work, public, batches = self.disjoint_fixture(Path(d))
            for invalid in ([], [batches[0], batches[0]]):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    m.append_review(work, root, public, invalid)
            m.append_review(work, root, public, batches[0])
            paths = [work / "review_batches.json", work / "recovery_checkpoint.json"]
            before = [p.read_bytes() for p in paths]
            with self.assertRaises(ValueError):
                m.append_review(work, root, public, batches)
            self.assertEqual([p.read_bytes() for p in paths], before)

    def test_overlapping_review_packets_count_source_lines_and_regions_once(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            root, work, public, first = self.fixture(Path(d))
            second = copy.deepcopy(first)
            second.update(
                id="review-context",
                line_start=1,
                interval_sha256=hashlib.sha256("30 September\n17° 20¼′".encode()).hexdigest(),
                assertions=[],
            )
            m.append_review(work, root, public, [first, second])
            progress = read_json(work / "recovery_checkpoint.json")["in_progress"]
            self.assertEqual(progress["new_inspected_source_lines"], 2)
            self.assertEqual(progress["new_inspected_regions"], 1)

    def test_conflicting_reuse_of_review_id_is_rejected(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            root, work, public, batch = self.fixture(Path(d))
            m.append_review(work, root, public, batch)
            changed = copy.deepcopy(batch)
            changed["assertions"][0]["role"] = "historical_input"
            with self.assertRaisesRegex(ValueError, "Conflicting review"):
                m.append_review(work, root, public, changed)
            self.assertEqual(json.loads((work / "review_batches.json").read_text()), [batch])

    def test_source_validation_failure_leaves_ledger_and_checkpoint_unchanged(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            root, work, public, batch = self.fixture(Path(d))
            paths = [work / "review_batches.json", work / "recovery_checkpoint.json"]
            before = [p.read_bytes() for p in paths]
            batch["assertions"][0]["components"]["arcminute"] = "21¼"
            with self.assertRaises(ValueError):
                m.append_review(work, root, public, batch)
            self.assertEqual([p.read_bytes() for p in paths], before)

    def test_previous_quantities_cannot_be_changed_deleted_or_duplicated(self):
        m = self.module()
        prior = [{"id": "a", "value": 1}]
        m.preserve_rows(prior, [*prior, {"id": "b", "value": 2}])
        for current in ([], [{"id": "a", "value": 2}], prior + prior):
            with self.subTest(current=current), self.assertRaises(ValueError):
                m.preserve_rows(prior, current)

    def test_reviewed_control_link_addition_preserves_all_other_fields(self):
        m = self.module()
        prior = [dict(id="a", value="1")]
        linked = [dict(id="a", value="1", workbook_control_id="Sheet1:7")]
        self.assertEqual(m.preserve_rows(prior, linked, control_reviews={"a": "Sheet1:7"}), [])
        with self.assertRaises(ValueError):
            m.preserve_rows(prior, linked)
        for changed in (
            [dict(id="a", value="2", workbook_control_id="Sheet1:7")],
            [dict(id="a", value="1", workbook_control_id="Sheet1:8")],
            [],
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                m.preserve_rows(prior, changed, control_reviews={"a": "Sheet1:7"})
        with self.assertRaises(ValueError):
            m.preserve_rows(
                linked,
                [dict(id="a", value="1", workbook_control_id="Sheet1:8")],
                control_reviews={"a": "Sheet1:8"},
            )
        with self.assertRaises(ValueError):
            m.preserve_rows(prior, linked, control_reviews={"missing": "Sheet1:7"})

    def test_manifest_path_escape_is_rejected_before_reading(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "outside"):
                m.checked_hashes(Path(d), {"../outside": "a" * 64})

    def test_manifest_check_detects_changed_output(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "output").write_text("verified")
            expected = {"output": hashlib.sha256(b"verified").hexdigest()}
            m.checked_hashes(p, expected)
            (p / "output").write_text("changed")
            with self.assertRaisesRegex(ValueError, "changed"):
                m.checked_hashes(p, expected)

    def test_changed_scan_witness_prevents_append(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            root, work, public, batch = self.fixture(Path(d))
            (work / "evidence.pdf").write_bytes(b"different witness")
            with self.assertRaisesRegex(ValueError, "changed"):
                m.append_review(work, root, public, batch)
            self.assertEqual(read_json(work / "review_batches.json"), [])

    def test_review_without_retained_scan_evidence_is_rejected(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            root, work, public, batch = self.fixture(Path(d))
            del batch["basis"]["evidence_hashes"]
            with self.assertRaisesRegex(ValueError, "evidence"):
                m.append_review(work, root, public, batch)

    def test_final_edition_review_needs_no_scan_but_still_validates_canonical_numbers(self):
        m = self.module()
        for invalid in (False, True):
            with self.subTest(invalid_number=invalid), tempfile.TemporaryDirectory() as d:
                root, work, public, batch = self.fixture(Path(d))
                batch["basis"] = dict(kind="final_edition_review", printed_page=445)
                (work / "evidence.pdf").unlink()
                if invalid:
                    batch["assertions"][0]["components"]["arcminute"] = "21¼"
                    with self.assertRaises(ValueError):
                        m.append_review(work, root, public, batch)
                    self.assertEqual(read_json(work / "review_batches.json"), [])
                else:
                    result = m.append_review(work, root, public, batch)
                    self.assertEqual(result["status"], "appended")
                    self.assertEqual(read_json(work / "review_batches.json"), [batch])

    def test_reviewed_cell_groups_preserve_fractions_and_explicit_blank_clock_pairing(self):
        m = self.module()
        text = "| 8^h^ 1^m^ | 17° 20¼′ |\n| | 17° 20½′ |\n"
        recipe = dict(
            volume=12,
            line_start=1,
            line_end=2,
            assertion_defaults=dict(
                subject="Mars",
                role="recorded_coordinate",
                reference=None,
                direction=None,
                unit_basis="Reviewed columns",
            ),
            row_events={"1": "pointing", "2": "pointing"},
            cell_groups=[
                dict(
                    quantity="recorded_clock",
                    subject="observing clock",
                    role="printed_correction",
                    cells=[[1, 1]],
                ),
                dict(
                    quantity="declination",
                    cells=[
                        [1, 2],
                        dict(line=2, column=2, role="repeated_reading", source_pair_position=2),
                    ],
                ),
            ],
        )
        spans = [dict(id="s", volume=12, line_start=1, line_end=2)]
        result = m.materialize_review(recipe, text, spans)
        self.assertEqual(
            [a["components"] for a in result["assertions"]],
            [
                {"hour": "8", "minute": "1"},
                {"degree": "17", "arcminute": "20 1/4"},
                {"degree": "17", "arcminute": "20 1/2"},
            ],
        )
        self.assertEqual([a["event_key"] for a in result["assertions"]], ["pointing"] * 3)
        self.assertEqual(result["assertions"][-1]["role"], "repeated_reading")

    def test_numeric_group_cannot_turn_a_bare_annotation_into_a_measurement(self):
        m = self.module()
        recipe = dict(
            volume=12,
            line_start=1,
            line_end=1,
            cell_groups=[dict(quantity="declination", cells=[[1, 1]])],
        )
        with self.assertRaisesRegex(ValueError, "numeric components"):
            m.materialize_review(
                recipe, "| both [vtroque] |\n", [dict(id="s", volume=12, line_start=1, line_end=1)]
            )

    def test_supplementary_decisions_resume_without_duplicates(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            root, work, public, batch = self.fixture(Path(d))
            target = work / "edition_issues.json"
            target.write_text("[]")
            batch["record_updates"] = {
                "edition_issues.json": [{"id": "source-issue", "finding": "Source reviewed"}]
            }
            m.append_review(work, root, public, batch)
            self.assertEqual(read_json(target), batch["record_updates"]["edition_issues.json"])
            target.write_text("[]")
            m.append_review(work, root, public, batch)
            self.assertEqual(read_json(target), batch["record_updates"]["edition_issues.json"])
            self.assertEqual(len(read_json(work / "review_batches.json")), 1)

    def test_counts_come_from_outputs_and_inconsistent_totals_are_rejected(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            work = p / "work"
            public = p / "public"
            work.mkdir()
            public.mkdir()
            summary = dict(
                reviewed_subset=dict(assertions=7, event_groups=3),
                inspection=dict(inspected_source_lines=11, inspected_candidate_spans=2),
            )
            catalogue = dict(
                summary=dict(review_batches=4, normalization_statuses=dict(exact=6, incomplete=1))
            )
            (public / "summary.json").write_text(json.dumps(summary))
            (work / "catalogue_manifest.json").write_text(json.dumps(catalogue))
            result = m.current_counts(work, public)
            self.assertEqual(
                (
                    result["assertions"],
                    result["source_groups"],
                    result["exact"],
                    result["review_batches"],
                ),
                (7, 3, 6, 4),
            )
            catalogue["summary"]["normalization_statuses"]["exact"] = 5
            (work / "catalogue_manifest.json").write_text(json.dumps(catalogue))
            with self.assertRaisesRegex(ValueError, "normalization"):
                m.current_counts(work, public)

    def test_running_tally_does_not_count_unverified_work(self):
        m = self.module()
        checkpoint = dict(
            checkpoint_status="in_progress_after_verified_checkpoint",
            last_verified=dict(
                assertions=7, source_groups=3, inspected_regions=2, candidate_regions=10
            ),
            in_progress=dict(new_quantities=99, new_inspected_regions=4),
        )
        result = m.progress_tally(checkpoint)
        self.assertEqual(
            (
                result["quantities"],
                result["source_groups"],
                result["inspected_regions"],
                result["remaining_regions"],
            ),
            (7, 3, 2, 8),
        )
        self.assertEqual(result["region_coverage_percent"], 20.0)
        self.assertEqual(result["pending_quantities"], 99)

    def reference_fixture(self, base):
        m = self.module()
        from src.inventory import inventory_text

        root, work, public, _ = self.fixture(base)
        text = "| Star | Altitude |\n| --- | --- |\n| Regulus | 53° 37′ |\n\nMars altitudes can be limited from these two altitudes.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        (root / "source.md").write_text(text)
        (work / "witnesses.json").write_text(
            json.dumps([dict(volume=12, private_source="source.md", edition_sha256=sha)])
        )
        spans = inventory_text(text, 12, sha)["spans"]
        (work / "inventory_spans.jsonl").write_text("".join(json.dumps(s) + "\n" for s in spans))
        (work / "inventory_manifest.json").write_text(
            json.dumps(
                dict(volumes=[12], source_hashes={"source.md": sha}, benchmark_artifact_sha256={})
            )
        )
        (work / "source_reference_reviews.json").write_text("[]")
        reference = dict(
            id="star-calibration",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=3,
            interval_sha256=hashlib.sha256("\n".join(text.splitlines()[:3]).encode()).hexdigest(),
            reference_parent_line=5,
            parent_line_sha256=hashlib.sha256(text.splitlines()[4].encode()).hexdigest(),
            reference_kind="following_context",
            reference_phrase="Regulus",
            reason="Explicitly referenced stellar calibration",
        )
        return m, root, work, public, reference, text, spans

    def test_reference_refresh_resumes_interrupted_ledger_write_without_touching_reviews(self):
        with tempfile.TemporaryDirectory() as d:
            m, root, work, public, reference, text, spans = self.reference_fixture(Path(d))
            operation = getattr(m, "begin_reference_refresh", None)
            self.assertTrue(
                callable(operation), "Reference additions need a shared durable refresh operation"
            )
            ledger = (work / "review_batches.json").read_bytes()
            operation(work, root, public, [reference])
            cp = read_json(work / "recovery_checkpoint.json")
            self.assertEqual(cp["in_progress"]["operation"], "reference_inventory_refresh")
            self.assertEqual(cp["in_progress"]["review_ids"], [])
            self.assertEqual(m.rows(work / cp["in_progress"]["prior_inventory_spans"]), spans)
            (work / "source_reference_reviews.json").write_text("[]")
            operation(work, root, public, [reference])
            self.assertEqual(read_json(work / "source_reference_reviews.json"), [reference])
            self.assertEqual((work / "review_batches.json").read_bytes(), ledger)
            self.assertEqual((root / "source.md").read_text(), text)

    def test_stale_reference_or_conflicting_resume_cannot_mutate_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            m, root, work, public, reference, _, _ = self.reference_fixture(Path(d))
            operation = getattr(m, "begin_reference_refresh", None)
            self.assertTrue(callable(operation), "Reference refresh must preflight source bindings")
            bad = {**reference, "parent_line_sha256": "0" * 64}
            before = (work / "recovery_checkpoint.json").read_bytes()
            with self.assertRaises(ValueError):
                operation(work, root, public, [bad])
            self.assertEqual((work / "recovery_checkpoint.json").read_bytes(), before)
            self.assertEqual(read_json(work / "source_reference_reviews.json"), [])
            operation(work, root, public, [reference])
            with self.assertRaisesRegex(ValueError, "Conflicting"):
                operation(work, root, public, [{**reference, "reason": "different decision"}])

    def test_reference_refresh_preserves_existing_spans_and_protected_inputs(self):
        from src.inventory import inventory_text

        with tempfile.TemporaryDirectory() as d:
            m, root, work, public, reference, text, spans = self.reference_fixture(Path(d))
            operation = getattr(m, "begin_reference_refresh", None)
            self.assertTrue(
                callable(operation), "Reference refresh must retain an inventory baseline"
            )
            operation(work, root, public, [reference])
            enlarged = inventory_text(
                text, 12, reference["edition_sha256"], reference_reviews=[reference]
            )["spans"]
            path = work / "inventory_spans.jsonl"
            path.write_text("".join(json.dumps(s) + "\n" for s in enlarged))
            result = m.verify_reference_refresh(work)
            self.assertEqual(result["prior_candidate_regions_unchanged"], len(spans))
            self.assertEqual(len(result["added_candidate_region_ids"]), 1)
            enlarged[-1]["text_original"] = "changed source"
            path.write_text("".join(json.dumps(s) + "\n" for s in enlarged))
            with self.assertRaisesRegex(ValueError, "changed or disappeared"):
                m.verify_reference_refresh(work)
            path.write_text("".join(json.dumps(s) + "\n" for s in spans))
            manifest = read_json(work / "inventory_manifest.json")
            manifest["source_hashes"]["source.md"] = "0" * 64
            (work / "inventory_manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "Protected inventory inputs"):
                m.verify_reference_refresh(work)

    def test_reference_refresh_preserves_mars_regions_when_adding_research_calibration(self):
        from src.inventory import inventory_text
        from tests.test_inventory_references import InventoryReferenceTests

        text, sha, refs = InventoryReferenceTests().research_calibration_fixture()
        with tempfile.TemporaryDirectory() as d:
            root, work, public, _ = self.fixture(Path(d))
            m = self.module()
            (root / "source.md").write_text(text)
            (work / "witnesses.json").write_text(
                json.dumps([dict(volume=11, private_source="source.md", edition_sha256=sha)])
            )
            prior = inventory_text(text, 11, sha)["spans"]
            (work / "inventory_spans.jsonl").write_text(
                "".join(json.dumps(s) + "\n" for s in prior)
            )
            (work / "inventory_manifest.json").write_text(
                json.dumps(
                    dict(
                        volumes=[11], source_hashes={"source.md": sha}, benchmark_artifact_sha256={}
                    )
                )
            )
            (work / "source_reference_reviews.json").write_text("[]")
            try:
                m.begin_reference_refresh(work, root, public, refs)
            except ValueError as error:
                self.fail("Shared refresh must accept declared research calibration: " + str(error))
            expanded = inventory_text(text, 11, sha, reference_reviews=refs)["spans"]
            (work / "inventory_spans.jsonl").write_text(
                "".join(json.dumps(s) + "\n" for s in expanded)
            )
            result = m.verify_reference_refresh(work)
            self.assertEqual(result["prior_candidate_regions_unchanged"], 2)
            self.assertEqual(len(result["added_candidate_region_ids"]), 3)
            self.assertEqual((root / "source.md").read_text(), text)


def read_json(path):
    return json.loads(path.read_text())
