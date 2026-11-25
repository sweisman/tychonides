"""Reproduce the Mars comparison without network access or a catalog download."""

import argparse
import csv
from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OPPOSITION_DATE = date(1595, 10, 31)  # Julian label, used for calendar arithmetic.
OPPOSITION_LONGITUDE = 30 + 17 + (30 + 2 / 3) / 60
OPPOSITION_JD = (OPPOSITION_DATE + timedelta(days=10)).toordinal() + 1721425
APOGEE = (9 + 6 / 60 + 40 / 3600 + 28 + 8 / 60 + 40 / 3600 - (240 + 8 + 20 / 60)) % 360
SUN_APOGEE = np.deg2rad(96)
ANNUAL_RATE = np.deg2rad(360 / 365.2422)
MARS_RATE = np.deg2rad(360 / 686.98)

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


def deferent(anomaly):
    eccentric_offset = 6 / 60
    along_ray = np.sqrt(1 - (eccentric_offset * np.sin(anomaly)) ** 2) - (
        eccentric_offset * np.cos(anomaly)
    )
    return np.exp(1j * np.deg2rad(APOGEE)) * (
        2 * eccentric_offset + along_ray * np.exp(1j * anomaly)
    )


def epicycles(anomaly, large, small):
    return np.exp(1j * anomaly) + large - small * np.exp(2j * anomaly)


def longomontanus_annual_radius(solar_anomaly, mars_anomaly):
    return (630275 + 11750 * (1 + np.cos(solar_anomaly)) + 12925 * (1 + np.cos(mars_anomaly))) / 1e6


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


def models(day):
    day = np.asarray(day, dtype=float)
    origin = np.zeros_like(day, dtype=complex)
    apsis = np.exp(1j * np.deg2rad(APOGEE))
    circular_earth = np.exp(1j * (np.deg2rad(OPPOSITION_LONGITUDE) + ANNUAL_RATE * day))

    phase = anomaly_at_longitude(deferent, OPPOSITION_LONGITUDE, APOGEE)
    center = deferent(phase + MARS_RATE * day) / (39.5 / 60)
    ptolemy = Track(
        "Ptolemaic equant", "ptolemaic", "#996019", "--", origin, center - circular_earth, center
    )

    def copernican(anomaly):
        return apsis * epicycles(anomaly, 0.146, 0.050)

    phase = anomaly_at_longitude(copernican, OPPOSITION_LONGITUDE, APOGEE)
    mars = copernican(phase + MARS_RATE * day) / 0.658
    copernicus = Track(
        "Copernican circles", "copernican", "#07678a", ":", circular_earth, mars, origin
    )

    def longomontanus(anomaly):
        return apsis * epicycles(anomaly, 0.1484, 0.0371)

    def sun_trajectory(anomaly):
        return np.exp(1j * SUN_APOGEE) * (1 / 28 + np.exp(1j * anomaly))

    phase = anomaly_at_longitude(longomontanus, OPPOSITION_LONGITUDE, APOGEE)
    mars_about_sun = longomontanus(phase + MARS_RATE * day)
    solar_phase = anomaly_at_longitude(
        sun_trajectory, OPPOSITION_LONGITUDE + 180, np.rad2deg(SUN_APOGEE)
    )
    sun_direction = np.angle(sun_trajectory(solar_phase + ANNUAL_RATE * day))
    annual_radius = longomontanus_annual_radius(
        sun_direction - SUN_APOGEE, np.angle(mars_about_sun / apsis)
    )
    sun = annual_radius * np.exp(1j * sun_direction) / 0.654950
    mars = sun + mars_about_sun / 0.654950
    tycho = Track("Tychonic (Longomontanus)", "tychonic", "#984481", "-.", origin, mars, sun)

    # The date-centered comparison omits light time and sub-day TT/UT differences.
    elapsed = OPPOSITION_JD - 2451545 + day
    earth = heliocentric_orbit(elapsed, EARTH_ELEMENTS)
    mars = heliocentric_orbit(elapsed, MARS_ELEMENTS)
    geocentric = mars - earth
    latitude = np.rad2deg(np.arctan2(geocentric[..., 2], np.hypot(*geocentric[..., :2].T)))
    anchor = heliocentric_orbit(OPPOSITION_JD - 2451545, MARS_ELEMENTS) - heliocentric_orbit(
        OPPOSITION_JD - 2451545, EARTH_ELEMENTS
    )
    phase = np.deg2rad(OPPOSITION_LONGITUDE - angle(complex(*anchor[:2])))
    rotation = np.exp(1j * phase)
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


