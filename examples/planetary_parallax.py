"""Recompute the tables of the two planetary parallax pages.

Inputs, all beside this script:

- parallax-inputs.csv, parallax-venus-pairs.csv, and parallax-riccioli.csv,
  which parallax_select.py builds from the catalog;
- parallax-ephemeris.csv, which parallax_ephemeris.py caches from JPL Horizons;
- refraction-tables.csv, which holds Tycho's solar and fixed-star tables.

The script runs offline and needs NumPy.
"""

import argparse
import csv
from datetime import date
from fractions import Fraction
from pathlib import Path

import numpy as np
from mars_model import julian_day_number
from refraction_tables import ARCSECONDS, bennett
from refraction_tables import load as load_refraction

HERE = Path(__file__).parent
EARTH_RADIUS_KM = 6378.1366
AU_IN_EARTH_RADII = 149597870.7 / EARTH_RADIUS_KM
LATITUDE = np.deg2rad(55 + 54 / 60 + 28.3 / 3600)
UT_OFFSET_HOURS = (50 + 47.7 / 60) / 60
LONGOMONTANUS_DISTANCE = 850.0
# Nearest and farthest distances from Earth in millions of kilometers, NASA fact sheets.
NASA_DISTANCES = {
    "Mercury": (77.3, 221.9),
    "Venus": (38.2, 261.0),
    "Mars": (54.6, 401.4),
    "Jupiter": (588.5, 968.5),
    "Saturn": (1205.5, 1658.6),
}
OUTER = (  # Planet, Julian date, ephemeris key and Horizons target.
    ("Mars", date(1582, 12, 26), "mars-1582", "4"),
    ("Mars", date(1587, 3, 7), "mars-1587", "4"),
    ("Jupiter", date(1593, 6, 29), "jupiter-1593", "5"),
    ("Saturn", date(1599, 3, 25), "saturn-1599", "6"),
)
VENUS_1582 = (  # Ephemeris key, Julian date, and the input holding the printed clock.
    ("venus-1582-february", date(1582, 2, 26), "venus_1582_february_clock"),
    ("venus-1582-march-afternoon", date(1582, 3, 20), "venus_1582_march_afternoon_clock"),
    ("venus-1582-march-evening", date(1582, 3, 20), "venus_1582_march_evening_clock"),
)
MERCURY_DAYS = (24, 27, 28)
CLOCK_SHIFTS = (-15, 15)  # Minutes.


def altitude_parallax(altitude, distance):
    """Parallax in altitude, in arcseconds, at a distance in Earth radii."""
    return float(np.arcsin(np.cos(np.deg2rad(altitude)) / distance) * ARCSECONDS)


def declination_shift(declination, altitude, distance):
    """Topocentric minus geocentric declination in arcseconds on a spherical Earth."""
    delta, height = np.deg2rad(declination), np.deg2rad(altitude)
    shifted = (np.sin(delta) - np.sin(LATITUDE) / distance) / np.sqrt(
        1 + 1 / distance**2 - 2 * np.sin(height) / distance
    )
    return float((np.arcsin(shifted) - delta) * ARCSECONDS)


def projection(altitude, declination):
    """Share of a vertical change that falls in declination."""
    height, delta = np.deg2rad(altitude), np.deg2rad(declination)
    return float(
        (np.sin(LATITUDE) - np.sin(height) * np.sin(delta)) / (np.cos(height) * np.cos(delta))
    )


def tycho(rows, altitude):
    """Linear interpolation in one of Tycho's tables, and zero above its last entry."""
    arguments = [row["altitude"] for row in rows]
    if altitude > arguments[-1]:
        return 0.0
    return float(np.interp(altitude, arguments, [row["refraction"] for row in rows]))


def modern(altitude):
    return float(bennett(altitude))


def local_jd(day, hours):
    """UT Julian date of local mean hours after noon on a Julian-calendar date."""
    return julian_day_number(day) + (hours - UT_OFFSET_HOURS) / 24


def read(name):
    with (HERE / name).open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def load_inputs():
    return {row["key"]: float(Fraction(row["value"])) for row in read("parallax-inputs.csv")}


def load_pairs():
    """Each complete Venus pair by day: clocks in hours, angles in degrees."""
    pairs = {}
    for row in read("parallax-venus-pairs.csv"):
        pairs.setdefault(int(row["day"]), {})[row["measure"]] = float(
            Fraction(row["value_exact"]) / 3600
        )
    return pairs


