"""Cache JPL Horizons positions for the printed-predictions study.

The study runs offline from printed-predictions-ephemeris.csv. This script
rebuilds that file from JPL Horizons (DE441): the apparent geocentric ecliptic
longitude and latitude of date for the Moon and each planet, at local noon and
the following midnight of every prediction date and at the instant of every
log value on those dates.

    python examples/predictions_ephemeris.py

Mars, Jupiter, and Saturn use their system barycenters, as Horizons has no
planet-center ephemeris for them before 1600. The difference is far below an
arcsecond as seen from Earth.
"""

import csv

from mars_ephemeris import fetch
from printed_predictions import HERE, TARGETS, instants


def main():
    count = 0
    with (HERE / "printed-predictions-ephemeris.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["body", "jd_ut", "longitude_degrees", "latitude_degrees"])
        for body, epochs in instants().items():
            positions = fetch([float(jd) for jd in epochs], TARGETS[body])
            for jd, (longitude, latitude) in zip(epochs, positions, strict=True):
                writer.writerow([body, jd, f"{longitude:.7f}", f"{latitude:.7f}"])
            count += len(epochs)
    print(f"cached {count} positions")


if __name__ == "__main__":
    main()