def read_observations(path):
    with path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    return {
        "rows": rows,
        "day": np.array(
            [(date.fromisoformat(row["julian_date"]) - OPPOSITION_DATE).days for row in rows]
        ),
        "longitude": np.array([float(Fraction(row["longitude_degrees_exact"])) for row in rows]),
        "latitude": np.array([float(row["latitude_arcseconds"] or "nan") / 3600 for row in rows]),
    }


def write_results(path, observations):
    tracks = models(observations["day"])
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = [*observations["rows"][0], "nominal_jd", "modern_latitude_degrees"]
        for track in tracks:
            fields.extend([f"{track.key}_longitude_degrees", f"{track.key}_minus_log_arcmin"])
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for i, row in enumerate(observations["rows"]):
            result = {
                **row,
                "nominal_jd": OPPOSITION_JD + observations["day"][i],
                "modern_latitude_degrees": f"{tracks[-1].latitude[i]:.6f}",
            }
            for track in tracks:
                predicted = track.longitude[i]
                result[f"{track.key}_longitude_degrees"] = f"{predicted:.6f}"
                difference = wrapped(predicted - observations["longitude"][i]) * 60
                result[f"{track.key}_minus_log_arcmin"] = f"{difference:.2f}"
            writer.writerow(result)


def julian_label(day, _position=None):
    return (OPPOSITION_DATE + timedelta(days=round(day))).strftime("%b %d").replace(" 0", " ")


def plot_motion(output, observations):
    sample = np.linspace(-57, 56, 1131)
    tracks = models(sample)
    fig, (ax, residuals) = plt.subplots(
        2, 1, figsize=(9, 7), sharex=True, height_ratios=(2, 1), layout="constrained"
    )
    days = observations["day"]
    longitude = observations["longitude"]
    for track, at_records in zip(tracks, models(days), strict=True):
        ax.plot(sample, track.longitude, track.style, color=track.color, lw=2, label=track.name)
        residuals.plot(
            days,
            wrapped(at_records.longitude - longitude),
            linestyle="none",
            marker="o",
            ms=3.5,
            color=track.color,
        )
    ax.scatter(days, longitude, zorder=8, s=26, c="#22262e", label="Tycho's dated reductions")
    ax.set(ylabel="Ecliptic longitude (degrees)", title="Mars reverses direction in 1595")
    ax.legend(ncols=2, frameon=False, loc="upper right", fontsize=9)
    residuals.axhline(0, color="#89939f", lw=0.8)
    residuals.set(ylabel="Model − log (degrees)", xlabel="1595 date (Julian calendar)")
    for panel in (ax, residuals):
        panel.axvline(0, color="#89939f", lw=1, alpha=0.65)
        panel.grid(alpha=0.18)
        panel.spines[["top", "right"]].set_visible(False)
    ticks = [-54, -31, -16, 0, 15, 30, 53]
    residuals.set_xticks(ticks, [julian_label(d) for d in ticks])
    fig.savefig(output / "mars-1595-motion.png", dpi=170)
    plt.close(fig)