def load_ephemeris():
    return {
        row["key"]: (float(row["declination_degrees"]), float(row["range_au"]))
        for row in read("parallax-ephemeris.csv")
    }


def instants(inputs, pairs):
    """Every ephemeris key, Horizons target, and UT Julian date the tables need."""
    wanted = [(key, target, float(julian_day_number(day))) for _, day, key, target in OUTER]
    wanted += [(key, "299", local_jd(day, inputs[clock])) for key, day, clock in VENUS_1582]
    for day, pair in pairs.items():
        for part in ("meridian", "evening"):
            epoch = local_jd(date(1590, 3, day), pair[f"{part}_clock"])
            wanted.append((f"venus-1590-{day:02d}-{part}", "299", epoch))
            for shift in CLOCK_SHIFTS:
                key = f"venus-1590-{day:02d}-{part}{shift:+d}"
                wanted.append((key, "299", epoch + shift / 1440))
    previous = local_jd(date(1590, 3, 3), inputs["venus_1590_march3_meridian_clock"])
    wanted.append(("venus-1590-03-meridian", "299", previous))
    for day in MERCURY_DAYS:
        epoch = local_jd(date(1589, 3, day), inputs[f"mercury_1589_march{day}_clock"])
        wanted.append((f"mercury-1589-{day}", "199", epoch))
    return wanted


def model_ranges():
    lines = [
        {
            "planet": row["planet"],
            "authority": "Riccioli" if row["authority"] == "Ourselves" else row["authority"],
            "far_arcseconds": f"{float(Fraction(row['far_arcseconds'])):.2f}",
            "near_arcseconds": f"{float(Fraction(row['near_arcseconds'])):.2f}",
        }
        for row in read("parallax-riccioli.csv")
    ]
    for planet, (near, far) in NASA_DISTANCES.items():
        angles = [np.arcsin(EARTH_RADIUS_KM / (value * 1e6)) * ARCSECONDS for value in (far, near)]
        lines.append(
            {
                "planet": planet,
                "authority": "Modern",
                "far_arcseconds": f"{angles[0]:.2f}",
                "near_arcseconds": f"{angles[1]:.2f}",
            }
        )
    return lines


def outer(inputs, ephemeris, sun, stars):
    inverted = np.cos(np.deg2rad(inputs["mars_1587_altitude"])) / np.sin(
        inputs["mars_1587_parallax"] / ARCSECONDS
    )
    reduced = inputs["jupiter_1593_mean_distance"] - inputs["jupiter_1593_distance_reduction"]
    geometry = (
        (inputs["mars_1582_altitude"], inputs["mars_1582_distance"]),
        (inputs["mars_1587_altitude"], float(inverted)),
        (inputs["jupiter_1593_altitude"], reduced),
        (inputs["saturn_1599_meridian_altitude"], inputs["saturn_1599_distance"]),
    )
    lines = []
    for (planet, day, key, _), (altitude, distance) in zip(OUTER, geometry, strict=True):
        now = ephemeris[key][1] * AU_IN_EARTH_RADII
        line = {
            "planet": planet,
            "julian_date": day.isoformat(),
            "altitude_degrees": f"{altitude:.4f}",
            "historical_distance_earth_radii": f"{distance:.1f}",
            "modern_range_au": f"{ephemeris[key][1]:.5f}",
            "historical_altitude_parallax_arcseconds": f"{altitude_parallax(altitude, distance):.1f}",
            "modern_altitude_parallax_arcseconds": f"{altitude_parallax(altitude, now):.1f}",
        }
        rules = (
            ("tycho_stellar", tycho(stars, altitude)),
            ("tycho_solar", tycho(sun, altitude)),
            ("bennett", modern(altitude)),
        )
        for name, refraction in rules:
            line[f"{name}_refraction_arcseconds"] = f"{refraction:.1f}"
        for basis, radius in (("historical", distance), ("modern", now)):
            for name, refraction in rules:
                net = altitude_parallax(altitude - refraction / 3600, radius) - refraction
                line[f"{basis}_net_{name}_arcseconds"] = f"{net:+.1f}"
        lines.append(line)
    return lines


