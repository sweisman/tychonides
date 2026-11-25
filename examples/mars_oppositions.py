"""Repeat the 1595 Mars comparison at every opposition covered by Tycho's logs.

The selection, time, and anchor rules are the ones fixed for 1595 in
mars_select.py and mars_model.py. Nothing here is tuned per opposition. The
script runs offline from the CSV files beside it.
"""

import argparse
from datetime import date
from pathlib import Path

import mars_1595 as study
import mars_model as mm
import numpy as np

MAIN_SET_DATES = 11  # An opposition with fewer dated nights is reported as sparse.
# The catalog records no calendar for these entries, and their dates read as Gregorian.
CALENDAR_UNRECORDED = {"X"}
FLAG_ARCMIN = 30  # Rows this far from the ephemeris are counted for review, not removed.
VARIANTS = (
    ("baseline", {}),
    ("every date read as Gregorian", {"calendar": -10.0}),
    ("every row at local noon", {"time": "noon"}),
    ("mean Sun opposite Mars at the anchor", {"mean_sun": "opposite Mars"}),
    ("apsidal line 20 degrees earlier", {"apogee_shift": -20.0}),
    ("apsidal line 10 degrees earlier", {"apogee_shift": -10.0}),
    ("apsidal line 10 degrees later", {"apogee_shift": 10.0}),
)
RESULT_KEEP = [
    "opposition", "julian_date", "daypart", "source_id", "printed_page", "longitude_id", "role",
    "longitude_expression", "longitude_degrees_exact", "date_weight", "epoch_expression",
]  # fmt: skip
COLORS = {
    "ptolemaic": "#996019",
    "copernican": "#07678a",
    "tychonic": "#984481",
    "modern": "#276b4c",
    "de441": "#22262e",
}
NAMES = {
    "ptolemaic": "Ptolemaic equant",
    "copernican": "Copernican circles",
    "tychonic": "Tychonic (Longomontanus)",
    "modern": "Modern Keplerian",
    "de441": "JPL DE441",
}
PRINTED = {"Alphonsine": "#996019", "Copernicus": "#07678a", "Prutenic": "#3aa0c4"}


def rms(values, weights):
    return f"{mm.weighted_rms(values, weights):.3f}" if len(values) else ""


def mean_arcmin(values, weights):
    return f"{np.average(values, weights=weights) * 60:.2f}" if len(values) else ""


def analyze(number):
    """Residuals of every construction for one opposition, in degrees."""
    opposition, rows, _ = study.load(number)
    days, longitude, weights, timed = mm.arrays(rows, opposition)
    tracks = mm.models(days, opposition)
    residuals = {track.key: mm.wrapped(track.longitude - longitude) for track in tracks}
    residuals["de441"] = mm.wrapped(np.array([row["de441_longitude"] for row in rows]) - longitude)
    return opposition, rows, days, longitude, weights, timed, tracks, residuals


def run(numbers):
    results, summary, sensitivity, predictions, printed_summary = [], [], [], [], []
    panels = {}
    for number in numbers:
        opposition, rows, days, longitude, weights, timed, tracks, residuals = analyze(number)
        dates = sorted({row["julian_date"] for row in rows})
        if number in CALENDAR_UNRECORDED:
            group = "calendar unrecorded"
        else:
            group = "main" if len(dates) >= MAIN_SET_DATES else "sparse"
        shared = {
            "opposition": number,
            "opposition_date": opposition.day.isoformat(),
            "set": group,
            "rows": len(rows),
            "dates": len(dates),
            "rows_with_usable_hour": int(timed.sum()),
            "rows_far_from_de441": int((np.abs(residuals["de441"]) * 60 > FLAG_ARCMIN).sum()),
        }
        for index, row in enumerate(rows):
            result = {name: row[name] for name in RESULT_KEEP}
            result |= {
                "time_basis": row["time_basis"],
                "days_from_opposition": f"{days[index]:.4f}",
            }
            for key, values in residuals.items():
                result[f"{key}_minus_log_arcmin"] = f"{values[index] * 60:.2f}"
            results.append(result)
        described = {track.key: mm.describe(track, opposition) for track in tracks}
        for key, values in residuals.items():
            summary.append(
                {
                    **shared,
                    "model": key,
                    "retrograde_span_degrees": described.get(key, {}).get(
                        "retrograde_span_degrees", ""
                    ),
                    "rms_degrees": rms(values, weights),
                    "rms_timed_degrees": rms(values[timed], weights[timed]),
                    "mean_timed_arcmin": mean_arcmin(values[timed], weights[timed]),
                    "median_absolute_arcmin": f"{np.median(np.abs(values)) * 60:.2f}",
                }
            )
        noon = np.array(
            [mm.jd_ut(date.fromisoformat(row["julian_date"]), 12.0) - opposition.jd for row in rows]
        )
        for name, options in VARIANTS:
            options = dict(options)
            when = (noon if options.pop("time", None) else days) + options.pop("calendar", 0.0)
            line = {"opposition": number, "set": group, "variant": name}
            for track in mm.models(when, opposition, **options):
                values = mm.wrapped(track.longitude - longitude)
                line[f"{track.key}_rms_degrees"] = rms(values, weights)
            sensitivity.append(line)
        compared = study.compare_predictions(opposition, rows)
        for item in compared:
            predictions.append({"opposition": number, **item})
        for model in sorted({item["model"] for item in compared}):
            printed = [item for item in compared if item["model"] == model]
            matched = [item for item in printed if item.get("prediction_minus_log_arcmin")]
            line = {
                "opposition": number,
                "opposition_date": opposition.day.isoformat(),
                "set": group,
                "model": model,
                "predictions": len(printed),
                "with_a_reduction_on_the_date": len(matched),
            }
            for reference in ("log", "de441"):
                gaps = np.array(
                    [float(item[f"prediction_minus_{reference}_arcmin"]) for item in matched]
                )
                if len(gaps):
                    line[f"mean_minus_{reference}_arcmin"] = f"{gaps.mean():.1f}"
                    line[f"median_absolute_minus_{reference}_arcmin"] = (
                        f"{np.median(np.abs(gaps)):.1f}"
                    )
            printed_summary.append(line)
        panels[number] = (opposition, days, timed, residuals, group)
    return results, summary, sensitivity, predictions, printed_summary, panels


