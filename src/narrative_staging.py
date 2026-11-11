"""Source-bound narrative containers and provisional numeric expressions."""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from .catalog import identity, normalize_quantity
from .coordinate_staging import parse_coordinate
from .inventory import blocks
from .table_staging import descriptor, parse_clock, PATTERNS
from .core import digest
from .normalization import COMMA_THOUSANDS_NUMBER


VULGAR = "¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞"
NUMBER = rf"(?:\d+\s+\d+[/⁄]\d+|\d+(?:[/⁄]\d+)?(?:[{VULGAR}]|[⁰¹²³⁴⁵⁶⁷⁸⁹]+[/⁄][₀₁₂₃₄₅₆₇₈₉]+)?|[{VULGAR}])"
SIGNED = rf"[+−-]?{NUMBER}"
ANGLE = re.compile(
    rf"(?<![\w.]){SIGNED}\s*(?:°|ᵍ|ᴾ|\^[goP]\^)(?:\.?\s*{NUMBER}\s*[′\x27])?(?:\.?\s*{NUMBER}\s*[″\x22])?",
    re.I,
)
PREFIX_ANGLE = re.compile(rf"\bP\.\s*{NUMBER}\s*M\.\s*{NUMBER}(?:\s*S\.\s*{NUMBER})?", re.I)
TIME = re.compile(
    rf"(?<!\w)(?:{NUMBER}\^h\^(?:\s*{NUMBER}\^m\^)?(?:\s*{NUMBER}\^s\^)?|H\.\s*{NUMBER}(?:\s*(?:M\.\s*)?{NUMBER})?(?:\s*(?:S\.\s*)?{NUMBER})?|(?:hour|horam)\s+{NUMBER})",
    re.I,
)
BARE_LABEL = re.compile(
    rf"\b(?P<label>(?:declination|declinatio|declin\.|decl\.|altitude|altitudo|alt\.|azimuth|azim\.)\s*(?:of\s+)?(?:the\s+)?(?:Mars|Moon|Sun|♂|☾|☽|☉|⊙)?\s*(?:was|is)?\s*(?:\[[^\]]*\])?\s*[\]:,=]?\s*)(?P<value>{SIGNED}(?:\s+{NUMBER}){{1,2}})(?![\w/⁄])",
    re.I,
)
NUMERIC = re.compile(rf"(?<!\w)[+−-]?(?:{COMMA_THOUSANDS_NUMBER}|{NUMBER})(?!\w)")


def material_role(span):
    body = span["text_original"].strip()
    kind = span["block_kind"]
    if body.startswith("<!--") or body.startswith(("[QA:", "[ed.:")):
        return "structural_metadata"
    if re.fullmatch(r"(?:\[\^[^\]]+\]\s*)+", body):
        return "reference_marker"
    if kind == "annotation":
        return "note_definition"
    return {
        "heading": "heading_context",
        "diagram": "diagram_description",
        "list": "list_block",
    }.get(kind, "narrative_context")


def local_spec(prefix):
    found = []
    for quantity, pattern in PATTERNS.items():
        if quantity == "recorded_clock":
            continue
        for match in re.finditer(pattern, prefix, re.I):
            found.append((match.start(), quantity))
    if not found:
        return descriptor("")
    start, quantity = max(found)
    spec = descriptor(prefix[start:])
    spec["quantity"] = quantity
    return spec


def angular_value(expression):
    converted = expression.replace("ᵍ", "°").replace("ᴾ", "°")
    converted = re.sub(r"\^[goP]\^", "°", converted, flags=re.I)
    prefixed = PREFIX_ANGLE.fullmatch(converted)
    if prefixed:
        values = re.findall(NUMBER, converted)
        converted = (
            values[0] + "° " + values[1] + "′" + (" " + values[2] + "″" if len(values) > 2 else "")
        )
    return parse_coordinate(converted)


