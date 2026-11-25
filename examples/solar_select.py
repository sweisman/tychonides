"""Select the printed elements of Tycho's solar theory from the released catalog.

The first chapter of the Progymnasmata prints ten equinox instants for 1584 to
1588, three intervals of the Sun's course, the apogee and eccentricity derived
from them, and the constants that correct an observed altitude of the Sun. The
equinox instants are every calculation epoch of the Sun on printed page 13. Each
other item names one catalog quantity, chosen by reading the page. The script
copies the printed expression, exact value, and date from the catalog:

    ./scripts/download-catalog downloads
    python examples/solar_select.py downloads/tychonides.sqlite

It rewrites solar-theory-inputs.csv beside this script. No ephemeris or
expected value is consulted.
"""

import argparse
import json
import sqlite3
from pathlib import Path

from mars_select import clean, date_claim, write

HERE = Path(__file__).parent
SOURCE = "brahe-progymnasmata-erara"
PREFIX = "assertion-sbrahe-progymnasmata-erara-"
ITEMS = {  # Item name and the catalog quantity that prints it.
    "tropical year": "ef1dbcb8935a7c903b2c",
    "vernal to autumnal equinox": "8e4999dbb4ac4d1604c9",
    "vernal equinox to 15 Taurus": "726c1c027ba0f2611ce5",
    "15 Leo to autumnal equinox": "41ce697f4ce27617ecfd",
    "apogee from 15 Taurus": "839c513f88dc85b1cffc",
    "apogee from 15 Leo": "c3e1d3b18cfb270c429e",
    "eccentricity from 15 Taurus": "511d670191af782dc16d",
    "eccentricity from 15 Leo": "1a46b2964e622ad0cdb7",
    "adopted eccentricity": "bbc67625b28266606ef0",
    "obliquity": "4db2508f614c5ce73c88",
    "horizontal parallax of the Sun": "615339164b42fa61abbb",
    "pole altitude": "60667f0e87d3cd341eaa",
    "earlier pole altitude": "c12cd9d77250c0b9aa79",
}
FIELDS = [
    "item",
    "id",
    "source_id",
    "printed_page",
    "quantity",
    "expression",
    "value_exact",
    "unit",
    "julian_date",
]
QUERY = """SELECT c.id, c.source_id, c.printed_page, c.quantity, c.expression, c.status,
                  c.unit, c.value_exact, i.normalized_json
    FROM catalogue c JOIN interpretations i ON i.quantity_id = c.id AND i.version = c.version
    WHERE """


def record(db, item, row):
    identifier, source, page, quantity, expression, status, unit, exact, normalized = row
    if status != "exact":
        raise ValueError("The catalog gives no exact value for " + item)
    place = json.loads(normalized).get("zodiac_longitude_degrees")
    when, _daypart, calendar, reason = date_claim(db, identifier)
    if calendar == "Gregorian":
        raise ValueError("The solar chapter is dated in the Julian calendar")
    return {
        "item": item,
        "id": identifier,
        "source_id": source,
        "printed_page": page,
        "quantity": quantity,
        "expression": clean(expression),
        "value_exact": place if place is not None else exact,
        "unit": "degree" if place is not None else unit or "",
        "julian_date": "" if reason else when,
    }


def select(db):
    rows = []
    for row in db.execute(
        QUERY + "c.source_id = ? AND c.printed_page = 13 AND c.quantity = 'calculation_epoch'"
        " AND c.subject = 'Sun' ORDER BY c.id",
        (SOURCE,),
    ).fetchall():
        entry = record(db, "", row)
        entry["item"] = {3: "vernal equinox", 9: "autumnal equinox"}[entry["julian_date"].month]
        rows.append(entry)
    rows.sort(key=lambda entry: entry["julian_date"])
    if len(rows) != 10:
        raise ValueError("The equinox table should give ten dated instants")
    for item, suffix in ITEMS.items():
        found = db.execute(QUERY + "c.id = ?", (PREFIX + suffix,)).fetchall()
        if len(found) != 1:
            raise ValueError("Missing catalog quantity for " + item)
        rows.append(record(db, item, found[0]))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("catalog", type=Path, help="path to tychonides.sqlite")
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    db = sqlite3.connect(f"file:{args.catalog}?mode=ro", uri=True)
    rows = select(db)
    args.output.mkdir(parents=True, exist_ok=True)
    write(args.output / "solar-theory-inputs.csv", FIELDS, rows)
    print(f"{len(rows)} printed elements")


if __name__ == "__main__":
    main()
