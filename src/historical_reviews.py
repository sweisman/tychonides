"""Named-edition orchestration using the shared review compiler and exporter."""

import hashlib
import json
from pathlib import Path
import re
import shutil

from .assembly import assemble
from .catalog import compile_catalogue, identity
from .catalog_release import write_catalogue
from .core import digest
from .date_claims import project_date_claims, validate_date_links
from .public_assertions import public_assertion
from .public_context_projection import project_contexts, validate_projection
from .public_relationships import validate_links
from .recovery import write_json_atomic
from .release_validation import validate_release
from .review_preparation import materialize_review
from .source_registry import historical_sources


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def project_historical_events(events, assertions):
    """Summarize correction groups without treating a guessed label as a body."""
    subjects = {}
    for row in assertions:
        subjects.setdefault(row.get("event_id"), set()).add(row.get("subject"))
    result = [dict(event) for event in events]
    for event in result:
        if event.get("kind") == "source_correction_group":
            values = subjects.get(event["id"], set())
            event["subject"] = next(iter(values)) if len(values) == 1 else None
    return result


def _validate_word_occurrence_correction(review, row, text):
    """Relocate an unchanged native count word to its explicit unit on the same line."""
    before, after = review["before"], review["after"]
    units = {
        "source_year_count": "years?",
        "source_month_count": "months?",
        "source_day_count": "days?",
        "source_week_count": "weeks?",
        "source_cycle_count": "cycles?",
    }
    unit = units.get(row.get("source_parameter_kind"))
    literal = row.get("source_expression")
    if (
        set(after) != {"char_start", "char_end"}
        or row.get("quantity") != "source_scalar"
        or row.get("column") is not None
        or row.get("source_fragments")
        or not unit
        or literal not in row.get("source_word_numbers", {})
        or hashlib.sha256(text.encode()).hexdigest() != review.get("source_sha256")
    ):
        raise ValueError("Occurrence correction requires an unchanged native count word and source")
    line = text.splitlines()[row["line"] - 1]
    for position in (before, after):
        start, end = position["char_start"], position["char_end"]
        if (
            type(start) is not int
            or type(end) is not int
            or not 0 <= start < end <= len(line)
            or line[start:end] != literal
            or (start > 0 and line[start - 1].isalnum())
            or (end < len(line) and line[end].isalnum())
        ):
            raise ValueError("Occurrence correction differs from its complete literal word")
    start, end = after["char_start"], after["char_end"]
    following_unit = re.match(r"\s+(?:" + unit + r")\b", line[end:], re.I)
    if not following_unit or not any(
        item["line"] == row["line"]
        and line.index(item["source_expression"]) <= start
        and end + following_unit.end()
        <= line.index(item["source_expression"]) + len(item["source_expression"])
        for item in review["evidence"]
    ):
        raise ValueError("Occurrence evidence must contain the corrected word and its native unit")


