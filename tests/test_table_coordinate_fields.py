"""Declared table fields preserve native targets and coordinate conventions."""

import copy
import hashlib
import unittest

from src.assembly import assemble
from src.catalog import compile_catalogue
from src.public_assertions import public_assertion
from src.review_preparation import materialize_review


class TableCoordinateFieldsTests(unittest.TestCase):
    def fixture(self):
        text = (
            "| Sun [Sol] | 12° 30′ 0″ B | ♊ 20° 23′; June 2 |\n"
            "| Mars [Mars] | 0° 10′ 0″ A | ♌ 1° 2′; July 3 |\n"
        )
        sha = hashlib.sha256(text.encode()).hexdigest()
        spans = [dict(id="span", volume=10, edition_sha256=sha, line_start=1, line_end=2)]
        row_context = dict(
            key_prefix="coordinate-row",
            columns=dict(subject_as_printed=1, declination_as_printed=2, longitude_date=3),
        )
        review = dict(
            id="declared-coordinate-fields",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            basis=dict(kind="final_edition_review", printed_page=1),
            assertion_defaults=dict(
                subject=None,
                reference=None,
                direction=None,
                role="historical_input",
                flags=["not_an_additional_raw_reading"],
                row_context=row_context,
                unit_basis="Reviewed native labels, A=south/B=north, and literal zodiac glyphs.",
            ),
            cell_groups=[
                dict(
                    line_range=[1, 2],
                    column=2,
                    quantity="declination",
                    component_units=["degree", "arcminute", "arcsecond"],
                    table_fields=dict(
                        subject_column=1, direction_suffixes=dict(A="south", B="north")
                    ),
                ),
                dict(
                    line_range=[1, 2],
                    column=3,
                    quantity="ecliptic_longitude",
                    component_units=["degree", "arcminute"],
                    table_fields=dict(
                        subject_column=1, zodiac_from_expression=True, value_before=";"
                    ),
                ),
            ],
        )
        return text, spans, review

    def compile(self, text, spans, review):
        materialized = materialize_review(review, text, spans)
        rows = compile_catalogue([materialized], {10: text}, spans)["assertions"]
        return materialized, rows

    def test_range_uses_native_labels_and_each_explicit_hemisphere(self):
        text, spans, review = self.fixture()
        materialized, rows = self.compile(text, spans, review)
        declinations = [r for r in rows if r["quantity"] == "declination"]
        declinations.sort(key=lambda row: row["line"])
        self.assertEqual([r["subject"] for r in declinations], ["Sun", "Mars"])
        self.assertEqual([r["direction"] for r in declinations], ["north", "south"])
        self.assertEqual(
            [r["normalized"]["signed_magnitude"] for r in declinations], ["45000", "-600"]
        )
        self.assertEqual(
            [r["source_expression"] for r in declinations], ["12° 30′ 0″ B", "0° 10′ 0″ A"]
        )
        self.assertEqual(review, self.fixture()[2])
        self.assertTrue(all("table_fields" not in row for row in materialized["assertions"]))

    def test_zodiac_prefix_keeps_the_separate_date_evidence(self):
        text, spans, review = self.fixture()
        materialized, rows = self.compile(text, spans, review)
        longitudes = sorted(
            (r for r in rows if r["quantity"] == "ecliptic_longitude"), key=lambda r: r["line"]
        )
        self.assertEqual([r["source_expression"] for r in longitudes], ["♊ 20° 23′", "♌ 1° 2′"])
        self.assertEqual(
            [r["normalized"]["zodiac_longitude_degrees"] for r in longitudes],
            ["4823/60", "3631/30"],
        )
        contexts = {c["key"]: c for c in materialized["contexts"]}
        self.assertEqual(
            contexts["coordinate-row-1"]["value"]["longitude_date"], "♊ 20° 23′; June 2"
        )
        assembled = assemble({10: text}, rows, [], [], [])
        self.assertTrue(
            all(r["anchor_status"] == "unique_source_interval" for r in assembled["items"])
        )
        self.assertEqual(public_assertion(longitudes[0])["normalized"]["zodiac_sign"], "Gemini")

    def test_declared_hemisphere_prefixes_preserve_native_labels_and_signs(self):
        for north, south in (("B", "A"), ("North", "South")):
            with self.subTest(north=north, south=south):
                text, spans, review = self.fixture()
                text = text.replace("12° 30′ 0″ B", f"{north} 12° 30′ 0″")
                text = text.replace("0° 10′ 0″ A", f"{south} 0° 10′ 0″")
                sha = hashlib.sha256(text.encode()).hexdigest()
                review["edition_sha256"] = spans[0]["edition_sha256"] = sha
                fields = review["cell_groups"][0]["table_fields"]
                fields.pop("direction_suffixes")
                fields["direction_prefixes"] = {north: "north", south: "south"}
                _, rows = self.compile(text, spans, review)
                coordinates = sorted(
                    (r for r in rows if r["quantity"] == "declination"),
                    key=lambda r: r["line"],
                )
                self.assertEqual(
                    [r["normalized"]["signed_magnitude"] for r in coordinates],
                    ["45000", "-600"],
                )
                self.assertEqual(coordinates[0]["source_expression"], f"{north} 12° 30′ 0″")
                for row in coordinates:
                    public_assertion(row)
                for change in (
                    dict(direction="south"),
                    dict(table_fields=dict(direction_prefixes={north: "west"})),
                    dict(table_fields=dict(direction_prefixes={"Unknown": "north"})),
                    dict(
                        table_fields=dict(
                            direction_prefixes={north: "north", south: "south"},
                            direction_suffixes={"B": "north"},
                        )
                    ),
                ):
                    invalid = copy.deepcopy(review)
                    invalid["cell_groups"][0].update(change)
                    with self.subTest(change=change), self.assertRaises(ValueError):
                        self.compile(text, spans, invalid)
                invalid_text = text.replace(f"{north} 12°", f"{north} {south} 12°")
                invalid = copy.deepcopy(review)
                invalid_sha = hashlib.sha256(invalid_text.encode()).hexdigest()
                invalid["edition_sha256"] = invalid_sha
                invalid_spans = [dict(spans[0], edition_sha256=invalid_sha)]
                with self.assertRaises(ValueError):
                    self.compile(invalid_text, invalid_spans, invalid)

    def test_explicit_target_direction_and_zodiac_cannot_be_overwritten(self):
        text, spans, review = self.fixture()
        for group, field, value in (
            (0, "subject", "Venus"),
            (0, "direction", "south"),
            (1, "zodiac_sign", "Taurus"),
        ):
            altered = copy.deepcopy(review)
            altered["cell_groups"][group][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.compile(text, spans, altered)

    def test_unknown_direction_or_multiple_signs_remain_review_required(self):
        text, spans, review = self.fixture()
        for changed in (text.replace("0″ A", "0″ ?"), text.replace("♊ 20°", "♊ [recte: ♋] 20°")):
            sha = hashlib.sha256(changed.encode()).hexdigest()
            altered = copy.deepcopy(review)
            altered["edition_sha256"] = sha
            altered_spans = [dict(spans[0], edition_sha256=sha)]
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.compile(changed, altered_spans, altered)

    def test_dynamic_fields_need_physical_columns_and_retained_evidence(self):
        text, spans, review = self.fixture()
        for change in (
            dict(table_fields=dict(subject_column=True)),
            dict(table_fields=dict(subject_column=9)),
            dict(table_fields=dict(subject_column=1), row_context=None),
            dict(table_fields=dict(value_before=":")),
            dict(table_fields=dict(zodiac_from_expression=False)),
            dict(table_fields=dict(direction_suffixes=dict(A="west"))),
        ):
            altered = copy.deepcopy(review)
            altered["cell_groups"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.compile(text, spans, altered)

    def test_native_subjects_work_with_split_coordinate_columns(self):
        _, spans, review = self.fixture()
        text = "| Sun | 12 | 30 | 0 |\n| Mars | 0 | 10 | 0 |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        review["edition_sha256"] = spans[0]["edition_sha256"] = sha
        review["cell_groups"] = [
            dict(
                line_range=[1, 2],
                column=None,
                source_columns=[2, 3, 4],
                quantity="declination",
                component_units=["degree", "arcminute", "arcsecond"],
                row_context=dict(key_prefix="split-row", columns=dict(subject_as_printed=1)),
                table_fields=dict(subject_column=1),
            )
        ]
        _, rows = self.compile(text, spans, review)
        rows.sort(key=lambda row: row["line"])
        self.assertEqual([r["subject"] for r in rows], ["Sun", "Mars"])
        self.assertEqual([r["normalized"]["magnitude"] for r in rows], ["45000", "600"])
        self.assertTrue(
            all(
                r["anchor_status"] == "unique_source_interval"
                for r in assemble({10: text}, rows, [], [], [])["items"]
            )
        )
        for row in rows:
            public_assertion(row)
        review["cell_groups"][0]["table_fields"]["direction_suffixes"] = dict(A="south")
        with self.assertRaises(ValueError):
            self.compile(text, spans, review)

    def test_constellation_scope_preserves_qualified_native_magnitude_labels(self):
        _, spans, review = self.fixture()
        text = "| Eye [queried] | 3 |\n| Tail | 4 |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        review["edition_sha256"] = spans[0]["edition_sha256"] = sha
        review["cell_groups"] = [
            dict(
                line_range=[1, 2],
                column=2,
                quantity="stellar_magnitude_class",
                component_units=["scalar"],
                row_context=dict(key_prefix="magnitude-row", columns=dict(subject_as_printed=1)),
                table_fields=dict(subject_column=1, subject_prefix="Taurus"),
            )
        ]
        _, rows = self.compile(text, spans, review)
        rows.sort(key=lambda row: row["line"])
        self.assertEqual([r["subject"] for r in rows], ["Taurus: Eye [queried]", "Taurus: Tail"])
        self.assertEqual([r["normalized"]["magnitude"] for r in rows], ["3", "4"])
        self.assertEqual(rows[0]["normalized"]["unit"], "source_visual_magnitude_class")
        for prefix in (True, "", "Taurus\nAries"):
            invalid = copy.deepcopy(review)
            invalid["cell_groups"][0]["table_fields"]["subject_prefix"] = prefix
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                self.compile(text, spans, invalid)
        invalid = copy.deepcopy(review)
        invalid["cell_groups"][0]["table_fields"].pop("subject_column")
        with self.assertRaises(ValueError):
            self.compile(text, spans, invalid)

    def test_split_latitudes_use_their_own_printed_hemisphere_column(self):
        _, spans, review = self.fixture()
        text = "| Sun | 0 | 10 | 0 | A |\n| Mars | 1 | 0 | 0 | B |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        review["edition_sha256"] = spans[0]["edition_sha256"] = sha
        review["cell_groups"] = [
            dict(
                line_range=[1, 2],
                column=None,
                source_columns=[2, 3, 4],
                quantity="ecliptic_latitude",
                component_units=["degree", "arcminute", "arcsecond"],
                row_context=dict(key_prefix="latitude-row", columns=dict(subject=1, hemisphere=5)),
                table_fields=dict(
                    subject_column=1,
                    direction_column=dict(column=5, values=dict(A="south", B="north")),
                ),
            )
        ]
        _, rows = self.compile(text, spans, review)
        rows.sort(key=lambda row: row["line"])
        self.assertEqual([r["direction"] for r in rows], ["south", "north"])
        self.assertEqual([r["normalized"]["signed_magnitude"] for r in rows], ["-600", "3600"])
        for row in rows:
            public_assertion(row)
        for change in ("unknown", "missing_evidence", "conflict", "wrong_quantity"):
            invalid = copy.deepcopy(review)
            group = invalid["cell_groups"][0]
            if change == "unknown":
                del group["table_fields"]["direction_column"]["values"]["A"]
            elif change == "missing_evidence":
                del group["row_context"]["columns"]["hemisphere"]
            elif change == "conflict":
                group["direction"] = "north"
            else:
                group["quantity"] = "right_ascension"
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.compile(text, spans, invalid)
        for qualification in ("[?]", "[recte: B]"):
            changed = text.replace("| A |", f"| A {qualification} |")
            changed_sha = hashlib.sha256(changed.encode()).hexdigest()
            invalid = copy.deepcopy(review)
            invalid["edition_sha256"] = changed_sha
            changed_spans = [dict(spans[0], edition_sha256=changed_sha)]
            with self.subTest(qualification=qualification), self.assertRaises(ValueError):
                self.compile(changed, changed_spans, invalid)

    def test_explicit_blank_hemisphere_policy_keeps_the_signed_value_unknown(self):
        _, spans, review = self.fixture()
        text = "| Sun | 0 10 | |\n| Mars | 1 0 | B |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        review["edition_sha256"] = spans[0]["edition_sha256"] = sha
        review["cell_groups"] = [
            dict(
                line_range=[1, 2],
                column=2,
                quantity="declination",
                component_units=["degree", "arcminute"],
                row_context=dict(
                    key_prefix="blank-direction-row", columns=dict(star=1, hemisphere=3)
                ),
                table_fields=dict(
                    subject_column=1,
                    direction_column=dict(column=3, values={"": None, "B": "north"}),
                ),
            )
        ]
        _, rows = self.compile(text, spans, review)
        rows.sort(key=lambda row: row["line"])
        self.assertEqual([r["normalized"]["magnitude"] for r in rows], ["600", "3600"])
        self.assertEqual([r["normalized"]["signed_magnitude"] for r in rows], [None, "3600"])
        for row in rows:
            public_assertion(row)
        for assigned in ("north", "south"):
            invalid = copy.deepcopy(review)
            invalid["cell_groups"][0]["table_fields"]["direction_column"]["values"][""] = assigned
            with self.subTest(assigned=assigned), self.assertRaises(ValueError):
                self.compile(text, spans, invalid)

    def test_native_altitude_targets_do_not_acquire_coordinate_hemispheres(self):
        text, spans, review = self.fixture()
        text = text.replace("0″ B", "0″").replace("0″ A", "0″")
        sha = hashlib.sha256(text.encode()).hexdigest()
        review["edition_sha256"] = spans[0]["edition_sha256"] = sha
        review["cell_groups"] = [review["cell_groups"][0]]
        group = review["cell_groups"][0]
        group.update(quantity="altitude", table_fields=dict(subject_column=1))
        _, rows = self.compile(text, spans, review)
        rows.sort(key=lambda row: row["line"])
        self.assertEqual([r["subject"] for r in rows], ["Sun", "Mars"])
        self.assertEqual([r["normalized"]["magnitude"] for r in rows], ["45000", "600"])
        for row in rows:
            self.assertIsNone(row["direction"])
            public_assertion(row)
        group["table_fields"]["direction_suffixes"] = dict(A="south", B="north")
        with self.assertRaises(ValueError):
            self.compile(text, spans, review)

    def test_omitting_empty_columns_keeps_zeroes_and_incomplete_written_values(self):
        _, spans, review = self.fixture()
        text = (
            "| Sun | 12 | 30 | 0 |\n| Mars | | | |\n| Venus | 13 | 20 | |\n| Moon | 0 | 0 | 0 |\n"
        )
        sha = hashlib.sha256(text.encode()).hexdigest()
        review["edition_sha256"] = spans[0]["edition_sha256"] = sha
        review["line_end"] = spans[0]["line_end"] = 4
        review["cell_groups"] = [
            dict(
                line_range=[1, 4],
                column=None,
                source_columns=[2, 3, 4],
                quantity="altitude",
                component_units=["degree", "arcminute", "arcsecond"],
                omit_empty_source_columns=True,
                incomplete_component_policy="unresolved",
                row_context=dict(key_prefix="optional-angle-row", columns=dict(star=1)),
                table_fields=dict(subject_column=1),
            )
        ]
        _, rows = self.compile(text, spans, review)
        rows.sort(key=lambda row: row["line"])
        self.assertEqual([r["subject"] for r in rows], ["Sun", "Venus", "Moon"])
        self.assertEqual([r["normalized"]["magnitude"] for r in rows], ["45000", None, "0"])
        self.assertIn("13", rows[1]["source_expression"])
        for row in rows:
            public_assertion(row)
        for option in (False, 1):
            invalid = copy.deepcopy(review)
            invalid["cell_groups"][0]["omit_empty_source_columns"] = option
            with self.subTest(option=option), self.assertRaises(ValueError):
                self.compile(text, spans, invalid)
        changed = text.replace("13 | 20 |", "13 | |")
        changed_sha = hashlib.sha256(changed.encode()).hexdigest()
        invalid = copy.deepcopy(review)
        invalid["edition_sha256"] = changed_sha
        with self.assertRaises(ValueError):
            self.compile(changed, [dict(spans[0], edition_sha256=changed_sha)], invalid)

    def test_optional_split_suffix_preserves_unmarked_and_rejects_queried_directions(self):
        _, spans, review = self.fixture()
        text = "| Sun | 0 | 10 | 0 A |\n| Mars | 1 | 0 | 0 |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        review["edition_sha256"] = spans[0]["edition_sha256"] = sha
        review["cell_groups"] = [
            dict(
                line_range=[1, 2],
                column=None,
                source_columns=[2, 3, 4],
                quantity="declination",
                component_units=["degree", "arcminute", "arcsecond"],
                row_context=dict(key_prefix="optional-suffix-row", columns=dict(star=1)),
                table_fields=dict(
                    subject_column=1,
                    direction_suffixes=dict(A="south", B="north"),
                    unmarked_direction="unknown",
                ),
            )
        ]
        _, rows = self.compile(text, spans, review)
        rows.sort(key=lambda row: row["line"])
        self.assertEqual([r["normalized"]["signed_magnitude"] for r in rows], ["-600", None])
        for row in rows:
            public_assertion(row)
        for suffix in ("X", "A [?]", "A [recte: B]"):
            changed = text.replace("0 A", "0 " + suffix)
            changed_sha = hashlib.sha256(changed.encode()).hexdigest()
            invalid = copy.deepcopy(review)
            invalid["edition_sha256"] = changed_sha
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                self.compile(changed, [dict(spans[0], edition_sha256=changed_sha)], invalid)
        invalid = copy.deepcopy(review)
        invalid["cell_groups"][0]["table_fields"]["unmarked_direction"] = "north"
        with self.assertRaises(ValueError):
            self.compile(text, spans, invalid)
