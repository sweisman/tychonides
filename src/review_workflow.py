"""Shared, resumable operations for source-reviewed catalogue batches.

Review records are data. Historical interpretation belongs in those records;
this module orchestrates the existing compiler, provenance and export stages.
"""

from .review_migrations import rebind_provenance_inputs as rebind_provenance_inputs
from .review_migrations import begin_source_refresh as begin_source_refresh
from .review_migrations import begin_reference_refresh as begin_reference_refresh
from .review_migrations import verify_reference_refresh as verify_reference_refresh

from .review_preparation import materialize_review as materialize_review
from .review_preparation import record_update_plan as record_update_plan
from .review_preparation import apply_record_updates as apply_record_updates
from .review_preparation import inspect_range as inspect_range

from .review_state import read as read
from .review_state import rows as rows
from .review_state import path_key as path_key
from .review_state import checked_hashes as checked_hashes
from .review_state import preserve_rows as preserve_rows
from .review_state import source_texts as source_texts
from .review_state import edition_hashes as edition_hashes

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

from .core import digest
from .recovery import write_json_atomic
from .source_bindings import load_bindings

REPO = Path(__file__).resolve().parents[1]
PUBLIC = REPO / "work/mars-checkpoint-export"
STAGES = ("catalogue", "coordinate_staging", "assembly", "provenance", "public")
MANIFESTS = ("inventory", "table_staging", "narrative_staging", *STAGES[:-1])


def current_counts(workspace, public=PUBLIC):
    work, public = Path(workspace), Path(public)
    summary = read(public / "summary.json")
    sub, inspection = summary["reviewed_subset"], summary["inspection"]
    catalogue = read(work / "catalogue_manifest.json")["summary"]
    norm = catalogue["normalization_statuses"]
    if sum(norm.values()) != sub["assertions"]:
        raise ValueError("Catalogue and normalization totals differ")
    return dict(
        assertions=sub["assertions"],
        source_groups=sub["event_groups"],
        inspected_regions=inspection["inspected_candidate_spans"],
        inspected_source_lines=inspection["inspected_source_lines"],
        review_batches=catalogue["review_batches"],
        exact=norm.get("exact", 0),
        incomplete=norm.get("incomplete", 0),
        unsupported=norm.get("unsupported", 0),
    )


def progress_tally(checkpoint):
    verified = checkpoint["last_verified"]
    total = verified["candidate_regions"]
    inspected = verified["inspected_regions"]
    pending = (
        checkpoint.get("in_progress", {})
        if checkpoint["checkpoint_status"].startswith("in_progress")
        else {}
    )
    return dict(
        quantities=verified["assertions"],
        source_groups=verified["source_groups"],
        inspected_regions=inspected,
        candidate_regions=total,
        remaining_regions=total - inspected,
        region_coverage_percent=round(100 * inspected / total, 1) if total else 0.0,
        pending_quantities=pending.get("new_quantities", 0),
        pending_regions=pending.get("new_inspected_regions", 0),
    )


