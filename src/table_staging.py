"""Lossless table-cell staging with explicit, provisional column interpretations."""

import json
import re
from collections import Counter
from pathlib import Path
from fractions import Fraction

from .catalog import identity, normalize_quantity
from .coordinate_staging import parse_coordinate
from .core import digest, fraction_text, recorded_clock


PATTERNS = {
    "declination": r"\bdecl",
    "altitude": r"\baltit|\balt\.",
    "azimuth": r"\bazim",
    "angular_separation": r"\bdistance\b|\bdist\.|\bdiſt\.|\bbetween\b|\binter\b",
    "ecliptic_longitude": r"\blongit",
    "ecliptic_latitude": r"\blatit",
    "right_ascension": r"right asc|\bascens|\baſcens|\baſc\.",
    "hour_angle": r"hour angle",
    "recorded_clock": r"^time$|^hours|^h\.?\s*m\.?",
}
OBJECTS = [
    ("Mars", r"♂|\bMars\b"),
    ("Moon", r"[☽☾]|\bMoon\b|\bLun[æae]"),
    ("Sun", r"[☉⊙]|\bSun\b"),
    ("Venus", r"♀|\bVenus\b"),
    ("Jupiter", r"♃|\bJupiter\b"),
    ("Saturn", r"♄|\bSaturn\b"),
    ("Mercury", r"☿|\bMercury\b"),
]


def main_text(text):
    return text.split("[", 1)[0].replace("*", "").replace("`", "").strip()


def descriptor(text):
    plain = main_text(text)
    quantities = [q for q, p in PATTERNS.items() if re.search(p, plain, re.I)]
    objects = [name for name, p in OBJECTS if re.search(p, plain, re.I)]
    result = dict(
        quantity=quantities[0] if len(quantities) == 1 else None,
        subject=objects[0] if len(objects) == 1 else None,
        endpoints=[],
        text=text,
        flags=["multiple_quantity_labels"] if len(quantities) > 1 else [],
    )
    if result["quantity"] == "angular_separation":
        match = re.search(
            r"(?:Distance\s+of\s+(.+?)\s+from\s+(.+)|Between\s+(.+?)\s+and\s+(.+))$", plain, re.I
        )
        if match:
            endpoints = [
                s.strip() for s in (match.groups()[:2] if match[1] else match.groups()[2:])
            ]
            result["endpoints"] = endpoints
            named = [name for name, p in OBJECTS if re.fullmatch(p, endpoints[0], re.I)]
            result["subject"] = named[0] if len(named) == 1 else endpoints[0]
    return result


def parse_clock(expression, header):
    result = dict(
        components=None, normalized=normalize_quantity({"quantity": "recorded_clock"}), flags=[]
    )
    if re.search(r"\?|…|\.\.\.", expression):
        result["normalized"] = normalize_quantity(dict(quantity="recorded_clock", incomplete=True))
        return result
    text = main_text(expression)
    if "[" in expression:
        result["flags"].append("parallel_clock_expression_unreviewed")
    norm = fraction_text(text).strip()
    norm = re.sub(r"\s*(?:[AP]\.\s*M\.(?:\s*N\.)?)\s*$", "", norm, flags=re.I)
    token = r"(\d+(?:\s+\d+/\d+)?)"
    explicit = re.fullmatch(
        token + r"\^h\^(?:\s*" + token + r"\^m\^)?(?:\s*" + token + r"\^s\^)?", norm, re.I
    )
    components = None
    if explicit:
        components = {
            u: v
            for u, v in zip(("hour", "minute", "second"), explicit.groups(), strict=True)
            if v is not None
        }
    elif re.fullmatch(r"\d+(?:\s+\d+/\d+)?(?:\s+\d+(?:\s+\d+/\d+)?){1,2}", norm):
        h = main_text(header)
        expected = (
            3
            if re.fullmatch(r"H\.?\s*M\.?\s*S\.?", h, re.I)
            else 2
            if re.fullmatch(r"H\.?\s*M\.?", h, re.I)
            else None
        )
        tokens = re.findall(r"\d+(?:\s+\d+/\d+)?", norm)
        if expected == len(tokens):
            components = dict(zip(("hour", "minute", "second")[: len(tokens)], tokens, strict=True))
    elif norm.startswith("H."):
        value = recorded_clock(norm)
        if value is not None:
            result["normalized"].update(status="exact", magnitude=value, unit="second_of_time")
    if components:
        try:
            normalized = normalize_quantity(dict(quantity="recorded_clock", components=components))
            if normalized["magnitude"] is not None and Fraction(normalized["magnitude"]) >= 86400:
                raise ValueError("Clock component may be a partial minute/second reading")
        except ValueError:
            result["flags"].append("clock_components_unresolved")
        else:
            result.update(components=components, normalized=normalized)
    return result


