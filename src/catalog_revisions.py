"""Append source-reviewed revisions to readings that already carry an interpretation.

A reading revision assigns the quantity type, subject, reference or role that the printed page
establishes. A date revision moves readings from an inherited date claim to the date their own
heading or table states. Neither changes a printed expression, a component or a value, and every
earlier interpretation stays in the version history.

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
from .date_claims import DAYPARTS
from .normalization import ANGLE_QUANTITIES, ANGULAR_RATES, normalize_quantity
from .vocabulary import load_vocabulary

READING_REVISION = "reviewed_reading_revision"
DATE_REVISION = "reviewed_date_binding"
REVIEWED_KINDS = (READING_REVISION, DATE_REVISION)
BASIS_KINDS = ("printed_heading", "printed_label", "printed_reckoning", "printed_table_column")
CARRIED_FIELDS = ("completed_source_expression", "date_claim_ids")
READING_FIELDS = ("quantity", "subject", "reference", "role")
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
    kept = {key: previous[key] for key in CARRIED_FIELDS if key in previous}
    kept["direction"] = previous.get(
        "direction", json.loads(current["original_json"]).get("direction")
    )
    return kept


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
        if (
            identifier in revised_ids
            or tuple(sorted(previous)) != tuple(sorted(READING_FIELDS))
            or tuple(sorted(revised)) != tuple(sorted(READING_FIELDS))
            or previous == revised
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
        if revised["quantity"] != previous["quantity"]:
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
                )
            )
            if (
                current["status"] != "exact"
                or current["unit"] != "arcsecond"
                or trial.get("status") != "exact"
                or trial.get("unit") != "arcsecond"
                or trial.get("magnitude") != current["value_exact"]
                or trial.get("signed_magnitude") != current["signed_value_exact"]
            ):
                raise ValueError(
                    "A reading revision cannot change the printed value: " + identifier
                )
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
        revision = dict(
            carried(current),
            kind=READING_REVISION,
            role=revised["role"],
            previous=previous,
            revised=revised,
            basis=reviewed_basis(decision, editions, [current["expression"]]),
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
                current["signed_value_exact"],
                current["normalized_json"],
                current["components_json"],
                encoded([flag for flag in flags if flag not in withdrawn]),
                encoded(revision),
            ),
        )
        revised_ids.append(identifier)
    if revised_ids:
        recreate_view(db)
    return revised_ids


def swap_link(db, table, identifier, old, new):
    """Move one link from the old claim to the new one, in every scope that holds it."""
    db.execute(
        f"UPDATE {table} SET context_id=? WHERE id=? AND context_id=?", (new, identifier, old)
    )


def stated_claim(db, prior, stated):
    """Return the source's claim for the stated components, adding it when none exists.

    A heading states its own day. A calendar or day origin stated for the prior claim is
    not carried to it.
    """
    if set(prior) != CLAIM_FIELDS:
        raise ValueError("Date revision needs a plain reviewed claim: " + prior["id"])
    wanted = dict(
        prior,
        **stated,
        calendar=None,
        day_origin=None,
        component_status="complete_named_components",
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
            or (
                components is not None
                and (
                    set(components) != {"year", "month", "day", "daypart_original"}
                    or any(type(components[key]) is not int for key in ("year", "month", "day"))
                    or not 1 <= components["year"] <= 9999
                    or not 1 <= components["month"] <= 12
                    or not 1 <= components["day"] <= 31
                    or (label is not None and flat(label).upper() not in DAYPARTS)
                )
            )
        ):
            raise ValueError("Date revision needs one prior claim and complete printed components")
        prior = json.loads(stored[0])
        stated = components and dict(
            {key: components[key] for key in ("year", "month", "day")},
            daypart=None if label is None else DAYPARTS[flat(label).upper()],
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
            value = {key: components[key] for key in ("day", "month", "year")}
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