def repair_pending_columns(workspace, source_root, public, batches):
    """Repair only column pointers in an unverified tail, retaining every attempt."""
    from .catalog import compile_catalogue
    from .date_claims import project_date_claims
    from .public_checkpoint import public_assertion
    from .io import guard

    work = Path(workspace)
    batches = batches if isinstance(batches, list) else [batches]
    guard(work.resolve(), Path(source_root).resolve())
    if (work / "pafko.json").exists() or (work / "raw/mars.xls").exists():
        raise ValueError("Protected benchmark workspace")
    checkpoint = read(work / "recovery_checkpoint.json")
    progress = checkpoint.get("in_progress", {})
    if (
        not checkpoint.get("checkpoint_status", "").startswith("in_progress")
        or progress.get("operation") == "reference_inventory_refresh"
        or [b["id"] for b in batches] != progress.get("review_ids")
    ):
        raise ValueError("Column repair requires the current unverified review tail")
    ledger = read(work / "review_batches.json")
    prefix = read(work / progress["prior_review_ledger_backup"])
    retained = progress.get("column_repair_plan")
    if retained:
        checked_hashes(work, {retained["path"]: retained["sha256"]})
        plan = read(work / retained["path"])
        if plan["batches"] != batches:
            raise ValueError("Conflicting pending column repair")
        checked_hashes(work, {plan["prior_attempt"]: plan["prior_attempt_sha256"]})
        before = read(work / plan["prior_attempt"])
    else:
        before = ledger
        if digest(work / "review_batches.json") != progress["review_ledger_sha256"]:
            raise ValueError("Pending review ledger fingerprint changed")
    if (
        before[: len(prefix)] != prefix
        or [b["id"] for b in before[len(prefix) :]] != progress["review_ids"]
    ):
        raise ValueError("Verified review prefix changed")
    old = before[len(prefix) :]
    permitted = copy.deepcopy(old)
    changes = []
    texts = source_texts(work, source_root)
    source_lines = {volume: text.splitlines() for volume, text in texts.items()}
    if len(permitted) != len(batches):
        raise ValueError("Column repair cannot add or remove reviews")
    for prior, new in zip(permitted, batches, strict=True):
        if len(prior.get("assertions", [])) != len(new.get("assertions", [])):
            raise ValueError("Column repair cannot add or remove quantities")
        for a, b in zip(prior.get("assertions", []), new.get("assertions", []), strict=True):
            if a.get("column") != b.get("column"):
                column = b.get("column")
                if column is None:
                    if source_lines[new["volume"]][b["line"] - 1].lstrip().startswith("|"):
                        raise ValueError("Printed table cells require a column pointer")
                elif type(column) is not int or column < 1:
                    raise ValueError("Invalid repaired column")
                changes.append(
                    dict(
                        review_id=prior["id"],
                        key=a["key"],
                        old_column=a.get("column"),
                        new_column=b["column"],
                    )
                )
                a["column"] = b["column"]
    if permitted != batches or not changes:
        raise ValueError("Only pending column pointers may change")
    expected = prefix + batches
    if ledger not in (before, expected):
        raise ValueError("Review ledger differs from both retained repair states")
    if retained and retained["status"] == "committed" and ledger == expected:
        return dict(status="already_repaired", prior_attempt=plan["prior_attempt"])
    compiled = compile_catalogue(
        expected,
        texts,
        rows(work / "inventory_spans.jsonl"),
        edition_hashes=edition_hashes(work),
        source_bindings=load_bindings(work),
    )
    temporal = project_date_claims(compiled["contexts"], compiled["assertions"], compiled["events"])
    prior = rows(work / progress["prior_public_snapshot"])
    prior_by_id = {a["id"]: a for a in prior}
    # Preserve the public projection, including its derived date/control links.
    projected = [
        public_assertion(
            dict(
                a,
                source_date_claim_ids=temporal["assertion_date_ids"][a["id"]],
                workbook_control_id=prior_by_id.get(a["id"], {}).get("workbook_control_id"),
            )
        )
        for a in compiled["assertions"]
    ]
    preserve_rows(prior, projected)
    if not retained:
        backup = (
            "recovery/review-ledger-before-column-repair-"
            + digest(work / "review_batches.json")
            + ".json"
        )
        write_json_atomic(work / backup, before)
        plan = dict(
            batches=batches,
            changes=changes,
            prior_attempt=backup,
            prior_attempt_sha256=digest(work / backup),
        )
        path = (
            "recovery/column-repair-"
            + hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
            + ".json"
        )
        write_json_atomic(work / path, plan)
        retained = dict(path=path, sha256=digest(work / path), status="prepared")
        progress.update(column_repair_plan=retained, stage="column_repair_ready")
        write_json_atomic(work / "recovery_checkpoint.json", checkpoint)
    write_json_atomic(work / "review_batches.json", expected)
    retained["status"] = "committed"
    progress.update(
        review_ledger_sha256=digest(work / "review_batches.json"),
        completed_build_stages=[],
        stage="review_ledger_committed_builds_pending",
    )
    write_json_atomic(work / "recovery_checkpoint.json", checkpoint)
    return dict(status="columns_repaired", changes=changes, prior_attempt=plan["prior_attempt"])