def stage_span(span, previous_label=None):
    text = span["text_original"]
    role = material_role(span)
    expressions = []
    fragments = []
    clock_header = None
    clock_anchor = None
    skip = role in ("structural_metadata", "reference_marker")

    def emit(body, line, start, end, kind, spec=None, basis="explicit_unit", extra=(), header=""):
        nonlocal expressions
        if any(
            e["line"] == line and start < e["char_end"] and end > e["char_start"]
            for e in expressions
        ):
            return
        tail = body[end:]
        uncertain = re.match(r"(?:[/⁄]\s*\[[^\]]*\](?:\^[hms]\^)?|\s*(?:…|\.\.\.|\?))", tail, re.I)
        if uncertain:
            end += uncertain.end()
        raw = body[start:end]
        prefix = body[max(0, start - 180) : start]
        spec = dict(spec or local_spec(prefix))
        flags = [*extra, "quantity_role_and_target_unreviewed"]
        temporal = None
        if kind == "time":
            temporal = (
                "calculation_epoch_candidate"
                if re.search(r"(?:for\s*$|ad\s*$)", prefix, re.I)
                and re.match(r"(?:hour|horam)", raw, re.I)
                else "hour_angle_candidate"
                if re.search(r"meridian|merid\.|hour angle", prefix, re.I)
                else "recorded_clock_candidate"
                if basis == "list_clock_field"
                else "time_role_unresolved"
            )
            time_text = re.sub(rf"^(?:hour|horam)\s+({NUMBER})$", r"\1^h^", raw, flags=re.I)
            parsed = parse_clock(time_text, header)
            quantity = {
                "hour_angle_candidate": "hour_angle",
                "calculation_epoch_candidate": "calculation_epoch",
            }.get(temporal, "time_quantity")
            flags.append("temporal_role_unreviewed")
        else:
            parsed = angular_value(raw)
            quantity = spec.get("quantity")
            if not quantity:
                flags.append("quantity_unresolved")
            if not spec.get("subject"):
                flags.append("target_unresolved")
        if re.match(r"(?:\s+\d|[./⁄]\d)", body[end:]):
            parsed["components"] = None
            parsed["normalized"] = normalize_quantity({"quantity": "declination"})
            flags.append("possible_numeric_continuation_unresolved")
        flags.extend(parsed["flags"])
        before = body[:start]
        layer = "bracketed" if before.count("[") > before.count("]") else "main"
        if re.search(r"\[[^\]]*\d", body):
            flags.append("parallel_numeric_context_unreviewed")
        if role in ("heading_context", "diagram_description", "note_definition"):
            flags.append("context_not_direct_measurement")
        if quantity == "angular_separation" and len(spec.get("endpoints", [])) != 2:
            flags.append("separation_endpoints_unresolved")
        expressions.append(
            dict(
                id=identity(
                    "narrative-expression",
                    span["volume"],
                    span["edition_sha256"],
                    line,
                    f"{start}:{end}:{kind}",
                ),
                span_id=span["id"],
                volume=span["volume"],
                edition_sha256=span["edition_sha256"],
                line=line,
                char_start=start,
                char_end=end,
                source_expression=raw,
                expression_kind=kind,
                quantity_claim=quantity,
                subject_claim=spec.get("subject"),
                endpoints=spec.get("endpoints", []),
                label_evidence=spec.get("text"),
                quantity_basis=basis,
                material_role=role,
                rendering_layer=layer,
                temporal_role_claim=temporal,
                components=parsed["components"],
                normalized=parsed["normalized"],
                flags=sorted(set(flags)),
                inherited_label_line=previous_label["line"]
                if previous_label and basis == "list_value_field"
                else None,
                source_line_group_id=identity(
                    "narrative-row", span["volume"], span["edition_sha256"], line, "row"
                ),
                printed_pages=span.get("printed_pages", []),
                absolute_timestamp=None,
            )
        )

    if not skip:
        for offset, body in enumerate(text.splitlines()):
            line = span["line_start"] + offset
            if (
                span["block_kind"] == "list"
                and previous_label
                and previous_label["spec"].get("quantity") == "angular_separation"
                and "—" in body
            ):
                fields = []
                for index, part in enumerate(re.finditer(r"[^—]+", body)):
                    raw = part[0]
                    left = len(raw) - len(raw.lstrip())
                    if index == 0:
                        bullet = re.match(r"\s*[-•]\s+", raw)
                        if bullet:
                            left = bullet.end()
                    right = len(raw.rstrip())
                    fields.append((part.start() + left, part.start() + right))
                if len(fields) >= 2:
                    start, end = fields[0]
                    clock = body[start:end]
                    if re.fullmatch(rf"(?:H\.\s*)?{NUMBER}(?:\s+{NUMBER}){{0,2}}", clock, re.I):
                        if clock.startswith("H."):
                            count = len(re.findall(NUMBER, clock))
                            clock_header = (
                                "H. M. S." if count == 3 else "H. M." if count == 2 else ""
                            )
                            clock_anchor = line
                        extra = (
                            ["list_clock_units_from_prior_row"]
                            if clock_header and clock_anchor != line
                            else []
                        )
                        emit(
                            body,
                            line,
                            start,
                            end,
                            "time",
                            basis="list_clock_field",
                            extra=extra,
                            header=clock_header or "",
                        )
                    start, end = fields[1]
                    if re.match(rf"[`*\s]*{SIGNED}", body[start:end]):
                        emit(
                            body,
                            line,
                            start,
                            end,
                            "angle",
                            previous_label["spec"],
                            "list_value_field",
                            ("units_from_unreviewed_list_schema",),
                        )
            for matcher, kind in ((PREFIX_ANGLE, "angle"), (ANGLE, "angle"), (TIME, "time")):
                for match in matcher.finditer(body):
                    emit(body, line, match.start(), match.end(), kind)
            for match in BARE_LABEL.finditer(body):
                spec = descriptor(match["label"])
                emit(
                    body,
                    line,
                    match.start("value"),
                    match.end("value"),
                    "angle",
                    spec,
                    "explicit_quantity_label",
                    ("units_from_unreviewed_quantity_label",),
                )
            for match in NUMERIC.finditer(body):
                covering = [
                    e["id"]
                    for e in expressions
                    if e["line"] == line
                    and e["char_start"] <= match.start()
                    and match.end() <= e["char_end"]
                ]
                fragments.append(
                    dict(
                        line=line,
                        char_start=match.start(),
                        char_end=match.end(),
                        source_expression=match[0],
                        expression_ids=covering,
                        status="covered_expression"
                        if covering
                        else "uninterpreted_numeric_fragment",
                    )
                )
    material = dict(
        id=span["id"],
        volume=span["volume"],
        edition_sha256=span["edition_sha256"],
        line_start=span["line_start"],
        line_end=span["line_end"],
        block_kind=span["block_kind"],
        material_role=role,
        text_original=text,
        printed_pages=span.get("printed_pages", []),
        inherited_label=previous_label,
        expression_ids=[e["id"] for e in expressions],
        numeric_fragments=fragments,
        numeric_extraction_skipped=skip,
        skip_basis="structural_metadata_or_reference_marker" if skip else None,
        inspection_status="unreviewed",
    )
    return dict(
        material=material,
        expressions=sorted(expressions, key=lambda e: (e["line"], e["char_start"])),
    )


