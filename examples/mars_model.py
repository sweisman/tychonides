"""Shared geometry and conventions for the Mars opposition studies.

Everything here runs offline from the CSV files beside this module and needs
only NumPy. The conventions below were fixed on the 1595 passage before any
other apparition was computed.

Time. Dates are the Julian-calendar labels printed in the logs. A printed
calculation hour is used when its reckoning is unambiguous:

- an hour with no daypart label, or with an afternoon, evening, night, or
  before-midnight label, is counted from noon of the labeled date, as in the
  astronomical day (13h 40m is 1:40 the following morning);
- an hour labeled morning is a civil morning hour of the labeled date.

Hours labeled before noon or after midnight are not used, because the catalog
leaves their day origin open. Those rows, and rows with no printed hour, are
evaluated at local noon of the labeled date and reported as untimed. Local time
is converted to UT with the longitude of Uraniborg. The equation of time (at
most 16 minutes) and Tycho's clock corrections are not applied.

Anchors. Each historical curve passes through Longomontanus's observed
longitude at his printed opposition time. The Ptolemaic and Copernican
constructions refer Mars to the mean Sun, so their mean Sun is placed with the
same eccentric solar model the Tychonic curve uses, not opposite Mars.
"""

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path

import numpy as np
from mars_select import mixed
from mars_select import sexagesimal as exact_sexagesimal

HERE = Path(__file__).parent
SITE_EAST_LONGITUDE = 12.6967  # Uraniborg on Hven, degrees east of Greenwich.
ANNUAL_RATE = np.deg2rad(360 / 365.2422)
MARS_RATE = np.deg2rad(360 / 686.98)
SUN_APOGEE = np.deg2rad(96)
SUN_ECCENTRICITY = 1 / 28
MEAN_ANNUAL_RADIUS = 0.654950
FROM_NOON = {"", "after_noon", "evening", "night", "before_midnight"}
SIGNS = "♈♉♊♋♌♍♎♏♐♑♒♓"
KEYS = ("ptolemaic", "copernican", "tychonic", "modern")

# JPL approximate positions, Table 2a. Columns a, e, inclination, mean
# longitude, perihelion longitude, node longitude. Second row per century.
EARTH_ELEMENTS = (
    (1.00000018, 0.01673163, -0.00054346, 100.46691572, 102.93005885, -5.11260389),
    (-0.00000003, -0.00003661, -0.01337178, 35999.37306329, 0.31795260, -0.24123856),
)
MARS_ELEMENTS = (
    (1.52371243, 0.09336511, 1.85181869, -4.56813164, -23.91744784, 49.71320984),
    (0.00000097, 0.00009149, -0.00724757, 19140.29934243, 0.45223625, -0.26852431),
)


def angle(vector):
    return np.angle(vector, deg=True)


def wrapped(degrees):
    return (degrees + 180) % 360 - 180


def sexagesimal(text):
    """Degrees from 'S · D M S', whose first place counts sixties of degrees, or 'D M S'."""
    return float(exact_sexagesimal(text))


def zodiac(text):
    """Degrees of longitude from a sign, degrees, and minutes, such as '♉ 17 29½'."""
    sign, degrees, minutes = text.split()
    return float(30 * SIGNS.index(sign) + mixed(degrees) + mixed(minutes) / 60)


def julian_day_number(day):
    """Julian day number at noon of a Julian-calendar date between 1500 and 1700."""
    return (day + timedelta(days=10)).toordinal() + 1721425


def jd_ut(day, hours):
    """UT Julian date of local hours after the midnight that opens a labeled date."""
    return julian_day_number(day) - 0.5 + hours / 24 - SITE_EAST_LONGITUDE / 360


def clock(daypart, epoch_seconds):
    """Local hours after the midnight opening the labeled date, with the basis used."""
    if not epoch_seconds:
        return 12.0, "nominal noon"
    hours = float(Fraction(epoch_seconds)) / 3600
    if daypart in FROM_NOON:
        return 12.0 + hours, "printed hour from noon"
    if daypart == "morning" and hours < 12:
        return hours, "printed morning hour"
    return 12.0, "nominal noon, hour label open"


