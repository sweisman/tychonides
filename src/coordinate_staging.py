"""Version-bound coordinate staging; extraction and cell reviews add no span coverage."""

import bisect
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from .catalog import identity, normalize_quantity
from .core import fraction_text, digest


def coordinate_qualifiers(text):
    """Peel only recognized, number-free edge phrases; retain their literals."""
    qualifiers = []
    patterns = [
        ("pinnule", r"(?:with |by )?one\s*\[vno\.?\]"),
        ("pinnule", r"with one pinnule\s*\[vno (?:pinn|pin)\.\s*,?\]"),
        ("pinnule", r"(?:with )?both\s*\[(?:vtroq\.|vtroque)\]"),
        ("pinnule", r"with the other\s*\[alt\.\]"),
        ("pinnule", r"with the other pinnule\s*\[altero pin\.\]"),
        ("quality", r"nearly\s*\[fere\]"),
        ("quality", r"good\s*\[bona\]"),
        ("quality", r"better\s*\[melior\]"),
        ("quality", r"exactly\s*\[exacte\]"),
        ("quality", r"doubtful\s*\[dubia\]"),
        ("quality", r"doubtful because of the beam\s*\[dubia propter tignum\]"),
        ("instrument", r"by the steel instrument\s*\[per Chal\.\]"),
    ]
    label = re.match(r"^Declination\s*(\[Decl\.\])\s*", text, re.I)
    if label:
        qualifiers.append(dict(kind="parallel_label", text_without_markup=label[1]))
        text = "Declination " + text[label.end() :]
    for _ in range(4):
        changed = False
        for kind, pattern in patterns:
            match = re.search(rf"(?<!\w){pattern}\s*[,\.]?$", text, re.I)
            if match is None:
                match = re.match(rf"{pattern}\s*,?\s*", text, re.I)
            if match:
                qualifiers.append(dict(kind=kind, text_without_markup=match[0].strip()))
                text = (text[: match.start()] + text[match.end() :]).strip()
                changed = True
                break
        if not changed:
            break
    for pattern in (r"^\{\s*", r"\s*\}$"):
        match = re.search(pattern, text)
        if match:
            qualifiers.append(dict(kind="grouping_marker", text_without_markup=match[0].strip()))
            text = (text[: match.start()] + text[match.end() :]).strip()
    return text.rstrip(" .,"), qualifiers


def parse_coordinate(expression):
    result = dict(
        components=None,
        normalized=normalize_quantity({"quantity": "declination"}),
        flags=[],
        qualifiers=[],
    )
    if re.search(r"…|\.\.\.|\?", expression):
        result["normalized"] = normalize_quantity(dict(quantity="declination", incomplete=True))
        return result
    if re.search(r"[♀♃♄☉☽☿]", expression):
        result["flags"].append("target_symbol_requires_review")
        return result
    text = expression.strip().replace("*", "").replace("`", "")
    text = re.sub(r"\[\^[^\]]+\]", "", text)
    if re.search(r"\[recte:", text, re.I):
        text = re.split(r"\[recte:", text, flags=re.I)[0].strip()
        result["flags"].append("inline_variant_requires_extraction")
    parallel = re.fullmatch(r"(.*?)\s*\[([^\]]+)\]\s*", text)
    if parallel and re.search(r"\d", parallel[2]):
        first = parse_coordinate(parallel[1])
        second = parse_coordinate(parallel[2])
        result["flags"].extend(first["flags"] + second["flags"])
        result["qualifiers"].extend(first["qualifiers"] + second["qualifiers"])
        if first["normalized"]["status"] == second["normalized"]["status"] == "exact":
            if first["normalized"]["magnitude"] == second["normalized"]["magnitude"]:
                result.update(components=first["components"], normalized=first["normalized"])
                result["flags"].append("parallel_numeric_expressions_agree")
            else:
                result["flags"].append("parallel_numeric_expressions_disagree")
        return result
    text, result["qualifiers"] = coordinate_qualifiers(text)
    if result["qualifiers"]:
        result["flags"].append("literal_qualifiers_preserved")
    text = re.sub(r"\[(?:B|Bor|M|Merid)\.?\]", "", text, flags=re.I)
    text = re.sub(
        r"^(?:Declination|Declinatio|Declin\.?|Decl\.)(?:\s+of)?\s*♂?\s*,?\s*", "", text, flags=re.I
    )
    if re.search(r"\b(?:doubtful|dubia)\b", text, re.I):
        result["flags"].append("source_quality_note_present")
    if re.search(r"\b(?:twice|bis)\b", text, re.I):
        result["flags"].append("source_repetition_note_present")
    text = re.sub(r"\b(?:doubtful|dubia|twice|bis)\b", "", text, flags=re.I)
    text = re.sub(
        r"\b(?:north|south|northern|southern|B|Bor|M|Merid)\.?(?=\s|$)", "", text, flags=re.I
    ).strip()
    text = fraction_text(text).strip(" ,")
    token = r"\d+(?:\s+\d+/\d+|/\d+)?"
    components = None
    if "°" in text:
        match = re.fullmatch(
            rf"({token})\s*°(?:\.?\s*({token})\s*[′\x27])?(?:\.?\s*({token})\s*[″\x22])?",
            text,
        )
        if match:
            components = {
                u: v
                for u, v in zip(("degree", "arcminute", "arcsecond"), match.groups(), strict=True)
                if v is not None
            }
    elif re.fullmatch(rf"{token}(?:\s+{token}){{1,2}}", text):
        tokens = re.findall(token, text)
        components = dict(
            zip(("degree", "arcminute", "arcsecond")[: len(tokens)], tokens, strict=True)
        )
    if components:
        try:
            normalized = normalize_quantity(dict(quantity="declination", components=components))
        except ValueError:
            result["flags"].append("invalid_sexagesimal_components")
        else:
            result.update(components=components, normalized=normalized)
    return result


