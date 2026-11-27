"""Compare the distances of Mars from fixed stars measured at Kassel and at Uraniborg.

On some nights of 1593 and 1595 Jost Bürgi at Kassel and Tycho's observers at
Uraniborg measured the distance of Mars from the same star. This script sets
the two readings side by side.

    python examples/mars_kassel.py --output docs/figures

The readings were taken hours apart and from two places, so they are not the
same angle. Mars moves against the stars, and refraction closes the angle by
an amount that depends on how high Mars and the star stand. Each reading is
therefore compared with the distance computed for its own instant and place:
from the JPL DE441 ephemeris, modern star positions, modern refraction in
standard air, and the parallax of Mars. The difference between the two
computed distances is the change to expect between the readings. What is left
of the difference between the readings after that change is the disagreement
of the two observatories.

The distances come from mars-kassel-readings.csv, which mars_kassel_select.py
builds from the catalog. The stars come from mars-kassel-stars.csv and Mars
from mars-kassel-ephemeris.csv, which mars_kassel_ephemeris.py caches from JPL
Horizons. The printed clocks are taken as apparent solar time at each site.
Kassel prints its hours to the half hour, so every result is repeated with the
Kassel clock half an hour later and earlier. The tables need NumPy. The figure
needs Matplotlib.
"""

import argparse
import csv
from collections import defaultdict
from datetime import date
from fractions import Fraction
from pathlib import Path

import mars_model as mm
import numpy as np
from mars_kassel_select import SITES
from mars_parallax_1587 import angle, of_date, raised, sidereal, star_direction, unit
from planetary_parallax import AU_IN_EARTH_RADII
from refraction_tables import STANDARD
from solar_theory import equation_of_time

HERE = Path(__file__).parent
STEP_MINUTES = 30  # Kassel prints its hours to the half hour.
REVIEW_ARCMIN = 30.0  # A difference this large puts the date, hour, star, or reading in question.
REVIEW = "date, hour, star, or reading in question"
CLOCK_REVIEW_DEGREES = 5.0  # A printed altitude of Mars this far from the computed one.
CLOCK_REVIEW = "clock in question: the printed altitude of Mars contradicts the printed hour"
NAMES = {  # The name used on the study page for each Hipparcos number.
    "9884": "bright star of Aries",
    "21421": "Aldebaran",
    "24608": "Capella",
    "106278": "left shoulder of Aquarius",
    "107315": "mouth of Pegasus",
}
READING_FIELDS = [
    "id",
    "site",
    "night",
    "star",
    "hip",
    "printed_page",
    "expression",
    "clock_expression",
    "hours_from_noon",
    "jd_ut",
    "observed_arcmin",
    "computed_arcmin",
    "refraction_arcmin",
    "observed_minus_computed_arcmin",
    "mars_altitude_degrees",
    "star_altitude_degrees",
    "recorded_altitude_degrees",
    "review",
]
PAIR_FIELDS = [
    "night",
    "star",
    "hip",
    "kassel_readings",
    "kassel_hours_from_noon",
    "kassel_arcmin",
    "kassel_mars_altitude_degrees",
    "uraniborg_readings",
    "uraniborg_hours_from_noon",
    "uraniborg_arcmin",
    "uraniborg_mars_altitude_degrees",
    "kassel_minus_uraniborg_arcmin",
    "computed_change_arcmin",
    "difference_left_arcmin",
    "difference_left_kassel_clock_later_arcmin",
    "difference_left_kassel_clock_earlier_arcmin",
    "kassel_minus_de441_arcmin",
    "uraniborg_minus_de441_arcmin",
    "review",
]
SUMMARY_FIELDS = [
    "measure",
    "pairs",
    "mean_arcmin",
    "median_absolute_arcmin",
    "largest_absolute_arcmin",
]
ALTITUDE_FIELDS = [
    "site",
    "night",
    "printed_page",
    "clock_expression",
    "hours_from_noon",
    "recorded_altitude_degrees",
    "computed_altitude_degrees",
    "recorded_minus_computed_degrees",
]


def read(name):
    with (HERE / name).open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def instant(row, minutes=0.0):
    """UT Julian date of a reading whose clock shows apparent time at its site."""
    hours = float(Fraction(row["seconds_from_noon"])) / 3600 + minutes / 60
    day = mm.julian_day_number(date.fromisoformat(row["julian_date"]))
    mean = day + hours / 24 - SITES[row["site"]][1] / 360
    return mean - equation_of_time(mean)


