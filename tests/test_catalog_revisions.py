"""Reviewed revisions keep every printed value and every earlier interpretation."""

import hashlib
import json
import sqlite3
import unittest

from src.catalog_release import CSV_COLUMNS, SCHEMA, encoded
from src.catalog_revisions import (
    DATE_REVISION,
    READING_REVISION,
    apply_date_revisions,
    apply_reading_revisions,
)
from src.csv_projection import PUBLISHED_REVIEWS, project_csv

SOURCE = "tycho-oo-12"
OLD = "context-v12-" + "0" * 20
SCOPE = "scope"
LINES = [
    "| Observed altitude of the Sun [Altit. ⊙ obſeruata] | 37° 13′ 40″ |",
    "| Refraction, to be removed [Refractio auferenda] | 0′ 23″ |",
    "| | 37°" + chr(0xA0) + "13′" + chr(0x202F) + "17″ |",  # no-break spaces, as in the editions
    "**In the month of March, in the year 1590.** [MENSE MARTIO ANNI 1590.]",
    "| 4 | 2^h^ 46½^m^ [2 46½] | 51° 59′ 35″ |",
    "| 8 51 | 2° 45½′ |",
]
TEXT = "\n".join(LINES)
EDITIONS = {SOURCE: {"sha256": hashlib.sha256(TEXT.encode()).hexdigest(), "lines": LINES}}
READINGS = (
    # name, expression, quantity, role, subject, arcseconds, event, locus
    ("observed", "37° 13′ 40″", "altitude", "recorded_reading", "Sun", "134020", None, None),
    ("refraction", "0′ 23″", "refraction_angle", "historical_correction", "Sun", "23", None, None),
    (
        "result",
        "37° 13′ 17″",
        "refraction_angle",
        "historical_correction",
        "Sun",
        "133997",
        None,
        None,
    ),
    ("march", "51° 59′ 35″", "altitude", "recorded_reading", "Venus", "187175", "event-a", "l1"),
    (
        "clock",
        "2^h^ 46½^m^",
        "recorded_clock",
        "recorded_clock",
        "observing clock",
        None,
        "event-a",
        "l1",
    ),
    ("december", "2° 45½′", "altitude", "recorded_reading", "Venus", "9930", None, "l2"),
)


def reading(name):
    return "assertion-v12-" + name


def stated(identifier, month, day, daypart=None):
    return dict(
        id=identifier,
        volume=12,
        year=1590,
        month=month,
        day=day,
        daypart=daypart,
        calendar="Julian",
        day_origin=None,
        component_status="complete_named_components",
        claim_basis="reviewed_source_context",
        calendar_validation="not_performed",
        accepted_observing_date=None,
        absolute_timestamp=None,
    )


def database():
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    db.execute("INSERT INTO sources VALUES (?,?,?,?,?,?,?)", (SOURCE, "", "", "", "", 12, "{}"))
    claim = stated(OLD, 12, 20)
    db.execute("INSERT INTO dates VALUES (?,?)", (OLD, encoded(claim)))
    db.execute(
        "INSERT INTO contexts VALUES (?,?,?,?,?,?)",
        (OLD, SCOPE, "recorded_date", '{"day":20,"month":12,"year":1590}', SOURCE, "{}"),
    )
    db.execute("INSERT INTO groups VALUES ('event-a',NULL,NULL,'{\"flags\":[]}')")
    db.execute("INSERT INTO group_dates VALUES ('event-a',?)", (OLD,))
    db.execute("INSERT INTO group_contexts VALUES ('event-a',?,?)", (OLD, SCOPE))
    for locus in ("l1", "l2"):
        record = dict(id=locus, context_ids=[dict(context_id=OLD, scope_id=SCOPE)])
        db.execute(
            "INSERT INTO source_loci VALUES (?,?,?,?,?)",
            (locus, SOURCE, 69, "mapped_source_page", encoded(record)),
        )
        db.execute("INSERT INTO locus_contexts VALUES (?,?,?)", (locus, OLD, SCOPE))
    for name, expression, quantity, role, subject, value, event, locus in READINGS:
        identifier = reading(name)
        degree, minute, second = (
            expression.replace("°", "′").replace("″", "").split("′") + [""] * 3
        )[:3]
        components = (
            {}
            if value is None
            else {
                key: part.strip()
                for key, part in (("degree", degree), ("arcminute", minute), ("arcsecond", second))
                if part.strip()
            }
        )
        if value is not None and "°" not in expression:
            components = {"arcminute": "0", "arcsecond": "23"}
        normalized = dict(
            status="exact" if value else "unsupported",
            unit="arcsecond" if value else "second_of_time",
            magnitude=value,
            signed_magnitude=None,
        )
        original = dict(
            id=identifier,
            volume=12,
            printed_page=12,
            quantity=quantity,
            subject=subject,
            reference=None,
            role=role,
            direction=None,
            flags=["not_an_additional_raw_reading"],
            normalized=normalized,
            source_date_claim_ids=[OLD] if locus else [],
        )
        db.execute(
            "INSERT INTO quantities VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                identifier,
                12,
                12,
                expression,
                role,
                event,
                None,
                encoded(original),
                encoded(components),
                "{}",
                SOURCE,
                None,
                identifier,
                None,
                "{}",
                None,
            ),
        )
        db.execute(
            "INSERT INTO interpretations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                identifier,
                0,
                quantity,
                subject,
                None,
                normalized["status"],
                normalized["unit"],
                value,
                None,
                encoded(normalized),
                encoded(components),
                '["not_an_additional_raw_reading"]',
                None,
            ),
        )
        if locus:
            db.execute("INSERT INTO quantity_dates VALUES (?,?)", (identifier, OLD))
            db.execute("INSERT INTO quantity_contexts VALUES (?,?,?)", (identifier, OLD, SCOPE))
            db.execute("INSERT INTO locus_quantities VALUES (?,?)", (locus, identifier))
    db.commit()
    return db


