"""Select the historical refraction tables from the released catalog.

    ./scripts/download-catalog downloads
    python examples/refraction_select.py downloads/tychonides.sqlite

It rewrites two files beside this script:

- refraction-tables.csv: every table entry that has a recorded altitude argument.
- refraction-tables-excluded.csv: the tables and entries left out, with the reason.

Rules:

1. A candidate is an exact refraction angle in arcseconds from a printed
   refraction table in the Progymnasmata, Astronomia Danica, or Astronomia
   Reformata. The tables are identified by source and printed page.
2. An entry is used when the catalog records its altitude argument. The
   argument is never supplied from the order of the entries.
3. A season label is carried where the catalog records one.
"""

import argparse
import csv
import json
import sqlite3
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).parent
ARGUMENT_KEYS = ("altitude_degrees", "altitude_as_stated", "apparent_altitude_argument_as_printed")
# Source, printed page (None where the catalog has no page), and the table's author.
TABLES = (
    ("brahe-progymnasmata-erara", 79, "Tycho"),
    ("brahe-progymnasmata-erara", 280, "Tycho"),
    ("brahe-progymnasmata-erara", None, "Tycho"),
    ("longomontanus-astronomia-danica", 285, "Longomontanus"),
    ("riccioli-astronomia-reformata", 47, "Riccioli"),
    ("riccioli-astronomia-reformata", 57, "Tycho, as printed by Riccioli"),
)
FIELDS = [
    "author", "source_id", "printed_page", "body", "season", "altitude_degrees",
    "refraction_arcseconds_exact", "expression", "quantity_id",
]  # fmt: skip
EXCLUDED_FIELDS = ["author", "source_id", "printed_page", "body", "entries", "reason"]


def contexts(db, identifier):
    for (value,) in db.execute(
        """SELECT k.value_json FROM quantity_contexts q JOIN contexts k
           ON k.context_id = q.context_id AND k.scope_id = q.scope_id WHERE q.id = ?""",
        (identifier,),
    ):
        item = json.loads(value)
        if isinstance(item, dict):
            yield item


def select(db):
    kept, excluded = [], {}
    for source, page, author in TABLES:
        where = "c.printed_page IS NULL" if page is None else "c.printed_page = ?"
        rows = db.execute(
            f"""SELECT c.id, c.subject, c.expression, c.value_exact FROM catalogue c
                WHERE c.source_id = ? AND {where} AND c.quantity = 'refraction_angle'
                  AND c.status = 'exact' AND c.unit = 'arcsecond' ORDER BY c.id""",
            (source,) if page is None else (source, page),
        ).fetchall()
        for identifier, body, expression, value in rows:
            altitude, season = None, ""
            for item in contexts(db, identifier):
                for key in ARGUMENT_KEYS:
                    if key in item:
                        altitude = item[key]
                season = item.get("source_season", season)
            try:
                altitude = Fraction(str(altitude))
            except (ValueError, ZeroDivisionError):
                key = (author, source, page if page is not None else "", body)
                excluded[key] = excluded.get(key, 0) + 1
                continue
            kept.append(
                {
                    "author": author,
                    "source_id": source,
                    "printed_page": page if page is not None else "",
                    "body": body,
                    "season": season,
                    "altitude_degrees": str(altitude),
                    "refraction_arcseconds_exact": value,
                    "expression": (expression or "").replace("\xa0", " ").strip(),
                    "quantity_id": identifier,
                }
            )
    kept.sort(
        key=lambda row: (
            row["author"],
            row["source_id"],
            row["body"],
            row["season"],
            Fraction(row["altitude_degrees"]),
            row["quantity_id"],
        )
    )
    left_out = [
        {
            "author": author,
            "source_id": source,
            "printed_page": page,
            "body": body,
            "entries": count,
            "reason": "no altitude argument recorded",
        }
        for (author, source, page, body), count in sorted(excluded.items(), key=str)
    ]
    return kept, left_out


def write(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("catalog", type=Path, help="path to tychonides.sqlite")
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    db = sqlite3.connect(f"file:{args.catalog}?mode=ro", uri=True)
    kept, left_out = select(db)
    write(args.output / "refraction-tables.csv", FIELDS, kept)
    write(args.output / "refraction-tables-excluded.csv", EXCLUDED_FIELDS, left_out)
    tables = {}
    for row in kept:
        key = (row["author"], row["printed_page"], row["body"], row["season"])
        tables[key] = tables.get(key, 0) + 1
    for key, count in tables.items():
        print(f"{count:3d} entries  ", *key)
    for row in left_out:
        print(f"{row['entries']:3d} left out ", row["author"], row["printed_page"], row["body"])


if __name__ == "__main__":
    main()
