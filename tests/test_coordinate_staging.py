import copy
import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path


class CoordinateStagingTests(unittest.TestCase):
    def module(self):
        try:
            return importlib.import_module("src.coordinate_staging")
        except ModuleNotFoundError:
            self.fail("Coordinate staging bridge is not implemented")

    def fixture(self):
        text = "| clock | declination |\n| 8 20 | 17°20¼′ |\nDeclination 17…\nDeclination 18 2\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        source = "brahe/thesaurus_observationum_vol1/translation/brahe_thesaurus_observationum_vol1_prepub.md"
        observations = [
            dict(
                id="o1",
                source=source,
                volume=10,
                line=2,
                column=2,
                page=457,
                row_original="| 8 20 | 17°20¼′ |",
                value_original="17°20¼′",
                measurement_type="declination",
                role="observation",
                target="Mars",
                flags=["hemisphere_unresolved"],
                time_original="8 20",
                time_key="30000",
            ),
            dict(
                id="o2",
                source=source,
                volume=10,
                line=3,
                column=None,
                page=452,
                row_original="Declination 17…",
                value_original="17…",
                measurement_type="declination",
                role="observation",
                target="Mars",
                flags=["value_unresolved"],
            ),
            dict(
                id="o3",
                source=source,
                volume=10,
                line=4,
                column=None,
                page=452,
                row_original="Declination 18 2",
                value_original="18 2",
                measurement_type="declination",
                role="derived",
                target="Mars",
                flags=["derived_or_editorial"],
            ),
        ]
        spans = [
            dict(id="s1", volume=10, line_start=1, line_end=2, edition_sha256=sha),
            dict(id="s2", volume=10, line_start=3, line_end=3, edition_sha256=sha),
        ]
        controls = [
            dict(
                pafko_id="p1",
                source_record_id="o1",
                preferred_source_page=458,
                page_basis="source_scan_review",
                preferred_recorded_time_key=None,
                time_basis="source_scan_review",
                preferred_magnitude_arcsec="62415",
            ),
            dict(
                pafko_id="p2",
                source_record_id="o2",
                preferred_source_page=452,
                page_basis="source_text_unverified",
                preferred_magnitude_arcsec=None,
            ),
        ]
        return observations, {10: text}, spans, controls

    def test_normalizes_both_degree_notation_and_plain_components_exactly(self):
        m = self.module()
        for text in ("17°20¼′", "17 20¼", "**17° 20¼′** north [B.]"):
            with self.subTest(text=text):
                r = m.parse_coordinate(text)
                self.assertEqual(r["normalized"]["magnitude"], "62415")
                self.assertIsNone(r["normalized"]["signed_magnitude"])

    def test_incomplete_and_other_planet_cells_are_retained_without_guessed_values(self):
        m = self.module()
        self.assertEqual(m.parse_coordinate("17…")["normalized"]["status"], "incomplete")
        for text in ("♀ 14 44½ B.", "17.25", "17 65", "17 20 and 17 21"):
            r = m.parse_coordinate(text)
            self.assertIsNone(r["normalized"]["magnitude"])
            self.assertEqual(r["normalized"]["status"], "unsupported")

    def test_unit_adjacent_dots_separate_components_without_rewriting_decimals(self):
        for literal, exact in (
            ("13°.0⅔′", "46840"),
            ("22°.43′.50″", "81830"),
            ("0°.0′.½″", "1/2"),
            ("17°.14′ North", "62040"),
        ):
            with self.subTest(literal=literal):
                parsed = self.module().parse_coordinate(literal)
                self.assertEqual(parsed["normalized"]["magnitude"], exact)
        for literal in ("13.5°", "13°.2.5′", "13°.2′.5.5″", "13°.2′.50"):
            with self.subTest(literal=literal):
                self.assertIsNone(self.module().parse_coordinate(literal)["components"])

    def test_bilingual_numbers_must_agree_before_shared_normalization(self):
        m = self.module()
        r = m.parse_coordinate("*Declination of ♂, 4°42′ north* [Decl. ♂ 4 42 B.]")
        self.assertEqual(r["normalized"]["magnitude"], "16920")
        self.assertIn("parallel_numeric_expressions_agree", r["flags"])
        r = m.parse_coordinate("4°42′ north [4 43 B.]")
        self.assertIsNone(r["normalized"]["magnitude"])
        self.assertIn("parallel_numeric_expressions_disagree", r["flags"])
        r = m.parse_coordinate("17°23¾′ [17 23⁸⁄₄]")
        self.assertIsNone(r["normalized"]["magnitude"])
        self.assertIn("parallel_numeric_expressions_disagree", r["flags"])
        r = m.parse_coordinate("*1°31¼′ doubtful* [1 31¼ dubia]")
        self.assertEqual(r["normalized"]["magnitude"], "5475")
        self.assertIn("source_quality_note_present", r["flags"])

    def test_instrument_and_quality_qualifiers_preserve_exact_numbers_and_literal_notes(self):
        cases = [
            ("12°50½′ with one [vno]", "46230", "pinnule"),
            ("with the other [alt.] 12°40½′", "45630", "pinnule"),
            ("17°54′ both [vtroq.]", "64440", "pinnule"),
            ("23°34′ nearly [fere]", "84840", "quality"),
            ("1°10′ doubtful because of the beam [dubia propter tignum]", "4200", "quality"),
            ("7°24½′ by the steel instrument [per Chal.]", "26670", "instrument"),
            ("Declination [Decl.] 1°16′", "4560", "parallel_label"),
        ]
        for expression, magnitude, kind in cases:
            with self.subTest(expression=expression):
                parsed = self.module().parse_coordinate(expression)
                self.assertEqual(parsed["normalized"]["magnitude"], magnitude)
                self.assertTrue(any(q["kind"] == kind for q in parsed["qualifiers"]))
                self.assertTrue(
                    all(q["text_without_markup"] in expression for q in parsed["qualifiers"])
                )
                self.assertIsNone(parsed["normalized"]["signed_magnitude"])

    def test_qualifier_support_does_not_consume_extra_numbers_or_unknown_notes(self):
        for expression in (
            "12°50′ with one [vno 2]",
            "12°50′ with both [altero]",
            "12°50′ nearly [fere] 10",
            "12°50′. Altitude 25°30′",
            "12°50′ revised [12 51]",
        ):
            with self.subTest(expression=expression):
                self.assertEqual(
                    self.module().parse_coordinate(expression)["normalized"]["status"],
                    "unsupported",
                )

    def test_grouping_brace_is_retained_without_inventing_a_group(self):
        parsed = self.module().parse_coordinate("{ 18 19⅚")
        self.assertEqual(parsed["normalized"]["magnitude"], "65990")
        self.assertEqual(
            parsed["qualifiers"], [dict(kind="grouping_marker", text_without_markup="{")]
        )
        self.assertNotIn("series_id", parsed)

    def test_controls_link_by_source_identity_and_do_not_define_selection(self):
        obs, texts, spans, controls = self.fixture()
        m = self.module()
        r = m.stage_coordinates(obs, texts, spans, controls, [])
        self.assertEqual(len(r["coordinates"]), 3)
        self.assertEqual(r["summary"]["coordinates_without_workbook_control"], 1)
        self.assertEqual(r["summary"]["inspected_candidate_spans_added"], 0)
        self.assertEqual(r["summary"]["candidate_spans_not_selected"], 1)
        ids = [a["coordinate_id"] for a in r["control_links"]]
        obs2 = copy.deepcopy(obs)
        obs2[0]["value_original"] = "999"
        again = m.stage_coordinates(obs2, texts, spans, controls, [])
        self.assertEqual(ids, [a["coordinate_id"] for a in again["control_links"]])
        self.assertEqual(r["coordinates"][0]["review_scope"], "coordinate_candidate_only")

    def test_reviewed_page_assertion_and_null_clock_preserve_extracted_claims(self):
        obs, texts, spans, controls = self.fixture()
        r = self.module().stage_coordinates(obs, texts, spans, controls, [])
        row = next(a for a in r["coordinates"] if a["legacy_source_record_id"] == "o1")
        self.assertEqual(row["provisional_page"], 457)
        self.assertEqual(row["reviewed_page"], 458)
        self.assertEqual(row["temporal_claims"]["extracted_time_key"], "30000")
        self.assertIsNone(row["temporal_claims"]["reviewed_time_key"])
        self.assertTrue(row["temporal_claims"]["time_reviewed"])
        self.assertEqual(len(r["location_assertions"]), 1)
        self.assertIsNone(r["location_assertions"][0].get("source_expression"))

    def test_raw_source_binding_and_whole_span_review_remain_distinct(self):
        obs, texts, spans, controls = self.fixture()
        reviewed = [dict(id="manual-decl", volume=10, line=2, column=2, quantity="declination")]
        r = self.module().stage_coordinates(obs, texts, spans, controls, reviewed)
        row = next(a for a in r["coordinates"] if a["legacy_source_record_id"] == "o1")
        self.assertEqual(row["reviewed_assertion_id"], "manual-decl")
        bad = copy.deepcopy(obs)
        bad[0]["row_original"] = "a different row"
        pending = self.module().stage_coordinates(bad, texts, spans, controls, [])
        row = next(a for a in pending["coordinates"] if a["legacy_source_record_id"] == "o1")
        self.assertIsNone(row["normalized"]["magnitude"])
        self.assertIn("source_row_binding_unresolved", row["flags"])

    def test_duplicate_control_identity_cannot_hide_a_workbook_row(self):
        obs, texts, spans, controls = self.fixture()
        with self.assertRaises(ValueError):
            self.module().stage_coordinates(obs, texts, spans, [*controls, controls[0]], [])

    def test_explicit_source_identity_link_resolves_prose_column_without_values(self):
        obs, texts, spans, controls = self.fixture()
        text = texts[10]
        sha = hashlib.sha256(text.encode()).hexdigest()
        reviewed = [
            dict(
                id="manual-first",
                volume=10,
                line=4,
                column=1,
                quantity="declination",
                edition_sha256=sha,
                subject="Mars",
                role="reduction",
                normalized={"magnitude": "999"},
            ),
            dict(
                id="manual-other",
                volume=10,
                line=4,
                column=1,
                quantity="declination",
                edition_sha256=sha,
                subject="Mars",
                role="reduction",
                normalized={"magnitude": "1"},
            ),
        ]
        decision = dict(
            id="binding-1",
            source_record_id="o3",
            volume=10,
            line=4,
            edition_sha256=sha,
            evidence_start=4,
            evidence_end=4,
            evidence_sha256=hashlib.sha256(text.splitlines()[3].encode()).hexdigest(),
            reviewed_target="Mars",
            reviewed_role="historical_reduction",
            decision="classify_role",
            basis="final_edition_context",
            reason="The first source reading is selected by printed order.",
            reviewed_assertion_id="manual-first",
            assertion_binding_basis="source_location_and_printed_order",
        )
        m = self.module()
        result = m.stage_coordinates(obs, texts, spans, controls, reviewed, [decision])
        linked = next(r for r in result["coordinates"] if r["legacy_source_record_id"] == "o3")
        self.assertEqual(linked["reviewed_assertion_id"], "manual-first")
        shared = copy.deepcopy(reviewed)
        for r in shared:
            r["column"] = None
        repeated = m.stage_coordinates(obs, texts, spans, controls, shared, [decision])
        self.assertEqual(
            next(r for r in repeated["coordinates"] if r["legacy_source_record_id"] == "o3")[
                "reviewed_assertion_id"
            ],
            "manual-first",
        )
        reviewed.reverse()
        reviewed[0]["normalized"]["magnitude"] = "108120"
        controls[0]["preferred_magnitude_arcsec"] = "1"
        again = m.stage_coordinates(obs, texts, spans, controls, reviewed, [decision])
        self.assertEqual(
            next(r for r in again["coordinates"] if r["legacy_source_record_id"] == "o3")[
                "reviewed_assertion_id"
            ],
            "manual-first",
        )
        for change in (
            {"reviewed_assertion_id": "missing"},
            {"assertion_binding_basis": "angle_agreement"},
            {"reviewed_target": "Sun"},
            {"reviewed_role": "recorded_coordinate"},
        ):
            bad = copy.deepcopy(decision)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.stage_coordinates(obs, texts, spans, controls, reviewed, [bad])
        for change in (
            {"line": 3},
            {"volume": 11},
            {"edition_sha256": "f" * 64},
            {"quantity": "altitude"},
            {"column": 2},
        ):
            bad = copy.deepcopy(reviewed)
            next(r for r in bad if r["id"] == "manual-first").update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.stage_coordinates(obs, texts, spans, controls, bad, [decision])

    def test_context_adjudication_rejects_false_mars_claim_without_discarding_source(self):
        obs, texts, spans, controls = self.fixture()
        text = texts[10]
        decision = dict(
            id="classification-1",
            source_record_id="o3",
            volume=10,
            line=4,
            edition_sha256=hashlib.sha256(text.encode()).hexdigest(),
            evidence_start=4,
            evidence_end=4,
            evidence_sha256=hashlib.sha256(text.splitlines()[3].encode()).hexdigest(),
            reviewed_target="Sun",
            decision="exclude_as_mars_coordinate",
            basis="final_edition_context",
            reason="The quantity belongs to the Sun in its explicit source context.",
        )
        r = self.module().stage_coordinates(obs, texts, spans, controls, [], [decision])
        row = next(a for a in r["coordinates"] if a["legacy_source_record_id"] == "o3")
        self.assertEqual(row["target_claim"], "Mars")
        self.assertEqual(row["reviewed_target"], "Sun")
        self.assertEqual(row["mars_coordinate_selection"], "excluded_other_target")
        self.assertEqual(len(r["coordinates"]), 3)
        self.assertEqual(r["summary"]["inspected_candidate_spans_added"], 0)
        bad = copy.deepcopy(decision)
        bad["evidence_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "[Ff]ingerprint"):
            self.module().stage_coordinates(obs, texts, spans, controls, [], [bad])

    def test_reviewed_reduction_role_does_not_erase_the_original_extractor_claim(self):
        obs, texts, spans, controls = self.fixture()
        text = texts[10]
        decision = dict(
            id="role-1",
            source_record_id="o3",
            volume=10,
            line=4,
            edition_sha256=hashlib.sha256(text.encode()).hexdigest(),
            evidence_start=4,
            evidence_end=4,
            evidence_sha256=hashlib.sha256(text.splitlines()[3].encode()).hexdigest(),
            reviewed_target="Mars",
            reviewed_role="historical_reduction",
            decision="classify_role",
            basis="final_edition_context",
            reason="Source explicitly states a calculation from earlier observations.",
        )
        result = self.module().stage_coordinates(obs, texts, spans, controls, [], [decision])
        row = next(r for r in result["coordinates"] if r["legacy_source_record_id"] == "o3")
        self.assertEqual(row["role_claim"], "derived")
        self.assertEqual(row["reviewed_role"], "historical_reduction")
        self.assertEqual(row["raw_astrometry_selection"], "excluded_reviewed_reduction")
        self.assertEqual(result["summary"]["nonexcluded_coordinates_without_workbook_control"], 1)

        decision["reviewed_role"] = "historical_input"
        again = self.module().stage_coordinates(obs, texts, spans, controls, [], [decision])
        historical_input = next(
            r for r in again["coordinates"] if r["legacy_source_record_id"] == "o3"
        )
        self.assertEqual(
            historical_input["raw_astrometry_selection"], "excluded_reviewed_reduction"
        )
        self.assertEqual(historical_input["role_claim"], "derived")

    def test_workspace_bridge_preserves_benchmark_and_checks_input_versions(self):
        obs, texts, spans, controls = self.fixture()
        m = self.module()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            work = base / "mars"
            benchmark = base / "benchmark"
            source.mkdir()
            work.mkdir()
            benchmark.mkdir()
            relative = obs[0]["source"]
            path = source / relative
            path.parent.mkdir(parents=True)
            path.write_text(texts[10])
            for name, value in [
                ("observations.json", obs),
                ("derived_catalogue.json", controls),
                ("workbook.json", {"sha256": hashlib.sha256(b"fixture").hexdigest()}),
            ]:
                (benchmark / name).write_text(json.dumps(value))
            (benchmark / "raw").mkdir()
            (benchmark / "raw" / "mars.xls").write_bytes(b"fixture")
            before = {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [
                    benchmark / "observations.json",
                    benchmark / "derived_catalogue.json",
                    benchmark / "workbook.json",
                ]
            }
            (work / "inventory_manifest.json").write_text(
                json.dumps(
                    dict(
                        benchmark_artifact_sha256=before,
                        source_hashes={relative: hashlib.sha256(texts[10].encode()).hexdigest()},
                    )
                )
            )
            (work / "witnesses.json").write_text(
                json.dumps(
                    [
                        dict(
                            volume=10,
                            private_source=relative,
                            edition_sha256=hashlib.sha256(texts[10].encode()).hexdigest(),
                        )
                    ]
                )
            )
            (work / "inventory_spans.jsonl").write_text(
                "".join(json.dumps(s) + "\n" for s in spans)
            )
            m.build_staging(source, work, benchmark)
            names = [
                "staged_coordinates.jsonl",
                "staged_coordinates.csv",
                "coordinate_control_links.jsonl",
                "coordinate_staging_manifest.json",
                "public_coordinate_staging_summary.json",
            ]
            snapshot = {n: (work / n).read_bytes() for n in names}
            m.build_staging(source, work, benchmark)
            self.assertEqual(snapshot, {n: (work / n).read_bytes() for n in names})
            self.assertEqual(
                before,
                {n: hashlib.sha256((benchmark / n).read_bytes()).hexdigest() for n in before},
            )
            self.assertEqual(path.read_text(), texts[10])
            with self.assertRaises(ValueError):
                m.build_staging(source, benchmark, benchmark)
            (benchmark / "observations.json").write_text("[]")
            with self.assertRaisesRegex(ValueError, "[Ff]ingerprint"):
                m.build_staging(source, work, benchmark)


if __name__ == "__main__":
    unittest.main()
