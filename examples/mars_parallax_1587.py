"""Test the parallax of Mars on Tycho's Mars-to-star distances of 1587.

On the nights of February 23 and March 10, 1587, Tycho measured the distance
of Mars from fixed stars with Mars low in the east, near the meridian, and low
in the west, in order to find its parallax. This script computes each distance
from the JPL DE441 ephemeris and modern star positions, and asks what
horizontal parallax of Mars the measured distances themselves imply.

    python examples/mars_parallax_1587.py --output docs/figures

The distances come from mars-parallax-readings.csv, which
mars_parallax_select.py builds from the catalog. The stars come from
mars-parallax-stars.csv and Mars from mars-parallax-ephemeris.csv, which
mars_parallax_ephemeris.py caches from JPL Horizons. Tycho's own parallax for
this opposition comes from parallax-inputs.csv.

Each computed distance is built in steps: the geocentric directions of Mars
and the star with aberration, the lift of both by refraction, and the
displacement of Mars by parallax as seen from Uraniborg. The printed clocks
are apparent solar time. The tables need NumPy. The figure needs Matplotlib.
"""

import argparse
import csv
from collections import defaultdict
from datetime import date
from fractions import Fraction
from itertools import pairwise
from pathlib import Path

import mars_model as mm
import numpy as np
from planetary_parallax import AU_IN_EARTH_RADII, LATITUDE, load_inputs
from refraction_tables import COLD, STANDARD, bennett, load
from solar_theory import J2000, approximate_longitude, equation_of_time, mean_elements

HERE = Path(__file__).parent
ARCSECONDS = 206264.80624709636
ABERRATION = 20.49552 / ARCSECONDS
STEP_MINUTES = 10  # Cached offset used for clock sensitivity.
PROBE = 60.0  # Horizontal parallax in arcseconds used to measure each parallax factor.
THIRD_STAR = "61941"  # The star whose morning distances disagree with its evening ones.
SESSIONS = ((10, "evening"), (15, "near the meridian"), (99, "toward setting"))
READING_FIELDS = [
    "id",
    "julian_date",
    "session",
    "star",
    "clock_expression",
    "jd_ut",
    "observed_arcmin",
    "geocentric_arcmin",
    "refraction_arcsec",
    "parallax_factor",
    "modern_parallax_arcsec",
    "tycho_parallax_arcsec",
    "observed_minus_modern_arcsec",
    "observed_minus_tycho_arcsec",
    "recorded_altitude_degrees",
    "computed_altitude_degrees",
    "star_altitude_degrees",
]
PAIR_FIELDS = [
    "julian_date",
    "star",
    "first_session",
    "second_session",
    "readings",
    "parallax_factor_change",
    "observed_change_arcsec",
    "motion_arcsec",
    "refraction_arcsec",
    "modern_parallax_arcsec",
    "tycho_parallax_arcsec",
    "observed_minus_modern_arcsec",
    "observed_minus_tycho_arcsec",
    "implied_parallax_arcsec",
]
SUMMARY_FIELDS = [
    "case",
    "readings",
    "groups",
    "implied_parallax_arcsec",
    "standard_error_arcsec",
    "rms_modern_arcsec",
    "rms_tycho_arcsec",
]
CLOCK_FIELDS = [
    "julian_date",
    "session",
    "altitudes",
    "recorded_minus_computed_arcmin",
    "clock_offset_minutes",
]


def read(name):
    with (HERE / name).open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def instant(row):
    """UT Julian date of a reading whose clock shows apparent time at Uraniborg."""
    hours = (12 if row["clock_origin"] == "noon" else 24) + float(
        Fraction(row["clock_seconds"])
    ) / 3600
    mean = mm.jd_ut(date.fromisoformat(row["julian_date"]), hours)
    return mean - equation_of_time(mean)


def session(row):
    hours = (0 if row["clock_origin"] == "noon" else 12) + float(
        Fraction(row["clock_seconds"])
    ) / 3600
    return next(name for limit, name in SESSIONS if hours < limit)


def instants():
    """Every UT Julian date the study needs from the ephemeris, as cache keys."""
    wanted = set()
    for row in read("mars-parallax-readings.csv"):
        for minutes in (-STEP_MINUTES, 0, STEP_MINUTES):
            wanted.add(f"{instant(row) + minutes / 1440:.6f}")
    return sorted(wanted)


def unit(ascension, declination):
    return np.array(
        [
            np.cos(declination) * np.cos(ascension),
            np.cos(declination) * np.sin(ascension),
            np.sin(declination),
        ]
    )


