"""Conservative Mars source screening; candidate spans are not measurements."""

import bisect
import hashlib
import re
import unicodedata
from collections import defaultdict


MARS = re.compile(r"♂|\bMar(?:s|tis|tem|ti|te|tian)\b", re.I)
OTHERS = re.compile(
    r"[♃♄♀☿☉⊙☽☾]|\b(?:Jupiter|Iovis|Jove|Saturn\w*|Venus|Veneris|Mercur\w*|Sun|Solis|Moon|Luna\w*)\b",
    re.I,
)
DATE = re.compile(
    r"^(?:DIE\b|NOCTE\b|EA NOCTE\b|(?:On\s+)?\d{1,2}\s+\w+|(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day\b|On the same day\b|In the (?:evening|morning) of the same day\b|After noon\b|Before noon\b|The following morning\b)",
    re.I,
)
QUANTITIES = {
    "declination": r"\bdecl",
    "right_ascension": r"right asc|recta|aſc\.\s*r\.",
    "ecliptic_longitude": r"\blongit",
    "ecliptic_latitude": r"\blatit",
    "angular_separation": r"\bdist|\bdiſt|\binter\b|\bbetween\b",
    "altitude": r"\baltit|\balt\.",
    "azimuth": r"\bazim",
    "transit_or_hour_angle": r"meridian|\bmerid\b|\btransit|tranſ",
    "clock_or_correction": r"horolog|clock|\bcorr\.",
    "parallax": r"parallax|parallaxi",
    "refraction": r"refract|refractio",
}


def block_kind(line):
    if line.startswith("|"):
        return "table"
    if re.match(r"^\s*\*\*Diagram\.", line, re.I):
        return "diagram"
    if line.startswith(("[^", "[QA:", "[ed.:", "<!--")):
        return "annotation"
    if re.match(r"^#{1,6}\s", line) or re.fullmatch(r"\*\*.+?\*\*(?:\s*\[[^\]]*\])?\s*", line):
        return "heading"
    if re.match(r"^\s*(?:[-•]\s|\d+[.)]\s)", line):
        return "list"
    return "paragraph"


def blocks(lines):
    i = 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        start = i
        kind = block_kind(lines[i])
        i += 1
        if kind not in ("heading", "diagram"):
            while i < len(lines) and lines[i].strip() and block_kind(lines[i]) == kind:
                i += 1
        yield start + 1, i, kind, "\n".join(lines[start:i])


def plain(text):
    return re.sub(r"^[#*`\s]+", "", text).replace("*", "").replace("`", "").strip()


def mars_reference(text, heading=False):
    original = bool(MARS.search(text))
    cleaned = re.sub(r"\bDIE\s+MARTIS\b", "DIE", text, flags=re.I)
    cleaned = re.sub(r"\b(?:QUI ERAT|which was)\s*♂\.?", "", cleaned, flags=re.I)
    if heading and DATE.match(plain(text)) and not re.search(r"\bobser|\bMars\b", cleaned, re.I):
        cleaned = cleaned.replace("♂", "")
    explicit = bool(MARS.search(cleaned))
    return explicit, original and not explicit


def audit_screening(text, spans):
    """Check the full text for unselected explicit references, including long s.

    This is a lexical coverage check, not proof that every implicit reference or
    measurement has been recognized. It does not change the reviewed inventory.
    """
    lines = text.splitlines()
    covered = set()
    for span in spans:
        start, end = span["line_start"], span["line_end"]
        if not 1 <= start <= end <= len(lines):
            raise ValueError("Source span outside audited text")
        covered.update(range(start, end + 1))
    explicit = []
    weekday = []
    extended = []
    for start, end, kind, _body in blocks(lines):
        for n in range(start, end + 1):
            normalized = unicodedata.normalize("NFKC", lines[n - 1]).replace("ſ", "s")
            marked, day = mars_reference(normalized, kind == "heading")
            if marked:
                explicit.append(n)
                if not mars_reference(lines[n - 1], kind == "heading")[0]:
                    extended.append(n)
            if day:
                weekday.append(n)
    missing = sorted(set(explicit) - covered)
    return dict(
        screened_lines=len(lines),
        selected_source_lines=len(covered),
        explicit_reference_lines=len(explicit),
        weekday_only_lines=weekday,
        typographic_reference_lines=extended,
        unselected_reference_lines=missing,
        status="additional_reference_review_needed"
        if missing
        else "explicit_reference_screening_closed",
        limit="Lexical coverage does not prove completeness of implicit references or measurement extraction.",
    )


