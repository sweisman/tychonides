"""Compare historical refraction tables with a modern refraction formula.

The tables come from refraction-tables.csv beside this script, which
refraction_select.py builds from the catalog. The modern value is Bennett's
formula for apparent altitude, scaled for pressure and temperature. The script
runs offline and needs NumPy for the tables and Matplotlib for the figure.
"""

import argparse
import csv
from fractions import Fraction
from itertools import pairwise
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
STANDARD = (1010.0, 10.0)  # Pressure in hPa and temperature in degrees Celsius.
COLD = (1030.0, -10.0)
WARM = (1000.0, 20.0)
ARCSECONDS = 206264.80624709636
TYCHO_SOLAR_DISTANCE = 1146.0  # Earth radii, giving his three-minute horizontal parallax.
MODERN_SOLAR_PARALLAX = 8.794  # Arcseconds.
CHECK_ALTITUDES = (0, 5, 10, 15, 20, 26, 30, 45)
SEASONS = {"": "", "summer": " summer", "equinoctial": " equinoctial", "winter": " winter"}


def bennett(altitude, pressure=STANDARD[0], temperature=STANDARD[1]):
    """Refraction in arcseconds at an apparent altitude in degrees (Bennett 1982)."""
    altitude = np.asarray(altitude, dtype=float)
    standard = 60 / np.tan(np.deg2rad(altitude + 7.31 / (altitude + 4.4)))
    return standard * (pressure / 1010) * (283 / (273 + temperature))


def altitude_parallax(altitude, horizontal):
    """Parallax in altitude, in arcseconds, for a horizontal parallax in arcseconds."""
    return horizontal * np.cos(np.deg2rad(np.asarray(altitude, dtype=float)))


def load(path=HERE / "refraction-tables.csv"):
    """Tables keyed by author, body, and season, each a sorted list of entries."""
    tables = {}
    with path.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            row["altitude"] = float(Fraction(row["altitude_degrees"]))
            row["refraction"] = float(Fraction(row["refraction_arcseconds_exact"]))
            tables.setdefault((row["author"], row["body"], row["season"]), []).append(row)
    for rows in tables.values():
        rows.sort(key=lambda row: row["altitude"])
    return tables


def compare(tables):
    comparison, summary = [], []
    tycho_parallax = ARCSECONDS * np.arcsin(1 / TYCHO_SOLAR_DISTANCE)
    for (author, body, season), rows in tables.items():
        altitude = np.array([row["altitude"] for row in rows])
        printed = np.array([row["refraction"] for row in rows])
        modern = bennett(altitude)
        difference = printed - modern
        for index, row in enumerate(rows):
            line = {
                "author": author,
                "source_id": row["source_id"],
                "printed_page": row["printed_page"],
                "body": body,
                "season": season,
                "altitude_degrees": row["altitude_degrees"],
                "expression": row["expression"],
                "quantity_id": row["quantity_id"],
                "table_arcseconds": f"{printed[index]:.1f}",
                "modern_arcseconds": f"{modern[index]:.1f}",
                "table_minus_modern_arcseconds": f"{difference[index]:.1f}",
                "modern_cold_arcseconds": f"{bennett(altitude[index], *COLD):.1f}",
                "modern_warm_arcseconds": f"{bennett(altitude[index], *WARM):.1f}",
            }
            if author == "Tycho" and body == "Sun":
                historical = printed[index] - altitude_parallax(altitude[index], tycho_parallax)
                current = modern[index] - altitude_parallax(altitude[index], MODERN_SOLAR_PARALLAX)
                line["tycho_refraction_minus_parallax_arcseconds"] = f"{historical:.1f}"
                line["modern_refraction_minus_parallax_arcseconds"] = f"{current:.1f}"
            comparison.append(line)
        zero = altitude[printed == 0]
        line = {
            "author": author,
            "body": body,
            "season": season,
            "entries": len(rows),
            "highest_altitude_degrees": f"{altitude.max():g}",
            "first_altitude_with_zero_degrees": f"{zero.min():g}" if len(zero) else "",
            "rms_difference_arcseconds": f"{np.sqrt(np.mean(difference**2)):.1f}",
        }
        for check in CHECK_ALTITUDES:
            at = np.flatnonzero(altitude == check)
            line[f"difference_at_{check}_arcseconds"] = (
                f"{difference[at[0]]:.1f}" if len(at) else ""
            )
        summary.append(line)
    return comparison, summary


def seasonal(tables):
    """Riccioli's winter and summer tables against each other."""
    lines = []
    for body in ("Sun", "Moon", "fixed stars"):
        winter = {
            row["altitude"]: row["refraction"] for row in tables[("Riccioli", body, "winter")]
        }
        summer = {
            row["altitude"]: row["refraction"] for row in tables[("Riccioli", body, "summer")]
        }
        for altitude in sorted(set(winter) & set(summer)):
            if summer[altitude] > 0:
                lines.append(
                    {
                        "body": body,
                        "altitude_degrees": f"{altitude:g}",
                        "winter_arcseconds": f"{winter[altitude]:.0f}",
                        "summer_arcseconds": f"{summer[altitude]:.0f}",
                        "winter_over_summer": f"{winter[altitude] / summer[altitude]:.3f}",
                    }
                )
    return lines


