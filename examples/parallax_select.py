"""Resolve the inputs of the parallax studies against the released catalog.

    ./scripts/download-catalog downloads
    python examples/parallax_select.py downloads/tychonides.sqlite

It rewrites three files beside this script:

- parallax-venus-pairs.csv: the complete meridian-to-evening Venus pairs of March 1590.
- parallax-riccioli.csv: Riccioli's horizontal parallaxes by planet and authority.
- parallax-inputs.csv: every other printed value the studies use, with the
  catalog entry that holds it.

Rules:

1. Venus pairs. On Opera Omnia XII, p. 69, the catalog keeps each row of the
   recap as one event and labels each value's column. A row with a meridian
   altitude is a complete pair. The earlier clock belongs to the meridian
   reading. The two armillae declinations are ordered like the row's two
   altitude-derived declinations, whose columns are labeled.
2. Venus days. The catalog does not link a row to its day label. The rows,
   taken from the latest first clock to the earliest, receive the page's day
   labels in increasing order. The catalog's own date for each value is kept
   in the file for comparison.
3. Riccioli. On Almagestum Novum I, p. 700, the two exact parallax entries
   for a planet and authority are its far and near values. The smaller is the
   far one.
4. Other inputs. Each is declared below with its source, printed pages, and
   printed digits. It resolves to the catalog entry on those pages whose
   expression has the same digits. Where several entries share the digits, the
   file records how many and names none.
"""

import argparse
import csv
import json
import re
import sqlite3
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).parent
VULGAR = {"½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4", "⅙": "1/6", "⅚": "5/6"}
VOLUMES = {
    "X": "tycho-oo-10",
    "XI": "tycho-oo-11",
    "XII": "tycho-oo-12",
    "XIII": "tycho-oo-13",
    "Progymnasmata": "brahe-progymnasmata-erara",
    "Astronomia Danica": "longomontanus-astronomia-danica",
    "Origanus": "origanus-ephemerides-brandenburgicae",
}
DAY = "Day [Dies]"
CLOCK = "Hours, minutes"
MERIDIAN_ALTITUDE = "Meridian altitude of Venus"
EVENING_ALTITUDE = "Altitude of Venus in the 90th degree"
MERIDIAN_DECLINATION = "Declination of Venus from the meridian altitude"
EVENING_DECLINATION = "Declination of Venus from the altitude in the 90th degree"
ARMILLAE = "Declination of Venus by the armillae"

