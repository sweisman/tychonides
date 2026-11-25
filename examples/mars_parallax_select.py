"""Select Tycho's Mars-to-star distances on the two parallax nights of 1587.

Opera Omnia XI pp. 181 to 187 hold the observations around the opposition of
March 1587. Two entries say they were made for the parallax of Mars: the night
of February 23, and the night of March 10 with Mars followed toward its
setting. This script selects the distances of those two nights from the
released catalog:

    ./scripts/download-catalog downloads
    python examples/mars_parallax_select.py downloads/tychonides.sqlite

The rules are fixed here and use no ephemeris or expected value.

1. A candidate is an exact distance of Mars from a star on those pages, with
   the role of a recorded or repeated reading.
2. It needs one complete date claim, on February 23 or March 10, 1587.
3. Its star must be one of six whose modern identity is settled. Four have
   traditional names. The second and third stars in the wing of Virgo are Eta
   and Gamma Virginis: the log gives their declinations as 1° 39' and 0° 51'
   (p. 182), which no other star of that wing has.
4. It needs the exact printed clock of its source group.
5. The origin of the clock must be printed. A date claim marked after noon or
   evening counts from noon. An unmarked entry takes its origin from the words
   of the page, listed in SESSIONS. Hours after midnight belong to the night
   that began on the labeled date.
6. The altitude of Mars printed in the same source group is carried with the
   distance when there is exactly one.

mars-parallax-stars.csv gives the six stars from SIMBAD: ICRS position at
J2000 and proper motion. It was queried through SIMBAD's TAP service, with
ident.id as 'HIP ' and the number in the file:

    SELECT id, main_id, ra, dec, pmra, pmdec FROM basic
    JOIN ident ON oidref = oid WHERE id IN (...)
"""

import argparse
import sqlite3
from datetime import date
from fractions import Fraction
from pathlib import Path

from mars_model import FROM_NOON
from mars_select import clean, date_claim, write

HERE = Path(__file__).parent
SOURCE = "tycho-oo-11"
PAGES = (181, 187)
NIGHTS = (date(1587, 2, 23), date(1587, 3, 10))
STARS = {  # The catalog's name for each star and its Hipparcos number.
    "Spica": 65474,
    "heart of Leo": 49669,
    "tail of Leo": 57632,
    "Arcturus": 69673,
    "second star in wing of Virgo": 60129,
    "third star in wing of Virgo": 61941,
    "third star in southern wing of Virgo": 61941,
}
SESSIONS = (  # Date, first and last clock hour, origin, and the printed words that fix it.
    (date(1587, 2, 23), 7, 9, "noon", "iuxta Horam a Meridie 7 Min. 45"),
    (date(1587, 2, 23), 1, 6, "midnight", "P. M. N."),
    (date(1587, 3, 10), 4, 6, "midnight", "Sequitur obseruatio ♂ ad occasum tendentis P. M. N."),
)
FIELDS = [
    "id",
    "printed_page",
    "julian_date",
    "daypart",
    "clock_origin",
    "origin_basis",
    "star",
    "hip",
    "expression",
    "separation_arcseconds_exact",
    "clock_expression",
    "clock_seconds",
    "altitude_expression",
    "altitude_arcseconds_exact",
    "event_id",
]
EXCLUDED_FIELDS = ["id", "printed_page", "julian_date", "star", "expression", "reason"]


def clock(db, event):
    found = db.execute(
        """SELECT c.expression, c.value_exact FROM groups g
           JOIN catalogue c ON c.id = g.clock_quantity_id
           WHERE g.id = ? AND c.status = 'exact' AND c.unit = 'second_of_time'""",
        (event,),
    ).fetchone()
    return (clean(found[0]), found[1]) if found else ("", "")


def altitude(db, event):
    found = db.execute(
        """SELECT expression, value_exact FROM catalogue
           WHERE event_id = ? AND quantity = 'altitude' AND subject = 'Mars'
             AND status = 'exact' AND unit = 'arcsecond' ORDER BY id""",
        (event,),
    ).fetchall()
    return (clean(found[0][0]), found[0][1]) if len(found) == 1 else ("", "")


def origin(day, daypart, seconds):
    """Clock origin and its basis, or two empty strings when the page does not fix it."""
    if daypart and daypart in FROM_NOON:
        return "noon", "date claim: " + daypart
    hours = Fraction(seconds) / 3600
    for night, first, last, start, words in SESSIONS:
        if not daypart and day == night and first <= hours < last:
            return start, words
    return "", ""


def select(db):
    selected, excluded = [], []
    rows = db.execute(
        """SELECT id, printed_page, reference_object, expression, value_exact, event_id
           FROM catalogue
           WHERE source_id = ? AND printed_page BETWEEN ? AND ? AND subject = 'Mars'
             AND quantity = 'angular_separation' AND status = 'exact' AND unit = 'arcsecond'
             AND role IN ('recorded_reading', 'repeated_reading')
           ORDER BY printed_page, id""",
        (SOURCE, *PAGES),
    ).fetchall()
    for identifier, page, star, expression, value, event in rows:
        day, daypart, _calendar, reason = date_claim(db, identifier)
        printed, seconds = clock(db, event) if event else ("", "")
        start, basis = origin(day, daypart, seconds) if seconds and not reason else ("", "")
        if reason:
            reason = "no single complete date"
        elif day not in NIGHTS:
            reason = "not one of the two parallax nights"
        elif star not in STARS:
            reason = "star not identified"
        elif not seconds:
            reason = "no exact printed clock"
        elif not start:
            reason = "clock origin not printed"
        row = {
            "id": identifier,
            "printed_page": page,
            "julian_date": day or "",
            "daypart": daypart or "",
            "clock_origin": start,
            "origin_basis": basis,
            "star": star or "",
            "hip": STARS.get(star, ""),
            "expression": clean(expression),
            "separation_arcseconds_exact": value,
            "clock_expression": printed,
            "clock_seconds": seconds,
            "event_id": event or "",
            "reason": reason,
        }
        if reason:
            excluded.append(row)
            continue
        row["altitude_expression"], row["altitude_arcseconds_exact"] = altitude(db, event)
        selected.append(row)
    selected.sort(
        key=lambda row: (
            row["julian_date"],
            row["clock_origin"] == "midnight",
            Fraction(row["clock_seconds"]),
            row["id"],
        )
    )
    return selected, excluded


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("catalog", type=Path, help="path to tychonides.sqlite")
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    db = sqlite3.connect(f"file:{args.catalog}?mode=ro", uri=True)
    selected, excluded = select(db)
    args.output.mkdir(parents=True, exist_ok=True)
    write(args.output / "mars-parallax-readings.csv", FIELDS, selected)
    write(args.output / "mars-parallax-excluded.csv", EXCLUDED_FIELDS, excluded)
    print(f"{len(selected)} distances selected, {len(excluded)} left out")


if __name__ == "__main__":
    main()