def validate_dated_source_companion(review, lines, intervals):
    """Bind a bounded chapter to an explicit earlier date and two named endpoints."""
    from .date_claims import MONTHS

    keys = (
        "scope_year_line",
        "parent_date_heading_line",
        "reference_parent_line",
        "scope_heading_line",
        "reference_anchor_line",
        "line_start",
        "line_end",
        "scope_end_line",
    )
    values = [review.get(k) for k in keys]
    if any(type(n) is not int for n in values):
        raise ValueError("Dated source reference lacks bound source lines")
    year_line, date_line, parent, heading, anchor, start, end, scope_end = values
    if (
        not 1
        <= year_line
        < date_line
        < parent
        < heading
        < anchor
        <= start
        <= end
        <= scope_end
        <= len(lines)
        or scope_end not in {b for _, b in intervals}
        or anchor not in {a for a, _ in intervals}
        or any(block_kind(lines[n - 1]) != "heading" for n in (year_line, date_line, heading))
        or any(block_kind(s) == "heading" for s in lines[date_line : parent - 1])
        or any(block_kind(s) == "heading" for s in lines[heading:scope_end])
    ):
        raise ValueError("Dated source reference crosses its parent date or bounded chapter")
    for key, sha_key in [
        ("scope_year_line", "scope_year_sha256"),
        ("parent_date_heading_line", "parent_date_heading_sha256"),
        ("scope_heading_line", "scope_heading_sha256"),
        ("reference_anchor_line", "reference_anchor_sha256"),
    ]:
        if hashlib.sha256(lines[review[key] - 1].encode()).hexdigest() != review.get(sha_key):
            raise ValueError("Stale dated source reference evidence")
    date = review.get("reference_date")
    phrase = review.get("reference_phrase")
    spoken = re.fullmatch(r"Above, on (\d{1,2}) ([A-Za-z]+)", phrase or "")
    recorded = re.fullmatch(
        r"DIE\s+(\d{1,2})\s+([A-Za-z]+)\.?", plain(lines[date_line - 1]).upper()
    )
    year_pattern = r"\b(?:ANNO|ANNUS|YEAR)\s+(\d{4})\b"
    year = re.search(year_pattern, lines[year_line - 1], re.I)
    if (
        not isinstance(date, dict)
        or set(date) != {"year", "month", "day"}
        or any(type(date.get(k)) is not int for k in date)
        or not spoken
        or not recorded
        or not year
        or not 1 <= date["month"] <= 12
        or not 1 <= date["day"] <= 31
        or int(year[1]) != date["year"]
        or int(spoken[1]) != date["day"]
        or int(recorded[1]) != date["day"]
        or MONTHS.get(spoken[2].upper()) != date["month"]
        or MONTHS.get(recorded[2]) != date["month"]
        or lines[anchor - 1].count(phrase) != 1
        or any(
            block_kind(s) == "heading" and re.search(year_pattern, s, re.I)
            for s in lines[year_line:scope_end]
        )
    ):
        raise ValueError("Dated source reference needs the same explicit year, month and day")
    pairs = review.get("endpoint_pairs")
    if not isinstance(pairs, list) or len(pairs) != 2:
        raise ValueError("Dated source reference requires two endpoint pairs")
    for pair in pairs:
        if (
            not isinstance(pair, dict)
            or set(pair) != {"object", "parent_expression", "anchor_expression"}
            or any(
                not isinstance(v, str) or len(v) < 4 or not re.search(r"[^\W\d_]", v)
                for v in pair.values()
            )
            or pair["parent_expression"] not in lines[parent - 1]
            or pair["anchor_expression"] not in lines[anchor - 1]
        ):
            raise ValueError(
                "Dated source reference requires literal named endpoints, not numerical agreement"
            )
    if any(
        len({p[k] for p in pairs}) != 2
        for k in ("object", "parent_expression", "anchor_expression")
    ):
        raise ValueError("Dated source reference endpoints must be distinct")


