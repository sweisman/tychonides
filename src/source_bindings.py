"""Explicit, fingerprinted relocation of previously reviewed source passages.

Original review records remain immutable. These pure adapters validate a reviewed
revision and return current source locations with separate frozen ID anchors.
"""

import copy
import hashlib
import json
import re
from pathlib import Path


def load_bindings(workspace):
    path = Path(workspace) / "source_binding_reviews.json"
    bindings = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    if not isinstance(bindings, list):
        raise ValueError("Source binding ledger must be a list")
    index_bindings(bindings)
    return bindings


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def review_sha(review):
    return text_sha(json.dumps(review, sort_keys=True, ensure_ascii=False, separators=(",", ":")))


def index_bindings(bindings):
    indexed = {}
    versions = {}
    for binding in bindings:
        rid, volume = binding.get("review_id"), binding.get("volume")
        if not isinstance(rid, str) or not rid or rid in indexed or type(volume) is not int:
            raise ValueError("Duplicate or invalid source binding review")
        for key in ("current_source_sha256", "original_review_sha256", "identity_edition_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", binding.get(key, "")):
                raise ValueError("Source binding requires exact fingerprints")
        version = binding["current_source_sha256"]
        if volume in versions and versions[volume] != version:
            raise ValueError("Conflicting current source versions")
        indexed[rid] = binding
        versions[volume] = version
    return indexed


def apply_span_bindings(spans, bindings):
    indexed = index_bindings(bindings)
    maps, versions, reserved = {}, {}, set()
    for binding in indexed.values():
        volume = binding["volume"]
        versions[volume] = binding["current_source_sha256"]
        for item in binding["span_bindings"]:
            key = (volume, item["current_generated_id"])
            if key in maps or item["original_id"] in reserved:
                raise ValueError("Conflicting source span bindings")
            maps[key] = item
            reserved.add(item["original_id"])
    seen, result = set(), []
    for original in spans:
        volume = original["volume"]
        if volume not in versions:
            result.append(original)
            continue
        row = copy.deepcopy(original)
        generated = row.get("source_generated_span_id", row["id"])
        key = (volume, generated)
        binding = maps.get(key)
        if binding:
            if (row["line_start"], row["line_end"]) != (
                binding["current_line_start"],
                binding["current_line_end"],
            ) or text_sha(row["text_original"]) != binding["current_text_sha256"]:
                raise ValueError("Current source span differs from reviewed binding")
            row["id"] = binding["original_id"]
            seen.add(key)
        elif generated in reserved:
            token = text_sha(versions[volume] + "|" + generated)[:20]
            row["id"] = f"span-v{volume}-{token}"
        row["source_generated_span_id"] = generated
        row["source_version_sha256"] = versions[volume]
        result.append(row)
    if seen != set(maps) or len({r["id"] for r in result}) != len(result):
        raise ValueError("Missing source span binding or duplicate resulting identity")
    return result


