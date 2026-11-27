"""Append source-reviewed revisions to readings that already carry an interpretation.

A reading revision assigns the quantity type, subject, reference or role that the printed page
establishes. It may also set the north or south that the page prints beside the value, or drop
one that the page prints for another value of the label. A date revision moves readings from an
inherited date claim to the date their own heading or table states. Neither changes a printed
expression, a component or a magnitude, and every earlier interpretation stays in the version
history.

An edition reading is the one revision that changes a value. It gives a reading the whole
expression that its line of the bound edition prints, where the catalogue holds only a part of
that expression or a reading that the edition has since corrected. The numerals come from the
cited line and from nowhere else, and the value is converted again from them. A record that
holds nothing but the rest of the same printed expression is merged into the reading.

Each decision names lines of the bound edition. The edition text is read at apply time and only
the reviewed label and statement are stored with the catalogue.
"""

import collections
from collections.abc import Iterable, Mapping
from fractions import Fraction
import hashlib
import json
import re

from .catalog_release import WORKING_CATALOGUE_VIEW, encoded
from .core import fraction_text, number
from .csv_projection import MODEL_FIELDS
from .date_claims import DAYPARTS
from .normalization import ANGLE_QUANTITIES, ANGULAR_RATES, normalize_quantity
from .numeric_integrity import NUMBER
from .vocabulary import load_vocabulary

READING_REVISION = "reviewed_reading_revision"
DATE_REVISION = "reviewed_date_binding"
EDITION_READING = "reviewed_edition_reading"
REVIEWED_KINDS = (READING_REVISION, DATE_REVISION, EDITION_READING)
BASIS_KINDS = (
    "printed_expression",
    "printed_heading",
    "printed_label",
    "printed_reckoning",
    "printed_table_column",
)
# The places of a printed expression, from the greatest to the least, for each kind of unit.
COMPONENT_ORDER = (
    "sign_count",
    "degree",
    "arcminute",
    "arcsecond",
    "arcsexagesimal_third",
    "arcsexagesimal_fourth",
    "day",
    "hour",
    "minute",
    "second",
    "time_third",
    "time_fourth",
    "time_fifth",
    "source_part",
    "part_minute",
    "part_second",
    "proportional_minute",
    "proportional_second",
    "mile",
    "mile_minute",
    "scalar",
)
GROUPED_DIGITS = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")
PARTS_BETWEEN = " … "  # stands for the printed text between two parts of one value
# A record that anything else points to is never merged into another reading.
REFERENCES = (
    ("groups", "clock_quantity_id"),
    ("groups", "epoch_quantity_id"),
    ("series_quantities", "quantity_id"),
    ("derivations", "output_quantity_id"),
    ("derivation_inputs", "quantity_id"),
    ("control_links", "quantity_id"),
    ("quantity_links", "from_id"),
    ("quantity_links", "to_id"),
)
OWNED = (
    ("interpretations", "quantity_id"),
    ("quantity_contexts", "id"),
    ("quantity_dates", "quantity_id"),
    ("locus_quantities", "quantity_id"),
    ("quantities", "id"),
)
CARRIED_FIELDS = ("completed_source_expression", "date_claim_ids")
READING_FIELDS = ("quantity", "subject", "reference", "role")
# A value is attributed to a model where the page gives it as that model's place or as the
# difference of that place from the observed one.
MODEL_ROLES = ("historical_prediction", "historical_comparison")
UNNAMED_SOURCES = ("unnamed_as_stated", "unestablished_from_canon")
PLAIN_ANGLES = ANGLE_QUANTITIES - set(ANGULAR_RATES)
CLAIM_FIELDS = {
    "id",
    "volume",
    "year",
    "month",
    "day",
    "daypart",
    "calendar",
    "day_origin",
    "component_status",
    "claim_basis",
    "calendar_validation",
    "accepted_observing_date",
    "absolute_timestamp",
}
BOOK_CLAIM_FIELDS = (CLAIM_FIELDS - {"volume"}) | {"source_id"}
# What a supplementary book's claim may record about its own date expression.
BOOK_CLAIM_NOTES = {
    "source_clock_qualification",
    "source_context_record_type",
    "source_date_expression",
    "source_date_role",
    "source_date_witness",
    "source_day_relation",
}
SPACE = re.compile(r"\s+")  # Unicode white space, including the no-break forms in table cells.
INSERT = "INSERT INTO interpretations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"


