import hashlib
import re
import unicodedata
from collections import defaultdict
from fractions import Fraction
from functools import lru_cache


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def angular_place_marks(text):
    """Preserve explicit superscript fifth–eighth places before NFKC erases them."""
    places = {"ᵛ": "″″′", "ᵛⁱ": "″″″", "ᵛⁱⁱ": "″″″′", "ᵛⁱⁱⁱ": "″″″″"}
    return re.sub(r"ᵛⁱ{0,3}", lambda match: places[match[0]], text)


@lru_cache(maxsize=8192)
def fraction_text(text):
    # Unicode decomposition exposes numerator/denominator without losing mixed fractions.
    text = re.sub(r"(?<=\d)(?=[⁰¹²³⁴⁵⁶⁷⁸⁹])", " ", text)
    for ch in set(text):
        if unicodedata.category(ch) == "No" and "FRACTION" in unicodedata.name(ch, ""):
            text = text.replace(
                ch, " " + str(Fraction(unicodedata.numeric(ch)).limit_denominator(60))
            )
    text = unicodedata.normalize("NFKC", text).replace("⁄", "/").replace("′′", "″")
    return text


@lru_cache(maxsize=8192)
def number(text):
    parts = text.strip().split()
    return sum((Fraction(p) for p in parts), Fraction())


def angle(text):
    """Unsigned arcseconds, exact; unknown/unsupported notation stays unknown."""
    if "?" in text:
        return None
    text = fraction_text(text)
    m = re.search(
        r"(?<![\d/])(\d+(?:\s+\d+/\d+|/\d+)?)\s*°\s*(\d+(?:\s+\d+/\d+|/\d+)?)\s*[′\'](?:\s*(\d+(?:\s+\d+/\d+|/\d+)?)\s*[″\"])?",
        text,
    )
    if not m:
        return None
    if re.search(r"[0-9/°′″]", text[: m.start()] + text[m.end() :]):
        return None
    d, minute = number(m[1]), number(m[2])
    sec = number(m[3]) if m.lastindex == 3 and m[3] else Fraction()
    if minute >= 60 or sec >= 60:
        return None
    return d * 3600 + minute * 60 + sec


def time_key(text):
    text = fraction_text(text)
    m = re.search(
        r"(\d+(?:\s+\d+/\d+|/\d+)?)\^h\^(?:\s*(\d+(?:\s+\d+/\d+|/\d+)?)\^m\^)?(?:\s*(\d+(?:\s+\d+/\d+|/\d+)?)\^s\^)?",
        text,
        re.I,
    )
    if not m:
        return None
    if re.search(r"[0-9/°′″]", text[: m.start()] + text[m.end() :]):
        return None
    return str(number(m[1]) * 3600 + number(m[2] or "0") * 60 + number(m[3] or "0"))


def recorded_clock(text):
    """Literal wall-clock reading; AM/PM text is retained by the caller, not converted."""
    if len(re.findall(r"\bH\.", text, re.I)) != 1:
        return None
    raw = fraction_text(text).strip()
    raw = re.sub(r"\s*(?:[AP]\.\s*M\.(?:\s*N\.)?|corr\.)\s*$", "", raw, flags=re.I).strip()
    token = r"(\d+(?:\s+\d+/\d+|/\d+)?)"
    m = re.fullmatch(
        r"H\.\s*" + token + r"(?:\s*M\.\s*" + token + r")?(?:\s*S\.\s*" + token + r")?", raw, re.I
    )
    if m:
        h, minute, sec = m[1], m[2], m[3]
    else:
        m = re.fullmatch(
            r"H\.\s*" + token + r"(?:\s+" + token + r")?(?:\s+" + token + r")?", raw, re.I
        )
        if not m:
            m = re.fullmatch(
                r"H\.\s*" + token + r"\." + token + r"(?:\." + token + r")?", raw, re.I
            )
        if not m:
            return None
        h, minute, sec = m[1], m[2], m[3]
    hh, mm, ss = number(h), number(minute or "0"), number(sec or "0")
    if hh >= 24 or mm >= 60 or ss >= 60:
        return None
    return str(hh * 3600 + mm * 60 + ss)


def quote_angle(text):
    """Best-effort unsigned declination from Pafko's quotation, never its numeric cells."""
    if "?" in text:
        return None
    parts = re.split(r"\bDecl(?:inatio|in|ination)?\.?", text, flags=re.I)
    tail = parts[-1] if len(parts) > 1 else text
    # A separately labelled right ascension is not part of the declination.
    tail = re.split(r"\bet\s+A[fs]cen[fs]io\s+Recta\b", tail, maxsplit=1, flags=re.I)[0]
    repeated = re.fullmatch(r"\s*\[MS\]\s+I\s+(.+?)\s+II\s+(.+?)\s*", tail)
    if repeated:
        first, second = quote_angle(repeated[1]), quote_angle(repeated[2])
        return first if first is not None and first == second else None
    tail = fraction_text(tail)
    tail = re.sub(r"(\d+)\s*(?:grad\.|[go])\s*", r"\1 ", tail, flags=re.I)
    m = re.search(r"(\d+)\s*[o°]?\s+(\d+(?:\s+\d+/\d+|/\d+)?)(?:\s*[\'′]?\s+(\d+)(?!\s*/))?", tail)
    if not m:
        return None
    if re.search(r"[0-9/°′″]", tail[: m.start()] + tail[m.end() :]):
        return None
    minute = number(m[2])
    sec = Fraction(m[3] or "0")
    if minute >= 60 or sec >= 60:
        return None
    return Fraction(m[1]) * 3600 + minute * 60 + sec


MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


def hemisphere(label):
    # Meridian-altitude abbreviations describe the reduction, not its hemisphere.
    label = re.sub(r"\b(?:ex\s+alt\.?|(?:the\s+)?altitude)\s*(?:m|merid)\.", "", label, flags=re.I)
    if re.search(r"\bsouth(?:ern)?\b|\bmeridional|\b(?:M|Merid|aust|auſt|auft)\.", label, re.I):
        return -1
    if re.search(r"\bnorth(?:ern)?\b|\bBor\.|\bB\.(?!\w)|\bB\s*$", label, re.I):
        return 1
    return None


def extract_text(text, source, state):
    from .extraction import extract_text as contextual_extract

    return contextual_extract(text, source, state)


def sample_records(rows, count):
    """Round-robin year strata, SHA256 order fixed by source record ID."""
    groups = defaultdict(list)
    for r in rows:
        if r.get("date"):
            groups[r["date"][:4]].append(r)
    for group in groups.values():
        group.sort(key=lambda r: hashlib.sha256(("mars-pilot-v1:" + r["id"]).encode()).hexdigest())
    chosen = []
    while len(chosen) < count and any(groups.values()):
        for year in sorted(groups):
            if groups[year] and len(chosen) < count:
                chosen.append(groups[year].pop(0))
    return chosen


def compare_records(pafko, extracted, review_links=None):
    from .comparison import compare_records as contextual_compare

    return contextual_compare(pafko, extracted, review_links)