def rebind_review(original, text, binding):
    if (
        review_sha(original) != binding["original_review_sha256"]
        or original["id"] != binding["review_id"]
        or original["volume"] != binding["volume"]
        or original["edition_sha256"] != binding["identity_edition_sha256"]
        or text_sha(text) != binding["current_source_sha256"]
    ):
        raise ValueError("Source binding fingerprint or review identity changed")
    before, after = binding["original_interval"], binding["current_interval"]
    offset = binding["line_offset"]
    if (
        type(offset) is not int
        or (before["line_start"], before["line_end"])
        != (original["line_start"], original["line_end"])
        or before["sha256"] != original["interval_sha256"]
        or text_sha(before["text"]) != before["sha256"]
        or (after["line_start"], after["line_end"])
        != (before["line_start"] + offset, before["line_end"] + offset)
    ):
        raise ValueError("Source binding does not preserve its original reviewed interval")
    lines = text.splitlines()
    current = lines[after["line_start"] - 1 : after["line_end"]]
    old = before["text"].splitlines()
    if (
        len(current) != len(old)
        or len(old) != before["line_end"] - before["line_start"] + 1
        or text_sha("\n".join(current)) != after["sha256"]
    ):
        raise ValueError("Current reviewed interval changed")
    changes = {}
    for change in binding["line_changes"]:
        line = change["original_line"]
        if line in changes:
            raise ValueError("Duplicate source line change")
        changes[line] = change
    used = set()
    for line, (a, b) in enumerate(zip(old, current, strict=True), before["line_start"]):
        if a == b:
            continue
        change = changes.get(line)
        if (
            change is None
            or change["current_line"] != line + offset
            or change["original_text"] != a
            or change["current_text"] != b
        ):
            raise ValueError("Unreviewed source text change")
        kind = change["kind"]
        note = kind == "note_reference_renumbering" and all(
            re.fullmatch(r"\[\^ed\d+\]", value) for value in (a, b)
        )
        wording = (
            kind == "translation_wording"
            and "[" in a
            and "[" in b
            and a.partition("[")[2] == b.partition("[")[2]
            and re.findall(r"\d+|[¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞°′″]", a)
            == re.findall(r"\d+|[¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞°′″]", b)
        )
        if not (note or wording):
            raise ValueError("Binding cannot change numerical figures or Latin wording")
        used.add(line)
    if used != set(changes):
        raise ValueError("Source binding contains unused line changes")
    support = {}
    for item in binding["supporting_lines"]:
        line, new = item["original_line"], item["current_line"]
        if (
            line in support
            or before["line_start"] <= line <= before["line_end"]
            or new != line + offset
            or not 1 <= new <= len(lines)
            or lines[new - 1] != item["text"]
        ):
            raise ValueError("Unbound supporting source line")
        support[line] = new

    def move(line):
        if type(line) is not int:
            raise ValueError("Source position must be an integer")
        if before["line_start"] <= line <= before["line_end"]:
            return line + offset
        if line in support:
            return support[line]
        raise ValueError("Source position lacks a reviewed relocation")

    anchors = {"start": before["line_start"]}
    for kind, field in (("assertion", "assertions"), ("context", "contexts"), ("event", "events")):
        anchors[kind] = {
            item["key"]: item.get("line", (item.get("lines") or [before["line_start"]])[0])
            for item in original.get(field, [])
        }
    rebound = copy.deepcopy(original)
    rebound["line_start"], rebound["line_end"] = after["line_start"], after["line_end"]
    for segment in rebound["basis"].get("page_segments", []):
        segment["line_start"], segment["line_end"] = (
            move(segment["line_start"]),
            move(segment["line_end"]),
        )
    for context in rebound.get("contexts", []):
        context["lines"] = [move(n) for n in context["lines"]]
        if context["kind"] == "source_coordinate_frame":
            for field in ("line_start", "line_end"):
                context["value"][field] = move(context["value"][field])
    for field in ("assertions", "events", "derivations"):
        for item in rebound.get(field, []):
            if "line" in item:
                item["line"] = move(item["line"])
            for fragment in item.get("source_fragments", []):
                fragment["line"] = move(fragment["line"])
    rebound["interval_sha256"] = after["sha256"]
    rebound["basis"]["source_binding_review_id"] = binding["id"]
    for assertion in rebound.get("assertions", []):
        if assertion["source_expression"] not in lines[assertion["line"] - 1]:
            raise ValueError("Relocation changes an original numerical expression")
    return rebound, anchors


