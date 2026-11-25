"""Reproduce Longomontanus's table of Mars oppositions from JPL DE441.

Each row of the table gives the instant at which Mars stood opposite the Sun
and the longitude of Mars at that instant. This script finds the same two
things from the ephemeris: the instant at which the apparent geocentric
longitude of Mars is 180 degrees from that of the Sun, and the longitude of
Mars then.

    python examples/mars_opposition_table.py --output docs/figures

It runs offline from mars-opposition-table-ephemeris.csv. To rebuild that file
from JPL Horizons, add --fetch. The positions are cached every six hours for
two days on each side of the tabulated instant, and the opposition is found by
linear interpolation between the two cached instants that bracket it.
"""

import argparse
import csv
from pathlib import Path

import mars_model as mm
import numpy as np

HERE = Path(__file__).parent
CACHE = HERE / "mars-opposition-table-ephemeris.csv"
STEPS = np.arange(-8, 9) * 0.25  # Days from the tabulated instant.
FIELDS = [
    "opposition",
    "tabulated_date",
    "tabulated_hours_from_noon",
    "date_basis",
    "tabulated_longitude_degrees",
    "de441_opposition_offset_hours",
    "de441_longitude_at_its_opposition_degrees",
    "tabulated_minus_de441_longitude_arcmin",
    "de441_longitude_at_tabulated_instant_degrees",
    "tabulated_minus_de441_longitude_at_tabulated_instant_arcmin",
    "implied_sun_minus_de441_sun_arcmin",
    "solar_equation_excess_arcmin",
]
EARTH_ECCENTRICITY_1600 = 0.016877  # Meeus, Astronomical Algorithms, eq. 25.4.
# The eccentric solar circle of the Astronomia Danica gives a largest equation of
# arcsin(1/28). An ellipse of eccentricity e gives 2e radians, to first order.
EQUATION_EXCESS = np.rad2deg(np.arcsin(mm.SUN_ECCENTRICITY) - 2 * EARTH_ECCENTRICITY_1600)


def instants():
    """The UT Julian dates cached for each row of the table."""
    return {
        number: [f"{item.jd + step:.6f}" for step in STEPS]
        for number, item in mm.load_oppositions().items()
    }


def fetch():
    from mars_ephemeris import fetch as horizons

    with CACHE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["opposition", "jd_ut", "mars_longitude_degrees", "sun_longitude_degrees"])
        for number, epochs in instants().items():
            times = [float(jd) for jd in epochs]
            mars, sun = horizons(times, "4"), horizons(times, "10")
            for jd, (planet, _), (star, _) in zip(epochs, mars, sun, strict=True):
                writer.writerow([number, jd, f"{planet:.7f}", f"{star:.7f}"])


def load_cache():
    cached = {}
    with CACHE.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            cached.setdefault(row["opposition"], []).append(
                (
                    float(row["jd_ut"]),
                    float(row["mars_longitude_degrees"]),
                    float(row["sun_longitude_degrees"]),
                )
            )
    return cached


def reproduce():
    """One row per tabulated opposition, set beside the ephemeris."""
    cached, table = load_cache(), []
    for number, item in mm.load_oppositions().items():
        times, mars, sun = (np.array(column) for column in zip(*cached[number], strict=True))
        mars = item.longitude + mm.wrapped(mars - item.longitude)  # Continuous through 0 degrees.
        elongation = mm.wrapped(mars - sun - 180)
        middle = len(STEPS) // 2
        # A row asserts that the Sun stood opposite its longitude at its instant.
        implied_sun = mm.wrapped(item.longitude + 180 - sun[middle])
        line = {
            "opposition": number,
            "tabulated_date": item.day.isoformat(),
            "tabulated_hours_from_noon": f"{item.hours_from_noon:.2f}",
            "date_basis": item.date_basis,
            "tabulated_longitude_degrees": f"{item.longitude:.4f}",
            "de441_longitude_at_tabulated_instant_degrees": f"{mars[middle] % 360:.4f}",
            "tabulated_minus_de441_longitude_at_tabulated_instant_arcmin": (
                f"{(item.longitude - mars[middle]) * 60:.1f}"
            ),
            "implied_sun_minus_de441_sun_arcmin": f"{implied_sun * 60:.1f}",
            # What a solar equation of center too large by the excess would give.
            "solar_equation_excess_arcmin": (
                f"{-EQUATION_EXCESS * np.sin(np.deg2rad(sun[middle]) - mm.SUN_APOGEE) * 60:.1f}"
            ),
        }
        crossing = np.flatnonzero(np.sign(elongation[:-1]) != np.sign(elongation[1:]))
        if len(crossing) == 1:
            index = crossing[0]
            share = elongation[index] / (elongation[index] - elongation[index + 1])
            when = times[index] + share * (times[index + 1] - times[index])
            longitude = mars[index] + share * (mars[index + 1] - mars[index])
            line |= {
                "de441_opposition_offset_hours": f"{(when - item.jd) * 24:.2f}",
                "de441_longitude_at_its_opposition_degrees": f"{longitude % 360:.4f}",
                "tabulated_minus_de441_longitude_arcmin": (
                    f"{mm.wrapped(item.longitude - longitude) * 60:.1f}"
                ),
            }
        table.append(line)
    return table


def write_tables(output):
    with (output / "mars-opposition-table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(reproduce())


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fetch", action="store_true", help="rebuild the cache from JPL Horizons")
    args = parser.parse_args()
    if args.fetch:
        fetch()
    args.output.mkdir(parents=True, exist_ok=True)
    write_tables(args.output)


if __name__ == "__main__":
    main()