def stage_coordinates(
    observations,
    texts,
    spans,
    controls,
    reviewed_assertions,
    classifications=None,
    *,
    edition_hashes=None,
):
    editions = {
        v: (
            (edition_hashes or {}).get(v, hashlib.sha256(text.encode()).hexdigest()),
            text.splitlines(),
        )
        for v, text in texts.items()
    }
    classified = {}
    for decision in classifications or []:
        sid = decision["source_record_id"]
        sha, lines = editions[decision["volume"]]
        if sid in classified:
            raise ValueError("Duplicate coordinate classification")
        if decision["edition_sha256"] != sha:
            raise ValueError("Classification edition fingerprint mismatch")
        start, end = decision["evidence_start"], decision["evidence_end"]
        if not 1 <= start <= decision["line"] <= end <= len(lines):
            raise ValueError("Classification evidence interval invalid")
        if (
            hashlib.sha256("\n".join(lines[start - 1 : end]).encode()).hexdigest()
            != decision["evidence_sha256"]
        ):
            raise ValueError("Classification evidence fingerprint mismatch")
        if decision["decision"] not in (
            "exclude_as_mars_coordinate",
            "exclude_wrong_quantity",
            "classify_role",
        ) or not decision.get("reason"):
            raise ValueError("Unsupported coordinate classification")
        if decision["decision"] == "classify_role" and not decision.get("reviewed_role"):
            raise ValueError("Missing reviewed role")
        classified[sid] = decision
    indexes = {}
    for volume in texts:
        group = sorted((s for s in spans if s["volume"] == volume), key=lambda s: s["line_start"])
        indexes[volume] = ([s["line_start"] for s in group], group)
    control_by_source = {}
    pafko_ids = set()
    for control in controls:
        sid = control.get("source_record_id")
        pid = control["pafko_id"]
        if not sid or sid in control_by_source or pid in pafko_ids:
            raise ValueError("Controls require unique source identities")
        control_by_source[sid] = control
        pafko_ids.add(pid)
    manual = defaultdict(list)
    assertions_by_id = {r["id"]: r for r in reviewed_assertions}
    if len(assertions_by_id) != len(reviewed_assertions):
        raise ValueError("Duplicate reviewed assertion identity")
    explicit_links = {}
    for row in reviewed_assertions:
        if row["quantity"] == "declination":
            manual[(row["volume"], row["line"], row.get("column"))].append(row["id"])
    rows = []
    links = []
    locations = []
    source_ids = set()
    for source in observations:
        sid = source["id"]
        volume = source["volume"]
        line = source["line"]
        column = source.get("column")
        if sid in source_ids:
            raise ValueError("Duplicate extracted source identity")
        source_ids.add(sid)
        sha, lines = editions[volume]
        source_row = lines[line - 1]
        flags = list(source.get("flags", []))
        bound = source_row.strip() == source["row_original"].strip()
        expression = None
        if bound and column is not None and source_row.strip().startswith("|"):
            cells = source_row.strip().strip("|").split("|")
            if isinstance(column, int) and 1 <= column <= len(cells):
                expression = cells[column - 1].strip()
        elif bound and source.get("value_original") and source["value_original"] in source_row:
            expression = source["value_original"]
        if expression is None:
            flags.append("source_row_binding_unresolved")
        parsed = parse_coordinate(expression) if expression is not None else parse_coordinate("")
        flags.extend(parsed["flags"])
        flags.append("scientific_interpretation_unreviewed")
        starts, group = indexes[volume]
        position = bisect.bisect_right(starts, line) - 1
        span = group[position] if position >= 0 and line <= group[position]["line_end"] else None
        if span and span["edition_sha256"] != sha:
            raise ValueError("Inventory witness fingerprint mismatch")
        if span is None:
            flags.append("outside_selected_inventory_spans")
        key = sid.rsplit(":", 1)[-1]
        rid = identity("coordinate", volume, sha, line, key)
        control = control_by_source.get(sid)
        classification = classified.get(sid)
        if classification and (
            classification["volume"] != volume or classification["line"] != line
        ):
            raise ValueError("Classification source identity differs")
        target = (
            classification.get("reviewed_target")
            if classification
            else control.get("target")
            if control
            else None
        )
        selection = "pending_scientific_review"
        if classification and classification["decision"] == "exclude_wrong_quantity":
            selection = "excluded_wrong_quantity"
        elif target and target != "Mars":
            selection = "excluded_other_target"
        reviewed_role = classification.get("reviewed_role") if classification else None
        raw_selection = (
            selection
            if selection.startswith("excluded")
            else "excluded_reviewed_reduction"
            if reviewed_role
            in ("historical_reduction", "historical_input", "adopted_value", "calibration")
            else "pending_scientific_review"
        )
        reviewed_page = (
            control.get("preferred_source_page")
            if control and control.get("page_basis") == "source_scan_review"
            else None
        )
        time_reviewed = bool(control and control.get("time_basis") == "source_scan_review")
        temporal = dict(
            date_original=source.get("date_original"),
            time_original=source.get("time_original"),
            extracted_date=source.get("date"),
            extracted_time_key=source.get("time_key"),
            time_locus=source.get("time_locus"),
            time_reviewed=time_reviewed,
            reviewed_time_key=control.get("preferred_recorded_time_key") if time_reviewed else None,
            reviewed_date=control.get("preferred_recorded_date")
            if control and control.get("date_basis") == "source_scan_review"
            else None,
            calendar=None,
            day_origin=None,
            absolute_timestamp=None,
        )
        found = manual.get((volume, line, column), [])
        if classification and "reviewed_assertion_id" in classification:
            aid = classification["reviewed_assertion_id"]
            reviewed = assertions_by_id.get(aid)
            legacy_prose = (
                column is None
                and reviewed is not None
                and reviewed.get("column") == 1
                and not source_row.lstrip().startswith("|")
            )
            role_map = {"reduction": "historical_reduction"}
            if (
                classification["decision"] != "classify_role"
                or classification.get("assertion_binding_basis")
                != "source_location_and_printed_order"
                or not bound
                or expression is None
                or reviewed is None
                or any(
                    reviewed.get(k) != v
                    for k, v in (
                        ("volume", volume),
                        ("line", line),
                        ("edition_sha256", sha),
                        ("quantity", "declination"),
                        ("subject", target),
                    )
                )
                or (reviewed.get("column") != column and not legacy_prose)
                or reviewed_role != role_map.get(reviewed.get("role"), reviewed.get("role"))
                or (aid in explicit_links and explicit_links[aid] != sid)
            ):
                raise ValueError(
                    "Reviewed assertion link requires a unique, source-bound identity and role"
                )
            explicit_links[aid] = sid
            found = [aid]
        elif classification and "assertion_binding_basis" in classification:
            raise ValueError("Assertion binding basis requires its reviewed assertion identity")
        rows.append(
            dict(
                id=rid,
                legacy_source_record_id=sid,
                volume=volume,
                edition_sha256=sha,
                line=line,
                column=column,
                provisional_page=source.get("page"),
                reviewed_page=reviewed_page,
                span_id=span["id"] if span else None,
                source_expression=expression,
                legacy_value_original=source.get("value_original"),
                text_original=source_row,
                source_binding_status="bound" if expression is not None else "unresolved",
                quantity_claim=source.get("measurement_type"),
                target_claim=source.get("target"),
                role_claim=source.get("role"),
                label_original=source.get("label"),
                headers_original=source.get("headers_original"),
                components=parsed["components"],
                normalized=parsed["normalized"],
                qualifiers=parsed["qualifiers"],
                flags=sorted(set(flags)),
                review_scope="coordinate_candidate_only",
                reviewed_assertion_id=found[0] if len(found) == 1 else None,
                reviewed_target=target,
                mars_coordinate_selection=selection,
                reviewed_role=reviewed_role,
                raw_astrometry_selection=raw_selection,
                classification_id=classification["id"] if classification else None,
                temporal_claims=temporal,
                hemisphere_claim=dict(
                    signed_arcsec=source.get("arcsec"),
                    basis=source.get("hemisphere_basis"),
                    locus=source.get("hemisphere_locus"),
                ),
                benchmark_control_id=control["pafko_id"] if control else None,
                benchmark_validation=(
                    {
                        k: control.get(k)
                        for k in (
                            "comparison_status",
                            "preferred_basis",
                            "preferred_magnitude_arcsec",
                            "page_basis",
                            "time_basis",
                            "date_basis",
                            "source_check",
                            "mars_selection",
                            "target",
                            "role",
                        )
                    }
                    if control
                    else None
                ),
            )
        )
        if control:
            links.append(
                dict(
                    pafko_id=control["pafko_id"],
                    coordinate_id=rid,
                    source_record_id=sid,
                    basis="reconciled_source_identity",
                    span_id=span["id"] if span else None,
                )
            )
            if reviewed_page is not None and reviewed_page != source.get("page"):
                locations.append(
                    dict(
                        id=identity("location", volume, sha, line, key),
                        coordinate_id=rid,
                        edition_sha256=sha,
                        volume=volume,
                        line=line,
                        column=column,
                        provisional_page=source.get("page"),
                        reviewed_page=reviewed_page,
                        control_id=control["pafko_id"],
                        basis="prior_source_scan_review",
                        scope="source_record_only_not_whole_page",
                    )
                )
    if source_ids.intersection(control_by_source.keys()) != set(control_by_source):
        raise ValueError("Control source identity absent from extraction")
    if set(classified) - source_ids:
        raise ValueError("Classification source identity absent from extraction")
    summary = dict(
        status="coordinate_staging_not_complete_mars_catalogue",
        coordinate_candidates=len(rows),
        by_volume=dict(sorted(Counter(r["volume"] for r in rows).items())),
        normalization_statuses=dict(
            sorted(Counter(r["normalized"]["status"] for r in rows).items())
        ),
        benchmark_controls=len(links),
        coordinates_without_workbook_control=sum(r["benchmark_control_id"] is None for r in rows),
        candidate_spans_not_selected=sum(r["span_id"] is None for r in rows),
        source_bindings_unresolved=sum(r["source_binding_status"] != "bound" for r in rows),
        reviewed_assertion_overlaps=sum(r["reviewed_assertion_id"] is not None for r in rows),
        reviewed_location_assertions=len(locations),
        inspected_candidate_spans_added=0,
        measurement_count=None,
    )
    summary["coordinate_classifications"] = len(classified)
    summary["mars_coordinate_selections"] = dict(
        sorted(Counter(r["mars_coordinate_selection"] for r in rows).items())
    )
    summary["nonexcluded_coordinates_without_workbook_control"] = sum(
        r["benchmark_control_id"] is None
        and not r["mars_coordinate_selection"].startswith("excluded")
        for r in rows
    )
    summary["reviewed_coordinate_roles"] = dict(
        sorted(Counter(r["reviewed_role"] for r in rows if r["reviewed_role"]).items())
    )
    return dict(
        coordinates=rows, control_links=links, location_assertions=locations, summary=summary
    )