class DatabaseCase(unittest.TestCase):
    def database(self):
        db = database()
        self.addCleanup(db.close)
        return db


def retyping(**changes):
    decision = dict(
        quantity_id=reading("result"),
        source_id=SOURCE,
        printed_page=12,
        source_expression="37° 13′ 17″",
        version=0,
        edition_sha256=EDITIONS[SOURCE]["sha256"],
        previous=dict(
            quantity="refraction_angle", subject="Sun", reference=None, role="historical_correction"
        ),
        revised=dict(quantity="altitude", subject="Sun", reference=None, role="reduction"),
        reckoning=[
            dict(quantity_id=reading("observed"), sign=1),
            dict(quantity_id=reading("refraction"), sign=-1),
        ],
        basis=dict(
            kind="printed_reckoning",
            label="Refractio auferenda",
            lines=[1, 2, 3],
            statement="The unlabeled row is the observed altitude less the refraction above it.",
        ),
    )
    decision.update(changes)
    return decision


def redating(**changes):
    decision = dict(
        source_id=SOURCE,
        edition_sha256=EDITIONS[SOURCE]["sha256"],
        previous_date_claim_id=OLD,
        date=dict(year=1590, month=3, day=4, daypart_original="VESPERI"),
        quantity_ids=[reading("march"), reading("clock")],
        group_ids=["event-a"],
        basis=dict(
            kind="printed_table_column",
            label="MENSE MARTIO ANNI 1590",
            lines=[4, 5],
            statement="The table is headed March 1590 and its first column gives the day.",
        ),
    )
    decision.update(changes)
    return decision


def exported(db, name):
    return next(iter(project_csv(db, CSV_COLUMNS, identifier=reading(name))))


class ProjectionTests(DatabaseCase):
    def test_a_review_of_another_kind_leaves_the_row_as_the_source_recorded_it(self):
        db = self.database()
        identifier = reading("observed")
        recorded = db.execute("SELECT original_json FROM quantities WHERE id=?", (identifier,))
        original = json.loads(recorded.fetchone()[0])
        original["direction"] = "north"
        with db:
            db.execute(
                "UPDATE quantities SET original_json=? WHERE id=?", (encoded(original), identifier)
            )
            db.execute(
                "UPDATE interpretations SET revision_json=? WHERE quantity_id=?",
                ('{"kind":"source_quantity_classification"}', identifier),
            )
        row = exported(db, "observed")
        self.assertEqual(row["direction"], "north")
        self.assertNotIn("interpretation_review", json.loads(row["scientific_metadata_json"]))

    def test_every_reviewed_revision_is_published_with_its_row(self):
        self.assertLessEqual({READING_REVISION, DATE_REVISION}, PUBLISHED_REVIEWS)