def split_cells(line):
    text = line.strip().removeprefix("|").removesuffix("|")
    return [c.strip() for c in re.split(r"(?<!\\)\|", text)]


def stage_table(span):
    lines = span["text_original"].splitlines()
    cells = []
    events = []
    headers = []
    header_line = None
    last_label = None
    parts = [split_cells(line) for line in lines]
    separators = [bool(re.fullmatch(r"[| :\-]+", line.strip()) and "---" in line) for line in lines]
    for index, row in enumerate(parts):
        line = span["line_start"] + index
        if separators[index]:
            kind = "delimiter"
        elif index + 1 < len(parts) and separators[index + 1]:
            kind = "header"
            headers = row
            header_line = line
            last_label = None
        else:
            kind = "data"
        row_flags = [] if len(row) == len(headers) else ["row_width_differs"]
        row_label = None
        label_columns = []
        if kind == "data" and not row_flags:
            label_columns = [
                i for i, h in enumerate(headers) if main_text(h).lower() in ("reading", "line")
            ]
            if not label_columns and len(headers) >= 2 and not main_text(headers[0]):
                label_columns = [i for i, s in enumerate(row[:-1]) if descriptor(s)["quantity"]]
            if (
                not label_columns
                and len(headers) == 2
                and main_text(headers[0]).lower() in ("", "reading")
            ):
                label_columns = [0]
            if label_columns:
                label = " ".join(row[i] for i in label_columns).strip()
                candidate = descriptor(label)
                if candidate["quantity"]:
                    row_label = candidate
                    last_label = dict(candidate, line=line)
                elif (
                    not label or re.match(r"^(?:with\b|by\b|the other\b)", main_text(label), re.I)
                ) and last_label:
                    row_label = dict(last_label)
                    row_label["flags"] = [*last_label["flags"], "inherited_row_label"]
                else:
                    last_label = None
        event_id = (
            identity("table-event", span["volume"], span["edition_sha256"], line, "row")
            if kind == "data"
            else None
        )
        clock_id = None
        for column, expression in enumerate(row, 1):
            header = headers[column - 1] if column <= len(headers) else ""
            spec = descriptor(header) if kind == "data" and not row_flags else descriptor("")
            basis = "column_header" if spec["quantity"] else None
            if kind == "data" and not row_flags and column - 1 not in label_columns:
                if not spec["quantity"] and row_label:
                    spec = row_label
                    basis = "row_label"
                own = descriptor(expression)
                if own["quantity"] and own["quantity"] != spec["quantity"]:
                    if spec["quantity"]:
                        own["flags"] = [*own["flags"], "cell_quantity_differs_from_header"]
                    spec = own
                    basis = "cell_label"
            if kind != "data" or row_flags or column - 1 in label_columns:
                spec = descriptor("")
                basis = None
            spec = dict(spec)
            body_targets = (
                [
                    name
                    for name, pattern in OBJECTS
                    if re.search(pattern, main_text(expression), re.I)
                ]
                if kind == "data"
                else []
            )
            targets = sorted(set(([spec["subject"]] if spec["subject"] else []) + body_targets))
            target_conflict = bool(
                spec["quantity"] != "angular_separation"
                and spec["subject"]
                and any(t != spec["subject"] for t in body_targets)
            )
            if target_conflict:
                spec["subject"] = None
            contains = any(c.isnumeric() for c in expression)
            placeholder = bool(re.search(r"\?|…|\.\.\.", expression))
            parsed = dict(
                components=None,
                normalized=normalize_quantity({"quantity": "declination"}),
                flags=[],
            )
            if expression and (contains or placeholder) and spec["quantity"]:
                parsed = (
                    parse_clock(expression, header)
                    if spec["quantity"] == "recorded_clock"
                    else parse_coordinate(expression)
                )
            flags = [*row_flags, *spec["flags"], *parsed["flags"]]
            if target_conflict:
                flags.append("source_target_conflict")
            if kind == "data" and contains:
                flags.append("schema_and_scientific_interpretation_unreviewed")
                if not spec["quantity"]:
                    flags.append("quantity_unresolved")
                elif spec["quantity"] != "recorded_clock" and not spec["subject"]:
                    flags.append("target_unresolved")
                if spec["quantity"] == "angular_separation" and len(spec["endpoints"]) != 2:
                    flags.append("separation_endpoints_unresolved")
            if kind == "data" and not expression:
                flags.append("blank_source_cell")
            role = (
                "model_prediction"
                if re.search(r"Copern|Alphon|Tycho|Kepler", header, re.I)
                else "unreviewed_recorded_value"
            )
            rid = identity("table-cell", span["volume"], span["edition_sha256"], line, str(column))
            record = dict(
                id=rid,
                span_id=span["id"],
                volume=span["volume"],
                edition_sha256=span["edition_sha256"],
                line=line,
                column=column,
                row_kind=kind,
                row_width=len(row),
                header_width=len(headers),
                source_expression=expression,
                header_original=header,
                header_line=header_line,
                label_evidence=spec["text"],
                label_line=spec.get("line", line)
                if basis == "row_label"
                else header_line
                if basis == "column_header"
                else line,
                contains_number=contains,
                quantity_claim=spec["quantity"],
                subject_claim=spec["subject"],
                target_candidates=targets,
                numeric_placeholder=placeholder,
                endpoints=spec["endpoints"],
                role_claim=role,
                quantity_basis=basis,
                components=parsed["components"],
                normalized=parsed["normalized"],
                flags=sorted(set(flags)),
                event_id=event_id,
                printed_pages=span.get("printed_pages", []),
                absolute_timestamp=None,
            )
            cells.append(record)
            if (
                kind == "data"
                and spec["quantity"] == "recorded_clock"
                and parsed["normalized"]["status"] == "exact"
            ):
                clock_id = rid
        if kind == "data":
            events.append(
                dict(
                    id=event_id,
                    span_id=span["id"],
                    volume=span["volume"],
                    line=line,
                    clock_cell_id=clock_id,
                    clock_inherited=False,
                    absolute_timestamp=None,
                    review_status="unreviewed_source_row",
                )
            )
    numeric = [c for c in cells if c["row_kind"] == "data" and c["contains_number"]]
    summary = dict(
        source_cells=len(cells),
        data_rows=len(events),
        numeric_source_cells=len(numeric),
        quantity_claims=dict(
            sorted(Counter(c["quantity_claim"] or "unresolved" for c in numeric).items())
        ),
        normalization_statuses=dict(
            sorted(Counter(c["normalized"]["status"] for c in numeric).items())
        ),
        inspected_spans_added=0,
    )
    return dict(cells=cells, events=events, summary=summary)


