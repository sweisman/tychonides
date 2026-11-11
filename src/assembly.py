"""Assemble source contexts and location-linked catalogue views without fitting."""

from itertools import pairwise

import bisect
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from .catalog import ANGLE_QUANTITIES, identity, TIME_QUANTITIES, source_key, source_fields
from .core import digest
from .inventory import blocks, plain


YEAR = re.compile(r"Observ\w*.*?\b(?:year|anni)\s+(1[5-6]\d{2})\b", re.I)
DATE = re.compile(
    r"^(?:DIE\b|NOCTE\b|EA NOCTE\b|On\s+\d|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)|(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day\b|On the same day\b|The same\b|EODEM DIE\b|The following morning\b|After noon\b|Before noon\b|In the (?:evening|morning) of the same day\b)",
    re.I,
)
CALCULATION = re.compile(
    r"^(?:Pro loco\b|Calculus\b|For (?:the )?(?:place|position|calculation)\b|Calculation\b|Repetitio calculi\b|Repetition of (?:the )?calculation\b)",
    re.I,
)


def build_contexts(texts, *, edition_hashes=None):
    contexts = []
    by_id = {}
    indexes = {}
    for volume, text in sorted(texts.items(), key=lambda item: str(item[0])):
        sha = (edition_hashes or {}).get(volume, hashlib.sha256(text.encode()).hexdigest())
        sections = []
        year = None
        year_id = None
        date = None
        date_level = None
        calculation = None
        starts = [1]
        states = [
            dict(
                section_ids=[],
                year_context_id=None,
                recorded_year_claim=None,
                date_context_id=None,
                calculation_context_id=None,
            )
        ]
        for start, end, kind, body in blocks(text.splitlines()):
            label = plain(body)
            annual = YEAR.search(label) if kind == "heading" else None
            is_date = bool(kind == "heading" and DATE.match(label))
            calc = bool(CALCULATION.match(label))
            if kind != "heading" and not calc:
                continue
            level = len(re.match(r"^#+", body)[0]) if body.startswith("#") else 2
            context_kind = (
                "year_heading"
                if annual
                else "date_heading"
                if is_date
                else "calculation_scope"
                if calc
                else "section_heading"
            )
            cid = identity("source-context", volume, sha, start, context_kind)
            record = dict(
                id=cid,
                **source_fields(volume),
                edition_sha256=sha,
                line_start=start,
                line_end=end,
                kind=context_kind,
                text_original=body,
                heading_level=level if kind == "heading" else None,
                recorded_year_claim=int(annual[1]) if annual else None,
                calendar=None,
                day_origin=None,
                interpretation_status="recorded_source_context_not_accepted_observing_date",
            )
            if is_date:
                record["preceding_date_context_id"] = date
                record["date_label_kind"] = (
                    "relative_or_daypart"
                    if re.match(
                        r"On the same|The same|EODEM|The following|After noon|Before noon|In the (?:evening|morning)",
                        label,
                        re.I,
                    )
                    else "named_or_numeric_day"
                )
            contexts.append(record)
            by_id[cid] = record
            if annual:
                year = int(annual[1])
                year_id = cid
                date = None
                date_level = None
                calculation = None
                sections = [pair for pair in sections if pair[0] < level]
            elif is_date:
                date = cid
                date_level = level
                calculation = None
            elif calc:
                calculation = cid
            else:
                sections = [pair for pair in sections if pair[0] < level]
                sections.append((level, cid))
                calculation = None
                if date_level is not None and level <= date_level:
                    date = None
                    date_level = None
            starts.append(start)
            states.append(
                dict(
                    section_ids=[cid for _, cid in sections],
                    year_context_id=year_id,
                    recorded_year_claim=year,
                    date_context_id=date,
                    calculation_context_id=calculation,
                )
            )
        indexes[volume] = (starts, states)
    return dict(contexts=contexts, by_id=by_id, indexes=indexes)


