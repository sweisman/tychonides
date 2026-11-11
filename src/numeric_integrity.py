"""Independent checks of printed units and mechanical source conversions."""

from datetime import datetime, timedelta, UTC
from fractions import Fraction
import re

from .core import angular_place_marks, fraction_text

NUMBER = r"\d+(?:\s+\d+/\d+|/\d+)?"
MARKS = {
    "°": "degree",
    "′": "arcminute",
    "'": "arcminute",
    "″": "arcsecond",
    '"': "arcsecond",
    "″′": "arcsexagesimal_third",
    "″″": "arcsexagesimal_fourth",
    "‴": "arcsexagesimal_third",
    "⁗": "arcsexagesimal_fourth",
    "″″′": "arcsexagesimal_fifth",
    "″″″": "arcsexagesimal_sixth",
    "″″″′": "arcsexagesimal_seventh",
    "″″″″": "arcsexagesimal_eighth",
    "″″″″′": "arcsexagesimal_ninth",
    "″″″″″": "arcsexagesimal_tenth",
    "^h^": "hour",
    "^m^": "minute",
    "^s^": "second",
    "^g^": "degree",
    "^d^": "day",
    "^iv^": "arcsexagesimal_fourth",
    "^v^": "arcsexagesimal_fifth",
    "^vi^": "arcsexagesimal_sixth",
    "^vii^": "arcsexagesimal_seventh",
    "degree": "degree",
    "degrees": "degree",
    "minute": "arcminute",
    "minutes": "arcminute",
    "second": "arcsecond",
    "seconds": "arcsecond",
    "hour": "hour",
    "hours": "hour",
}