def append_review(workspace, source_root, public, batch):
    from .io import guard
    from .catalog import compile_catalogue
    from .date_claims import project_date_claims
    from .public_checkpoint import public_assertion, public_derivation, validate_links

    listed = isinstance(batch, list)
    batches = batch if listed else [batch]
    if not batches or any(
        not isinstance(b, dict) or not isinstance(b.get("id"), str) for b in batches
    ):
        raise ValueError("Supply a reviewed record or nonempty list of reviewed records")
    review_ids = [b["id"] for b in batches]
    if len(set(review_ids)) != len(review_ids):
        raise ValueError("Duplicate review identity in list")
    work, public = Path(workspace), Path(public)
    guard(work.resolve(), Path(source_root).resolve())
    ledger_path, checkpoint_path = work / "review_batches.json", work / "recovery_checkpoint.json"
    ledger, checkpoint = read(ledger_path), read(checkpoint_path)
    texts = source_texts(work, source_root)
    spans = rows(work / "inventory_spans.jsonl")
    batches = [
        materialize_review(b, texts[b["volume"]], spans) if "cell_groups" in b else b
        for b in batches
    ]
    merged_updates = {}
    for b in batches:
        for name, records in b.get("record_updates", {}).items():
            merged_updates.setdefault(name, []).extend(records)
    updates = record_update_plan(work, dict(record_updates=merged_updates))

    def receipt(status):
        return dict(
            status=status,
            **({"review_ids": review_ids} if listed else {"review_id": review_ids[0]}),
        )

    existing = [r for r in ledger if r["id"] in review_ids]
    if existing:
        indexed = {r["id"]: r for r in existing}
        if len(existing) != len(batches) or any(indexed.get(b["id"]) != b for b in batches):
            raise ValueError("Conflicting review identity or payload")
        progress = checkpoint.get("in_progress", {})
        if (
            set(progress.get("review_ids", [])) == set(review_ids)
            and progress.get("review_ids") != review_ids
        ):
            raise ValueError("Conflicting review order during recovery")
        if progress.get("review_ids") == review_ids:
            backup = read(work / progress["prior_review_ledger_backup"])
            if ledger != backup + batches:
                raise ValueError("Review ledger prefix changed during recovery")
            progress.setdefault("supplement_backups", {}).update(
                apply_record_updates(work, updates)
            )
            progress.update(
                stage="review_ledger_committed_builds_pending",
                review_ledger_sha256=digest(ledger_path),
            )
            write_json_atomic(checkpoint_path, checkpoint)
        return receipt("already_appended")
    if checkpoint.get("checkpoint_status") != "verified_resume_ready":
        raise ValueError("Finish the current review before appending another")
    evidence = {}
    for b in batches:
        basis = b.get("basis", {})
        hashes = basis.get("evidence_hashes", {})
        if not isinstance(hashes, dict) or (
            not hashes and basis.get("kind") != "final_edition_review"
        ):
            raise ValueError(
                "Reviewed records require a final-edition basis or retained scan evidence hashes"
            )
        checked_hashes(work, hashes)
        evidence.update(hashes)
    last = checkpoint.get("last_verified", {})
    if last.get("artifact_snapshot"):
        checked_hashes(REPO, read(work / last["artifact_snapshot"]))
    compiled = compile_catalogue(
        ledger + batches,
        texts,
        spans,
        edition_hashes=edition_hashes(work),
        source_bindings=load_bindings(work),
    )
    project_date_claims(compiled["contexts"], compiled["assertions"], compiled["events"])
    public_rows = [public_assertion(a) for a in compiled["assertions"]]
    public_by_id = {a["id"]: a for a in public_rows}
    for derivation in compiled["derivations"]:
        public_derivation(derivation, public_by_id)
    series_ids = {a["series_id"] for a in public_rows if a.get("series_id")}
    validate_links(
        public_rows,
        compiled["events"],
        [
            dict(id=s, assertion_ids=[a["id"] for a in public_rows if a.get("series_id") == s])
            for s in series_ids
        ],
    )
    recovery = work / "recovery"
    recovery.mkdir(exist_ok=True)
    backup = recovery / ("review-ledger-" + digest(ledger_path) + ".json")
    if not backup.exists():
        backup.write_bytes(ledger_path.read_bytes())
    prior_public = recovery / (
        "public-quantities-" + digest(public / "reviewed_assertions.jsonl") + ".jsonl"
    )
    if not prior_public.exists():
        prior_public.write_bytes((public / "reviewed_assertions.jsonl").read_bytes())
    relocated_intervals = {r["review_id"]: r["current_interval"] for r in load_bindings(work)}
    previous_lines = {
        (b["volume"], n)
        for b in ledger
        for n in range(
            relocated_intervals.get(b["id"], b)["line_start"],
            relocated_intervals.get(b["id"], b)["line_end"] + 1,
        )
    }
    new_lines = {
        (b["volume"], n) for b in batches for n in range(b["line_start"], b["line_end"] + 1)
    }
    previous_regions = {s["span_id"] for b in ledger for s in b["span_decisions"]}
    new_regions = {s["span_id"] for b in batches for s in b["span_decisions"]}
    progress = dict(
        review_ids=review_ids,
        stage="review_ledger_append_ready",
        prior_review_ledger_backup=str(backup.relative_to(work)),
        prior_public_snapshot=str(prior_public.relative_to(work)),
        evidence_hashes=evidence,
        prior_verified_snapshot=last.get("artifact_snapshot"),
        source_intervals=[[b["line_start"], b["line_end"]] for b in batches],
        source_ranges=[
            dict(
                volume=b["volume"],
                line_start=b["line_start"],
                line_end=b["line_end"],
                review_id=b["id"],
            )
            for b in batches
        ],
        new_quantities=sum(len(b.get("assertions", [])) for b in batches),
        new_source_groups=sum(len(b.get("events", [])) for b in batches),
        new_inspected_regions=len(new_regions - previous_regions),
        new_inspected_source_lines=len(new_lines - previous_lines),
        source_findings=[finding for b in batches for finding in b.get("source_findings", [])],
        completed_build_stages=[],
    )
    checkpoint.update(
        checkpoint_status="in_progress_after_verified_checkpoint", in_progress=progress
    )
    write_json_atomic(checkpoint_path, checkpoint)
    write_json_atomic(ledger_path, ledger + batches)
    progress["supplement_backups"] = apply_record_updates(work, updates)
    progress.update(
        stage="review_ledger_committed_builds_pending", review_ledger_sha256=digest(ledger_path)
    )
    write_json_atomic(checkpoint_path, checkpoint)
    return receipt("appended")