def stage_narratives(spans, texts, *, edition_hashes=None):
    materials = []
    expressions = []
    selected = {(s["volume"], s["line_start"]): s for s in spans if s["block_kind"] != "table"}
    for volume, text in sorted(texts.items()):
        previous = None
        sha = (edition_hashes or {}).get(volume, hashlib.sha256(text.encode()).hexdigest())
        for start, end, kind, body in blocks(text.splitlines()):
            span = selected.get((volume, start))
            if span:
                if (
                    span["edition_sha256"] != sha
                    or span["line_end"] != end
                    or span["text_original"] != body
                ):
                    raise ValueError("Narrative source binding or fingerprint mismatch")
                staged = stage_span(span, previous if kind == "list" else None)
                materials.append(staged["material"])
                expressions.extend(staged["expressions"])
            if kind == "heading" or kind == "table":
                previous = None
            elif material_role(dict(text_original=body, block_kind=kind)) in (
                "structural_metadata",
                "reference_marker",
            ):
                continue
            elif kind == "paragraph":
                spec = descriptor(body)
                previous = (
                    dict(text=body, line=start, spec=spec)
                    if spec["quantity"] and not ANGLE.search(body) and not TIME.search(body)
                    else None
                )
            else:
                previous = None
    if len(materials) != len(selected):
        raise ValueError("Some narrative spans were not represented")
    return dict(materials=materials, expressions=expressions)


