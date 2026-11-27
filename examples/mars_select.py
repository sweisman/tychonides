"""Select the Mars inputs for the opposition studies from the released catalog.

The selection uses catalog fields only. No model, ephemeris, or expected
motion of the planet is consulted. Run it after downloading the catalog:

    ./scripts/download-catalog downloads
    python examples/mars_select.py downloads/tychonides.sqlite

It rewrites four files beside this script:

- mars-oppositions.csv: Longomontanus's table of fourteen oppositions.
- mars-observations.csv: the dated Mars longitude reductions selected from
  Tycho's logs around each opposition.
- mars-predictions.csv: the model predictions of Mars's longitude that the
  logs print in the same windows.
- mars-observations-excluded.csv: every candidate left out, with the reason.

Rules, in order:

1. A candidate is an exact Mars ecliptic longitude in Tycho's four logs whose
   role is a reduction or an adopted value.
2. It needs exactly one complete date claim (year, month, day) and a printed
   zodiac sign. A sign is never supplied from neighboring entries. A date the
   catalog labels Gregorian is moved ten days earlier to the Julian calendar.
   A date with no calendar label is taken as Julian and the label stays blank.
3. The date must lie within 60 days of the opposition date in the table.
4. On each date the adopted values are used if the log prints any. Otherwise
   every reduction for that date is used. The rows of one date share a total
   weight of one, so a night with several trial reductions counts once.
5. A printed calculation hour attached to the same source group is carried
   with the row, together with the daypart recorded in the date claim.
6. A Mars ecliptic latitude is paired when the same source group holds exactly
   one signed reduction or adopted value. Competing latitudes are not paired.
7. Each opposition date is checked against the mean-longitude column of the
   same table, carried between rows at one revolution in 686.98 days. A row
   whose date disagrees with that column by more than 5 degrees takes the one
   month that agrees within 1 degree, keeps its printed year, day, and hour,
   and is flagged. The catalogued month stays in the output.
8. A prediction is an exact Mars ecliptic longitude with the role of a
   historical prediction, a model name, and one complete date in a window.
   Predictions printed without a zodiac sign keep only their value within
   the sign. Such a value of 30 degrees or more is left out, because it
   cannot be a place within a sign.
"""

