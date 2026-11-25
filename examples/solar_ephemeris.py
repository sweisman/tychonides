"""Cache JPL Horizons positions of the Sun for the solar-theory study.

The study runs offline from solar-theory-ephemeris.csv. This script rebuilds
that file from JPL Horizons (DE441): the apparent geocentric ecliptic longitude
and latitude of date of the Sun at every printed equinox instant, on five days
around each arrival of the Sun at the four places of the construction in 1584
to 1588, and every ten days through 1588.

    python examples/solar_ephemeris.py
"""

import csv

from mars_ephemeris import fetch
from solar_theory import HERE, instants


def main():
    epochs = instants()
    positions = fetch([float(jd) for jd in epochs], "10")
    with (HERE / "solar-theory-ephemeris.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["jd_ut", "longitude_degrees", "latitude_degrees"])
        for jd, (longitude, latitude) in zip(epochs, positions, strict=True):
            writer.writerow([jd, f"{longitude:.7f}", f"{latitude:.7f}"])
    print(f"cached {len(epochs)} positions")


if __name__ == "__main__":
    main()