@dataclass(frozen=True)
class Opposition:
    number: str
    day: date
    hours_from_noon: float
    jd: float
    longitude: float
    apogee: float
    apogee_basis: str
    date_basis: str
    anomaly: float
    computed: float

    @property
    def label(self):
        return f"{self.day.year} {self.day.strftime('%b')} {self.day.day}"

    def date_label(self, days):
        """Julian-calendar date nearest to an offset in days from the opposition."""
        return self.day + timedelta(days=round(float(days) + self.hours_from_noon / 24))


def load_oppositions(path=HERE / "mars-oppositions.csv"):
    """Longomontanus's opposition table with the apsidal direction implied by each row.

    The apsidal longitude is mean longitude plus precession minus anomaly. A
    precession cell more than one degree from the column median is not used;
    that row takes its apsidal longitude from a straight line through the others.
    """
    with path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    precession = np.array([sexagesimal(row["precession_expression"]) for row in rows])
    usable = np.abs(precession - np.median(precession)) <= 1
    days = [date(int(row["year"]), int(row["month"]), int(row["day"])) for row in rows]
    hours = [int(row["hour"]) + int(row["minute"]) / 60 for row in rows]
    epochs = np.array([jd_ut(day, 12 + hour) for day, hour in zip(days, hours, strict=True)])
    apogee = np.array(
        [
            sexagesimal(row["mean_longitude_expression"])
            + sexagesimal(row["precession_expression"])
            - sexagesimal(row["anomaly_expression"])
            for row in rows
        ]
    )
    apogee %= 360
    slope, intercept = np.polyfit(epochs[usable], apogee[usable], 1)
    result = {}
    for index, row in enumerate(rows):
        result[row["number"]] = Opposition(
            number=row["number"],
            day=days[index],
            hours_from_noon=hours[index],
            jd=float(epochs[index]),
            longitude=float(Fraction(row["observed_longitude_degrees_exact"])),
            apogee=float(apogee[index] if usable[index] else slope * epochs[index] + intercept),
            apogee_basis="printed row" if usable[index] else "line through the other rows",
            date_basis=row["date_basis"],
            anomaly=sexagesimal(row["anomaly_expression"]),
            computed=zodiac(row["computed_longitude_expression"]),
        )
    return result


def load_observations(number, path=HERE / "mars-observations.csv"):
    """Selected rows of one opposition with their evaluation times."""
    with path.open(encoding="utf-8", newline="") as source:
        rows = [row for row in csv.DictReader(source) if row["opposition"] == number]
    for row in rows:
        hours, basis = clock(row["daypart"], row["epoch_seconds"])
        row["time_basis"] = basis
        row["jd_ut"] = jd_ut(date.fromisoformat(row["julian_date"]), hours)
    return rows


def load_predictions(number, path=HERE / "mars-predictions.csv"):
    """Printed model predictions in one opposition window."""
    with path.open(encoding="utf-8", newline="") as source:
        return [row for row in csv.DictReader(source) if row["opposition"] == number]


def load_ephemeris(path=HERE / "mars-ephemeris.csv"):
    """Cached JPL DE441 apparent geocentric positions, keyed by row identity."""
    with path.open(encoding="utf-8", newline="") as source:
        return {row["key"]: row for row in csv.DictReader(source)}


def arrays(rows, opposition):
    """Offsets from the opposition, longitudes, weights, and the timed mask of selected rows."""
    return (
        np.array([row["jd_ut"] - opposition.jd for row in rows]),
        np.array([float(Fraction(row["longitude_degrees_exact"])) for row in rows]),
        np.array([float(Fraction(row["date_weight"])) for row in rows]),
        np.array([row["time_basis"].startswith("printed") for row in rows]),
    )


def weighted_rms(values, weights):
    """Root mean square in which the rows of one date share a weight of one."""
    values, weights = np.asarray(values, dtype=float), np.asarray(weights, dtype=float)
    return float(np.sqrt(np.sum(weights * values**2) / np.sum(weights)))


def deferent(anomaly, apogee, eccentricity=6 / 60):
    along_ray = np.sqrt(1 - (eccentricity * np.sin(anomaly)) ** 2) - eccentricity * np.cos(anomaly)
    return np.exp(1j * np.deg2rad(apogee)) * (2 * eccentricity + along_ray * np.exp(1j * anomaly))


def epicycles(anomaly, large, small):
    return np.exp(1j * anomaly) + large - small * np.exp(2j * anomaly)


def longomontanus_annual_radius(solar_anomaly, mars_anomaly):
    return (630275 + 11750 * (1 + np.cos(solar_anomaly)) + 12925 * (1 + np.cos(mars_anomaly))) / 1e6


