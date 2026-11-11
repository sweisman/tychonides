"""Review migrations: shared catalogue responsibilities."""

from .review_preparation import record_update_plan
from .review_preparation import apply_record_updates
from .review_state import read
from .review_state import rows
from .review_state import checked_hashes
from .review_state import preserve_rows
from .review_state import source_texts
from .review_state import edition_hashes
import copy
import hashlib
import json
from pathlib import Path
import re
from .core import digest
from .recovery import write_json_atomic
from .source_bindings import load_bindings, apply_span_bindings, rebind_review, review_sha

REPO = Path(__file__).resolve().parents[1]


def rebind_provenance_inputs(workspace, source_root, volume):
    """Resume a reference refresh after provenance-only edits outside its footprint."""
    from .inventory import inventory_text
    from .publication import load_publication

    work = Path(workspace)
    cp_path = work / "recovery_checkpoint.json"
    checkpoint = read(cp_path)
    progress = checkpoint.get("in_progress", {})
    if progress.get("operation") != "reference_inventory_refresh" or progress.get(
        "source_revision"
    ):
        raise ValueError("Provenance rebinding requires a pending reference refresh")
    checked_hashes(work, progress["reference_baseline_hashes"])
    witnesses = read(work / "witnesses.json")
    witness = next(w for w in witnesses if w["volume"] == volume)
    book = load_publication(source_root, volume)
    if book["source"] != witness["private_source"] or book["sha256"] != witness.get(
        "source_sha256", witness["edition_sha256"]
    ):
        raise ValueError("Provenance rebinding cannot change canonical text")
    source_texts(work, source_root)
    previous = read(work / progress["prior_inventory_manifest"])["source_hashes"]
    local = {n: h for n, h in previous.items() if Path(n).parent == Path(book["source"]).parent}
    if set(local) != set(book["source_hashes"]):
        raise ValueError("Provenance input set changed")
    changes = [
        dict(source=n, before=local[n], after=h)
        for n, h in book["source_hashes"].items()
        if local[n] != h
    ]
    if not changes or any(
        not re.fullmatch(r"batch_\d{3}\.md", Path(c["source"]).name) for c in changes
    ):
        raise ValueError("Only documented provenance batch revisions may be rebound")
    expected = dict(previous)
    expected.update(book["source_hashes"])
    checked_hashes(source_root, expected)
    references = read(work / "source_reference_reviews.json")
    old = [s for s in rows(work / "inventory_spans.jsonl") if s["volume"] == volume]
    current = inventory_text(
        book["text"],
        volume,
        witness["edition_sha256"],
        book["provenance"],
        reference_reviews=[r for r in references if r["volume"] == volume],
    )["spans"]
    preserve_rows(old, current)
    if len(current) != len(old):
        raise ValueError("Provenance revision changes candidate selection")
    before_provenance = read(work / f"provenance_v{volume}.json")
    after_provenance = {str(n): p for n, p in book["provenance"].items()}
    mapping_changes = [
        dict(line=int(n), before=before_provenance.get(n), after=after_provenance.get(n))
        for n in sorted(set(before_provenance) | set(after_provenance), key=int)
        if before_provenance.get(n) != after_provenance.get(n)
    ]
    # Persist evidence before changing the permitted input fingerprints.
    retained = []
    for path in (cp_path, work / f"provenance_v{volume}.json"):
        target = (
            work
            / "recovery"
            / (path.stem + "-before-provenance-rebind-" + digest(path) + path.suffix)
        )
        if not target.exists():
            target.write_bytes(path.read_bytes())
        retained.append(str(target.relative_to(work)))
    proof = dict(
        status="unchanged_selected_source_bindings",
        volume=volume,
        canonical_source_sha256=book["sha256"],
        changed_provenance_inputs=changes,
        unchanged_candidate_regions=len(old),
        mapping_changes=mapping_changes,
        limit="Batch wording is not an alternative canonical reading; unselected mappings are not certified.",
    )
    proof_path = (
        work
        / "recovery"
        / (
            "provenance-v"
            + str(volume)
            + "-rebind-"
            + hashlib.sha256(json.dumps(proof, sort_keys=True).encode()).hexdigest()
            + ".json"
        )
    )
    write_json_atomic(proof_path, proof)
    retained.append(str(proof_path.relative_to(work)))
    progress["reference_baseline_hashes"].update({n: digest(work / n) for n in retained})
    progress.update(
        source_revision=dict(
            kind="provenance_inputs_only",
            volume=volume,
            planned_witnesses=witnesses,
            expected_source_hashes=expected,
            proof=str(proof_path.relative_to(work)),
        ),
        completed_reference_stages=[],
        completed_build_stages=[],
        stage="provenance_refresh_ready",
    )
    write_json_atomic(cp_path, checkpoint)
    return dict(
        status="provenance_refresh_ready",
        volume=volume,
        changed_provenance_inputs=len(changes),
        unchanged_candidate_regions=len(old),
    )