def build_staging(source_root, workspace, benchmark):
    from .io import guard, write_json, write_csv

    root = Path(source_root).resolve()
    work = Path(workspace).resolve()
    benchmark = Path(benchmark).resolve()
    guard(work, root)
    if work.is_relative_to(benchmark) or benchmark.is_relative_to(work):
        raise ValueError("Coordinate staging must not overlap protected benchmark output")
    inventory = json.loads((work / "inventory_manifest.json").read_text(encoding="utf-8"))
    benchmark_hashes = inventory["benchmark_artifact_sha256"]
    if any(digest(benchmark / name) != sha for name, sha in benchmark_hashes.items()):
        raise ValueError("Benchmark fingerprint changed since inventory")
    workbook = json.loads((benchmark / "workbook.json").read_text(encoding="utf-8"))
    if digest(benchmark / "raw" / "mars.xls") != workbook["sha256"]:
        raise ValueError("Original workbook fingerprint changed")
    texts = {}
    input_names = ["inventory_manifest.json", "witnesses.json", "inventory_spans.jsonl"]
    if (work / "assertions.jsonl").exists():
        input_names.append("assertions.jsonl")
    if (work / "coordinate_adjudications.json").exists():
        input_names.append("coordinate_adjudications.json")
    if (work / "source_binding_reviews.json").exists():
        input_names.append("source_binding_reviews.json")
    input_hashes = {n: digest(work / n) for n in input_names}
    from .publication import read_witness

    witnesses = json.loads((work / "witnesses.json").read_text(encoding="utf-8"))
    for witness in witnesses:
        volume = witness["volume"]
        v = volume - 9
        relative = f"brahe/thesaurus_observationum_vol{v}/translation/brahe_thesaurus_observationum_vol{v}_prepub.md"
        if witness["private_source"] != relative:
            raise ValueError("Unexpected canonical source path")
        texts[volume] = read_witness(root, work, witness)
    for relative, sha in inventory["source_hashes"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or digest(path) != sha:
            raise ValueError("Source fingerprint changed")
    spans = [
        json.loads(s)
        for s in (work / "inventory_spans.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    reviewed = (
        [
            json.loads(s)
            for s in (work / "assertions.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        if "assertions.jsonl" in input_names
        else []
    )
    observations = json.loads((benchmark / "observations.json").read_text(encoding="utf-8"))
    classifications = (
        json.loads((work / "coordinate_adjudications.json").read_text(encoding="utf-8"))
        if "coordinate_adjudications.json" in input_names
        else []
    )
    from .source_bindings import load_bindings, rebind_extraction_inputs

    controls = json.loads((benchmark / "derived_catalogue.json").read_text(encoding="utf-8"))
    observations, classifications = rebind_extraction_inputs(
        observations,
        classifications,
        texts,
        load_bindings(work),
        control_source_ids={c["source_record_id"] for c in controls},
    )
    staged = stage_coordinates(
        observations,
        texts,
        spans,
        controls,
        reviewed,
        classifications,
        edition_hashes={w["volume"]: w["edition_sha256"] for w in witnesses},
    )
    if any(digest(benchmark / name) != sha for name, sha in benchmark_hashes.items()):
        raise ValueError("Benchmark changed during staging")
    if any(digest(work / name) != sha for name, sha in input_hashes.items()):
        raise ValueError("Inventory/review inputs changed during staging")
    if any(digest(root / relative) != sha for relative, sha in inventory["source_hashes"].items()):
        raise ValueError("Source changed during staging")
    outputs = {}
    for key, name in [
        ("coordinates", "staged_coordinates"),
        ("control_links", "coordinate_control_links"),
        ("location_assertions", "reviewed_locations"),
    ]:
        path = work / (name + ".jsonl")
        path.write_text(
            "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in staged[key]),
            encoding="utf-8",
        )
        outputs[path.name] = digest(path)
        csv_path = work / (name + ".csv")
        write_csv(csv_path, staged[key])
        outputs[csv_path.name] = digest(csv_path)
    summary = dict(
        **staged["summary"],
        limits=[
            "Coordinate candidates do not cover every Mars quantity or all Mars source material",
            "Extraction and prior cell checks do not add whole-span inspected coverage",
            "Unreviewed target, role, hemisphere, calendar and clock claims require scientific review",
            "Counts without workbook controls are candidate coordinates, not additional independent observations",
        ],
    )
    write_json(work / "public_coordinate_staging_summary.json", summary)
    outputs["public_coordinate_staging_summary.json"] = digest(
        work / "public_coordinate_staging_summary.json"
    )
    write_json(
        work / "coordinate_staging_manifest.json",
        dict(
            schema_version=1,
            status="coordinate_staging_partial",
            inventory_input_hashes=input_hashes,
            benchmark_artifact_sha256=benchmark_hashes,
            workbook_sha256=workbook["sha256"],
            source_hashes=inventory["source_hashes"],
            output_hashes=outputs,
            source_inputs_unchanged=True,
            benchmark_unchanged=True,
            summary=summary,
        ),
    )
    return staged


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
    parser.add_argument("--benchmark", default="work/pafko-full-reconciliation")
    args = parser.parse_args()
    print(json.dumps(build_staging(args.source_root, args.workspace, args.benchmark)["summary"]))
