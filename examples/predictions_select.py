"""Select every printed model prediction in Tycho's logs from the released catalog.

The selection uses catalog fields only. No ephemeris or expected motion is
consulted. Run it after downloading the catalog:

    ./scripts/download-catalog downloads
    python examples/predictions_select.py downloads/tychonides.sqlite

It rewrites three files beside this script:

- printed-predictions.csv: the predictions of the Moon and the planets.
- printed-predictions-references.csv: the log's own values for the same body
  and quantity on the same dates.
- printed-predictions-excluded.csv: every candidate left out, with the reason.

Rules, in order:

1. A prediction is an exact ecliptic longitude or latitude of the Moon or a
   planet in Tycho's four logs whose role is a historical prediction.
2. It needs a model name and exactly one complete date claim (year, month,
   day). A date the catalog labels Gregorian is moved ten days earlier to the
   Julian calendar. A date with no calendar label is taken as Julian and the
   label stays blank.
3. A longitude printed without a zodiac sign keeps only its value within the
   sign. Such a value of 30 degrees or more is left out, because it cannot be
   a place within a sign. So is a value the catalog labels a mean longitude or
   counts from an origin other than the equinox. A latitude needs a printed
   direction. Neither a sign nor a direction is supplied from neighboring
   entries.
4. The log's own values for a prediction are the exact reductions and adopted
   values of the same body and quantity whose single complete date is the same
   day. They need a printed zodiac sign or direction. On each date the adopted
   values are used if the log prints any. Otherwise every reduction for that
   date is used. The rows of one date share a total weight of one.
5. A printed calculation hour attached to the same source group as a log value
   is carried with it, together with the daypart recorded in the date claim.
   So is the calculation hour that the catalog links to a prediction.
"""

import argparse
import json
import sqlite3
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

from mars_select import LOGS, clean, date_claim, write