def valid_manifest(work, source_root, benchmark, manifest, output_base=None):
    m = read(manifest)
    if "source_reference_reviews_sha256" in m:
        checked_hashes(
            work, {"source_reference_reviews.json": m["source_reference_reviews_sha256"]}
        )
    for field in (
        "input_hashes",
        "inventory_input_hashes",
        "input_manifest_hashes",
        "upstream_files",
        "upstream_hashes",
    ):
        checked_hashes(work, m.get(field, {}))
    checked_hashes(output_base or work, m.get("output_hashes", {}))
    checked_hashes(source_root, m.get("source_hashes", {}))
    checked_hashes(benchmark, m.get("benchmark_artifact_sha256", {}))


def build(workspace, source_root, benchmark, repeat=False):
    from .catalog import build_workspace
    from .coordinate_staging import build_staging
    from .assembly import build_assembly
    from .provenance import build_provenance
    from .public_checkpoint import build_checkpoint

    work, benchmark = Path(workspace), Path(benchmark)
    if (
        read(work / "recovery_checkpoint.json")
        .get("in_progress", {})
        .get("column_repair_plan", {})
        .get("status")
        == "prepared"
    ):
        raise ValueError("Resume the prepared column repair before rebuilding")
    if (
        read(work / "recovery_checkpoint.json")["in_progress"].get("operation")
        == "reference_inventory_refresh"
    ):
        from .io import inventory
        from .table_staging import build_tables
        from .narrative_staging import build_narratives

        checkpoint = read(work / "recovery_checkpoint.json")
        progress = checkpoint["in_progress"]
        for name, action in (
            (
                "inventory",
                lambda: inventory(
                    SimpleNamespace(
                        source_root=source_root,
                        output=work,
                        benchmark=benchmark,
                        volumes=read(work / progress["prior_inventory_manifest"])["volumes"],
                    )
                ),
            ),
            ("table_staging", lambda: build_tables(source_root, work)),
            ("narrative_staging", lambda: build_narratives(source_root, work)),
        ):
            completed = progress.setdefault("completed_reference_stages", [])
            if not repeat and name in completed:
                try:
                    valid_manifest(work, source_root, benchmark, work / (name + "_manifest.json"))
                    verify_reference_refresh(work)
                    continue
                except (ValueError, OSError):
                    pass
            progress["stage"] = "refreshing_" + name
            write_json_atomic(work / "recovery_checkpoint.json", checkpoint)
            action()
            verify_reference_refresh(work)
            if name not in completed:
                completed.append(name)
            progress["stage"] = "refreshed_" + name
            write_json_atomic(work / "recovery_checkpoint.json", checkpoint)
            print(name + " refreshed", flush=True)
    actions = (
        lambda: build_workspace(source_root, work),
        lambda: build_staging(source_root, work, benchmark),
        lambda: build_assembly(source_root, work),
        lambda: build_provenance(source_root, work),
        lambda: build_checkpoint(work, benchmark),
    )
    for name, action in zip(STAGES, actions, strict=True):
        checkpoint = read(work / "recovery_checkpoint.json")
        progress = checkpoint["in_progress"]
        completed = progress.setdefault("completed_build_stages", [])
        manifest = (
            PUBLIC / "manifest.json" if name == "public" else work / (name + "_manifest.json")
        )
        if not repeat and name in completed:
            try:
                valid_manifest(
                    work, source_root, benchmark, manifest, PUBLIC if name == "public" else None
                )
                continue
            except (ValueError, OSError):
                pass
        progress["stage"] = ("repeat_" if repeat else "building_") + name
        write_json_atomic(work / "recovery_checkpoint.json", checkpoint)
        action()
        if name not in completed:
            completed.append(name)
        progress["stage"] = "built_" + name
        write_json_atomic(work / "recovery_checkpoint.json", checkpoint)
        print(name + " complete", flush=True)


def fingerprints(work, public=PUBLIC):
    work, public = Path(work), Path(public)
    checkpoint = read(work / "recovery_checkpoint.json")
    previous = (
        checkpoint.get("in_progress", {}).get("prior_verified_snapshot")
        or checkpoint["last_verified"]["artifact_snapshot"]
    )
    paths = {Path(n) for n in read(work / previous)}
    affected = set()
    for name in MANIFESTS:
        manifest = work / (name + "_manifest.json")
        paths.add(manifest)
        outputs = {work / n for n in read(manifest).get("output_hashes", {})}
        paths.update(outputs)
        if (
            name in STAGES
            or checkpoint.get("in_progress", {}).get("operation") == "reference_inventory_refresh"
        ):
            affected.update([manifest, *outputs])
    manifest = public / "manifest.json"
    paths.add(manifest)
    outputs = {public / n for n in read(manifest)["output_hashes"]}
    paths.update(outputs)
    affected.update([manifest, *outputs])
    return {path_key(p): digest(p) for p in paths}, {path_key(p) for p in affected}