def validate_units(
    expression,
    components,
    inherited=(),
    order=None,
    addends=None,
    quantity=None,
    source_context=None,
):
    """Bind explicit marks to the corresponding literal component, not just its digits."""
    if not components:
        return
    from .normalization import (
        TIME_QUANTITIES,
        ANGLE_QUANTITIES,
        SOURCE_MILE_UNITS,
        DAY_FRACTION_UNITS,
    )

    text = fraction_text(
        angular_place_marks(expression) if quantity in ANGLE_QUANTITIES else expression
    )
    tokens = list(re.finditer(NUMBER, text))
    word_units = r"degrees?|arcminutes?|arcseconds?|days?|hours?|minutes?|seconds?|thirds?"
    if quantity in SOURCE_MILE_UNITS:
        word_units += r"|(?:German\s+)?miles?"
    day_scale = quantity == "clock_elapsed_time" and (
        bool(set(DAY_FRACTION_UNITS) & set(components))
        or bool(re.search(r"\bof\s+(?:(?:a|the)\s+)?day\b", text, re.I))
    )
    prefix_words = bool(
        tokens and re.search(r"\b(" + word_units + r")\s*$", text[: tokens[0].start()], re.I)
    )
    standard = (
        "sign_count",
        "sexagena",
        "degree",
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
    )
    default_order = [u for u in standard if u in components] + [
        u for u in components if u not in standard
    ]
    units = [u for u in (order or default_order) if u in components and u not in inherited]
    expanded = [u for u in units for _ in (addends or {}).get(u, [components[u]])]
    if len(tokens) != len(expanded):
        raise ValueError("Explicit unit binding requires complete component correspondence")
    for token, unit in zip(tokens, expanded, strict=True):
        mark = re.match(
            r"\s*(″″″″″|″″″″′|″″″″|″″″′|″″″|″″′|″′|″″|‴|⁗|°|′|″|'|\"|\^(?:[hmsgd]|iv|vii|vi|v)\^)",
            text[token.end() :],
            re.I,
        )
        expected = MARKS[mark[1].lower()] if mark else None
        word_mark = None
        if mark is None and quantity in TIME_QUANTITIES | ANGLE_QUANTITIES | set(
            SOURCE_MILE_UNITS
        ) | {
            "distance_in_semidiameters",
            "source_sexagesimal_length",
            "eclipse_extent",
            "proportional_minutes",
        }:
            if prefix_words:
                word_mark = re.search(r"\b(" + word_units + r")\s*$", text[: token.start()], re.I)
            if word_mark is None:
                word_mark = re.match(
                    r"(?:st|nd|rd|th)?\s*(?:whole\s+)?(" + word_units + r")\b",
                    text[token.end() :],
                    re.I,
                )
            if word_mark:
                expected = {
                    "degree": "degree",
                    "arcminute": "arcminute",
                    "arcsecond": "arcsecond",
                    "hour": "hour",
                    "day": "day",
                    "minute": "arcminute",
                    "second": "arcsecond",
                    "third": "arcsexagesimal_third",
                    "mile": "mile",
                    "german mile": "mile",
                }[word_mark[1].lower().removesuffix("s")]
                if (
                    word_mark[1].lower().startswith("german")
                    and quantity != "distance_in_german_miles"
                ):
                    raise ValueError("Explicit German miles conflict with the native distance unit")
        if quantity in TIME_QUANTITIES and not day_scale:
            expected = {
                "arcminute": "minute",
                "arcsecond": "second",
                "arcsexagesimal_third": "time_third",
                "arcsexagesimal_fourth": "time_fourth",
                "arcsexagesimal_fifth": "time_fifth",
            }.get(expected, expected)
        if day_scale:
            expected = {
                "degree": "day",
                "arcminute": "day_minute",
                "arcsecond": "day_second",
                "arcsexagesimal_third": "day_third",
                "arcsexagesimal_fourth": "day_fourth",
                "arcsexagesimal_fifth": "day_fifth",
                "arcsexagesimal_sixth": "day_sixth",
            }.get(expected, expected)
        if mark and mark[1] in ("^M^", "^S^") and unit in ("arcminute", "arcsecond"):
            expected = {"^M^": "arcminute", "^S^": "arcsecond"}[mark[1]]
        if quantity == "proportional_minutes":
            expected = {
                "arcminute": "proportional_minute",
                "arcsecond": "proportional_second",
                "arcsexagesimal_third": "proportional_third",
            }.get(expected, expected)
        if quantity == "eclipse_extent":
            expected = (
                {"arcminute": "digit_minute", "arcsecond": "digit_second"}
                if {"digit", "digit_minute", "digit_second"} & set(components)
                else {"arcminute": "point_minute"}
            ).get(expected, expected)
        if quantity == "source_sexagesimal_length":
            expected = {
                "degree": "source_part",
                "arcminute": "part_minute",
                "arcsecond": "part_second",
            }.get(expected, expected)
        if quantity == "distance_in_semidiameters":
            expected = {"arcminute": "semidiameter_minute", "arcsecond": "semidiameter_second"}.get(
                expected, expected
            )
        if quantity in SOURCE_MILE_UNITS:
            expected = {"arcminute": "mile_minute", "arcsecond": "mile_second"}.get(
                expected, expected
            )
            if expected == "mile" and set(components) == {"scalar"}:
                expected = "scalar"
        if mark and quantity in ANGLE_QUANTITIES:
            if mark[1].lower() == "^m^":
                expected = "arcminute"
            if mark[1].lower() == "^s^":
                expected = (
                    "sign_count"
                    if "sign_count" in components
                    else "sexagena"
                    if "sexagena" in components
                    else "arcsecond"
                )
        if word_mark:
            explicit = word_mark[1].lower().removesuffix("s")
            if explicit in ("degree", "arcminute", "arcsecond"):
                # Unlike primes or bare "minutes", these words explicitly
                # identify angular units even inside a time/length expression.
                expected = explicit
        if (
            expected == "degree"
            and unit == "ordinal_degree"
            and quantity == "ecliptic_longitude"
            and word_mark is not None
            and re.match(r"(?:st|nd|rd|th)\s*degrees?\b", text[token.end() :], re.I)
        ):
            # This is a degree index; the compiler separately requires
            # source-bound evidence for its coordinate interpretation.
            expected = "ordinal_degree"
        if (mark or word_mark) and expected != unit:
            # A contradictory prime remains literal; only an explicit adjacent H.
            # heading can establish this first clock component as hours.
            if (
                quantity in TIME_QUANTITIES
                and unit == "hour"
                and token is tokens[0]
                and mark is not None
                and mark[1] == "′"
                and source_context is not None
                and source_context.count("H. " + expression) == 1
            ):
                continue
            label = mark[1] if mark else word_mark[1]
            raise ValueError("Components differ from explicit source unit: " + label)


