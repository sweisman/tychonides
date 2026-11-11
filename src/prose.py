"""Recognize explicit declination clauses in the final book's prose and lists."""

import re
from .core import fraction_text, time_key


def clock(text):
    tagged = time_key(text)
    if tagged is not None:
        return tagged
    m = re.search(
        r"\bH\.\s*(\d+(?:\s+\d+/\d+)?)(?:\s*(?:M\.|\.)?\s*(\d+(?:\s+\d+/\d+)?))?(?:\s*S\.\s*(\d+(?:\s+\d+/\d+)?))?",
        fraction_text(text),
    )
    if not m:
        m = re.match(
            r"\s*At\s+(\d+)\s+(\d+(?:\s+\d+/\d+)?)(?:\s+(\d+))?\s*[,;:]", fraction_text(text), re.I
        )
    if not m:
        return None
    return time_key(
        f"{m[1]}^h^ " + (f"{m[2]}^m^ " if m[2] else "") + (f"{m[3]}^s^" if m[3] else "")
    )


def readings(line, mars_context=False):
    english = re.sub(r"\[[^\]]*\]", "", line).replace("*", "").replace("`", "")
    pattern = r"\bdecl(?:ination|inatio|in)?\.?"
    if not mars_context and not re.search(r"♂|\bMars\b", english, re.I):
        return []
    matches = list(re.finditer(pattern, english, re.I))
    results = []
    for index, m in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(english)
        tail = english[m.end() : end]
        if re.match(r"\s+of\s+(?!Mars\b)[A-Za-z]", tail, re.I) or re.search(
            r"\b(?:Spica|Aldebaran|Jupiter|Venus|Mercury|Saturn|Moon|Sun)\b",
            tail.split(",")[0],
            re.I,
        ):
            continue
        value = re.search(r'\d[\d\s°′″\'"¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉⁄/]*', tail)
        if not value:
            continue
        prefix = (
            english[: m.start()] if index == 0 else english[matches[index - 1].end() : m.start()]
        )
        direction = re.search(r"\b(northern|southern|north|south)\s*$", english[: m.start()], re.I)
        label = (
            (direction[1] + " " if direction else "")
            + english[m.start() : m.end()]
            + tail[: value.start()]
        )
        suffix = re.match(r"\s*((?:Bor|B|M|Auſt|Aust)\.?|north|south)\b", tail[value.end() :], re.I)
        if suffix:
            label += " " + suffix[1]
        # Instrument orientation is not the planet's hemisphere.
        label = re.sub(r"\b(?:northern|southern) armillae\b", "armillae", label, flags=re.I)
        results.append(
            dict(
                label=label,
                value=value[0].strip(),
                time_key=clock(prefix),
                time_original=prefix.strip(),
            )
        )
        continuation = re.search(
            r';\s*(?:with (?:the )?other(?: pinnule)?|altero)\s*:\s*(\d[\d\s°′″\'"¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞⁄/]*)',
            tail,
            re.I,
        )
        if continuation:
            results.append(
                dict(
                    label=label + " with the other pinnule",
                    value=continuation[1].strip(),
                    time_key=clock(prefix),
                    time_original=prefix.strip(),
                )
            )
    return results