def examples(inputs, ephemeris):
    cases = (
        ("Venus, 1582 February 26", "venus_1582_february", "february", "venus-1582-february"),
        ("Venus, 1582 March 20, afternoon", "venus_1582_march", "march_afternoon", "venus-1582-march-afternoon"),
        ("Venus, 1582 March 20, evening", "venus_1582_march", "march_evening", "venus-1582-march-evening"),
        ("Venus, Opera Omnia XII p. 463", "venus_p463", "", None),
        ("Venus, Opera Omnia XII p. 468", "venus_p468", "", None),
        ("Venus, 1610 December 12", "venus_1610", "", None),
    )  # fmt: skip
    lines = []
    for label, distance, reading, key in cases:
        stem = f"venus_1582_{reading}" if reading else distance
        altitude, radius = inputs[f"{stem}_altitude"], inputs[f"{distance}_distance"]
        line = {
            "example": label,
            "distance_earth_radii": f"{radius:g}",
            "altitude_degrees": f"{altitude:g}",
            "printed_altitude_parallax_arcseconds": f"{inputs[f'{stem}_parallax']:g}",
            "recomputed_arcseconds": f"{altitude_parallax(altitude, radius):.1f}",
            "modern_arcseconds": "",
        }
        if key:
            now = ephemeris[key][1] * AU_IN_EARTH_RADII
            line["modern_arcseconds"] = f"{altitude_parallax(altitude, now):.1f}"
        lines.append(line)
    return lines


def mercury(inputs, ephemeris, stars):
    """Mercury in March 1589 at the logged altitude and one degree either side."""
    declination = inputs["mercury_1589_declination"]
    printed, historical = inputs["mercury_1589_refraction"], inputs["mercury_1589_parallax"]
    lines = []
    for altitude in (inputs["mercury_1589_altitude"] + step for step in (-1, 0, 1)):
        share = projection(altitude, declination)
        line = {"altitude_degrees": f"{altitude:g}", "projection": f"{share:.4f}"}
        corrections = {}
        for day in MERCURY_DAYS:
            now, distance = ephemeris[f"mercury-1589-{day}"]
            corrections[day] = -declination_shift(now, altitude, distance * AU_IN_EARTH_RADII)
            line[f"modern_parallax_march{day}_arcseconds"] = f"{corrections[day]:+.1f}"
        rules = (
            ("printed", printed),
            ("tycho_stellar", tycho(stars, altitude) * share),
            ("bennett", modern(altitude) * share),
        )
        for name, refraction in rules:
            line[f"{name}_refraction_arcseconds"] = f"{refraction:.1f}"
        for basis, parallax in (("historical", historical), ("modern", corrections[24])):
            for name, refraction in rules:
                line[f"{basis}_net_{name}_arcseconds"] = f"{parallax - refraction:+.1f}"
        lines.append(line)
    return lines


def venus_pairs(inputs, pairs, ephemeris, sun, stars):
    """One row per complete pair, with every term in arcseconds."""
    rows = []
    for day, pair in sorted(pairs.items()):
        high, low = pair["meridian_altitude"], pair["evening_altitude"]
        first, second = (
            pair["meridian_declination_from_altitude"],
            pair["evening_declination_from_altitude"],
        )
        noon, dusk = (ephemeris[f"venus-1590-{day:02d}-{part}"] for part in ("meridian", "evening"))
        motion = (dusk[0] - noon[0]) * 3600
        shifted = [
            (
                ephemeris[f"venus-1590-{day:02d}-evening{shift:+d}"][0]
                - ephemeris[f"venus-1590-{day:02d}-meridian{shift:+d}"][0]
            )
            * 3600
            - motion
            for shift in CLOCK_SHIFTS
        ]
        mean = [(tycho(stars, height) + tycho(sun, height)) / 2 for height in (high, low)]
        rows.append(
            {
                "day": day,
                "interval_minutes": (pair["evening_clock"] - pair["meridian_clock"]) * 60,
                "change_from_altitudes": (second - first) * 3600,
                "change_by_armillae": (
                    pair["evening_declination_armillae"] - pair["meridian_declination_armillae"]
                )
                * 3600,
                "parallax_850": declination_shift(second, low, LONGOMONTANUS_DISTANCE)
                - declination_shift(first, high, LONGOMONTANUS_DISTANCE),
                "modern_motion": motion,
                "modern_parallax": declination_shift(dusk[0], low, dusk[1] * AU_IN_EARTH_RADII)
                - declination_shift(noon[0], high, noon[1] * AU_IN_EARTH_RADII),
                "modern_horizontal_parallax": ARCSECONDS / (noon[1] * AU_IN_EARTH_RADII),
                "refraction_tycho_stellar": tycho(stars, low) * projection(low, second)
                - tycho(stars, high) * projection(high, first),
                "refraction_longomontanus_mean": mean[1] * projection(low, second)
                - mean[0] * projection(high, first),
                "refraction_bennett": modern(low) * projection(low, second)
                - modern(high) * projection(high, first),
                "refraction_tangent_law": 58
                * (
                    projection(low, second) / np.tan(np.deg2rad(low))
                    - projection(high, first) / np.tan(np.deg2rad(high))
                ),
                "motion_change_clocks_minus_15_minutes": shifted[0],
                "motion_change_clocks_plus_15_minutes": shifted[1],
                "meridian_altitude_minus_ephemeris": (high - (90 - np.rad2deg(LATITUDE) + noon[0]))
                * 3600,
            }
        )
    for row in rows:
        row["altitude_minus_armillae_change"] = (
            row["change_from_altitudes"] - row["change_by_armillae"]
        )
    return rows


