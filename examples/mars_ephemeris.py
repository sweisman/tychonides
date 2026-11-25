"""Cache JPL Horizons positions for the selected Mars rows.

The studies run offline from mars-ephemeris.csv. This script rebuilds that
file from JPL Horizons (DE441): the apparent geocentric ecliptic longitude and
latitude of date for the Mars system barycenter, at the UT instant assigned to
each selected row and to each tabulated opposition.

    python examples/mars_ephemeris.py

Horizons has no Mars-center ephemeris before 1600. The barycenter differs from
the planet's center by far less than an arcsecond as seen from Earth.
"""

import csv
import urllib.parse
import urllib.request

from mars_model import HERE, load_observations, load_oppositions

API = "https://ssd.jpl.nasa.gov/api/horizons.api"
SETTINGS = {
    "format": "text",
    "OBJ_DATA": "'NO'",
    "MAKE_EPHEM": "'YES'",
    "EPHEM_TYPE": "'OBSERVER'",
    "COMMAND": "'4'",
    "CENTER": "'500@399'",
    "QUANTITIES": "'31'",
    "ANG_FORMAT": "'DEG'",
    "CSV_FORMAT": "'YES'",
    "CAL_FORMAT": "'JD'",
    "TIME_TYPE": "'UT'",
    "TLIST_TYPE": "'JD'",
    "EXTRA_PREC": "'YES'",
}
CHUNK = 40


def numbers(line):
    values = []
    for field in line.split(","):
        try:
            values.append(float(field))
        except ValueError:
            continue
    return values


def fetch(epochs, target="4"):
    """Longitude and latitude of a Horizons target for each UT Julian date, in the order given."""
    found = []
    for start in range(0, len(epochs), CHUNK):
        part = epochs[start : start + CHUNK]
        query = {
            **SETTINGS,
            "COMMAND": f"'{target}'",
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
        table = [row for row in table if len(row) >= 3]
        for jd in part:
            row = min(table, key=lambda item: abs(item[0] - jd))
            if abs(row[0] - jd) > 2e-6:
                raise RuntimeError(f"Horizons table lacks JD {jd:.6f}")
            found.append((row[-2], row[-1]))
    return found


def main():
    oppositions = load_oppositions()
    wanted = [(f"opposition-{number}", item.jd) for number, item in oppositions.items()]
    for number in oppositions:
        wanted.extend((row["longitude_id"], row["jd_ut"]) for row in load_observations(number))
    positions = fetch([jd for _, jd in wanted])
    with (HERE / "mars-ephemeris.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["key", "jd_ut", "longitude_degrees", "latitude_degrees"])
        for (key, jd), (longitude, latitude) in zip(wanted, positions, strict=True):
            writer.writerow([key, f"{jd:.6f}", f"{longitude:.7f}", f"{latitude:.7f}"])
    print(f"cached {len(wanted)} positions")


if __name__ == "__main__":
    main()
