"""Select the Mars-to-star distances that Kassel and Uraniborg measured on the same nights.

Jost Bürgi measured the distances of the planets from fixed stars with the
sextant at Kassel from 1590 to 1597. Willebrord Snellius printed them in 1618
(Observationes Hassiacae, pp. 13 to 68). Tycho's logs hold distances of Mars
from some of the same stars on some of the same nights. This script selects
those readings from the released catalog:

    ./scripts/download-catalog downloads
    python examples/mars_kassel_select.py downloads/tychonides.sqlite

The rules are fixed here. They use no ephemeris of Mars and no expected distance.

1. A candidate is an exact distance of Mars from a star, with the role of a
   recorded or repeated reading, in the Kassel book or in Tycho's logs.
2. It needs one complete date claim, from 1590 through 1596. Tycho's observers
   worked at Uraniborg through those years.
3. Its star must be one of five that both sites name. Capella, the left
   shoulder of Aquarius, and the mouth of Pegasus carry the same name at both.
   The eye of Taurus is Aldebaran. Kassel's third star of Aries is the bright
   star of Aries: the book gives it longitude Taurus 2° 7' 44" and latitude
   9° 54' 12" north (p. 65), which no other star of Aries has.
4. The other site must have a candidate of the same star labeled within a day
   of it. Readings outside those dates are not listed.
5. It needs the exact printed clock of its source group.
6. The clocks show hours on a twelve-hour dial. An hour labeled after noon,
   evening, night, or before midnight, or with no label, is counted from noon
   of the labeled date. When that count falls in daylight, and the same dated
   entry also has an hour after sunset, the hour has passed twelve on the dial
   and gains twelve hours. An hour labeled morning is a civil morning hour of
   the labeled date. An hour labeled before noon or after midnight is left
   out, because its day is open.
7. A night runs from noon to noon. A reading is kept when the other site has a
   kept reading of the same star on the same night.
8. The altitude of Mars printed in the same source group is carried with the
   distance when there is exactly one.

Daylight is judged from the Sun's place by a short formula, at the latitude of
each site. mars-kassel-stars.csv gives the five stars from SIMBAD: ICRS
position at J2000 and proper motion. It was queried through SIMBAD's TAP
service, with ident.id as 'HIP ' and the number in the file:

    SELECT id, main_id, ra, dec, pmra, pmdec FROM basic
    JOIN ident ON oidref = oid WHERE id IN (...)
"""

import argparse
import math
import sqlite3
from collections import defaultdict
from datetime import timedelta
from fractions import Fraction
from pathlib import Path

from mars_model import FROM_NOON, SITE_EAST_LONGITUDE, julian_day_number
from mars_parallax_select import altitude, clock
from mars_select import clean, date_claim, write
from planetary_parallax import LATITUDE
from solar_theory import approximate_longitude, mean_elements

HERE = Path(__file__).parent
KASSEL = "snellius-observationes-hassiacae"
YEARS = (1590, 1596)
HALF_DAY = 43200
SITES = {  # Latitude and east longitude in degrees.
    "Kassel": (51 + 19 / 60, 9.5),
    "Uraniborg": (math.degrees(LATITUDE), SITE_EAST_LONGITUDE),
}
OTHER = {"Kassel": "Uraniborg", "Uraniborg": "Kassel"}
STARS = {  # The catalog's name for each star at either site and its Hipparcos number.
    "third star of Aries": 9884,
    "bright star of Aries": 9884,
    "eye of Taurus": 21421,
    "Aldebaran": 21421,
    "Capella": 24608,
    "left shoulder of Aquarius": 106278,
    "mouth of Pegasus": 107315,
}
FIELDS = [
    "id",
    "site",
    "source_id",
    "printed_page",
    "julian_date",
    "daypart",
    "night",
    "star",
    "hip",
    "expression",
    "separation_arcseconds_exact",
    "clock_expression",
    "clock_seconds",
    "seconds_from_noon",
    "clock_basis",
    "altitude_expression",
    "altitude_arcseconds_exact",
    "event_id",
]
EXCLUDED_FIELDS = [
    "id",
    "site",
    "source_id",
    "printed_page",
    "julian_date",
    "daypart",
    "star",
    "expression",
    "clock_expression",
    "reason",
]


def sun_is_up(site, day, seconds):
    """Whether the Sun stands above the horizon at apparent seconds after noon of a date."""
    jd = julian_day_number(day) + float(seconds) / 86400
    tilt = math.radians(mean_elements(jd)[2])
    declination = math.asin(math.sin(tilt) * math.sin(math.radians(approximate_longitude(jd))))
    latitude = math.radians(SITES[site][0])
    hour_angle = math.radians(float(seconds) / 240)
    return (
        math.sin(latitude) * math.sin(declination)
        + math.cos(latitude) * math.cos(declination) * math.cos(hour_angle)
    ) > 0