def plot_geometry(output):
    span = np.linspace(-140, 160, 601)
    snapshots = np.array([-36.0, 0.0, 36.0])
    fig, axes = plt.subplots(2, 2, figsize=(9, 8.7), layout="constrained")
    for ax, track, positions in zip(axes.flat, models(span), models(snapshots), strict=True):
        ax.plot(track.mars.real, track.mars.imag, color=track.color, lw=2)
        ax.plot(track.earth.real, track.earth.imag, color="#425a79", lw=1.35)
        ax.plot(track.guide.real, track.guide.imag, color="#ba8a37", lw=1.25, ls="--")
        for i, (earth, mars, guide) in enumerate(
            zip(positions.earth, positions.mars, positions.guide, strict=True)
        ):
            ax.plot([earth.real, mars.real], [earth.imag, mars.imag], color="#a9b0ba", lw=1)
            ax.scatter(earth.real, earth.imag, color="#425a79", s=25, zorder=5)
            ax.scatter(guide.real, guide.imag, color="#ba8a37", s=29, zorder=4)
            if track.key == "ptolemaic":
                ax.add_patch(
                    plt.Circle(
                        (guide.real, guide.imag), 1, fill=False, ls=":", lw=0.8, color="#b79561"
                    )
                )
            ax.scatter(mars.real, mars.imag, color=track.color, s=28, zorder=5)
            if track.key in {"ptolemaic", "tychonic"}:
                offset = [(-18, 11), (0, -20), (18, 11)][i]
                ax.annotate(
                    str(i + 1),
                    (mars.real, mars.imag),
                    xytext=offset,
                    textcoords="offset points",
                    ha="center",
                    va="center",
                    arrowprops={"arrowstyle": "-", "color": "#9fa7b1"},
                    fontsize=10,
                )
            else:
                ax.annotate(
                    str(i + 1),
                    (mars.real, mars.imag),
                    xytext=(5, 7),
                    textcoords="offset points",
                    fontsize=10,
                )
        ax.set(title=track.name, xlim=(-2.65, 2.65), ylim=(-2.65, 2.65), aspect="equal")
        ax.set_xticks([-2, 0, 2])
        ax.set_yticks([-2, 0, 2])
        ax.set_axisbelow(True)
        ax.grid(alpha=0.2)
        ax.spines[:].set_visible(False)
    fig.suptitle("Four geometries for the same reversal", fontsize=18)
    fig.supxlabel("Sightlines 1–3: Sep 25, Oct 31, Dec 6 (Julian)   •   Unit: mean annual radius")
    fig.savefig(output / "mars-1595-geometry.png", dpi=170)
    plt.close(fig)


def plot_sky(output, observations):
    modern = models(np.linspace(-57, 56, 1131))[-1]
    fig, ax = plt.subplots(figsize=(8.5, 4), layout="constrained")
    ax.plot(
        modern.longitude, modern.latitude, color=modern.color, lw=2, label="Modern Keplerian track"
    )
    paired = np.isfinite(observations["latitude"])
    ax.scatter(
        observations["longitude"][paired],
        observations["latitude"][paired],
        color="#22262e",
        zorder=5,
        s=27,
        label="Tycho's paired reductions",
    )
    for day in (-43, 0, 53):
        track = models([day])[-1]
        ax.annotate(
            julian_label(day),
            (track.longitude[0], track.latitude[0]),
            xytext=(3, 8),
            textcoords="offset points",
            fontsize=9,
        )
    ax.invert_xaxis()
    ax.set(
        xlabel="Ecliptic longitude (degrees, increases leftward)",
        ylabel="Ecliptic latitude (degrees)",
        title="The reversal in the sky",
    )
    ax.legend(frameon=False, loc="lower right")
    ax.grid(alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(output / "mars-1595-sky.png", dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    observations = read_observations(Path(__file__).with_name("mars-1595-observations.csv"))
    plt.rcParams.update({"font.size": 11, "axes.titleweight": "bold", "axes.labelcolor": "#263445"})
    write_results(args.output / "mars-1595-results.csv", observations)
    plot_motion(args.output, observations)
    plot_geometry(args.output)
    plot_sky(args.output, observations)


if __name__ == "__main__":
    main()