def context_at(registry, volume, line):
    starts, states = registry["indexes"][volume]
    state = dict(states[bisect.bisect_right(starts, line) - 1])
    date = registry["by_id"].get(state["date_context_id"])
    state.update(
        date_heading_label=date["text_original"] if date else None,
        section_heading_labels=[
            registry["by_id"][cid]["text_original"] for cid in state["section_ids"]
        ],
        date_context_applicability="preceding_heading_only_calculation_scope"
        if state["calculation_context_id"]
        else "source_heading_context_only",
        accepted_observing_date=None,
        calendar=None,
        day_origin=None,
        absolute_timestamp=None,
    )
    return state


def cell_intervals(line, *, declared_table=False):
    pipes = [m.start() for m in re.finditer(r"(?<!\\)\|", line)]
    if declared_table and pipes:
        if line[: pipes[0]].strip():
            pipes.insert(0, -1)
        if line[pipes[-1] + 1 :].strip():
            pipes.append(len(line))
    result = []
    for left, right in pairwise(pipes):
        raw = line[left + 1 : right]
        start = left + 1 + len(raw) - len(raw.lstrip())
        end = right - (len(raw) - len(raw.rstrip()))
        result.append((start, max(start, end)))
    return result


def literal_intervals(line, expression):
    if not expression:
        return []
    if expression in ("...", "…"):
        return [
            (m.start(), m.end())
            for m in re.finditer(r"(?<![.…])" + re.escape(expression) + r"(?![.…])", line)
        ]
    intervals = []
    offset = 0
    while (start := line.find(expression, offset)) >= 0:
        end = start + len(expression)
        before = line[start - 1] if start else ""
        after = line[end] if end < len(line) else ""
        if not (before.isalnum() or before == "_" or after.isalnum() or after == "_"):
            intervals.append((start, end))
        # The preceding lookahead also admitted overlapping literal occurrences.
        offset = start + 1
    return intervals


