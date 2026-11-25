"""Reproduce Tycho's solar apogee and eccentricity and compare them with DE441.

The printed elements come from solar-theory-inputs.csv beside this script,
which solar_select.py builds from the catalog. Tycho's solar refraction table
comes from refraction-tables.csv. The DE441 longitudes of the Sun come from
solar-theory-ephemeris.csv, which solar_ephemeris.py caches from JPL Horizons.

    python examples/solar_theory.py --output docs/figures

The script does four things.

1. It reads DE441 at each printed equinox instant. The printed hours count from
   apparent noon at Uraniborg, so the equation of time and the longitude of
   Uraniborg turn them into UT.
2. It repeats Tycho's construction of the eccentric circle from his three
   printed intervals, and applies the same construction to the intervals DE441
   gives for 1584 to 1588.
3. It passes the DE441 Sun through Tycho's own reduction of a meridian
   altitude: his solar refraction table, his horizontal parallax, his pole
   altitude, and his obliquity. The intervals and elements that result are what
   exact altitudes would have given him.
4. It anchors an eccentric with his adopted elements on the printed equinoxes
   and follows its difference from DE441 through 1588.

The tables need NumPy. The figure needs Matplotlib.
"""

import argparse
import csv
from datetime import date
from fractions import Fraction
from pathlib import Path

import mars_model as mm
import numpy as np
from planetary_parallax import LATITUDE
from refraction_tables import MODERN_SOLAR_PARALLAX, altitude_parallax, bennett
from refraction_tables import load as load_refraction

HERE = Path(__file__).parent
J2000 = 2451545.0
SITE_LATITUDE = float(np.rad2deg(LATITUDE))
YEARS = range(1584, 1589)
TARGETS = {  # Longitude in degrees of each place the construction uses.
    "vernal equinox": 0.0,
    "15 Taurus": 45.0,
    "15 Leo": 135.0,
    "autumnal equinox": 180.0,
}
INTERVALS = {  # Printed interval and the two places it joins.
    "vernal to autumnal equinox": ("vernal equinox", "autumnal equinox"),
    "vernal equinox to 15 Taurus": ("vernal equinox", "15 Taurus"),
    "15 Leo to autumnal equinox": ("15 Leo", "autumnal equinox"),
}
WINDOW = 2  # Cached days on either side of each DE441 crossing.
YEAR_STEP = 10  # Days between the positions that follow the model through 1588.
EQUINOX_FIELDS = [
    "item",
    "id",
    "julian_date",
    "expression",
    "jd_ut",
    "de441_longitude_degrees",
    "printed_minus_de441_arcmin",
    "printed_minus_de441_hours",
    "reduction_gives_arcmin",
    "reduction_gives_hours",
]
INTERVAL_FIELDS = [
    "interval",
    "printed_days",
    "de441_days",
    "reduction_gives_days",
    "printed_minus_de441_hours",
    "printed_minus_reduction_hours",
]
ELEMENT_FIELDS = ["basis", "place", "apogee_degrees", "eccentricity", "greatest_equation_arcmin"]
YEAR_FIELDS = ["jd_ut", "de441_longitude_degrees", "model_minus_de441_arcmin"]


def read(name):
    with (HERE / name).open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def inputs():
    """Printed equinox rows, and every other printed item by name."""
    rows = read("solar-theory-inputs.csv")
    equinoxes = [row for row in rows if row["julian_date"]]
    return equinoxes, {row["item"]: row for row in rows if not row["julian_date"]}


def number(row):
    return float(Fraction(row["value_exact"]))


def mean_elements(jd):
    """Mean longitude and mean anomaly of the Sun, mean obliquity, and centuries from J2000.

    The polynomials are those of Meeus, Astronomical Algorithms (1998), chapter 25.
    """
    centuries = (jd - J2000) / 36525
    mean = 280.46646 + 36000.76983 * centuries + 0.0003032 * centuries**2
    anomaly = 357.52911 + 35999.05029 * centuries - 0.0001537 * centuries**2
    return mean, anomaly, 23.439291 - 0.0130042 * centuries, centuries


def approximate_longitude(jd):
    """Apparent longitude of the Sun in degrees, good to a hundredth of a degree."""
    mean, anomaly, _, centuries = mean_elements(jd)
    anomaly = np.deg2rad(anomaly)
    center = (
        (1.914602 - 0.004817 * centuries) * np.sin(anomaly)
        + (0.019993 - 0.000101 * centuries) * np.sin(2 * anomaly)
        + 0.000289 * np.sin(3 * anomaly)
    )
    node = np.deg2rad(125.04 - 1934.136 * centuries)
    return (mean + center - 0.00569 - 0.00478 * np.sin(node)) % 360