def precession(jd):
    """Matrix from the J2000 equator to the mean equator and equinox of date (IAU 1976)."""
    t = (jd - J2000) / 36525
    zeta = (2306.2181 * t + 0.30188 * t**2 + 0.017998 * t**3) / ARCSECONDS
    z = (2306.2181 * t + 1.09468 * t**2 + 0.018203 * t**3) / ARCSECONDS
    theta = (2004.3109 * t - 0.42665 * t**2 - 0.041833 * t**3) / ARCSECONDS
    cz, sz, ct, st, cx, sx = (
        np.cos(z),
        np.sin(z),
        np.cos(theta),
        np.sin(theta),
        np.cos(zeta),
        np.sin(zeta),
    )
    return np.array(
        [
            [cz * ct * cx - sz * sx, -cz * ct * sx - sz * cx, -cz * st],
            [sz * ct * cx + cz * sx, -sz * ct * sx + cz * cx, -sz * st],
            [st * cx, -st * sx, ct],
        ]
    )


def star_direction(star, jd):
    """ICRS direction of a star at a date, from its J2000 position and proper motion."""
    ascension, declination = (
        np.deg2rad(float(star["ra_degrees"])),
        np.deg2rad(float(star["dec_degrees"])),
    )
    years = (jd - J2000) / 365.25
    east = np.array([-np.sin(ascension), np.cos(ascension), 0.0])
    north = np.array(
        [
            -np.sin(declination) * np.cos(ascension),
            -np.sin(declination) * np.sin(ascension),
            np.cos(declination),
        ]
    )
    moved = unit(ascension, declination) + years / (1000 * ARCSECONDS) * (
        float(star["pm_ra_mas_per_year"]) * east + float(star["pm_dec_mas_per_year"]) * north
    )
    return moved / np.linalg.norm(moved)


def of_date(direction, jd):
    """Direction on the mean equator of date, displaced by annual aberration."""
    _, _, obliquity, _ = mean_elements(jd)
    sun, obliquity = np.deg2rad(approximate_longitude(jd)), np.deg2rad(obliquity)
    velocity = ABERRATION * np.array(
        [np.sin(sun), -np.cos(sun) * np.cos(obliquity), -np.cos(sun) * np.sin(obliquity)]
    )
    seen = precession(jd) @ direction + velocity
    return seen / np.linalg.norm(seen)


def sidereal(jd):
    """Local mean sidereal time at Uraniborg, in radians."""
    t = (jd - J2000) / 36525
    greenwich = 280.46061837 + 360.98564736629 * (jd - J2000) + 0.000387933 * t**2
    return np.deg2rad((greenwich + mm.SITE_EAST_LONGITUDE) % 360)


def zenith(jd):
    """Direction of the zenith of Uraniborg on the equator of date."""
    return unit(sidereal(jd), LATITUDE)


def altitude(direction, jd):
    return float(np.rad2deg(np.arcsin(direction @ zenith(jd))))


def tycho_table():
    """Tycho's refractions for the fixed stars, which end at an altitude of 20 degrees."""
    rows = load()[("Tycho", "fixed stars", "")]
    heights, values = [row["altitude"] for row in rows], [row["refraction"] for row in rows]
    return lambda seen: float(np.interp(seen, heights, values, right=0.0))


def lifted(direction, jd, air):
    """Direction after refraction raises it toward the zenith.

    `air` is a pressure and temperature for the modern formula, or a function
    that gives the refraction in arcseconds at an apparent altitude in degrees.
    """
    bend = air if callable(air) else lambda seen: float(bennett(seen, *air))
    up = zenith(jd)
    true = np.arcsin(direction @ up)
    seen = true
    for _ in range(4):
        seen = true + bend(np.rad2deg(seen)) / ARCSECONDS
    level = direction - np.sin(true) * up
    return np.cos(seen) * level / np.linalg.norm(level) + np.sin(seen) * up


def angle(first, second):
    """Angle between two directions, in arcseconds."""
    return float(np.arctan2(np.linalg.norm(np.cross(first, second)), first @ second) * ARCSECONDS)