def sun_path(anomaly):
    return np.exp(1j * SUN_APOGEE) * (SUN_ECCENTRICITY + np.exp(1j * anomaly))


def anomaly_at_longitude(trajectory, longitude, apogee):
    """Solve the monotone longitude near its corresponding circular phase."""
    center = np.deg2rad(wrapped(longitude - apogee))
    low, high = center - 0.4, center + 0.4
    for _ in range(48):
        mid = (low + high) / 2
        if wrapped(angle(trajectory(mid)) - longitude) < 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def heliocentric_orbit(days_since_j2000, elements):
    century = np.asarray(days_since_j2000)[..., None] / 36525
    start, rates = np.asarray(elements)
    a, e, inclination, mean_longitude, perihelion, node = np.moveaxis(
        start + rates * century, -1, 0
    )
    mean_anomaly = np.deg2rad(wrapped(mean_longitude - perihelion))
    eccentric_anomaly = mean_anomaly.copy()
    for _ in range(6):
        eccentric_anomaly -= (eccentric_anomaly - e * np.sin(eccentric_anomaly) - mean_anomaly) / (
            1 - e * np.cos(eccentric_anomaly)
        )
    x = a * (np.cos(eccentric_anomaly) - e)
    y = a * np.sqrt(1 - e**2) * np.sin(eccentric_anomaly)
    omega, inclination, node = np.deg2rad([perihelion - node, inclination, node])
    along_node = x * np.cos(omega) - y * np.sin(omega)
    across_node = x * np.sin(omega) + y * np.cos(omega)
    projected = across_node * np.cos(inclination)
    return np.stack(
        [
            along_node * np.cos(node) - projected * np.sin(node),
            along_node * np.sin(node) + projected * np.cos(node),
            across_node * np.sin(inclination),
        ],
        axis=-1,
    )


@dataclass(frozen=True)
class Track:
    name: str
    key: str
    color: str
    style: str
    earth: np.ndarray
    mars: np.ndarray
    guide: np.ndarray
    latitude: np.ndarray | None = None

    @property
    def sightline(self):
        return self.mars - self.earth

    @property
    def longitude(self):
        return angle(self.sightline)