def equation_of_time(jd):
    """Apparent minus mean solar time, in days."""
    mean, _, obliquity, _ = mean_elements(jd)
    longitude = np.deg2rad(approximate_longitude(jd))
    ascension = np.arctan2(np.cos(np.deg2rad(obliquity)) * np.sin(longitude), np.cos(longitude))
    return mm.wrapped(mean - 0.0057183 - np.rad2deg(ascension)) / 360


def printed_instant(row, apparent=True):
    """UT Julian date of a printed equinox, whose hours count from noon at Uraniborg."""
    hours = 12 + number(row) / 3600
    instant = mm.jd_ut(date.fromisoformat(row["julian_date"]), hours)
    return instant - equation_of_time(instant) if apparent else instant


def crossing_day(year, target):
    """Julian day number nearest the Sun's arrival at a longitude in a year."""
    jd = mm.julian_day_number(date(year, 3, 10)) + target / 0.9856
    for _ in range(4):
        jd -= mm.wrapped(approximate_longitude(jd) - target) / 0.9856
    return round(jd)


def year_days():
    start = mm.julian_day_number(date(1588, 1, 1))
    return [start + step for step in range(0, 366, YEAR_STEP)]


def instants():
    """Every UT Julian date the study needs from the ephemeris."""
    wanted = {f"{printed_instant(row):.6f}" for row in inputs()[0]}
    for year in YEARS:
        for target in TARGETS.values():
            middle = crossing_day(year, target)
            wanted |= {f"{middle + day:.6f}" for day in range(-WINDOW, WINDOW + 1)}
    return sorted(wanted | {f"{day:.6f}" for day in year_days()})


def load_ephemeris():
    return {
        row["jd_ut"]: float(row["longitude_degrees"]) for row in read("solar-theory-ephemeris.csv")
    }


def crossing(ephemeris, year, target, offset=0.0):
    """UT Julian date at which DE441 puts the Sun `offset` degrees past a longitude."""
    middle = crossing_day(year, target)
    days = np.arange(-WINDOW, WINDOW + 1)
    past = [mm.wrapped(ephemeris[f"{middle + day:.6f}"] - target) for day in days]
    return middle + float(np.polynomial.Polynomial.fit(past, days, len(days) - 1)(offset))


def construction(year, half, place, interval):
    """Apogee in degrees and eccentricity of the eccentric through both equinoxes and one place.

    The Sun moves uniformly on a circle of radius one about the origin. The Earth lies on the
    chord joining the equinoxes, and sees the third place 45 degrees from the nearer equinox.
    """
    rate = 2 * np.pi / year
    vernal = (np.pi - rate * half) / 2
    height = np.sin(vernal)
    if place == "15 Taurus":
        sun = vernal + rate * interval
        across = np.cos(sun) - (np.sin(sun) - height)
    else:
        sun = np.pi - vernal - rate * interval
        across = np.cos(sun) + (np.sin(sun) - height)
    earth = complex(across, height)
    return float(np.rad2deg(np.angle(-earth)) % 360), abs(earth)


class Reduction:
    """Tycho's reduction of a meridian altitude of the Sun to its longitude."""

    def __init__(self, items, true_obliquity, pole="pole altitude"):
        table = load_refraction()[("Tycho", "Sun", "")]
        self.altitudes = [row["altitude"] for row in table]
        self.refractions = [row["refraction"] for row in table]
        self.parallax = number(items["horizontal parallax of the Sun"])
        self.pole = number(items[pole]) / 3600
        self.obliquity = np.deg2rad(number(items["obliquity"]) / 3600)
        self.true_obliquity = np.deg2rad(true_obliquity)

    def seen(self, altitude):
        """Altitude at which the Sun's center appears for its geocentric altitude, in degrees."""
        lowered = altitude - altitude_parallax(altitude, MODERN_SOLAR_PARALLAX) / 3600
        lifted = lowered
        for _ in range(4):
            lifted = lowered + bennett(lifted) / 3600
        return float(lifted)

    def correction(self, altitude):
        """Arcseconds Tycho adds to an observed altitude: his parallax less his refraction."""
        refraction = np.interp(altitude, self.altitudes, self.refractions, right=0.0)
        return float(altitude_parallax(altitude, self.parallax) - refraction)

    def longitude(self, true_longitude):
        """Longitude the reduction gives when the Sun stands at a true longitude."""
        longitude = np.deg2rad(true_longitude)
        declination = np.rad2deg(np.arcsin(np.sin(self.true_obliquity) * np.sin(longitude)))
        observed = self.seen(90 - SITE_LATITUDE + declination)
        reduced = observed + self.correction(observed) / 3600 - (90 - self.pole)
        found = np.rad2deg(np.arcsin(np.sin(np.deg2rad(reduced)) / np.sin(self.obliquity)))
        return float(found if np.cos(longitude) > 0 else 180 - found)

    def true_place(self, target):
        """True longitude of the Sun when the reduction puts it at a target longitude."""
        place = target
        for _ in range(8):
            place -= mm.wrapped(self.longitude(place) - target)
        return place