def shifts(row):
    """Minutes added to the clock of a reading in the cases the study computes."""
    return (-STEP_MINUTES, 0, STEP_MINUTES) if row["site"] == "Kassel" else (0,)


def instants():
    """Every UT Julian date the study needs from the ephemeris, as cache keys."""
    wanted = set()
    for row in read("mars-kassel-readings.csv"):
        for minutes in shifts(row):
            wanted.add(f"{instant(row, minutes):.6f}")
    return sorted(wanted)


def zenith(site, jd):
    """Direction of the zenith of a site on the equator of date."""
    latitude, east = SITES[site]
    return unit(sidereal(jd, east), np.deg2rad(latitude))


def altitude(direction, up):
    return float(np.rad2deg(np.arcsin(direction @ up)))


class Sky:
    """Computed distances of Mars from the stars at cached instants."""

    def __init__(self):
        self.mars = {
            row["jd_ut"]: (
                unit(np.deg2rad(float(row["ra_degrees"])), np.deg2rad(float(row["dec_degrees"]))),
                float(row["distance_au"]) * AU_IN_EARTH_RADII,
            )
            for row in read("mars-kassel-ephemeris.csv")
        }
        self.stars = {row["hip"]: row for row in read("mars-kassel-stars.csv")}

    def view(self, site, jd, hip, air=STANDARD):
        """Distance in arcseconds and the altitudes of Mars and the star in degrees, as seen.

        Mars is displaced by its parallax at the site. `air` is None for no refraction.
        """
        up = zenith(site, jd)
        direction, radii = self.mars[f"{jd:.6f}"]
        planet = of_date(direction, jd) * radii - up
        planet /= np.linalg.norm(planet)
        star = of_date(star_direction(self.stars[hip], jd), jd)
        if air:
            planet, star = raised(planet, up, air), raised(star, up, air)
        return angle(planet, star), altitude(planet, up), altitude(star, up)


def evaluate(sky, rows, kassel_minutes=0.0):
    """One record per reading. `kassel_minutes` is added to the Kassel clock."""
    records = []
    for row in rows:
        minutes = kassel_minutes if row["site"] == "Kassel" else 0.0
        jd = instant(row, minutes)
        computed, mars_altitude, star_altitude = sky.view(row["site"], jd, row["hip"])
        bare, _, _ = sky.view(row["site"], jd, row["hip"], air=None)
        recorded = row["altitude_arcseconds_exact"]
        records.append(
            {
                "row": row,
                "site": row["site"],
                "night": row["night"],
                "hip": row["hip"],
                "jd": jd,
                # Hours after the noon that opens the night of the reading.
                "hours": float(Fraction(row["seconds_from_noon"])) / 3600 % 24 + minutes / 60,
                "observed": float(Fraction(row["separation_arcseconds_exact"])),
                "computed": computed,
                "refraction": computed - bare,
                "mars_altitude": mars_altitude,
                "star_altitude": star_altitude,
                "recorded_altitude": float(Fraction(recorded)) / 3600 if recorded else None,
            }
        )
    return records


def clock_in_question(record):
    """Whether the altitude of Mars printed with a reading contradicts its printed hour."""
    recorded = record["recorded_altitude"]
    return recorded is not None and abs(recorded - record["mars_altitude"]) > CLOCK_REVIEW_DEGREES


def mean(values):
    return float(np.mean(list(values)))


def pairs(records):
    """One entry per night and star that both sites measured. Angles are in arcseconds.

    `raw` is Kassel minus Uraniborg as read, `change` the same difference of the
    computed distances, and `left` what remains of the first after the second.
    """
    groups = defaultdict(lambda: defaultdict(list))
    for record in records:
        groups[(record["night"], record["hip"])][record["site"]].append(record)
    found = []
    for (night, hip), sites in sorted(
        groups.items(), key=lambda item: (item[0][0], int(item[0][1]))
    ):
        if len(sites) < 2:
            continue
        pair = {"night": night, "hip": hip}
        for site, readings in sites.items():
            pair[site] = {
                "readings": len(readings),
                "hours": mean(record["hours"] for record in readings),
                "observed": mean(record["observed"] for record in readings),
                "computed": mean(record["computed"] for record in readings),
                "left": mean(record["observed"] - record["computed"] for record in readings),
                "mars_altitude": mean(record["mars_altitude"] for record in readings),
            }
        kassel, uraniborg = pair["Kassel"], pair["Uraniborg"]
        pair["raw"] = kassel["observed"] - uraniborg["observed"]
        pair["change"] = kassel["computed"] - uraniborg["computed"]
        pair["left"] = pair["raw"] - pair["change"]
        found.append(pair)
    return found