HERE = Path(__file__).parent
BODIES = ("Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
QUANTITIES = ("ecliptic_longitude", "ecliptic_latitude")
QUERY = f"""SELECT c.id, c.source_id, c.printed_page, c.subject, c.quantity, c.role,
                   c.expression, c.event_id, c.unit, c.signed_value_exact, q.original_json,
                   i.normalized_json, c.model_name
    FROM catalogue c JOIN quantities q ON q.id = c.id
    JOIN interpretations i ON i.quantity_id = c.id AND i.version = c.version
    WHERE c.source_id IN {LOGS} AND c.status = 'exact'
      AND c.subject IN {BODIES} AND c.quantity IN {QUANTITIES} AND c.role IN ({{roles}})
    ORDER BY c.id"""
SHARED = ["id", "source_id", "printed_page", "body", "quantity"]
DATED = ["julian_date", "daypart", "calendar_label"]
HOUR = ["epoch_id", "epoch_expression", "epoch_seconds"]
PREDICTION_FIELDS = [*SHARED, "model", "expression", "degrees_exact", "basis", *DATED, *HOUR]
REFERENCE_FIELDS = [
    *SHARED,
    "role",
    "expression",
    "degrees_exact",
    *DATED,
    *HOUR,
    "date_weight",
]
EXCLUDED_FIELDS = [*SHARED, "role", "model", "expression", "julian_date", "reason"]


def value(quantity, unit, signed, normalized):
    """Exact degrees and what the printed entry fixes, or the reason it fixes too little."""
    if quantity == "ecliptic_longitude":
        full = normalized.get("zodiac_longitude_degrees")
        if full is not None:
            return str(full), "printed sign", ""
        return str(normalized.get("magnitude_degrees")), "within the sign", "no printed zodiac sign"
    if signed is None or unit != "arcsecond":
        return "", "", "no printed latitude direction"
    return str(Fraction(signed) / 3600), "printed direction", ""


def entries(db, roles):
    query = QUERY.format(roles=", ".join(f"'{role}'" for role in roles))
    for row in db.execute(query):
        identifier, source, page, body, quantity, role, expression, event, unit, signed = row[:10]
        degrees, basis, gap = value(quantity, unit, signed, json.loads(row[11]))
        original = json.loads(row[10])
        yield {
            "id": identifier,
            "source_id": source,
            "printed_page": page,
            "body": body,
            "quantity": quantity,
            "role": role,
            "model": row[12] or "",
            "not_a_place": original.get("argument_name") == "mean_longitude"
            or bool(original.get("source_longitude_origin")),
            "expression": clean(expression),
            "degrees_exact": degrees,
            "basis": basis,
            "gap": gap,
            "event": event,
        }


def epoch(db, event):
    found = db.execute(
        """SELECT c.id, c.expression, c.value_exact FROM groups g
           JOIN catalogue c ON c.id = g.epoch_quantity_id
           WHERE g.id = ? AND c.status = 'exact' AND c.unit = 'second_of_time'""",
        (event,),
    ).fetchone()
    return (found[0], clean(found[1]), found[2]) if found else ("", "", "")


def calculation_hour(db, identifier):
    """The single exact calculation hour that the catalog links to a prediction."""
    found = db.execute(
        """SELECT c.id, c.expression, c.value_exact FROM quantity_links l
           JOIN catalogue c ON c.id = l.to_id
           WHERE l.from_id = ? AND l.kind = 'calculation_epoch_id'
             AND c.status = 'exact' AND c.unit = 'second_of_time' ORDER BY c.id""",
        (identifier,),
    ).fetchall()
    return (found[0][0], clean(found[0][1]), found[0][2]) if len(found) == 1 else ("", "", "")


def select(db):
    excluded = []

    def drop(row, reason, when=""):
        excluded.append({**row, "julian_date": when, "reason": reason})

    predictions = []
    for row in entries(db, ["historical_prediction"]):
        when, daypart, calendar, reason = date_claim(db, row["id"])
        if not reason and not row["model"]:
            reason = "no model name"
        if not reason and row["quantity"] == "ecliptic_latitude":
            reason = row["gap"]
        if not reason and row["not_a_place"]:
            reason = "a mean longitude or an origin other than the equinox"
        if not reason and row["gap"] and Fraction(row["degrees_exact"]) >= 30:
            reason = "no zodiac sign and a value of 30 degrees or more"
        if reason:
            drop(row, reason, when or "")
            continue
        dated = {"julian_date": when, "daypart": daypart, "calendar_label": calendar}
        hour = dict(zip(HOUR, calculation_hour(db, row["id"]), strict=True))
        predictions.append({**row, **dated, **hour})
    wanted = {(row["body"], row["quantity"], row["julian_date"]) for row in predictions}

    chosen = defaultdict(list)
    for row in entries(db, ["reduction", "adopted_value"]):
        when, daypart, calendar, reason = date_claim(db, row["id"])
        key = (row["body"], row["quantity"], when)
        if reason or key not in wanted:
            continue  # Not placed on a prediction's date, so not a candidate.
        if row["gap"]:
            drop(row, row["gap"], when)
            continue
        identifier, expression, seconds = epoch(db, row["event"])
        chosen[key].append(
            {
                **row,
                "julian_date": when,
                "daypart": daypart,
                "calendar_label": calendar,
                **dict(zip(HOUR, (identifier, expression, seconds), strict=True)),
            }
        )
    references = []
    for key in sorted(chosen, key=lambda item: (item[2], item[0], item[1])):
        rows = chosen[key]
        adopted = [row for row in rows if row["role"] == "adopted_value"]
        for row in rows:
            if adopted and row["role"] != "adopted_value":
                drop(row, "superseded by an adopted value on the same date", key[2])
        kept = adopted or rows
        references.extend({**row, "date_weight": str(Fraction(1, len(kept)))} for row in kept)

    order = {body: index for index, body in enumerate(BODIES)}
    predictions.sort(
        key=lambda row: (
            order[row["body"]],
            row["julian_date"],
            row["quantity"],
            row["model"],
            row["id"],
        )
    )
    excluded.sort(key=lambda row: (str(row["julian_date"]), row["id"]))
    return predictions, references, excluded


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("catalog", type=Path, help="Path to tychonides.sqlite")
    args = parser.parse_args()
    with sqlite3.connect(args.catalog.resolve().as_uri() + "?mode=ro", uri=True) as db:
        predictions, references, excluded = select(db)
    write(HERE / "printed-predictions.csv", PREDICTION_FIELDS, predictions)
    write(HERE / "printed-predictions-references.csv", REFERENCE_FIELDS, references)
    write(HERE / "printed-predictions-excluded.csv", EXCLUDED_FIELDS, excluded)
    counts = defaultdict(lambda: [0, 0])
    dated = {(row["body"], row["quantity"], row["julian_date"]) for row in references}
    for row in predictions:
        key = (row["body"], row["quantity"])
        counts[key][0] += 1
        counts[key][1] += (row["body"], row["quantity"], row["julian_date"]) in dated
    for (body, quantity), (total, matched) in counts.items():
        print(f"{body} {quantity}: {total} predictions, {matched} with a log value on the date")
    reasons = defaultdict(int)
    for row in excluded:
        reasons[row["reason"]] += 1
    print("Left out:", dict(reasons))


if __name__ == "__main__":
    main()