import argparse
import csv
import json
import sqlite3
import statistics
import unicodedata
from collections import defaultdict
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).parent
WINDOW_DAYS = 60
GREGORIAN_LEAD_DAYS = 10  # Valid from 1582 to February 1700.
MEAN_MOTION = Fraction(36000, 68698)  # Degrees of mean longitude per day.
LOGS = "('tycho-oo-10', 'tycho-oo-11', 'tycho-oo-12', 'tycho-oo-13')"
MONTHS = {
    "ian": 1, "feb": 2, "mar": 3, "apr": 4, "mai": 5, "iun": 6,
    "iul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}  # fmt: skip
OPPOSITION_FIELDS = [
    "number", "year", "month", "day", "hour", "minute", "printed_month", "date_basis",
    "observed_longitude_id", "observed_longitude_expression", "observed_longitude_degrees_exact",
    "mean_longitude_expression", "anomaly_expression", "precession_expression",
    "computed_longitude_expression", "difference_expression",
]  # fmt: skip
OBSERVATION_FIELDS = [
    "opposition", "julian_date", "daypart", "calendar_label", "source_id", "printed_page",
    "longitude_id", "role", "longitude_expression", "longitude_degrees_exact", "date_weight",
    "epoch_id", "epoch_expression", "epoch_seconds", "latitude_id", "latitude_arcseconds_exact",
]  # fmt: skip
PREDICTION_FIELDS = [
    "opposition", "julian_date", "daypart", "calendar_label", "source_id", "printed_page",
    "longitude_id", "model", "longitude_expression", "within_sign_degrees_exact",
    "longitude_degrees_exact",
]  # fmt: skip
EXCLUDED_FIELDS = [
    "opposition", "julian_date", "source_id", "printed_page", "longitude_id", "role",
    "longitude_expression", "reason",
]  # fmt: skip


def clean(text):
    return (text or "").replace("\xa0", " ").strip()


def mixed(text):
    """Exact value of digits followed by an optional vulgar fraction, such as 29½."""
    digits = "".join(ch for ch in text if ch.isascii() and ch.isdigit())
    extra = sum(
        Fraction(unicodedata.numeric(ch)).limit_denominator(60)
        for ch in text
        if not ch.isascii() and unicodedata.category(ch) == "No"
    )
    return Fraction(int(digits) if digits else 0) + extra


def sexagesimal(text):
    """Exact degrees from 'S · D M S', whose first place counts sixties of degrees, or 'D M S'."""
    lead, dot, rest = text.partition("·")
    places = [mixed(part) for part in (rest if dot else lead).split()]
    value = sum(place / 60**index for index, place in enumerate(places))
    return value + (60 * mixed(lead) if dot else 0)


def instant(row, month=None):
    day = date(row["year"], month or row["month"], row["day"]).toordinal()
    return day + Fraction(row["hour"], 24) + Fraction(row["minute"], 1440)


def mismatch(row, others, month=None):
    """Median gap in degrees between a row's mean longitude and the other rows carried to it."""
    mean = sexagesimal(row["mean_longitude_expression"])
    gaps = []
    for other in others:
        carried = sexagesimal(other["mean_longitude_expression"]) + MEAN_MOTION * (
            instant(row, month) - instant(other)
        )
        gaps.append((mean - carried + 180) % 360 - 180)
    return abs(statistics.median(gaps))


def check_dates(rows):
    """Apply rule 7 to the opposition table."""
    for row in rows:
        others = [other for other in rows if other is not row]
        row["date_basis"] = "printed date"
        if mismatch(row, others) <= 5:
            continue
        agreeing = []
        for month in range(1, 13):
            try:
                if mismatch(row, others, month) <= 1:
                    agreeing.append(month)
            except ValueError:  # The day does not exist in that month.
                continue
        if len(agreeing) != 1:
            raise ValueError("Opposition date cannot be reconciled: " + row["number"])
        row["month"] = agreeing[0]
        row["date_basis"] = "month from the mean-longitude column"


def oppositions(db):
    """Rows of the opposition table, read from each observed value's table-row context."""
    rows = []
    query = """SELECT c.id, c.expression, i.normalized_json FROM catalogue c
        JOIN interpretations i ON i.quantity_id = c.id AND i.version = c.version
        WHERE c.source_id = 'longomontanus-astronomia-danica' AND c.printed_page = 342
          AND c.subject = 'Mars' AND c.quantity = 'ecliptic_longitude' AND c.role = 'adopted_value'"""
    for identifier, expression, normalized in db.execute(query).fetchall():
        fields = None
        for (value,) in db.execute(
            """SELECT c.value_json FROM quantity_contexts q JOIN contexts c
               ON c.context_id = q.context_id AND c.scope_id = q.scope_id WHERE q.id = ?""",
            (identifier,),
        ):
            item = json.loads(value)
            if isinstance(item, dict) and item.get("record_type") == "source_table_row":
                fields = {n: clean(str(item.get(f"native_field_{n}", ""))) for n in range(1, 13)}
        if fields is None:
            raise ValueError("Opposition row without its table context: " + identifier)
        rows.append(
            {
                "number": fields[1],
                "year": int(fields[2]),
                "month": MONTHS[fields[3][:3].lower()],
                "day": int(fields[4]),
                "hour": int(fields[5]),
                "minute": int(fields[6]),
                "printed_month": fields[3],
                "observed_longitude_id": identifier,
                "observed_longitude_expression": clean(expression),
                "observed_longitude_degrees_exact": json.loads(normalized)[
                    "zodiac_longitude_degrees"
                ],
                "mean_longitude_expression": fields[8],
                "anomaly_expression": fields[9],
                "precession_expression": fields[10],
                "computed_longitude_expression": fields[11],
                "difference_expression": fields[12],
            }
        )
    if len(rows) != 14:
        raise ValueError(f"Expected fourteen oppositions, found {len(rows)}")
    check_dates(rows)
    return sorted(rows, key=lambda row: (row["year"], row["month"], row["day"]))


def date_claim(db, identifier):
    """Julian date, daypart, and calendar label of a quantity's single complete date claim.

    The last item is the reason when there is no such claim.
    """
    claims = [
        json.loads(data)
        for (data,) in db.execute(
            """SELECT d.data_json FROM quantity_dates q JOIN dates d ON d.id = q.date_id
               WHERE q.quantity_id = ? ORDER BY d.id""",
            (identifier,),
        )
    ]
    complete = [
        claim
        for claim in claims
        if all(isinstance(claim.get(part), int) for part in ("year", "month", "day"))
    ]
    if len(complete) != 1:
        return None, "", "", "no single complete date claim"
    claim = complete[0]
    try:
        when = date(claim["year"], claim["month"], claim["day"])
    except ValueError:
        return None, "", "", "impossible calendar date"
    calendar = claim.get("calendar") or ""
    if calendar == "Gregorian":
        when -= timedelta(days=GREGORIAN_LEAD_DAYS)
    return when, claim.get("daypart") or "", calendar, ""


def window(centers, when):
    """The opposition whose window holds a date, if any."""
    near = [n for n, center in centers.items() if abs((when - center).days) <= WINDOW_DAYS]
    return near[0] if near else None


def candidates(db):
    query = f"""SELECT c.id, c.source_id, c.printed_page, c.role, c.expression, c.event_id,
                      i.normalized_json
        FROM catalogue c JOIN interpretations i ON i.quantity_id = c.id AND i.version = c.version
        WHERE c.source_id IN {LOGS}
          AND c.subject = 'Mars' AND c.quantity = 'ecliptic_longitude' AND c.status = 'exact'
          AND c.role IN ('reduction', 'adopted_value')
        ORDER BY c.id"""
    for identifier, source, page, role, expression, event, normalized in db.execute(query):
        epoch = db.execute(
            """SELECT c.id, c.expression, c.value_exact FROM groups g
               JOIN catalogue c ON c.id = g.epoch_quantity_id
               WHERE g.id = ? AND c.status = 'exact' AND c.unit = 'second_of_time'""",
            (event,),
        ).fetchone()
        latitudes = db.execute(
            """SELECT id, signed_value_exact FROM catalogue
               WHERE event_id = ? AND subject = 'Mars' AND quantity = 'ecliptic_latitude'
                 AND status = 'exact' AND role IN ('reduction', 'adopted_value')
                 AND signed_value_exact IS NOT NULL ORDER BY id""",
            (event,),
        ).fetchall()
        latitude = latitudes[0] if len(latitudes) == 1 else ("", "")
        yield {
            "latitude_id": latitude[0],
            "latitude_arcseconds_exact": latitude[1],
            "source_id": source,
            "printed_page": page,
            "longitude_id": identifier,
            "role": role,
            "longitude_expression": clean(expression),
            "longitude_degrees_exact": json.loads(normalized).get("zodiac_longitude_degrees"),
            "epoch_id": epoch[0] if epoch else "",
            "epoch_expression": clean(epoch[1]) if epoch else "",
            "epoch_seconds": epoch[2] if epoch else "",
        }


def predictions(db, centers, drop):
    """Apply rule 8."""
    query = f"""SELECT c.id, c.source_id, c.printed_page, c.role, c.expression, c.model_name,
                      i.normalized_json
        FROM catalogue c
        JOIN interpretations i ON i.quantity_id = c.id AND i.version = c.version
        WHERE c.source_id IN {LOGS}
          AND c.subject = 'Mars' AND c.quantity = 'ecliptic_longitude' AND c.status = 'exact'
          AND c.role = 'historical_prediction'
        ORDER BY c.id"""
    kept = []
    for identifier, source, page, role, expression, model, normalized in db.execute(query):
        normalized = json.loads(normalized)
        row = {
            "source_id": source,
            "printed_page": page,
            "longitude_id": identifier,
            "role": role,
            "model": model or "",
            "longitude_expression": clean(expression),
            "within_sign_degrees_exact": normalized.get("magnitude_degrees"),
            "longitude_degrees_exact": normalized.get("zodiac_longitude_degrees") or "",
        }
        when, daypart, calendar, reason = date_claim(db, identifier)
        if reason:
            drop(row, reason)
            continue
        number = window(centers, when)
        if number is None:
            continue
        if not row["model"]:
            drop(row, "no model name", number, when)
            continue
        if not row["longitude_degrees_exact"] and Fraction(row["within_sign_degrees_exact"]) >= 30:
            drop(row, "no zodiac sign and a value of 30 degrees or more", number, when)
            continue
        dated = {"julian_date": when, "daypart": daypart, "calendar_label": calendar}
        kept.append({**row, "opposition": number, **dated})
    return sorted(kept, key=lambda row: (row["julian_date"], row["model"], row["longitude_id"]))


def select(db):
    table = oppositions(db)
    centers = {row["number"]: date(row["year"], row["month"], row["day"]) for row in table}
    chosen, excluded = defaultdict(list), []

    def drop(row, reason, number="", when=""):
        excluded.append({**row, "opposition": number, "julian_date": when, "reason": reason})

    for row in candidates(db):
        when, daypart, calendar, reason = date_claim(db, row["longitude_id"])
        if reason:
            drop(row, reason)
            continue
        number = window(centers, when)
        if number is None:
            continue  # Outside every window: not a candidate for these studies.
        if row["longitude_degrees_exact"] is None:
            drop(row, "no printed zodiac sign", number, when)
        else:
            row["daypart"], row["calendar_label"] = daypart, calendar
            chosen[(number, when)].append(row)

    selected = []
    for (number, when), rows in sorted(chosen.items(), key=lambda item: item[0][1]):
        adopted = [row for row in rows if row["role"] == "adopted_value"]
        for row in rows:
            if adopted and row["role"] != "adopted_value":
                drop(row, "superseded by an adopted value on the same date", number, when)
        kept = adopted or rows
        for row in kept:
            selected.append(
                {
                    **row,
                    "opposition": number,
                    "julian_date": when,
                    "date_weight": str(Fraction(1, len(kept))),
                }
            )
    predicted = predictions(db, centers, drop)
    excluded.sort(key=lambda row: (str(row["julian_date"]), row["longitude_id"]))
    return table, selected, predicted, excluded


def write(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("catalog", type=Path, help="path to tychonides.sqlite")
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    db = sqlite3.connect(f"file:{args.catalog}?mode=ro", uri=True)
    table, selected, predicted, excluded = select(db)
    args.output.mkdir(parents=True, exist_ok=True)
    write(args.output / "mars-oppositions.csv", OPPOSITION_FIELDS, table)
    write(args.output / "mars-observations.csv", OBSERVATION_FIELDS, selected)
    write(args.output / "mars-predictions.csv", PREDICTION_FIELDS, predicted)
    write(args.output / "mars-observations-excluded.csv", EXCLUDED_FIELDS, excluded)
    for row in table:
        rows = [item for item in selected if item["opposition"] == row["number"]]
        nights = {item["julian_date"] for item in rows}
        timed = {item["julian_date"] for item in rows if item["epoch_id"]}
        models = [item for item in predicted if item["opposition"] == row["number"]]
        flag = "" if row["date_basis"] == "printed date" else "  " + row["date_basis"]
        print(
            f"{row['number']:>5} {row['year']}-{row['month']:02d}-{row['day']:02d}"
            f"  rows {len(rows):3d}  dates {len(nights):3d}  with hour {len(timed):3d}"
            f"  predictions {len(models):3d}{flag}"
        )
    reasons = defaultdict(int)
    for row in excluded:
        reasons[row["reason"]] += 1
    print(f"selected {len(selected)} rows and {len(predicted)} predictions; excluded:")
    for reason, count in sorted(reasons.items()):
        print(f"  {count:3d}  {reason}")


if __name__ == "__main__":
    main()