def rebind_extraction_inputs(
    observations, classifications, texts, bindings, *, control_source_ids=()
):
    """Relocate frozen extraction inputs without modifying benchmark records."""
    indexed = index_bindings(bindings)
    records, decisions, volumes = {}, {}, set()
    for binding in indexed.values():
        volume = binding["volume"]
        if volume not in texts or text_sha(texts[volume]) != binding["current_source_sha256"]:
            raise ValueError("Extraction binding source fingerprint changed")
        volumes.add(volume)
        for field, target in (
            ("observation_record_bindings", records),
            ("coordinate_classification_bindings", decisions),
        ):
            for item in binding.get(field, []):
                if item["id"] in target:
                    raise ValueError("Duplicate extraction source binding")
                target[item["id"]] = (binding, item)
    book_lines = {volume: texts[volume].splitlines() for volume in volumes}
    controls = set(control_source_ids)
    moved, seen = [], set()

    def locator(value, source, offset):
        prefix = source + ":"
        if not isinstance(value, str) or not value.startswith(prefix):
            raise ValueError("Unrecognized source locator")
        pieces = value[len(prefix) :].split(":")
        if not pieces[0].isdigit() or int(pieces[0]) + offset < 1:
            raise ValueError("Invalid source locator position")
        pieces[0] = str(int(pieces[0]) + offset)
        return prefix + ":".join(pieces)

    for original in observations:
        if original["volume"] not in volumes:
            moved.append(original)
            continue
        if original["id"] not in records or original["id"] in seen:
            raise ValueError("Missing or duplicate extraction binding")
        binding, record = records[original["id"]]
        offset = binding["line_offset"]
        line = record["current_line"]
        lines = book_lines[original["volume"]]
        if (
            review_sha(original) != record["original_record_sha256"]
            or record["original_line"] != original["line"]
            or line != original["line"] + offset
            or not 1 <= line <= len(lines)
            or lines[line - 1] != record["current_row_original"]
            or record["current_source_record_id"]
            != locator(original["id"], original["source"], offset)
        ):
            raise ValueError("Extraction binding differs from frozen record or current source")
        old, current = original["row_original"].strip(), lines[line - 1].strip()
        kind = record["kind"]
        strip_notes = lambda text: re.sub(r"\[\^ed\d+\]", "", text).strip()
        if kind == "unchanged" and old != current:
            raise ValueError("Unreviewed extraction row change")
        if kind == "note_reference_renumbering" and strip_notes(old) != strip_notes(current):
            raise ValueError("Extraction change exceeds note renumbering")
        if kind not in ("unchanged", "note_reference_renumbering", "notation_revision"):
            raise ValueError("Unreviewed extraction revision kind")
        row = copy.deepcopy(original)
        if kind == "notation_revision":
            column = original.get("column")
            cells = current.strip("|").split("|") if current.startswith("|") else []
            if (
                original["id"] in controls
                or record.get("workbook_source_membership") != "not_selected"
                or record.get("normalization_status") != "unresolved"
                or type(column) is not int
                or not 1 <= column <= len(cells)
                or cells[column - 1].strip() != record["current_expression"]
                or "?" not in record["current_expression"]
            ):
                raise ValueError(
                    "Notation revision cannot silently revise a control or establish a scalar"
                )
            row["legacy_normalization"] = {
                key: original.get(key) for key in ("arcsec", "magnitude_arcsec")
            }
            row["arcsec"] = row["magnitude_arcsec"] = None
            row["flags"] = list(
                dict.fromkeys([*row.get("flags", []), "source_notation_unresolved"])
            )
        expected_loci = {}
        for field in ("time_locus", "hemisphere_locus"):
            if original.get(field):
                expected_loci[field] = locator(original[field], original["source"], offset)
                row[field] = expected_loci[field]
        if expected_loci != record["current_source_loci"]:
            raise ValueError("Extraction timing or hemisphere locator differs")
        row.update(
            line=line,
            row_original=lines[line - 1],
            source_current_record_id=record["current_source_record_id"],
            source_binding_review_id=binding["id"],
            source_version_sha256=binding["current_source_sha256"],
        )
        moved.append(row)
        seen.add(original["id"])
    if seen != set(records):
        raise ValueError("Unused extraction source binding")
    if classifications is None:
        return moved, None
    by_id = {row["id"]: row for row in moved}
    relocated, used = [], set()
    for original in classifications:
        if original["volume"] not in volumes or original["id"] not in decisions:
            relocated.append(original)
            continue
        if original["id"] in used:
            raise ValueError("Missing or duplicate classification source binding")
        binding, item = decisions[original["id"]]
        offset = binding["line_offset"]
        target = by_id.get(original["source_record_id"])
        if (
            review_sha(original) != item["original_sha256"]
            or item["line_offset"] != offset
            or item["original_source_record_id"] != original["source_record_id"]
            or target is None
            or target.get("source_current_record_id") != item["current_source_record_id"]
        ):
            raise ValueError("Classification differs from frozen source identity")
        row = copy.deepcopy(original)
        for field in ("line", "evidence_start", "evidence_end"):
            row[field] += offset
        lines = book_lines[original["volume"]]
        evidence = "\n".join(lines[row["evidence_start"] - 1 : row["evidence_end"]])
        if text_sha(evidence) != original["evidence_sha256"]:
            raise ValueError("Classification evidence changed and requires its own review")
        row["source_current_record_id"] = item["current_source_record_id"]
        relocated.append(row)
        used.add(original["id"])
    if used != set(decisions):
        raise ValueError("Unused classification source binding")
    return moved, relocated
