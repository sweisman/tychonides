"""Reviewed revisions keep every printed value and every earlier interpretation."""

import hashlib
import json
import sqlite3
import unittest

from src.catalog_release import CSV_COLUMNS, SCHEMA, encoded
from src.catalog_revisions import (
    DATE_REVISION,
    EDITION_READING,
    READING_REVISION,
    REVIEWED_KINDS,
    apply_date_revisions,
    apply_edition_readings,
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
    "its longitude from the mean equinox is composed as 5s 9° 9′ 25″, aggregated as 6° 24⅓′ nearly.",
    "the distance between the limits, which is 3° 15′ of the circle.",
    "there come 2 days 2 hours 11⅗, and the interval of 733,805 days 16h 54′ 13″ holds them.",
    "| 19 | 1 | 27 | 33 | 20 | 41 | 24 [recte: 4] |",
    "the year holds 365 days, 5^h^ 56^m^ 53^s^; at its least it adds to these a further 24^m^ 38^s^.",
    "| The first star | 7^h^ | 12^m^ |",
    "| The second star | | 29^m^ |",
    "the month runs to 29 days, 12^h^ 44^m^ 3^s^ 10‴ 58⁗ [recte: 38⁗] 10^v^.",
    "| From the Prutenic, Mästlin's [E Prutenico Mæſtlini] | 51° 59′ 35″ | 2° 45½′ |",
    "| From our Tables [Ex Tabulis noſtris] | 2° 45½′ |",
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


def southward(**changes):
    decision = dict(
        quantity_id=reading("december"),
        source_id=SOURCE,
        printed_page=12,
        source_expression="2° 45½′",
        version=0,
        edition_sha256=EDITIONS[SOURCE]["sha256"],
        previous=dict(
            quantity="altitude", subject="Venus", reference=None, role="recorded_reading"
        ),
        revised=dict(
            quantity="declination", subject="Venus", reference=None, role="recorded_coordinate"
        ),
        direction=dict(previous=None, revised="south", label="8 51"),
        basis=dict(
            kind="printed_label",
            label="8 51",
            lines=[6],
            statement="The row names the declination and prints it on this side of the equator.",
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
        self.assertLessEqual(set(REVIEWED_KINDS), PUBLISHED_REVIEWS)


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

    def test_a_printed_direction_is_set_and_one_printed_for_another_value_is_dropped(self):
        db = self.database()
        south = southward()
        with db:
            apply_reading_revisions(db, [south], EDITIONS)
        row = exported(db, "december")
        self.assertEqual(
            (row["quantity"], row["direction"], row["value_exact"], row["signed_value_exact"]),
            ("declination", "south", "9930", "-9930"),
        )
        review = json.loads(row["scientific_metadata_json"])["interpretation_review"]
        self.assertEqual((review["previous_direction"], review["direction_label"]), (None, "8 51"))
        back = dict(
            south,
            version=1,
            previous=south["revised"],
            revised=south["previous"],
            direction=dict(previous="south", revised=None, label="8 51"),
        )
        with db:
            apply_reading_revisions(db, [back], EDITIONS)
        row = exported(db, "december")
        self.assertEqual(
            (row["quantity"], row["direction"], row["value_exact"], row["signed_value_exact"]),
            ("altitude", None, "9930", None),
        )

    def test_a_direction_the_page_does_not_print_is_rejected(self):
        cases = (
            (dict(previous="north", revised="south", label="8 51"), "Direction revision"),
            (dict(previous=None, revised=None, label="8 51"), "Direction revision"),
            (dict(previous=None, revised="east", label="8 51"), "Direction revision"),
            (
                dict(previous=None, revised="south", label="south"),
                "do not print the reviewed label",
            ),
        )
        for direction, message in cases:
            db = self.database()
            with self.subTest(direction=direction), self.assertRaisesRegex(ValueError, message):
                apply_reading_revisions(db, [southward(direction=direction)], EDITIONS)


NAMELESS = dict(model_name=None, source_model_label=None, source_model_attribution=None)
PLACE = dict(quantity="altitude", subject="Venus", reference=None)


def attributing(**changes):
    decision = dict(
        quantity_id=reading("december"),
        source_id=SOURCE,
        printed_page=12,
        source_expression="2° 45½′",
        version=0,
        edition_sha256=EDITIONS[SOURCE]["sha256"],
        previous=dict(PLACE, role="recorded_reading"),
        revised=dict(PLACE, role="historical_prediction"),
        model=dict(previous=NAMELESS, revised=dict(NAMELESS, model_name="Maestlin")),
        basis=dict(
            kind="printed_table_column",
            label="Mästlin's",
            lines=[15],
            statement="The row gives the place from the ephemerides of Mästlin.",
        ),
    )
    decision.update(changes)
    return decision


def typing_only(**changes):
    decision = attributing(**changes)
    del decision["model"]
    return decision


def published_model(db, name):
    row = exported(db, name)
    return row, json.loads(row["scientific_metadata_json"])


class ModelAttributionTests(DatabaseCase):
    def test_a_place_takes_the_model_that_its_label_names(self):
        db = self.database()
        before = db.execute("SELECT * FROM quantities ORDER BY id").fetchall()
        with db:
            apply_reading_revisions(db, [attributing()], EDITIONS)
        self.assertEqual(db.execute("SELECT * FROM quantities ORDER BY id").fetchall(), before)
        row, metadata = published_model(db, "december")
        self.assertEqual(
            (row["role"], row["interpretation_version"], metadata["model_name"]),
            ("historical_prediction", 1, "Maestlin"),
        )
        review = metadata["interpretation_review"]
        self.assertEqual(review["model_name"], "Maestlin")
        self.assertEqual(
            review["previous_model"],
            {"model_name": None, "source_model_label": None, "source_model_attribution": None},
        )
        self.assertEqual(review["basis"]["source_label"], "Mästlin's")

    def test_a_model_is_named_where_nothing_else_changes(self):
        db = self.database()
        prediction = dict(PLACE, role="historical_prediction")
        with db:
            apply_reading_revisions(db, [typing_only()], EDITIONS)
            apply_reading_revisions(
                db, [attributing(version=1, previous=prediction, revised=prediction)], EDITIONS
            )
        row, metadata = published_model(db, "december")
        self.assertEqual(
            (row["role"], row["interpretation_version"], metadata["model_name"]),
            ("historical_prediction", 2, "Maestlin"),
        )
        with self.assertRaisesRegex(ValueError, "frozen reading"):
            apply_reading_revisions(
                db, [typing_only(version=2, previous=prediction, revised=prediction)], EDITIONS
            )

    def test_a_source_that_the_page_leaves_unnamed_keeps_its_wording(self):
        db = self.database()
        unnamed = dict(
            model_name=None,
            source_model_label="our Tables",
            source_model_attribution="unnamed_as_stated",
        )
        decision = attributing(
            model=dict(previous=NAMELESS, revised=unnamed),
            basis=dict(attributing()["basis"], label="From our Tables", lines=[16]),
        )
        with db:
            apply_reading_revisions(db, [decision], EDITIONS)
        _, metadata = published_model(db, "december")
        self.assertEqual(
            (
                metadata["model_name"],
                metadata["source_model_label"],
                metadata["source_model_attribution"],
            ),
            (None, "our Tables", "unnamed_as_stated"),
        )

    def test_attributions_that_the_page_does_not_support_are_rejected(self):
        maestlin = dict(NAMELESS, model_name="Maestlin")
        ours = dict(NAMELESS, source_model_label="our Tables")
        cases = (
            (
                dict(model=dict(previous=dict(NAMELESS, model_name="Prutenic"), revised=maestlin)),
                "Model",
            ),
            (dict(model=dict(previous=NAMELESS, revised=NAMELESS)), "Model"),
            (dict(model=dict(previous=NAMELESS, revised=dict(model_name="Maestlin"))), "Model"),
            (dict(model=dict(previous=NAMELESS, revised=dict(NAMELESS, model_name=" "))), "Model"),
            (
                dict(
                    model=dict(
                        previous=NAMELESS,
                        revised=dict(maestlin, source_model_attribution="unnamed_as_stated"),
                    )
                ),
                "Model",
            ),
            (
                dict(
                    model=dict(
                        previous=NAMELESS,
                        revised=dict(NAMELESS, source_model_attribution="unnamed_as_stated"),
                    )
                ),
                "Model",
            ),
            (dict(model=dict(previous=NAMELESS, revised=ours)), "Model"),
            (
                dict(
                    model=dict(
                        previous=NAMELESS, revised=dict(ours, source_model_attribution="guessed")
                    )
                ),
                "Model",
            ),
            (dict(revised=dict(PLACE, role="repeated_reading")), "Model"),
            (
                dict(
                    model=dict(
                        previous=NAMELESS,
                        revised=dict(ours, source_model_attribution="unnamed_as_stated"),
                    )
                ),
                "do not print the reviewed label",
            ),
        )
        for changes, message in cases:
            db = self.database()
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, message):
                apply_reading_revisions(db, [attributing(**changes)], EDITIONS)

    def test_a_later_date_revision_keeps_the_named_model(self):
        db = self.database()
        named = attributing(quantity_id=reading("march"), source_expression="51° 59′ 35″")
        with db:
            apply_reading_revisions(db, [named], EDITIONS)
            apply_date_revisions(db, [redating()], EDITIONS)
        row, metadata = published_model(db, "march")
        self.assertEqual((row["interpretation_version"], metadata["model_name"]), (2, "Maestlin"))
        self.assertEqual(json.loads(row["date_claims_json"])[0]["day"], 4)

    def test_a_recorded_model_stays_until_a_review_replaces_it(self):
        db = self.database()
        identifier = reading("december")
        recorded = db.execute("SELECT original_json FROM quantities WHERE id=?", (identifier,))
        original = dict(json.loads(recorded.fetchone()[0]), model_name="Alphonsine")
        prediction = dict(PLACE, role="historical_prediction")
        with db:
            db.execute(
                "UPDATE quantities SET original_json=?, scientific_metadata_json=? WHERE id=?",
                (encoded(original), '{"model_name":"Alphonsine"}', identifier),
            )
            apply_reading_revisions(db, [typing_only()], EDITIONS)
        _, metadata = published_model(db, "december")
        self.assertEqual(metadata["model_name"], "Alphonsine")
        self.assertNotIn("model_name", metadata["interpretation_review"])
        replaced = attributing(
            version=1,
            previous=prediction,
            revised=prediction,
            model=dict(
                previous=dict(NAMELESS, model_name="Alphonsine"),
                revised=dict(NAMELESS, model_name="Maestlin"),
            ),
        )
        with db:
            apply_reading_revisions(db, [replaced], EDITIONS)
        _, metadata = published_model(db, "december")
        self.assertEqual(metadata["model_name"], "Maestlin")
        self.assertEqual(
            metadata["interpretation_review"]["previous_model"]["model_name"], "Alphonsine"
        )

    def test_the_catalogue_states_the_model_of_the_current_interpretation(self):
        db = self.database()
        identifier = reading("december")

        def shown():
            stated = db.execute("SELECT model_name FROM catalogue WHERE id=?", (identifier,))
            return stated.fetchone()[0]

        self.assertIsNone(shown())
        recorded = db.execute("SELECT original_json FROM quantities WHERE id=?", (identifier,))
        original = dict(json.loads(recorded.fetchone()[0]), model_name="Alphonsine")
        with db:
            db.execute(
                "UPDATE quantities SET original_json=? WHERE id=?", (encoded(original), identifier)
            )
            apply_reading_revisions(db, [typing_only()], EDITIONS)
        self.assertEqual(shown(), "Alphonsine")
        prediction = dict(PLACE, role="historical_prediction")
        named = dict(previous=prediction, revised=prediction)
        renamed = dict(
            previous=dict(NAMELESS, model_name="Alphonsine"),
            revised=dict(NAMELESS, model_name="Maestlin"),
        )
        with db:
            apply_reading_revisions(db, [attributing(version=1, model=renamed, **named)], EDITIONS)
        self.assertEqual(shown(), "Maestlin")
        # A review that leaves the source unnamed withdraws the name; the recorded one stays out.
        unnamed = dict(
            previous=renamed["revised"],
            revised=dict(
                model_name=None,
                source_model_label="our Tables",
                source_model_attribution="unnamed_as_stated",
            ),
        )
        basis = dict(attributing()["basis"], label="From our Tables", lines=[16])
        with db:
            apply_reading_revisions(
                db, [attributing(version=2, model=unnamed, basis=basis, **named)], EDITIONS
            )
        self.assertIsNone(shown())


CALCULATION = dict(
    quantity="calculation_angle",
    subject="Saturn calculation",
    reference=None,
    role="historical_input",
)


ELAPSED = dict(CALCULATION, quantity="clock_elapsed_time")
COUNT = dict(CALCULATION, quantity="source_scalar")


def from_text(
    db, name, expression, value, components, event=None, typing=None, unit="arcsecond", page=12
):
    """Add a reading from running text. It is a calculation angle unless typed otherwise."""
    identifier = reading(name)
    typing = typing or CALCULATION
    normalized = dict(status="exact", unit=unit, magnitude=value, signed_magnitude=None)
    original = dict(
        typing,
        id=identifier,
        volume=12,
        printed_page=page,
        direction=None,
        flags=["not_an_additional_raw_reading"],
        normalized=normalized,
        source_date_claim_ids=[],
    )
    db.execute(
        "INSERT INTO quantities VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            identifier,
            12,
            page,
            expression,
            typing["role"],
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
            typing["quantity"],
            typing["subject"],
            None,
            "exact",
            unit,
            value,
            None,
            encoded(normalized),
            encoded(components),
            '["not_an_additional_raw_reading"]',
            None,
        ),
    )


def completing(name="composed", **changes):
    decision = dict(
        quantity_id=reading(name),
        source_id=SOURCE,
        printed_page=12,
        source_expression="9° 9′ 25″",
        version=0,
        edition_sha256=EDITIONS[SOURCE]["sha256"],
        expression="5s 9° 9′ 25″",
        components=dict(sign_count="5", degree="9", arcminute="9", arcsecond="25"),
        previous=dict(CALCULATION),
        revised=dict(CALCULATION),
        basis=dict(
            kind="printed_expression",
            label="composed as 5s 9° 9′ 25″",
            lines=[7],
            statement="The line prints a count of signs before the degrees.",
        ),
    )
    decision.update(changes)
    return decision


def merging(**changes):
    decision = completing(
        "minutes",
        source_expression="15′",
        expression="3° 15′",
        components=dict(degree="3", arcminute="15"),
        absorbed=[reading("degrees")],
        basis=dict(
            kind="printed_expression",
            label="which is 3° 15′ of the circle",
            lines=[8],
            statement="The line prints the degrees and the minutes as one distance.",
        ),
    )
    decision.update(changes)
    return decision


YEAR = dict(day="365", hour="5", minute="24", second="38")
CLOCK = dict(hour="7", minute="29")
MONTH_FIRST = "29 days, 12^h^ 44^m^ 3^s^ 10‴ 58⁗"
MONTH = dict(
    day="29", hour="12", minute="44", second="3", time_third="10", time_fourth="58", time_fifth="10"
)


def in_parts(name, first, parts, components, lines, **changes):
    decision = completing(
        name,
        source_expression=first,
        expression=" … ".join(parts),
        parts=parts,
        components=components,
        previous=dict(ELAPSED),
        revised=dict(ELAPSED),
        basis=dict(
            kind="printed_expression",
            label=parts[0],
            lines=lines,
            statement="The page prints this value in parts with other text between them.",
        ),
    )
    decision.update(changes)
    return decision


class EditionReadingTests(DatabaseCase):
    def database(self):
        db = super().database()
        with db:
            from_text(
                db,
                "composed",
                "9° 9′ 25″",
                "32965",
                dict(degree="9", arcminute="9", arcsecond="25"),
            )
            from_text(db, "sum", "6° 24¼′", "23055", dict(degree="6", arcminute="24 1/4"))
            from_text(db, "minutes", "15′", "900", dict(arcminute="15"))
            from_text(db, "degrees", "3°", "10800", dict(degree="3"))
        return db

    def current(self, db, name):
        return db.execute(
            "SELECT expression,version,value_exact,status,unit FROM catalogue WHERE id=?",
            (reading(name),),
        ).fetchone()

    def test_a_part_of_a_printed_expression_is_completed_from_its_line(self):
        db = self.database()
        with db:
            revised, absorbed = apply_edition_readings(db, [completing()], EDITIONS)
        self.assertEqual((revised, absorbed), ([reading("composed")], []))
        self.assertEqual(
            self.current(db, "composed"), ("5s 9° 9′ 25″", 1, "572965", "exact", "arcsecond")
        )
        intake = db.execute(
            "SELECT q.expression,i.value_exact FROM quantities q JOIN interpretations i "
            "ON i.quantity_id=q.id AND i.version=0 WHERE q.id=?",
            (reading("composed"),),
        ).fetchone()
        self.assertEqual(intake, ("9° 9′ 25″", "32965"))
        review = json.loads(exported(db, "composed")["scientific_metadata_json"])[
            "interpretation_review"
        ]
        self.assertEqual(review["kind"], EDITION_READING)
        self.assertEqual(review["previous_source_expression"], "9° 9′ 25″")
        self.assertEqual(review["previous_value_exact"], "32965")
        self.assertEqual(review["basis"]["source_label"], "composed as 5s 9° 9′ 25″")

    def test_a_reading_the_edition_corrected_takes_the_printed_numerals(self):
        db = self.database()
        decision = completing(
            "sum",
            source_expression="6° 24¼′",
            expression="6° 24⅓′",
            components=dict(degree="6", arcminute="24 1/3"),
            basis=dict(
                kind="printed_expression",
                label="aggregated as 6° 24⅓′",
                lines=[7],
                statement="The edition now reads a third where it read a quarter.",
            ),
        )
        with db:
            apply_edition_readings(db, [decision], EDITIONS)
        self.assertEqual(self.current(db, "sum"), ("6° 24⅓′", 1, "23060", "exact", "arcsecond"))

    def test_a_record_that_holds_the_rest_of_the_expression_is_merged(self):
        db = self.database()
        with db:
            absorbed = apply_edition_readings(db, [merging()], EDITIONS)[1]
        self.assertEqual(absorbed, [reading("degrees")])
        self.assertEqual(self.current(db, "minutes"), ("3° 15′", 1, "11700", "exact", "arcsecond"))
        for table, column in (("quantities", "id"), ("interpretations", "quantity_id")):
            left = db.execute(
                f"SELECT count(*) FROM {table} WHERE {column}=?", (reading("degrees"),)
            ).fetchone()[0]
            self.assertEqual(left, 0)
        review = json.loads(exported(db, "minutes")["scientific_metadata_json"])[
            "interpretation_review"
        ]
        self.assertEqual(
            [(record["id"], record["source_expression"]) for record in review["absorbed_readings"]],
            [(reading("degrees"), "3°")],
        )
        self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_readings_that_the_line_does_not_print_are_rejected(self):
        thirds = dict(degree="6", arcminute="24 1/3")
        cases = (
            (completing(expression="6s 9° 9′ 25″"), "do not print the reviewed label"),
            (
                completing(components=dict(sign_count="5", degree="9", arcminute="9")),
                "Components differ",
            ),
            (
                completing(components=dict(degree="5", arcminute="9", arcsecond="9", second="25")),
                "component unit mismatch",
            ),
            (
                completing(
                    components=dict(sign_count="9", degree="5", arcminute="9", arcsecond="25")
                ),
                "Components differ",
            ),
            (completing(expression="6° 24⅓′", components=thirds), "still print the earlier"),
            (completing(version=1), "frozen reading"),
            (completing(expression="9° 9′ 25″"), "frozen reading"),
            (completing(absorbed=[reading("degrees")]), "Only the rest"),
            (merging(absorbed=[reading("sum")]), "Only the rest"),
        )
        for decision, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                apply_edition_readings(self.database(), [decision], EDITIONS)

    def test_a_reading_left_incomplete_takes_the_part_that_the_edition_now_prints(self):
        db = self.database()
        with db:
            from_text(db, "open", "6°", None, dict(degree="6"))
            db.execute(
                "UPDATE interpretations SET status='incomplete' WHERE quantity_id=?",
                (reading("open"),),
            )
            decision = completing(
                "open",
                source_expression="6°",
                expression="6° 24⅓′",
                components=dict(degree="6", arcminute="24 1/3"),
                basis=dict(
                    kind="printed_expression",
                    label="aggregated as 6° 24⅓′",
                    lines=[7],
                    statement="The edition now prints the minutes.",
                ),
            )
            apply_edition_readings(db, [decision], EDITIONS)
        self.assertEqual(self.current(db, "open"), ("6° 24⅓′", 1, "23060", "exact", "arcsecond"))

    def test_a_second_record_of_the_same_expression_joins_its_reading(self):
        whole = dict(
            source_expression="3° 15′",
            expression="3° 15′",
            components=dict(degree="3", arcminute="15"),
            basis=merging()["basis"],
        )
        db = self.database()
        with db:
            from_text(db, "whole", "3° 15′", "11700", dict(degree="3", arcminute="15"))
            from_text(db, "twin", "3° 15′", "11700", dict(degree="3", arcminute="15"))
            decision = completing("whole", absorbed=[reading("twin")], **whole)
            revised, absorbed = apply_edition_readings(db, [decision], EDITIONS)
        self.assertEqual((revised, absorbed), ([reading("whole")], [reading("twin")]))
        self.assertEqual(self.current(db, "whole"), ("3° 15′", 1, "11700", "exact", "arcsecond"))
        self.assertIsNone(self.current(db, "twin"))
        review = json.loads(
            db.execute(
                "SELECT revision_json FROM interpretations WHERE quantity_id=? AND version=1",
                (reading("whole"),),
            ).fetchone()[0]
        )
        self.assertEqual(
            [(record["id"], record["source_expression"]) for record in review["absorbed_readings"]],
            [(reading("twin"), "3° 15′")],
        )

    def test_a_fragment_joins_a_reading_that_already_holds_the_whole_expression(self):
        whole = dict(
            source_expression="3° 15′",
            expression="3° 15′",
            components=dict(degree="3", arcminute="15"),
            basis=merging()["basis"],
        )
        db = self.database()
        with db:
            from_text(db, "whole", "3° 15′", "11700", dict(degree="3", arcminute="15"))
            decision = completing("whole", absorbed=[reading("minutes")], **whole)
            revised, absorbed = apply_edition_readings(db, [decision], EDITIONS)
        self.assertEqual((revised, absorbed), ([reading("whole")], [reading("minutes")]))
        self.assertEqual(self.current(db, "whole"), ("3° 15′", 1, "11700", "exact", "arcsecond"))
        self.assertIsNone(self.current(db, "minutes"))
        cases = (
            (completing("whole", **whole), "frozen reading"),
            (
                completing(
                    "whole",
                    absorbed=[reading("minutes")],
                    **dict(whole, components=dict(arcminute="3", arcsecond="15")),
                ),
                "keeps its components",
            ),
        )
        for decision, message in cases:
            db = self.database()
            from_text(db, "whole", "3° 15′", "11700", dict(degree="3", arcminute="15"))
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                apply_edition_readings(db, [decision], EDITIONS)

    def test_the_end_of_a_value_printed_across_a_page_break_joins_its_reading(self):
        spelled = dict(
            source_expression="3 degrees 15 minutes",
            expression="3° 15′",
            components=dict(degree="3", arcminute="15"),
            basis=merging()["basis"],
        )
        decision = completing("spelled", absorbed=[reading("end")], **spelled)

        def database(page, parts):
            db = self.database()
            whole = dict(degree="3", arcminute="15")
            from_text(db, "spelled", "3 degrees 15 minutes", "11700", whole)
            from_text(db, "end", "15 minutes", "900", parts, page=page)
            return db

        db = database(13, dict(arcminute="15"))
        with db:
            absorbed = apply_edition_readings(db, [decision], EDITIONS)[1]
        self.assertEqual(absorbed, [reading("end")])
        self.assertEqual(self.current(db, "spelled"), ("3° 15′", 1, "11700", "exact", "arcsecond"))
        self.assertIsNone(self.current(db, "end"))
        refused = (
            (14, dict(arcminute="15")),
            (13, dict(arcsecond="15")),
            (12, dict(arcminute="15")),
        )
        for page, parts in refused:
            with (
                self.subTest(page=page, parts=parts),
                self.assertRaisesRegex(ValueError, "Only the rest"),
            ):
                apply_edition_readings(database(page, parts), [decision], EDITIONS)

    def test_a_value_set_in_neighboring_cells_takes_all_of_them(self):
        thirds = dict(hour="1", minute="27", second="33", time_third="20")
        share = dict(proportional_minute="41", proportional_second="24")
        portion = dict(CALCULATION, quantity="proportional_minutes")
        cases = (
            ("hours", "1", "1 | 27 | 33 | 20", thirds, ELAPSED, "15760/3", "second_of_time"),
            ("share", "41", "41 | 24", share, portion, "69/100", "ratio"),
        )
        for name, first, cells, parts, typing, value, unit in cases:
            db = self.database()
            decision = completing(
                name,
                source_expression=first,
                expression=cells,
                components=parts,
                previous=dict(typing),
                revised=dict(typing),
                basis=dict(
                    kind="printed_expression",
                    label=cells,
                    lines=[10],
                    statement="The row prints the parts of this value in neighboring cells.",
                ),
            )
            with self.subTest(name=name), db:
                from_text(db, name, first, value, parts, typing=typing, unit=unit)
                apply_edition_readings(db, [decision], EDITIONS)
                self.assertEqual(self.current(db, name), (cells, 1, value, "exact", unit))

    def test_a_value_printed_in_parts_shows_each_part_in_printed_order(self):
        cases = (
            ("year", "365 days", ["365 days, 5^h^", "24^m^ 38^s^"], YEAR, "31555478", [11]),
            ("watch", "7^h^", ["7^h^", "29^m^"], CLOCK, "26940", [12, 13]),
            ("month", MONTH_FIRST, [MONTH_FIRST, "10^v^"], MONTH, "55111172749/21600", [14]),
        )
        for name, first, parts, components, value, lines in cases:
            db = self.database()
            decision = in_parts(name, first, parts, components, lines)
            with self.subTest(name=name), db:
                from_text(db, name, first, value, components, typing=ELAPSED, unit="second_of_time")
                apply_edition_readings(db, [decision], EDITIONS)
                self.assertEqual(
                    self.current(db, name),
                    (" … ".join(parts), 1, value, "exact", "second_of_time"),
                )

    def test_parts_that_the_lines_do_not_print_in_this_order_are_rejected(self):
        whole = dict(hour="7", minute="12")
        cases = (
            (
                "lines cited out of order",
                in_parts("watch", "7^h^", ["7^h^", "29^m^"], CLOCK, [13, 12]),
            ),
            ("an unprinted part", in_parts("watch", "7^h^", ["7^h^", "30^m^"], CLOCK, [12, 13])),
            ("one part", in_parts("watch", "7^h^", ["7^h^ | 12^m^"], whole, [12])),
            (
                "an expression that is not the parts",
                in_parts(
                    "watch", "7^h^", ["7^h^", "29^m^"], CLOCK, [12, 13], expression="7^h^ 29^m^"
                ),
            ),
        )
        for name, decision in cases:
            db = self.database()
            with self.subTest(name=name), db:
                from_text(
                    db, "watch", "7^h^", "26940", CLOCK, typing=ELAPSED, unit="second_of_time"
                )
                with self.assertRaises(ValueError):
                    apply_edition_readings(db, [decision], EDITIONS)

    def test_a_whole_expression_with_a_number_of_no_stated_unit_keeps_no_value(self):
        interval = dict(
            source_expression="2 days 2 hours",
            expression="2 days 2 hours 11⅗",
            components={},
            previous=dict(ELAPSED),
            revised=dict(ELAPSED),
            basis=dict(
                kind="printed_expression",
                label="2 days 2 hours 11⅗",
                lines=[9],
                statement="The line prints a third number without a unit.",
            ),
        )

        def database():
            db = self.database()
            from_text(
                db, "interval", "2 days 2 hours", "180000", dict(day="2", hour="2"), None, ELAPSED,
                "second_of_time",
            )  # fmt: skip
            from_text(
                db, "loose", "11⅗", "58/5", dict(scalar="11 3/5"), None, COUNT, "source_scalar"
            )
            return db

        db = database()
        with db:
            decision = completing("interval", absorbed=[reading("loose")], **interval)
            apply_edition_readings(db, [decision], EDITIONS)
        self.assertEqual(
            self.current(db, "interval"), ("2 days 2 hours 11⅗", 1, None, "unsupported", None)
        )
        review = json.loads(exported(db, "interval")["scientific_metadata_json"])[
            "interpretation_review"
        ]
        self.assertEqual(review["previous_value_exact"], "180000")
        # A corrected reading is not a longer one, so it may not lose its value this way.
        corrected = completing(
            "sum", source_expression="6° 24¼′", expression="6° 24⅓′", components={}
        )
        retyped = completing("interval", **dict(interval, revised=dict(CALCULATION)))
        for decision in (corrected, retyped):
            with self.assertRaisesRegex(ValueError, "does not convert"):
                apply_edition_readings(database(), [decision], EDITIONS)

    def test_a_long_number_that_the_edition_groups_is_the_same_number(self):
        db = self.database()
        with db:
            from_text(
                db, "hours", "16h 54′ 13″", "60853", dict(hour="16", minute="54", second="13"),
                None, ELAPSED, "second_of_time",
            )  # fmt: skip
            from_text(
                db, "count", "733805", "733805", dict(scalar="733805"), None, COUNT, "source_scalar"
            )
            decision = completing(
                "hours",
                source_expression="16h 54′ 13″",
                expression="733,805 days 16h 54′ 13″",
                components=dict(day="733805", hour="16", minute="54", second="13"),
                previous=dict(ELAPSED),
                revised=dict(ELAPSED),
                absorbed=[reading("count")],
                basis=dict(
                    kind="printed_expression",
                    label="733,805 days 16h 54′ 13″",
                    lines=[9],
                    statement="The line prints the days before the hours.",
                ),
            )
            apply_edition_readings(db, [decision], EDITIONS)
        self.assertEqual(
            self.current(db, "hours"),
            ("733,805 days 16h 54′ 13″", 1, "63400812853", "exact", "second_of_time"),
        )

    def test_a_reading_is_completed_once_and_a_merged_record_is_gone(self):
        with self.assertRaisesRegex(ValueError, "frozen reading"):
            apply_edition_readings(self.database(), [completing(), completing()], EDITIONS)
        again = completing(
            "degrees",
            source_expression="3°",
            expression="3° 15′",
            components=dict(degree="3", arcminute="15"),
            basis=merging()["basis"],
        )
        with self.assertRaisesRegex(ValueError, "Missing reviewed historical reading"):
            apply_edition_readings(self.database(), [merging(), again], EDITIONS)


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

    def test_a_book_claim_is_revised_without_the_notes_on_its_own_date(self):
        book = dict(
            stated(OLD, 12, 20),
            source_id=SOURCE,
            source_clock_qualification="After noon of the preceding day",
            source_date_role="calculation_target",
        )
        del book["volume"]
        db = self.database()
        db.execute("UPDATE dates SET data_json=? WHERE id=?", (encoded(book), OLD))
        with db:
            apply_date_revisions(db, [redating()], EDITIONS)
        (new,) = db.execute("SELECT date_id FROM group_dates WHERE group_id='event-a'").fetchone()
        claim = json.loads(
            db.execute("SELECT data_json FROM dates WHERE id=?", (new,)).fetchone()[0]
        )
        self.assertEqual(set(claim), set(book) - {"source_clock_qualification", "source_date_role"})
        self.assertEqual((claim["source_id"], claim["month"], claim["day"]), (SOURCE, 3, 4))
        # A date tied to a model is not a plain claim. It is refused.
        db = self.database()
        modeled = encoded(dict(book, model_name="Prutenic"))
        db.execute("UPDATE dates SET data_json=? WHERE id=?", (modeled, OLD))
        with self.assertRaisesRegex(ValueError, "plain reviewed claim"), db:
            apply_date_revisions(db, [redating()], EDITIONS)

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

    def test_a_line_that_names_the_last_day_of_its_month_keeps_that_rule(self):
        last = dict(year=1590, month=3, day_rule="last_day_of_month", daypart_original="VESPERI")
        db = self.database()
        with db:
            apply_date_revisions(db, [redating(date=last)], EDITIONS)
        (new,) = db.execute("SELECT date_id FROM group_dates WHERE group_id='event-a'").fetchone()
        claim = json.loads(
            db.execute("SELECT data_json FROM dates WHERE id=?", (new,)).fetchone()[0]
        )
        self.assertEqual(
            (claim["year"], claim["month"], claim["day"], claim["day_rule"], claim["daypart"]),
            (1590, 3, None, "last_day_of_month", "evening"),
        )
        self.assertEqual(claim["component_status"], "partial_named_components")
        (value,) = db.execute(
            "SELECT value_json FROM contexts WHERE context_id=?", (new,)
        ).fetchone()
        self.assertEqual(
            json.loads(value),
            dict(
                year=1590,
                month=3,
                day=None,
                day_rule="last_day_of_month",
                daypart_original="VESPERI",
            ),
        )
        printed = json.loads(exported(db, "march")["date_claims_json"])[0]
        self.assertEqual((printed["day"], printed["day_rule"]), (None, "last_day_of_month"))
        for date in (
            dict(last, day_rule="following_named_day"),
            dict(last, day=31),
            dict(year=1590, month=3, daypart_original=None),
        ):
            db = self.database()
            with (
                self.subTest(date=date),
                self.assertRaisesRegex(ValueError, "complete printed components"),
            ):
                apply_date_revisions(db, [redating(date=date)], EDITIONS)

    def test_a_heading_for_the_night_beside_a_named_day_keeps_that_relation(self):
        night = dict(
            year=1590, month=3, day=4, daypart_original="NOCTE", day_relation="preceding_night"
        )
        db = self.database()
        with db:
            apply_date_revisions(db, [redating(date=night)], EDITIONS)
        (new,) = db.execute("SELECT date_id FROM group_dates WHERE group_id='event-a'").fetchone()
        claim = json.loads(
            db.execute("SELECT data_json FROM dates WHERE id=?", (new,)).fetchone()[0]
        )
        self.assertEqual(
            (
                claim["day"],
                claim["daypart"],
                claim["source_date_role"],
                claim["source_day_relation"],
                claim["component_status"],
            ),
            (4, "night", "observation_label", "preceding_night", "complete_named_components"),
        )
        (value,) = db.execute(
            "SELECT value_json FROM contexts WHERE context_id=?", (new,)
        ).fetchone()
        self.assertEqual(
            json.loads(value), dict(year=1590, month=3, day=4, daypart_original="NOCTE")
        )
        printed = json.loads(exported(db, "march")["date_claims_json"])[0]
        self.assertEqual(printed["source_day_relation"], "preceding_night")
        for date in (
            dict(night, day_relation="same_night"),
            dict(night, daypart_original="VESPERI"),
            dict(night, daypart_original=None),
            dict(
                year=1590,
                month=3,
                day_rule="last_day_of_month",
                **{"daypart_original": "NOCTE", "day_relation": "preceding_night"},
            ),
        ):
            db = self.database()
            with (
                self.subTest(date=date),
                self.assertRaisesRegex(ValueError, "complete printed components"),
            ):
                apply_date_revisions(db, [redating(date=date)], EDITIONS)

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
