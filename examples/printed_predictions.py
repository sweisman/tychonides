"""Compare every printed model prediction in Tycho's logs with the log and with JPL DE441.

The inputs are the files written by predictions_select.py and
predictions_ephemeris.py, so this script runs offline:

    python examples/printed_predictions.py --output docs/figures

Each prediction is set beside the log's own values for the same body and
quantity on the same date, and beside the apparent geocentric position of date
from DE441. The ephemeris is evaluated at the instants of the log's values,
then at the printed hour of the calculation itself, and at local noon when the
log prints no usable hour. A separate table measures DE441 itself against the
log on the dates where the log prints every hour.
The tables need NumPy. The figure needs Matplotlib.
"""

import argparse
import csv
from collections import defaultdict
from datetime import date
from fractions import Fraction
from pathlib import Path

import mars_model as mm
import numpy as np

HERE = Path(__file__).parent
TARGETS = {
    "Moon": "301",
    "Mercury": "199",
    "Venus": "299",
    "Mars": "4",
    "Jupiter": "5",
    "Saturn": "6",
}
CALENDAR_OPEN_FROM = 1599  # Tycho reached Prague in June 1599, where both calendars were in use.
WINDOW_DAYS = 60  # The window of the Mars opposition studies.
REVIEW_DEGREES = 10  # A longitude this far from the ephemeris puts its date or body in question.
MODELS = (
    "Alphonsine",
    "Copernicus",
    "Prutenic",
    "Prutenic, corrected",
    "Stadius",
    "Leovitius",
    "Maestlin",
    "Carelli",
)
STYLES = {  # Color and marker for each table or ephemeris with a longitude in the figure.
    "Alphonsine": ("#996019", "o"),
    "Copernicus": ("#00699a", "s"),
    "Prutenic": ("#3a9cc4", "^"),
    "Stadius": ("#7a5195", "D"),
    "Leovitius": ("#c8553d", "v"),
    "Maestlin": ("#3d4fb8", "X"),
    "Carelli": ("#12a089", "P"),
}
RESULT_FIELDS = [
    "id",
    "source_id",
    "printed_page",
    "body",
    "quantity",
    "model",
    "julian_date",
    "set",
    "review",
    "basis",
    "prediction_degrees",
    "log_values",
    "log_values_with_printed_hour",
    "log_degrees",
    "de441_degrees",
    "de441_time_basis",
    "de441_change_in_12_hours_arcmin",
    "prediction_minus_log_arcmin",
    "prediction_minus_de441_arcmin",
    "log_minus_de441_arcmin",
]
SUMMARY_FIELDS = [
    "body",
    "quantity",
    "model",
    "set",
    "predictions",
    "flagged_for_review",
    "with_a_log_value",
    "timed",
    "mean_minus_log_arcmin",
    "median_absolute_minus_log_arcmin",
    "largest_absolute_minus_log_arcmin",
    "mean_minus_de441_arcmin",
    "median_absolute_minus_de441_arcmin",
    "largest_absolute_minus_de441_arcmin",
    "median_absolute_minus_de441_timed_arcmin",
    "median_absolute_log_minus_de441_timed_arcmin",
]
CHECK_FIELDS = [
    "body",
    "quantity",
    "set",
    "dates",
    "mean_de441_minus_log_arcmin",
    "median_absolute_de441_minus_log_arcmin",
    "largest_absolute_de441_minus_log_arcmin",
]