def interval_means(ephemeris, offsets):
    """Mean length in days of each interval over the years, for an offset at each place."""
    found = {}
    for name, (first, last) in INTERVALS.items():
        found[name] = float(
            np.mean(
                [
                    crossing(ephemeris, year, TARGETS[last], offsets[last])
                    - crossing(ephemeris, year, TARGETS[first], offsets[first])
                    for year in YEARS
                ]
            )
        )
    return found


def element_rows(basis, year, lengths):
    half = lengths["vernal to autumnal equinox"]
    rows = []
    for place, name in (
        ("15 Taurus", "vernal equinox to 15 Taurus"),
        ("15 Leo", "15 Leo to autumnal equinox"),
    ):
        rows.append((basis, place, *construction(year, half, place, lengths[name])))
    return rows


class Model:
    """An eccentric with Tycho's adopted elements, anchored on the printed equinoxes."""

    def __init__(self, items, equinoxes):
        self.apogee = np.deg2rad(number(items["apogee from 15 Taurus"]))
        self.eccentricity = number(items["adopted eccentricity"]) / 100000
        self.rate = 2 * np.pi / (number(items["tropical year"]) / 86400)
        self.start = printed_instant(equinoxes[0])
        gaps = []
        for row in equinoxes:
            seen = np.deg2rad(TARGETS[row["item"]]) - self.apogee
            mean = self.apogee + seen + np.arcsin(self.eccentricity * np.sin(seen))
            elapsed = printed_instant(row) - self.start
            gaps.append(mm.wrapped(np.rad2deg(mean - self.rate * elapsed)))
        self.mean_at_start = np.deg2rad(float(np.mean(gaps)))
        self.anchor_spread_arcmin = float(np.ptp(gaps) * 60)

    def longitude(self, jd):
        anomaly = self.mean_at_start + self.rate * (jd - self.start) - self.apogee
        seen = np.angle(self.eccentricity + np.exp(1j * anomaly))
        return float(np.rad2deg(self.apogee + seen) % 360)