def flat(text):
    """Compare printed text without regard to the kind or amount of white space."""
    return SPACE.sub(" ", text).strip()


def read_edition(path):
    """Read one edition with the fingerprint of the exact bytes."""
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "lines": data.decode("utf-8").split("\n")}


def current_reading(db, identifier):
    row = db.execute(
        """
        SELECT c.source_id,c.volume,c.printed_page,c.expression,c.role,c.event_id,i.version,
               i.quantity,i.subject,i.reference_object,i.status,i.unit,i.value_exact,
               i.signed_value_exact,i.normalized_json,i.components_json,i.flags_json,
               i.revision_json,q.original_json
        FROM catalogue c JOIN quantities q ON q.id=c.id
        JOIN interpretations i ON i.quantity_id=c.id AND i.version=c.version
        WHERE c.id=? AND q.source_payload_json IS NULL
        """,
        (identifier,),
    ).fetchone()
    if row is None:
        raise ValueError("Missing reviewed historical reading: " + identifier)
    keys = (
        "source_id",
        "volume",
        "printed_page",
        "expression",
        "role",
        "event_id",
        "version",
        "quantity",
        "subject",
        "reference",
        "status",
        "unit",
        "value_exact",
        "signed_value_exact",
        "normalized_json",
        "components_json",
        "flags_json",
        "revision_json",
        "original_json",
    )
    return dict(zip(keys, row, strict=True))


def reviewed_basis(decision, editions: Mapping, expressions):
    """Return the public basis after finding the label and every reading on the cited lines."""
    basis = decision["basis"]
    edition = editions.get(decision["source_id"])
    if (
        set(basis) != {"kind", "label", "lines", "statement"}
        or basis["kind"] not in BASIS_KINDS
        or not flat(basis["label"])
        or not flat(basis["statement"])
        or not basis["lines"]
        or edition is None
        or edition["sha256"] != decision["edition_sha256"]
        or any(
            type(number) is not int or not 1 <= number <= len(edition["lines"])
            for number in basis["lines"]
        )
    ):
        raise ValueError("Revision lacks printed evidence in its bound edition")
    cited = [flat(edition["lines"][number - 1]) for number in basis["lines"]]
    if not any(flat(basis["label"]) in line for line in cited) or not all(
        any(flat(expression) in line for line in cited) for expression in expressions
    ):
        raise ValueError("Cited lines do not print the reviewed label and readings")
    return dict(
        kind=basis["kind"], source_label=flat(basis["label"]), statement=flat(basis["statement"])
    )


def carried(current):
    """Keep what an earlier review established and this one does not change."""
    previous = json.loads(current["revision_json"] or "{}")
    kept = {key: previous[key] for key in (*CARRIED_FIELDS, *MODEL_FIELDS) if key in previous}
    kept["direction"] = previous.get(
        "direction", json.loads(current["original_json"]).get("direction")
    )
    return kept


def attributed(naming, recorded, role):
    """Return the reviewed attribution, or None unless it names a model or states that none is."""
    if tuple(sorted(naming)) != ("previous", "revised") or any(
        tuple(sorted(part)) != tuple(sorted(MODEL_FIELDS)) for part in naming.values()
    ):
        return None
    revised = {
        key: flat(value) if isinstance(value, str) else value
        for key, value in naming["revised"].items()
    }
    name, label, unnamed = (revised[key] for key in MODEL_FIELDS)
    if (
        naming["previous"] != recorded
        or revised == recorded
        or role not in MODEL_ROLES
        or any(type(value) not in (str, type(None)) for value in revised.values())
        or (name is None) == (unnamed is None)
        or (label is None) != (unnamed is None)
        or not (name or label)
        or unnamed not in (None, *UNNAMED_SOURCES)
    ):
        return None
    return revised