def scenarios(rows):
    """Residual after motion, parallax, and refraction, across all pairs."""
    lines = []
    for method in ("change_from_altitudes", "change_by_armillae"):
        for parallax in ("modern_parallax", "parallax_850"):
            for rule in ("tycho_stellar", "longomontanus_mean", "bennett"):
                left = np.array(
                    [
                        row[method]
                        - row["modern_motion"]
                        - row[parallax]
                        - row[f"refraction_{rule}"]
                        for row in rows
                    ]
                )
                lines.append(
                    {
                        "recorded_change": method.removeprefix("change_"),
                        "parallax": parallax.removesuffix("_parallax").removeprefix("parallax_"),
                        "refraction": rule,
                        "mean_arcseconds": f"{left.mean():+.1f}",
                        "standard_deviation_arcseconds": f"{left.std(ddof=1):.1f}",
                        "least_arcseconds": f"{left.min():+.1f}",
                        "greatest_arcseconds": f"{left.max():+.1f}",
                    }
                )
    return lines


def march_4(inputs, pairs, rows, ephemeris):
    """The March 4 pair under two motion estimates and two parallax scales."""
    pair, row = pairs[4], rows[0]
    high, low = pair["meridian_altitude"], pair["evening_altitude"]
    first, second = (
        pair["meridian_declination_from_altitude"],
        pair["evening_declination_from_altitude"],
    )
    rise = (high - inputs["venus_1590_march3_meridian_altitude"]) * 3600
    elapsed = 24 + pair["meridian_clock"] - inputs["venus_1590_march3_meridian_clock"]
    interpolated = rise / elapsed * (pair["evening_clock"] - pair["meridian_clock"])
    tangent = round(float(1 / np.sin(np.deg2rad(3 / 60)))) * np.cos(
        np.deg2rad(inputs["venus_1590_march3_sun_separation"])
    )
    historical = declination_shift(second, low, tangent) - declination_shift(first, high, tangent)
    lines = []
    for motion_name, motion in (
        ("log interpolation", interpolated),
        ("Horizons", row["modern_motion"]),
    ):
        for parallax_name, parallax in (
            ("historical", historical),
            ("modern", row["modern_parallax"]),
        ):
            line = {
                "motion_estimate": motion_name,
                "motion_arcseconds": f"{motion:+.1f}",
                "parallax_scale": parallax_name,
                "parallax_arcseconds": f"{parallax:+.1f}",
            }
            for rule in ("tycho_stellar", "longomontanus_mean", "bennett"):
                left = row["change_from_altitudes"] - motion - parallax - row[f"refraction_{rule}"]
                line[f"residual_{rule}_arcseconds"] = f"{left:+.1f}"
            lines.append(line)
    previous = ephemeris["venus-1590-03-meridian"][0]
    noon = ephemeris["venus-1590-04-meridian"][0]
    extras = {
        "March 3 to 4 change in meridian altitude (arcseconds)": rise,
        "March 3 to 4 interval between meridian clocks (hours)": elapsed,
        "March 4 motion by log interpolation (arcseconds)": interpolated,
        "March 3 to 4 change in ephemeris declination (arcseconds)": (noon - previous) * 3600,
        "Tangent-triangle distance of Venus (Earth radii)": tangent,
        "March 4 parallax shift at that distance (arcseconds)": historical,
    }
    return lines, extras