class ReadingRevisionTests(DatabaseCase):
    def test_retyped_reading_keeps_its_value_and_its_earlier_interpretation(self):
        db = self.database()
        before = db.execute("SELECT * FROM quantities ORDER BY id").fetchall()
        with db:
            self.assertEqual(
                apply_reading_revisions(db, [retyping()], EDITIONS), [reading("result")]
            )
        self.assertEqual(db.execute("SELECT * FROM quantities ORDER BY id").fetchall(), before)
        versions = db.execute(
            "SELECT version,quantity,value_exact FROM interpretations WHERE quantity_id=? ORDER BY 1",
            (reading("result"),),
        ).fetchall()
        self.assertEqual(versions, [(0, "refraction_angle", "133997"), (1, "altitude", "133997")])
        row = exported(db, "result")
        self.assertEqual(
            (row["quantity"], row["role"], row["original_quantity"], row["interpretation_version"]),
            ("altitude", "reduction", "refraction_angle", 1),
        )
        review = json.loads(row["scientific_metadata_json"])["interpretation_review"]
        self.assertEqual(review["kind"], READING_REVISION)
        self.assertEqual(review["basis"]["source_label"], "Refractio auferenda")
        # The edition's own text and fingerprint stay out of the catalogue.
        self.assertNotIn("lines", review["basis"])
        self.assertNotIn(EDITIONS[SOURCE]["sha256"], encoded(review))

    def test_revisions_that_the_page_does_not_support_are_rejected(self):
        cases = (
            (dict(version=1), "frozen reading"),
            (dict(source_expression="37° 13′ 18″"), "frozen reading"),
            (
                dict(
                    revised=dict(
                        quantity="recorded_clock", subject="Sun", reference=None, role="reduction"
                    )
                ),
                "cannot change the printed value",
            ),
            (dict(reckoning=[dict(quantity_id=reading("observed"), sign=1)]), "does not close"),
            (dict(edition_sha256="0" * 64), "printed evidence"),
            (
                dict(basis=dict(retyping()["basis"], label="Parallaxis addenda")),
                "do not print the reviewed label",
            ),
            (
                dict(basis=dict(retyping()["basis"], lines=[1, 2])),
                "do not print the reviewed label",
            ),
            (dict(withdrawn_flags=["historical_parallax_not_detection"]), "Withdrawn flag"),
        )
        for changes, message in cases:
            db = self.database()
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, message):
                apply_reading_revisions(db, [retyping(**changes)], EDITIONS)

    def test_a_reading_is_revised_once_per_review(self):
        db = self.database()
        with self.assertRaisesRegex(ValueError, "frozen reading"):
            apply_reading_revisions(db, [retyping(), retyping()], EDITIONS)