def study():
    """Rows of the four output tables."""
    equinoxes, items = inputs()
    ephemeris = load_ephemeris()
    middle = float(np.mean([printed_instant(row) for row in equinoxes]))
    mean_longitude, mean_anomaly, true_obliquity, _ = mean_elements(middle)
    reduction = Reduction(items, true_obliquity)
    earlier = Reduction(items, true_obliquity, "earlier pole altitude")
    offsets = {name: reduction.true_place(target) - target for name, target in TARGETS.items()}
    earlier_offsets = {
        name: earlier.true_place(target) - target for name, target in TARGETS.items()
    }
    exact = dict.fromkeys(TARGETS, 0.0)

    equinox_rows = []
    for row in equinoxes:
        target = TARGETS[row["item"]]
        year = int(row["julian_date"][:4])
        instant = printed_instant(row)
        longitude = ephemeris[f"{instant:.6f}"]
        true_crossing = crossing(ephemeris, year, target)
        reduced_crossing = crossing(ephemeris, year, target, offsets[row["item"]])
        equinox_rows.append(
            {
                "item": row["item"],
                "id": row["id"],
                "julian_date": row["julian_date"],
                "expression": row["expression"],
                "jd_ut": f"{instant:.6f}",
                "de441_longitude_degrees": f"{longitude:.5f}",
                "printed_minus_de441_arcmin": f"{mm.wrapped(target - longitude) * 60:.1f}",
                "printed_minus_de441_hours": f"{(instant - true_crossing) * 24:.2f}",
                "reduction_gives_arcmin": f"{-offsets[row['item']] * 60:.1f}",
                "reduction_gives_hours": f"{(reduced_crossing - true_crossing) * 24:.2f}",
            }
        )

    printed = {name: number(items[name]) / 86400 for name in INTERVALS}
    modern = interval_means(ephemeris, exact)
    reduced = interval_means(ephemeris, offsets)
    interval_rows = [
        {
            "interval": name,
            "printed_days": f"{printed[name]:.4f}",
            "de441_days": f"{modern[name]:.4f}",
            "reduction_gives_days": f"{reduced[name]:.4f}",
            "printed_minus_de441_hours": f"{(printed[name] - modern[name]) * 24:.2f}",
            "printed_minus_reduction_hours": f"{(printed[name] - reduced[name]) * 24:.2f}",
        }
        for name in INTERVALS
    ]

    year = number(items["tropical year"]) / 86400
    elements = [
        (
            "printed result",
            place,
            number(items[f"apogee from {place}"]),
            number(items[f"eccentricity from {place}"]) / 60,
        )
        for place in ("15 Taurus", "15 Leo")
    ]
    elements += element_rows("recomputed from the printed intervals", year, printed)
    elements += element_rows("DE441 intervals", year, modern)
    elements += element_rows("DE441 through Tycho's reduction", year, reduced)
    elements += element_rows(
        "DE441 through Tycho's reduction, earlier pole altitude",
        year,
        interval_means(ephemeris, earlier_offsets),
    )
    orbit = 0.016708634 - 0.000042037 * (middle - J2000) / 36525
    elements.append(("ellipse of date", "", (mean_longitude - mean_anomaly + 180) % 360, 2 * orbit))
    element_table = [
        {
            "basis": basis,
            "place": place,
            "apogee_degrees": f"{apogee:.3f}",
            "eccentricity": f"{eccentricity:.5f}",
            "greatest_equation_arcmin": f"{np.rad2deg(np.arcsin(eccentricity)) * 60:.1f}",
        }
        for basis, place, apogee, eccentricity in elements
    ]

    model = Model(items, equinoxes)
    year_rows = []
    for day in year_days():
        longitude = ephemeris[f"{day:.6f}"]
        difference = mm.wrapped(model.longitude(day) - longitude) * 60
        year_rows.append(
            {
                "jd_ut": f"{day:.6f}",
                "de441_longitude_degrees": f"{longitude:.5f}",
                "model_minus_de441_arcmin": f"{difference:.1f}",
            }
        )
    notes = {
        "equation_of_time_minutes": [
            round(float(equation_of_time(printed_instant(row)) * 1440), 1) for row in equinoxes
        ],
        "tycho_correction_arcseconds": {
            name: round(reduction.correction(reduction.seen(90 - SITE_LATITUDE + height)))
            for name, height in (("equinox", 0.0), ("15 Taurus and 15 Leo", 16.37))
        },
        "anchor_spread_arcmin": round(model.anchor_spread_arcmin, 2),
        "true_obliquity_degrees": round(float(true_obliquity), 4),
    }
    return equinox_rows, interval_rows, element_table, year_rows, offsets, notes


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_tables(output):
    """Write every numerical output. Needs NumPy only."""
    equinoxes, intervals, elements, year, offsets, notes = study()
    write_csv(output / "solar-theory-equinoxes.csv", EQUINOX_FIELDS, equinoxes)
    write_csv(output / "solar-theory-intervals.csv", INTERVAL_FIELDS, intervals)
    write_csv(output / "solar-theory-elements.csv", ELEMENT_FIELDS, elements)
    write_csv(output / "solar-theory-year.csv", YEAR_FIELDS, year)
    return equinoxes, year, offsets, notes


def plot(plt, output, equinoxes, year, offsets):
    """The anchored model against DE441 through 1588, with the equinoxes and the reduction."""
    fig, ax = plt.subplots(figsize=(9.5, 4.8), layout="constrained")
    longitude = [float(row["de441_longitude_degrees"]) for row in year]
    order = np.argsort(longitude)
    ax.plot(
        np.array(longitude)[order],
        np.array([float(row["model_minus_de441_arcmin"]) for row in year])[order],
        color="#00699a",
        lw=2,
        label="Eccentric with Tycho's elements",
    )
    ax.scatter(
        [TARGETS[row["item"]] for row in equinoxes],
        [float(row["printed_minus_de441_arcmin"]) for row in equinoxes],
        s=42,
        color="#996019",
        edgecolor="white",
        linewidth=0.6,
        zorder=3,
        label="Printed equinoxes, 1584 to 1588",
    )
    ax.scatter(
        list(TARGETS.values()),
        [-offsets[name] * 60 for name in TARGETS],
        s=70,
        marker="D",
        facecolor="none",
        edgecolor="#c8553d",
        linewidth=1.6,
        zorder=4,
        label="Tycho's reduction of an exact altitude",
    )
    ax.axhline(0, color="#89939f", lw=0.8)
    ax.set_xticks(range(0, 361, 45))
    ax.set_xlim(-8, 360)
    ax.set(
        xlabel="Longitude of the Sun (degrees)",
        ylabel="Tycho − DE441 (arcminutes)",
        title="Tycho's solar longitude against DE441",
    )
    ax.legend(frameon=False, loc="lower left", fontsize=9.5)
    ax.grid(axis="y", alpha=0.18)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(output / "solar-theory.png", dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tables-only", action="store_true", help="skip the figure")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    equinoxes, year, offsets, notes = write_tables(args.output)
    for name, value in notes.items():
        print(name, value)
    if args.tables_only:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 11, "axes.titleweight": "bold", "axes.labelcolor": "#263445"})
    plot(plt, args.output, equinoxes, year, offsets)


if __name__ == "__main__":
    main()