def validate_research_calibration(review, lines, intervals):
    """Select declared research support without asserting historical application."""
    heading, anchor, last = (
        review.get(k) for k in ("scope_heading_line", "calibration_anchor_line", "scope_end_line")
    )
    if (
        any(type(n) is not int for n in (heading, anchor, last))
        or not 1 <= heading < anchor <= last <= len(lines)
        or not heading <= review["line_start"] <= review["line_end"] <= last
        or last not in {b for _, b in intervals}
        or block_kind(lines[heading - 1]) != "heading"
        or not re.search(r"refra", lines[heading - 1], re.I)
        or any(block_kind(s) == "heading" for s in lines[heading:last])
        or not mars_reference(lines[review["reference_parent_line"] - 1])[0]
        or review.get("research_basis") != "shared_comparison_star"
        or review.get("historical_application_established") is not False
    ):
        raise ValueError(
            "Research calibration requires a bounded refraction scope and explicitly unestablished historical use"
        )
    for line, key in ((heading, "scope_heading_sha256"), (anchor, "calibration_anchor_sha256")):
        if hashlib.sha256(lines[line - 1].encode()).hexdigest() != review.get(key):
            raise ValueError("Stale research calibration evidence")
    name = review.get("shared_reference_name")
    for key, line in (
        ("parent_endpoint_literal", review["reference_parent_line"]),
        ("calibration_endpoint_literal", anchor),
    ):
        literal = review.get(key)
        if (
            not isinstance(name, str)
            or len(name) < 3
            or not re.search(r"[^\W\d_]", name)
            or not isinstance(literal, str)
            or name.casefold() not in literal.casefold()
            or literal not in lines[line - 1]
        ):
            raise ValueError(
                "Research calibration requires the named star at both bound source loci"
            )


