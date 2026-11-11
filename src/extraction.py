"""Extract readings using the translation's own table and passage context."""

import re

from .core import MONTHS, angle, fraction_text, hemisphere, time_key


MARS = re.compile(r"\b(?:Mars|Martis|Martem)\b|♂", re.I)
OTHER_PLANET = re.compile(r"\b(?:Jupiter|Venus|Mercury|Saturn|Moon|Sun)\b|[♃♀☿♄☾☉⊙]", re.I)
DECL = re.compile(r"decl", re.I)
LATIN_MONTHS = [
    "JANUARIJ",
    "FEBRUARIJ",
    "MARTIJ",
    "APRILIS",
    "MAIJ",
    "JUNIJ",
    "JULIJ",
    "AUGUSTI",
    "SEPTEMBRIS",
    "OCTOBRIS",
    "NOUEMBRIS",
    "DECEMBRIS",
]
DERIVED = re.compile(
    r"\b(?:calculation|computation|investigation|repetition of the calculation|true declination|corrected declination)\b|\b(?:Calculus|Supputatio|Inueſtigatio)\b",
    re.I,
)


def clean(text):
    return text.replace("*", "").strip()


def magnitude(text):
    text = re.split(r"\.\s+Altitude\b", text, maxsplit=1, flags=re.I)[0]
    # A bracketed transcription is redundant only when every numeric component
    # agrees. Disputed variants remain unresolved rather than being discarded.
    brackets = re.findall(r"\[([^\]]*)\]", text)
    if brackets:
        outside = re.sub(r"\[[^\]]*\]", "", text)
        token = r"\d+(?:\s+\d+/\d+|/\d+)?"
        numbers = re.findall(token, fraction_text(outside))
        if all(
            not re.search(r"\d", b) or re.findall(token, fraction_text(b)) == numbers
            for b in brackets
        ):
            text = outside
    value = angle(text)
    if value is not None or "?" in text:
        return value
    # Bare figures are accepted only after a declination column/label establishes units.
    bare = fraction_text(text).strip("{} \t\n")
    bare = re.sub(r"\s*(?:B|M)\.?\s*$", "", bare, flags=re.I)
    bare = re.sub(
        r"\s+(?:with one|with both|with the other)(?: pinnule)?(?:\s*\[[^\]]*\])?\s*$",
        "",
        bare,
        flags=re.I,
    )
    m = re.fullmatch(r"(\d+)\s+(\d+(?:\s+\d+/\d+)?)(?:\s+(\d+))?", bare)
    if not m:
        return None
    return angle(f"{m[1]}° {m[2]}′ " + (f"{m[3]}″" if m[3] else ""))


def clock_key(text, allow_bare=False):
    key = time_key(text)
    if key is None and re.match(r"^(?:At\s+)?H\.", clean(text), re.I):
        from .prose import clock

        key = clock(re.sub(r"\[[^\]]*\]", "", clean(text)))
    if key is not None or not allow_bare:
        return key
    original = clean(text).split(";")[0].split("[")[0].strip().lstrip("{").strip()
    original = re.split(
        r"\s+(?:Afterwards\s+)?(?:Mars|♂)\s+crossed\s+the\s+meridian\b", original, flags=re.I
    )[0].strip()
    m = re.fullmatch(
        r"(\d+)\s+(\d+(?:\s+\d+/\d+)?)(?:\s+(\d+))?(?:,?\s*(?:corrected|corr\.))?",
        fraction_text(original),
        re.I,
    )
    if not m or int(m[1]) > 24:
        return None
    return time_key(f"{m[1]}^h^ {m[2]}^m^ " + (f"{m[3]}^s^" if m[3] else ""))


def subject(label, fallback=None):
    # Only use the English label before its verbatim Latin bracket.
    english = clean(label).split("[")[0]
    if MARS.search(english):
        return "Mars"
    if OTHER_PLANET.search(english) or re.search(
        r"\b(?:Spica|Aldebaran|star|Regulus|Arcturus|Vulture)\b", english, re.I
    ):
        return "other"
    if re.search(r"declination\s+from\s+(?:the\s+)?(?:meridian\s+)?altitude", english, re.I):
        return fallback
    if re.search(r"(?:declination|decl\.)\s+(?:of|from)\s+\w+", english, re.I):
        return "other"
    return fallback


