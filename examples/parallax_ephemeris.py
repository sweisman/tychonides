"""Cache JPL Horizons declinations and distances for the parallax tables.

The parallax script runs offline from parallax-ephemeris.csv. This script
rebuilds that file from JPL Horizons (DE441): the apparent geocentric
declination and the distance from Earth's center at each UT instant the tables
use. Mercury and Venus are the planet centers. Mars, Jupiter, and Saturn are
the system barycenters, since Horizons has no planet-center ephemeris for them
before 1600.

    python examples/parallax_ephemeris.py
"""

import csv
import urllib.parse
import urllib.request

from mars_ephemeris import API, CHUNK, SETTINGS, numbers
from planetary_parallax import HERE, instants, load_inputs, load_pairs


def fetch(target, epochs):
    """Declination in degrees and range in au for each UT Julian date, in the order given."""
    found = []
    for start in range(0, len(epochs), CHUNK):
        part = epochs[start : start + CHUNK]
        query = {
            **SETTINGS,
            "COMMAND": f"'{target}'",
            "QUANTITIES": "'2,20'",
            "TLIST": "'" + " ".join(f"{jd:.6f}" for jd in part) + "'",
        }
        request = urllib.request.Request(
            API + "?" + urllib.parse.urlencode(query), headers={"User-Agent": "ephemeris-cache"}
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            text = response.read().decode("utf-8")
        if "$$SOE" not in text:
            raise RuntimeError("Horizons returned no table:\n" + text[-600:])
        table = [numbers(line) for line in text.split("$$SOE")[1].split("$$EOE")[0].splitlines()]
        table = [row for row in table if len(row) >= 5]
        for jd in part:
            row = min(table, key=lambda item: abs(item[0] - jd))
            if abs(row[0] - jd) > 2e-6:
                raise RuntimeError(f"Horizons table lacks JD {jd:.6f}")
            found.append((row[-3], row[-2]))
    return found


def main():
    wanted = instants(load_inputs(), load_pairs())
    lines = []
    for target in sorted({item[1] for item in wanted}):
        part = [item for item in wanted if item[1] == target]
        values = fetch(target, [item[2] for item in part])
        for (key, _, jd), (declination, distance) in zip(part, values, strict=True):
            lines.append([key, target, f"{jd:.6f}", f"{declination:.7f}", f"{distance:.10f}"])
    order = {item[0]: index for index, item in enumerate(wanted)}
    lines.sort(key=lambda line: order[line[0]])
    with (HERE / "parallax-ephemeris.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["key", "target", "jd_ut", "declination_degrees", "range_au"])
        writer.writerows(lines)
    print(f"cached {len(lines)} positions")


if __name__ == "__main__":
    main()
