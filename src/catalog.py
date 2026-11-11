"""Compile version-bound source reviews; never infer clocks or missing digits."""

import copy
import hashlib
import json
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path

from .core import fraction_text, number
from .source_bindings import load_bindings


from .normalization import source_numeric_text as source_numeric_text
from .normalization import ANGLE_QUANTITIES as ANGLE_QUANTITIES
from .normalization import TIME_QUANTITIES as TIME_QUANTITIES
from .normalization import ANGULAR_RATES as ANGULAR_RATES
from .normalization import ZODIAC_SIGNS as ZODIAC_SIGNS
from .normalization import SOURCE_WORD_NUMBERS as SOURCE_WORD_NUMBERS
from .normalization import validate_reference_status as validate_reference_status
from .normalization import normalize_quantity as normalize_quantity
from .normalization import zodiac_arithmetic_values as zodiac_arithmetic_values


def source_key(record):
    if record.get("source_id") is not None:
        value = record["source_id"]
        if (
            not isinstance(value, str)
            or not re.fullmatch(r"[a-z][a-z0-9-]+", value)
            or record.get("volume") is not None
        ):
            raise ValueError("Named source requires its own identity without a Tycho volume")
        return value
    return record["volume"]


def source_fields(key):
    return {"source_id": key} if isinstance(key, str) else {"volume": key}


def identity(kind, volume, sha, line, key):
    token = hashlib.sha256(f"{volume}|{sha}|{line}|{key}".encode()).hexdigest()[:20]
    return f"{kind}-s{volume}-{token}" if isinstance(volume, str) else f"{kind}-v{volume}-{token}"