def assemble(texts, reviewed, coordinates, cells, narratives, issues=(), *, edition_hashes=None):
    editions = {
        v: ((edition_hashes or {}).get(v, hashlib.sha256(t.encode()).hexdigest()), t.splitlines())
        for v, t in texts.items()
    }
    registry = build_contexts(texts, edition_hashes=edition_hashes)
    items = []
    links = []
    source_map = {}
    cell_groups = defaultdict(list)
    interval_groups = defaultdict(list)
    active_issues = [
        i
        for i in issues
        if not i.get("status", "").startswith("rejected") and i.get("source_line") is not None
    ]
    for issue in active_issues:
        if issue["source_sha256"] != editions[source_key(issue)][0]:
            raise ValueError("Edition issue fingerprint mismatch")
    candidates = [
        r
        for r in cells
        if r["row_kind"] == "data"
        and (
            r.get("contains_number")
            or r.get("numeric_placeholder")
            or (r.get("quantity_claim") and r.get("source_expression"))
        )
    ]
    layers = [
        ("reviewed_assertion", reviewed),
        ("coordinate_candidate", coordinates),
        ("table_cell", candidates),
        ("narrative_expression", narratives),
    ]
    for layer, rows in layers:
        for row in rows:
            volume, line = source_key(row), row["line"]
            sha, lines = editions[volume]
            if row["edition_sha256"] != sha:
                raise ValueError("Catalogue source fingerprint mismatch")
            raw = lines[line - 1]
            expression = row.get("source_expression")
            column = row.get("column")
            intervals = []
            slots = cell_intervals(raw)
            # The shared review recipe selects a prose line as its single field.
            # Bind its literals as prose; it has no printed table-cell location.
            if (
                layer == "reviewed_assertion"
                and column == 1
                and not slots
                and not raw.lstrip().startswith("|")
            ):
                column = None
            if column is not None:
                if not isinstance(column, int) or not 1 <= column <= len(slots):
                    raise ValueError("Source cell binding invalid")
                start, end = slots[column - 1]
                if raw[start:end] == expression:
                    intervals = [(start, end)]
                elif layer == "reviewed_assertion":
                    intervals = [
                        (start + a, start + b)
                        for a, b in literal_intervals(raw[start:end], expression)
                    ]
                    if not intervals:
                        raise ValueError("Reviewed source cell expression binding mismatch")
                else:
                    raise ValueError("Source cell expression binding mismatch")
                # Physical columns have always been authoritative for a unique
                # cell literal. Use offsets to resolve multiple occurrences,
                # without reinterpreting earlier non-authoritative hints.
                if (
                    layer == "reviewed_assertion"
                    and len(intervals) > 1
                    and ("char_start" in row or "char_end" in row)
                ):
                    selected = (row.get("char_start"), row.get("char_end"))
                    if selected not in intervals:
                        raise ValueError("Reviewed source cell offset binding mismatch")
                    intervals = [selected]
            elif row.get("char_start") is not None:
                start, end = row["char_start"], row["char_end"]
                if raw[start:end] != expression:
                    raise ValueError("Source interval binding mismatch")
                allowed = literal_intervals(raw, expression)
                if (
                    layer == "reviewed_assertion"
                    and row.get("quantity") in ANGLE_QUANTITIES
                    and re.fullmatch(r"\d+", expression)
                    and row.get("components") == {"degree": expression}
                ):
                    allowed.extend(
                        m.span("degree")
                        for m in re.finditer(
                            r"(?<!\w)(?P<degree>"
                            + re.escape(expression)
                            + r")(?:st|nd|rd|th) degree\b",
                            raw,
                        )
                    )
                if layer == "reviewed_assertion" and row.get("quantity") in TIME_QUANTITIES:
                    allowed.extend(
                        m.span("time")
                        for m in re.finditer(
                            r"(?<!\w)Hora(?P<time>" + re.escape(expression) + r")(?!\w)", raw
                        )
                    )
                if (start, end) not in allowed:
                    raise ValueError("Source interval binding crosses a lexical boundary")
                intervals = [(start, end)]
            elif expression:
                intervals = literal_intervals(raw, expression)
                if (
                    not intervals
                    and layer == "reviewed_assertion"
                    and row.get("quantity") in TIME_QUANTITIES
                    and re.match(r"\d", expression)
                ):
                    intervals = [
                        m.span("time")
                        for m in re.finditer(
                            r"(?<!\w)Hora(?P<time>" + re.escape(expression) + r")(?!\w)", raw
                        )
                    ]
            if expression and not intervals:
                raise ValueError("Source expression binding unresolved")
            if column is None and len(intervals) == 1:
                containing = [
                    index + 1
                    for index, (a, b) in enumerate(slots)
                    if a <= intervals[0][0] and intervals[0][1] <= b
                ]
                if len(containing) == 1:
                    column = containing[0]
            iid = identity("catalogue-item", volume, sha, line, f"{layer}:{row['id']}")
            if (layer, row["id"]) in source_map:
                raise ValueError("Duplicate upstream catalogue identity")
            source_map[(layer, row["id"])] = iid
            cell_anchor = (
                identity("cell-anchor", volume, sha, line, str(column))
                if column is not None
                else None
            )
            interval_anchor = (
                identity(
                    "interval-anchor", volume, sha, line, f"{intervals[0][0]}:{intervals[0][1]}"
                )
                if len(intervals) == 1
                else None
            )
            status = (
                "unique_source_interval"
                if len(intervals) == 1
                else "ambiguous_literal_occurrences"
                if len(intervals) > 1
                else "source_expression_absent"
            )
            context = context_at(registry, volume, line)
            if row.get("material_role") in (
                "note_definition",
                "diagram_description",
                "heading_context",
            ):
                context["date_context_applicability"] = "preceding_heading_only_contextual_material"
            pages = (
                [row["reviewed_page"]]
                if row.get("reviewed_page") is not None
                else [row["printed_page"]]
                if row.get("printed_page") is not None
                else row.get("printed_pages")
                or ([row["provisional_page"]] if row.get("provisional_page") is not None else [])
            )
            items.append(
                dict(
                    id=iid,
                    layer=layer,
                    upstream_id=row["id"],
                    **source_fields(volume),
                    edition_sha256=sha,
                    line=line,
                    column=column,
                    source_expression=expression,
                    candidate_intervals=[dict(char_start=a, char_end=b) for a, b in intervals],
                    anchor_status=status,
                    cell_anchor_id=cell_anchor,
                    interval_anchor_id=interval_anchor,
                    quantity_claim=row.get("quantity", row.get("quantity_claim")),
                    role_claim=row.get("reviewed_role")
                    or row.get("role", row.get("role_claim", row.get("material_role"))),
                    subject_claim=row.get(
                        "subject",
                        row.get(
                            "reviewed_target", row.get("subject_claim", row.get("target_claim"))
                        ),
                    ),
                    normalized=row.get("normalized"),
                    bibliographic_pages=pages,
                    source_context=context,
                    review_status="reviewed_source_assertion"
                    if layer == "reviewed_assertion"
                    else "unreviewed_view",
                    edition_issue_ids=[
                        i["id"]
                        for i in active_issues
                        if source_key(i) == volume
                        and i["source_line"] == line
                        and (i.get("source_column") is None or i["source_column"] == column)
                    ],
                    flags=row.get("flags", []),
                    evidence=row,
                )
            )
            if cell_anchor:
                cell_groups[cell_anchor].append(iid)
            if interval_anchor:
                interval_groups[interval_anchor].append(iid)
    for relation, groups in [
        ("shared_source_cell_container", cell_groups),
        ("same_source_interval", interval_groups),
    ]:
        for anchor, group in sorted(groups.items()):
            for iid in sorted(group)[1:]:
                links.append(
                    dict(
                        relation=relation,
                        source_id=sorted(group)[0],
                        target_id=iid,
                        anchor_id=anchor,
                        basis="source_location_not_measured_value",
                    )
                )
    for row in coordinates:
        if row.get("reviewed_assertion_id"):
            target = source_map.get(("reviewed_assertion", row["reviewed_assertion_id"]))
            if target:
                links.append(
                    dict(
                        relation="prior_review_correspondence",
                        source_id=source_map[("coordinate_candidate", row["id"])],
                        target_id=target,
                        anchor_id=None,
                        basis="prior_source_identity_review",
                    )
                )
    return dict(items=items, links=links, contexts=registry["contexts"], source_map=source_map)


