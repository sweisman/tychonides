"""Cache JPL Horizons positions of Mars for the 1587 parallax study.

The study runs offline from mars-parallax-ephemeris.csv. This script rebuilds
that file from JPL Horizons (DE441): the astrometric geocentric right ascension
and declination of Mars in the ICRF and its distance from the Earth's center,
at the instant of every selected distance and ten minutes either side.

    python examples/mars_parallax_ephemeris.py

Mars uses its system barycenter, as Horizons has no planet-center ephemeris
for it before 1600. The difference is far below an arcsecond as seen from
Earth.
"""

import csv
import urllib.parse
import urllib.request

from mars_ephemeris import API, CHUNK, SETTINGS, numbers
from mars_parallax_1587 import HERE, instants


def fetch(epochs):
    """Right ascension, declination, and distance of Mars for each UT Julian date."""
    found = []
    for start in range(0, len(epochs), CHUNK):
        part = epochs[start : start + CHUNK]
        query = {
            **SETTINGS,
            "COMMAND": "'4'",
            "QUANTITIES": "'1,20'",
            "TLIST": "'" + " ".join(part) + "'",
        }
        request = urllib.request.Request(
            API + "?" + urllib.parse.urlencode(query), headers={"User-Agent": "ephemeris-cache"}
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            text = response.read().decode("utf-8")
        if "$$SOE" not in text:
            raise RuntimeError("Horizons returned no table:\n" + text[-600:])
        table = [numbers(line) for line in text.split("$$SOE")[1].split("$$EOE")[0].splitlines()]
        table = [row for row in table if len(row) == 5]
        for jd in part:
            row = min(table, key=lambda item: abs(item[0] - float(jd)))
            if abs(row[0] - float(jd)) > 2e-6:
                raise RuntimeError("Horizons table lacks JD " + jd)
            found.append(row[1:4])
    return found


def main():
    epochs = instants()
    with (HERE / "mars-parallax-ephemeris.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["jd_ut", "ra_degrees", "dec_degrees", "distance_au"])
        for jd, (ascension, declination, distance) in zip(epochs, fetch(epochs), strict=True):
            writer.writerow([jd, f"{ascension:.7f}", f"{declination:.7f}", f"{distance:.10f}"])
    print(f"cached {len(epochs)} positions")


if __name__ == "__main__":
    main()