# Key, work, printed pages, printed digits, value used, unit of that value.
INPUTS = (
    ("mars_1582_distance", "X", (200,), "721", "721", "earth_radius"),
    ("mars_1582_altitude", "X", (200,), "40 0", "40", "degree"),
    ("mars_1582_parallax", "X", (200,), "0 3 39", "219", "arcsecond"),
    ("mars_1582_longitude_parallax", "X", (200,), "0 2 36", "156", "arcsecond"),
    ("mars_1582_latitude_parallax", "X", (200,), "0 2 34", "154", "arcsecond"),
    ("mars_1587_altitude", "XI", (181, 182, 183, 184, 185, 186, 187), "39", "39", "degree"),
    ("mars_1587_parallax", "XI", (181, 182, 183, 184, 185, 186, 187), "3 55", "235", "arcsecond"),
    (
        "mars_1587_latitude_parallax",
        "XI",
        (181, 182, 183, 184, 185, 186, 187),
        "3 36",
        "216",
        "arcsecond",
    ),
    ("jupiter_1593_mean_distance", "XII", (280,), "3990", "3990", "earth_radius"),
    ("jupiter_1593_distance_reduction", "XII", (280,), "575", "575", "earth_radius"),
    ("jupiter_1593_distance", "XII", (280,), "3415", "3415", "earth_radius"),
    ("jupiter_1593_altitude", "XII", (280,), "11", "11", "degree"),
    ("jupiter_1593_parallax", "XII", (280,), "59", "59", "arcsecond"),
    ("jupiter_1593_september_distance", "XII", (433,), "3042", "3042", "earth_radius"),
    ("jupiter_1593_september_altitude", "XII", (433,), "32 1/3", "97/3", "degree"),
    ("jupiter_1593_september_parallax", "XII", (433,), "0 56", "56", "arcsecond"),
    ("saturn_1599_distance", "XIII", (168, 169), "9400", "9400", "earth_radius"),
    ("saturn_1599_meridian_altitude", "XIII", (168, 169), "35 35 45", "8543/240", "degree"),
    ("saturn_1599_instrument_adjustment", "XIII", (168, 169), "35", "35", "arcsecond"),
    ("saturn_1599_latitude_parallax", "XIII", (168, 169), "18", "18", "arcsecond"),
    ("venus_1582_february_distance", "Progymnasmata", (157, 158), "815", "815", "earth_radius"),
    ("venus_1582_february_altitude", "Progymnasmata", (157, 158), "48 1/2", "97/2", "degree"),
    ("venus_1582_february_parallax", "Progymnasmata", (157, 158), "0 2 48", "168", "arcsecond"),
    ("venus_1582_march_distance", "Progymnasmata", (160, 161, 162), "623", "623", "earth_radius"),
    ("venus_1582_march_afternoon_altitude", "Progymnasmata", (160,), "57", "57", "degree"),
    ("venus_1582_march_afternoon_parallax", "Progymnasmata", (160,), "3 0", "180", "arcsecond"),
    ("venus_1582_march_evening_altitude", "Progymnasmata", (161, 162), "23 1/2", "47/2", "degree"),
    ("venus_1582_march_evening_parallax", "Progymnasmata", (161, 162), "0 5 4", "304", "arcsecond"),
    ("venus_p463_distance", "XII", (463,), "343", "343", "earth_radius"),
    ("venus_p463_altitude", "XII", (463,), "12", "12", "degree"),
    ("venus_p463_parallax", "XII", (463,), "9 20", "560", "arcsecond"),
    ("venus_p463_refraction", "XII", (463,), "6 0", "360", "arcsecond"),
    ("venus_p463_side_a", "XII", (463,), "1112", "1112", "earth_radius"),
    ("venus_p463_side_b", "XII", (463,), "822", "822", "earth_radius"),
    ("venus_p463_included_angle", "XII", (463,), "10 0", "10", "degree"),
    ("venus_p468_distance", "XII", (468,), "348", "348", "earth_radius"),
    ("venus_p468_altitude", "XII", (468,), "3", "3", "degree"),
    ("venus_p468_parallax", "XII", (468,), "9 52", "592", "arcsecond"),
    ("venus_1610_distance", "Astronomia Danica", (185,), "850", "850", "earth_radius"),
    ("venus_1610_altitude", "Astronomia Danica", (185,), "15 1/2", "31/2", "degree"),
    ("venus_1610_parallax", "Astronomia Danica", (185,), "4", "240", "arcsecond"),
    ("mercury_1589_declination", "XI", (339,), "14 55", "179/12", "degree"),
    ("mercury_1589_refraction", "XI", (339,), "8", "480", "arcsecond"),
    ("mercury_1589_parallax", "XI", (339,), "3", "180", "arcsecond"),
    ("mercury_1589_altitude", "XI", (339,), "5", "5", "degree"),
    ("mercury_1589_march24_clock", "XI", (339,), "8 1/4", "33/4", "hour"),
    ("mercury_1589_march27_clock", "XI", (339,), "8 9", "163/20", "hour"),
    ("mercury_1589_march28_clock", "XI", (339,), "8 15", "33/4", "hour"),
    ("venus_1582_february_clock", "Progymnasmata", (157, 158), "3 35", "43/12", "hour"),
    ("venus_1582_march_afternoon_clock", "Progymnasmata", (160,), "2 25", "29/12", "hour"),
    ("venus_1582_march_evening_clock", "Progymnasmata", (161, 162), "8 11", "491/60", "hour"),
    ("mercury_1592_refraction", "XII", (225,), "8 15", "495", "arcsecond"),
    ("mercury_1592_parallax", "XII", (225,), "3 15", "195", "arcsecond"),
    ("venus_1590_march3_meridian_altitude", "XII", (51, 52), "51 35 1/2", "6191/120", "degree"),
    ("venus_1590_march3_meridian_clock", "XII", (51,), "2 47", "167/60", "hour"),
    ("venus_1590_march3_sun_separation", "XII", (51,), "46 0", "46", "degree"),
    ("origanus_venus_latitude", "Origanus", (143,), "1 3 5", "757/720", "degree"),
    ("origanus_mercury_latitude", "Origanus", (143,), "0 17 19", "1039/3600", "degree"),
)
INPUT_FIELDS = [
    "key", "value", "unit", "source_id", "printed_pages", "printed_digits", "catalog_entries",
    "printed_page", "expression", "quantity", "role", "status", "quantity_id",
]  # fmt: skip
PAIR_FIELDS = [
    "day", "measure", "expression", "value_exact", "unit", "quantity_id", "event_id",
    "catalog_date",
]  # fmt: skip
RICCIOLI_FIELDS = [
    "planet", "authority", "far_arcseconds", "near_arcseconds", "far_expression",
    "near_expression", "far_id", "near_id",
]  # fmt: skip