def recreate_view(db):
    db.execute("DROP VIEW catalogue")
    db.execute(WORKING_CATALOGUE_VIEW)


def apply_reading_revisions(db, decisions: Iterable[dict], editions: Mapping):
    """Select the type, subject, reference or role that the printed page establishes."""
    vocabulary = load_vocabulary("historical")
    revised_ids = []
    for decision in decisions:
        identifier = decision["quantity_id"]
        current = current_reading(db, identifier)
        previous, revised = decision["previous"], decision["revised"]
        naming = decision.get("model")
        if (
            identifier in revised_ids
            or tuple(sorted(previous)) != tuple(sorted(READING_FIELDS))
            or tuple(sorted(revised)) != tuple(sorted(READING_FIELDS))
            or (previous == revised and naming is None)
            or current["source_id"] != decision["source_id"]
            or current["printed_page"] != decision["printed_page"]
            or flat(current["expression"]) != flat(decision["source_expression"])
            or current["version"] != decision["version"]
            or {key: current[key] for key in READING_FIELDS} != previous
            or revised["quantity"] not in vocabulary["quantity"]
            or revised["role"] not in vocabulary["role"]
            or not flat(revised["subject"] or "")
        ):
            raise ValueError("Reading revision differs from its frozen reading: " + identifier)
        original = json.loads(current["original_json"])
        kept = carried(current)
        turn = decision.get("direction")
        if turn is not None and (
            tuple(sorted(turn)) != ("label", "previous", "revised")
            or turn["previous"] != kept["direction"]
            or turn["revised"] == kept["direction"]
            or turn["revised"] not in (None, "north", "south")
            or not flat(turn["label"] or "")
        ):
            raise ValueError("Direction revision differs from its frozen reading: " + identifier)
        model = None
        if naming is not None:
            recorded = {key: kept.get(key, original.get(key)) for key in MODEL_FIELDS}
            model = attributed(naming, recorded, revised["role"])
            if model is None:
                raise ValueError("Model attribution differs from its frozen reading: " + identifier)
        signed, normalized = current["signed_value_exact"], current["normalized_json"]
        if revised["quantity"] != previous["quantity"] or turn is not None:
            if not {previous["quantity"], revised["quantity"]} <= PLAIN_ANGLES:
                raise ValueError(
                    "A reading revision cannot change the printed value: " + identifier
                )
            trial = normalize_quantity(
                dict(
                    original,
                    source_expression=current["expression"],
                    components=json.loads(current["components_json"]),
                    quantity=revised["quantity"],
                    subject=revised["subject"],
                    reference=revised["reference"],
                    role=revised["role"],
                    direction=turn["revised"] if turn else kept["direction"],
                )
            )
            if (
                current["status"] != "exact"
                or current["unit"] != "arcsecond"
                or trial.get("status") != "exact"
                or trial.get("unit") != "arcsecond"
                or trial.get("magnitude") != current["value_exact"]
                or (turn is None and trial.get("signed_magnitude") != signed)
            ):
                raise ValueError(
                    "A reading revision cannot change the printed value: " + identifier
                )
            if turn is not None:
                # The printed magnitude stays. Only the side of the circle it is counted on moves.
                signed = trial.get("signed_magnitude")
                normalized = encoded(dict(json.loads(normalized), signed_magnitude=signed))
        terms = [
            dict(quantity_id=term["quantity_id"], sign=term["sign"])
            for term in decision.get("reckoning", ())
        ]
        if terms:
            total = Fraction(0)
            for term in terms:
                other = current_reading(db, term["quantity_id"])
                if (
                    term["sign"] not in (1, -1)
                    or other["source_id"] != current["source_id"]
                    or other["status"] != "exact"
                    or other["unit"] != current["unit"]
                ):
                    raise ValueError("Printed reckoning needs exact readings of one source")
                total += term["sign"] * Fraction(other["value_exact"])
            if current["status"] != "exact" or total != Fraction(current["value_exact"]):
                raise ValueError("Printed reckoning does not close on the reading: " + identifier)
        flags = json.loads(current["flags_json"])
        withdrawn = list(decision.get("withdrawn_flags", ()))
        if any(flag not in flags for flag in withdrawn):
            raise ValueError("Withdrawn flag is not on the reading: " + identifier)
        printed = [current["expression"]] + ([turn["label"]] if turn else [])
        if model is not None and model["source_model_label"] is not None:
            # The wording kept for a source that the page leaves unnamed is the page's own.
            printed.append(model["source_model_label"])
        revision = dict(
            kept,
            kind=READING_REVISION,
            role=revised["role"],
            previous=previous,
            revised=revised,
            basis=reviewed_basis(decision, editions, printed),
        )
        if model is not None:
            revision.update(model, previous_model=naming["previous"])
        if turn is not None:
            revision.update(
                direction=turn["revised"],
                previous_direction=turn["previous"],
                direction_label=flat(turn["label"]),
            )
        if terms:
            revision["reckoning"] = terms
        if withdrawn:
            revision["withdrawn_flags"] = withdrawn
        db.execute(
            INSERT,
            (
                identifier,
                current["version"] + 1,
                revised["quantity"],
                revised["subject"],
                revised["reference"],
                current["status"],
                current["unit"],
                current["value_exact"],
                signed,
                normalized,
                current["components_json"],
                encoded([flag for flag in flags if flag not in withdrawn]),
                encoded(revision),
            ),
        )
        revised_ids.append(identifier)
    if revised_ids:
        recreate_view(db)
    return revised_ids