def check(workspace, source_root, benchmark, label, repeat=False, tests=False):
    work, benchmark = Path(workspace), Path(benchmark)
    checkpoint = read(work / "recovery_checkpoint.json")
    progress = checkpoint["in_progress"]
    expansion = (
        verify_reference_refresh(work)
        if progress.get("operation") == "reference_inventory_refresh"
        else None
    )
    checked_hashes(work, progress.get("evidence_hashes", {}))
    if digest(work / "review_batches.json") != progress["review_ledger_sha256"]:
        raise ValueError("Review ledger changed since append")
    ledger = read(work / "review_batches.json")
    old = read(work / progress["prior_review_ledger_backup"])
    if ledger[: len(old)] != old or [b["id"] for b in ledger[len(old) :]] != progress["review_ids"]:
        raise ValueError("Review ledger prefix or appended identities changed")
    for name in MANIFESTS:
        valid_manifest(work, source_root, benchmark, work / (name + "_manifest.json"))
    valid_manifest(work, source_root, benchmark, PUBLIC / "manifest.json", PUBLIC)
    inventory = read(work / "inventory_manifest.json")
    checked_hashes(benchmark, {"raw/mars.xls": read(benchmark / "workbook.json")["sha256"]})
    prior_path = work / progress.get(
        "prior_public_snapshot", "recovery/" + label + "-prior-public.jsonl"
    )
    prior, current = rows(prior_path), rows(PUBLIC / "reviewed_assertions.jsonl")
    direction_reviews = {}
    for assertion in rows(work / "assertions.jsonl"):
        for review in assertion.get("direction_review_history", []):
            if review["review_id"] in progress["review_ids"]:
                if assertion["id"] in direction_reviews:
                    raise ValueError("Competing direction reviews in one workflow run")
                direction_reviews[assertion["id"]] = review
    if len(direction_reviews) != sum(
        len(b.get("direction_reviews", [])) for b in ledger[len(old) :]
    ):
        raise ValueError("Direction review applications differ from the appended ledger")
    control_reviews = {}
    coordinates = {r["legacy_source_record_id"]: r for r in rows(work / "staged_coordinates.jsonl")}
    prior_ids = {r["id"] for r in prior}
    for batch in ledger[len(old) :]:
        for review in batch.get("record_updates", {}).get("coordinate_adjudications.json", []):
            aid = review.get("reviewed_assertion_id")
            if aid is None:
                continue
            coordinate = coordinates.get(review["source_record_id"])
            if (
                coordinate is None
                or coordinate.get("classification_id") != review["id"]
                or coordinate.get("reviewed_assertion_id") != aid
            ):
                raise ValueError("Reviewed control link differs from its staged source identity")
            control = coordinate.get("benchmark_control_id")
            if control is None or aid not in prior_ids:
                continue
            if aid in control_reviews and control_reviews[aid] != control:
                raise ValueError("Competing control identity reviews")
            control_reviews[aid] = control
    control_changes = [
        r["id"]
        for r in prior
        if r["id"] in control_reviews and r.get("workbook_control_id") != control_reviews[r["id"]]
    ]
    direction_changes = preserve_rows(prior, current, direction_reviews, control_reviews)
    before, affected = fingerprints(work)
    previous = read(work / progress["prior_verified_snapshot"])
    upstream = set(before) - affected
    if any(previous.get(n) != before[n] for n in upstream):
        raise ValueError("Upstream inventory artifacts changed during reviewed-only work")
    if repeat:
        write_json_atomic(work / ("recovery/" + label + "-pre-repeat-output-hashes.json"), before)
        build(work, source_root, benchmark, repeat=True)
        after, _ = fingerprints(work)
        if after != before:
            raise ValueError("Repeated outputs differ")
    for n in read(PUBLIC / "manifest.json")["output_hashes"]:
        content = (PUBLIC / n).read_text(encoding="utf-8")
        if any(
            x in content
            for x in (
                "/home/",
                "/site/",
                "prepub.md",
                "text_original",
                "private_source",
                "line_start",
                "context_keys",
                "month_original",
                "daypart_original",
            )
        ):
            raise ValueError("Private source fields in public output: " + n)
    test_result = None
    if tests:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        print(output[-1000:], flush=True)
        if result.returncode:
            raise ValueError("Software checks failed")
        match = re.search(r"Ran (\d+) tests?", output)
        if not match:
            raise ValueError("Missing software-check result")
        test_result = dict(tests_passed=int(match.group(1)), returncode=0)
        write_json_atomic(work / (label + "_test_result.json"), test_result)
    counts = current_counts(work)
    previous_report = work / (label + "_workflow_verification.json")
    retained = read(previous_report) if previous_report.exists() else {}
    snapshot_path = work / ("recovery/" + label + "-verified-output-hashes.json")
    if (
        retained.get("review_ledger_sha256") != digest(work / "review_batches.json")
        or not snapshot_path.exists()
        or read(snapshot_path) != before
    ):
        retained = {}
    report = dict(
        status="verified",
        counts=counts,
        review_ids=progress["review_ids"],
        review_ledger_sha256=digest(work / "review_batches.json"),
        prior_public_quantities_unchanged=len(prior)
        - len(set(direction_changes) | set(control_changes)),
        reviewed_control_link_changes=len(control_changes),
        reviewed_control_link_change_ids=control_changes,
        reviewed_direction_changes=len(direction_changes),
        reviewed_direction_change_ids=direction_changes,
        repeat_artifacts_identical=len(affected)
        if repeat
        else retained.get("repeat_artifacts_identical"),
        upstream_artifacts_unchanged=len(upstream),
        snapshot_artifacts_verified=len(before),
        protected_benchmark_hashes_unchanged=len(inventory["benchmark_artifact_sha256"]),
        canonical_edition_fingerprints_unchanged=sum(
            n.endswith("_prepub.md") for n in inventory["source_hashes"]
        )
        - bool(
            progress.get("source_revision")
            and progress["source_revision"].get("kind") != "provenance_inputs_only"
        ),
        reviewed_canonical_source_revisions=int(
            bool(
                progress.get("source_revision")
                and progress["source_revision"].get("kind") != "provenance_inputs_only"
            )
        ),
        reviewed_provenance_input_revisions=int(
            progress.get("source_revision", {}).get("kind") == "provenance_inputs_only"
        ),
        public_privacy_checks="passed",
        tests=test_result or retained.get("tests"),
    )
    if expansion:
        report["inventory_expansion"] = expansion
    write_json_atomic(work / ("recovery/" + label + "-verified-output-hashes.json"), before)
    write_json_atomic(work / (label + "_workflow_verification.json"), report)
    return report