def build_narratives(source_root, workspace):
    from .io import guard, write_json, write_csv
    from .publication import read_witness

    root = Path(source_root).resolve()
    work = Path(workspace).resolve()
    guard(work, root)
    if (work / "pafko.json").exists() or (work / "raw" / "mars.xls").exists():
        raise ValueError("Protected benchmark workspace")
    names = ("witnesses.json", "inventory_manifest.json", "inventory_spans.jsonl")
    hashes = {n: digest(work / n) for n in names}
    inventory = json.loads((work / "inventory_manifest.json").read_text(encoding="utf-8"))
    texts = {}
    witnesses = json.loads((work / "witnesses.json").read_text(encoding="utf-8"))
    for witness in witnesses:
        volume = witness["volume"]
        v = volume - 9
        relative = f"brahe/thesaurus_observationum_vol{v}/translation/brahe_thesaurus_observationum_vol{v}_prepub.md"
        if witness["private_source"] != relative:
            raise ValueError("Unexpected canonical source path")
        texts[volume] = read_witness(root, work, witness)
    spans = [
        json.loads(s)
        for s in (work / "inventory_spans.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    result = stage_narratives(
        spans, texts, edition_hashes={w["volume"]: w["edition_sha256"] for w in witnesses}
    )
    for relative, sha in inventory["source_hashes"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or digest(path) != sha:
            raise ValueError("Source fingerprint changed")
    if any(digest(work / n) != sha for n, sha in hashes.items()):
        raise ValueError("Inventory fingerprint changed")
    materials = result["materials"]
    expressions = result["expressions"]
    summary = dict(
        status="narrative_staging_not_reviewed_catalogue",
        source_spans=len(materials),
        by_block_kind=dict(sorted(Counter(m["block_kind"] for m in materials).items())),
        by_material_role=dict(sorted(Counter(m["material_role"] for m in materials).items())),
        expression_candidates=len(expressions),
        expression_kinds=dict(sorted(Counter(e["expression_kind"] for e in expressions).items())),
        normalization_statuses=dict(
            sorted(Counter(e["normalized"]["status"] for e in expressions).items())
        ),
        uninterpreted_numeric_fragments=sum(
            sum(f["status"] == "uninterpreted_numeric_fragment" for f in m["numeric_fragments"])
            for m in materials
        ),
        inspected_spans_added=0,
        measurement_count=None,
        limits=[
            "Expression occurrences include bilingual and repeated statements; they are not independent observations",
            "Lists without established labels retain unsupported numeric fragments",
            "Subjects, roles, units and temporal associations require review",
            "No absolute timestamps are inferred",
        ],
    )
    outputs = {}
    for name, rows in [("narrative_materials", materials), ("narrative_expressions", expressions)]:
        path = work / (name + ".jsonl")
        path.write_text(
            "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows),
            encoding="utf-8",
        )
        outputs[path.name] = digest(path)
        path = work / (name + ".csv")
        write_csv(path, rows)
        outputs[path.name] = digest(path)
    write_json(work / "public_narrative_staging_summary.json", summary)
    outputs["public_narrative_staging_summary.json"] = digest(
        work / "public_narrative_staging_summary.json"
    )
    write_json(
        work / "narrative_staging_manifest.json",
        dict(
            schema_version=1,
            input_hashes=hashes,
            output_hashes=outputs,
            source_hashes=inventory["source_hashes"],
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
    print(json.dumps(build_narratives(args.source_root, args.workspace)))