class Sky:
    """Computed distances of Mars from the stars at cached instants."""

    def __init__(self):
        self.mars = {
            row["jd_ut"]: (
                unit(np.deg2rad(float(row["ra_degrees"])), np.deg2rad(float(row["dec_degrees"]))),
                float(row["distance_au"]) * AU_IN_EARTH_RADII,
            )
            for row in read("mars-parallax-ephemeris.csv")
        }
        self.stars = {row["hip"]: row for row in read("mars-parallax-stars.csv")}
        inputs = load_inputs()
        self.tycho_parallax = float(
            inputs["mars_1587_parallax"] / np.cos(np.deg2rad(inputs["mars_1587_altitude"]))
        )

    def distance(self, jd, hip, parallax=0.0, air=STANDARD):
        """Distance in arcseconds, for a horizontal parallax of Mars in arcseconds.

        `air` is None for no refraction. A parallax of None takes the DE441 distance.
        """
        planet, star = (
            of_date(self.mars[f"{jd:.6f}"][0], jd),
            of_date(star_direction(self.stars[hip], jd), jd),
        )
        if parallax is None:
            parallax = self.modern_parallax(jd)
        if parallax:
            planet = planet / np.sin(parallax / ARCSECONDS) - zenith(jd)
            planet /= np.linalg.norm(planet)
        if air:
            planet, star = lifted(planet, jd, air), lifted(star, jd, air)
        return angle(planet, star)

    def modern_parallax(self, jd):
        return float(np.arcsin(1 / self.mars[f"{jd:.6f}"][1]) * ARCSECONDS)

    def altitudes(self, jd, hip, air=STANDARD):
        """Apparent altitudes of Mars, with its modern parallax, and of the star, in degrees."""
        planet, radii = self.mars[f"{jd:.6f}"]
        planet = of_date(planet, jd) * radii - zenith(jd)
        planet /= np.linalg.norm(planet)
        star = of_date(star_direction(self.stars[hip], jd), jd)
        return altitude(lifted(planet, jd, air), jd), altitude(lifted(star, jd, air), jd)


def evaluate(sky, rows, shift=None, air=STANDARD):
    """One record per reading. `shift` gives minutes added to the clock, by session."""
    records = []
    for row in rows:
        key = (row["julian_date"], session(row))
        jd = instant(row) + (shift or {}).get(key, 0.0) / 1440
        hip = row["hip"]
        observed = float(Fraction(row["separation_arcseconds_exact"]))
        geocentric = sky.distance(jd, hip, air=None)
        refracted = sky.distance(jd, hip, air=air)
        factor = (sky.distance(jd, hip, PROBE, air) - refracted) / PROBE
        modern = sky.modern_parallax(jd) * factor
        tycho = sky.tycho_parallax * factor
        mars_altitude, star_altitude = sky.altitudes(jd, hip, air)
        recorded = row["altitude_arcseconds_exact"]
        records.append(
            {
                "row": row,
                "key": key,
                "group": (row["julian_date"], hip),
                "jd": jd,
                "observed": observed,
                "geocentric": geocentric,
                "refraction": refracted - geocentric,
                "factor": factor,
                "modern": modern,
                "tycho": tycho,
                "left": observed - refracted,
                "recorded_altitude": float(Fraction(recorded)) / 3600 if recorded else None,
                "mars_altitude": mars_altitude,
                "star_altitude": star_altitude,
            }
        )
    return records


def grouped(records):
    """Readings of each star on each night, which share one free offset."""
    groups = defaultdict(list)
    for record in records:
        groups[record["group"]].append(record)
    return groups


def implied(records):
    """Horizontal parallax the distances imply, its standard error, and the number of offsets."""
    groups = grouped(records)
    left, factor = [], []
    for members in groups.values():
        left += list(np.array([m["left"] for m in members]) - np.mean([m["left"] for m in members]))
        factor += list(
            np.array([m["factor"] for m in members]) - np.mean([m["factor"] for m in members])
        )
    left, factor = np.array(left), np.array(factor)
    parallax = float(left @ factor / (factor @ factor))
    freedom = len(left) - len(groups) - 1
    spread = float(np.sum((left - parallax * factor) ** 2) / freedom)
    return parallax, float(np.sqrt(spread / (factor @ factor))), len(groups)


def rms(records, name):
    """Scatter about each offset after removing one parallax term."""
    groups = [
        np.array([member["left"] - member[name] for member in members])
        for members in grouped(records).values()
    ]
    centered = np.concatenate([values - values.mean() for values in groups])
    return float(np.sqrt(np.mean(centered**2)))


def clock_check(sky, records):
    """Recorded minus computed altitude of Mars by session, and the clock offset it implies."""
    sessions = defaultdict(list)
    for record in records:
        if record["recorded_altitude"] is not None:
            later = sky.altitudes(record["jd"] + STEP_MINUTES / 1440, record["row"]["hip"])[0]
            rate = (later - record["mars_altitude"]) / STEP_MINUTES
            gap = record["recorded_altitude"] - record["mars_altitude"]
            sessions[record["key"]].append((gap, gap / rate))
    rows, offsets = [], {}
    for key, found in sessions.items():
        gaps, minutes = (np.array(column) for column in zip(*found, strict=True))
        offsets[key] = float(np.mean(minutes))
        rows.append(
            {
                "julian_date": key[0],
                "session": key[1],
                "altitudes": len(found),
                "recorded_minus_computed_arcmin": f"{np.mean(gaps) * 60:.1f}",
                "clock_offset_minutes": f"{np.mean(minutes):.1f}",
            }
        )
    return rows, offsets