def compile_catalogue(batches, texts, spans, *, edition_hashes=None, source_bindings=None):
    """Validate reviews against canonical text, then compile assertions and coverage.

    Reviews supply explicit semantics. A successful compile verifies the bindings
    and arithmetic, not the reviewer's historical interpretation.
    """
    from .assembly import cell_intervals, literal_intervals
    from .source_bindings import apply_span_bindings, index_bindings, rebind_review

    batches = list(batches)
    bindings = index_bindings(source_bindings or [])
    if set(bindings) - {b["id"] for b in batches}:
        raise ValueError("Source binding references an unknown review")
    if bindings:
        spans = apply_span_bindings(spans, source_bindings)
    by_span = {s["id"]: s for s in spans}
    rows = {
        k: []
        for k in ("assertions", "contexts", "events", "derivations", "span_reviews", "coverage")
    }
    inspected = {}
    decisions = {}
    seen_batches = set()
    seen_ids = set()
    completed_assertions = {}
    completed_events = {}
    prepared_sources = {}
    for batch in sorted(batches, key=lambda b: b["id"]):
        if batch["id"] in seen_batches:
            raise ValueError("Duplicate review batch")
        seen_batches.add(batch["id"])
        volume = source_key(batch)
        text = texts[volume]
        if volume not in prepared_sources:
            sha = (
                edition_hashes[volume]
                if edition_hashes is not None and volume in edition_hashes
                else hashlib.sha256(text.encode()).hexdigest()
            )
            prepared_sources[volume] = (text.splitlines(), sha)
        lines, sha = prepared_sources[volume]
        anchors = {}
        if batch["id"] in bindings:
            batch, anchors = rebind_review(batch, text, bindings[batch["id"]])
        if sha != batch["edition_sha256"]:
            raise ValueError("Edition fingerprint mismatch")
        start, end = batch["line_start"], batch["line_end"]
        if not 1 <= start <= end <= len(lines):
            raise ValueError("Review interval outside source")
        interval = "\n".join(lines[start - 1 : end])
        if hashlib.sha256(interval.encode()).hexdigest() != batch["interval_sha256"]:
            raise ValueError("Reviewed interval fingerprint mismatch")
        basis = batch["basis"]
        unpaged_exclusion = (
            basis.get("kind") == "final_edition_review"
            and basis.get("non_observational_exclusion") is True
            and not batch.get("assertions")
            and not batch.get("events")
            and bool(batch.get("span_decisions"))
            and all(d.get("decision") == "exclude" for d in batch["span_decisions"])
        )
        unpaged_annotations = (
            basis.get("kind") == "final_edition_review"
            and basis.get("edition_annotations") is True
            and basis.get("printed_page") is None
            and not batch.get("events")
            and bool(batch.get("contexts"))
            and bool(batch.get("span_decisions"))
            and all(d.get("decision") == "context" for d in batch["span_decisions"])
        )
        annotation_markers = {}
        if unpaged_annotations:
            for context in batch["contexts"]:
                value = context.get("value", {})
                marker = value.get("note_marker", "")
                definition = value.get("definition_line")
                attachments = value.get("attachment_lines", [])
                if (
                    context.get("kind") != "source_observation_context"
                    or value.get("record_type") != "edition_annotation"
                    or not re.fullmatch(r"\[\^[\w-]+\]", marker)
                    or type(definition) is not int
                    or not start <= definition <= end
                    or not lines[definition - 1].startswith(marker + ":")
                    or not attachments
                    or any(
                        type(n) is not int or not 1 <= n < start or marker not in lines[n - 1]
                        for n in attachments
                    )
                    or set(context.get("lines", [])) != {definition, *attachments}
                ):
                    raise ValueError("Edition annotation lacks literal definition and attachment")
            for assertion in batch.get("assertions", []):
                notes = [
                    c
                    for c in batch["contexts"]
                    if c["key"] in assertion.get("context_keys", [])
                    and c["value"]["definition_line"] == assertion.get("line")
                ]
                flags = set(assertion.get("flags", []))
                role = assertion["role"]
                if (
                    "edition_note_marker" in assertion
                    or len(notes) != 1
                    or role
                    not in ("editorial_addition", "editorial_variant", "editorial_suggestion")
                    or not {"source_annotation_variant", "not_an_additional_raw_reading"} <= flags
                    or (
                        role != "editorial_addition"
                        and "alternative_suggestion_not_applied" not in flags
                    )
                    or any(
                        assertion.get(k) is not None
                        for k in ("event_key", "event_ref", "annotation_of_key")
                    )
                ):
                    raise ValueError(
                        "Unpaged numerical note requires an attached editorial annotation"
                    )
                annotation_markers[assertion["key"]] = notes[0]["value"]["note_marker"]
        if "annotation_attachment_citations" in basis:
            citations = basis["annotation_attachment_citations"]
            if not unpaged_annotations or not isinstance(citations, list) or not citations:
                raise ValueError("Attachment citations require a bound edition-note review")
            for citation in citations:
                if (
                    not isinstance(citation, dict)
                    or set(citation) != {"review_id", "context_key", "line", "printed_page"}
                    or type(citation["line"]) is not int
                    or type(citation["printed_page"]) is not int
                    or citation["printed_page"] < 1
                ):
                    raise ValueError("Invalid edition-note attachment citation")
                target = next(
                    (
                        c
                        for c in rows["contexts"]
                        if c["review_id"] == citation["review_id"]
                        and c["key"] == citation["context_key"]
                    ),
                    None,
                )
                value = target.get("value", {}) if target else {}
                if (
                    target is None
                    or source_key(target) != volume
                    or target.get("edition_sha256") != sha
                    or value.get("record_type") != "edition_annotation"
                    or citation["line"] not in value.get("attachment_lines", [])
                    or not any(
                        c["value"].get("note_marker") == value.get("note_marker")
                        and c["value"].get("definition_line") == value.get("definition_line")
                        and citation["line"] in c["value"].get("attachment_lines", [])
                        for c in batch["contexts"]
                    )
                ):
                    raise ValueError("Attachment citation differs from its literal note scope")
        locator = None
        if "source_page_locator" in basis:
            from .source_locator import validate_page_locator

            if basis.get("kind") != "final_edition_review":
                raise ValueError("Source page locator requires final-edition review")
            locator = validate_page_locator(basis["source_page_locator"])
        if not basis.get("kind") or (
            not basis.get("printed_page")
            and not (unpaged_exclusion or unpaged_annotations or locator)
        ):
            raise ValueError("Missing review basis")
        page_by_line = {}
        locator_by_line = {}
        if "page_segments" in basis:
            segments = basis["page_segments"]
            cursor = start
            if not isinstance(segments, list) or not segments:
                raise ValueError("Missing reviewed page segments")
            for segment_index, segment in enumerate(segments):
                pdf_page = segment.get("pdf_page") if isinstance(segment, dict) else None
                if (
                    not isinstance(segment, dict)
                    or any(
                        type(segment.get(k)) is not int
                        for k in ("line_start", "line_end", "printed_page")
                    )
                    or segment["line_start"] != cursor
                    or not cursor <= segment["line_end"] <= end
                    or segment["printed_page"] < 1
                    or (pdf_page is None and basis["kind"] != "final_edition_review")
                    or (pdf_page is not None and (type(pdf_page) is not int or pdf_page < 1))
                    or not isinstance(segment.get("witness_sha256"), str)
                    or not re.fullmatch(r"[0-9a-f]{64}", segment["witness_sha256"])
                ):
                    raise ValueError("Invalid or incomplete reviewed page segment")
                page_by_line.update(
                    (n, segment["printed_page"]) for n in range(cursor, segment["line_end"] + 1)
                )
                if locator is not None:
                    segment_locator = (
                        locator
                        if segment_index == 0
                        else dict(
                            source_pdf_page=pdf_page,
                            printed_page_label=str(segment["printed_page"]),
                            later_hand_page_label=None,
                        )
                        if pdf_page is not None
                        else None
                    )
                    locator_by_line.update(
                        (n, segment_locator) for n in range(cursor, segment["line_end"] + 1)
                    )
                cursor = segment["line_end"] + 1
            if cursor != end + 1:
                raise ValueError("Reviewed page segments do not cover interval")
        local_decisions = {}
        for decision in batch["span_decisions"]:
            span = by_span[decision["span_id"]]
            if source_key(span) != volume or span["edition_sha256"] != sha:
                raise ValueError("Span fingerprint mismatch")
            if not start <= span["line_start"] <= span["line_end"] <= end:
                raise ValueError("Inspected span outside review interval")
            if decision["decision"] not in ("include", "context", "exclude") or not decision.get(
                "reason"
            ):
                raise ValueError("Missing relevance decision")
            old = decisions.get(span["id"])
            if old and old != decision["decision"]:
                raise ValueError("Conflicting span review decisions")
            decisions[span["id"]] = decision["decision"]
            local_decisions[span["id"]] = decision["decision"]
            rows["span_reviews"].append(dict(**decision, review_id=batch["id"], basis=basis))
        inspected.setdefault(volume, set()).update(range(start, end + 1))
        rows["coverage"].append(
            dict(
                review_id=batch["id"],
                **source_fields(volume),
                edition_sha256=sha,
                line_start=start,
                line_end=end,
                basis=basis,
            )
        )
        maps = {}
        for kind, items in (
            ("context", batch.get("contexts", [])),
            ("event", batch.get("events", [])),
            ("assertion", batch.get("assertions", [])),
        ):
            maps[kind] = {}
            for item in items:
                line = item.get("line", (item.get("lines") or [start])[0])
                key = item["key"]
                if key in maps[kind]:
                    raise ValueError("Duplicate local record key")
                maps[kind][key] = identity(
                    kind, volume, sha, anchors.get(kind, {}).get(key, line), key
                )

        def external_assertion(ref, volume=volume, sha=sha):
            if (
                not isinstance(ref, dict)
                or set(ref) != {"review_id", "key", "basis"}
                or not isinstance(ref["basis"], str)
                or not ref["basis"].strip()
            ):
                raise ValueError("External assertion reference requires a reviewed basis")
            target = completed_assertions.get(ref["review_id"], {}).get(ref["key"])
            if target is None or source_key(target) != volume or target["edition_sha256"] != sha:
                raise ValueError("External assertion reference is unbound or crosses an edition")
            return target

        def context_ids(item, maps=maps):
            return [maps["context"][k] for k in item.get("context_keys", [])]

        for context in batch.get("contexts", []):
            if not context.get("lines") or any(not 1 <= n <= len(lines) for n in context["lines"]):
                raise ValueError("Context outside source")
            rows["contexts"].append(
                dict(
                    **context,
                    id=maps["context"][context["key"]],
                    **source_fields(volume),
                    edition_sha256=sha,
                    review_id=batch["id"],
                    text_original="\n".join(lines[n - 1] for n in context["lines"]),
                )
            )
        local_assertions = {a["key"]: a for a in batch.get("assertions", [])}
        compiled_local = {}
        for assertion in local_assertions.values():
            line = assertion["line"]
            span = by_span[assertion["span_id"]]
            if not start <= line <= end or not span["line_start"] <= line <= span["line_end"]:
                raise ValueError("Assertion outside reviewed span")
            if local_decisions.get(span["id"]) not in ("include", "context"):
                raise ValueError("Assertion requires relevant inspected span")
            expression = assertion["source_expression"]
            if not expression or expression not in lines[line - 1]:
                raise ValueError("Source expression mismatch")
            if "source_columns" in assertion:
                columns = assertion["source_columns"]
                slots = cell_intervals(lines[line - 1], declared_table=True)
                if (
                    assertion.get("column") is not None
                    or not isinstance(columns, list)
                    or len(columns) < 2
                    or any(type(c) is not int for c in columns)
                    or columns != list(range(columns[0], columns[-1] + 1))
                    or not 1 <= columns[0] <= columns[-1] <= len(slots)
                    or re.sub(
                        r"\s+\[recte: \d+(?:[′″])?\]$",
                        "",
                        lines[line - 1][slots[columns[0] - 1][0] : slots[columns[-1] - 1][1]],
                    )
                    != expression
                ):
                    raise ValueError("Source expression differs from consecutive table columns")
            if lines[line - 1].lstrip().startswith("|") and assertion.get("column") is not None:
                column = assertion["column"]
                slots = cell_intervals(lines[line - 1])
                if type(column) is not int or not 1 <= column <= len(slots):
                    raise ValueError("Source table column invalid")
                left, right = slots[column - 1]
                if not literal_intervals(lines[line - 1][left:right], expression):
                    raise ValueError("Source expression is not in the reviewed table column")
            source_expression = expression
            if "source_fragments" in assertion:
                fragments = assertion["source_fragments"]
                context_key = assertion.get("source_continuation_context_key")
                context = next(
                    (c for c in batch.get("contexts", []) if c["key"] == context_key), None
                )
                value = context.get("value") if context else None
                if (
                    not isinstance(fragments, list)
                    or not 2 <= len(fragments) <= 4
                    or context is None
                    or context.get("kind") != "source_observation_context"
                    or not isinstance(value, dict)
                    or value.get("record_type") != "source_continuation"
                    or context_key not in assertion.get("context_keys", [])
                    or len(context.get("lines", [])) != 1
                    or not isinstance(value.get("source_expression"), str)
                    or not value["source_expression"]
                    or value["source_expression"] not in lines[context["lines"][0] - 1]
                ):
                    raise ValueError("Source fragments require a bound continuation statement")
                positions = []
                for fragment in fragments:
                    n = fragment.get("line")
                    sid = fragment.get("span_id")
                    part = fragment.get("source_expression")
                    bound = by_span.get(sid)
                    if (
                        set(fragment)
                        not in (
                            {"line", "span_id", "source_expression"},
                            {"line", "span_id", "source_expression", "char_start", "char_end"},
                        )
                        or type(n) is not int
                        or not start <= n <= end
                        or bound is None
                        or source_key(bound) != volume
                        or bound["edition_sha256"] != sha
                        or not bound["line_start"] <= n <= bound["line_end"]
                        or local_decisions.get(sid) not in ("include", "context")
                        or not isinstance(part, str)
                        or not part
                    ):
                        raise ValueError("Source continuation fragment is unbound")
                    matches = literal_intervals(lines[n - 1], part)
                    matches = [
                        (left, right)
                        for left, right in matches
                        if not (part[0].isdigit() and left > 0 and lines[n - 1][left - 1] in "/⁄.")
                        and not (
                            part[-1].isdigit()
                            and right < len(lines[n - 1])
                            and (
                                lines[n - 1][right] in "/⁄"
                                or (
                                    lines[n - 1][right] == "."
                                    and right + 1 < len(lines[n - 1])
                                    and lines[n - 1][right + 1].isdigit()
                                )
                            )
                        )
                    ]
                    if "char_start" in fragment:
                        selected = (fragment["char_start"], fragment["char_end"])
                        if (
                            any(type(offset) is not int for offset in selected)
                            or selected not in matches
                        ):
                            raise ValueError(
                                "Source fragment character position differs from literal"
                            )
                        matches = [selected]
                    if len(matches) != 1:
                        raise ValueError("Source continuation fragment is unbound or ambiguous")
                    offset, fragment_end = matches[0]
                    if positions and (
                        n < positions[-1][0]
                        or (n == positions[-1][0] and offset < positions[-1][2])
                    ):
                        raise ValueError("Source continuation fragments overlap or reverse order")
                    positions.append((n, offset, fragment_end))
                if (
                    {k: fragments[0][k] for k in ("line", "span_id", "source_expression")}
                    != dict(line=line, span_id=assertion["span_id"], source_expression=expression)
                    or (
                        "char_start" in fragments[0]
                        and (assertion.get("char_start"), assertion.get("char_end"))
                        != (fragments[0]["char_start"], fragments[0]["char_end"])
                    )
                    or not line <= context["lines"][0] <= fragments[-1]["line"]
                    or any(
                        re.match(r"^\s*#{1,6}\s", s) for s in lines[line : fragments[-1]["line"]]
                    )
                ):
                    raise ValueError(
                        "Source continuation crosses a heading or lacks its primary fragment"
                    )
                source_expression = " ".join(f["source_expression"] for f in fragments)
            elif "source_continuation_context_key" in assertion:
                raise ValueError("Source continuation context requires literal fragments")
            numeric_expression = source_expression
            word_numbers = assertion.get("source_word_numbers", {})
            if not isinstance(word_numbers, dict):
                raise ValueError("Invalid source word-number mapping")
            for word, value in word_numbers.items():
                if (
                    word not in SOURCE_WORD_NUMBERS
                    or value != SOURCE_WORD_NUMBERS[word]
                    or len(re.findall(r"\b" + re.escape(word) + r"\b", numeric_expression)) != 1
                ):
                    raise ValueError("Unreviewed or absent source word number")
                numeric_expression = re.sub(
                    r"\b" + re.escape(word) + r"\b", value, numeric_expression
                )
            note_marker = assertion.get("source_note_marker_original")
            note_anchor = assertion.get("source_note_marker_after_unit")
            if note_anchor is not None and note_marker is None:
                raise ValueError("Internal note anchor requires a reviewed marker")
            if note_marker is not None:
                if not re.fullmatch(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]+", note_marker):
                    raise ValueError("Invalid attached source note marker")
                if note_anchor is None:
                    match = re.search(
                        re.escape(note_marker)
                        + r"(?P<suffix>\s*["
                        + "".join(ZODIAC_SIGNS.values())
                        + r"]\s*)?$",
                        numeric_expression,
                    )
                    if match is None:
                        raise ValueError("Invalid attached source note marker")
                    numeric_expression = numeric_expression[: match.start()] + (
                        match.group("suffix") or ""
                    )
                else:
                    if note_anchor == "minute" and assertion["quantity"] in (
                        "recorded_clock",
                        "transit_clock",
                    ):
                        matches = list(
                            re.finditer(
                                r"(?<=\^m\^)" + re.escape(note_marker) + r"(?=\s*\d+\^s\^\s*$)",
                                numeric_expression,
                            )
                        )
                        if len(matches) != 1:
                            raise ValueError("Invalid internal clock note marker")
                        match = matches[0]
                    elif (
                        note_anchor == "degree"
                        and assertion["quantity"] in ANGLE_QUANTITIES
                        and set(assertion.get("components", {})) == {"degree", "arcminute"}
                    ):
                        match = re.fullmatch(
                            r"\s*\d+°?(?P<marker>" + re.escape(note_marker) + r")\s+\d+′?\s*",
                            numeric_expression,
                        )
                        if match is None:
                            raise ValueError("Invalid internal degree note marker")
                        numeric_expression = (
                            numeric_expression[: match.start("marker")]
                            + numeric_expression[match.end("marker") :]
                        )
                        match = None
                    else:
                        raise ValueError("Unreviewed internal source note anchor")
                    if match is not None:
                        numeric_expression = (
                            numeric_expression[: match.start()] + numeric_expression[match.end() :]
                        )
            if any(
                key in assertion
                for key in (
                    "source_number_grouping",
                    "source_digit_restorations",
                    "comparison_label_original",
                    "comparison_sources",
                )
            ):
                numeric_expression = source_numeric_text(assertion, numeric_expression)
            if "source_unit_notation" in assertion:
                from .normalization import interpret_part_minute_notation

                if "source_number_grouping" in assertion or "source_word_numbers" in assertion:
                    raise ValueError("Unit notation cannot combine numerical rewriting rules")
                numeric_expression, _ = interpret_part_minute_notation(assertion)
            zodiac_origin_key = assertion.get("zodiac_sign_inherited_from_key")
            zodiac_basis_key = assertion.get("zodiac_sign_basis_key")
            if "zodiac_sign_basis_key" in assertion and (
                assertion.get("zodiac_sign") is None
                or "zodiac_sign_inherited_from_key" in assertion
            ):
                raise ValueError("Zodiac context requires one explicit sign basis")
            if (
                "zodiac_sign_inherited_from_key" in assertion
                and assertion.get("zodiac_sign") is None
            ):
                raise ValueError("Inherited zodiac sign requires a reviewed sign")
            if assertion.get("zodiac_sign") is not None:
                sign = assertion["zodiac_sign"]
                glyphs = {
                    name for name, glyph in ZODIAC_SIGNS.items() if glyph in source_expression
                }
                if "zodiac_sign_basis_key" in assertion:
                    frame = next(
                        (c for c in batch.get("contexts", []) if c["key"] == zodiac_basis_key), None
                    )
                    value = frame.get("value") if frame else None
                    frame_lines = frame.get("lines", []) if frame else []
                    required = {
                        "subject",
                        "zodiac_sign",
                        "line_start",
                        "line_end",
                        "source_expression",
                    }
                    following_note = (
                        isinstance(value, dict)
                        and value.get("scope_basis") == "following_table_note"
                    )
                    scope_valid = False
                    if (
                        isinstance(value, dict)
                        and len(frame_lines) == 1
                        and all(type(value.get(k)) is int for k in ("line_start", "line_end"))
                    ):
                        if following_note:
                            scope_valid = (
                                type(assertion.get("column")) is int
                                and start
                                <= value["line_start"]
                                <= line
                                <= value["line_end"]
                                < frame_lines[0]
                                <= end
                                and all(
                                    s.lstrip().startswith("|")
                                    for s in lines[value["line_start"] - 1 : value["line_end"]]
                                )
                                and not any(
                                    s.strip() for s in lines[value["line_end"] : frame_lines[0] - 1]
                                )
                            )
                        else:
                            scope_valid = (
                                start
                                <= value["line_start"]
                                == frame_lines[0]
                                <= line
                                <= value["line_end"]
                                <= end
                            )
                    if (
                        frame is None
                        or frame.get("kind") != "source_coordinate_frame"
                        or not isinstance(value, dict)
                        or set(value) != required | ({"scope_basis"} if following_note else set())
                        or len(frame_lines) != 1
                        or any(type(value.get(k)) is not int for k in ("line_start", "line_end"))
                        or not scope_valid
                        or assertion["quantity"] not in ("ecliptic_longitude", "orbital_longitude")
                        or assertion.get("direction") is not None
                        or value["subject"] != assertion["subject"]
                        or value["zodiac_sign"] != sign
                        or zodiac_basis_key not in assertion.get("context_keys", [])
                        or glyphs
                        or not isinstance(value["source_expression"], str)
                        or not value["source_expression"]
                        or value["source_expression"] not in lines[frame_lines[0] - 1]
                        or {
                            name
                            for name, glyph in ZODIAC_SIGNS.items()
                            if glyph in value["source_expression"]
                            or re.search(
                                r"\b"
                                + (r"Scorpi(?:o|us)" if name == "Scorpio" else re.escape(name))
                                + r"\b",
                                value["source_expression"],
                            )
                        }
                        != {sign}
                        or any(
                            re.match(r"^\s*#{1,6}\s", s)
                            for s in lines[frame_lines[0] : value["line_end"]]
                        )
                    ):
                        raise ValueError("Invalid reviewed zodiac context or source frame scope")
                elif "zodiac_sign_inherited_from_key" in assertion:
                    target = (
                        local_assertions.get(zodiac_origin_key)
                        if isinstance(zodiac_origin_key, str)
                        else None
                    )
                    column_origin = (
                        target is not None
                        and target["line"] < line
                        and target.get("column") == assertion.get("column")
                        and target.get("role") == assertion.get("role")
                    )
                    variant_origin = (
                        target is not None
                        and target["line"] == line
                        and assertion.get("variant_of_key") == target["key"]
                        and assertion.get("role") in ("printed_correction", "editorial_variant")
                        and type(target.get("column")) is int
                        and type(assertion.get("column")) is int
                        and target["column"] < assertion["column"]
                    )
                    source_variant_origin = (
                        target is not None
                        and target["line"] < line
                        and assertion.get("role") == "source_alternative"
                        and assertion.get("variant_of_key") == target["key"]
                        and assertion.get("inherited_components", {}).get("degree") == target["key"]
                        and target.get("components", {}).get("degree")
                        == assertion.get("components", {}).get("degree")
                    )
                    ephemeris_origin = (
                        target is not None
                        and target["line"] == line
                        and assertion.get("zodiac_inheritance_kind") == "same_ephemeris_statement"
                        and assertion.get("model_name") in ("Stadius", "Carelli")
                        and target.get("model_name") == assertion["model_name"]
                        and target.get("role") == assertion.get("role") == "historical_prediction"
                        and target.get("subject")
                        in ("Moon", "Mars", "Venus", "Mercury", "Jupiter", "Saturn")
                        and assertion.get("subject")
                        in ("Moon", "Mars", "Venus", "Mercury", "Jupiter", "Saturn")
                        and target["subject"] != assertion["subject"]
                        and target.get("column") is None
                        and assertion.get("column") is None
                        and not lines[line - 1].lstrip().startswith("|")
                        and lines[line - 1].find(target["source_expression"])
                        < lines[line - 1].find(expression)
                    )
                    target_expression = (
                        " ".join(f["source_expression"] for f in target["source_fragments"])
                        if target is not None and "source_fragments" in target
                        else target.get("source_expression", "")
                        if target
                        else ""
                    )
                    if (
                        glyphs
                        or target is None
                        or not (
                            column_origin
                            or variant_origin
                            or source_variant_origin
                            or ephemeris_origin
                        )
                        or ("zodiac_inheritance_kind" in assertion and not ephemeris_origin)
                        or assertion["quantity"] != "ecliptic_longitude"
                        or target["quantity"] != assertion["quantity"]
                        or target.get("zodiac_sign") != sign
                        or "zodiac_sign_inherited_from_key" in target
                        or (
                            not ephemeris_origin
                            and not source_variant_origin
                            and (
                                type(assertion.get("column")) is not int or assertion["column"] < 1
                            )
                        )
                        or any(
                            target.get(k) != assertion.get(k)
                            for k in (
                                ("model_name", "source_parameter_kind")
                                if ephemeris_origin
                                else ("subject", "model_name", "source_parameter_kind")
                            )
                        )
                        or not set(target.get("context_keys", []))
                        & set(assertion.get("context_keys", []))
                        or {
                            name
                            for name, glyph in ZODIAC_SIGNS.items()
                            if glyph in target_expression
                        }
                        != {sign}
                    ):
                        raise ValueError("Invalid reviewed zodiac column inheritance")
                elif glyphs != {sign}:
                    raise ValueError("Zodiac interpretation differs from literal source glyph")
            components = assertion.get("components") or {}
            if "ordinal_degree" in components or "ordinal_degree_evidence" in assertion:
                evidence = assertion.get("ordinal_degree_evidence")
                if (
                    not isinstance(evidence, dict)
                    or set(evidence) != {"line", "expression"}
                    or type(evidence["line"]) is not int
                    or not start <= evidence["line"] <= end
                    or not isinstance(evidence["expression"], str)
                    or not evidence["expression"]
                    or evidence["expression"] not in lines[evidence["line"] - 1]
                ):
                    raise ValueError("Ordinal degree requires literal source-bound evidence")
            units = (
                "sign_count",
                "sexagena",
                "degree",
                "ordinal_degree",
                "arcminute",
                "arcsecond",
                "arcsexagesimal_third",
                "arcsexagesimal_fourth",
                "arcsexagesimal_fifth",
                "arcsexagesimal_sixth",
                "arcsexagesimal_seventh",
                "arcsexagesimal_eighth",
                "arcsexagesimal_ninth",
                "arcsexagesimal_tenth",
                "day",
                "day_minute",
                "day_second",
                "day_third",
                "day_fourth",
                "day_fifth",
                "day_sixth",
                "hour",
                "minute",
                "second",
                "time_third",
                "time_fourth",
                "time_fifth",
                "semidiameter",
                "semidiameter_minute",
                "semidiameter_second",
                "mile",
                "mile_minute",
                "mile_second",
                "ratio",
                "proportional_minute",
                "proportional_second",
                "proportional_third",
                "source_part",
                "part_minute",
                "part_second",
                "reference_scale",
                "fraction",
                "scalar",
                "point",
                "point_minute",
                "digit",
                "digit_minute",
                "digit_second",
                "component_1",
                "component_2",
                "component_3",
                "component_4",
            )
            inherited = assertion.get("inherited_components", {})
            literal_inherited = set(inherited)
            carry = None
            if "table_carry" in assertion:
                from .table_components import table_carry_origin

                carry = table_carry_origin(assertion, batch, lines)
                if carry["unit"] not in components or number(
                    fraction_text(components[carry["unit"]])
                ) != number(fraction_text(carry["source_expression"])):
                    raise ValueError("Carried component differs from its printed source origin")
                if carry["source_line"] < line:
                    literal_inherited.add(carry["unit"])
            source_order = assertion.get("source_component_order", units)
            if "source_component_order" in assertion and (
                not components
                or not isinstance(source_order, list)
                or not source_order
                or any(u not in units for u in source_order)
                or len(set(source_order)) != len(source_order)
                or set(source_order) != set(components) - literal_inherited
            ):
                raise ValueError("Source component order must name each literal unit exactly once")
            literal_angle = re.fullmatch(
                r"\s*\d+(?:\s+\d+/\d+|/\d+)?\s*([°′″])\s*", fraction_text(numeric_expression)
            )
            if (
                assertion["quantity"] in ANGLE_QUANTITIES
                and literal_angle
                and set(components) - literal_inherited
                != {{"°": "degree", "′": "arcminute", "″": "arcsecond"}[literal_angle.group(1)]}
            ):
                raise ValueError("Components differ from explicit angular unit")
            literal_time = re.fullmatch(
                r"\s*\d+(?:\s+\d+/\d+|/\d+)?\s*\^([hms])\^\s*", fraction_text(numeric_expression)
            )
            if (
                assertion["quantity"] in TIME_QUANTITIES
                and literal_time
                and set(components) - literal_inherited
                != {{"h": "hour", "m": "minute", "s": "second"}[literal_time.group(1)]}
            ):
                raise ValueError("Components differ from explicit time unit")
            variant = assertion.get("variant_of_key")
            if variant:
                original = local_assertions[variant]
                if assertion["role"] not in (
                    "printed_correction",
                    "editorial_variant",
                    "source_alternative",
                ):
                    raise ValueError(
                        "Variant must preserve its correction, editorial or source-alternative role"
                    )
                if any(
                    assertion.get(k) != original.get(k)
                    for k in ("quantity", "subject", "reference")
                ):
                    raise ValueError("Variant quantity/endpoints differ from original")
            for unit, parent_key in inherited.items():
                if parent_key != variant or unit not in components:
                    raise ValueError("Inherited component requires the linked original")
                parent = local_assertions[parent_key]
                if unit in parent.get("inherited_components", {}):
                    raise ValueError("Inherited component chain is unsupported")
                parent_component = parent.get("components", {}).get(unit)
                if parent_component is None or number(fraction_text(parent_component)) != number(
                    fraction_text(components[unit])
                ):
                    raise ValueError("Inherited component differs from linked original")
            if components:
                from .numeric_integrity import validate_units

                validate_units(
                    numeric_expression,
                    components,
                    literal_inherited,
                    source_order,
                    assertion.get("source_component_addends"),
                    assertion["quantity"],
                    lines[line - 1],
                )
                tokens = re.findall(r"\d+(?:\s+\d+/\d+|/\d+)?", fraction_text(numeric_expression))
                source_values = [number(token) for token in tokens]
                addends = assertion.get("source_component_addends", {})
                if "source_component_addends" in assertion and (
                    not isinstance(addends, dict)
                    or not addends
                    or set(addends) - set(components)
                    or set(addends) & literal_inherited
                ):
                    raise ValueError("Source addends require literal, noninherited component units")
                component_values = []
                for unit in source_order:
                    if unit not in components or unit in literal_inherited:
                        continue
                    parts = addends.get(unit, [components[unit]])
                    if (
                        not isinstance(parts, list)
                        or (unit in addends and len(parts) < 2)
                        or any(
                            not isinstance(p, str)
                            or not re.fullmatch(
                                r"\d+(?:/\d+)?(?:\s+\d+/\d+)?", fraction_text(p).strip()
                            )
                            for p in parts
                        )
                        or sum((number(fraction_text(p)) for p in parts), Fraction())
                        != number(fraction_text(components[unit]))
                    ):
                        raise ValueError("Source component addends differ from their exact total")
                    component_values.extend(number(fraction_text(p)) for p in parts)
                if source_values != component_values:
                    raise ValueError("Component does not match the complete source number")
            elif "source_component_addends" in assertion:
                raise ValueError("Source addends require interpreted components")
            if not assertion.get("unit_basis"):
                raise ValueError("Missing unit basis")
            if "edition_note_marker" in assertion:
                raise ValueError("Edition note markers must come from validated source contexts")
            note_marker = None
            if unpaged_annotations:
                target = external_assertion(assertion.get("annotation_of_ref"))
                if (
                    target["line"] >= start
                    or target["role"]
                    in ("editorial_addition", "editorial_variant", "editorial_suggestion")
                    or any(target.get(k) != assertion.get(k) for k in ("subject", "reference"))
                ):
                    raise ValueError("Unpaged numerical note requires its original source quantity")
                note_marker = annotation_markers[assertion["key"]]
            missing_reference = validate_reference_status(assertion)
            if (
                assertion["quantity"] in ("angular_separation", "separation_difference")
                and not assertion.get("reference")
                and not missing_reference
            ):
                raise ValueError("Angular separation requires both endpoints")
            from .source_coordinate_products import bind_coordinate_product

            coordinate_product = bind_coordinate_product(
                assertion, batch.get("contexts", []), lines, start, end, maps["context"]
            )
            record = dict(
                **assertion,
                id=maps["assertion"][assertion["key"]],
                **source_fields(volume),
                edition_sha256=sha,
                printed_page=page_by_line.get(line, basis["printed_page"]),
                review_id=batch["id"],
                normalized=normalize_quantity(assertion),
                context_ids=context_ids(assertion),
                event_id=maps["event"].get(assertion.get("event_key")),
                text_original=lines[line - 1],
            )
            if coordinate_product is not None:
                record["source_coordinate_product"] = coordinate_product
            quantity_locator = locator_by_line.get(line, locator)
            if carry is not None and carry["source_line"] < line:
                record["source_component_carry"] = dict(
                    unit=carry["unit"],
                    source_line=carry["source_line"],
                    source_column=carry["source_column"],
                    source_expression=carry["source_expression"],
                    source_printed_page=page_by_line.get(
                        carry["source_line"], basis["printed_page"]
                    ),
                    rule_context_id=maps["context"][carry["rule_key"]],
                )
            if note_marker is not None:
                record["edition_note_marker"] = note_marker
                record["locator"] = note_marker
            if quantity_locator is not None:
                record["source_page_locator"] = quantity_locator
            record["variant_of_id"] = maps["assertion"].get(variant)
            if "source_fragments" in assertion:
                record["source_fragment_pages"] = list(
                    dict.fromkeys(
                        page_by_line.get(f["line"], basis["printed_page"])
                        for f in assertion["source_fragments"]
                    )
                )
            equal_key = assertion.get("source_value_equal_to_key")
            if equal_key is not None or "source_value_stated_equal" in assertion.get("flags", []):
                target = compiled_local.get(equal_key)
                clock_equal = (
                    assertion["quantity"] == "recorded_clock"
                    and assertion["role"] == "recorded_clock"
                    and assertion["subject"] == "observing clock"
                    and assertion.get("reference") is None
                    and expression in ("The hour as above.", "The hour as above")
                )
                repeated_equal = (
                    expression == "the same"
                    and assertion["quantity"] == "angular_separation"
                    and assertion["role"] == "repeated_reading"
                    and target is not None
                    and target["role"] in ("recorded_reading", "repeated_reading")
                    and assertion.get("reference") == target.get("reference")
                )
                separation_equal = (
                    assertion["quantity"] == "angular_separation"
                    and assertion["role"] in ("recorded_reading", "repeated_reading", "calibration")
                    and (
                        expression in ("the same amount", "tantundem", "by the same interval")
                        or repeated_equal
                    )
                )
                if (
                    target is None
                    or assertion.get("components")
                    or not (clock_equal or separation_equal)
                    or "source_value_stated_equal" not in assertion.get("flags", [])
                    or any(
                        assertion.get(k) != target.get(k)
                        for k in ("quantity", "subject", "direction")
                    )
                    or (assertion["role"] != target["role"] and not repeated_equal)
                    or assertion.get("direction") is not None
                    or target.get("source_value_equal_to_id") is not None
                    or (
                        target["normalized"]["status"] != "exact"
                        and not (
                            repeated_equal
                            and target["normalized"].get("normalization_issue")
                            == "source_notation_unresolved"
                            and "source_notation_unresolved" in assertion.get("flags", [])
                        )
                    )
                    or target["normalized"]["unit"]
                    != ("second_of_time" if clock_equal else "arcsecond")
                    or target["line"] > line
                    or not set(context_ids(assertion)) & set(target["context_ids"])
                    or (
                        target["line"] == line
                        and lines[line - 1].find(target["source_expression"])
                        >= lines[line - 1].find(expression)
                    )
                ):
                    raise ValueError(
                        "Stated equal value requires an earlier compatible quantity and explicit source relation"
                    )
                record["normalized"] = dict(target["normalized"])
                record["source_value_equal_to_id"] = target["id"]
                if repeated_equal:
                    record["source_equality_kind"] = "repeated_measurement"
            if zodiac_origin_key is not None:
                record["zodiac_sign_inherited_from_id"] = maps["assertion"][zodiac_origin_key]
            if zodiac_basis_key is not None:
                record["zodiac_sign_basis_context_id"] = maps["context"][zodiac_basis_key]
            if "calculation_epoch_key" in assertion:
                if "calculation_epoch_ref" in assertion:
                    raise ValueError("Competing calculation epoch links")
                epoch_key = assertion["calculation_epoch_key"]
                if (
                    epoch_key not in local_assertions
                    or local_assertions[epoch_key]["quantity"] != "calculation_epoch"
                ):
                    raise ValueError("Assertion epoch link requires a calculation epoch")
                record["calculation_epoch_id"] = maps["assertion"][epoch_key]
            if "calculation_epoch_ref" in assertion:
                target = external_assertion(assertion["calculation_epoch_ref"])
                if target["quantity"] != "calculation_epoch":
                    raise ValueError("External epoch must be a calculation epoch")
                record["calculation_epoch_id"] = target["id"]
            if "source_time_anchor_event_key" in assertion:
                key = assertion["source_time_anchor_event_key"]
                target = next((e for e in batch.get("events", []) if e["key"] == key), None)
                if (
                    target is None
                    or key == assertion.get("event_key")
                    or target["line"] >= line
                    or assertion["quantity"] != "clock_elapsed_time"
                    or assertion.get("time_reference") != "elapsed_after_prior_observations"
                ):
                    raise ValueError("Relative time requires its earlier source observation group")
                record["source_time_anchor_event_id"] = maps["event"][key]
            annotation = assertion.get("annotation_of_key")
            if annotation is not None and "annotation_of_ref" in assertion:
                raise ValueError("Annotation cannot have both local and external targets")
            if annotation is not None:
                if (
                    annotation not in maps["assertion"]
                    or annotation == assertion["key"]
                    or assertion["role"]
                    not in ("editorial_addition", "editorial_variant", "editorial_suggestion")
                ):
                    raise ValueError("Invalid annotation target or role")
                record["annotation_of_id"] = maps["assertion"][annotation]
            if "annotation_of_ref" in assertion:
                if assertion["role"] not in (
                    "editorial_addition",
                    "editorial_variant",
                    "editorial_suggestion",
                ):
                    raise ValueError("External annotation requires an editorial role")
                record["annotation_of_id"] = external_assertion(assertion["annotation_of_ref"])[
                    "id"
                ]
            series = assertion.get("series_key")
            record["series_id"] = maps["context"].get(series)
            if series:
                series_context = next(
                    (c for c in batch.get("contexts", []) if c["key"] == series), None
                )
                if not series_context or series_context["kind"] != "repeated_series":
                    raise ValueError("Unknown repeated series")
                if not isinstance(assertion.get("ordinal"), int) or assertion["ordinal"] < 1:
                    raise ValueError("Repeated series requires positive source ordinal")
                if assertion.get("ordinal_original", "") not in lines[line - 1]:
                    raise ValueError("Source ordinal absent")
            if "event_ref" in assertion:
                ref = assertion["event_ref"]
                if (
                    assertion.get("event_key")
                    or not isinstance(ref, dict)
                    or set(ref) != {"review_id", "key", "basis"}
                    or not isinstance(ref["basis"], str)
                    or not ref["basis"].strip()
                ):
                    raise ValueError("External event reference requires one reviewed association")
                prior = completed_events.get(ref["review_id"], {})
                target = prior.get("events", {}).get(ref["key"])
                if (
                    target is None
                    or prior.get("source") != volume
                    or prior.get("edition_sha256") != sha
                    or target.get("subject") != assertion.get("subject")
                ):
                    raise ValueError("External event is unbound or differs in source or subject")
                record["event_id"] = target["id"]
            if "event_clock_ref" in assertion:
                ref = assertion["event_clock_ref"]
                mode = assertion.get("clock_association_kind")
                if (
                    assertion.get("event_key")
                    or "event_ref" in assertion
                    or not isinstance(ref, dict)
                    or set(ref) != {"review_id", "key", "basis"}
                    or not isinstance(ref["basis"], str)
                    or not ref["basis"].strip()
                    or mode not in ("point", "interval_lower", "interval_upper")
                    or assertion["quantity"] != "recorded_clock"
                    or assertion["role"] != "recorded_clock"
                    or assertion["subject"] != "observing clock"
                    or assertion.get("reference") is not None
                    or assertion.get("direction") is not None
                    or "absolute_time_unestablished" not in assertion.get("flags", [])
                    or "clock_association_unresolved" in assertion.get("flags", [])
                ):
                    raise ValueError(
                        "Supplementary clock requires an explicit point or interval association"
                    )
                prior = completed_events.get(ref["review_id"], {})
                target = prior.get("events", {}).get(ref["key"])
                if (
                    target is None
                    or prior.get("source") != volume
                    or prior.get("edition_sha256") != sha
                    or target.get("line") != line
                ):
                    raise ValueError("Supplementary clock must belong to the same source statement")
                record["event_id"] = target["id"]
                if mode == "point":
                    if target.get("clock_assertion_id") is not None:
                        raise ValueError(
                            "Supplementary clock cannot replace an existing clock association"
                        )
                    target["clock_assertion_id"] = record["id"]
            if assertion.get("event_key") and record["event_id"] is None:
                raise ValueError("Unknown event")
            if record["id"] in seen_ids:
                raise ValueError("Duplicate source assertion identity")
            seen_ids.add(record["id"])
            rows["assertions"].append(record)
            compiled_local[assertion["key"]] = record
        for event in batch.get("events", []):
            if not start <= event["line"] <= end:
                raise ValueError("Event outside review interval")
            clock = event.get("clock_key")
            if clock and any(
                a.get("event_key") == event["key"]
                and "clock_association_unresolved" in a.get("flags", [])
                for a in local_assertions.values()
            ):
                raise ValueError("Unresolved clock association cannot select an event clock")
            if clock and local_assertions[clock]["quantity"] not in (
                "recorded_clock",
                "transit_clock",
            ):
                raise ValueError(
                    "Event clock must be a recorded clock, not an hour angle or expected time"
                )
            epoch = event.get("epoch_key")
            if epoch and local_assertions[epoch]["quantity"] != "calculation_epoch":
                raise ValueError("Event epoch must be a calculation epoch")
            epoch_id = maps["assertion"].get(epoch)
            if "epoch_ref" in event:
                if epoch:
                    raise ValueError("Competing event epoch links")
                target = external_assertion(event["epoch_ref"])
                if target["quantity"] != "calculation_epoch":
                    raise ValueError("External event epoch must be a calculation epoch")
                epoch_id = target["id"]
            rows["events"].append(
                dict(
                    **event,
                    id=maps["event"][event["key"]],
                    **source_fields(volume),
                    review_id=batch["id"],
                    context_ids=context_ids(event),
                    clock_assertion_id=maps["assertion"].get(clock),
                    epoch_assertion_id=epoch_id,
                )
            )
        for derivation in batch.get("derivations", []):
            if "input_refs" in derivation:
                if (
                    "input_keys" in derivation
                    or not isinstance(derivation["input_refs"], list)
                    or not derivation["input_refs"]
                ):
                    raise ValueError("Derivation requires one nonempty input reference list")
                inputs = []
                for ref in derivation["input_refs"]:
                    if isinstance(ref, dict) and set(ref) == {"key"}:
                        if ref["key"] not in maps["assertion"]:
                            raise ValueError("Unknown local derivation input")
                        inputs.append(maps["assertion"][ref["key"]])
                    else:
                        inputs.append(external_assertion(ref)["id"])
            else:
                inputs = [maps["assertion"][k] for k in derivation["input_keys"]]
            if ("output_key" in derivation) == ("output_ref" in derivation):
                raise ValueError("Derivation requires exactly one local or external output")
            if "output_ref" in derivation:
                output = external_assertion(derivation["output_ref"])["id"]
            else:
                if derivation["output_key"] not in maps["assertion"]:
                    raise ValueError("Unknown local derivation output")
                output = maps["assertion"][derivation["output_key"]]
            values = {a["id"]: a["normalized"] for a in rows["assertions"]}
            norms = [values[k] for k in [*inputs, output]]
            computed = None
            agrees = None
            if (
                derivation["operation"]
                in (
                    "difference",
                    "difference_modulo_360_degrees",
                    "difference_modulo_360_in_zodiac_frame",
                )
                and len(inputs) != 2
            ):
                raise ValueError("Difference requires two ordered inputs")
            if derivation["operation"] == "mean" and len(inputs) < 2:
                raise ValueError("Mean requires at least two inputs")
            if derivation["operation"] in (
                "sum",
                "difference",
                "mean",
                "sum_modulo_360_degrees",
                "difference_modulo_360_degrees",
                "sum_modulo_360_in_zodiac_frame",
                "difference_modulo_360_in_zodiac_frame",
            ) and all(n["status"] == "exact" for n in norms):
                if len({n["unit"] for n in norms}) != 1:
                    raise ValueError("Derivation units differ")
                magnitudes = (
                    zodiac_arithmetic_values(norms)
                    if derivation["operation"]
                    in ("sum_modulo_360_in_zodiac_frame", "difference_modulo_360_in_zodiac_frame")
                    else [Fraction(n["magnitude"]) for n in norms]
                )
                computed = (
                    magnitudes[0] - magnitudes[1]
                    if derivation["operation"]
                    in (
                        "difference",
                        "difference_modulo_360_degrees",
                        "difference_modulo_360_in_zodiac_frame",
                    )
                    else sum(magnitudes[:-1], Fraction())
                )
                if derivation["operation"] == "mean":
                    computed /= len(inputs)
                if derivation["operation"] in (
                    "sum_modulo_360_degrees",
                    "difference_modulo_360_degrees",
                    "sum_modulo_360_in_zodiac_frame",
                    "difference_modulo_360_in_zodiac_frame",
                ):
                    if norms[0]["unit"] != "arcsecond":
                        raise ValueError("Circular arithmetic requires angular quantities")
                    computed %= 360 * 3600
                agrees = computed == magnitudes[-1]
            rows["derivations"].append(
                dict(
                    **derivation,
                    id=identity(
                        "derivation", volume, sha, anchors.get("start", start), derivation["key"]
                    ),
                    input_ids=inputs,
                    output_id=output,
                    review_id=batch["id"],
                    computed_magnitude=str(computed) if computed is not None else None,
                    arithmetic_agrees=agrees,
                    **(
                        dict(arithmetic_frame="zodiac_zero")
                        if derivation["operation"]
                        in (
                            "sum_modulo_360_in_zodiac_frame",
                            "difference_modulo_360_in_zodiac_frame",
                        )
                        else {}
                    ),
                )
            )
        reviewed_directions = set()
        for review in batch.get("direction_reviews", []):
            target = external_assertion(review["target_ref"])
            anchor = (
                external_assertion(review["source_label_ref"])
                if "source_label_ref" in review
                else target
            )
            expansion = review.get("source_expansion")
            label = review.get("source_label")
            meaning = {
                "septentrionalis": ("S.", "north"),
                "borealis": ("B.", "north"),
                "meridionalis": ("M.", "south"),
                "australis": ("A.", "south"),
            }.get(expansion)
            direction = review.get("direction")
            old = review.get("expected_direction")
            if (
                not review.get("key")
                or not review.get("reason")
                or meaning != (label, direction)
                or old not in ("north", "south")
                or old == direction
                or target.get("direction") != old
                or target["id"] in reviewed_directions
                or target["quantity"] not in ("declination", "ecliptic_latitude")
                or target["normalized"]["status"] != "exact"
                or target["normalized"]["unit"] != "arcsecond"
                or label not in anchor["source_expression"]
            ):
                raise ValueError("Invalid or unbound direction interpretation review")
            if anchor is not target and (
                "hemisphere_inherited" not in target.get("flags", [])
                or anchor["line"] >= target["line"]
                or type(target.get("column")) is not int
                or any(
                    anchor.get(k) != target.get(k)
                    for k in ("quantity", "column", "subject", "model_name", "review_id")
                )
            ):
                raise ValueError("Direction label inheritance requires its earlier source column")
            previous = copy.deepcopy(target["normalized"])
            revised = normalize_quantity(dict(target, direction=direction))
            if any(revised.get(k) != v for k, v in previous.items() if k != "signed_magnitude"):
                raise ValueError("Direction review cannot change component magnitudes or units")
            target.setdefault("direction_review_history", []).append(
                dict(
                    review_id=batch["id"],
                    key=review["key"],
                    old_direction=old,
                    new_direction=direction,
                    previous_normalized=previous,
                    source_label=label,
                    source_expansion=expansion,
                    source_label_assertion_id=anchor["id"],
                    reason=review["reason"],
                )
            )
            target.update(direction=direction, normalized=revised)
            reviewed_directions.add(target["id"])
        completed_assertions[batch["id"]] = {
            a["key"]: a for a in rows["assertions"] if a["review_id"] == batch["id"]
        }
        completed_events[batch["id"]] = dict(
            source=volume,
            edition_sha256=sha,
            events={e["key"]: e for e in rows["events"] if e["review_id"] == batch["id"]},
        )
    for key in rows:
        rows[key].sort(key=lambda r: r.get("id", r.get("review_id", "")) + r.get("span_id", ""))
    rows["summary"] = dict(
        status="partial_reviewed_catalogue",
        review_batches=len(batches),
        inspected_source_lines=sum(map(len, inspected.values())),
        inspected_candidate_spans=len(decisions),
        source_assertions=len(rows["assertions"]),
        source_events=len(rows["events"]),
        assertion_quantities=dict(
            sorted(Counter(a["quantity"] for a in rows["assertions"]).items())
        ),
        assertion_roles=dict(sorted(Counter(a["role"] for a in rows["assertions"]).items())),
        normalization_statuses=dict(
            sorted(Counter(a["normalized"]["status"] for a in rows["assertions"]).items())
        ),
        measurement_count=None,
    )
    return rows