def summary_row(measure, values):
    values = np.array(values) / 60
    return {
        "measure": measure,
        "pairs": len(values),
        "mean_arcmin": f"{values.mean():.2f}",
        "median_absolute_arcmin": f"{np.median(np.abs(values)):.2f}",
        "largest_absolute_arcmin": f"{np.abs(values).max():.2f}",
    }


def study():
    """Records of the readings, one entry per pair with its clock cases, and the summary rows."""
    sky, rows = Sky(), read("mars-kassel-readings.csv")
    records = evaluate(sky, rows)
    doubtful = {record["row"]["id"] for record in records if clock_in_question(record)}
    for record in records:
        record["review"] = CLOCK_REVIEW if record["row"]["id"] in doubtful else ""
    rows = [row for row in rows if row["id"] not in doubtful]
    found = pairs([record for record in records if not record["review"]])
    for name, minutes in (("later", STEP_MINUTES), ("earlier", -STEP_MINUTES)):
        for pair, moved in zip(found, pairs(evaluate(sky, rows, minutes)), strict=True):
            pair[name] = moved["left"]
    for pair in found:
        pair["review"] = REVIEW if abs(pair["left"]) > REVIEW_ARCMIN * 60 else ""
    sound = [pair for pair in found if not pair["review"]]
    summary = [
        summary_row("Kassel minus Uraniborg, as read", [pair["raw"] for pair in sound]),
        summary_row(
            "Kassel minus Uraniborg, after the computed change", [pair["left"] for pair in sound]
        ),
        summary_row("The same, Kassel clock half an hour later", [pair["later"] for pair in sound]),
        summary_row(
            "The same, Kassel clock half an hour earlier", [pair["earlier"] for pair in sound]
        ),
        summary_row("Kassel minus DE441", [pair["Kassel"]["left"] for pair in sound]),
        summary_row("Uraniborg minus DE441", [pair["Uraniborg"]["left"] for pair in sound]),
    ]
    return records, found, summary


def reading_row(record):
    row = record["row"]
    recorded = record["recorded_altitude"]
    return {
        "id": row["id"],
        "site": row["site"],
        "night": row["night"],
        "star": NAMES[row["hip"]],
        "hip": row["hip"],
        "printed_page": row["printed_page"],
        "expression": row["expression"],
        "clock_expression": row["clock_expression"],
        "hours_from_noon": f"{record['hours']:.3f}",
        "jd_ut": f"{record['jd']:.6f}",
        "observed_arcmin": f"{record['observed'] / 60:.3f}",
        "computed_arcmin": f"{record['computed'] / 60:.3f}",
        "refraction_arcmin": f"{record['refraction'] / 60:.2f}",
        "observed_minus_computed_arcmin": f"{(record['observed'] - record['computed']) / 60:.2f}",
        "mars_altitude_degrees": f"{record['mars_altitude']:.2f}",
        "star_altitude_degrees": f"{record['star_altitude']:.2f}",
        "recorded_altitude_degrees": "" if recorded is None else f"{recorded:.3f}",
        "review": record["review"],
    }


def pair_row(pair):
    kassel, uraniborg = pair["Kassel"], pair["Uraniborg"]
    return {
        "night": pair["night"],
        "star": NAMES[pair["hip"]],
        "hip": pair["hip"],
        "kassel_readings": kassel["readings"],
        "kassel_hours_from_noon": f"{kassel['hours']:.2f}",
        "kassel_arcmin": f"{kassel['observed'] / 60:.2f}",
        "kassel_mars_altitude_degrees": f"{kassel['mars_altitude']:.1f}",
        "uraniborg_readings": uraniborg["readings"],
        "uraniborg_hours_from_noon": f"{uraniborg['hours']:.2f}",
        "uraniborg_arcmin": f"{uraniborg['observed'] / 60:.2f}",
        "uraniborg_mars_altitude_degrees": f"{uraniborg['mars_altitude']:.1f}",
        "kassel_minus_uraniborg_arcmin": f"{pair['raw'] / 60:.2f}",
        "computed_change_arcmin": f"{pair['change'] / 60:.2f}",
        "difference_left_arcmin": f"{pair['left'] / 60:.2f}",
        "difference_left_kassel_clock_later_arcmin": f"{pair['later'] / 60:.2f}",
        "difference_left_kassel_clock_earlier_arcmin": f"{pair['earlier'] / 60:.2f}",
        "kassel_minus_de441_arcmin": f"{kassel['left'] / 60:.2f}",
        "uraniborg_minus_de441_arcmin": f"{uraniborg['left'] / 60:.2f}",
        "review": pair["review"],
    }


