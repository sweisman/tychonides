import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path


class AssemblyTests(unittest.TestCase):
    def test_unique_physical_cell_keeps_authority_over_legacy_offset_hints(self):
        text = "| 5 | 14′ 20″ | 20 |\n"
        row = dict(
            id="a",
            volume=10,
            edition_sha256=hashlib.sha256(text.encode()).hexdigest(),
            line=1,
            column=3,
            source_expression="20",
            quantity="source_scalar",
        )
        expected = self.module().assemble({10: text}, [row], [], [], [])["items"][0]
        hint = text.index("20")
        bound = self.module().assemble(
            {10: text}, [dict(row, char_start=hint, char_end=hint + 2)], [], [], []
        )["items"][0]
        self.assertEqual(bound["anchor_status"], "unique_source_interval")
        self.assertEqual(bound["candidate_intervals"], expected["candidate_intervals"])
        self.assertEqual(bound["interval_anchor_id"], expected["interval_anchor_id"])

    def test_reviewed_cell_offsets_distinguish_equal_native_labels(self):
        text = "| 25 | 25 25 |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        base = dict(
            id="a",
            volume=10,
            edition_sha256=sha,
            line=1,
            column=2,
            source_expression="25",
            quantity="source_scalar",
        )
        positions = (text.index("25", 5), text.rindex("25"))
        anchors = []
        for start in positions:
            row = dict(base, char_start=start, char_end=start + 2)
            item = self.module().assemble({10: text}, [row], [], [], [])["items"][0]
            self.assertEqual(item["anchor_status"], "unique_source_interval")
            self.assertEqual(
                item["candidate_intervals"], [{"char_start": start, "char_end": start + 2}]
            )
            anchors.append(item["interval_anchor_id"])
        self.assertNotEqual(*anchors)
        item = self.module().assemble({10: text}, [base], [], [], [])["items"][0]
        self.assertEqual(item["anchor_status"], "ambiguous_literal_occurrences")
        for start, end in ((2, 4), (positions[0], positions[0] + 1), (-1, 1)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                self.module().assemble(
                    {10: text}, [dict(base, char_start=start, char_end=end)], [], [], []
                )

    def test_explicit_ordinal_degree_binding_preserves_whole_number(self):
        for text, start, accepted in (
            ("the 22nd degree", 4, True),
            ("the 122nd degree", 5, False),
            ("the 22nd degree", 4, False),
        ):
            row = dict(
                id="a",
                volume=10,
                edition_sha256=hashlib.sha256(text.encode()).hexdigest(),
                line=1,
                source_expression="22",
                quantity="ecliptic_longitude" if accepted or start == 5 else "recorded_clock",
                components={"degree": "22"},
                char_start=start,
                char_end=start + 2,
            )
            with self.subTest(text=text, quantity=row["quantity"]):
                if accepted:
                    result = self.module().assemble({10: text}, [row], [], [], [])
                    self.assertEqual(result["items"][0]["anchor_status"], "unique_source_interval")
                else:
                    with self.assertRaisesRegex(ValueError, "[Bb]inding"):
                        self.module().assemble({10: text}, [row], [], [], [])

    def test_reviewed_time_binds_after_attached_Hora_label_without_changing_role(self):
        text = "Hora9 M.9½ Mars on the meridian\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        for quantity in ("recorded_clock", "hour_angle"):
            row = dict(
                id="a",
                volume=10,
                edition_sha256=sha,
                line=1,
                source_expression="9 M.9½",
                quantity=quantity,
            )
            with self.subTest(quantity=quantity):
                item = self.module().assemble({10: text}, [row], [], [], [])["items"][0]
                self.assertEqual(item["quantity_claim"], quantity)
                self.assertEqual(item["anchor_status"], "unique_source_interval")
                interval = item["candidate_intervals"][0]
                self.assertEqual(
                    (interval["char_start"], text[interval["char_start"] : interval["char_end"]]),
                    (4, "9 M.9½"),
                )
                explicit = dict(row, char_start=4, char_end=10)
                bound = self.module().assemble({10: text}, [explicit], [], [], [])["items"][0]
                self.assertEqual(bound["interval_anchor_id"], item["interval_anchor_id"])

    def test_attached_Hora_binding_rejects_partial_numbers_and_nontime_quantities(self):
        for text, quantity in [
            ("Hora19 M.9½\n", "recorded_clock"),
            ("Other9 M.9½\n", "recorded_clock"),
            ("Hora9 M.9½0\n", "recorded_clock"),
            ("Hora9 M.9½\n", "declination"),
        ]:
            sha = hashlib.sha256(text.encode()).hexdigest()
            row = dict(
                id="a",
                volume=10,
                edition_sha256=sha,
                line=1,
                source_expression="9 M.9½",
                quantity=quantity,
            )
            with (
                self.subTest(text=text, quantity=quantity),
                self.assertRaisesRegex(ValueError, "[Bb]inding"),
            ):
                self.module().assemble({10: text}, [row], [], [], [])

    def module(self):
        try:
            return importlib.import_module("src.assembly")
        except ModuleNotFoundError:
            self.fail("Catalogue context and assembly layer is not implemented")

    def fixture(self):
        text = "## Observations of the year 1585\n### DIE 21 JANUARIJ\n| H. M. | Declination of Mars |\n|---|---|\n| 8 20 | 17 20¼ |\nPro loco Mars ad diem 12 Februarii\nDeclination 18 2\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        norm = {"status": "exact", "magnitude": "62415", "unit": "arcsecond"}
        reviewed = [
            dict(
                id="a",
                volume=10,
                edition_sha256=sha,
                line=5,
                source_expression="17 20¼",
                quantity="declination",
                normalized=norm,
            )
        ]
        coordinate = [
            dict(
                id="c",
                volume=10,
                edition_sha256=sha,
                line=5,
                column=2,
                source_expression="17 20¼",
                quantity_claim="declination",
                normalized=norm,
            )
        ]
        cells = [
            dict(
                id="t",
                volume=10,
                edition_sha256=sha,
                line=5,
                column=2,
                row_kind="data",
                contains_number=True,
                numeric_placeholder=False,
                source_expression="17 20¼",
                quantity_claim="declination",
                normalized=norm,
            )
        ]
        return text, reviewed, coordinate, cells

    def test_date_and_calculation_epoch_contexts_remain_distinct(self):
        text, *_ = self.fixture()
        m = self.module()
        registry = m.build_contexts({10: text})
        observation = m.context_at(registry, 10, 5)
        calculation = m.context_at(registry, 10, 7)
        self.assertEqual(observation["recorded_year_claim"], 1585)
        self.assertIn("DIE 21 JANUARIJ", observation["date_heading_label"])
        self.assertIsNone(observation["accepted_observing_date"])
        self.assertEqual(
            calculation["date_context_applicability"], "preceding_heading_only_calculation_scope"
        )
        self.assertIsNotNone(calculation["calculation_context_id"])
        self.assertNotEqual(calculation["calculation_context_id"], calculation["date_context_id"])
        self.assertIsNone(calculation["calendar"])

    def test_date_heading_does_not_remove_same_level_planetary_scope(self):
        text = "## Observations of the Moon\n## DIE 2 JANUARIJ\nDeclination 27 24\n# References\nOther text\n"
        m = self.module()
        r = m.build_contexts({13: text})
        first = m.context_at(r, 13, 3)
        last = m.context_at(r, 13, 5)
        self.assertEqual(first["section_heading_labels"], ["## Observations of the Moon"])
        self.assertIsNone(last["date_context_id"])

    def test_weekday_and_relative_daypart_labels_keep_a_source_context_chain(self):
        text = "## Observations of Mars\n### Tuesday 10 November, in the evening\nValue\n### After noon\nAnother value\n"
        m = self.module()
        r = m.build_contexts({12: text})
        first = m.context_at(r, 12, 3)
        second = m.context_at(r, 12, 5)
        self.assertIsNotNone(first["date_context_id"])
        self.assertIn("Tuesday", first["date_heading_label"])
        node = r["by_id"][second["date_context_id"]]
        self.assertEqual(node["preceding_date_context_id"], first["date_context_id"])
        self.assertEqual(node["date_label_kind"], "relative_or_daypart")
        self.assertIsNone(second["accepted_observing_date"])

    def test_new_top_level_year_does_not_keep_previous_planetary_section(self):
        text = "## Observations of Mars\n### Observations of the year 1585\nValue\n# Observations of the year 1586\nAnother value\n"
        m = self.module()
        registry = m.build_contexts({10: text})
        self.assertEqual(
            m.context_at(registry, 10, 3)["section_heading_labels"], ["## Observations of Mars"]
        )
        self.assertEqual(m.context_at(registry, 10, 5)["section_heading_labels"], [])

    def test_cell_overlap_is_linked_by_location_without_merging_quantities(self):
        text, reviewed, coordinates, cells = self.fixture()
        m = self.module()
        r = m.assemble({10: text}, reviewed, coordinates, cells, [])
        self.assertEqual(len(r["items"]), 3)
        self.assertEqual(len({i["cell_anchor_id"] for i in r["items"]}), 1)
        self.assertTrue(any(x["relation"] == "same_source_interval" for x in r["links"]))
        coordinates[0]["normalized"]["magnitude"] = "999"
        again = m.assemble({10: text}, reviewed, coordinates, cells, [])
        self.assertEqual(r["links"], again["links"])

    def test_repeated_literal_is_not_resolved_by_numerical_agreement(self):
        text = "Declination 17 20¼ [Declin. 17 20¼]\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        row = dict(
            id="a",
            volume=10,
            edition_sha256=sha,
            line=1,
            source_expression="17 20¼",
            quantity="declination",
        )
        r = self.module().assemble({10: text}, [row], [], [], [])
        self.assertEqual(r["items"][0]["anchor_status"], "ambiguous_literal_occurrences")
        self.assertEqual(len(r["items"][0]["candidate_intervals"]), 2)
        self.assertIsNone(r["items"][0]["interval_anchor_id"])

    def test_missing_distance_placeholder_binds_when_joined_to_label_and_footnote(self):
        for expression in ("...", "…"):
            text = "H. 10⅓ Distance with the Radius" + expression + "¹\n"
            sha = hashlib.sha256(text.encode()).hexdigest()
            row = dict(
                id="a",
                volume=13,
                edition_sha256=sha,
                line=1,
                source_expression=expression,
                quantity="angular_separation",
                normalized=dict(status="incomplete", magnitude=None, unit="arcsecond"),
            )
            with self.subTest(expression=expression):
                result = self.module().assemble({13: text}, [row], [], [], [])
                item = result["items"][0]
                self.assertEqual(item["anchor_status"], "unique_source_interval")
                interval = item["candidate_intervals"][0]
                self.assertEqual(text[interval["char_start"] : interval["char_end"]], expression)
        self.assertEqual(self.module().literal_intervals("Radius....¹", "..."), [])

    def test_numeric_prefix_cannot_bind_to_a_different_longer_number(self):
        text = "3 47½\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        row = dict(
            id="a",
            volume=10,
            edition_sha256=sha,
            line=1,
            source_expression="3 4",
            quantity="angular_separation",
        )
        with self.assertRaisesRegex(ValueError, "[Bb]inding"):
            self.module().assemble({10: text}, [row], [], [], [])
        with self.assertRaisesRegex(ValueError, "[Bb]inding"):
            self.module().assemble({10: text}, [dict(row, char_start=0, char_end=3)], [], [], [])

    def test_literal_search_preserves_overlaps_unicode_and_word_boundaries(self):
        for text, expression, expected in (
            ("::::", "::", [(0, 2), (1, 3), (2, 4)]),
            ("α12 12 12β 12_ 12", "12", [(4, 6), (15, 17)]),  # noqa: RUF001 - intentional Greek boundaries
            ("1/2 1/2", "1/2", [(0, 3), (4, 7)]),
            ("(a.b) aXb", "a.b", [(1, 4)]),
            ("ſ1 1½ 1", "1", [(6, 7)]),
            ("á a", "a", [(0, 1), (3, 4)]),
            ("x... ...x ...", "...", [(1, 4), (5, 8), (10, 13)]),
            (".... … …...", "...", []),
            ("anything", "", []),
        ):
            with self.subTest(text=text, expression=expression):
                self.assertEqual(self.module().literal_intervals(text, expression), expected)

    def test_reviewed_subcell_literals_are_confined_to_the_claimed_cell(self):
        text = "| 6 48 | Declination 1°31′ north [Decl. 1 31 B.] |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        row = dict(
            id="a",
            volume=11,
            edition_sha256=sha,
            line=1,
            column=2,
            source_expression="1°31′",
            quantity="declination",
        )
        result = self.module().assemble({11: text}, [row], [], [], [])
        item = result["items"][0]
        interval = item["candidate_intervals"][0]
        self.assertEqual(text[interval["char_start"] : interval["char_end"]], "1°31′")
        self.assertIsNotNone(item["cell_anchor_id"])
        row["column"] = 1
        with self.assertRaises(ValueError):
            self.module().assemble({11: text}, [row], [], [], [])
        row.update(column=2, source_expression="1 3")
        with self.assertRaises(ValueError):
            self.module().assemble({11: text}, [row], [], [], [])

    def test_reviewed_single_field_prose_binds_literals_without_inventing_table_cells(self):
        text = "Subtract about 2′ from the declination.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        row = dict(
            id="a",
            volume=12,
            edition_sha256=sha,
            line=1,
            column=1,
            source_expression="2′",
            quantity="declination_correction",
        )
        result = self.module().assemble({12: text}, [row], [], [], [])
        item = result["items"][0]
        interval = item["candidate_intervals"][0]
        self.assertEqual(text[interval["char_start"] : interval["char_end"]], "2′")
        self.assertIsNone(item["cell_anchor_id"])
        self.assertIsNotNone(item["interval_anchor_id"])
        self.assertEqual(row["column"], 1)
        for column in (0, 2):
            with self.subTest(column=column), self.assertRaises(ValueError):
                self.module().assemble({12: text}, [dict(row, column=column)], [], [], [])
        with self.assertRaises(ValueError):
            self.module().assemble({12: text}, [], [row], [], [])
        repeated = "Exceeds by 1 56 [superet 1 56].\n"
        row.update(
            edition_sha256=hashlib.sha256(repeated.encode()).hexdigest(),
            source_expression="1 56",
            quantity="longitude_difference",
        )
        item = self.module().assemble({12: repeated}, [row], [], [], [])["items"][0]
        self.assertEqual(item["anchor_status"], "ambiguous_literal_occurrences")
        self.assertEqual(len(item["candidate_intervals"]), 2)
        self.assertIsNone(item["cell_anchor_id"])
        self.assertIsNone(item["interval_anchor_id"])

    def test_subcell_review_keeps_parallel_locations_but_other_layers_require_whole_cells(self):
        text = "| Declination 17 20¼ [Decl. 17 20¼] |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        row = dict(
            id="a",
            volume=11,
            edition_sha256=sha,
            line=1,
            column=1,
            source_expression="17 20¼",
            quantity="declination",
        )
        result = self.module().assemble({11: text}, [row], [], [], [])
        self.assertEqual(len(result["items"][0]["candidate_intervals"]), 2)
        self.assertIsNone(result["items"][0]["interval_anchor_id"])
        with self.assertRaises(ValueError):
            self.module().assemble({11: text}, [], [row], [], [])

    def test_unknown_narrative_time_stays_without_accepted_timestamp(self):
        text = "H. 8 M. 22\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        row = dict(
            id="n",
            volume=10,
            edition_sha256=sha,
            line=1,
            char_start=0,
            char_end=10,
            source_expression="H. 8 M. 22",
            quantity_claim="hour_angle",
            temporal_role_claim="hour_angle_candidate",
        )
        r = self.module().assemble({10: text}, [], [], [], [row])
        self.assertIsNone(r["items"][0]["source_context"]["absolute_timestamp"])
        self.assertIsNone(r["items"][0]["source_context"]["accepted_observing_date"])

    def test_edition_issue_links_use_source_locus_and_keep_view_values(self):
        text, reviewed, coordinates, cells = self.fixture()
        sha = hashlib.sha256(text.encode()).hexdigest()
        issue = dict(
            id="issue-1",
            status="confirmed_internal_numeric_mismatch",
            volume=10,
            source_sha256=sha,
            source_line=5,
            source_column=2,
        )
        r = self.module().assemble({10: text}, reviewed, coordinates, cells, [], [issue])
        self.assertTrue(all(i["edition_issue_ids"] == ["issue-1"] for i in r["items"]))
        self.assertTrue(all(i["normalized"]["magnitude"] == "62415" for i in r["items"]))

    def test_workspace_assembly_verifies_upstream_versions_and_repeats(self):
        text, reviewed, coordinates, cells = self.fixture()
        sha = hashlib.sha256(text.encode()).hexdigest()
        m = self.module()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            work = base / "mars"
            source.mkdir()
            work.mkdir()
            relative = "brahe/thesaurus_observationum_vol1/translation/brahe_thesaurus_observationum_vol1_prepub.md"
            path = source / relative
            path.parent.mkdir(parents=True)
            path.write_text(text)
            (work / "witnesses.json").write_text(
                json.dumps([dict(volume=10, private_source=relative, edition_sha256=sha)])
            )
            (work / "inventory_manifest.json").write_text(
                json.dumps(dict(source_hashes={relative: sha}))
            )
            files = {
                "assertions.jsonl": reviewed,
                "staged_coordinates.jsonl": coordinates,
                "table_cells.jsonl": cells,
                "narrative_expressions.jsonl": [],
                "coordinate_control_links.jsonl": [dict(pafko_id="p1", coordinate_id="c")],
            }
            for name, rows in files.items():
                (work / name).write_text("".join(json.dumps(r) + "\n" for r in rows))
            layers = {
                "catalogue_manifest.json": ["assertions.jsonl"],
                "coordinate_staging_manifest.json": [
                    "staged_coordinates.jsonl",
                    "coordinate_control_links.jsonl",
                ],
                "table_staging_manifest.json": ["table_cells.jsonl"],
                "narrative_staging_manifest.json": ["narrative_expressions.jsonl"],
            }
            for name, names in layers.items():
                (work / name).write_text(
                    json.dumps(
                        dict(
                            output_hashes={
                                n: hashlib.sha256((work / n).read_bytes()).hexdigest()
                                for n in names
                            }
                        )
                    )
                )
            m.build_assembly(source, work)
            names = [
                "catalogue_items.jsonl",
                "catalogue_items.csv",
                "catalogue_links.jsonl",
                "source_contexts.jsonl",
                "assembly_manifest.json",
            ]
            snapshot = {n: (work / n).read_bytes() for n in names}
            m.build_assembly(source, work)
            self.assertEqual(snapshot, {n: (work / n).read_bytes() for n in names})
            self.assertNotIn("text_original", (work / "public_assembly_summary.json").read_text())
            self.assertEqual(path.read_text(), text)
            (work / "table_cells.jsonl").write_text("")
            with self.assertRaisesRegex(ValueError, "[Ff]ingerprint"):
                m.build_assembly(source, work)


if __name__ == "__main__":
    unittest.main()