def begin_source_refresh(workspace, source_root, public, volume, binding=None):
    """Rebind identical selected/reviewed passages, preserving their identities.

    Refuse moved, changed or newly selected regions and changed provenance inputs.
    Material outside the research footprint is not certified by this operation.
    """
    from .io import guard
    from .inventory import inventory_text
    from .publication import load_publication, read_witness

    work, public = Path(workspace), Path(public)
    guard(work.resolve(), Path(source_root).resolve())
    cp_path = work / "recovery_checkpoint.json"
    checkpoint = read(cp_path)
    progress = checkpoint.get("in_progress", {})
    if checkpoint.get("checkpoint_status") != "verified_resume_ready":
        revision = progress.get("source_revision", {})
        if progress.get("operation") == "reference_inventory_refresh" and not revision:
            return rebind_provenance_inputs(work, source_root, volume)
        if (
            revision.get("volume") != volume
            or progress.get("operation") != "reference_inventory_refresh"
        ):
            raise ValueError("Conflicting operation during source refresh")
        checked_hashes(work, progress["reference_baseline_hashes"])
        if revision.get("kind") == "reviewed_bindings":
            if binding is not None and binding != revision["binding_record"]:
                raise ValueError("Conflicting source binding during recovery")
            prior = read(work / revision["prior_source_bindings"])
            path = work / "source_binding_reviews.json"
            actual = read(path) if path.exists() else []
            if actual not in (prior, revision["planned_source_bindings"]):
                raise ValueError("Source binding ledger changed during recovery")
            write_json_atomic(path, revision["planned_source_bindings"])
        for witness in revision["planned_witnesses"]:
            read_witness(source_root, work, witness)
        write_json_atomic(work / "witnesses.json", revision["planned_witnesses"])
        return dict(status="source_refresh_resumed", volume=volume)
    last = checkpoint.get("last_verified", {})
    if last.get("artifact_snapshot"):
        checked_hashes(REPO, read(work / last["artifact_snapshot"]))
    witnesses = read(work / "witnesses.json")
    witness = next((w for w in witnesses if w["volume"] == volume), None)
    if witness is None:
        raise ValueError("Unknown source volume")
    book = load_publication(source_root, volume)
    if book["source"] != witness["private_source"]:
        raise ValueError("Unexpected canonical source")
    if book["sha256"] == witness.get("source_sha256", witness["edition_sha256"]):
        read_witness(source_root, work, witness)
        return dict(status="source_already_bound", volume=volume)
    prior_manifest = read(work / "inventory_manifest.json")
    for name, sha in book["source_hashes"].items():
        if name != book["source"] and prior_manifest["source_hashes"].get(name) != sha:
            raise ValueError("Provenance input changed with canonical revision")
    references = read(work / "source_reference_reviews.json")
    old = [s for s in rows(work / "inventory_spans.jsonl") if s["volume"] == volume]
    current = inventory_text(
        book["text"],
        volume,
        witness["edition_sha256"],
        book["provenance"],
        reference_reviews=[r for r in references if r["volume"] == volume],
    )["spans"]
    existing_bindings = load_bindings(work)
    proposed_bindings = existing_bindings
    if binding is None:
        preserve_rows(old, current)
        if len(current) != len(old):
            raise ValueError("Canonical revision changes candidate selection")
    else:
        if (
            binding.get("volume") != volume
            or binding.get("current_source_sha256") != book["sha256"]
            or binding.get("original_source_sha256")
            != witness.get("source_sha256", witness["edition_sha256"])
            or any(b.get("volume") == volume for b in existing_bindings)
        ):
            raise ValueError("Source binding requires its exact original and current witnesses")
        proposed_bindings = [*existing_bindings, binding]
        current = apply_span_bindings(
            current, [b for b in proposed_bindings if b["volume"] == volume]
        )
    lines = book["text"].splitlines()
    ledger = read(work / "review_batches.json")
    reviews = [r for r in ledger if r["volume"] == volume]
    if binding is not None:
        targets = [r for r in reviews if r["id"] == binding["review_id"]]
        if len(targets) != 1:
            raise ValueError("Source binding review is absent")
        rebind_review(targets[0], book["text"], binding)
        expected_ids = {d["span_id"] for d in targets[0]["span_decisions"]}
        if {s["original_id"] for s in binding["span_bindings"]} != expected_ids:
            raise ValueError("Source binding does not cover the reviewed spans")
        old_by_id = {s["id"]: s for s in old}
        if len(binding["prior_source_rows"]) != len(expected_ids) or any(
            old_by_id.get(s["id"]) != s for s in binding["prior_source_rows"]
        ):
            raise ValueError("Frozen source span evidence differs")
    for batch in reviews:
        if binding is not None and batch["id"] == binding["review_id"]:
            continue
        interval = "\n".join(lines[batch["line_start"] - 1 : batch["line_end"]])
        if hashlib.sha256(interval.encode()).hexdigest() != batch["interval_sha256"]:
            raise ValueError("Canonical revision changes a reviewed interval")
    supporting = []
    if (work / "contexts.jsonl").exists():
        supporting = [c for c in rows(work / "contexts.jsonl") if c["volume"] == volume]
        for context in supporting:
            if binding is not None and context["review_id"] == binding["review_id"]:
                continue
            if "\n".join(lines[n - 1] for n in context["lines"]) != context["text_original"]:
                raise ValueError("Canonical revision changes reviewed supporting context")
    recovery = work / "recovery"
    recovery.mkdir(exist_ok=True)

    def retain(path):
        target = recovery / (path.stem + "-before-source-refresh-" + digest(path) + path.suffix)
        if not target.exists():
            target.write_bytes(path.read_bytes())
        return str(target.relative_to(work))

    backups = {
        name: retain(work / name)
        for name in (
            "inventory_spans.jsonl",
            "inventory_manifest.json",
            "source_reference_reviews.json",
            "review_batches.json",
            "witnesses.json",
        )
    }
    if binding is not None:
        prior_binding_path = recovery / (
            "source-bindings-before-" + review_sha(existing_bindings) + ".json"
        )
        if not prior_binding_path.exists():
            write_json_atomic(prior_binding_path, existing_bindings)
        backups["source_binding_reviews.json"] = str(prior_binding_path.relative_to(work))
    if supporting:
        backups["contexts.jsonl"] = retain(work / "contexts.jsonl")
    prior_public = retain(public / "reviewed_assertions.jsonl")
    proof = dict(
        status="unchanged_source_bindings",
        volume=volume,
        private_source=book["source"],
        identity_edition_sha256=witness["edition_sha256"],
        previous_source_sha256=witness.get("source_sha256", witness["edition_sha256"]),
        current_source_sha256=book["sha256"],
        unchanged_candidate_regions=len(old),
        unchanged_reviewed_intervals=len(reviews),
        unchanged_supporting_contexts=len(supporting),
        retained_artifact_hashes={name: digest(work / name) for name in backups.values()},
        limit="Unselected, unreviewed book material is outside this compatibility proof.",
    )
    proof_file = recovery / f"source-v{volume}-revision-{book['sha256']}.json"
    if binding is not None:
        proof.update(
            status="reviewed_source_bindings",
            unchanged_candidate_regions=None,
            current_candidate_regions=len(current),
            current_inventory_sha256=review_sha(current),
            source_binding_id=binding["id"],
            binding_record=binding,
            original_review_ledger=backups["review_batches.json"],
            reviewed_source_span_identities_preserved=len(binding["span_bindings"]),
        )
    write_json_atomic(proof_file, proof)
    planned = copy.deepcopy(witnesses)
    target = next(w for w in planned if w["volume"] == volume)
    target.update(
        source_sha256=book["sha256"],
        source_revision=dict(
            evidence_file=str(proof_file.relative_to(work)), evidence_sha256=digest(proof_file)
        ),
    )
    expected_hashes = dict(prior_manifest["source_hashes"])
    expected_hashes[book["source"]] = book["sha256"]
    evidence = [*backups.values(), prior_public, str(proof_file.relative_to(work))]
    progress = dict(
        operation="reference_inventory_refresh",
        stage="source_refresh_ready",
        reference_records=[],
        reference_ids=[],
        review_ids=[],
        prior_review_ledger_backup=backups["review_batches.json"],
        prior_public_snapshot=prior_public,
        prior_inventory_spans=backups["inventory_spans.jsonl"],
        prior_inventory_manifest=backups["inventory_manifest.json"],
        prior_reference_reviews=backups["source_reference_reviews.json"],
        reference_baseline_hashes={name: digest(work / name) for name in evidence},
        prior_verified_snapshot=last.get("artifact_snapshot"),
        review_ledger_sha256=digest(work / "review_batches.json"),
        new_quantities=0,
        new_source_groups=0,
        new_inspected_regions=0,
        new_inspected_source_lines=0,
        source_intervals=[],
        source_ranges=[],
        source_findings=["Canonical layout revision preserves all selected and reviewed bindings."],
        completed_build_stages=[],
        source_revision=dict(
            volume=volume,
            planned_witnesses=planned,
            expected_source_hashes=expected_hashes,
            proof=str(proof_file.relative_to(work)),
        ),
    )
    if binding is not None:
        progress["source_revision"].update(
            kind="reviewed_bindings",
            binding_record=binding,
            prior_source_bindings=backups["source_binding_reviews.json"],
            planned_source_bindings=proposed_bindings,
            current_inventory_sha256=review_sha(current),
        )
        progress["source_findings"] = [
            "Explicit source-version relocation preserves original reviews, quantities and identities; note references and the English clock-quality paraphrase are separately bound."
        ]
    checkpoint.update(
        checkpoint_status="in_progress_after_verified_checkpoint", in_progress=progress
    )
    write_json_atomic(cp_path, checkpoint)
    if binding is not None:
        write_json_atomic(work / "source_binding_reviews.json", proposed_bindings)
    write_json_atomic(work / "witnesses.json", planned)
    return dict(
        status="source_refresh_ready",
        volume=volume,
        **(
            dict(
                reviewed_source_span_identities_preserved=len(binding["span_bindings"]),
                prior_candidate_regions=len(old),
                current_candidate_regions=len(current),
                reviewed_intervals_rebound=1,
            )
            if binding is not None
            else dict(
                unchanged_candidate_regions=len(old), unchanged_reviewed_intervals=len(reviews)
            )
        ),
    )