def printed_numbers(text):
    """The numbers of a printed expression in order, as exact values."""
    return [
        number(token) for token in re.findall(NUMBER, fraction_text(GROUPED_DIGITS.sub("", text)))
    ]


def run_within(part, whole):
    """Does the sequence stand unbroken inside the other?"""
    return bool(part) and any(
        whole[start : start + len(part)] == part for start in range(len(whole) - len(part) + 1)
    )


def printed_in_order(parts, lines):
    """Do the parts stand one after another, without overlap, on the lines in the order cited?"""
    text, at = "\n".join(lines), 0
    for part in parts:
        at = text.find(part, at)
        if at < 0:
            return False
        at += len(part)
    return True


def adjacent(first, second):
    """True for two printed pages numbered one apart."""
    try:
        return abs(int(first) - int(second)) == 1
    except (TypeError, ValueError):
        return False


def apply_edition_readings(db, decisions: Iterable[dict], editions: Mapping):
    """Give each reading the whole expression that its line of the bound edition prints.

    The earlier expression must be a part of the printed one, or must no longer stand on the
    cited lines. The reviewed components must carry the printed numerals in order, and the
    value comes from the same conversion as every other reading. A longer expression with a
    number that no component can hold keeps no value. A record named as absorbed must hold
    nothing but the rest of the printed expression, or, on the page before or after, one end
    of a value printed across the page break. It leaves the catalogue, and the reading keeps
    its identifier and expression. A reading that already holds the whole expression changes
    only by absorbing such a record: a part of that expression kept as a record of its own, or
    a second record of the same expression.

    A value that the page prints in parts, with other text between them or on neighboring
    lines, is decided with its parts. The expression is then the parts in printed order with
    an ellipsis for what stands between, and the cited lines must print them in that order.
    """
    vocabulary = load_vocabulary("historical")
    revised_ids, absorbed_ids = [], []
    for decision in decisions:
        identifier = decision["quantity_id"]
        current = current_reading(db, identifier)
        previous, revised = decision["previous"], decision["revised"]
        old, new = flat(current["expression"]), flat(decision["expression"])
        components = {key: str(value) for key, value in decision["components"].items()}
        held = json.loads(current["components_json"])
        if (
            identifier in revised_ids
            or identifier in absorbed_ids
            or tuple(sorted(previous)) != tuple(sorted(READING_FIELDS))
            or tuple(sorted(revised)) != tuple(sorted(READING_FIELDS))
            or current["source_id"] != decision["source_id"]
            or current["printed_page"] != decision["printed_page"]
            or old != flat(decision["source_expression"])
            or current["version"] != decision["version"]
            or {key: current[key] for key in READING_FIELDS} != previous
            or revised["quantity"] not in vocabulary["quantity"]
            or revised["role"] not in vocabulary["role"]
            or not flat(revised["subject"] or "")
            or not new
            or (new == old and not decision.get("absorbed"))
        ):
            raise ValueError("Edition reading differs from its frozen reading: " + identifier)
        if new == old and (components != held or revised != previous):
            raise ValueError(
                "A reading that keeps its expression keeps its components: " + identifier
            )
        parts = [flat(part) for part in decision.get("parts", ())]
        basis = reviewed_basis(decision, editions, parts or [new])
        lines = editions[decision["source_id"]]["lines"]
        cited = [flat(lines[number_ - 1]) for number_ in decision["basis"]["lines"]]
        if "parts" in decision and (
            len(parts) < 2
            or not all(parts)
            or new != PARTS_BETWEEN.join(parts)
            or not printed_in_order(parts, cited)
        ):
            raise ValueError("The cited lines do not print these parts in order: " + identifier)
        if old not in new and any(old in line for line in cited):
            raise ValueError("The cited lines still print the earlier reading: " + identifier)
        printed = printed_numbers(new)
        if any(key not in COMPONENT_ORDER for key in components) or (
            components
            and [
                number(fraction_text(components[key]))
                for key in COMPONENT_ORDER
                if key in components
            ]
            != printed
        ):
            raise ValueError("Components differ from the printed numerals: " + identifier)
        original = json.loads(current["original_json"])
        kept = carried(current)

        def converted(expression, parts, typing, original=original, kept=kept):
            return normalize_quantity(
                dict(
                    original,
                    source_expression=expression,
                    components=parts,
                    quantity=typing["quantity"],
                    subject=typing["subject"],
                    reference=typing["reference"],
                    role=typing["role"],
                    direction=kept["direction"],
                )
            )

        frozen = converted(current["expression"], held, previous)
        # A reading that intake marked incomplete has no value to reproduce. Only a longer
        # printed expression can complete it.
        open_reading = current["status"] == "incomplete" and old != new and old in new
        if not open_reading and (
            frozen.get("status"),
            frozen.get("unit"),
            frozen.get("magnitude"),
            frozen.get("signed_magnitude"),
        ) != (
            current["status"],
            current["unit"],
            current["value_exact"],
            current["signed_value_exact"],
        ):
            raise ValueError("The conversion does not reproduce the frozen reading: " + identifier)
        trial = converted(decision["expression"], components, revised)
        if components:
            sound = trial.get("status") == "exact"
        elif held:  # The longer expression has a number that no component can hold.
            sound = old != new and old in new and trial.get("status") == "unsupported"
        else:
            sound = trial.get("status") == current["status"]
        if not sound or (not components and revised != previous):
            raise ValueError("The printed expression does not convert as decided: " + identifier)
        absorbed = []
        rest = new if new == old else new.replace(old, " ", 1)
        ungrouped = [GROUPED_DIGITS.sub("", line) for line in cited]
        for other_id in decision.get("absorbed", ()):
            other = current_reading(db, other_id)
            numerals = printed_numbers(other["expression"])
            if other["printed_page"] == current["printed_page"]:
                joins = (
                    old in new
                    and run_within(numerals, printed_numbers(rest))
                    and any(
                        GROUPED_DIGITS.sub("", flat(other["expression"])) in line
                        for line in ungrouped
                    )
                )
            else:
                # A value printed across a page break, with one end kept as a record of its own
                # page. The reading must hold each component of that record.
                parts = json.loads(other["components_json"])
                joins = (
                    adjacent(other["printed_page"], current["printed_page"])
                    and bool(parts)
                    and all(components.get(key) == str(value) for key, value in parts.items())
                )
            if (
                other_id in [identifier, *revised_ids, *absorbed_ids]
                or other_id in [record["id"] for record in absorbed]
                or other["source_id"] != current["source_id"]
                or other["event_id"] is not None
                or not joins
                or any(
                    db.execute(f"SELECT 1 FROM {table} WHERE {column}=?", (other_id,)).fetchone()
                    for table, column in REFERENCES
                )
            ):
                raise ValueError("Only the rest of the printed expression is merged: " + other_id)
            absorbed.append(
                dict(
                    id=other_id,
                    source_expression=other["expression"],
                    quantity=other["quantity"],
                    subject=other["subject"],
                    role=other["role"],
                    unit=other["unit"],
                    value_exact=other["value_exact"],
                )
            )
        revision = dict(
            kept,
            kind=EDITION_READING,
            role=revised["role"],
            previous_source_expression=current["expression"],
            completed_source_expression=decision["expression"],
            previous_unit=current["unit"],
            previous_value_exact=current["value_exact"],
            basis=basis,
        )
        if revised != previous:
            revision.update(previous=previous, revised=revised)
        if absorbed:
            revision["absorbed_readings"] = absorbed
        db.execute(
            INSERT,
            (
                identifier,
                current["version"] + 1,
                revised["quantity"],
                revised["subject"],
                revised["reference"],
                trial["status"],
                trial["unit"],
                trial["magnitude"],
                trial["signed_magnitude"],
                encoded(trial),
                encoded(components),
                current["flags_json"],
                encoded(revision),
            ),
        )
        for record in absorbed:
            for table, column in OWNED:
                db.execute(f"DELETE FROM {table} WHERE {column}=?", (record["id"],))
            absorbed_ids.append(record["id"])
        revised_ids.append(identifier)
    if revised_ids:
        recreate_view(db)
    return revised_ids, absorbed_ids