def build_tables(source_root, workspace):
    from .io import guard, write_json, write_csv
    from .publication import read_witness

    root = Path(source_root).resolve()
    work = Path(workspace).resolve()
    guard(work, root)
    if (work / "pafko.json").exists() or (work / "raw" / "mars.xls").exists():
        raise ValueError("Protected benchmark workspace")
    names = ("witnesses.json", "inventory_manifest.json", "inventory_spans.jsonl")
    hashes = {n: digest(work / n) for n in names}
    manifest = json.loads((work / "inventory_manifest.json").read_text(encoding="utf-8"))
    editions = {}
    for witness in json.loads((work / "witnesses.json").read_text(encoding="utf-8")):
        volume = witness["volume"]
        v = volume - 9
        relative = f"brahe/thesaurus_observationum_vol{v}/translation/brahe_thesaurus_observationum_vol{v}_prepub.md"
        if witness["private_source"] != relative:
            raise ValueError("Unexpected source path")
        editions[volume] = (
            witness["edition_sha256"],
            read_witness(root, work, witness).splitlines(),
        )
    spans = [
        json.loads(s)
        for s in (work / "inventory_spans.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    cells = []
    events = []
    tables = []
    for span in spans:
        if span["block_kind"] != "table":
            continue
        sha, source_lines = editions[span["volume"]]
        if (
            span["edition_sha256"] != sha
            or "\n".join(source_lines[span["line_start"] - 1 : span["line_end"]])
            != span["text_original"]
        ):
            raise ValueError("Table fingerprint or source binding mismatch")
        staged = stage_table(span)
        cells.extend(staged["cells"])
        events.extend(staged["events"])
        tables.append(dict(span_id=span["id"], volume=span["volume"], **staged["summary"]))
    for relative, sha in manifest["source_hashes"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or digest(path) != sha:
            raise ValueError("Source fingerprint changed")
    if any(digest(work / n) != sha for n, sha in hashes.items()):
        raise ValueError("Inventory input fingerprint changed")
    numeric = [c for c in cells if c["row_kind"] == "data" and c["contains_number"]]
    summary = dict(
        status="table_cell_staging_not_reviewed_catalogue",
        table_spans=len(tables),
        tables_by_volume=dict(sorted(Counter(t["volume"] for t in tables).items())),
        source_cells=len(cells),
        data_rows=len(events),
        numeric_source_cells=len(numeric),
        quantity_claims=dict(
            sorted(Counter(c["quantity_claim"] or "unresolved" for c in numeric).items())
        ),
        normalization_statuses=dict(
            sorted(Counter(c["normalized"]["status"] for c in numeric).items())
        ),
        inspected_spans_added=0,
        measurement_count=None,
        limits=[
            "Cells and rows are not independent observations",
            "Column/target/role interpretations remain provisional",
            "Blank cells, mismatched widths and unsupported expressions are retained",
            "Table staging is not complete Mars coverage",
        ],
    )
    outputs = {}
    for name, rows in [
        ("table_cells", cells),
        ("table_events", events),
        ("table_summaries", tables),
    ]:
        path = work / (name + ".jsonl")
        path.write_text(
            "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows),
            encoding="utf-8",
        )
        outputs[path.name] = digest(path)
        path = work / (name + ".csv")
        write_csv(path, rows)
        outputs[path.name] = digest(path)
    write_json(work / "public_table_staging_summary.json", summary)
    outputs["public_table_staging_summary.json"] = digest(
        work / "public_table_staging_summary.json"
    )
    write_json(
        work / "table_staging_manifest.json",
        dict(
            schema_version=1,
            input_hashes=hashes,
            output_hashes=outputs,
            source_hashes=manifest["source_hashes"],
            source_inputs_unchanged=True,
            summary=summary,
        ),
    )
    return summary


if __name__ == "__main__":
    import argparse
    import os

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--source-root",
        default=os.environ.get("TYCHONIDES_SOURCE_ROOT"),
        required=not os.environ.get("TYCHONIDES_SOURCE_ROOT"),
    )
    p.add_argument("--workspace", default="work/mars-catalogue")
    args = p.parse_args()
    print(json.dumps(build_tables(args.source_root, args.workspace)))