def begin_reference_refresh(workspace, source_root, public, references):
    """Commit reviewed reference links with recoverable inventory/input baselines."""
    from .io import guard
    from .inventory import inventory_text

    work, public = Path(workspace), Path(public)
    guard(work.resolve(), Path(source_root).resolve())
    if (
        not isinstance(references, list)
        or not references
        or any(not isinstance(r, dict) or not r.get("id") for r in references)
        or len({r["id"] for r in references}) != len(references)
    ):
        raise ValueError("Supply a nonempty list of distinct reference reviews")
    checkpoint_path = work / "recovery_checkpoint.json"
    checkpoint = read(checkpoint_path)
    progress = checkpoint.get("in_progress", {})
    if checkpoint.get("checkpoint_status") != "verified_resume_ready":
        if (
            progress.get("operation") != "reference_inventory_refresh"
            or progress.get("reference_records") != references
        ):
            raise ValueError("Conflicting operation during reference refresh")
        checked_hashes(work, progress["reference_baseline_hashes"])
        before = read(work / progress["prior_reference_reviews"])
        expected = before + [r for r in references if r["id"] not in {v["id"] for v in before}]
        if read(work / "source_reference_reviews.json") not in (before, expected):
            raise ValueError("Conflicting reference ledger during recovery")
        write_json_atomic(work / "source_reference_reviews.json", expected)
        return dict(status="reference_refresh_resumed", reference_ids=[r["id"] for r in references])
    last = checkpoint.get("last_verified", {})
    if last.get("artifact_snapshot"):
        checked_hashes(REPO, read(work / last["artifact_snapshot"]))
    planned = record_update_plan(
        work, dict(record_updates={"source_reference_reviews.json": references})
    )
    before, after = planned["source_reference_reviews.json"]
    if before == after:
        return dict(status="references_already_present")
    texts = source_texts(work, source_root)
    if any(r.get("volume") not in texts for r in references):
        raise ValueError("Unknown reference volume")
    for volume, text in texts.items():
        inventory_text(
            text,
            volume,
            edition_hashes(work)[volume],
            reference_reviews=[r for r in after if r.get("volume") == volume],
        )
    recovery = work / "recovery"
    recovery.mkdir(exist_ok=True)

    def retain(path):
        target = recovery / (path.stem + "-before-reference-refresh-" + digest(path) + path.suffix)
        if not target.exists():
            target.write_bytes(path.read_bytes())
        return str(target.relative_to(work))

    ledger = retain(work / "review_batches.json")
    prior_public = retain(public / "reviewed_assertions.jsonl")
    prior_spans = retain(work / "inventory_spans.jsonl")
    prior_manifest = retain(work / "inventory_manifest.json")
    prior_references = retain(work / "source_reference_reviews.json")
    backups = [ledger, prior_public, prior_spans, prior_manifest, prior_references]
    progress = dict(
        operation="reference_inventory_refresh",
        stage="reference_refresh_ready",
        reference_records=references,
        reference_ids=[r["id"] for r in references],
        review_ids=[],
        prior_review_ledger_backup=ledger,
        prior_public_snapshot=prior_public,
        prior_inventory_spans=prior_spans,
        prior_inventory_manifest=prior_manifest,
        prior_reference_reviews=prior_references,
        reference_baseline_hashes={n: digest(work / n) for n in backups},
        prior_verified_snapshot=last.get("artifact_snapshot"),
        review_ledger_sha256=digest(work / "review_batches.json"),
        new_quantities=0,
        new_source_groups=0,
        new_inspected_regions=0,
        new_inspected_source_lines=0,
        source_intervals=[],
        source_ranges=[],
        source_findings=[
            "Admit explicitly referenced companion material without altering prior readings."
        ],
        completed_build_stages=[],
    )
    checkpoint.update(
        checkpoint_status="in_progress_after_verified_checkpoint", in_progress=progress
    )
    write_json_atomic(checkpoint_path, checkpoint)
    apply_record_updates(work, planned)
    return dict(status="reference_refresh_ready", reference_ids=progress["reference_ids"])