def inventory_text(text, volume, edition_sha256, provenance=None, *, reference_reviews=()):
    provenance = provenance or {}
    lines = text.splitlines()
    spans = []
    pages = {}
    unmapped = 0
    candidate_lines = 0
    section = None
    section_level = None
    passage = False
    explicit_lines = 0
    weekday_lines = 0
    witness = f"tycho-oo-{volume}-prepub-{edition_sha256[:12]}"
    source_blocks = list(blocks(lines))
    intervals = {(a, b) for a, b, _, _ in source_blocks}
    references = {}
    review_ids = set()
    if not isinstance(reference_reviews, (list, tuple)):
        raise ValueError("Invalid reference review ledger")
    for review in reference_reviews:
        if not isinstance(review, dict):
            raise ValueError("Invalid reference review")
        start, end, parent = (
            review.get(k) for k in ("line_start", "line_end", "reference_parent_line")
        )
        marker = review.get("reference_marker")
        rid = review.get("id")
        if (
            not isinstance(rid, str)
            or not rid
            or rid in review_ids
            or review.get("volume") != volume
            or review.get("edition_sha256") != edition_sha256
            or any(type(n) is not int for n in (start, end, parent))
            or (start, end) not in intervals
            or (start, end) in references
            or not 1 <= parent <= len(lines)
            or start <= parent <= end
            or not review.get("reason")
            or hashlib.sha256("\n".join(lines[start - 1 : end]).encode()).hexdigest()
            != review.get("interval_sha256")
            or hashlib.sha256(lines[parent - 1].encode()).hexdigest()
            != review.get("parent_line_sha256")
        ):
            raise ValueError("Stale or unbound reference review")
        kind = review.get("reference_kind", "marked_note")
        if kind == "marked_note":
            parent_marker = review.get("reference_parent_marker", marker)

            def ordinal(value):
                if not isinstance(value, str):
                    return None
                if re.fullmatch(r"\^[0-9]+\^", value):
                    return int(value[1:-1])
                if re.fullmatch(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]+", value):
                    return int(value.translate(str.maketrans("¹²³⁴⁵⁶⁷⁸⁹⁰", "1234567890")))
                if re.fullmatch(r"\[\^(?:p[0-9]+-[0-9]+|ed[0-9]+)\]", value):
                    return value
                return None

            if (
                parent >= start
                or ordinal(marker) is None
                or ordinal(parent_marker) != ordinal(marker)
                or not lines[start - 1].lstrip().startswith(marker)
                or parent_marker not in lines[parent - 1]
                or (
                    marker.startswith("[^")
                    and not lines[start - 1].lstrip().startswith(marker + ":")
                )
            ):
                raise ValueError("Unbound marked note reference")
        elif kind == "following_context":
            phrase = review.get("reference_phrase")
            headings = [
                n for n in range(end + 1, parent + 1) if block_kind(lines[n - 1]) == "heading"
            ]
            comparison = review.get("comparison_heading_line")
            if comparison is not None:
                date = review.get("source_input_date_line")
                named = review.get("reference_parent_phrase")
                if (
                    type(comparison) is not int
                    or type(date) is not int
                    or not 1 <= date < start <= end < comparison < parent <= len(lines)
                    or headings != [comparison]
                    or not DATE.match(plain(lines[date - 1]))
                    or any(block_kind(s) == "heading" for s in lines[date:end])
                    or not re.search(
                        r"\b(?:differentiarum|differences)\b", plain(lines[comparison - 1]), re.I
                    )
                    or hashlib.sha256(lines[comparison - 1].encode()).hexdigest()
                    != review.get("comparison_heading_sha256")
                    or hashlib.sha256(lines[date - 1].encode()).hexdigest()
                    != review.get("source_input_date_sha256")
                    or not isinstance(named, str)
                    or len(named) < 4
                    or not re.search(r"[^\W\d_]", named)
                    or named not in lines[parent - 1]
                ):
                    raise ValueError(
                        "Instrument input requires a bound date, comparison heading and named endpoint"
                    )
            if (
                parent <= end
                or not isinstance(phrase, str)
                or not phrase
                or phrase not in "\n".join(lines[start - 1 : end])
                or (headings and comparison is None)
            ):
                raise ValueError("Following context crosses a heading or lacks its source phrase")
        elif kind == "preceding_context":
            phrase = review.get("reference_phrase")
            if (
                parent >= start
                or not isinstance(phrase, str)
                or not phrase
                or phrase not in "\n".join(lines[start - 1 : end])
                or any(block_kind(line) == "heading" for line in lines[parent : start - 1])
            ):
                raise ValueError("Preceding context crosses a heading or lacks its source phrase")
        elif kind == "report_back_reference":
            report = review.get("scope_start_line")
            heading = review.get("scope_heading_line")
            last = review.get("scope_end_line")
            phrase = review.get("reference_phrase")
            back = review.get("reference_parent_phrase")
            if (
                any(type(n) is not int for n in (report, heading, last))
                or not 1 <= report <= start <= end <= last < parent <= len(lines)
                or not report < heading <= last
                or last not in {b for _, b in intervals}
                or block_kind(lines[report - 1]) != "heading"
                or block_kind(lines[heading - 1]) != "heading"
                or not re.match(r"^ECLIPSIS\s+☽\s+ANNO\b", plain(lines[report - 1]), re.I)
                or "DE ECLIPSI ☽ ANTECEDENTE" not in plain(lines[heading - 1])
                or hashlib.sha256(lines[report - 1].encode()).hexdigest()
                != review.get("scope_start_sha256")
                or hashlib.sha256(lines[heading - 1].encode()).hexdigest()
                != review.get("scope_heading_sha256")
                or back != "as can be gathered from what precedes"
                or lines[parent - 1].count(back) != 1
                or not isinstance(phrase, str)
                or not phrase
                or phrase not in "\n".join(lines[start - 1 : end])
                or any(s.strip() for s in lines[last : parent - 1])
                or [n for n in range(report, parent) if block_kind(lines[n - 1]) == "heading"]
                != [report, heading]
            ):
                raise ValueError(
                    "Eclipse back-reference requires its bound report, explicit recap heading and immediate later Mars reference"
                )
        elif kind == "headed_continuation":
            heading = review.get("scope_heading_line")
            scope_end = review.get("scope_end_line")
            forward = review.get("reference_parent_phrase")
            phrase = review.get("reference_phrase")
            if (
                type(heading) is not int
                or type(scope_end) is not int
                or not 1 <= parent < heading < start <= end <= scope_end <= len(lines)
                or block_kind(lines[heading - 1]) != "heading"
                or hashlib.sha256(lines[heading - 1].encode()).hexdigest()
                != review.get("scope_heading_sha256")
                or forward != "as may be seen below"
                or forward not in lines[parent - 1]
                or not isinstance(phrase, str)
                or not phrase
                or phrase not in "\n".join(lines[start - 1 : end])
                or scope_end not in {b for _, b in intervals}
                or [
                    n
                    for n in range(parent + 1, scope_end + 1)
                    if block_kind(lines[n - 1]) == "heading"
                ]
                != [heading]
            ):
                raise ValueError(
                    "Headed continuation requires an explicit forward phrase and one bounded source heading"
                )
        elif kind == "report_continuation":
            report = review.get("scope_start_line")
            heading = review.get("scope_heading_line")
            phrase = review.get("scope_heading_phrase")
            body_phrase = review.get("reference_phrase")
            if (
                type(report) is not int
                or type(heading) is not int
                or not 1 <= report < parent < heading < start <= end <= len(lines)
                or review.get("scope_end_line") != end
                or block_kind(lines[report - 1]) != "heading"
                or block_kind(lines[heading - 1]) != "heading"
                or hashlib.sha256(lines[report - 1].encode()).hexdigest()
                != review.get("scope_start_sha256")
                or hashlib.sha256(lines[heading - 1].encode()).hexdigest()
                != review.get("scope_heading_sha256")
                or phrase not in ("EX PRÆDICTA OBSERUATIONE", "FROM THE PRECEDING OBSERVATION")
                or phrase not in lines[heading - 1]
                or not isinstance(body_phrase, str)
                or not body_phrase
                or body_phrase not in "\n".join(lines[start - 1 : end])
                or [n for n in range(parent + 1, end + 1) if block_kind(lines[n - 1]) == "heading"]
                != [heading]
            ):
                raise ValueError(
                    "Report continuation requires a bound report, its explicit backward-reference heading and one subsection"
                )
        elif kind == "column_context":
            heading = review.get("scope_heading_line")
            phrase = review.get("reference_phrase")
            if (
                type(heading) is not int
                or not 1 <= parent < heading < start <= end <= len(lines)
                or block_kind(lines[heading - 1]) != "heading"
                or not re.search(r"\b(?:left|right) column\s*$", lines[heading - 1], re.I)
                or hashlib.sha256(lines[heading - 1].encode()).hexdigest()
                != review.get("scope_heading_sha256")
                or phrase != "This observation was repeated"
                or phrase not in "\n".join(lines[start - 1 : end])
                or [n for n in range(parent + 1, end + 1) if block_kind(lines[n - 1]) == "heading"]
                != [heading]
            ):
                raise ValueError(
                    "Column context requires one bound column heading and an explicit repetition statement"
                )
        elif kind == "column_continuation":
            from .date_claims import MONTHS

            date_line = review.get("date_heading_line")
            heading = review.get("scope_heading_line")
            note = review.get("reference_note_line")
            phrase = review.get("reference_phrase")
            date = review.get("reference_date")
            if (
                any(type(n) is not int for n in (date_line, heading, note))
                or not 1 <= date_line < parent < heading < start <= end <= len(lines)
                or not 1 <= note <= len(lines)
                or any(block_kind(lines[n - 1]) != "heading" for n in (date_line, heading))
                or [
                    n
                    for n in range(date_line + 1, end + 1)
                    if block_kind(lines[n - 1]) == "heading"
                ]
                != [heading]
                or any(
                    hashlib.sha256(lines[review[k] - 1].encode()).hexdigest() != review.get(s)
                    for k, s in [
                        ("date_heading_line", "date_heading_sha256"),
                        ("scope_heading_line", "scope_heading_sha256"),
                        ("reference_note_line", "reference_note_sha256"),
                    ]
                )
                or not isinstance(marker, str)
                or not re.fullmatch(r"\[\^ed\d+\]", marker)
                or not re.match(r"^#{1,6}\s+(?:Left|Right) column\b", lines[heading - 1])
                or marker not in lines[heading - 1]
                or not lines[note - 1].startswith(marker + ":")
                or not isinstance(phrase, str)
                or phrase not in lines[note - 1]
            ):
                raise ValueError(
                    "Column continuation lacks a bound heading, note or uninterrupted date scope"
                )
            spoken = re.fullmatch(
                r"The entry for (\d{1,2}) ([A-Za-z]+) resumes at the top of this column\.", phrase
            )
            recorded = re.fullmatch(
                r"DIE\s+(\d{1,2})\s+([A-Za-z]+)\.?", plain(lines[date_line - 1]).upper()
            )
            if (
                not isinstance(date, dict)
                or set(date) != {"month", "day"}
                or any(type(n) is not int for n in date.values())
                or not spoken
                or not recorded
                or not 1 <= date["day"] <= 31
                or not 1 <= date["month"] <= 12
                or int(spoken[1]) != date["day"]
                or int(recorded[1]) != date["day"]
                or MONTHS.get(spoken[2].upper()) != date["month"]
                or MONTHS.get(recorded[2]) != date["month"]
            ):
                raise ValueError("Column continuation note and recorded date must agree explicitly")
        elif kind == "research_calibration":
            validate_research_calibration(review, lines, intervals)
        elif kind == "dated_source_companion":
            validate_dated_source_companion(review, lines, intervals)
        elif kind == "report_scope":
            scope_start = review.get("scope_start_line")
            scope_end = review.get("scope_end_line")
            phrase = review.get("reference_phrase")
            if (
                type(scope_start) is not int
                or type(scope_end) is not int
                or not 1 <= scope_start < parent < start <= end
                or scope_end != end
                or block_kind(lines[scope_start - 1]) != "heading"
                or hashlib.sha256(lines[scope_start - 1].encode()).hexdigest()
                != review.get("scope_start_sha256")
                or phrase not in ("All these observations", "Omnes hæ obſeruationes")
                or phrase not in "\n".join(lines[start - 1 : end])
            ):
                raise ValueError(
                    "Report scope requires a bound report heading, internal Mars parent and explicit closing scope statement"
                )
        else:
            raise ValueError("Unknown source reference kind")
        references[start, end] = review
        review_ids.add(rid)
    independent = (
        inventory_text(text, volume, edition_sha256, provenance)["spans"]
        if any(
            r.get("reference_kind")
            in (
                "following_context",
                "report_continuation",
                "report_back_reference",
                "research_calibration",
            )
            for r in reference_reviews
        )
        else None
    )
    for start, end, kind, body in source_blocks:
        is_heading = kind == "heading"
        is_date = is_heading and bool(DATE.match(plain(body)))
        explicit, weekday = mars_reference(body, is_heading)
        for lineno in range(start, end + 1):
            marked, day = mars_reference(lines[lineno - 1], is_heading)
            explicit_lines += bool(marked)
            weekday_lines += bool(day)
        if is_heading:
            level = len(re.match(r"^#+", body)[0]) if body.startswith("#") else 2
            if not is_date:
                if explicit:
                    section = "Mars"
                    section_level = level
                elif OTHERS.search(body):
                    section = "other"
                    section_level = level
                elif section_level is not None and level <= section_level:
                    section = None
                    section_level = None
            passage = False
        elif explicit:
            passage = True
        elif kind == "paragraph" and OTHERS.search(body):
            passage = False
        reasons = []
        if explicit:
            reasons.append("explicit_mars_reference")
        if section == "Mars":
            reasons.append("mars_section_context")
        if passage and not explicit:
            reasons.append("mars_passage_context")
        reference = references.get((start, end))
        parent_span = None
        if reference:
            parent = reference["reference_parent_line"]
            candidates = (
                independent
                if reference.get("reference_kind")
                in (
                    "following_context",
                    "report_continuation",
                    "report_back_reference",
                    "research_calibration",
                )
                and independent is not None
                else spans
            )
            parent_span = next(
                (
                    s
                    for s in candidates
                    if s["line_start"] <= parent <= s["line_end"]
                    and (
                        reference.get("reference_kind", "marked_note") == "marked_note"
                        or any(r != "reviewed_reference_scope" for r in s["selection_reasons"])
                    )
                ),
                None,
            )
            if parent_span is None:
                raise ValueError("Reference parent is not an independently selected Mars region")
            if not reasons:
                reasons.append(
                    "reviewed_research_calibration"
                    if reference.get("reference_kind") == "research_calibration"
                    else "reviewed_reference_scope"
                )
        selected = bool(reasons)
        loci = []
        missing = 0
        for lineno in range(start, end + 1):
            meta = provenance.get(lineno, {})
            page = meta.get("page")
            if page is None:
                unmapped += 1
                missing += 1
            else:
                loci.append(page)
                entry = pages.setdefault(
                    page,
                    dict(
                        printed_page=page,
                        first_line=lineno,
                        last_line=lineno,
                        machine_screened_nonblank_lines=0,
                        candidate_nonblank_lines=0,
                        inspection_status="unreviewed",
                    ),
                )
                entry["last_line"] = lineno
                entry["machine_screened_nonblank_lines"] += 1
                entry["candidate_nonblank_lines"] += selected
            candidate_lines += selected
        if not selected:
            continue
        identity = hashlib.sha256(f"{volume}|{edition_sha256}|{start}|{end}".encode()).hexdigest()[
            :20
        ]
        flags = []
        if missing:
            flags.append("page_provenance_incomplete")
        if len(set(loci)) > 1:
            flags.append("multiple_printed_pages")
        if weekday:
            flags.append("weekday_marker_present")
        spans.append(
            dict(
                id=f"span-v{volume}-{identity}",
                witness_id=witness,
                volume=volume,
                edition_sha256=edition_sha256,
                line_start=start,
                line_end=end,
                block_kind=kind,
                text_original=body,
                printed_pages=sorted(set(loci)),
                selection_reasons=reasons,
                section_subject=section,
                quantity_hints=[
                    name for name, pattern in QUANTITIES.items() if re.search(pattern, body, re.I)
                ],
                review_status="unreviewed",
                flags=flags,
            )
        )
        if reference and reasons == ["reviewed_reference_scope"]:
            spans[-1].update(
                source_reference_review_id=reference["id"],
                source_reference_parent_span_id=parent_span["id"],
            )
        if reference and reasons == ["reviewed_research_calibration"]:
            spans[-1].update(
                research_support_review_id=reference["id"],
                research_support_parent_span_id=parent_span["id"],
                historical_application_established=False,
            )
    coverage = dict(
        volume=volume,
        witness_id=witness,
        edition_sha256=edition_sha256,
        screened_lines=len(lines),
        nonblank_lines=sum(bool(line.strip()) for line in lines),
        candidate_nonblank_lines=candidate_lines,
        explicit_mars_reference_lines=explicit_lines,
        weekday_marker_lines=weekday_lines,
        candidate_spans=len(spans),
        reviewed_spans=0,
        unmapped_nonblank_lines=unmapped,
        pages=[pages[p] for p in sorted(pages)],
        status="machine_screened_not_inspected",
        measurement_count=None,
    )
    return dict(spans=spans, coverage=coverage)


def benchmark_links(spans, observations, outcomes):
    by_id = {r["id"]: r for r in observations}
    grouped = defaultdict(list)
    for span in spans:
        grouped[span["volume"]].append(span)
    indexes = {}
    for volume, group in grouped.items():
        ordered = sorted(group, key=lambda s: s["line_start"])
        indexes[volume] = ([s["line_start"] for s in ordered], ordered)
    result = []
    for row in outcomes:
        ids = row.get("candidate_ids", [])
        observation = by_id.get(ids[0]) if len(ids) == 1 else None
        span = None
        if observation:
            starts, ordered = indexes.get(observation["volume"], ([], []))
            position = bisect.bisect_right(starts, observation["line"]) - 1
            if position >= 0 and observation["line"] <= ordered[position]["line_end"]:
                span = ordered[position]
        result.append(
            dict(
                pafko_id=row["pafko_id"],
                source_record_id=observation["id"] if observation else None,
                span_id=span["id"] if span else None,
                coverage_status="covered"
                if span
                else "outside_selected_spans"
                if observation
                else "source_identity_missing",
            )
        )
    return result
