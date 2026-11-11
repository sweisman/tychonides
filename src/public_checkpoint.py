"""Export a numeric reviewed subset and aggregate progress, never working prose."""

from .public_assertions import public_assertion as public_assertion

from .public_relationships import identifier as identifier
from .public_relationships import public_derivation as public_derivation
from .public_relationships import validate_links as validate_links

import json
import re
from collections import Counter
from pathlib import Path

from .core import digest
from .date_claims import project_date_claims, validate_date_links

from .public_policy import SUBJECTS as SUBJECTS
from .public_policy import REFERENCES as REFERENCES
from .public_policy import QUANTITIES as QUANTITIES
from .public_policy import ROLES as ROLES
from .public_policy import FLAGS as FLAGS
from .public_policy import FLAGS_EQUAL_VALUE as FLAGS_EQUAL_VALUE


def public_counts(source, keys):
    out = {}
    for key in keys:
        value = source[key]
        if type(value) is not int or value < 0:
            raise ValueError("Public count must be a nonnegative integer")
        out[key] = value
    return out


def reviewed_control_links(coordinates):
    links = {}
    used = set()
    for row in coordinates:
        aid = row.get("reviewed_assertion_id")
        control = row.get("benchmark_control_id")
        if aid is None or control is None:
            continue
        identifier(aid, "assertion")
        if not re.fullmatch(r"Sheet1:\d+", control) or aid in links or control in used:
            raise ValueError("Invalid or duplicate reviewed workbook link")
        links[aid] = control
        used.add(control)
    return links


def unlinked_recorded_mars_declinations(assertions):
    """Source assertion identities only; no independence or full omission census."""
    return sorted(
        row["id"]
        for row in assertions
        if row["quantity"] == "declination"
        and row["subject"] == "Mars"
        and row["role"] in ("recorded_coordinate", "recorded_reading", "repeated_reading")
        and not row.get("workbook_control_id")
    )