def read(name):
    with (HERE / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def noon(day):
    return mm.jd_ut(day, 12.0)


def instant(row):
    """UT Julian date of a log value and whether the log prints its hour."""
    hours, basis = mm.clock(row["daypart"], row["epoch_seconds"])
    return mm.jd_ut(date.fromisoformat(row["julian_date"]), hours), basis.startswith("printed")


def calculation_instant(item):
    """UT Julian date of the calculation hour printed with a prediction, or None.

    The hour follows the rule for a log value. An hour whose label leaves its origin open,
    such as "4h A.M.", is not used.
    """
    if not item.get("epoch_seconds"):
        return None
    hours, basis = mm.clock(item["daypart"], item["epoch_seconds"])
    if not basis.startswith("printed"):
        return None
    return mm.jd_ut(date.fromisoformat(item["julian_date"]), hours)


def instants():
    """Every UT Julian date the study needs from the ephemeris, by body."""
    wanted = defaultdict(set)
    for row in read("printed-predictions.csv"):
        base = noon(date.fromisoformat(row["julian_date"]))
        wanted[row["body"]] |= {f"{base:.6f}", f"{base + 0.5:.6f}"}
        if calculation_instant(row) is not None:
            wanted[row["body"]].add(f"{calculation_instant(row):.6f}")
    for row in read("printed-predictions-references.csv"):
        wanted[row["body"]].add(f"{instant(row)[0]:.6f}")
    return {body: sorted(wanted[body]) for body in TARGETS if body in wanted}


def load_ephemeris():
    return {
        (row["body"], row["jd_ut"]): (
            float(row["longitude_degrees"]),
            float(row["latitude_degrees"]),
        )
        for row in read("printed-predictions-ephemeris.csv")
    }


def mean_angle(values, weights):
    """Weighted mean of angles in degrees that may straddle 0."""
    values, weights = np.array(values, dtype=float), np.array(weights, dtype=float)
    return values[0] + float(np.sum(weights * mm.wrapped(values - values[0])) / np.sum(weights))


def gap(value, reference, basis):
    """Difference in degrees, taken within the sign when no zodiac sign is printed."""
    if basis == "within the sign":
        return (value - reference + 15) % 30 - 15
    return float(mm.wrapped(value - reference))


def group(item, day, windows):
    if day.year >= CALENDAR_OPEN_FROM and not item["calendar_label"]:
        return "calendar unrecorded"
    if item["body"] != "Mars":
        return "main"
    near = any(abs((day - center).days) <= WINDOW_DAYS for center in windows)
    return "near opposition" if near else "away from opposition"


def compare():
    """One row per prediction, with differences in arcminutes."""
    ephemeris = load_ephemeris()
    windows = [item.day for item in mm.load_oppositions().values()]
    references = defaultdict(list)
    for row in read("printed-predictions-references.csv"):
        references[(row["body"], row["quantity"], row["julian_date"])].append(row)
    table = []
    for item in read("printed-predictions.csv"):
        column = 0 if item["quantity"] == "ecliptic_longitude" else 1
        day = date.fromisoformat(item["julian_date"])
        value = float(Fraction(item["degrees_exact"]))
        base = noon(day)
        at_noon = ephemeris[(item["body"], f"{base:.6f}")][column]
        later = ephemeris[(item["body"], f"{base + 0.5:.6f}")][column]
        same = references.get((item["body"], item["quantity"], item["julian_date"]), [])
        result = {name: item.get(name, "") for name in RESULT_FIELDS}
        result |= {
            "set": group(item, day, windows),
            "prediction_degrees": f"{value:.6f}",
            "log_values": len(same),
            "de441_change_in_12_hours_arcmin": f"{abs(mm.wrapped(later - at_noon)) * 60:.1f}",
        }
        modern, printed = at_noon, 0
        if same:
            weights = [float(Fraction(row["date_weight"])) for row in same]
            times = [instant(row) for row in same]
            printed = sum(timed for _, timed in times)
            log = mean_angle([float(Fraction(row["degrees_exact"])) for row in same], weights)
            modern = mean_angle(
                [ephemeris[(item["body"], f"{jd:.6f}")][column] for jd, _ in times], weights
            )
            result["log_degrees"] = f"{log:.6f}"
        timed = bool(same) and printed == len(same)
        own = calculation_instant(item)
        if own is not None and not timed:
            # The prediction was computed for this hour, so both comparisons are read there.
            modern, timed = ephemeris[(item["body"], f"{own:.6f}")][column], True
            result["de441_time_basis"] = "calculation hour"
        else:
            result["de441_time_basis"] = (
                "printed hours"
                if timed
                else "nominal noon"
                if same
                else "nominal noon, no log value"
            )
        result["log_values_with_printed_hour"] = printed
        if item["body"] == "Moon" and not timed:
            # The Moon moves about half a degree an hour, so it needs a printed hour.
            result["de441_time_basis"] = "not compared, no printed hour"
            result["log_degrees"] = ""
        else:
            result["de441_degrees"] = f"{modern:.6f}"
            result["prediction_minus_de441_arcmin"] = (
                f"{gap(value, modern, item['basis']) * 60:.2f}"
            )
            if same:
                result |= {
                    "prediction_minus_log_arcmin": f"{gap(value, log, item['basis']) * 60:.2f}",
                    "log_minus_de441_arcmin": f"{mm.wrapped(log - modern) * 60:.2f}",
                }
        table.append(result)
    # A longitude far from the ephemeris flags every prediction of that body in its printed entry.
    doubtful = {
        entry(row)
        for row in table
        if row["quantity"] == "ecliptic_longitude"
        and row["prediction_minus_de441_arcmin"]
        and abs(float(row["prediction_minus_de441_arcmin"])) > REVIEW_DEGREES * 60
    }
    for row in table:
        row["review"] = "date or body in question" if entry(row) in doubtful else ""
    return table


def entry(row):
    return row["source_id"], row["printed_page"], row["body"], row["julian_date"]


def column(rows, name):
    return np.array([float(row[name]) for row in rows if row[name] != ""])


def summarize(table):
    groups = defaultdict(list)
    for row in table:
        groups[(row["body"], row["quantity"], row["model"], row["set"])].append(row)
    order = {name: index for index, name in enumerate([*TARGETS, *MODELS])}
    summary = []
    for key in sorted(groups, key=lambda item: (order[item[0]], item[1], order[item[2]], item[3])):
        line = dict(zip(("body", "quantity", "model", "set"), key, strict=True))
        line |= {
            "predictions": len(groups[key]),
            "flagged_for_review": sum(bool(row["review"]) for row in groups[key]),
        }
        # The statistics leave out the rows flagged for review.
        rows = [row for row in groups[key] if not row["review"]]
        timed = [
            row for row in rows if row["de441_time_basis"] in ("printed hours", "calculation hour")
        ]
        line |= {
            "with_a_log_value": sum(row["log_values"] > 0 for row in rows),
            "timed": len(timed),
        }
        for reference in ("log", "de441"):
            gaps = column(rows, f"prediction_minus_{reference}_arcmin")
            if len(gaps):
                line |= {
                    f"mean_minus_{reference}_arcmin": f"{gaps.mean():.1f}",
                    f"median_absolute_minus_{reference}_arcmin": f"{np.median(np.abs(gaps)):.1f}",
                    f"largest_absolute_minus_{reference}_arcmin": f"{np.abs(gaps).max():.1f}",
                }
        for name, source in (
            ("median_absolute_minus_de441_timed_arcmin", "prediction_minus_de441_arcmin"),
            ("median_absolute_log_minus_de441_timed_arcmin", "log_minus_de441_arcmin"),
        ):
            gaps = column(timed, source)
            if len(gaps):
                line[name] = f"{np.median(np.abs(gaps)):.1f}"
        summary.append(line)
    return summary


def ephemeris_check(table):
    """DE441 minus the log, once for each date on which the log prints every hour.

    Only those dates read the ephemeris at the instants of the observations. Several
    predictions for one date share one log value, so the date counts once.
    """
    dates = {}
    for row in table:
        if row["de441_time_basis"] == "printed hours" and not row["review"]:
            key = (row["body"], row["quantity"], row["set"], row["julian_date"])
            dates[key] = -float(row["log_minus_de441_arcmin"])
    groups = defaultdict(list)
    for (body, quantity, name, _), difference in dates.items():
        groups[(body, quantity, name)].append(difference)
    order = {name: index for index, name in enumerate(TARGETS)}
    check = []
    for key in sorted(groups, key=lambda item: (order[item[0]], item[1], item[2])):
        gaps = np.array(groups[key])
        line = dict(zip(("body", "quantity", "set"), key, strict=True))
        line |= {
            "dates": len(gaps),
            "mean_de441_minus_log_arcmin": f"{gaps.mean():.1f}",
            "median_absolute_de441_minus_log_arcmin": f"{np.median(np.abs(gaps)):.1f}",
            "largest_absolute_de441_minus_log_arcmin": f"{np.abs(gaps).max():.1f}",
        }
        check.append(line)
    return check


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_tables(output):
    """Write every numerical output. Needs NumPy only."""
    table = compare()
    write_csv(output / "printed-predictions-results.csv", RESULT_FIELDS, table)
    write_csv(output / "printed-predictions-summary.csv", SUMMARY_FIELDS, summarize(table))
    write_csv(
        output / "printed-predictions-ephemeris-check.csv", CHECK_FIELDS, ephemeris_check(table)
    )
    return table


FIGURE_COLUMNS = [  # Body, set, and label of each column of the figure.
    ("Mercury", "main", "Mercury"),
    ("Venus", "main", "Venus"),
    ("Mars", "away from opposition", "Mars, away from\nopposition"),
    ("Mars", "near opposition", "Mars, near\nopposition"),
    ("Jupiter", "main", "Jupiter"),
    ("Saturn", "main", "Saturn"),
]


def figure_rows(table):
    """The compared longitudes that the figure shows. Each source needs a color and marker."""
    shown = [
        row
        for row in table
        if row["quantity"] == "ecliptic_longitude"
        and not row["review"]
        and row["prediction_minus_de441_arcmin"] != ""
        and any((row["body"], row["set"]) == (body, name) for body, name, _ in FIGURE_COLUMNS)
    ]
    missing = {row["model"] for row in shown} - set(STYLES)
    if missing:
        raise ValueError("No color and marker for " + ", ".join(sorted(missing)))
    return shown


def figure_point(row):
    """Degrees from the log, or from DE441 where the study has no log value, and which it is."""
    if row["prediction_minus_log_arcmin"] != "":
        return float(row["prediction_minus_log_arcmin"]) / 60, "log"
    return float(row["prediction_minus_de441_arcmin"]) / 60, "DE441"


def plot(plt, output, table):
    """Every compared longitude, one column per body and one marker per table or ephemeris."""
    columns = FIGURE_COLUMNS
    shown = figure_rows(table)
    fig, ax = plt.subplots(figsize=(9.5, 5.3), layout="constrained")
    middle = (len(STYLES) - 1) / 2
    for position, (body, name, _) in enumerate(columns):
        for slot, (model, (color, marker)) in enumerate(STYLES.items()):
            points = sorted(
                figure_point(row)
                for row in shown
                if (row["body"], row["set"], row["model"]) == (body, name, model)
            )
            for reference in ("log", "DE441"):
                # Filled from the log. Open from DE441, where the study has no log value.
                across, values = [], []
                for index, (value, measured_from) in enumerate(points):
                    if measured_from == reference:
                        across.append(position + (slot - middle) * 0.12 + (index % 5 - 2) * 0.012)
                        values.append(value)
                filled = reference == "log"
                ax.scatter(
                    across,
                    values,
                    s=30,
                    marker=marker,
                    facecolor=color if filled else "none",
                    edgecolor="white" if filled else color,
                    linewidth=0.5 if filled else 1.2,
                )
        if position:
            ax.axvline(position - 0.5, color="#d5dae0", lw=0.8)
    ax.axhline(0, color="#89939f", lw=0.8)
    ax.set_xticks(range(len(columns)), [label for *_, label in columns])
    ax.set_xlim(-0.5, len(columns) - 0.5)
    ax.set(
        ylabel="Printed longitude − log longitude (degrees)",
        title="Table and ephemeris longitudes printed in the logs, against the log",
    )
    handles = [
        plt.Line2D([], [], ls="", marker=marker, color=color, mec="white", ms=7.5, label=model)
        for model, (color, marker) in STYLES.items()
    ]
    # Below the axes, in one row: seven entries inside the axes would cover points.
    fig.legend(
        handles=handles, frameon=False, ncols=len(handles), loc="outside lower center", fontsize=9.5
    )
    neutral = "#5b6673"
    ax.legend(
        handles=[
            plt.Line2D([], [], ls="", marker="o", color=neutral, mec="white", ms=7.5),
            plt.Line2D([], [], ls="", marker="o", mfc="none", mec=neutral, mew=1.2, ms=6.5),
        ],
        labels=["Measured from the log", "No log value: measured from DE441"],
        frameon=False,
        loc="upper left",
        fontsize=9.5,
    )
    ax.grid(axis="y", alpha=0.18)
    ax.tick_params(axis="x", length=0)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(output / "printed-predictions.png", dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tables-only", action="store_true", help="skip the figure")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    table = write_tables(args.output)
    if args.tables_only:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 11, "axes.titleweight": "bold", "axes.labelcolor": "#263445"})
    plot(plt, args.output, table)


if __name__ == "__main__":
    main()