def derivation_check(tables):
    """Riccioli's solar tables beside Tycho's solar table less Tycho's solar parallax."""
    tycho = {row["altitude"]: row["refraction"] for row in tables[("Tycho", "Sun", "")]}
    horizontal = ARCSECONDS * np.arcsin(1 / TYCHO_SOLAR_DISTANCE)
    lines = []
    for season in ("summer", "equinoctial", "winter"):
        for row in tables[("Riccioli", "Sun", season)]:
            altitude = row["altitude"]
            if altitude not in tycho:
                continue
            reduced = tycho[altitude] - altitude_parallax(altitude, horizontal)
            lines.append(
                {
                    "season": season,
                    "altitude_degrees": f"{altitude:g}",
                    "riccioli_arcseconds": f"{row['refraction']:.0f}",
                    "tycho_arcseconds": f"{tycho[altitude]:.0f}",
                    "tycho_less_his_parallax_arcseconds": f"{reduced:.1f}",
                    "riccioli_minus_that_arcseconds": f"{row['refraction'] - reduced:.1f}",
                }
            )
    return lines


def sequence_breaks(tables):
    """Entries larger than the entry one step lower in the same table."""
    lines = []
    for (author, body, season), rows in tables.items():
        for lower, row in pairwise(rows):
            if row["refraction"] > lower["refraction"]:
                lines.append(
                    {
                        "author": author,
                        "body": body,
                        "season": season,
                        "altitude_degrees": row["altitude_degrees"],
                        "expression": row["expression"],
                        "arcseconds": f"{row['refraction']:.0f}",
                        "entry_below_arcseconds": f"{lower['refraction']:.0f}",
                        "quantity_id": row["quantity_id"],
                    }
                )
    return lines


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_tables(output):
    """Write every numerical output. Needs NumPy only."""
    tables = load()
    comparison, summary = compare(tables)
    write_csv(output / "refraction-tables-comparison.csv", comparison)
    write_csv(output / "refraction-tables-summary.csv", summary)
    write_csv(output / "refraction-tables-seasons.csv", seasonal(tables))
    write_csv(output / "refraction-tables-derivation.csv", derivation_check(tables))
    write_csv(output / "refraction-tables-sequence.csv", sequence_breaks(tables))
    return tables


def plot(plt, output, tables):
    shown = (
        (("Tycho", "Sun", ""), "Tycho, Sun", "#984481", "o"),
        (("Tycho", "fixed stars", ""), "Tycho, fixed stars", "#07678a", "s"),
        (("Riccioli", "Sun", "equinoctial"), "Riccioli, Sun, equinoctial", "#996019", "^"),
        (
            ("Riccioli", "fixed stars", "equinoctial"),
            "Riccioli, fixed stars, equinoctial",
            "#276b4c",
            "v",
        ),
    )
    fig, (values, gaps) = plt.subplots(1, 2, figsize=(11, 4.6), layout="constrained")
    grid = np.linspace(0, 45, 451)
    values.fill_between(
        grid,
        bennett(grid, *WARM) / 60,
        bennett(grid, *COLD) / 60,
        color="#b9c2cc",
        label="Modern, warm to cold air",
    )
    values.plot(grid, bennett(grid) / 60, color="#22262e", lw=1.2, label="Modern, standard air")
    for key, name, color, marker in shown:
        altitude = np.array([row["altitude"] for row in tables[key]])
        printed = np.array([row["refraction"] for row in tables[key]])
        values.plot(altitude, printed / 60, marker, ms=3.5, color=color, label=name)
        gaps.plot(
            altitude, (printed - bennett(altitude)) / 60, marker + "-", ms=3.5, lw=0.8, color=color
        )
    gaps.fill_between(
        grid,
        (bennett(grid, *WARM) - bennett(grid)) / 60,
        (bennett(grid, *COLD) - bennett(grid)) / 60,
        color="#b9c2cc",
    )
    gaps.axhline(0, color="#22262e", lw=1.2)
    values.set(xlabel="Apparent altitude (degrees)", ylabel="Refraction (arcminutes)")
    values.set_title("Printed tables and modern refraction")
    values.set_yscale("symlog", linthresh=1)
    values.set_yticks([0, 1, 2, 5, 10, 20, 30], ["0", "1", "2", "5", "10", "20", "30"])
    values.legend(frameon=False, fontsize=8.5)
    gaps.set(xlabel="Apparent altitude (degrees)", ylabel="Table − modern (arcminutes)")
    gaps.set_title("Difference from modern standard air")
    for panel in (values, gaps):
        panel.grid(alpha=0.18)
        panel.spines[["top", "right"]].set_visible(False)
    fig.savefig(output / "refraction-tables.png", dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tables-only", action="store_true", help="skip the figure")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    tables = write_tables(args.output)
    if args.tables_only:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 11, "axes.titleweight": "bold", "axes.labelcolor": "#263445"})
    plot(plt, args.output, tables)


if __name__ == "__main__":
    main()