def pairs(records):
    """Change of each star's mean distance between two sessions of a night."""
    sessions = defaultdict(list)
    for record in records:
        sessions[(*record["group"], record["key"][1])].append(record)
    order = [name for _, name in SESSIONS]
    rows = []
    for night, star in sorted({key[:2] for key in sessions}):
        held = [name for name in order if (night, star, name) in sessions]
        for first, second in pairwise(held):
            before, after = sessions[(night, star, first)], sessions[(night, star, second)]

            def change(name, before=before, after=after):
                return np.mean([r[name] for r in after]) - np.mean([r[name] for r in before])

            observed, motion, refraction = (
                change("observed"),
                change("geocentric"),
                change("refraction"),
            )
            modern, tycho, factor = change("modern"), change("tycho"), change("factor")
            rows.append(
                {
                    "julian_date": night,
                    "star": before[0]["row"]["star"],
                    "first_session": first,
                    "second_session": second,
                    "readings": f"{len(before)} and {len(after)}",
                    "parallax_factor_change": f"{factor:.2f}",
                    "observed_change_arcsec": f"{observed:.0f}",
                    "motion_arcsec": f"{motion:.0f}",
                    "refraction_arcsec": f"{refraction:.0f}",
                    "modern_parallax_arcsec": f"{modern:.0f}",
                    "tycho_parallax_arcsec": f"{tycho:.0f}",
                    "observed_minus_modern_arcsec": f"{observed - motion - refraction - modern:.0f}",
                    "observed_minus_tycho_arcsec": f"{observed - motion - refraction - tycho:.0f}",
                    "implied_parallax_arcsec": f"{(observed - motion - refraction) / factor:.0f}",
                }
            )
    return rows


def summary_row(case, records):
    parallax, error, groups = implied(records)
    return {
        "case": case,
        "readings": len(records),
        "groups": groups,
        "implied_parallax_arcsec": f"{parallax:.0f}",
        "standard_error_arcsec": f"{error:.0f}",
        "rms_modern_arcsec": f"{rms(records, 'modern'):.0f}",
        "rms_tycho_arcsec": f"{rms(records, 'tycho'):.0f}",
    }


def study():
    sky = Sky()
    rows = read("mars-parallax-readings.csv")
    records = evaluate(sky, rows)
    clocks, offsets = clock_check(sky, records)
    keys = {record["key"] for record in records}
    summary = [summary_row("both nights", records)]
    for night in sorted({record["key"][0] for record in records}):
        summary.append(
            summary_row(night, [record for record in records if record["key"][0] == night])
        )
    summary.append(
        summary_row(
            "without the third star in the wing of Virgo",
            [record for record in records if record["row"]["hip"] != THIRD_STAR],
        )
    )
    for minutes in (-STEP_MINUTES, STEP_MINUTES):
        shifted = evaluate(sky, rows, dict.fromkeys(keys, minutes))
        summary.append(summary_row(f"every clock {minutes:+d} minutes", shifted))
    late = {key: STEP_MINUTES for key in keys if key[1] == "toward setting"}
    summary.append(
        summary_row(f"clocks toward setting {STEP_MINUTES:+d} minutes", evaluate(sky, rows, late))
    )
    summary.append(summary_row("cold air", evaluate(sky, rows, air=COLD)))
    summary.append(
        summary_row("refractions from the log's table", evaluate(sky, rows, air=tycho_table()))
    )
    changes = pairs(records)
    each = np.array([float(row["implied_parallax_arcsec"]) for row in changes])
    summary.append(
        {
            "case": "mean of the pairs",
            "groups": len(each),
            "implied_parallax_arcsec": f"{each.mean():.0f}",
            "standard_error_arcsec": f"{each.std(ddof=1) / np.sqrt(len(each)):.0f}",
        }
    )
    readings = [
        {
            "id": record["row"]["id"],
            "julian_date": record["key"][0],
            "session": record["key"][1],
            "star": record["row"]["star"],
            "clock_expression": record["row"]["clock_expression"],
            "jd_ut": f"{record['jd']:.6f}",
            "observed_arcmin": f"{record['observed'] / 60:.2f}",
            "geocentric_arcmin": f"{record['geocentric'] / 60:.2f}",
            "refraction_arcsec": f"{record['refraction']:.0f}",
            "parallax_factor": f"{record['factor']:.3f}",
            "modern_parallax_arcsec": f"{record['modern']:.0f}",
            "tycho_parallax_arcsec": f"{record['tycho']:.0f}",
            "observed_minus_modern_arcsec": f"{record['left'] - record['modern']:.0f}",
            "observed_minus_tycho_arcsec": f"{record['left'] - record['tycho']:.0f}",
            "recorded_altitude_degrees": ""
            if record["recorded_altitude"] is None
            else f"{record['recorded_altitude']:.3f}",
            "computed_altitude_degrees": f"{record['mars_altitude']:.3f}",
            "star_altitude_degrees": f"{record['star_altitude']:.3f}",
        }
        for record in records
    ]
    notes = {
        "tycho_horizontal_parallax_arcsec": round(sky.tycho_parallax, 1),
        "modern_horizontal_parallax_arcsec": sorted(
            {round(sky.modern_parallax(record["jd"]), 1) for record in records}
        ),
        "clock_offsets_minutes": {key: round(value, 1) for key, value in offsets.items()},
    }
    return readings, changes, summary, clocks, records, notes


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_tables(output):
    """Write every numerical output. Needs NumPy only."""
    readings, changes, summary, clocks, records, notes = study()
    write_csv(output / "mars-parallax-1587-readings.csv", READING_FIELDS, readings)
    write_csv(output / "mars-parallax-1587-pairs.csv", PAIR_FIELDS, changes)
    write_csv(output / "mars-parallax-1587-summary.csv", SUMMARY_FIELDS, summary)
    write_csv(output / "mars-parallax-1587-clocks.csv", CLOCK_FIELDS, clocks)
    return records, notes