def altitude_rows(records):
    """Printed altitudes of Mars beside the computed ones, once for each printed altitude."""
    seen, rows = set(), []
    for record in records:
        row, recorded = record["row"], record["recorded_altitude"]
        key = (row["site"], row["event_id"])
        if recorded is None or key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "site": row["site"],
                "night": row["night"],
                "printed_page": row["printed_page"],
                "clock_expression": row["clock_expression"],
                "hours_from_noon": f"{record['hours']:.3f}",
                "recorded_altitude_degrees": f"{recorded:.3f}",
                "computed_altitude_degrees": f"{record['mars_altitude']:.3f}",
                "recorded_minus_computed_degrees": f"{recorded - record['mars_altitude']:.2f}",
            }
        )
    return rows


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_tables(output):
    records, found, summary = study()
    write_csv(
        output / "mars-kassel-readings.csv",
        READING_FIELDS,
        [reading_row(record) for record in records],
    )
    write_csv(output / "mars-kassel-pairs.csv", PAIR_FIELDS, [pair_row(pair) for pair in found])
    write_csv(output / "mars-kassel-summary.csv", SUMMARY_FIELDS, summary)
    write_csv(output / "mars-kassel-altitudes.csv", ALTITUDE_FIELDS, altitude_rows(records))
    return found


def plot(plt, output, found):
    """Kassel minus Uraniborg for each night and star, as read and after the computed change."""
    sound = [pair for pair in found if not pair["review"]]
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    blue, gray = "#00699a", "#5b6673"
    for position, pair in enumerate(sound):
        low, high = sorted((pair["later"] / 60, pair["earlier"] / 60))
        ax.plot([position, position], [low, high], color=blue, lw=1.6, alpha=0.45)
        ax.scatter(position, pair["raw"] / 60, s=42, facecolor="none", edgecolor=gray, lw=1.3)
        ax.scatter(position, pair["left"] / 60, s=46, color=blue, edgecolor="white", lw=0.6)
        previous = sound[position - 1]["night"] if position else ""
        if position and previous != pair["night"]:
            ax.axvline(position - 0.5, color="#d5dae0", lw=0.8)
    ax.axhline(0, color="#89939f", lw=0.8)
    labels = []
    for pair in sound:
        day = date.fromisoformat(pair["night"])
        labels.append(f"{day:%b} {day.day}, {day.year}\n{NAMES[pair['hip']]}")
    ax.set_xticks(range(len(sound)), labels, rotation=55, ha="right", fontsize=8.5)
    ax.set_xlim(-0.6, len(sound) - 0.4)
    ax.set(
        ylabel="Kassel − Uraniborg (arcminutes)",
        title="Mars from the same star on the same night, at Kassel and at Uraniborg",
    )
    ax.legend(
        handles=[
            plt.Line2D([], [], ls="", marker="o", mfc="none", mec=gray, mew=1.3, ms=6.5),
            plt.Line2D([], [], ls="", marker="o", color=blue, mec="white", ms=7.5),
            plt.Line2D([], [], color=blue, lw=1.6, alpha=0.45),
        ],
        labels=[
            "As read",
            "After the computed motion and refraction",
            "Kassel clock half an hour either way",
        ],
        frameon=False,
        fontsize=9.5,
        loc="upper left",
    )
    ax.grid(axis="y", alpha=0.18)
    ax.tick_params(axis="x", length=0)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(output / "mars-kassel.png", dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tables-only", action="store_true", help="skip the figure")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    found = write_tables(args.output)
    if args.tables_only:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 11, "axes.titleweight": "bold", "axes.labelcolor": "#263445"})
    plot(plt, args.output, found)


if __name__ == "__main__":
    main()