def plain(text):
    return (text or "").replace("\xa0", " ").strip()


def digits(text):
    """The digit groups of a printed expression, with vulgar fractions spelled out."""
    for mark, spelled in VULGAR.items():
        text = text.replace(mark, f" {spelled} ")
    return re.findall(r"\d+/\d+|\d+", text)


def contexts(db, identifier):
    for (value,) in db.execute(
        """SELECT k.value_json FROM quantity_contexts q JOIN contexts k
           ON k.context_id = q.context_id AND k.scope_id = q.scope_id WHERE q.id = ?""",
        (identifier,),
    ):
        item = json.loads(value)
        if isinstance(item, dict):
            yield item


def labelled(db, identifier, key):
    return next((item[key] for item in contexts(db, identifier) if key in item), "")


def date_claims(db, identifier):
    found = set()
    for (data,) in db.execute(
        """SELECT d.data_json FROM quantity_dates q JOIN dates d ON d.id = q.date_id
           WHERE q.quantity_id = ?""",
        (identifier,),
    ):
        item = json.loads(data)
        found.add(f"{item.get('year')}-{item.get('month'):02d}-{item.get('day'):02d}")
    return ";".join(sorted(found))


def page_rows(db, source, pages):
    marks = ",".join("?" * len(pages))
    return db.execute(
        f"""SELECT c.id, c.subject, c.quantity, c.role, c.status, c.expression, c.value_exact,
                   c.unit, c.event_id, c.printed_page
            FROM catalogue c WHERE c.source_id = ? AND c.printed_page IN ({marks})
            ORDER BY c.id""",
        (source, *pages),
    ).fetchall()


def venus_pairs(db):
    """Complete pairs in long form, and the number of rows without a meridian altitude."""
    days, events = [], {}
    for identifier, _, _, _, status, expression, value, unit, event, _ in page_rows(
        db, VOLUMES["XII"], (69,)
    ):
        label = labelled(db, identifier, "source_column_label")
        if label == DAY:
            days.append(int(plain(expression)))
        elif event and status == "exact":
            entry = (Fraction(value), plain(expression), unit, identifier)
            events.setdefault(event, {}).setdefault(label, []).append(entry)
    rows = [(event, found) for event, found in events.items() if EVENING_ALTITUDE in found]
    rows.sort(key=lambda row: -min(row[1][CLOCK])[0])
    lines, incomplete = [], 0
    for day, (event, found) in zip(sorted(days), rows, strict=True):
        if MERIDIAN_ALTITUDE not in found:
            incomplete += 1
            continue
        armillae = sorted(found[ARMILLAE])
        if found[EVENING_DECLINATION][0] < found[MERIDIAN_DECLINATION][0]:
            armillae.reverse()
        clocks = sorted(found[CLOCK])
        measures = {
            "meridian_clock": clocks[0],
            "evening_clock": clocks[1],
            "meridian_altitude": found[MERIDIAN_ALTITUDE][0],
            "evening_altitude": found[EVENING_ALTITUDE][0],
            "meridian_declination_from_altitude": found[MERIDIAN_DECLINATION][0],
            "evening_declination_from_altitude": found[EVENING_DECLINATION][0],
            "meridian_declination_armillae": armillae[0],
            "evening_declination_armillae": armillae[1],
        }
        if any(len(found[label]) != count for label, count in PAIR_SHAPE.items()):
            raise ValueError(f"Unexpected Venus row shape for day {day}")
        for measure, (value, expression, unit, identifier) in measures.items():
            lines.append(
                {
                    "day": day,
                    "measure": measure,
                    "expression": expression,
                    "value_exact": str(value),
                    "unit": unit,
                    "quantity_id": identifier,
                    "event_id": event,
                    "catalog_date": date_claims(db, identifier),
                }
            )
    return lines, incomplete