def checks(inputs, rows, extras):
    """Single numbers quoted in the text of the two pages."""
    sun = 1 / np.sin(np.deg2rad(3 / 60))
    scale = round(float(sun))
    side = np.sqrt(
        inputs["venus_p463_side_a"] ** 2
        + inputs["venus_p463_side_b"] ** 2
        - 2
        * inputs["venus_p463_side_a"]
        * inputs["venus_p463_side_b"]
        * np.cos(np.deg2rad(inputs["venus_p463_included_angle"]))
    )
    jupiter = inputs["jupiter_1593_mean_distance"] - inputs["jupiter_1593_distance_reduction"]
    found = {
        "Solar distance for a 3 arcminute horizontal parallax (Earth radii)": sun,
        "That distance, rounded, in millions of kilometers": scale * EARTH_RADIUS_KM / 1e6,
        "That distance in millions of miles": scale * EARTH_RADIUS_KM / 1.609344 / 1e6,
        "Horizontal parallax at one astronomical unit (arcseconds)": ARCSECONDS
        * np.arcsin(1 / AU_IN_EARTH_RADII),
        "Ratio of 3 arcminutes to that parallax": 180
        / (ARCSECONDS * np.arcsin(1 / AU_IN_EARTH_RADII)),
        "Jupiter 1593 horizontal parallax at the reduced distance (arcseconds)": ARCSECONDS
        * np.arcsin(1 / jupiter),
        "Jupiter 1593 September altitude parallax (arcseconds)": altitude_parallax(
            inputs["jupiter_1593_september_altitude"], inputs["jupiter_1593_september_distance"]
        ),
        "Saturn 1599 horizontal parallax (arcseconds)": ARCSECONDS
        * np.arcsin(1 / inputs["saturn_1599_distance"]),
        "Venus p. 463 triangle side by the cosine rule (Earth radii)": side,
        "Venus p. 463 altitude parallax at the printed distance (arcseconds)": altitude_parallax(
            inputs["venus_p463_altitude"], inputs["venus_p463_distance"]
        ),
        "Origanus Venus latitude by interpolation (arcseconds south)": (62 + 4 * 39 / 144) * 60,
        "Origanus Mercury latitude by interpolation (arcseconds north)": (30 - 47 * 39 / 144) * 60,
        **extras,
    }
    for name, column in (
        ("Method disagreement, altitude change minus armillae change", "altitude_minus_armillae_change"),
        ("Modern parallax shift", "modern_parallax"),
        ("Modern horizontal parallax of Venus", "modern_horizontal_parallax"),
        ("Parallax shift at 850 Earth radii", "parallax_850"),
        ("Tangent-law differential refraction", "refraction_tangent_law"),
        ("Motion change for clocks 15 minutes early", "motion_change_clocks_minus_15_minutes"),
        ("Motion change for clocks 15 minutes late", "motion_change_clocks_plus_15_minutes"),
        ("Meridian altitude minus ephemeris", "meridian_altitude_minus_ephemeris"),
    ):  # fmt: skip
        values = [row[column] for row in rows]
        found[f"{name}, least of the seven pairs (arcseconds)"] = min(values)
        found[f"{name}, greatest of the seven pairs (arcseconds)"] = max(values)
    return [{"quantity": name, "value": f"{value:.2f}"} for name, value in found.items()]


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_tables(output):
    inputs, pairs, ephemeris = load_inputs(), load_pairs(), load_ephemeris()
    if {key for key, _, _ in instants(inputs, pairs)} - set(ephemeris):
        raise RuntimeError("Cached ephemeris is incomplete; run parallax_ephemeris.py")
    tables = load_refraction()
    sun, stars = tables[("Tycho", "Sun", "")], tables[("Tycho", "fixed stars", "")]
    rows = venus_pairs(inputs, pairs, ephemeris, sun, stars)
    fourth, extras = march_4(inputs, pairs, rows, ephemeris)
    write_csv(output / "parallax-model-ranges.csv", model_ranges())
    write_csv(output / "parallax-outer-planets.csv", outer(inputs, ephemeris, sun, stars))
    write_csv(output / "parallax-examples.csv", examples(inputs, ephemeris))
    write_csv(output / "parallax-mercury.csv", mercury(inputs, ephemeris, stars))
    write_csv(
        output / "parallax-venus-pairs.csv",
        [
            {key: value if key == "day" else f"{value:+.1f}" for key, value in row.items()}
            for row in rows
        ],
    )
    write_csv(output / "parallax-venus-scenarios.csv", scenarios(rows))
    write_csv(output / "parallax-venus-march-4.csv", fourth)
    write_csv(output / "parallax-checks.csv", checks(inputs, rows, extras))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    write_tables(args.output)


if __name__ == "__main__":
    main()
