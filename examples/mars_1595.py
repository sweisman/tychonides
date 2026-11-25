"""Reproduce the 1595 Mars comparison without network access or a catalog download.

Inputs are the CSV files beside this script: the selected log reductions, the
opposition table, and cached JPL positions. `mars_select.py` and
`mars_ephemeris.py` rebuild those inputs from the catalog and from Horizons.
"""

import argparse
import csv
from collections import defaultdict
from datetime import date
from fractions import Fraction
from pathlib import Path

import mars_model as mm
import numpy as np

NUMBER = "VIII"
PREDICTION_KEEP = [
    "julian_date", "source_id", "printed_page", "longitude_id", "model", "longitude_expression",
]  # fmt: skip
PREDICTION_FIELDS = [
    *PREDICTION_KEEP, "sign_basis", "log_longitude_degrees", "prediction_minus_log_arcmin",
    "de441_longitude_degrees", "prediction_minus_de441_arcmin",
]  # fmt: skip
VARIANTS = (
    ("baseline", {}),
    ("every row at nominal noon", {"time": "noon"}),
    ("printed hours 30 minutes later", {"time": 0.5}),
    ("printed hours 30 minutes earlier", {"time": -0.5}),
    ("mean Sun opposite Mars at the anchor", {"mean_sun": "opposite Mars"}),
    ("apsidal line 20 degrees earlier", {"apogee_shift": -20.0}),
    ("apsidal line 10 degrees earlier", {"apogee_shift": -10.0}),
    ("apsidal line 10 degrees later", {"apogee_shift": 10.0}),
    ("Copernican Earth circle 0.65495", {"copernican": (0.146, 0.050, 0.65495)}),
    ("Copernican small circles 1484 and 371", {"copernican": (0.1484, 0.0371, 0.658)}),
    ("Tychonic radius rule with mean anomalies", {"radius_rule": "mean anomalies"}),
    ("Tychonic constant annual radius", {"radius_rule": "constant"}),
    (
        "Tychonic uniform Sun and constant radius",
        {"radius_rule": "constant", "eccentric_sun": False},
    ),
    ("without the September 7 globe estimates", {"omit": "1595-09-07"}),
    ("without the log's computed opposition of October 29", {"omit": "1595-10-29"}),
)


def load():
    opposition = mm.load_oppositions()[NUMBER]
    rows = mm.load_observations(NUMBER)
    ephemeris = mm.load_ephemeris()
    for row in rows:
        cached = ephemeris[row["longitude_id"]]
        if abs(float(cached["jd_ut"]) - row["jd_ut"]) > 2e-6:
            raise ValueError("Cached ephemeris is stale; run mars_ephemeris.py")
        row["de441_longitude"] = float(cached["longitude_degrees"])
    return opposition, rows, ephemeris


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_results(path, opposition, rows):
    days, longitude, _, _ = mm.arrays(rows, opposition)
    tracks = mm.models(days, opposition)
    keep = [
        "julian_date", "daypart", "source_id", "printed_page", "longitude_id", "role",
        "longitude_expression", "longitude_degrees_exact", "date_weight", "epoch_expression",
        "latitude_id", "latitude_arcseconds_exact",
    ]  # fmt: skip
    fields = [*keep, "time_basis", "jd_ut", "days_from_opposition", "modern_latitude_degrees"]
    fields += ["de441_longitude_degrees", "de441_minus_log_arcmin"]
    for track in tracks:
        fields += [f"{track.key}_longitude_degrees", f"{track.key}_minus_log_arcmin"]
    results = []
    for i, row in enumerate(rows):
        result = {name: row[name] for name in keep}
        result |= {
            "time_basis": row["time_basis"],
            "jd_ut": f"{row['jd_ut']:.6f}",
            "days_from_opposition": f"{days[i]:.4f}",
            "modern_latitude_degrees": f"{tracks[-1].latitude[i]:.6f}",
            "de441_longitude_degrees": f"{row['de441_longitude']:.6f}",
            "de441_minus_log_arcmin": f"{(row['de441_longitude'] - longitude[i]) * 60:.2f}",
        }
        for track in tracks:
            result[f"{track.key}_longitude_degrees"] = f"{track.longitude[i]:.6f}"
            difference = mm.wrapped(track.longitude[i] - longitude[i]) * 60
            result[f"{track.key}_minus_log_arcmin"] = f"{difference:.2f}"
        results.append(result)
    write_csv(path, fields, results)


def compare_predictions(opposition, rows):
    """Each printed prediction beside the log and DE441 on the same date."""
    by_date = defaultdict(list)
    for row in rows:
        by_date[row["julian_date"]].append(row)
    table = []
    for item in mm.load_predictions(opposition.number):
        result = {name: item[name] for name in PREDICTION_KEEP}
        signed = bool(item["longitude_degrees_exact"])
        result["sign_basis"] = "printed" if signed else "not printed; compared within the sign"
        value = float(
            Fraction(item["longitude_degrees_exact"] or item["within_sign_degrees_exact"])
        )
        same = by_date.get(item["julian_date"], [])
        if same:
            references = {
                "log": np.mean([float(Fraction(row["longitude_degrees_exact"])) for row in same]),
                "de441": np.mean([row["de441_longitude"] for row in same]),
            }
            for name, reference in references.items():
                gap = (
                    mm.wrapped(value - reference) if signed else (value - reference + 15) % 30 - 15
                )
                result[f"{name}_longitude_degrees"] = f"{reference:.6f}"
                result[f"prediction_minus_{name}_arcmin"] = f"{gap * 60:.2f}"
        table.append(result)
    return table