PAIR_SHAPE = {
    CLOCK: 2,
    MERIDIAN_ALTITUDE: 1,
    EVENING_ALTITUDE: 1,
    MERIDIAN_DECLINATION: 1,
    EVENING_DECLINATION: 1,
    ARMILLAE: 2,
}


def riccioli(db):
    groups = {}
    for identifier, planet, quantity, _, status, expression, value, *_ in page_rows(
        db, "riccioli-almagestum-novum-t1", (700,)
    ):
        if quantity == "parallax_angle" and status == "exact":
            authority = labelled(db, identifier, "native_distance_authority")
            entry = (Fraction(value), plain(expression), identifier)
            groups.setdefault((planet, authority), []).append(entry)
    lines, odd = [], []
    for (planet, authority), found in sorted(groups.items()):
        if len(found) != 2 or not authority:
            odd.append((planet, authority, len(found)))
            continue
        far, near = sorted(found)
        lines.append(
            {
                "planet": planet,
                "authority": authority,
                "far_arcseconds": str(far[0]),
                "near_arcseconds": str(near[0]),
                "far_expression": far[1],
                "near_expression": near[1],
                "far_id": far[2],
                "near_id": near[2],
            }
        )
    return lines, odd


def agrees(declared, unit, value, catalog_unit):
    """Whether a declared value equals the catalog's exact value where the units allow a check."""
    if value is None:
        return True
    if catalog_unit == "arcsecond" and unit in ("degree", "arcsecond"):
        return Fraction(value) == Fraction(declared) * (3600 if unit == "degree" else 1)
    return catalog_unit in ("arcsecond", "second_of_time") or Fraction(value) == Fraction(declared)


def inputs(db):
    lines = []
    for key, work, pages, printed, value, unit in INPUTS:
        wanted = digits(printed)
        found = [
            row for row in page_rows(db, VOLUMES[work], pages) if digits(row[5] or "") == wanted
        ]
        line = {
            "key": key,
            "value": value,
            "unit": unit,
            "source_id": VOLUMES[work],
            "printed_pages": " ".join(str(page) for page in pages),
            "printed_digits": printed,
            "catalog_entries": len(found),
        }
        if len(found) == 1:
            identifier, _, quantity, role, status, expression, exact, catalog_unit, _, page = found[
                0
            ]
            if status == "exact" and not agrees(value, unit, exact, catalog_unit):
                raise ValueError(f"{key}: declared {value} {unit}, catalog {exact} {catalog_unit}")
            line.update(
                printed_page=page,
                expression=plain(expression),
                quantity=quantity,
                role=role,
                status=status,
                quantity_id=identifier,
            )
        lines.append(line)
    return lines


def write(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def select(db):
    pairs, incomplete = venus_pairs(db)
    models, odd = riccioli(db)
    return pairs, incomplete, models, odd, inputs(db)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("catalog", type=Path, help="path to tychonides.sqlite")
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    db = sqlite3.connect(f"file:{args.catalog}?mode=ro", uri=True)
    pairs, incomplete, models, odd, resolved = select(db)
    write(args.output / "parallax-venus-pairs.csv", PAIR_FIELDS, pairs)
    write(args.output / "parallax-riccioli.csv", RICCIOLI_FIELDS, models)
    write(args.output / "parallax-inputs.csv", INPUT_FIELDS, resolved)
    print(f"Venus: {len(pairs) // 8} complete pairs, {incomplete} rows without a meridian altitude")
    print(f"Riccioli: {len(models)} planet and authority rows; left out: {odd}")
    single = [line for line in resolved if line["catalog_entries"] == 1]
    typed = sum(line["status"] == "exact" for line in single)
    shared = sum(line["catalog_entries"] > 1 for line in resolved)
    missing = [line["key"] for line in resolved if line["catalog_entries"] == 0]
    print(
        f"Inputs: {len(resolved)} declared; {typed} resolve to one exact entry, "
        f"{len(single) - typed} to one unclassified entry, {shared} share their digits "
        f"with other entries; not found: {missing}"
    )


if __name__ == "__main__":
    main()
