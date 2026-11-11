"""Strict row parser for a reviewed clock/separation/ordinal/altitude schema.

Callers must establish the column roles, endpoints and session context first.
This parser does not discover or approve those semantics.
"""

import re

from .catalog import normalize_quantity


def _quantity(field, units, quantity):
    match = re.search(r"\d", field)
    if not match:
        raise ValueError("Missing numeric field")
    expression = field[match.start() :].strip()
    tokens = expression.split()
    if not 1 <= len(tokens) <= len(units):
        raise ValueError("Unsupported numeric field")
    result = dict(
        source_expression=expression,
        components=dict(zip(units[: len(tokens)], tokens, strict=True)),
    )
    normalize_quantity(dict(result, quantity=quantity))
    return result


def parse_separation_row(text):
    body = re.sub(r"\[recte:.*?\]", "", text)
    body = re.sub(r"^\s*-\s*", "", body)
    fields = [s.strip() for s in body.split("—")]
    if len(fields) not in (3, 4):
        raise ValueError("Unsupported series row shape")
    roman = fields[2]
    if not re.fullmatch(r"[IVXLCDM]+", roman):
        raise ValueError("Missing source ordinal")
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    ordinal = sum(
        -values[c] if i + 1 < len(roman) and values[c] < values[roman[i + 1]] else values[c]
        for i, c in enumerate(roman)
    )
    return dict(
        clock=_quantity(fields[0], ("hour", "minute", "second"), "recorded_clock"),
        separation=_quantity(fields[1], ("degree", "arcminute", "arcsecond"), "angular_separation"),
        ordinal=ordinal,
        ordinal_original=roman,
        altitude=_quantity(fields[3], ("degree", "arcminute", "arcsecond"), "altitude")
        if len(fields) == 4
        else None,
    )