class DateRevisionTests(DatabaseCase):
    def test_a_whole_group_moves_to_the_date_its_table_prints(self):
        db = self.database()
        with db:
            moved = apply_date_revisions(db, [redating()], EDITIONS)
        self.assertEqual(moved, [reading("march"), reading("clock")])
        (new,) = db.execute("SELECT date_id FROM group_dates WHERE group_id='event-a'").fetchone()
        claim = json.loads(
            db.execute("SELECT data_json FROM dates WHERE id=?", (new,)).fetchone()[0]
        )
        self.assertEqual((claim["year"], claim["month"], claim["day"]), (1590, 3, 4))
        self.assertEqual((claim["daypart"], claim["calendar"]), ("evening", None))
        self.assertEqual(json.loads(exported(db, "march")["date_claims_json"])[0]["month"], 3)
        self.assertEqual(json.loads(exported(db, "december")["date_claims_json"])[0]["month"], 12)
        for query, expected in (
            ("SELECT context_id FROM locus_contexts WHERE locus_id='l1'", new),
            ("SELECT context_id FROM locus_contexts WHERE locus_id='l2'", OLD),
            ("SELECT context_id FROM group_contexts WHERE id='event-a'", new),
            ("SELECT context_id FROM quantity_contexts WHERE id='assertion-v12-clock'", new),
        ):
            self.assertEqual([row[0] for row in db.execute(query)], [expected], query)
        locus = json.loads(
            db.execute("SELECT data_json FROM source_loci WHERE id='l1'").fetchone()[0]
        )
        self.assertEqual(locus["context_ids"], [dict(context_id=new, scope_id=SCOPE)])
        review = json.loads(exported(db, "clock")["scientific_metadata_json"])[
            "interpretation_review"
        ]
        self.assertEqual(
            (review["kind"], review["previous_date_claim_ids"], review["date_claim_ids"]),
            (DATE_REVISION, [OLD], [new]),
        )
        self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_a_date_the_page_does_not_print_for_a_group_is_withdrawn(self):
        db = self.database()
        with db:
            moved = apply_date_revisions(db, [redating(date=None)], EDITIONS)
        self.assertEqual(moved, [reading("march"), reading("clock")])
        for name in ("march", "clock"):
            self.assertEqual(json.loads(exported(db, name)["date_claims_json"]), [])
        self.assertEqual(json.loads(exported(db, "december")["date_claims_json"])[0]["month"], 12)
        for query, expected in (
            ("SELECT date_id FROM group_dates WHERE group_id='event-a'", []),
            ("SELECT date_id FROM quantity_dates WHERE quantity_id='assertion-v12-march'", []),
            ("SELECT context_id FROM locus_contexts WHERE locus_id='l1'", []),
            ("SELECT context_id FROM locus_contexts WHERE locus_id='l2'", [OLD]),
            ("SELECT context_id FROM group_contexts WHERE id='event-a'", []),
            ("SELECT context_id FROM quantity_contexts WHERE id='assertion-v12-clock'", []),
            ("SELECT id FROM dates", [OLD]),
        ):
            self.assertEqual([row[0] for row in db.execute(query)], expected, query)
        locus = json.loads(
            db.execute("SELECT data_json FROM source_loci WHERE id='l1'").fetchone()[0]
        )
        self.assertEqual(locus["context_ids"], [])
        review = json.loads(exported(db, "clock")["scientific_metadata_json"])[
            "interpretation_review"
        ]
        self.assertEqual(
            (review["kind"], review["previous_date_claim_ids"], review["date_claim_ids"]),
            (DATE_REVISION, [OLD], []),
        )
        self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_a_claim_the_source_already_states_is_reused(self):
        db = self.database()
        known = "context-v12-" + "1" * 20
        with db:
            db.execute(
                "INSERT INTO dates VALUES (?,?)",
                (known, encoded(dict(stated(known, 3, 4, "evening"), calendar=None))),
            )
            apply_date_revisions(db, [redating()], EDITIONS)
        self.assertEqual([row[0] for row in db.execute("SELECT date_id FROM group_dates")], [known])
        self.assertEqual(db.execute("SELECT count(*) FROM dates").fetchone()[0], 2)

    def test_a_later_reading_revision_keeps_the_revised_date(self):
        db = self.database()
        with db:
            apply_date_revisions(db, [redating()], EDITIONS)
            apply_reading_revisions(
                db,
                [
                    retyping(
                        quantity_id=reading("march"),
                        source_expression="51° 59′ 35″",
                        version=1,
                        previous=dict(
                            quantity="altitude",
                            subject="Venus",
                            reference=None,
                            role="recorded_reading",
                        ),
                        revised=dict(
                            quantity="altitude",
                            subject="Venus",
                            reference=None,
                            role="repeated_reading",
                        ),
                        reckoning=[],
                        basis=dict(
                            kind="printed_label",
                            label="MENSE MARTIO",
                            lines=[4, 5],
                            statement="The table collects readings printed under their own days.",
                        ),
                    )
                ],
                EDITIONS,
            )
        row = exported(db, "march")
        self.assertEqual((row["role"], row["interpretation_version"]), ("repeated_reading", 2))
        self.assertEqual(json.loads(row["date_claims_json"])[0]["day"], 4)

    def test_partial_groups_and_unprinted_readings_are_rejected(self):
        cases = (
            (dict(quantity_ids=[reading("march")]), "whole group"),
            (dict(group_ids=[]), "frozen reading"),
            (
                dict(quantity_ids=[reading("march"), reading("clock"), reading("december")]),
                "do not print",
            ),
            (
                dict(date=dict(year=1590, month=12, day=20, daypart_original=None)),
                "repeats the prior claim",
            ),
            (
                dict(date=dict(year=1590, month=13, day=4, daypart_original=None)),
                "complete printed components",
            ),
        )
        for changes, message in cases:
            db = self.database()
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, message):
                apply_date_revisions(db, [redating(**changes)], EDITIONS)


if __name__ == "__main__":
    unittest.main()