def write_tables(output):
    """Write every numerical output. Needs NumPy only."""
    oppositions = mm.load_oppositions()
    numbers = [number for number in oppositions if mm.load_observations(number)]
    results, summary, sensitivity, predictions, printed_summary, panels = run(numbers)
    study.write_csv(
        output / "mars-oppositions-prediction-summary.csv",
        [
            "opposition",
            "opposition_date",
            "set",
            "model",
            "predictions",
            "with_a_reduction_on_the_date",
            "mean_minus_log_arcmin",
            "median_absolute_minus_log_arcmin",
            "mean_minus_de441_arcmin",
            "median_absolute_minus_de441_arcmin",
        ],
        printed_summary,
    )
    study.write_csv(output / "mars-oppositions-results.csv", list(results[0]), results)
    study.write_csv(output / "mars-oppositions-summary.csv", list(summary[0]), summary)
    study.write_csv(output / "mars-oppositions-sensitivity.csv", list(sensitivity[0]), sensitivity)
    study.write_csv(
        output / "mars-oppositions-predictions.csv",
        ["opposition", *study.PREDICTION_FIELDS],
        predictions,
    )
    return predictions, panels


def plot_residuals(plt, output, panels):
    chosen = [number for number, panel in panels.items() if panel[4] != "sparse"]
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.8), sharex=True, layout="constrained")
    for ax, number in zip(axes.flat, chosen, strict=True):
        opposition, days, timed, residuals, group = panels[number]
        for key, values in residuals.items():
            for mask, fill in ((timed, COLORS[key]), (~timed, "white")):
                ax.scatter(
                    days[mask],
                    values[mask],
                    s=17,
                    facecolors=fill,
                    edgecolors=COLORS[key],
                    linewidths=1,
                    zorder=5 if key == "de441" else 3,
                    label=NAMES[key] if mask is timed else None,
                )
        ax.axhline(0, color="#89939f", lw=0.8)
        ax.axvline(0, color="#89939f", lw=0.8, alpha=0.6)
        note = "calendar not recorded" if group != "main" else f"opposition {opposition.label[5:]}"
        ax.set_title(f"{opposition.day.year}  ({note})", fontsize=11)
        ax.grid(alpha=0.18)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0, 0].legend(frameon=False, fontsize=8, loc="lower left")
    fig.supxlabel("Days from opposition")
    fig.supylabel("Model − log (degrees)")
    fig.suptitle("Six oppositions under one set of rules", fontsize=16)
    fig.savefig(output / "mars-oppositions-residuals.png", dpi=170)
    plt.close(fig)


def plot_predictions(plt, output, predictions):
    fig, ax = plt.subplots(figsize=(9, 4.4), layout="constrained")
    for model, color in PRINTED.items():
        points = [
            (date.fromisoformat(item["julian_date"]), float(item["prediction_minus_log_arcmin"]))
            for item in predictions
            if item["model"] == model
            and item.get("prediction_minus_log_arcmin")
            and item["opposition"] not in CALENDAR_UNRECORDED
        ]
        when = [day.year + (day.timetuple().tm_yday - 1) / 365.25 for day, _ in points]
        ax.scatter(
            when, [gap / 60 for _, gap in points], s=22, color=color, label=model, alpha=0.85
        )
    ax.axhline(0, color="#89939f", lw=0.8)
    ax.set_xticks(range(1580, 1600, 2))
    ax.set(
        xlabel="Julian year",
        ylabel="Printed prediction − log (degrees)",
        title="Table predictions printed beside the Mars reductions",
    )
    ax.legend(frameon=False, ncols=3, loc="lower left")
    ax.grid(alpha=0.18)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(output / "mars-oppositions-predictions.png", dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tables-only", action="store_true", help="skip the figures")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    predictions, panels = write_tables(args.output)
    if args.tables_only:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 11, "axes.titleweight": "bold", "axes.labelcolor": "#263445"})
    plot_residuals(plt, args.output, panels)
    plot_predictions(plt, args.output, predictions)


if __name__ == "__main__":
    main()