def build_checkpoint(workspace, benchmark):
    from .io import write_json, write_csv
    from .recovery import write_text_atomic

    work = Path(workspace).resolve()
    base = Path(benchmark).resolve()
    repo = Path(__file__).resolve().parents[1]
    out = (repo / "work" / "mars-checkpoint-export").resolve()
    if (
        not out.is_relative_to(repo / "work")
        or out.is_relative_to(work)
        or work.is_relative_to(out)
    ):
        raise ValueError("Unsafe public destination")
    manifests = (
        "inventory_manifest.json",
        "catalogue_manifest.json",
        "coordinate_staging_manifest.json",
        "table_staging_manifest.json",
        "narrative_staging_manifest.json",
        "assembly_manifest.json",
        "provenance_manifest.json",
    )
    hashes = {name: digest(work / name) for name in manifests}
    for name in manifests:
        manifest = json.loads((work / name).read_text(encoding="utf-8"))
        for field in ("input_hashes", "output_hashes"):
            for relative, sha in manifest.get(field, {}).items():
                path = (work / relative).resolve()
                if not path.is_relative_to(work) or digest(path) != sha:
                    raise ValueError("Stale checkpoint input/output")
    inventory = json.loads((work / "inventory_manifest.json").read_text(encoding="utf-8"))
    for relative, sha in inventory["benchmark_artifact_sha256"].items():
        path = (base / relative).resolve()
        if not path.is_relative_to(base) or digest(path) != sha:
            raise ValueError("Benchmark fingerprint changed")
    load = lambda n: json.loads((work / n).read_text(encoding="utf-8"))
    records = lambda n: [json.loads(s) for s in (work / n).read_text(encoding="utf-8").splitlines()]
    links = reviewed_control_links(records("staged_coordinates.jsonl"))
    source_assertions = records("assertions.jsonl")
    source_events = records("events.jsonl")
    temporal = project_date_claims(records("contexts.jsonl"), source_assertions, source_events)
    date_claims = temporal["date_claims"]
    assertions = [
        public_assertion(
            dict(
                r,
                workbook_control_id=links.get(r["id"]),
                source_date_claim_ids=temporal["assertion_date_ids"][r["id"]],
            )
        )
        for r in source_assertions
    ]
    if not set(links) <= {r["id"] for r in assertions}:
        raise ValueError("Reviewed workbook link has no public assertion")
    events = [
        dict(
            id=identifier(r["id"], "event"),
            clock_assertion_id=identifier(r["clock_assertion_id"], "assertion"),
            epoch_assertion_id=identifier(r["epoch_assertion_id"], "assertion"),
            source_date_claim_ids=temporal["event_date_ids"][r["id"]],
        )
        for r in source_events
    ]
    series = [
        dict(id=sid, assertion_ids=sorted(r["id"] for r in assertions if r["series_id"] == sid))
        for sid in sorted({r["series_id"] for r in assertions if r["series_id"]})
    ]
    validate_links(assertions, events, series)
    validate_date_links(assertions, events, date_claims, series)
    by_assertion = {r["id"]: r for r in assertions}
    derivations = [public_derivation(r, by_assertion) for r in records("derivations.jsonl")]
    unlinked_declinations = unlinked_recorded_mars_declinations(assertions)
    summary = dict(
        schema_version=2,
        status="partial_reviewed_checkpoint_not_complete_mars_catalogue",
        project="Tychonides — an Ars Astronomica project",
        bibliography_registry="../../src/data/public_sources.json",
        complete_mars_inventory=False,
        measurement_count=None,
        accepted_absolute_timestamps=0,
        temporal_claims=dict(
            date_claims=len(date_claims),
            assertions_with_source_date_claims=sum(
                bool(r["source_date_claim_ids"]) for r in assertions
            ),
            events_with_source_date_claims=sum(bool(r["source_date_claim_ids"]) for r in events),
            assertions_with_multiple_source_date_claims=sum(
                len(r["source_date_claim_ids"]) > 1 for r in assertions
            ),
            link_basis="explicit_review_context_ids",
            link_interpretation="source_context_only",
            accepted_observing_dates=0,
        ),
        reviewed_subset=dict(
            assertions=len(assertions),
            event_groups=len(events),
            derivations=len(derivations),
            arithmetic_agreements=sum(r["arithmetic_agrees"] is True for r in derivations),
            arithmetic_disagreements=sum(r["arithmetic_agrees"] is False for r in derivations),
            assertions_linked_to_workbook_controls=len(links),
            assertions_without_workbook_control_links=len(assertions) - len(links),
            unlinked_recorded_mars_declinations=dict(
                assertion_count=len(unlinked_declinations),
                assertion_ids=unlinked_declinations,
                independent_measurement_count=None,
                coverage_status="partial_reviewed_subset",
            ),
            quantities=dict(sorted(Counter(r["quantity"] for r in assertions).items())),
            roles=dict(sorted(Counter(r["role"] for r in assertions).items())),
        ),
        inventory=public_counts(
            load("public_inventory_summary.json"),
            ("source_lines_screened", "candidate_spans", "benchmark_controls_covered"),
        ),
        inspection=public_counts(
            load("public_catalogue_preview.json")["summary"],
            ("inspected_source_lines", "inspected_candidate_spans"),
        ),
        coordinates=public_counts(
            load("public_coordinate_staging_summary.json"),
            (
                "coordinate_candidates",
                "benchmark_controls",
                "coordinates_without_workbook_control",
                "nonexcluded_coordinates_without_workbook_control",
                "coordinate_classifications",
            ),
        ),
        coordinate_normalizations=public_counts(
            load("public_coordinate_staging_summary.json")["normalization_statuses"],
            ("exact", "incomplete", "unsupported"),
        ),
        assembly=public_counts(
            load("public_assembly_summary.json"),
            ("catalogue_views", "source_contexts", "location_links"),
        ),
        provenance=public_counts(
            load("public_provenance_summary.json"),
            (
                "note_definitions",
                "note_references",
                "duplicate_definition_keys",
                "views_without_upstream_pages_with_reference_loci",
                "views_with_reference_context_only",
                "accepted_inferred_note_pages",
            ),
        ),
        limits=[
            "Assertions and event groups are not independent-observation counts",
            "Only the reviewed subset is exported as numeric records; staging counts are broader",
            "Exact arithmetic does not establish observational accuracy",
            "Clock conventions, calendars, instruments and reductions require linked source review",
            "Original source expressions and detailed review evidence remain in protected working records",
        ],
    )
    if any(digest(work / n) != sha for n, sha in hashes.items()):
        raise ValueError("Checkpoint inputs changed")
    out.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for name, rows in (
        ("reviewed_assertions", assertions),
        ("event_groups", events),
        ("series_groups", series),
        ("date_claims", date_claims),
        ("derivations", derivations),
    ):
        path = out / (name + ".jsonl")
        write_text_atomic(
            path, "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows)
        )
        outputs[path.name] = digest(path)
        path = out / (name + ".csv")
        write_csv(path, rows)
        outputs[path.name] = digest(path)
    write_json(out / "summary.json", summary)
    outputs["summary.json"] = digest(out / "summary.json")
    write_json(
        out / "manifest.json",
        dict(
            schema_version=2,
            status=summary["status"],
            input_manifest_hashes=hashes,
            output_hashes=outputs,
        ),
    )
    return summary


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", default="work/mars-catalogue")
    p.add_argument("--benchmark", default="work/pafko-full-reconciliation")
    args = p.parse_args()
    from .checkout import require_checkout

    require_checkout(p)
    print(json.dumps(build_checkpoint(args.workspace, args.benchmark)))