def public_preview(catalogue):
    """Explicit whitelist: no excerpts, private line/path locators or production notes."""
    fields = (
        "id",
        "volume",
        "printed_page",
        "quantity",
        "role",
        "subject",
        "reference",
        "direction",
        "normalized",
        "flags",
        "event_id",
        "context_ids",
        "record_status",
        "variant_of_id",
        "series_id",
        "ordinal",
        "ordinal_original",
    )
    return dict(
        status="reviewed_subset_preview_not_full_release",
        summary=catalogue["summary"],
        assertions=[{key: a.get(key) for key in fields} for a in catalogue["assertions"]],
    )


def build_workspace(source_root, workspace):
    """Build only reviewed catalogue tables inside an existing inventory workspace."""
    from .io import guard, write_json, write_csv
    from .core import digest
    from .publication import read_witness

    source_root = Path(source_root).resolve()
    workspace = Path(workspace).resolve()
    guard(workspace, source_root)
    if (workspace / "pafko.json").exists() or (workspace / "raw" / "mars.xls").exists():
        raise ValueError("Catalogue output must not replace the protected benchmark workspace")
    files = ("witnesses.json", "inventory_spans.jsonl", "review_batches.json")
    if (workspace / "source_binding_reviews.json").is_file():
        files += ("source_binding_reviews.json",)
    input_hashes = {name: digest(workspace / name) for name in files}
    witnesses = json.loads((workspace / "witnesses.json").read_text(encoding="utf-8"))
    texts = {}
    hashes = {}
    for witness in witnesses:
        volume = witness["volume"]
        v = volume - 9
        relative = f"brahe/thesaurus_observationum_vol{v}/translation/brahe_thesaurus_observationum_vol{v}_prepub.md"
        if witness["private_source"] != relative:
            raise ValueError("Unrecognized canonical source location")
        path = source_root / relative
        texts[volume] = read_witness(source_root, workspace, witness)
        hashes[relative] = hashlib.sha256(texts[volume].encode()).hexdigest()
    extra = workspace / "source_hashes.json"
    if extra.exists():
        for relative, sha in json.loads(extra.read_text(encoding="utf-8")).items():
            path = (source_root / relative).resolve()
            if not path.is_relative_to(source_root):
                raise ValueError("Source hash path outside library")
            if digest(path) != sha:
                raise ValueError("Screening source fingerprint changed")
            hashes[relative] = sha
    spans = [
        json.loads(s)
        for s in (workspace / "inventory_spans.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    catalogue = compile_catalogue(
        json.loads((workspace / "review_batches.json").read_text(encoding="utf-8")),
        texts,
        spans,
        edition_hashes={w["volume"]: w["edition_sha256"] for w in witnesses},
        source_bindings=load_bindings(workspace),
    )
    if any(digest(source_root / relative) != sha for relative, sha in hashes.items()):
        raise ValueError("Source changed during catalogue compilation")
    if any(digest(workspace / name) != sha for name, sha in input_hashes.items()):
        raise ValueError("Review inputs changed during catalogue compilation")
    output_hashes = {}
    for name in ("assertions", "contexts", "events", "derivations", "span_reviews", "coverage"):
        path = workspace / (name + ".jsonl")
        path.write_text(
            "".join(
                json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
                for row in catalogue[name]
            ),
            encoding="utf-8",
        )
        output_hashes[path.name] = digest(path)
        csv_path = workspace / (name + ".csv")
        write_csv(csv_path, catalogue[name])
        output_hashes[csv_path.name] = digest(csv_path)
    write_json(workspace / "public_catalogue_preview.json", public_preview(catalogue))
    output_hashes["public_catalogue_preview.json"] = digest(
        workspace / "public_catalogue_preview.json"
    )
    manifest = dict(
        schema_version=1,
        status="partial_reviewed_catalogue",
        source_hashes=hashes,
        input_hashes=input_hashes,
        output_hashes=output_hashes,
        source_inputs_unchanged=True,
        summary=catalogue["summary"],
    )
    write_json(workspace / "catalogue_manifest.json", manifest)
    return catalogue


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
    print(json.dumps(build_workspace(args.source_root, args.workspace)["summary"]))
