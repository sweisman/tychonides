"""Cache JPL Horizons positions of Mars for the Kassel and Uraniborg comparison.

The study runs offline from mars-kassel-ephemeris.csv. This script rebuilds
that file from JPL Horizons (DE441): the astrometric geocentric right ascension
and declination of Mars in the ICRF and its distance from the Earth's center,
at the instant of every selected distance, and half an hour either side of
each Kassel reading.

    python examples/mars_kassel_ephemeris.py

Mars uses its system barycenter, as Horizons has no planet-center ephemeris
for it before 1600. The difference is far below an arcsecond as seen from
Earth.
"""

import csv

from mars_kassel import HERE, instants
from mars_parallax_ephemeris import fetch


def main():
    epochs = instants()
    with (HERE / "mars-kassel-ephemeris.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["jd_ut", "ra_degrees", "dec_degrees", "distance_au"])
        for jd, (ascension, declination, distance) in zip(epochs, fetch(epochs), strict=True):
            writer.writerow([jd, f"{ascension:.7f}", f"{declination:.7f}", f"{distance:.10f}"])
    print(f"cached {len(epochs)} positions")


if __name__ == "__main__":
    main()