def build_assembly(source_root, workspace):
    from .io import guard, write_json, write_csv

    root = Path(source_root).resolve()
    work = Path(workspace).resolve()
    guard(work, root)
    if (work / "pafko.json").exists() or (work / "raw" / "mars.xls").exists():
        raise ValueError("Protected benchmark workspace")
    manifest_names = (
        "catalogue_manifest.json",
        "coordinate_staging_manifest.json",
        "table_staging_manifest.json",
        "narrative_staging_manifest.json",
    )
    names = [
        "witnesses.json",
        "inventory_manifest.json",
        "assertions.jsonl",
        "staged_coordinates.jsonl",
        "table_cells.jsonl",
        "narrative_expressions.jsonl",
        "coordinate_control_links.jsonl",
        *manifest_names,
    ]
    if (work / "edition_issues.json").exists():
        names.append("edition_issues.json")
    inputs = {name: digest(work / name) for name in names}
    upstream_files = {}
    for name in manifest_names:
        manifest = json.loads((work / name).read_text(encoding="utf-8"))
        for file, sha in {
            **manifest.get("output_hashes", {}),
            **manifest.get("input_hashes", {}),
            **manifest.get("inventory_input_hashes", {}),
        }.items():
            path = (work / file).resolve()
            if not path.is_relative_to(work) or digest(path) != sha:
                raise ValueError("Upstream input/output fingerprint mismatch")
            upstream_files[file] = sha
    inventory = json.loads((work / "inventory_manifest.json").read_text(encoding="utf-8"))
    texts = {}
    from .publication import read_witness

    witnesses = json.loads((work / "witnesses.json").read_text(encoding="utf-8"))
    for witness in witnesses:
        volume = witness["volume"]
        v = volume - 9
        relative = f"brahe/thesaurus_observationum_vol{v}/translation/brahe_thesaurus_observationum_vol{v}_prepub.md"
        if witness["private_source"] != relative:
            raise ValueError("Unexpected source path")
        texts[volume] = read_witness(root, work, witness)

    def rows(name):
        return [json.loads(line) for line in (work / name).read_text(encoding="utf-8").splitlines()]

    issues = (
        json.loads((work / "edition_issues.json").read_text(encoding="utf-8"))
        if "edition_issues.json" in names
        else []
    )
    assembled = assemble(
        texts,
        rows("assertions.jsonl"),
        rows("staged_coordinates.jsonl"),
        rows("table_cells.jsonl"),
        rows("narrative_expressions.jsonl"),
        issues,
        edition_hashes={w["volume"]: w["edition_sha256"] for w in witnesses},
    )
    controls = []
    seen = set()
    for row in rows("coordinate_control_links.jsonl"):
        if row["pafko_id"] in seen:
            raise ValueError("Duplicate workbook control link")
        seen.add(row["pafko_id"])
        controls.append(
            dict(
                pafko_id=row["pafko_id"],
                catalogue_item_id=assembled["source_map"][
                    ("coordinate_candidate", row["coordinate_id"])
                ],
                upstream_coordinate_id=row["coordinate_id"],
                basis="reconciled_source_identity_not_numeric_similarity",
            )
        )
    for relative, sha in inventory["source_hashes"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or digest(path) != sha:
            raise ValueError("Source fingerprint changed")
    if any(digest(work / name) != sha for name, sha in {**upstream_files, **inputs}.items()):
        raise ValueError("Assembly input fingerprint changed")
    items = assembled["items"]
    contexts = assembled["contexts"]
    links = assembled["links"]
    summary = dict(
        status="assembled_source_views_not_final_scientific_release",
        catalogue_views=len(items),
        by_layer=dict(sorted(Counter(i["layer"] for i in items).items())),
        source_contexts=len(contexts),
        context_kinds=dict(sorted(Counter(c["kind"] for c in contexts).items())),
        location_links=len(links),
        link_kinds=dict(sorted(Counter(l["relation"] for l in links).items())),
        source_anchor_statuses=dict(sorted(Counter(i["anchor_status"] for i in items).items())),
        views_without_bibliographic_page=sum(not i["bibliographic_pages"] for i in items),
        views_with_date_heading_context=sum(
            i["source_context"]["date_context_id"] is not None for i in items
        ),
        views_in_calculation_scope=sum(
            i["source_context"]["calculation_context_id"] is not None for i in items
        ),
        views_linked_to_edition_issues=sum(bool(i["edition_issue_ids"]) for i in items),
        workbook_controls=len(controls),
        accepted_absolute_timestamps=0,
        inspected_spans_added=0,
        measurement_count=None,
        limits=[
            "Views overlap and are not independent observations",
            "Cell containment does not imply identical quantities",
            "Date headings and calculation scopes are source contexts, not accepted observing dates",
            "Ambiguous source intervals and scientific interpretations remain explicit",
        ],
    )
    outputs = {}
    for name, values in [
        ("catalogue_items", items),
        ("catalogue_links", links),
        ("source_contexts", contexts),
        ("catalogue_control_links", controls),
    ]:
        path = work / (name + ".jsonl")
        path.write_text(
            "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in values),
            encoding="utf-8",
        )
        outputs[path.name] = digest(path)
        path = work / (name + ".csv")
        write_csv(path, values)
        outputs[path.name] = digest(path)
    write_json(work / "public_assembly_summary.json", summary)
    outputs["public_assembly_summary.json"] = digest(work / "public_assembly_summary.json")
    write_json(
        work / "assembly_manifest.json",
        dict(
            schema_version=1,
            input_hashes=inputs,
            upstream_files=upstream_files,
            source_hashes=inventory["source_hashes"],
            output_hashes=outputs,
            source_inputs_unchanged=True,
            summary=summary,
        ),
    )
    return summary


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        default=os.environ.get("TYCHONIDES_SOURCE_ROOT"),
        required=not os.environ.get("TYCHONIDES_SOURCE_ROOT"),
    )
    parser.add_argument("--workspace", default="work/mars-catalogue")
    args = parser.parse_args()
    print(json.dumps(build_assembly(args.source_root, args.workspace)))