def verify_reference_refresh(workspace):
    work = Path(workspace)
    progress = read(work / "recovery_checkpoint.json")["in_progress"]
    checked_hashes(work, progress["reference_baseline_hashes"])
    prior_spans, current_spans = (
        rows(work / progress["prior_inventory_spans"]),
        rows(work / "inventory_spans.jsonl"),
    )
    revision = progress.get("source_revision")
    migrated = bool(revision and revision.get("kind") == "reviewed_bindings")
    unchanged = len(prior_spans)
    if migrated:
        volume = revision["volume"]
        unaffected = [s for s in prior_spans if s["volume"] != volume]
        preserve_rows(unaffected, current_spans)
        unchanged = len(unaffected)
        changed = [s for s in current_spans if s["volume"] == volume]
        if review_sha(changed) != revision["current_inventory_sha256"]:
            raise ValueError("Reviewed source inventory changed during migration")
        if read(work / "source_binding_reviews.json") != revision["planned_source_bindings"]:
            raise ValueError("Source binding ledger changed during migration")
    else:
        preserve_rows(prior_spans, current_spans)
    prior_ids = {s["id"] for s in prior_spans}
    added = [s for s in current_spans if s["id"] not in prior_ids]
    if not migrated and any(
        (s.get("source_reference_review_id") or s.get("research_support_review_id"))
        not in progress["reference_ids"]
        for s in added
    ):
        raise ValueError("Inventory additions lack the reviewed source reference")
    previous, current = (
        read(work / progress["prior_inventory_manifest"]),
        read(work / "inventory_manifest.json"),
    )
    for key in ("volumes", "source_hashes", "benchmark_artifact_sha256"):
        if revision and key == "source_hashes":
            if current[key] != revision["expected_source_hashes"]:
                raise ValueError("Source refresh inputs differ from review")
            continue
        if previous.get(key) != current.get(key):
            raise ValueError("Protected inventory inputs changed: " + key)
    if revision and read(work / "witnesses.json") != revision["planned_witnesses"]:
        raise ValueError("Revised witness differs from reviewed source binding")
    before = read(work / progress["prior_reference_reviews"])
    expected = before + [
        r for r in progress["reference_records"] if r["id"] not in {v["id"] for v in before}
    ]
    if read(work / "source_reference_reviews.json") != expected:
        raise ValueError("Reference ledger changed during refresh")
    if read(work / "review_batches.json") != read(work / progress["prior_review_ledger_backup"]):
        raise ValueError("Review ledger changed during reference refresh")
    return dict(
        prior_candidate_regions_unchanged=unchanged,
        candidate_regions=len(current_spans),
        added_candidate_region_ids=[s["id"] for s in added],
        reference_ids=progress["reference_ids"],
        **(
            dict(
                reviewed_source_span_identities_preserved=len(
                    revision["binding_record"]["span_bindings"]
                ),
                source_binding_id=revision["binding_record"]["id"],
            )
            if migrated
            else {}
        ),
    )