def recompute_conversion(row):
    literal, unit = row["literal"], row.get("unit", row.get("normalized", {}).get("unit"))
    if "incomplete_coordinate" in row.get("flags", []):
        return None
    if unit in ("sexagesimal_degree", "sexagesimal_hour"):
        parts = re.sub(r"^([+-])\s+(?=\d)", r"\1", literal.strip()).split()
        if len(parts) != 3:
            return None
        if any(p.startswith(("-", "+")) for p in parts[1:]):
            raise ValueError("Only the first sexagesimal component may carry a sign")
        a, b, c = map(Fraction, parts)
        if not 0 <= b < 60 or not 0 <= c < 60:
            raise ValueError("Invalid sexagesimal component")
        value = (abs(a) * 3600 + b * 60 + c) * (-1 if parts[0].startswith("-") else 1)
        if unit == "sexagesimal_hour":
            value *= 15
        return dict(magnitude=str(value), unit="arcsecond", method="sexagesimal_conversion")
    if unit in ("hhmmss_millisecond", "signed_ddmmss_centisecond"):
        if unit == "hhmmss_millisecond":
            if not re.fullmatch(r"[ 0-9]{9}", literal):
                raise ValueError("Invalid fixed-width right ascension")
            a, b, c = (
                Fraction(literal[:2].strip() or "0"),
                Fraction(literal[2:4]),
                Fraction(literal[4:]) / 1000,
            )
            value = (a * 3600 + b * 60 + c) * 15
        else:
            if not re.fullmatch(r"[+ -][ 0-9]{8}", literal):
                raise ValueError("Invalid fixed-width declination")
            a, b, c = Fraction(literal[1:3]), Fraction(literal[3:5]), Fraction(literal[5:]) / 100
            value = (a * 3600 + b * 60 + c) * (-1 if literal[0] == "-" else 1)
        if not 0 <= b < 60 or not 0 <= c < 60:
            raise ValueError("Invalid fixed-width component")
        return dict(magnitude=str(value), unit="arcsecond", method="JPL_fixed_width_conversion")
    if unit == "JPL_D12.5_UT":
        return dict(
            magnitude=str(Fraction(literal) / 100000),
            unit="julian_day",
            time_scale="UT_as_documented",
        )
    if row.get("time_scale") == "EDT" and row.get("date"):
        if not re.fullmatch(r"\d{1,2}:\d{2}(?::\d{2})?", literal):
            raise ValueError("Invalid recorded EDT clock")
        parts = list(map(int, literal.split(":")))
        date = datetime.fromisoformat(row["date"])
        if date.tzinfo is not None or date.time() != datetime.min.time():
            raise ValueError("EDT conversion requires a date without another clock or offset")
        local = date.replace(
            hour=parts[0], minute=parts[1], second=parts[2] if len(parts) == 3 else 0
        )
        return dict(
            timestamp=(local + timedelta(hours=4)).replace(tzinfo=UTC).isoformat(),
            method="source_EDT_UTC_minus_4",
            precision="second" if len(parts) == 3 else "minute",
        )
    return None


def validate_conversion(row):
    expected = recompute_conversion(row)
    supplied = row.get("derived_normalization")
    if supplied != expected:
        raise ValueError(
            "Derived normalization differs from independently recomputed source conversion"
        )
    return expected