def swap_link(db, table, identifier, old, new):
    """Move one link from the old claim to the new one, in every scope that holds it."""
    db.execute(
        f"UPDATE {table} SET context_id=? WHERE id=? AND context_id=?", (new, identifier, old)
    )


def printed_date(components, label):
    """Whether a decision's date is a full day, or the last day of a month named as such.

    A full day may be the one that a heading names for the night before or after it.
    """
    keys = set(components)
    if keys - {"day_relation"} == {"year", "month", "day", "daypart_original"}:
        day = type(components["day"]) is int and 1 <= components["day"] <= 31
        if "day_relation" in keys:
            day = (
                day
                and components["day_relation"] in ("preceding_night", "following_night")
                and label is not None
                and DAYPARTS.get(flat(label).upper()) == "night"
            )
    else:
        day = (
            keys == {"year", "month", "day_rule", "daypart_original"}
            and components["day_rule"] == "last_day_of_month"
        )
    return (
        day
        and all(type(components[key]) is int for key in ("year", "month"))
        and 1 <= components["year"] <= 9999
        and 1 <= components["month"] <= 12
        and (label is None or flat(label).upper() in DAYPARTS)
    )


def stated_claim(db, prior, stated):
    """Return the source's claim for the stated components, adding it when none exists.

    A heading states its own day. A calendar or day origin stated for the prior claim is
    not carried to it. Neither is what a book's claim records about its own date
    expression, such as its role or clock qualification. A heading that names the last
    day of its month keeps that rule and no day number. A heading for the night before or
    after a named day keeps that day, with its relation to the night.
    """
    fields = set(prior)
    book = BOOK_CLAIM_FIELDS <= fields <= BOOK_CLAIM_FIELDS | BOOK_CLAIM_NOTES
    if fields != CLAIM_FIELDS and not book:
        raise ValueError("Date revision needs a plain reviewed claim: " + prior["id"])
    wanted = dict(
        {key: value for key, value in prior.items() if key not in BOOK_CLAIM_NOTES},
        **stated,
        calendar=None,
        day_origin=None,
        component_status=(
            "partial_named_components" if stated["day"] is None else "complete_named_components"
        ),
        claim_basis="reviewed_source_context",
        calendar_validation="not_performed",
        accepted_observing_date=None,
        absolute_timestamp=None,
    )
    prefix = prior["id"].rsplit("-", 1)[0]
    same = sorted(
        identifier
        for identifier, data in db.execute(
            "SELECT id,data_json FROM dates WHERE id LIKE ?", (prefix + "-%",)
        )
        if dict(json.loads(data), id=None) == dict(wanted, id=None)
    )
    if same:
        return same[0]
    digest = hashlib.sha256(encoded([DATE_REVISION, prefix, stated]).encode()).hexdigest()
    new = prefix + "-" + digest[:20]
    db.execute("INSERT INTO dates VALUES (?,?)", (new, encoded(dict(wanted, id=new))))
    return new