def measures(residual, weights, timed):
    return {
        "rms_degrees": f"{mm.weighted_rms(residual, weights):.3f}",
        "rms_timed_degrees": f"{mm.weighted_rms(residual[timed], weights[timed]):.3f}",
        "mean_timed_arcmin": f"{np.average(residual[timed], weights=weights[timed]) * 60:.2f}",
    }


def write_summary(path, opposition, rows, predictions):
    days, longitude, weights, timed = mm.arrays(rows, opposition)
    fields = [
        "model", "kind", "rows", "first_station", "second_station", "retrograde_span_degrees",
        "projected_distance", "rms_degrees", "rms_timed_degrees", "mean_timed_arcmin",
    ]  # fmt: skip
    summary = []
    for track in mm.models(days, opposition):
        summary.append(
            {
                "model": track.key,
                "kind": "reconstruction",
                "rows": len(rows),
                **mm.describe(track, opposition),
                **measures(mm.wrapped(track.longitude - longitude), weights, timed),
            }
        )
    residual = np.array([row["de441_longitude"] for row in rows]) - longitude
    summary.append(
        {
            "model": "de441",
            "kind": "ephemeris",
            "rows": len(rows),
            **measures(residual, weights, timed),
        }
    )
    for model in sorted({item["model"] for item in predictions}):
        gaps = [
            float(item["prediction_minus_log_arcmin"]) / 60
            for item in predictions
            if item["model"] == model and item.get("prediction_minus_log_arcmin")
        ]
        if gaps:
            summary.append(
                {
                    "model": model,
                    "kind": "printed prediction",
                    "rows": len(gaps),
                    "rms_degrees": f"{mm.weighted_rms(gaps, np.ones(len(gaps))):.3f}",
                }
            )
    write_csv(path, fields, summary)


def write_sensitivity(path, opposition, rows):
    days, longitude, weights, timed = mm.arrays(rows, opposition)
    noon = np.array(
        [mm.jd_ut(date.fromisoformat(row["julian_date"]), 12.0) - opposition.jd for row in rows]
    )
    labels = np.array([row["julian_date"] for row in rows])
    table = []
    for name, options in VARIANTS:
        options = dict(options)
        time, omit = options.pop("time", None), options.pop("omit", None)
        when = noon if time == "noon" else days + (timed * time / 24 if time else 0)
        use = labels != omit
        result = {"variant": name}
        for track in mm.models(when, opposition, **options):
            residual = mm.wrapped(track.longitude - longitude)
            rms = mm.weighted_rms(residual[use], weights[use])
            result[f"{track.key}_rms_degrees"] = f"{rms:.3f}"
        table.append(result)
    write_csv(path, list(table[0]), table)


def write_validation(path, opposition, rows, ephemeris):
    """Checks of the coded constructions against values printed in the sources."""
    fields = ["check", "opposition", "printed", "coded", "difference", "unit", "note"]
    checks = []
    for item in mm.load_oppositions().values():
        coded = mm.first_inequality(item) % 360
        # Compared within the sign, so a sign that differs between columns stays visible.
        difference = (coded - item.computed + 15) % 30 - 15
        notes = [] if item.apogee_basis == "printed row" else ["apsidal longitude from the line"]
        if item.date_basis != "printed date":
            notes.append(item.date_basis)
        if abs(mm.wrapped(coded - item.computed)) > 15:
            notes.append("printed sign differs from the observed column")
        checks.append(
            {
                "check": "first inequality against the printed computed longitude",
                "opposition": f"{item.number} {item.label}",
                "printed": f"{item.computed:.4f}",
                "coded": f"{coded:.4f}",
                "difference": f"{difference * 60:.2f}",
                "unit": "arcmin",
                "note": "; ".join(notes),
            }
        )
        cached = float(ephemeris[f"opposition-{item.number}"]["longitude_degrees"])
        checks.append(
            {
                "check": "observed opposition longitude against DE441 at the printed time",
                "opposition": f"{item.number} {item.label}",
                "printed": f"{item.longitude:.4f}",
                "coded": f"{cached:.4f}",
                "difference": f"{mm.wrapped(cached - item.longitude) * 60:.2f}",
                "unit": "arcmin",
                "note": "DE441 minus Longomontanus",
            }
        )
    computed = min(
        (row for row in rows if row["julian_date"] == "1595-10-29"),
        key=lambda row: Fraction(row["epoch_seconds"]),
    )
    days, longitude = mm.mean_opposition(opposition)
    printed_days = computed["jd_ut"] - opposition.jd
    printed_longitude = float(Fraction(computed["longitude_degrees_exact"]))
    checks.append(
        {
            "check": "mean opposition time against the log's computed value",
            "opposition": f"{opposition.number} {opposition.label}",
            "printed": f"{printed_days:.4f}",
            "coded": f"{days:.4f}",
            "difference": f"{(days - printed_days) * 24:.2f}",
            "unit": "hours",
            "note": "days from the true opposition; solar model and Tychonic curve",
        }
    )
    checks.append(
        {
            "check": "mean opposition longitude against the log's computed value",
            "opposition": f"{opposition.number} {opposition.label}",
            "printed": f"{printed_longitude:.4f}",
            "coded": f"{longitude:.4f}",
            "difference": f"{(longitude - printed_longitude) * 60:.2f}",
            "unit": "arcmin",
            "note": computed["longitude_expression"],
        }
    )
    write_csv(path, fields, checks)