def apply_classification_reviews(work, compiled, texts):
    """Apply source-bound classifications, qualifiers and native-word occurrence repairs."""
    path = work / "classification_reviews.json"
    if not path.exists():
        return {}
    rows = {row["id"]: row for row in compiled["assertions"]}
    decisions = {}
    review_ids = set()
    for review in read(path):
        aid = review.get("assertion_id")
        before, after = review.get("before", {}), review.get("after", {})
        row = rows.get(aid)
        if (
            row is None
            or aid in decisions
            or not review.get("id")
            or review["id"] in review_ids
            or not review.get("reason")
            or not after
            or set(before) != set(after)
            or set(after) - {"subject", "reference", "role", "flags", "char_start", "char_end"}
            or before == after
        ):
            raise ValueError("Classification review has an invalid target or field set")
        fingerprint = hashlib.sha256(
            json.dumps(row, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        if fingerprint != review.get("original_sha256") or any(
            row.get(key) != value for key, value in before.items()
        ):
            raise ValueError("Classification review differs from the frozen interpretation")
        calculation_input = (
            before.get("role") == "calculation_intermediate"
            and after.get("role") == "historical_input"
            and row.get("event_id") is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        if (
            "role" in after
            and after["role"] not in ("recorded_reading", "repeated_reading")
            and not calculation_input
        ):
            raise ValueError("Classification review cannot change the scientific record class")
        if "reference" in after and not isinstance(after["reference"], str):
            raise ValueError("Classification review requires an explicit reference name")
        if "subject" in after:
            from .normalization import normalize_quantity
            from .public_policy import SUBJECTS

            original_normalization = normalize_quantity(row)
            if (
                set(after) != {"subject"}
                or not isinstance(after["subject"], str)
                or after["subject"] not in SUBJECTS
                or row.get("normalized") != original_normalization
                or normalize_quantity(dict(row, subject=after["subject"])) != original_normalization
            ):
                raise ValueError(
                    "Subject classification must preserve the exact numerical interpretation"
                )
        if "flags" in after:
            old_flags, new_flags = before["flags"], after["flags"]
            qualifiers = {
                "source_approximate",
                "source_lower_bound",
                "source_upper_bound",
                "source_quality_note_present",
            }
            if (
                set(after) != {"flags"}
                or not isinstance(old_flags, list)
                or not isinstance(new_flags, list)
                or any(not isinstance(f, str) for f in new_flags)
                or len(set(new_flags)) != len(new_flags)
                or new_flags[: len(old_flags)] != old_flags
                or len(new_flags) <= len(old_flags)
                or not set(new_flags[len(old_flags) :]) <= qualifiers
                or {"source_lower_bound", "source_upper_bound"} <= set(new_flags)
            ):
                raise ValueError(
                    "Classification qualifier review must preserve flags and add only source qualifications"
                )
        lines = texts[row["source_id"]].splitlines()
        evidence = review.get("evidence", [])
        if not evidence or any(
            not isinstance(item.get("line"), int)
            or not 1 <= item["line"] <= len(lines)
            or not item.get("source_expression")
            or lines[item["line"] - 1].count(item["source_expression"]) != 1
            for item in evidence
        ):
            raise ValueError("Classification review lacks unique literal source evidence")
        if ("flags" in after or "subject" in after) and not any(
            item["line"] == row.get("line")
            and row.get("source_expression")
            and row["source_expression"] in item["source_expression"]
            for item in evidence
        ):
            raise ValueError("Classification evidence must contain the bound source reading")
        if {"char_start", "char_end"} & set(after):
            _validate_word_occurrence_correction(review, row, texts[row["source_id"]])
        original = dict(row)
        row.update(after)
        decisions[aid] = {"before": original, "after": dict(row)}
        review_ids.add(review["id"])
    return decisions


def apply_page_binding_reviews(work, compiled, texts, reviews):
    """Correct reviewed folio/page locators while preserving the original ledger."""
    path = work / "page_binding_reviews.json"
    if not path.exists():
        return {}, {}
    by_review = {review["id"]: review for review in reviews}
    decisions = {}
    overrides = {}
    seen_ids = set()
    for correction in read(path):
        source_id = correction.get("source_id")
        review = by_review.get(correction.get("review_id"))
        start, end = correction.get("line_start"), correction.get("line_end")
        before, after = correction.get("before_printed_page"), correction.get("after_printed_page")
        if (
            not isinstance(correction.get("id"), str)
            or not correction["id"]
            or correction["id"] in seen_ids
            or review is None
            or source_id != review["source_id"]
            or correction.get("edition_sha256") != review["edition_sha256"]
            or not isinstance(start, int)
            or not isinstance(end, int)
            or not review["line_start"] <= start <= end <= review["line_end"]
            or not isinstance(before, int)
            or not isinstance(after, int)
            or before < 1
            or after < 1
            or before == after
            or not correction.get("reason")
        ):
            raise ValueError("Page binding review has an invalid target or field set")
        segments = review["basis"].get(
            "page_segments",
            [
                dict(
                    line_start=review["line_start"],
                    line_end=review["line_end"],
                    printed_page=review["basis"]["printed_page"],
                )
            ],
        )
        if any(
            not any(
                s["line_start"] <= n <= s["line_end"] and s["printed_page"] == before
                for s in segments
            )
            for n in range(start, end + 1)
        ):
            raise ValueError("Page binding review differs from the original locator")
        lines = texts[source_id].splitlines()
        evidence = correction.get("evidence", [])
        if not evidence or any(
            not isinstance(item.get("line"), int)
            or not start <= item["line"] <= end
            or not item.get("source_expression")
            or lines[item["line"] - 1].count(item["source_expression"]) != 1
            for item in evidence
        ):
            raise ValueError("Page binding review lacks unique source evidence")
        selected = [
            row
            for row in compiled["assertions"]
            if row["review_id"] == review["id"] and start <= row["line"] <= end
        ]
        if not selected or any(row["printed_page"] != before for row in selected):
            raise ValueError("Page binding review has no matching frozen quantities")
        for row in selected:
            if row["id"] in decisions or row.get("source_fragment_pages"):
                raise ValueError("Page binding review overlaps another locator decision")
            original = dict(row)
            row["printed_page"] = after
            decisions[row["id"]] = {"before": original, "after": dict(row)}
        for n in range(start, end + 1):
            key = (source_id, n)
            if key in overrides and overrides[key] != after:
                raise ValueError("Page binding reviews disagree on a source line")
            overrides[key] = after
        seen_ids.add(correction["id"])
    return decisions, overrides


def inputs(work):
    inventory = read(work / "inventory.json")
    registry = historical_sources()
    texts = {}
    for source in inventory["sources"]:
        sid = source["source_id"]
        if sid not in registry:
            raise ValueError("Unregistered historical book: " + sid)
        path = Path(source["source_path"])
        if digest(path) != source["source_sha256"]:
            raise ValueError("Historical source changed: " + sid)
        texts[sid] = path.read_text(encoding="utf-8")
    return inventory, texts, registry


def apply_locator_projection_reviews(work, assertions):
    """Authorize only audited locator changes to previously frozen assertions."""
    from .source_locator import validate_page_locator

    path = work / "locator_projection_reviews.json"
    if not path.exists():
        return {}
    review = read(path)
    if (
        not isinstance(review, dict)
        or set(review) != {"id", "reason", "corrections"}
        or not review["id"]
        or not review["reason"]
        or not isinstance(review["corrections"], list)
        or not review["corrections"]
    ):
        raise ValueError("Locator projection review lacks its scope and reason")
    rows = {row["id"]: row for row in assertions}
    decisions = {}
    for item in review["corrections"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"assertion_id", "original_sha256", "before", "after"}
            or item["assertion_id"] not in rows
            or item["assertion_id"] in decisions
            or item["before"] == item["after"]
        ):
            raise ValueError("Locator projection review has an invalid target")
        row = rows[item["assertion_id"]]
        for locator in (item["before"], item["after"]):
            if locator is not None:
                validate_page_locator(locator)
        original = dict(row)
        if item["before"] is None:
            original.pop("source_page_locator", None)
        else:
            original["source_page_locator"] = item["before"]
        fingerprint = hashlib.sha256(
            json.dumps(original, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        if (
            row.get("source_page_locator") != item["after"]
            or fingerprint != item["original_sha256"]
        ):
            raise ValueError("Locator projection review differs from the source-bound record")
        decisions[row["id"]] = dict(before=original, after=dict(row))
    return decisions


def validate_source_occurrences(assertions, assembled):
    """Reject repeated unlinked occurrences while allowing explicit variants in any order."""
    occurrences = set()
    bound_items = {item["upstream_id"]: item for item in assembled["items"]}
    for row in assertions:
        fragments = tuple(
            (fragment["line"], fragment["source_expression"])
            for fragment in row.get("source_fragments", [])
        )
        key = (row["source_id"], bound_items[row["id"]]["interval_anchor_id"], fragments)
        if not row.get("variant_of_id"):
            if key in occurrences:
                raise ValueError("Repeated source occurrence; reuse the existing quantity")
            occurrences.add(key)


def compile_reviews(work, reviews):
    inventory, texts, registry = inputs(work)
    spans = {}
    review_spans = []
    for review in reviews:
        sid = review["source_id"]
        if sid not in texts:
            raise ValueError("Review outside selected editions")
        lines = texts[sid].splitlines()
        start, end = review["line_start"], review["line_end"]
        if not 1 <= start <= end <= len(lines):
            raise ValueError("Review interval outside source")
        selected = []
        for n in range(start, end + 1):
            span_id = identity("span", sid, review["edition_sha256"], n, "line")
            spans[span_id] = dict(
                id=span_id,
                source_id=sid,
                edition_sha256=review["edition_sha256"],
                line_start=n,
                line_end=n,
            )
            selected.append(spans[span_id])
        review_spans.append(selected)
    spans = list(spans.values())
    materialized = [
        materialize_review(review, texts[review["source_id"]], selected)
        for review, selected in zip(reviews, review_spans, strict=True)
    ]
    compiled = compile_catalogue(materialized, texts, spans)
    compiled["classification_reviews"] = apply_classification_reviews(work, compiled, texts)
    assembled = assemble(texts, compiled["assertions"], [], [], [])
    if any(item["anchor_status"] != "unique_source_interval" for item in assembled["items"]):
        raise ValueError("Reviewed quantity lacks a unique source occurrence")
    validate_source_occurrences(compiled["assertions"], assembled)
    (
        compiled["page_binding_reviews"],
        compiled["page_binding_overrides"],
    ) = apply_page_binding_reviews(work, compiled, texts, reviews)
    project_date_claims(
        compiled["contexts"],
        compiled["assertions"],
        compiled["events"],
        include_structured_contexts=True,
    )
    compiled["locator_projection_reviews"] = apply_locator_projection_reviews(
        work, compiled["assertions"]
    )
    from .coordinate_origin import apply_coordinate_origin_reviews

    compiled["coordinate_origin_reviews"] = apply_coordinate_origin_reviews(work, compiled, texts)
    return inventory, compiled, registry


def _append_and_compile(work, additions):
    work = Path(work)
    additions = additions if isinstance(additions, list) else [additions]
    if not additions:
        raise ValueError("Empty review append")
    path = work / "reviews.json"
    prior = read(path) if path.exists() else []
    indexed = {r["id"]: r for r in prior}
    for review in additions:
        if review["id"] in indexed and indexed[review["id"]] != review:
            raise ValueError("Conflicting immutable review identity")
        indexed[review["id"]] = review
    combined = list(indexed.values())
    compiled_inputs = compile_reviews(work, combined)
    if combined != prior:
        if path.exists():
            backup = work / "recovery" / ("reviews-" + digest(path) + ".json")
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                shutil.copyfile(path, backup)
        write_json_atomic(path, combined)
    report = dict(review_batches=len(combined), appended=len(combined) - len(prior))
    return report, combined, compiled_inputs


def append(work, additions):
    return _append_and_compile(work, additions)[0]


def run(work, *, additions=None):
    work = Path(work)
    if additions is None:
        reviews = read(work / "reviews.json")
        compiled_inputs = compile_reviews(work, reviews)
    else:
        # Reuse only this invocation's fully validated result. The ledger is
        # already durable, so an interrupted export resumes with ordinary run.
        _, reviews, compiled_inputs = _append_and_compile(work, additions)
    inventory, compiled, registry = compiled_inputs
    previous = work / "compiled_assertions.json"
    if previous.exists():
        from .review_state import preserve_rows

        prior = read(previous)
        decisions = compiled["classification_reviews"]
        pages = compiled["page_binding_reviews"]
        locators = compiled["locator_projection_reviews"]
        origins = compiled.get("coordinate_origin_reviews", {})
        expected = []
        for row in prior:
            updated = (
                decisions[row["id"]]["after"]
                if row["id"] in decisions and row == decisions[row["id"]]["before"]
                else row
            )
            if updated["id"] in pages and updated == pages[updated["id"]]["before"]:
                updated = pages[updated["id"]]["after"]
            if updated["id"] in locators and updated == locators[updated["id"]]["before"]:
                updated = locators[updated["id"]]["after"]
            if updated["id"] in origins and updated == origins[updated["id"]]["before"]:
                updated = origins[updated["id"]]["after"]
            expected.append(updated)
        preserve_rows(expected, compiled["assertions"])
        if expected != prior:
            archive = work / "recovery" / ("assertions-" + digest(previous) + ".json")
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archive.exists():
                shutil.copyfile(previous, archive)
    published = [public_assertion(r, source_registry=registry) for r in compiled["assertions"]]
    dates = project_date_claims(
        compiled["contexts"],
        compiled["assertions"],
        compiled["events"],
        include_structured_contexts=True,
    )
    events = project_historical_events(compiled["events"], published)
    for rows, mapping in (
        (published, dates["assertion_date_ids"]),
        (events, dates["event_date_ids"]),
    ):
        for row in rows:
            if mapping[row["id"]]:
                row["source_date_claim_ids"] = mapping[row["id"]]
    validate_date_links(published, events, dates["date_claims"])
    validate_links(published, events)
    provenance = review_provenance(reviews, compiled["page_binding_overrides"])
    contexts, loci = project_contexts(
        compiled["contexts"],
        provenance,
        quantities=compiled["assertions"],
        events=compiled["events"],
    )
    validate_projection(contexts, loci, compiled["assertions"], compiled["events"])
    active = sorted({r["source_id"] for r in reviews})
    manifest = write_catalogue(
        work / "catalogue",
        compiled["assertions"],
        published,
        contexts,
        events,
        dates["date_claims"],
        compiled["derivations"],
        [],
        [registry[sid] for sid in active],
        [],
        {},
        loci=loci,
    )
    validate_release(work / "catalogue")
    write_json_atomic(previous, compiled["assertions"])
    covered = {}
    for review in reviews:
        covered.setdefault(review["source_id"], set()).update(
            range(review["line_start"], review["line_end"] + 1)
        )
    completed = sum(
        set(range(s["line_start"], s["line_end"] + 1)) <= covered.get(book["source_id"], set())
        for book in inventory["sources"]
        for s in book["sections"]
    )
    proof = dict(
        status="verified_partial_historical_import",
        review_sha256=digest(work / "reviews.json"),
        quantities=manifest["quantities"],
        groups=manifest["groups"],
        reviewed_sections=completed,
        total_sections=inventory["section_count"],
        reviewed_lines=sum(map(len, covered.values())),
        catalogue_manifest=manifest,
    )
    if compiled["classification_reviews"]:
        proof["classification_review_sha256"] = digest(work / "classification_reviews.json")
    if compiled["page_binding_reviews"]:
        proof["page_binding_review_sha256"] = digest(work / "page_binding_reviews.json")
    if compiled["locator_projection_reviews"]:
        proof["locator_projection_review_sha256"] = digest(work / "locator_projection_reviews.json")
    if compiled.get("coordinate_origin_reviews"):
        proof["coordinate_origin_review_sha256"] = digest(work / "coordinate_origin_reviews.json")
    archive = (
        work
        / "recovery"
        / (
            "verification-"
            + proof["review_sha256"]
            + "-"
            + manifest["output_hashes"]["tychonides.sqlite"]
            + ".json"
        )
    )
    if not archive.exists():
        write_json_atomic(archive, proof)
    write_json_atomic(work / "verification.json", proof)
    return proof


def review_provenance(reviews, overrides):
    """Retain reviewed leaf claims when a canonical paragraph crosses pages."""
    provenance = {}
    for review in reviews:
        sid = review["source_id"]
        mapping = provenance.setdefault(sid, {})
        scoped = provenance.setdefault((sid, review["id"]), {})
        segments = review["basis"].get(
            "page_segments",
            [
                dict(
                    line_start=review["line_start"],
                    line_end=review["line_end"],
                    printed_page=review["basis"].get("printed_page"),
                )
            ],
        )
        for segment in segments:
            for n in range(segment["line_start"], segment["line_end"] + 1):
                page = segment["printed_page"]
                scoped[n] = dict(page=page)
                prior = mapping.get(n, {})
                pages = set(prior.get("pages", []))
                pages.update(p for p in (prior.get("page"), page) if p is not None)
                mapping[n] = (
                    dict(page=None, pages=sorted(pages)) if len(pages) > 1 else dict(page=page)
                )
    attachment_citations = {}
    for review in reviews:
        sid = review["source_id"]
        for citation in review["basis"].get("annotation_attachment_citations", []):
            n, page = citation["line"], citation["printed_page"]
            for rid in (review["id"], citation["review_id"]):
                key = (sid, rid, n)
                scoped = provenance.setdefault((sid, rid), {})
                previous = attachment_citations.get(key, scoped.get(n, {}).get("page"))
                if previous is not None and previous != page:
                    raise ValueError(
                        "Edition-note attachment citations conflict within a review scope"
                    )
                attachment_citations[key] = page
                scoped[n] = dict(page=page)
    for (sid, n), page in overrides.items():
        if len(provenance[sid][n].get("pages", [])) > 1:
            raise ValueError("Cross-leaf page correction requires a review-specific disposition")
        provenance[sid][n] = dict(page=page)
        for key, mapping in provenance.items():
            if isinstance(key, tuple) and key[0] == sid and n in mapping:
                mapping[n] = dict(page=page)
    return provenance


def inspect(work, sid, start, end):
    from .inventory import blocks
    from .narrative_staging import stage_span
    from .table_staging import stage_table

    _, texts, _ = inputs(Path(work))
    lines = texts[sid].splitlines()
    if not 1 <= start <= end <= len(lines):
        raise ValueError("Inspection outside source")
    sha = hashlib.sha256(texts[sid].encode()).hexdigest()
    cells, expressions, fragments = [], [], []
    for first, last, kind, body in blocks(lines[start - 1 : end]):
        first, last = first + start - 1, last + start - 1
        span = dict(
            id=identity("inspection-span", sid, sha, first, kind),
            volume=sid,
            edition_sha256=sha,
            line_start=first,
            line_end=last,
            block_kind=kind,
            text_original=body,
        )
        if kind == "table":
            cells.extend(stage_table(span)["cells"])
        staged = stage_span(span)
        expressions.extend(staged["expressions"])
        fragments.extend(staged["material"]["numeric_fragments"])
    return dict(
        source_id=sid,
        edition_sha256=sha,
        lines=[dict(line=n, text=lines[n - 1]) for n in range(start, end + 1)],
        staged_cells=cells,
        staged_expressions=expressions,
        numeric_fragments=fragments,
        status="requires_source_review_not_accepted_observations",
    )


def dispatch(args, parser):
    from .review_workflow import REPO

    work = Path(args.workspace).resolve()
    if not work.is_relative_to(REPO / "work"):
        parser.error("Historical reviews require protected work storage")
    if args.volume is not None:
        parser.error("Named historical sources use --source-id, not --volume")
    if args.operation == "inspect":
        if args.source_id is None or args.start is None or args.end is None:
            parser.error("inspect requires --source-id, --start and --end")
        result = inspect(work, args.source_id, args.start, args.end)
    elif args.operation == "append":
        if not args.review:
            parser.error("append requires --review")
        result = append(work, read(args.review))
    elif args.operation in ("run", "build", "check"):
        if args.review and args.operation != "run":
            parser.error("Append during export requires run --review")
        result = run(work, additions=read(args.review) if args.review else None)
        if args.repeat and run(work) != result:
            raise ValueError("Historical catalogue repeat differs")
        if args.tests:
            import subprocess
            import sys

            subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=REPO, check=True
            )
    elif args.operation == "status":
        result = (
            read(work / "verification.json")
            if (work / "verification.json").exists()
            else dict(
                quantities=0,
                groups=0,
                reviewed_sections=0,
                total_sections=read(work / "inventory.json")["section_count"],
                status="inventory_only",
            )
        )
        if (work / "reviews.json").exists():
            result = dict(
                result, pending_build=result.get("review_sha256") != digest(work / "reviews.json")
            )
    else:
        parser.error("Operation unavailable for named editions; use inspect, append, run or status")
    if args.output:
        output = Path(args.output).resolve()
        if not output.is_relative_to(work):
            parser.error("Inspection output must remain inside the working directory")
        write_json_atomic(output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