def finish(workspace, label, next_preparation=None, tracker_sequence=None):
    work = Path(workspace)
    report = read(work / (label + "_workflow_verification.json"))
    checked_hashes(REPO, read(work / ("recovery/" + label + "-verified-output-hashes.json")))
    if digest(work / "review_batches.json") != report["review_ledger_sha256"]:
        raise ValueError("Reviewed inputs changed")
    counts = current_counts(work)
    summary = read(PUBLIC / "summary.json")
    sub, t = summary["reviewed_subset"], summary["temporal_claims"]
    if counts != report["counts"]:
        raise ValueError("Verified totals changed")
    checkpoint = read(work / "recovery_checkpoint.json")
    state = read(work / "work_state.json")
    progress = checkpoint.get("in_progress") or checkpoint["completed_review"]
    if progress["review_ids"] != report["review_ids"]:
        raise ValueError("Review identities changed")
    current_review_ids = progress["review_ids"] or checkpoint["last_verified"]["review_ids"]
    tests = report.get("tests") or (
        read(work / (label + "_test_result.json"))
        if (work / (label + "_test_result.json")).exists()
        else None
    )
    state.update(
        source_assertions=counts["assertions"],
        source_events=counts["source_groups"],
        exact_normalizations=counts["exact"],
        incomplete_normalizations=counts["incomplete"],
        unsupported_normalizations=counts["unsupported"],
        inspected_spans=counts["inspected_regions"],
        inspected_source_lines=counts["inspected_source_lines"],
        reviewed_batches=counts["review_batches"],
        public_checkpoint_assertions=counts["assertions"],
        public_checkpoint_events=counts["source_groups"],
        public_checkpoint_assertions_linked_to_workbook_controls=sub[
            "assertions_linked_to_workbook_controls"
        ],
        public_checkpoint_assertions_without_workbook_control_links=sub[
            "assertions_without_workbook_control_links"
        ],
        reviewed_batch_benchmark_controls=sub["assertions_linked_to_workbook_controls"],
        reviewed_unlinked_recorded_mars_declination_assertions=sub[
            "unlinked_recorded_mars_declinations"
        ]["assertion_count"],
        public_derivations=sub["derivations"],
        arithmetic_agreements=sub["arithmetic_agreements"],
        arithmetic_disagreements=sub["arithmetic_disagreements"],
        historical_algorithms_uncomputed=sum(
            d["computed_magnitude"] is None for d in rows(work / "derivations.jsonl")
        ),
        public_date_claims=t["date_claims"],
        public_assertions_with_source_date_claims=t["assertions_with_source_date_claims"],
        public_events_with_source_date_claims=t["events_with_source_date_claims"],
        public_assertions_with_multiple_source_date_claims=t[
            "assertions_with_multiple_source_date_claims"
        ],
        reviewed_source_diagrams=sum(
            c["kind"] == "source_diagram" for c in rows(work / "contexts.jsonl")
        ),
        current_review_batch=current_review_ids[-1],
        current_review_batches=current_review_ids,
        snapshot_artifacts_verified=report["snapshot_artifacts_verified"],
        upstream_artifacts_preserved=report["upstream_artifacts_unchanged"],
    )
    new_ids = {
        a["id"] for a in rows(work / "assertions.jsonl") if a["review_id"] in progress["review_ids"]
    }
    published = rows(PUBLIC / "reviewed_assertions.jsonl")
    state.update(
        current_batch_new_control_links=sum(
            bool(a.get("workbook_control_id")) for a in published if a["id"] in new_ids
        ),
        new_unlinked_recorded_mars_declinations=len(
            new_ids & set(sub["unlinked_recorded_mars_declinations"]["assertion_ids"])
        ),
        current_batch_repeat_artifacts_identical=report["repeat_artifacts_identical"],
    )
    if tests:
        state["tests_passed"] = tests["tests_passed"]
    assembly = read(work / "assembly_manifest.json")["summary"]
    coordinate = read(work / "coordinate_staging_manifest.json")["summary"]
    state.update(
        assembled_catalogue_views=assembly["catalogue_views"],
        source_context_records=assembly["source_contexts"],
        source_location_links=assembly["location_links"],
        multiple_literal_bindings=assembly["source_anchor_statuses"][
            "ambiguous_literal_occurrences"
        ],
        views_linked_to_edition_issues=assembly["views_linked_to_edition_issues"],
        reviewed_coordinate_assertion_overlaps=coordinate["reviewed_assertion_overlaps"],
        reviewed_coordinate_roles=coordinate["reviewed_coordinate_roles"],
        coordinate_context_classifications=coordinate["coordinate_classifications"],
        nonexcluded_coordinates_without_control=coordinate[
            "nonexcluded_coordinates_without_workbook_control"
        ],
    )
    if next_preparation:
        previous_preparation = checkpoint.get("next_review_preparation")
        if previous_preparation and (work / previous_preparation).exists():
            previous = read(work / previous_preparation)
            ranges = progress.get("source_ranges")
            matching_volume = not ranges or any(
                r["volume"] == previous.get("volume")
                and [r["line_start"], r["line_end"]] == previous.get("source_interval")
                for r in ranges
            )
            if (
                previous.get("source_interval") in progress.get("source_intervals", [])
                and matching_volume
            ):
                previous.update(
                    status="complete_verified",
                    review_ids=progress["review_ids"],
                    verification=label + "_workflow_verification.json",
                )
                write_json_atomic(work / previous_preparation, previous)
        preparation = read(work / next_preparation)
        state["next_review_preparation"] = next_preparation
        checkpoint["next_review_preparation"] = next_preparation
        interval = preparation.get("source_interval")
        fallback = f"Review the prepared source interval {interval}, using {next_preparation}; preserve frozen identities and source uncertainties."
        checkpoint["next_action"] = preparation.get("next_action", fallback)
        state["next_actions"][0] = checkpoint["next_action"]
    state["next_actions"] = [
        re.sub(
            r"\d+ unlinked recorded Mars declinations",
            str(state["reviewed_unlinked_recorded_mars_declination_assertions"])
            + " unlinked recorded Mars declinations",
            re.sub(
                r"(?:Six|Seven|Eight|\d+) retained diagrams",
                str(state["reviewed_source_diagrams"]) + " retained diagrams",
                x,
            ),
        )
        for x in state["next_actions"]
    ]
    snapshot = "recovery/" + label + "-verified-output-hashes.json"
    checkpoint["last_verified"] = dict(
        review_id=current_review_ids[-1],
        review_ids=current_review_ids,
        assertions=counts["assertions"],
        source_groups=counts["source_groups"],
        inspected_regions=counts["inspected_regions"],
        candidate_regions=len(rows(work / "inventory_spans.jsonl")),
        exact=counts["exact"],
        incomplete=counts["incomplete"],
        unsupported=counts["unsupported"],
        tests_passed=state.get("tests_passed"),
        repeat_artifacts_identical=report["repeat_artifacts_identical"],
        upstream_artifacts_unchanged=report["upstream_artifacts_unchanged"],
        snapshot_artifacts_verified=report["snapshot_artifacts_verified"],
        artifact_snapshot=snapshot,
        verification_reports=[label + "_workflow_verification.json"],
    )
    checkpoint.update(
        goal_status="active", checkpoint_status="verified_local_tracker_update_pending"
    )
    checkpoint["continuation_audit"] = dict(
        previous_turn="progress",
        current_turn="progress",
        evidence="Shared workflow verification: " + label + "_workflow_verification.json",
    )
    if tracker_sequence is not None:
        checkpoint.update(
            checkpoint_status="verified_resume_ready",
            tracker_sequence=tracker_sequence,
            tracker_readback_verified=True,
        )
        checkpoint["continuation_audit"].update(
            tracker_sequence=tracker_sequence, tracker_readback_verified=True
        )
        checkpoint["completed_review"] = checkpoint.pop("in_progress", progress)
    progress["stage"] = checkpoint["checkpoint_status"]
    state["running_tally"] = progress_tally(checkpoint)
    write_json_atomic(work / "work_state.json", state)
    write_json_atomic(work / "recovery_checkpoint.json", checkpoint)
    write_json_atomic(
        work / (label + "_review_notes.json"),
        dict(
            status=checkpoint["checkpoint_status"],
            verification=report,
            findings=progress.get("source_findings", []),
        ),
    )
    tally = state["running_tally"]
    text = (
        f"# Extraction status\n\n{counts['assertions']:,} quantities in {counts['source_groups']:,} groups.\n\n"
        f"Reviewed regions: {counts['inspected_regions']:,}/{tally['candidate_regions']:,} "
        f"({tally['region_coverage_percent']:.1f}%); {tally['remaining_regions']:,} remain.\n\n"
        "| Quantity | Count |\n| --- | ---: |\n"
        + "".join(
            "| " + k.replace("_", " ") + " | " + str(v) + " |\n"
            for k, v in sorted(sub["quantities"].items())
        )
    )
    (work / "status.md").write_text(text, encoding="utf-8")
    return counts


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "operation",
        choices=[
            "inspect",
            "append",
            "repair-columns",
            "refresh-references",
            "refresh-source",
            "migrate-source",
            "run",
            "build",
            "check",
            "finish",
            "status",
        ],
    )
    p.add_argument("--workspace", default="work/mars-catalogue")
    p.add_argument("--source-root", default=os.environ.get("TYCHONIDES_SOURCE_ROOT"))
    p.add_argument("--benchmark", default="work/pafko-full-reconciliation")
    p.add_argument("--label")
    p.add_argument("--review", help="Reviewed JSON record or nonempty list of reviewed records")
    p.add_argument("--volume", type=int)
    p.add_argument("--source-id", help="Registered source identity for a named historical edition")
    p.add_argument("--start", type=int)
    p.add_argument("--end", type=int)
    p.add_argument("--repeat", action="store_true")
    p.add_argument("--tests", action="store_true")
    p.add_argument("--next-preparation")
    p.add_argument("--tracker-sequence", type=int)
    p.add_argument("--output", help="Save inspection JSON inside the working directory")
    a = p.parse_args()
    from .checkout import require_checkout

    require_checkout(p)
    work = Path(a.workspace)
    inventory_path = work / "inventory.json"
    if a.source_id or (
        inventory_path.exists()
        and read(inventory_path).get("status") == "inventory_only_not_source_review"
    ):
        from .historical_reviews import dispatch

        dispatch(a, p)
        return
    if a.operation in ("run", "build", "check", "finish") and not a.label:
        p.error("--label identifies the retained verification record")
    if (
        a.operation in ("append", "repair-columns", "refresh-references", "migrate-source")
        and not a.review
    ):
        p.error("--review supplies the reviewed JSON record")
    if a.operation == "inspect" and any(x is None for x in (a.volume, a.start, a.end)):
        p.error("inspect requires --volume, --start and --end")
    if a.operation == "refresh-source" and a.volume is None:
        p.error("refresh-source requires --volume")
    if a.operation == "status":
        checkpoint = read(work / "recovery_checkpoint.json")
        result = dict(tally=progress_tally(checkpoint), checkpoint=checkpoint["checkpoint_status"])
    elif a.operation == "finish":
        result = finish(work, a.label, a.next_preparation, a.tracker_sequence)
    else:
        if not a.source_root:
            p.error("Set TYCHONIDES_SOURCE_ROOT or --source-root")
        if a.operation == "inspect":
            result = inspect_range(work, a.source_root, a.volume, a.start, a.end)
            if a.output:
                from .io import guard

                guard(work.resolve(), Path(a.source_root).resolve())
                target = (work / a.output).resolve()
                if not target.is_relative_to(work.resolve()):
                    p.error("Inspection output must remain inside the working directory")
                write_json_atomic(target, result)
                result = dict(
                    status=result["status"],
                    inspection=str(target),
                    source_lines=len(result["source_lines"]),
                    candidate_spans=len(result["candidate_spans"]),
                    staged_cells=len(result["staged_cells"]),
                )
        elif a.operation == "append":
            result = append_review(work, a.source_root, PUBLIC, read(a.review))
        elif a.operation == "repair-columns":
            result = repair_pending_columns(work, a.source_root, PUBLIC, read(a.review))
        elif a.operation == "refresh-references":
            result = begin_reference_refresh(work, a.source_root, PUBLIC, read(a.review))
        elif a.operation == "refresh-source":
            result = begin_source_refresh(work, a.source_root, PUBLIC, a.volume)
        elif a.operation == "migrate-source":
            binding = read(a.review)
            result = begin_source_refresh(
                work, a.source_root, PUBLIC, binding["volume"], binding=binding
            )
        else:
            if not a.label:
                p.error("--label identifies the retained verification record")
            if a.operation in ("build", "run"):
                build(work, a.source_root, a.benchmark)
            result = (
                check(work, a.source_root, a.benchmark, a.label, a.repeat, a.tests)
                if a.operation in ("check", "run")
                else {"status": "built"}
            )
            if a.operation == "run":
                finish(work, a.label, a.next_preparation)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