def plot(plt, output, records, tycho_parallax, modern_parallax):
    """What is left of each distance against its parallax factor, by night and star."""
    colors = ["#00699a", "#996019", "#7a5195", "#5c6670", "#12a089", "#c8553d"]
    markers = {"1587-02-23": "o", "1587-03-10": "s"}
    groups = grouped(records)
    names = {record["group"][1]: record["row"]["star"] for record in records}
    stars = sorted(names, key=names.get)
    fig, ax = plt.subplots(figsize=(9.5, 5), layout="constrained")
    for (night, star), members in sorted(groups.items()):
        factor = np.array([m["factor"] for m in members])
        left = np.array([m["left"] for m in members])
        ax.scatter(
            factor - factor.mean(),
            (left - left.mean()) / 60,
            s=34,
            color=colors[stars.index(star)],
            marker=markers[night],
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
    span = np.array(ax.get_xlim())
    ax.plot(span, span * tycho_parallax / 60, color="#263445", lw=1.4, ls="--")
    ax.plot(span, span * modern_parallax / 60, color="#263445", lw=1.4)
    ax.text(
        0.36,
        0.44 * tycho_parallax / 60,
        f"parallax in the log, {tycho_parallax:.0f}″",
        ha="right",
        va="center",
        fontsize=9.5,
    )
    ax.text(
        0.6,
        0.6 * modern_parallax / 60 + 0.3,
        f"parallax from DE441, {modern_parallax:.0f}″",
        ha="center",
        va="center",
        fontsize=9.5,
    )
    ax.set_xlim(span)
    handles = [
        plt.Line2D(
            [], [], ls="", marker="o", color=colors[index], mec="white", ms=7, label=names[star]
        )
        for index, star in enumerate(stars)
    ]
    handles += [
        plt.Line2D([], [], ls="", marker=mark, color="#89939f", mec="white", ms=7, label=night)
        for night, mark in markers.items()
    ]
    ax.legend(
        handles=handles,
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.6, 0.02),
        fontsize=9,
        ncols=2,
    )
    ax.axhline(0, color="#89939f", lw=0.8)
    ax.set(
        xlabel="Parallax factor of the distance, less its mean for the night and star",
        ylabel="Measured − computed distance (arcminutes)",
        title="Mars-to-star distances of 1587 against the parallax they would show",
    )
    ax.grid(axis="y", alpha=0.18)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(output / "mars-parallax-1587.png", dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tables-only", action="store_true", help="skip the figure")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    records, notes = write_tables(args.output)
    for name, value in notes.items():
        print(name, value)
    if args.tables_only:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 11, "axes.titleweight": "bold", "axes.labelcolor": "#263445"})
    plot(
        plt,
        args.output,
        records,
        notes["tycho_horizontal_parallax_arcsec"],
        float(np.mean(notes["modern_horizontal_parallax_arcsec"])),
    )


if __name__ == "__main__":
    main()