def write_tables(output):
    """Write every numerical output. Needs NumPy only."""
    opposition, rows, ephemeris = load()
    predictions = compare_predictions(opposition, rows)
    write_results(output / "mars-1595-results.csv", opposition, rows)
    write_csv(output / "mars-1595-predictions.csv", PREDICTION_FIELDS, predictions)
    write_summary(output / "mars-1595-summary.csv", opposition, rows, predictions)
    write_sensitivity(output / "mars-1595-sensitivity.csv", opposition, rows)
    write_validation(output / "mars-1595-validation.csv", opposition, rows, ephemeris)
    return opposition, rows


def plot_motion(plt, output, opposition, rows):
    sample = np.linspace(-57, 56, 1131)
    days, longitude, _, timed = mm.arrays(rows, opposition)
    fig, (ax, residuals) = plt.subplots(
        2, 1, figsize=(9, 7), sharex=True, height_ratios=(2, 1), layout="constrained"
    )
    for track, at_records in zip(
        mm.models(sample, opposition), mm.models(days, opposition), strict=True
    ):
        ax.plot(sample, track.longitude, track.style, color=track.color, lw=2, label=track.name)
        residuals.plot(
            days,
            mm.wrapped(at_records.longitude - longitude),
            linestyle="none",
            marker="o",
            ms=3.5,
            color=track.color,
        )
    ax.scatter(
        days[timed], longitude[timed], zorder=8, s=26, c="#22262e", label="Reductions, printed hour"
    )
    ax.scatter(
        days[~timed],
        longitude[~timed],
        zorder=8,
        s=26,
        facecolors="white",
        edgecolors="#22262e",
        label="Reductions, nominal noon",
    )
    ax.set(ylabel="Ecliptic longitude (degrees)", title="Mars reverses direction in 1595")
    ax.legend(ncols=2, frameon=False, loc="upper right", fontsize=9)
    residuals.axhline(0, color="#89939f", lw=0.8)
    residuals.set(ylabel="Model − log (degrees)", xlabel="1595 date (Julian calendar)")
    for panel in (ax, residuals):
        panel.axvline(0, color="#89939f", lw=1, alpha=0.65)
        panel.grid(alpha=0.18)
        panel.spines[["top", "right"]].set_visible(False)
    ticks = [-54, -31, -16, 0, 15, 30, 53]
    residuals.set_xticks(ticks, [label(opposition, d) for d in ticks])
    fig.savefig(output / "mars-1595-motion.png", dpi=170)
    plt.close(fig)


def label(opposition, days):
    return opposition.date_label(days).strftime("%b %d").replace(" 0", " ")


def plot_geometry(plt, output, opposition):
    span = np.linspace(-140, 160, 601)
    snapshots = np.array([-36.0, 0.0, 36.0])
    fig, axes = plt.subplots(2, 2, figsize=(9, 8.7), layout="constrained")
    for ax, track, positions in zip(
        axes.flat, mm.models(span, opposition), mm.models(snapshots, opposition), strict=True
    ):
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


def plot_sky(plt, output, opposition, rows):
    modern = mm.models(np.linspace(-57, 56, 1131), opposition)[-1]
    paired = [row for row in rows if row["latitude_arcseconds_exact"]]
    fig, ax = plt.subplots(figsize=(8.5, 4), layout="constrained")
    ax.plot(
        modern.longitude, modern.latitude, color=modern.color, lw=2, label="Modern Keplerian track"
    )
    ax.scatter(
        [float(Fraction(row["longitude_degrees_exact"])) for row in paired],
        [float(Fraction(row["latitude_arcseconds_exact"])) / 3600 for row in paired],
        color="#22262e",
        zorder=5,
        s=27,
        label="Tycho's paired reductions",
    )
    for day in (-43, 0, 53):
        track = mm.models([day], opposition)[-1]
        ax.annotate(
            label(opposition, day),
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
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tables-only", action="store_true", help="skip the figures")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    opposition, rows = write_tables(args.output)
    if args.tables_only:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 11, "axes.titleweight": "bold", "axes.labelcolor": "#263445"})
    plot_motion(plt, args.output, opposition, rows)
    plot_geometry(plt, args.output, opposition)
    plot_sky(plt, args.output, opposition, rows)


if __name__ == "__main__":
    main()