def apply_date_revisions(db, decisions: Iterable[dict], editions: Mapping):
    """Bind readings to the date their own heading or table prints.

    A decision whose date is None withdraws a date that the page does not print for the
    readings. They keep the earlier claim in their history and carry none.
    """
    decisions = list(decisions)
    # One pass over each table: neither is indexed by the column these lookups need.
    wanted = {group for decision in decisions for group in decision.get("group_ids", ())}
    members_of, loci_of = collections.defaultdict(set), collections.defaultdict(list)
    if wanted:
        for identifier, group in db.execute(
            "SELECT id,event_id FROM quantities WHERE event_id IS NOT NULL"
        ):
            if group in wanted:
                members_of[group].add(identifier)
    wanted = {identifier for decision in decisions for identifier in decision["quantity_ids"]}
    for locus, identifier in db.execute("SELECT locus_id,quantity_id FROM locus_quantities"):
        if identifier in wanted:
            loci_of[identifier].append(locus)
    moved = []
    for decision in decisions:
        old = decision["previous_date_claim_id"]
        components = decision["date"]
        readings = list(dict.fromkeys(decision["quantity_ids"]))
        groups = list(dict.fromkeys(decision.get("group_ids", ())))
        stored = db.execute("SELECT data_json FROM dates WHERE id=?", (old,)).fetchone()
        label = None if components is None else components.get("daypart_original")
        if (
            stored is None
            or not readings
            or set(readings) & set(moved)
            or (components is not None and not printed_date(components, label))
        ):
            raise ValueError("Date revision needs one prior claim and complete printed components")
        prior = json.loads(stored[0])
        stated = components and dict(
            {key: components.get(key) for key in ("year", "month", "day")},
            daypart=None if label is None else DAYPARTS[flat(label).upper()],
        )
        if stated and "day_rule" in components:
            stated["day_rule"] = components["day_rule"]
        if stated and "day_relation" in components:
            stated.update(
                source_date_role="observation_label",
                source_day_relation=components["day_relation"],
            )
        if stated and all(prior.get(key) == stated[key] for key in stated):
            raise ValueError("Date revision repeats the prior claim: " + old)
        expressions, loci, rows = [], set(), {}
        for identifier in readings:
            current = current_reading(db, identifier)
            claims = [
                claim
                for (claim,) in db.execute(
                    "SELECT date_id FROM quantity_dates WHERE quantity_id=?", (identifier,)
                )
            ]
            if (
                current["source_id"] != decision["source_id"]
                or claims != [old]
                or (current["event_id"] is not None and current["event_id"] not in groups)
            ):
                raise ValueError("Date revision differs from its frozen reading: " + identifier)
            rows[identifier] = current
            expressions.append(current["expression"])
            loci.update(loci_of[identifier])
        for group in groups:
            members = members_of[group]
            claims = [
                claim
                for (claim,) in db.execute(
                    "SELECT date_id FROM group_dates WHERE group_id=?", (group,)
                )
            ]
            if not members or not members <= set(readings) or claims not in ([old], []):
                raise ValueError("Date revision must move a whole group: " + group)
        basis = reviewed_basis(decision, editions, expressions)
        new = stated_claim(db, prior, stated) if stated else None
        scopes = {
            scope
            for table, identifiers in (("quantity_contexts", readings), ("group_contexts", groups))
            for identifier in identifiers
            for (scope,) in db.execute(
                f"SELECT scope_id FROM {table} WHERE id=? AND context_id=?", (identifier, old)
            )
        }
        if not scopes:
            raise ValueError("Prior date claim has no context to revise: " + old)
        if new is None:
            for table, key, identifiers in (
                ("quantity_dates", "quantity_id", readings),
                ("group_dates", "group_id", groups),
            ):
                for identifier in identifiers:
                    db.execute(
                        f"DELETE FROM {table} WHERE {key}=? AND date_id=?", (identifier, old)
                    )
            for table, identifiers in (("quantity_contexts", readings), ("group_contexts", groups)):
                for identifier in identifiers:
                    db.execute(
                        f"DELETE FROM {table} WHERE id=? AND context_id=?", (identifier, old)
                    )
        else:
            value = {key: stated[key] for key in ("day", "month", "year")}
            if "day_rule" in stated:
                value["day_rule"] = stated["day_rule"]
            if label is not None:
                value["daypart_original"] = flat(label)
            locator = dict(role="source_evidence_pages", source_locus_ids=sorted(loci))
            for scope in sorted(scopes):
                db.execute(
                    "INSERT OR IGNORE INTO contexts VALUES (?,?,?,?,?,?)",
                    (
                        new,
                        scope,
                        "recorded_date",
                        encoded(value),
                        decision["source_id"],
                        encoded(locator),
                    ),
                )
            for identifier in readings:
                db.execute(
                    "UPDATE quantity_dates SET date_id=? WHERE quantity_id=? AND date_id=?",
                    (new, identifier, old),
                )
                swap_link(db, "quantity_contexts", identifier, old, new)
            for group in groups:
                db.execute(
                    "UPDATE group_dates SET date_id=? WHERE group_id=? AND date_id=?",
                    (new, group, old),
                )
                swap_link(db, "group_contexts", group, old, new)
        for locus in sorted(loci):
            remaining = db.execute(
                """
                SELECT 1 FROM locus_quantities l JOIN quantity_dates d ON d.quantity_id=l.quantity_id
                WHERE l.locus_id=? AND d.date_id=?
                """,
                (locus, old),
            ).fetchone()
            record = json.loads(
                db.execute("SELECT data_json FROM source_loci WHERE id=?", (locus,)).fetchone()[0]
            )
            links = [link for link in record.get("context_ids", [])]
            for scope in sorted(scopes):
                held = db.execute(
                    "SELECT 1 FROM locus_contexts WHERE locus_id=? AND context_id=? AND scope_id=?",
                    (locus, old, scope),
                ).fetchone()
                if not held:
                    continue
                if new is not None:
                    db.execute(
                        "INSERT OR IGNORE INTO locus_contexts VALUES (?,?,?)", (locus, new, scope)
                    )
                    if dict(context_id=new, scope_id=scope) not in links:
                        links.append(dict(context_id=new, scope_id=scope))
                if not remaining:
                    db.execute(
                        "DELETE FROM locus_contexts WHERE locus_id=? AND context_id=? AND scope_id=?",
                        (locus, old, scope),
                    )
                    links = [link for link in links if link != dict(context_id=old, scope_id=scope)]
            if "context_ids" in record:
                record["context_ids"] = sorted(
                    links, key=lambda link: (link["context_id"], link["scope_id"])
                )
                db.execute(
                    "UPDATE source_loci SET data_json=? WHERE id=?", (encoded(record), locus)
                )
        for identifier, current in rows.items():
            revision = dict(
                carried(current),
                kind=DATE_REVISION,
                role=current["role"],
                previous_date_claim_ids=[old],
                date_claim_ids=[] if new is None else [new],
                basis=basis,
            )
            db.execute(
                INSERT,
                (
                    identifier,
                    current["version"] + 1,
                    current["quantity"],
                    current["subject"],
                    current["reference"],
                    current["status"],
                    current["unit"],
                    current["value_exact"],
                    current["signed_value_exact"],
                    current["normalized_json"],
                    current["components_json"],
                    current["flags_json"],
                    encoded(revision),
                ),
            )
        moved.extend(readings)
    if moved:
        recreate_view(db)
    return moved