def extract_text(text, source, state):
    records, headers = [], None
    last_labels = {}
    table_target = None
    schema_basis = "current_table"
    printed_headers = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, 1):
        if "_line_provenance" in state:
            meta = state["_line_provenance"].get(lineno, {})
            state["page"], state["pdf_page"] = meta.get("page"), meta.get("pdf_page")
            if meta.get("year"):
                state["year"] = meta["year"]
            if state.get("_date_parts") and state.get("year"):
                month, day = state["_date_parts"]
                state["date"] = f"{state['year']}-{month:02}-{day:02}"
        if re.match(
            r"^#{1,3}\s+(?:OBSERVATIONS OF (?:THE )?YEAR|ANNO|EX ANNO|OBSERUATIONES ANNI)\b",
            line,
            re.I,
        ):
            year = re.search(r"\b(15\d{2}|160[01])\b", line)
            if year:
                state["year"] = int(year[1])
        anchor = re.match(r"<!--\s*PDF p\.\s*(\d+)", line)
        if anchor:
            state["pdf_page"] = int(anchor[1])
            printed = re.search(r"printed p\.\s*(\d+)", line)
            state["page"] = int(printed[1]) if printed else None
            continue
        if line.startswith("[Running header:"):
            nums = [int(x) for x in re.findall(r"\b\d+\b", line)]
            years = [n for n in nums if 1560 <= n <= 1601]
            pages = [n for n in nums if n < 1000]
            if years:
                state["year"] = years[0]
            if pages:
                state["page"] = pages[0]
            continue
        if line.startswith("[QA:"):
            p = re.search(r"(?:PDF )?p\. (\d+)", line)
            if p and re.search(r"running head|opening|page number", line, re.I):
                state["pdf_page"] = int(p[1])
                printed = re.search(r'page number ["“](\d+)', line)
                if not printed:
                    printed = re.search(r'["“](\d+)["”]\s*\((?:right|left)\)', line)
                state["page"] = int(printed[1]) if printed else None
                year = re.search(r'["“]((?:15\d{2}|160[01]))["”]', line)
                if year:
                    state["year"] = int(year[1])
            continue
        if re.match(r"^#{1,3} Batch\b", line, re.I):
            continue
        if re.match(r"^#{1,3} (?:Structured|Coverage)", line, re.I):
            break
        date_line = re.sub(r"^(#{1,6}\s*)On the same day,\s*", r"\1", clean(line), flags=re.I)
        date = re.match(
            r"^(?:#{1,6}\s*)?(?:On\s+)?(\d{1,2}) (" + "|".join(MONTHS) + r")\b", date_line, re.I
        )
        latin = re.match(
            r"^(?:#{1,6}\s*)?\**DIE\s+(\d{1,2})\s+(" + "|".join(LATIN_MONTHS) + r")\b", line, re.I
        )
        if not latin and re.match(r"^(?:EA\s+)?NOCTE\b", date_line, re.I):
            latin = re.search(r"(\d{1,2})\s+(" + "|".join(LATIN_MONTHS) + r")\b", date_line, re.I)
        same_month = (
            re.match(
                r"^(?:#{1,6}\s*)?On this day,\s*(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?\b",
                clean(line),
                re.I,
            )
            if state.get("_date_parts")
            else None
        )
        if date or latin or same_month:
            day = int((date or latin or same_month)[1])
            month = (
                MONTHS.index(date[2].lower()) + 1
                if date
                else LATIN_MONTHS.index(latin[2].upper()) + 1
                if latin
                else state["_date_parts"][0]
            )
            state["_date_parts"] = (month, day)
            state["date"] = f"{state['year']}-{month:02}-{day:02}" if state.get("year") else None
            state["date_original"] = line
            for key in [
                "target",
                "mars_sign",
                "mars_sign_locus",
                "time",
                "time_locus",
                "time_key",
                "time_match_key",
                "role",
                "schema",
                "schema_page",
            ]:
                state.pop(key, None)
            if state.get("section_target"):
                state["target"] = state["section_target"]
            from .prose import clock

            heading_clock = clock(clean(line).split("[")[0])
            if heading_clock is not None:
                state["time_key"] = state["time_match_key"] = heading_clock
                state["time"], state["time_locus"] = line, f"{source}:{lineno}"
        elif line.startswith("#") and not re.match(
            r"^#+\s*(?:After noon|Before noon|The following morning|For.*\blatitude\b|On the same day\b|In the (?:evening|morning) of the same day\b)",
            clean(line),
            re.I,
        ):
            state.pop("date", None)
            state.pop("_date_parts", None)
            if MARS.search(line):
                state["target"] = state["section_target"] = "Mars"
            elif OTHER_PLANET.search(line) or re.search(r"fixed stars|STELLARUM", line, re.I):
                state["target"] = state["section_target"] = "other"
        if not line.startswith("|"):
            headers, table_target = None, None
            last_labels = {}
            if (
                not line.strip()
                or date
                or latin
                or same_month
                or (line.startswith("[") and not line.startswith("[At]"))
                or line.startswith(("<!--", "Parsing notes:", "^", "¹", "²", "³", "---", "    "))
            ):
                continue
            if DERIVED.match(clean(line)) or re.match(
                r"(?:#+\s*)?(?:For the place of Mars|Pro loco ♂|From this comes|Hence.*declination|Therefore.*declination|Investigation of the place|The meridian altitude gives|Reduction of the preceding|For.*\blatitude\b)",
                clean(line),
                re.I,
            ):
                if state.get("role") != "derived":
                    for key in ["time", "time_key", "time_match_key", "time_locus"]:
                        state.pop(key, None)
                state["role"] = "derived"
            elif re.search(r"(?:Mars was observed|observed Mars|Obſeruabatur ♂)", line, re.I):
                state["role"] = "observation"
            # Subject context may establish Mars, but comparison-star prose must not supply a sign.
            if re.search(
                r"For the places of the fixed|^To test the armillae|^To test the quadrants|^For correcting the armillae",
                clean(line),
                re.I,
            ):
                state["target"] = "other"
            elif MARS.search(line) and not OTHER_PLANET.search(line):
                state["target"] = "Mars"
            elif re.search(
                r"(?:declination of|observed) (?:Aldebaran|Spica|Jupiter|Venus|Mercury|Saturn)",
                line,
                re.I,
            ):
                state["target"] = "other"
            from .prose import readings, clock

            prose_readings = readings(line, state.get("target") == "Mars")
            clock_prefix = (
                prose_readings[0]["time_original"]
                if prose_readings
                else re.sub(r"\[[^\]]*\]", "", line)
            )
            prose_clock = clock(clock_prefix)
            if prose_clock is not None:
                state["time_key"] = state["time_match_key"] = prose_clock
                state["time"], state["time_locus"] = line, f"{source}:{lineno}"
            for occurrence, reading in enumerate(prose_readings, 1):
                if magnitude(reading["value"]) is None:
                    continue
                child = {k: v for k, v in state.items() if k != "_line_provenance"}
                if reading["time_key"] is not None:
                    child["time_key"] = child["time_match_key"] = reading["time_key"]
                    child["time"] = reading["time_original"]
                synthetic = (
                    "| | " + reading["label"] + " |\n|---|---|\n| | " + reading["value"] + " |"
                )
                for rec in extract_text(synthetic, source, child):
                    rec.update(
                        id=f"{source}:{lineno}:prose{occurrence}",
                        line=lineno,
                        column=None,
                        row_original=line,
                        extraction_basis="explicit_prose_clause",
                        input_edition="prepub" if "_line_provenance" in state else "batch",
                        provenance_source=meta.get("provenance_source")
                        if "_line_provenance" in state
                        else source,
                        provenance_line=meta.get("provenance_line")
                        if "_line_provenance" in state
                        else lineno,
                        provenance_basis=meta.get("provenance_basis")
                        if "_line_provenance" in state
                        else "direct_batch",
                    )
                    if rec.get("hemisphere_basis") == "explicit_label_or_value":
                        rec["hemisphere_locus"] = f"{source}:{lineno}"
                        if rec.get("target") == "Mars" and rec.get("role") == "observation":
                            sign = hemisphere(reading["label"]) or hemisphere(reading["value"])
                            if sign:
                                state["mars_sign"], state["mars_sign_locus"] = (
                                    sign,
                                    f"{source}:{lineno}",
                                )
                    records.append(rec)
            continue
        cells = [clean(c) for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r"[-: ]+", c) for c in cells):
            continue
        if headers is None:
            printed_headers = cells
            inherited = (
                not any(cells)
                and state.get("schema")
                and len(state["schema"]) == len(cells)
                and state.get("role") != "derived"
            )
            headers = list(state["schema"]) if inherited else list(cells)
            schema_basis = (
                (
                    "previous_page_same_date"
                    if state.get("schema_page") != state.get("pdf_page")
                    else "same_date_table_continuation"
                )
                if inherited
                else "current_table"
            )
            table_target = "Mars" if any(MARS.search(h) for h in headers) else state.get("target")
            # A declination explicitly assigned to another object overrides a Mars distance header.
            if any(MARS.search(h) for h in headers):
                state["target"] = "Mars"
            if (
                any(re.search(r"Time|Hours|clock", h, re.I) for h in headers)
                and table_target == "Mars"
                and any(DECL.search(h) for h in headers)
            ):
                state["role"] = "observation"
                state["schema"], state["schema_page"] = headers, state.get("pdf_page")
            continue
        if len(cells) != len(headers):
            continue
        # Unit-tagged time is unambiguous even under a blank header.
        row_clock = False
        for i, cell in enumerate(cells):
            key = clock_key(cell, allow_bare=(i == 0 and len(headers) >= 3))
            if key is not None and (i == 0 or re.search(r"Time|Hours|clock", headers[i], re.I)):
                previous_key = state.get("time_key")
                correction = re.search(r"corrected\s+(.*)", cell, re.I)
                correction_key = clock_key(correction[1], True) if correction else None
                if correction_key:
                    state["time_match_key"] = correction_key
                else:
                    state["time_match_key"] = (
                        previous_key
                        if re.search(r"corrected|corr\.", cell, re.I) and previous_key
                        else key
                    )
                state["time_key"] = key
                state["time"], state["time_locus"] = cell, f"{source}:{lineno}:{i + 1}"
                row_clock = True
                break
        vertical = (
            any(h.lower() == "value" for h in headers)
            or not any(headers)
            or (
                any(h.lower() in ("reading", "line") for h in headers)
                and not any(DECL.search(h) for h in headers)
            )
        )
        candidates = []
        if vertical:
            # Some transit blocks put label/value in columns 1/2 and a star reading in 3.
            labels = [i for i, c in enumerate(cells[:-1]) if DECL.search(c)]
            if labels:
                for li in labels:
                    label = cells[li]
                    if magnitude(label) is not None:
                        candidates.append((li, label, False))
                        last_labels[li] = label
                        continue
                    assigned = False
                    for vi in range(li + 1, len(cells)):
                        if magnitude(cells[vi]) is not None:
                            candidates.append((vi, label, False))
                            last_labels[vi] = label
                            assigned = True
                            break
                    if not assigned:
                        # A label-only row can scope subsequent pinnule/value rows.
                        following = [
                            vi for vi in range(li + 1, len(cells)) if headers[vi].lower() == "value"
                        ]
                        last_labels[following[0] if following else li + 1] = label
            else:
                inline = [i for i in last_labels if headers[i].lower() in ("reading", "line")]
                for i in inline:
                    if magnitude(cells[i]) is not None:
                        candidates.append((i, last_labels[i], False))
                    elif cells[i]:
                        last_labels.pop(i, None)
                value_columns = sorted(
                    set(i for i, h in enumerate(headers) if h.lower() == "value")
                    | set(i for i in last_labels if i not in inline)
                ) or [len(cells) - 1]
                for vi in value_columns:
                    reading_columns = [
                        i for i in range(vi) if headers[i].lower() in ("reading", "line")
                    ]
                    label = (
                        cells[reading_columns[-1]]
                        if reading_columns
                        else cells[vi - 1]
                        if any(headers) and vi > 0
                        else next(
                            (
                                c
                                for c in cells[:vi]
                                if re.search(r"[A-Za-z]{2}", c)
                                and (
                                    clock_key(c, True) is None
                                    or re.search(r"Distance|Altitude|ascension", c, re.I)
                                )
                            ),
                            "",
                        )
                    )
                    wrapped = clean(label).split("[")[0].strip()
                    if DECL.search(last_labels.get(vi, "")) and (
                        wrapped.lower().startswith("of ")
                        or re.fullmatch(r"♂\s*(?:B\.?|M\.?)?", wrapped, re.I)
                    ):
                        last_labels[vi] += " " + label
                    elif label and not re.search(
                        r"other pinnule|altero|alt\. pin|with (?:the )?(?:other|one|both)|^Repeated\b|^Repetita\b",
                        label,
                        re.I,
                    ):
                        last_labels[vi] = label
                    if DECL.search(last_labels.get(vi, "")):
                        candidates.append((vi, last_labels[vi], False))
        else:
            decl_columns = [i for i, h in enumerate(headers) if DECL.search(h)]
            # A new timed distance row resumes the table's nominal planetary columns.
            if row_clock:
                for vi in decl_columns:
                    if any(magnitude(cells[j]) is not None for j in range(1, vi)):
                        last_labels.pop(vi, None)
            inline_columns = set()
            for i, cell in enumerate(cells):
                if DECL.search(cell):
                    label = cell
                    if lineno < len(lines) and lines[lineno].startswith("|"):
                        following = [clean(c) for c in lines[lineno].strip().strip("|").split("|")]
                        if len(following) == len(cells) and re.match(r"^of\s+", following[i], re.I):
                            label += " " + following[i]
                    if magnitude(cell) is not None:
                        candidates.append((i, label, False))
                        inline_columns.add(i)
                        last_labels[i] = label
                    else:
                        following_columns = [j for j in decl_columns if j >= i]
                        values = [
                            j
                            for j in range(i + 1, len(cells))
                            if magnitude(cells[j]) is not None
                            and (
                                not headers[j]
                                or re.search(
                                    r"Decl|Distance|Altitude|Azimuth|Value", headers[j], re.I
                                )
                            )
                        ]
                        nominal_values = [j for j in following_columns if j in values]
                        vi = (
                            nominal_values[0]
                            if nominal_values
                            else values[0]
                            if values
                            else following_columns[0]
                            if following_columns
                            else i
                        )
                        last_labels[vi] = label
                        if values and vi not in following_columns:
                            headers[vi] = label
                elif (
                    re.search(
                        r"\b(?:Azimuth|Altitude|Distance|Right ascension|Between|Inter)\b",
                        cell,
                        re.I,
                    )
                    and magnitude(cell) is None
                ):
                    if DECL.search(headers[i]) or not headers[i]:
                        headers[i] = cell
                        if state.get("schema") and len(state["schema"]) == len(headers):
                            state["schema"] = list(headers)
                        last_labels.pop(i, None)
                    if re.search(r"\bAltitude\b", cell, re.I) and not row_clock:
                        for vi in decl_columns:
                            if i < vi:
                                last_labels[vi] = cell
                    elif re.search(r"\bDistance\b", cell, re.I):
                        for vi in decl_columns:
                            if i < vi:
                                last_labels.pop(vi, None)
            for i, label in list(last_labels.items()):
                if i in inline_columns:
                    continue
                if not headers[i] and DECL.search(label) and magnitude(cells[i]) is not None:
                    candidates.append((i, label, False))
                    inline_columns.add(i)
            for i, h in enumerate(headers):
                if i in inline_columns:
                    continue
                label = last_labels.get(i, h)
                if not DECL.search(h) or not DECL.search(label):
                    continue
                candidates.append((i, label, False))
                if (
                    i + 1 < len(headers)
                    and not headers[i + 1]
                    and magnitude(cells[i + 1]) is not None
                ):
                    candidates.append((i + 1, label, True))
        reviewed_columns = set()
        existing_columns = {i for i, _, _ in candidates}
        for i in range(len(cells)):
            if i not in existing_columns and f"{source}:{lineno}:{i + 1}" in state.get(
                "_include_record_ids", set()
            ):
                candidates.append((i, "Declination (source-bound column review)", False))
                reviewed_columns.add(i)
        for i, label, parallel in candidates:
            target = subject(label, table_target or state.get("target"))
            record_id = f"{source}:{lineno}:{i + 1}"
            if target != "Mars" and record_id not in state.get("_include_record_ids", set()):
                continue
            raw = cells[i]
            if not raw or not re.search(r"\d", raw):
                continue
            # Label-like material inside a declination column changes the quantity/target.
            if re.match(r"^(?:Altitude|Distance|Right ascension)\b", raw, re.I) and not DECL.search(
                raw
            ):
                continue
            val = magnitude(raw)
            direct_sign = hemisphere(label) or hemisphere(raw)
            sign = direct_sign or (state.get("mars_sign") if target == "Mars" else None)
            sign_basis = (
                "explicit_label_or_value" if direct_sign else "same_date_context" if sign else None
            )
            role = (
                "derived"
                if DERIVED.search(label) or state.get("role") == "derived"
                else "observation"
            )
            if direct_sign and role == "observation" and target == "Mars":
                state["mars_sign"], state["mars_sign_locus"] = (
                    direct_sign,
                    f"{source}:{lineno}:{i + 1}",
                )
            flags = []
            if parallel:
                flags.append("column_role_unresolved")
            if sign is None:
                flags.append("hemisphere_unresolved")
            if val is None:
                flags.append("value_unresolved")
            if role == "derived":
                flags.append("derived_or_editorial")
            if "?" in raw:
                flags.append("source_uncertainty")
            records.append(
                dict(
                    id=f"{source}:{lineno}:{i + 1}",
                    source=source,
                    line=lineno,
                    column=i + 1,
                    volume=state.get("volume", 12),
                    page=state.get("page"),
                    pdf_page=state.get("pdf_page"),
                    date=state.get("date"),
                    date_original=state.get("date_original"),
                    time_original=state.get("time", ""),
                    time_key=state.get("time_key"),
                    time_match_key=state.get("time_match_key"),
                    time_locus=state.get("time_locus"),
                    label=label,
                    value_original=raw,
                    magnitude_arcsec=str(val) if val is not None else None,
                    arcsec=str(val * sign) if val is not None and sign else None,
                    hemisphere_basis=sign_basis,
                    hemisphere_locus=f"{source}:{lineno}:{i + 1}"
                    if direct_sign
                    else state.get("mars_sign_locus"),
                    target=target,
                    target_basis="explicit_label"
                    if MARS.search(label)
                    else "passage_or_table_context",
                    measurement_type="declination",
                    role=role,
                    flags=flags,
                    row_original=line,
                    headers_original=printed_headers,
                    schema_basis=schema_basis,
                    input_edition="prepub" if "_line_provenance" in state else "batch",
                    provenance_basis=meta.get("provenance_basis")
                    if "_line_provenance" in state
                    else "direct_batch",
                    provenance_source=meta.get("provenance_source")
                    if "_line_provenance" in state
                    else source,
                    provenance_line=meta.get("provenance_line")
                    if "_line_provenance" in state
                    else lineno,
                )
            )
            if i in reviewed_columns:
                records[-1]["extraction_basis"] = "source_bound_review_column"
    return records