def models(
    days,
    opposition,
    *,
    apogee_shift=0.0,
    mean_sun="solar model",
    copernican=(0.146, 0.050, 0.658),
    radius_rule="true anomalies",
    eccentric_sun=True,
):
    """The four tracks at offsets in days from the opposition.

    The keyword arguments exist for the sensitivity table. `mean_sun` may be
    "opposite Mars", the phasing of the first release. `radius_rule` may be
    "mean anomalies" or "constant". `eccentric_sun=False` gives the Tychonic
    curve a uniform Sun.
    """
    days = np.asarray(days, dtype=float)
    origin = np.zeros_like(days, dtype=complex)
    anchor = opposition.longitude
    apogee = opposition.apogee + apogee_shift
    apsis = np.exp(1j * np.deg2rad(apogee))

    solar_phase = anomaly_at_longitude(sun_path, anchor + 180, np.rad2deg(SUN_APOGEE))
    mean_sun_anchor = (
        SUN_APOGEE + solar_phase if mean_sun == "solar model" else np.deg2rad(anchor + 180)
    )
    earth_anchor = -np.exp(1j * mean_sun_anchor)
    mean_earth = earth_anchor * np.exp(1j * ANNUAL_RATE * days)

    def epicycle_center(anomaly):
        return deferent(anomaly, apogee) / (39.5 / 60)

    phase = anomaly_at_longitude(lambda a: epicycle_center(a) - earth_anchor, anchor, apogee)
    center = epicycle_center(phase + MARS_RATE * days)
    ptolemy = Track(
        "Ptolemaic equant", "ptolemaic", "#996019", "--", origin, center - mean_earth, center
    )

    large, small, earth_circle = copernican

    def copernican_mars(anomaly):
        return apsis * epicycles(anomaly, large, small) / earth_circle

    phase = anomaly_at_longitude(lambda a: copernican_mars(a) - earth_anchor, anchor, apogee)
    copernicus = Track(
        "Copernican circles",
        "copernican",
        "#07678a",
        ":",
        mean_earth,
        copernican_mars(phase + MARS_RATE * days),
        origin,
    )

    def longomontanus(anomaly):
        return apsis * epicycles(anomaly, 0.1484, 0.0371)

    phase = anomaly_at_longitude(longomontanus, anchor, apogee)
    mars_about_sun = longomontanus(phase + MARS_RATE * days)
    if eccentric_sun:
        sun_direction = np.angle(sun_path(solar_phase + ANNUAL_RATE * days))
    else:
        sun_direction = np.deg2rad(anchor + 180) + ANNUAL_RATE * days
    if radius_rule == "constant":
        annual_radius = MEAN_ANNUAL_RADIUS
    elif radius_rule == "mean anomalies":
        annual_radius = longomontanus_annual_radius(
            solar_phase + ANNUAL_RATE * days, phase + MARS_RATE * days
        )
    else:
        annual_radius = longomontanus_annual_radius(
            sun_direction - SUN_APOGEE, np.angle(mars_about_sun / apsis)
        )
    sun = annual_radius * np.exp(1j * sun_direction) / MEAN_ANNUAL_RADIUS
    tycho = Track(
        "Tychonic (Longomontanus)",
        "tychonic",
        "#984481",
        "-.",
        origin,
        sun + mars_about_sun / MEAN_ANNUAL_RADIUS,
        sun,
    )

    # The modern track omits light time and the difference between TT and UT.
    elapsed = opposition.jd - 2451545 + days
    earth = heliocentric_orbit(elapsed, EARTH_ELEMENTS)
    mars = heliocentric_orbit(elapsed, MARS_ELEMENTS)
    geocentric = mars - earth
    latitude = np.rad2deg(np.arctan2(geocentric[..., 2], np.hypot(*geocentric[..., :2].T)))
    at_anchor = heliocentric_orbit(opposition.jd - 2451545, MARS_ELEMENTS) - heliocentric_orbit(
        opposition.jd - 2451545, EARTH_ELEMENTS
    )
    rotation = np.exp(1j * np.deg2rad(anchor - angle(complex(*at_anchor[:2]))))
    modern = Track(
        "Modern Keplerian",
        "modern",
        "#276b4c",
        "-",
        rotation * (earth[..., 0] + 1j * earth[..., 1]),
        rotation * (mars[..., 0] + 1j * mars[..., 1]),
        origin,
        latitude,
    )
    return ptolemy, copernicus, tycho, modern


def mean_sun_longitude(days, opposition):
    """Mean Sun of the eccentric solar model, in degrees, at offsets from the opposition."""
    phase = anomaly_at_longitude(sun_path, opposition.longitude + 180, np.rad2deg(SUN_APOGEE))
    return np.rad2deg(SUN_APOGEE + phase + ANNUAL_RATE * np.asarray(days, dtype=float))


def mean_opposition(opposition):
    """Offset in days and longitude where the Tychonic curve is opposite the mean Sun."""
    low, high = -4.0, 4.0

    def elongation(days):
        mars = models([days], opposition)[2].longitude[0]
        return wrapped(mars - mean_sun_longitude(days, opposition) - 180)

    for _ in range(48):
        mid = (low + high) / 2
        if elongation(mid) > 0:
            low = mid
        else:
            high = mid
    days = (low + high) / 2
    return days, float(models([days], opposition)[2].longitude[0])


def first_inequality(opposition):
    """Longitude at opposition from Longomontanus's printed anomaly and the coded circles."""
    anomaly = np.deg2rad(opposition.anomaly)
    return float(opposition.apogee + angle(epicycles(anomaly, 0.1484, 0.0371)))


def describe(track, opposition):
    """Stations, retrograde span, and projected distance of one track."""
    grid = np.arange(-90, 90.0001, 0.01)
    sampled = models(grid, opposition)[KEYS.index(track.key)]
    longitude = np.rad2deg(np.unwrap(np.deg2rad(sampled.longitude)))
    before, after = grid < 0, grid > 0
    first = grid[before][np.argmax(longitude[before])]
    second = grid[after][np.argmin(longitude[after])]
    at_anchor = models([0.0], opposition)[KEYS.index(track.key)]
    return {
        "first_station": opposition.date_label(first).isoformat(),
        "second_station": opposition.date_label(second).isoformat(),
        "retrograde_span_degrees": f"{longitude[before].max() - longitude[after].min():.2f}",
        "projected_distance": f"{abs(at_anchor.sightline[0]):.3f}",
    }