def placed(site, day, daypart, clock_seconds, evening):
    """Seconds after noon of the labeled date, the basis, and the reason when the hour is open.

    `evening` says whether the same dated entry has an hour after sunset counted from noon.
    """
    if not clock_seconds:
        return None, "", "no exact printed clock"
    seconds = Fraction(clock_seconds)
    if daypart == "morning" and seconds < HALF_DAY:
        return seconds - HALF_DAY, "civil morning hour of the labeled date", ""
    if daypart not in FROM_NOON:
        return None, "", "hour labeled before noon or after midnight: its day is open"
    if not sun_is_up(site, day, seconds):
        return seconds, "counted from noon", ""
    if evening and not sun_is_up(site, day, seconds + HALF_DAY):
        return seconds + HALF_DAY, "counted from noon, past twelve on the dial", ""
    return None, "", "hour falls in daylight and its entry has no evening hour"


def night(day, seconds):
    """The date on whose noon the night of a reading began."""
    return day + timedelta(days=math.floor(Fraction(seconds) / 86400))


def candidates(db):
    """Exact, dated distances of Mars from any star at either site, with their clocks."""
    rows = db.execute(
        """SELECT id, source_id, printed_page, reference_object, expression, value_exact, event_id
           FROM catalogue
           WHERE (source_id = ? OR source_id LIKE 'tycho-oo-1_') AND subject = 'Mars'
             AND quantity = 'angular_separation' AND status = 'exact' AND unit = 'arcsecond'
             AND role IN ('recorded_reading', 'repeated_reading')
           ORDER BY source_id, printed_page, id""",
        (KASSEL,),
    ).fetchall()
    found = []
    for identifier, source, page, star, expression, value, event in rows:
        day, daypart, _calendar, reason = date_claim(db, identifier)
        if reason or not YEARS[0] <= day.year <= YEARS[1]:
            continue
        printed, seconds = clock(db, event) if event else ("", "")
        found.append(
            {
                "id": identifier,
                "site": "Kassel" if source == KASSEL else "Uraniborg",
                "source_id": source,
                "printed_page": page,
                "julian_date": day,
                "daypart": daypart,
                "star": star or "",
                "hip": STARS.get(star, ""),
                "expression": clean(expression),
                "separation_arcseconds_exact": value,
                "clock_expression": printed,
                "clock_seconds": seconds,
                "event_id": event or "",
            }
        )
    return found


def entry(row):
    """The dated entry of a reading: its site, labeled date, and label."""
    return row["site"], row["julian_date"], row["daypart"]


def select(db):
    found = candidates(db)
    evening = defaultdict(bool)
    for row in found:
        if row["clock_seconds"] and row["daypart"] in FROM_NOON:
            dark = not sun_is_up(row["site"], row["julian_date"], Fraction(row["clock_seconds"]))
            evening[entry(row)] |= dark
    labeled = defaultdict(set)
    for row in found:
        if row["hip"]:
            labeled[(row["site"], row["hip"])].add(row["julian_date"])
    scoped = [
        row
        for row in found
        if row["hip"]
        and any(
            abs((row["julian_date"] - other).days) <= 1
            for other in labeled[(OTHER[row["site"]], row["hip"])]
        )
    ]
    sites = defaultdict(set)
    for row in scoped:
        seconds, row["clock_basis"], row["reason"] = placed(
            row["site"],
            row["julian_date"],
            row["daypart"],
            row["clock_seconds"],
            evening[entry(row)],
        )
        if not row["reason"]:
            row["seconds_from_noon"] = seconds
            row["night"] = night(row["julian_date"], seconds)
            sites[(row["night"], row["hip"])].add(row["site"])
    selected, excluded = [], []
    for row in scoped:
        if not row["reason"] and len(sites[(row["night"], row["hip"])]) < 2:
            row["reason"] = "no timed reading of this star at the other site that night"
        if row["reason"]:
            excluded.append(row)
            continue
        row["altitude_expression"], row["altitude_arcseconds_exact"] = altitude(db, row["event_id"])
        selected.append(row)
    selected.sort(
        key=lambda row: (row["night"], row["hip"], row["site"], row["seconds_from_noon"], row["id"])
    )
    excluded.sort(key=lambda row: (row["julian_date"], row["site"], row["printed_page"], row["id"]))
    return selected, excluded


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("catalog", type=Path, help="path to tychonides.sqlite")
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    db = sqlite3.connect(f"file:{args.catalog}?mode=ro", uri=True)
    selected, excluded = select(db)
    args.output.mkdir(parents=True, exist_ok=True)
    write(args.output / "mars-kassel-readings.csv", FIELDS, selected)
    write(args.output / "mars-kassel-excluded.csv", EXCLUDED_FIELDS, excluded)
    print(f"{len(selected)} distances selected, {len(excluded)} left out")


if __name__ == "__main__":
    main()
