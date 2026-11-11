"""Exact interpretation of reviewed source notation and units."""

import re
from fractions import Fraction
from .core import angular_place_marks, fraction_text, number

BODY_CALCULATIONS = {
    body + " calculation"
    for body in (
        "Sun",
        "Moon",
        "Mercury",
        "Venus",
        "Mars",
        "Jupiter",
        "Saturn",
        "New Star",
        "Earth",
        "fixed star",
    )
} | {"planetary motion calculation"}

JOVIAN_SATELLITES = {f"satellite {order} of Jupiter" for order in ("I", "II", "III", "IV")}
HISTORICAL_INTERVAL_BODIES = {
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Earth",
    "Mars",
    "Jupiter",
    "Saturn",
} | JOVIAN_SATELLITES

DAY_FRACTION_UNITS = (
    "day_minute",
    "day_second",
    "day_third",
    "day_fourth",
    "day_fifth",
    "day_sixth",
)

SOURCE_MILE_UNITS = {
    "distance_in_german_miles": "source_german_mile",
    "distance_in_ordinary_miles": "source_ordinary_mile",
    "distance_in_unspecified_miles": "source_unspecified_mile",
}

COMMA_THOUSANDS_NUMBER = r"[0-9]{1,3}(?:,[0-9]{3})+"

SOURCE_COMPARISON_LABELS = {
    "plus": "plus",
    "pl.": "plus",
    "min.": "minus",
    "minus": "minus",
    "min⁹": "minus",
    "min": "minus",
}


def comparison_numeric_text(row, expression):
    """Retain a reviewed unsigned angle or separate a printed sign label."""
    if row.get("comparison_relation") == "unsigned_difference_as_stated":
        from .coordinate_staging import parse_coordinate

        text = fraction_text(expression).strip()
        if (
            row.get("quantity") != "separation_difference"
            or row.get("role") != "historical_comparison"
            or row.get("source_comparison_sign") != "not_stated"
            or "comparison_label_original" in row
            or any(
                row.get(key)
                for key in (
                    "source_number_grouping",
                    "source_unit_notation",
                    "source_word_numbers",
                    "source_digit_restorations",
                    "source_note_marker_original",
                    "inherited_components",
                    "source_component_addends",
                )
            )
            or "°" not in text
            or re.fullmatch(r"[0-9/\s°′″'\"]+", text) is None
        ):
            raise ValueError("Unsigned comparison requires a complete literal angle without a sign")
        parsed = parse_coordinate(text)["components"]
        if parsed is None:
            raise ValueError("Unsigned comparison must consume the complete angular expression")
        if "components" in row:
            actual = row["components"]
            if (
                not isinstance(actual, dict)
                or set(actual) != set(parsed)
                or any(number(fraction_text(actual[k])) != number(v) for k, v in parsed.items())
            ):
                raise ValueError(
                    "Unsigned comparison components differ from literal units or values"
                )
        return text
    label = row.get("comparison_label_original")
    if (
        row.get("quantity") != "separation_difference"
        or row.get("role") != "historical_comparison"
        or row.get("comparison_relation") != "second_minus_first_as_stated"
        or not isinstance(label, str)
        or label not in SOURCE_COMPARISON_LABELS
        or SOURCE_COMPARISON_LABELS[label] != row.get("source_comparison_sign")
        or not expression.strip().endswith(" " + label)
        or any(
            row.get(key)
            for key in (
                "source_number_grouping",
                "source_unit_notation",
                "source_word_numbers",
                "source_digit_restorations",
                "source_note_marker_original",
                "inherited_components",
                "source_component_addends",
            )
        )
    ):
        raise ValueError("Comparison requires a literal, reviewed source sign label")
    text = fraction_text(expression.strip()[: -len(label)].strip()).strip()
    if re.fullmatch(r"\d+(?:\s+\d+/\d+|/\d+)?", text) is None:
        raise ValueError("Comparison magnitude must be one complete unsigned scalar")
    return text


def interpret_part_minute_notation(row):
    """Interpret explicitly reviewed source unit notation without changing its literal."""
    if row.get("source_unit_notation") == "roman_sexagesimal_places":
        return interpret_roman_places(row)
    notation = row.get("source_unit_notation")
    if notation in ("decimal_degrees", "decimal_hours"):
        angular = notation == "decimal_degrees"
        units = r"(?:degrees?|°)" if angular else r"hours?"
        match = re.fullmatch(r"([0-9]+\.[0-9]+)\s*" + units, row["source_expression"].strip())
        if (
            row.get("quantity") not in (ANGLE_QUANTITIES if angular else TIME_QUANTITIES)
            or match is None
        ):
            raise ValueError(
                "Decimal notation requires a complete unsigned decimal and matching unit"
            )
        value = str(Fraction(match[1]))
        return (f"{value}°", {"degree": value}) if angular else (f"{value}^h^", {"hour": value})
    if notation == "dms_latitude_terminal_half_minute":
        match = re.fullmatch(r"([0-9]+)°\s*([0-9]+)′\s*\.", row["source_expression"].strip())
        if (
            row.get("quantity") != "ecliptic_latitude"
            or row.get("role") not in ("historical_input", "reduction", "editorial_variant")
            or row.get("reference") is not None
            or row.get("direction") not in (None, "north", "south")
            or row.get("zodiac_sign") is not None
            or "not_an_additional_raw_reading" not in row.get("flags", [])
            or match is None
            or not 0 <= int(match[1]) < 90
            or not 0 <= int(match[2]) < 60
        ):
            raise ValueError("Latitude point requires a complete reviewed half-minute convention")
        return (
            f"{match[1]}° {match[2]}′ 30″",
            dict(degree=match[1], arcminute=match[2], arcsecond="30"),
        )
    if notation == "paired_decimal_tenths":
        match = re.fullmatch(
            r"([0-9]+)(?:\s*(?:\.,|[.:])\s*|\s+)([0-9])", row["source_expression"].strip()
        )
        if (
            row.get("quantity") != "source_scalar"
            or row.get("source_parameter_kind") != "sine_increment_per_source_second"
            or row.get("role")
            not in ("historical_input", "calculation_intermediate", "editorial_variant")
            or match is None
        ):
            raise ValueError("Paired tenths require a complete reviewed native sine increment")
        value = str(Fraction(10 * int(match[1]) + int(match[2]), 10))
        return value, {"scalar": value}
    if notation == "tabular_dms_terminal_half":
        match = re.fullmatch(
            r"([0-9]+)\s+([0-9]+)\s+([0-9]+)(\.)?", row["source_expression"].strip()
        )
        if (
            row.get("quantity") != "calculation_angle"
            or row.get("role") not in ("historical_input", "editorial_variant")
            or row.get("source_tabular_application") != "hours_by_arcminutes"
            or match is None
        ):
            raise ValueError("Tabular places require a complete selected angular application")
        second = match[3] + (" 1/2" if match[4] else "")
        components = dict(degree=match[1], arcminute=match[2], arcsecond=second)
        return f"{match[1]}° {match[2]}′ {second}″", components
    if notation == "postfixed_minute_second_third_slashes":
        match = re.fullmatch(
            r"([0-9]+)\s*/\s*([0-9]+)\s*//\s*([0-9]+)\s*///",
            row["source_expression"].strip(),
        )
        if row["quantity"] not in ANGLE_QUANTITIES or match is None:
            raise ValueError("Postfixed places require a complete reviewed angular sequence")
        components = dict(
            zip(("arcminute", "arcsecond", "arcsexagesimal_third"), match.groups(), strict=True)
        )
        return f"{match[1]}′ {match[2]}″ {match[3]}‴", components
    if notation not in ("parts_1_minutes", "parts_slash_minutes"):
        raise ValueError("Unknown source unit notation")
    if row["quantity"] not in ANGLE_QUANTITIES | {"source_sexagesimal_length"}:
        raise ValueError("Part/minute notation requires angular or native length units")
    token = r"[0-9]+(?:\s+[0-9]+/[0-9]+|/[0-9]+)?"
    pattern = (
        r"(?P<label>[PpGg])\.\s*(?P<degree>[0-9]+)\s*\.?\s*/\s*(?P<minute>[0-9]+)(?P<suffix>[^0-9/⁄°′″?⟦⟧]*)"
        if notation == "parts_slash_minutes"
        else rf"(?:Sign\s+(?P<sign>[0-9]+),?\s*)?(?P<label>[PG])\.\s*(?P<degree>{token})\s*[.,]?\s*1\.\s*(?P<minute>{token})(?P<suffix>[^0-9°′″]*)"
    )
    match = re.fullmatch(pattern, fraction_text(row["source_expression"]).strip())
    if match is None:
        raise ValueError("Incomplete or contradictory part/minute notation")
    native = row["quantity"] == "source_sexagesimal_length"
    sign = match.groupdict().get("sign")
    if native and (sign is not None or match["label"].upper() != "P"):
        raise ValueError("Native lengths cannot carry zodiac sign counts")
    components = {}
    if sign is not None:
        components["sign_count"] = sign
    components["source_part" if native else "degree"] = match["degree"]
    components["part_minute" if native else "arcminute"] = match["minute"]
    text = (
        (sign + "^s^ " if sign is not None else "")
        + match["degree"]
        + "° "
        + match["minute"]
        + "′"
        + match["suffix"]
    )
    return text, components


def interpret_roman_places(row):
    """Consume ordered, explicitly printed sexagesimal place labels completely."""
    angular = row["quantity"] in ANGLE_QUANTITIES
    if not angular and row["quantity"] != "clock_elapsed_time":
        raise ValueError("Roman places require an angle or elapsed duration")
    places = [("Sign", "sign_count", "^s^"), ("(?:[PG]|part)\\.", "degree", "°")] if angular else []
    places += [
        ("(?:1|l|min|minut)\\.", "arcminute" if angular else "minute", "′"),
        ("(?:11|ll)\\.", "arcsecond" if angular else "second", "″"),
        ("111\\.", "arcsexagesimal_third" if angular else "time_third", "‴"),
    ]
    if angular:
        places += [
            ("1111\\.", "arcsexagesimal_fourth", "⁗"),
            ("V\\.", "arcsexagesimal_fifth", "″″′"),
            ("V1\\.", "arcsexagesimal_sixth", "″″″"),
            ("V11\\.", "arcsexagesimal_seventh", "″″″′"),
        ]
    remaining = fraction_text(row["source_expression"]).strip()
    components, canonical = {}, []
    token = r"[0-9]+(?:\s+[0-9]+/[0-9]+|/[0-9]+)?"
    for label, unit, mark in places:
        match = re.match(rf"{label}\s+(?P<value>{token})(?=$|[\s.,])", remaining)
        if match is None:
            continue
        value = match["value"]
        components[unit] = value
        canonical.append(value + mark)
        remaining = remaining[match.end() :].lstrip(" .,\t\n")
    if remaining or not components:
        raise ValueError("Incomplete or out-of-order Roman sexagesimal places")
    return " ".join(canonical), components


def source_numeric_text(row, expression):
    """Interpret explicitly reviewed integer grouping without changing the literal."""
    if "comparison_label_original" in row or "comparison_sources" in row:
        return comparison_numeric_text(row, expression)
    if row["quantity"] in ANGLE_QUANTITIES:
        expression = angular_place_marks(expression)
    text = fraction_text(expression)
    if "source_digit_restorations" in row:
        restorations = row["source_digit_restorations"]
        if (
            not isinstance(restorations, list)
            or not restorations
            or any(not isinstance(s, str) for s in restorations)
            or len(set(restorations)) != len(restorations)
            or any(
                row.get(key)
                for key in (
                    "source_number_grouping",
                    "source_unit_notation",
                    "source_word_numbers",
                    "inherited_components",
                    "source_component_addends",
                )
            )
        ):
            raise ValueError("Digit restoration requires one independent literal interpretation")
        for literal in restorations:
            if len(literal) > 32 or not re.fullmatch(r"\d+(?:\[\d+\]\d*)+", literal):
                raise ValueError("Digit restoration requires explicit bracketed digits")
            pattern = r"(?<![\w\]])" + re.escape(literal) + r"(?![\w\[])"
            if len(list(re.finditer(pattern, text))) != 1:
                raise ValueError("Digit restoration lacks a unique complete numeric token")
            text = re.sub(pattern, literal.replace("[", "").replace("]", ""), text)
        return text
    if "source_number_grouping" not in row:
        return text
    grouping = row["source_number_grouping"]
    if row["quantity"] != "source_scalar" and not (
        row["quantity"]
        in set(SOURCE_MILE_UNITS)
        | {"distance_in_semidiameters", "source_sexagesimal_length", "distance_in_paces"}
        and grouping in ("comma_thousands", "comma_thousands_mixed_fraction")
    ):
        raise ValueError("Digit grouping requires a reviewed scalar or whole native distance")
    if grouping == "comma_thousands_mixed_fraction":
        match = re.fullmatch(
            rf"(?P<whole>{COMMA_THOUSANDS_NUMBER})\s+(?P<numerator>\d+)/(?P<denominator>\d+)",
            text.strip(),
        )
        if match is None or not 0 <= int(match["numerator"]) < int(match["denominator"]):
            raise ValueError("Invalid reviewed comma-grouped mixed fraction")
        return (
            match["whole"].replace(",", "") + " " + match["numerator"] + "/" + match["denominator"]
        )
    integer_patterns = {
        "spaced_integer_digits": r"[0-9]+(?:[ \t]+[0-9]+)+",
        "comma_thousands": COMMA_THOUSANDS_NUMBER,
        "middot_integer_digits": r"[0-9]+(?:·[0-9]+)+",
    }
    if grouping in integer_patterns:
        if re.fullmatch(integer_patterns[grouping], text.strip()) is None:
            raise ValueError("Invalid reviewed integer digit grouping")
        return re.sub(r"[ \t,·]", "", text.strip())
    if grouping != "spaced_thousands":
        raise ValueError("Unknown source digit grouping")
    match = re.fullmatch(
        r"(?P<integer>\d{1,3}(?:[ \t]+\d{3})+)(?P<fraction>[ \t]+\d+/\d+)?", text.strip()
    )
    if match is None:
        raise ValueError("Invalid spaced thousands groups")
    return re.sub(r"[ \t]+", "", match["integer"]) + (match["fraction"] or "")


ANGLE_QUANTITIES = {
    "zenith_distance",
    "obliquity",
    "polar_distance",
    "unclassified_angle",
    "declination",
    "right_ascension",
    "rising_amplitude",
    "ascensional_difference",
    "oblique_ascension",
    "oblique_descension",
    "ecliptic_longitude",
    "geographical_longitude",
    "geographical_latitude",
    "ecliptic_latitude",
    "orbital_longitude",
    "angular_separation",
    "angular_offset",
    "angular_diameter",
    "angular_diameter_variation",
    "angular_semidiameter",
    "angular_length",
    "altitude",
    "azimuth",
    "meridian_distance",
    "right_ascension_difference",
    "longitude_correction",
    "latitude_correction",
    "declination_correction",
    "azimuth_correction",
    "separation_correction",
    "separation_difference",
    "longitude_difference",
    "latitude_difference",
    "declination_difference",
    "altitude_difference",
    "angular_motion_difference",
    "parallax_angle",
    "refraction_angle",
    "net_refraction_parallax",
    "calculation_angle",
    "angular_daily_motion",
    "horizon_inclination",
    "instrument_dimension_angle",
    "instrument_altitude_bias",
    "instrument_separation_bias",
    "stated_angular_precision",
}
TIME_QUANTITIES = {
    "recorded_clock",
    "expected_clock",
    "hour_angle",
    "clock_correction",
    "transit_clock",
    "calculation_epoch",
    "clock_elapsed_time",
    "temporal_hour_count",
    "clock_drift",
    "annotated_time",
    "meridian_time_difference",
    "inferred_time",
}
ANGULAR_RATES = {
    "angular_daily_motion": "arcsecond_per_source_day",
    "angular_hourly_motion": "arcsecond_per_source_hour",
    "angular_yearly_motion": "arcsecond_per_source_year",
}
ANGLE_QUANTITIES.update(ANGULAR_RATES)
ZODIAC_SIGNS = dict(
    zip(
        (
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
        ),
        ("♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"),
        strict=True,
    )
)
SOURCE_WORD_NUMBERS = {
    "forty-first": "41",
    "quadraginta": "40",
    "tertia minuti parte": "1/3",
    "dimidij minuti": "1/2",
    "eight hundred": "800",
    "a thousand": "1000",
    "a year": "1",
    "fifty-eighth": "58",
    "a fourth part": "1/4",
    "an eighteenth part": "1/18",
    "a twelfth part": "1/12",
    "two thousand": "2000",
    "two hundred and sixty": "260",
    "three hundred and sixty": "360",
    "fifty thousand": "50000",
    "forty": "40",
    "every other year": "2",
    "a whole month": "1",
    "twenty-fourth": "24",
    "one degree and a quarter": "1 1/4",
    "three-and-a-half": "3 1/2",
    "six hundred": "600",
    "ten thousand": "10000",
    "1st": "1",
    "10th": "10",
    "two ells with a half": "5/2",
    "third": "3",
    "third part": "1/3",
    "One third": "1/3",
    "14th part": "1/14",
    "six": "6",
    "two": "2",
    "twice": "2",
    "three": "3",
    "half": "1/2",
    "one": "1",
    "whole": "1",
    "single": "1",
    "ten": "10",
    "a minute and a half": "1 1/2",
    "twelfth": "12",
}
SOURCE_WORD_NUMBERS.update(
    {
        "four": "4",
        "double": "2",
        "doubled": "2",
        "Two": "2",
        "quarter": "1/4",
        "sixth": "6",
        "seven": "7",
        "eight": "8",
    }
)
SOURCE_WORD_NUMBERS.update(
    {
        "a third": "1/3",
        "a fourth": "1/4",
        "a semidiameter": "1",
        "a Moon's diameter": "1",
        "two fifths": "2/5",
        "sixth hour": "6",
    }
)
SOURCE_WORD_NUMBERS["a 131st part"] = "1/131"
SOURCE_WORD_NUMBERS["by a third"] = "1/3"
SOURCE_WORD_NUMBERS["thirteenth hour and a quarter"] = "13 1/4"
SOURCE_WORD_NUMBERS.update(
    {
        "thirteenth": "13",
        "fourteenth": "14",
        "twenty-first": "21",
        "twenty-seven": "27",
        "twenty-ninth": "29",
        "a week": "1",
    }
)
SOURCE_WORD_NUMBERS["III"] = "3"
SOURCE_WORD_NUMBERS.update(
    {
        "I": "1",
        "II": "2",
        "IV": "4",
        "IIII": "4",
        "V": "5",
        "VI": "6",
        "VII": "7",
        "VIII": "8",
        "IX": "9",
        "X": "10",
        "XI": "11",
        "XII": "12",
        "XIII": "13",
        "XIV": "14",
        "XV": "15",
        "XVI": "16",
        "XVII": "17",
        "XVIII": "18",
        "XIIX": "18",
        "XIX": "19",
        "XX": "20",
        "XXI": "21",
        "XXII": "22",
        "XXIII": "23",
        "XXIV": "24",
        "XXIIII": "24",
        "XXV": "25",
        "XXVI": "26",
        "XXVII": "27",
        "XXVIII": "28",
        "XXIIX": "28",
        "XXIX": "29",
        "XXX": "30",
        "i": "1",
        "ij": "2",
        "viii": "8",
        "xij": "12",
        "xvj": "16",
        "xvij": "17",
        "xviij": "18",
    }
)
SOURCE_WORD_NUMBERS["tenth"] = "10"
SOURCE_WORD_NUMBERS.update(
    {"fifth": "5", "seventy thousand": "70000", "thirty-five thousand": "35000"}
)
SOURCE_WORD_NUMBERS["ninth"] = "9"
SOURCE_WORD_NUMBERS["ninetieth"] = "90"
SOURCE_WORD_NUMBERS["seventh"] = "7"
SOURCE_WORD_NUMBERS["exactly at the beginning"] = "0"
SOURCE_WORD_NUMBERS.update({"nine": "9", "eleven": "11"})
SOURCE_WORD_NUMBERS["second"] = "2"
SOURCE_WORD_NUMBERS.update({"Three": "3", "five": "5"})
SOURCE_WORD_NUMBERS["the amount of its illuminated portion"] = "1"
SOURCE_WORD_NUMBERS["quadrant"] = "90"
SOURCE_WORD_NUMBERS["none"] = "0"
SOURCE_WORD_NUMBERS["sixth part"] = "1/6"
SOURCE_WORD_NUMBERS["eleven twelfths"] = "11/12"
SOURCE_WORD_NUMBERS["eleven-twelfths"] = "11/12"
SOURCE_WORD_NUMBERS["a hundred and five"] = "105"
SOURCE_WORD_NUMBERS["ten and a half"] = "10 1/2"
SOURCE_WORD_NUMBERS["a full year"] = "1"
SOURCE_WORD_NUMBERS["eightfold"] = "8"
SOURCE_WORD_NUMBERS["three and a half"] = "3 1/2"
SOURCE_WORD_NUMBERS["a third part of a quadrant"] = "30"
SOURCE_WORD_NUMBERS["one degree less a twelfth"] = "11/12"
SOURCE_WORD_NUMBERS["one quarter"] = "1/4"
SOURCE_WORD_NUMBERS.update(
    {
        "30th": "30",
        "36th": "36",
        "fourth part": "1/4",
        "thirteen": "13",
        "Sixteen": "16",
        "the diameter": "1",
        "a lunar diameter": "1",
        "its own semidiameter": "1",
        "one temporal hour and three quarters": "1 3/4",
        "an hour and a half": "1 1/2",
        "two and a half hours": "2 1/2",
        "a fiftieth part": "1/50",
        "tenfold": "10",
        "fivefold": "5",
        "sesquiple": "1 1/2",
        "subsesquitertian": "3/4",
        "subtriple": "1/3",
        "thirty thousand": "30000",
        "one hundred and twenty": "120",
        "one hundred and eighty": "180",
        "a thirteenth": "1/13",
        "a fifteenth": "1/15",
        "the fifteenth": "1/15",
        "nil": "0",
        "unity": "1",
        "the thirtieth": "1/30",
        "one half": "1/2",
        "half of one": "1/2",
        "eight-twelfths": "2/3",
        "a whole quarter": "1/4",
        "seven hundred and eighty thousand": "780000",
        "one hundred and twenty thousand": "120000",
        "45th": "45",
        "20th": "20",
        "the seven hundred and twentieth": "1/720",
        "720th": "1/720",
        "the ninth": "1/9",
        "fifty": "50",
        "the 24th": "1/24",
        "half as large again": "3/2",
        "one twenty-fourth": "1/24",
        "one thousand": "1000",
        "one-hundred-and-eightieth": "1/180",
        "triple": "3",
        "the 109th part": "1/109",
        "the 720th part": "1/720",
        "the 3960th part": "1/3960",
        "six thousand": "6000",
        "CCCCXL": "440",
        "DCCCCXL": "940",
        "a 70th particle": "1/70",
        "the 7000th particle": "1/7000",
    }
)
SOURCE_WORD_NUMBERS["one degree and three quarters"] = "1 3/4"
SOURCE_WORD_NUMBERS["one degree and two fifths"] = "1 2/5"
SOURCE_WORD_NUMBERS["twenty-two"] = "22"
SOURCE_WORD_NUMBERS.update(
    {
        "thousand": "1000",
        "seven thousand": "7000",
        "forty-nine thousand": "49000",
        "seven hundred": "700",
        "threefold": "3",
        "twofold": "2",
        "hundredfold": "100",
        "twenty thousand": "20000",
        "four and a half": "4 1/2",
        "two hundred": "200",
        "seventy": "70",
        "twenty-nine": "29",
        "First": "1",
        "Second": "2",
        "Third": "3",
        "Fourth": "4",
        "Fifth": "5",
        "Sixth": "6",
        "twenty": "20",
        "sixteen": "16",
    }
)
SOURCE_WORD_NUMBERS.update(
    {
        "nineteen thousand": "19000",
        "22000th": "22000",
        "fifteenth": "15",
        "twentieth": "20",
        "eighteenth": "18",
        "ninety": "90",
        "seventy-two": "72",
        "fifty-four": "54",
        "thirty-six": "36",
        "eighteen": "18",
        "thirty-sixth": "36",
        "forty-two": "42",
        "six thousand": "6000",
        "five hundred": "500",
        "eighty": "80",
        "one hundred and fifty beyond the thousand": "1150",
    }
)
SOURCE_WORD_NUMBERS["eighth part"] = "1/8"
SOURCE_WORD_NUMBERS["twelfth part"] = "1/12"
SOURCE_WORD_NUMBERS["two-thirds"] = "2/3"
SOURCE_WORD_NUMBERS.update({"a fifth": "1/5", "a tenth": "1/10", "half a quadrant": "45"})
SOURCE_WORD_NUMBERS["a mile and a half"] = "1 1/2"
SOURCE_WORD_NUMBERS.update(
    {
        "three hundred": "300",
        "four hundred": "400",
        "three quarters": "3/4",
        "three-quarters": "3/4",
        "a million": "1000000",
        "two million": "2000000",
        "23rd": "23",
        "25th": "25",
        "29th": "29",
        "48th": "48",
        "57th": "57",
    }
)
SOURCE_WORD_NUMBERS.update({"right angle": "90", "semicircle": "180"})
SOURCE_WORD_NUMBERS["one sixth of a degree"] = "1/6"
SOURCE_WORD_NUMBERS["one circle and a half"] = "1 1/2"
SOURCE_WORD_NUMBERS["thirtieth"] = "30"
SOURCE_WORD_NUMBERS["a sign and a half"] = "1 1/2"
SOURCE_WORD_NUMBERS["nona cum quadrante"] = "9 1/4"
SOURCE_WORD_NUMBERS.update({"first": "1", "one and a half": "1 1/2", "fifth part": "1/5"})
SOURCE_WORD_NUMBERS["a degree and a half"] = "1 1/2"
SOURCE_WORD_NUMBERS.update({"a whole degree": "1", "a full degree and a half": "1 1/2"})
SOURCE_WORD_NUMBERS.update({"four years & a half": "4 1/2", "a full month": "1"})
SOURCE_WORD_NUMBERS["fifty"] = "50"
SOURCE_WORD_NUMBERS.update({"Twelve": "12", "Thirteen": "13"})
SOURCE_WORD_NUMBERS.update(
    {"fifty-one": "51", "twenty-eight": "28", "eighth": "8", "nineteenth": "19"}
)
SOURCE_WORD_NUMBERS["a whole sign"] = "1"
SOURCE_WORD_NUMBERS["Four"] = "4"
SOURCE_WORD_NUMBERS["fourfold"] = "4"
SOURCE_WORD_NUMBERS["double"] = "2"
SOURCE_WORD_NUMBERS["a quarter of 1"] = "1/4"
SOURCE_WORD_NUMBERS["twenty-three and a half"] = "23 1/2"
SOURCE_WORD_NUMBERS["twenty-four"] = "24"
SOURCE_WORD_NUMBERS["thirty"] = "30"
SOURCE_WORD_NUMBERS["thirtyfold"] = "30"
SOURCE_WORD_NUMBERS["decade"] = "10"
SOURCE_WORD_NUMBERS.update({"sixty-three": "63", "a sixth": "1/6"})
SOURCE_WORD_NUMBERS.update({"two digits": "2", "sub-sesquialter ratio": "2/3", "eleventh": "11"})
SOURCE_WORD_NUMBERS.update(
    {
        "four right angles": "360",
        "two right angles": "180",
        "a quarter part of the circumference": "90",
        "a right angle": "90",
        "fourteen": "14",
        "a third part": "1/3",
    }
)
SOURCE_WORD_NUMBERS.update(
    {
        "once": "1",
        "fourth": "4",
        "sixteen thousand": "16000",
        "a three-hundredth": "1/300",
        "one three-hundredth": "1/300",
        "three-hundredth": "1/300",
        "an inch": "1",
        "a sixteenth part": "1/16",
        "a hundredth part": "1/100",
    }
)
SOURCE_WORD_NUMBERS["Half"] = "1/2"
SOURCE_WORD_NUMBERS["an hour"] = "1"
SOURCE_WORD_NUMBERS["An hour"] = "1"
SOURCE_WORD_NUMBERS.update(
    {
        "one-and-a-half": "1 1/2",
        "hundred": "100",
        "twelve": "12",
        "fifteen": "15",
        "a whole minute": "1",
        "a whole degree": "1",
        "a single sextant of a degree": "1/6",
    }
)
SOURCE_WORD_NUMBERS["no latitude"] = "0"
SOURCE_WORD_NUMBERS["at the beginning"] = "0"
SOURCE_WORD_NUMBERS.update(
    {
        "without latitude": "0",
        "without altitude": "0",
        "a degree": "1",
        "Moon's semidiameter": "1",
        "one moon": "1",
        "a palm": "1",
    }
)
SOURCE_WORD_NUMBERS.update(
    {"a digit's breadth": "1", "Moon's diameter": "1", "breadth of a digit": "1", "a palm": "1"}
)
SOURCE_WORD_NUMBERS.update({"a degree": "1", "half a degree": "1/2"})
SOURCE_WORD_NUMBERS["sixth of a degree"] = "1/6"
SOURCE_WORD_NUMBERS["whole one"] = "1"
SOURCE_WORD_NUMBERS.update({"nineteen": "19", "two degrees less a quarter": "1 3/4"})
SOURCE_WORD_NUMBERS.update(
    {
        "five-twelfths": "5/12",
        "A": "1",
        "a minute": "1",
        "one third": "1/3",
        "one-tenth": "1/10",
        "two-hundredth": "1/200",
        "ninetieth part": "1/90",
        "halves": "1/2",
        "quarters": "1/4",
        "tens": "10",
        "fives": "5",
    }
)
SOURCE_WORD_NUMBERS.update(
    {
        "semidiameter of the Moon": "1",
        "a quarter": "1/4",
        "equal to the gap": "1",
        "a diameter of the Moon": "1",
        "one palm": "1",
        "diameter of the Moon": "1",
        "two Moons": "2",
        "a digit and a half": "1 1/2",
        "thousandths": "1000",
        "sixty": "60",
        "two-fifths": "2/5",
        "a tenth part": "1/10",
        "15th part": "1/15",
        "29th part": "1/29",
        "a seventh part": "1/7",
        "one-sixth": "1/6",
        "sixth part of one degree": "1/6",
        "a full degree": "1",
        "a whole year": "1",
        "an entire year": "1",
        "a year and a half": "1 1/2",
        "a year and a third": "1 1/3",
        "a hundred": "100",
        "a hundred and forty": "140",
        "two hundred and three": "203",
        "thirty-six thousand": "36000",
        "twenty-six thousand": "26000",
        "twenty": "20",
        "two thirds": "2/3",
        "single third": "1/3",
        "One hundred": "100",
        "four hundred and three thousand": "403000",
        "a quarter part": "1/4",
        "3rd": "3",
        "2nd": "2",
        "7th": "7",
        "sextant": "1/6",
        "5th": "5",
        "6th": "6",
        "12th": "12",
        "67th": "67",
        "no hour": "0",
        "nine hundred": "900",
        "six hundred and fifty": "650",
        "three sevenths": "3/7",
        "four ninths": "4/9",
        "a twelfth": "1/12",
        "a twenty-fourth part": "1/24",
        "a forty-eighth part": "1/48",
        "one fifth": "1/5",
        "a fifth part": "1/5",
        "dark third of the limb": "1/3",
        "One": "1",
        "western third": "1/3",
        "seven twelfths": "7/12",
        "one hundred and sixty-eighth": "1/168",
    }
)


def validate_reference_status(assertion):
    """Distinguish reviewed omissions or unresolved antecedents from missing data."""
    if "source_reference_status" not in assertion:
        return False
    if (
        assertion["source_reference_status"] not in ("not_recorded", "antecedent_unresolved")
        or assertion.get("quantity") != "angular_separation"
        or assertion.get("reference") is not None
        or (
            assertion["source_reference_status"] == "antecedent_unresolved"
            and "reference_antecedent_unresolved" not in assertion.get("flags", [])
        )
    ):
        raise ValueError("Invalid source reference status")
    return True


VISUAL_REFERENCE_KINDS = frozenset(
    {
        "visual_palm",
        "visual_digit_breadth",
        "visual_lunar_diameter",
        "visual_lunar_semidiameter",
        "visual_lunar_reference_unstated",
        "visual_reference_separation",
    }
)


def unresolved_visual_fraction(row):
    """Retain an unread native ratio without assigning it a scalar."""
    expression = row.get("source_expression", "")
    return (
        row.get("quantity") == "source_fraction"
        and row.get("source_fraction_kind") in VISUAL_REFERENCE_KINDS
        and row.get("role") in ("recorded_reading", "historical_input")
        and row.get("reference") is not None
        and row.get("direction") is None
        and {
            "source_notation_unresolved",
            "source_visual_estimate",
            "geometry_interpretation_unestablished",
        }
        <= set(row.get("flags", []))
        and isinstance(expression, str)
        and len(expression) <= 80
        and "[?]" in expression
        and re.fullmatch(r"[0-9\[\]?/⁄\s]+", expression) is not None
    )


def unresolved_instrument_scalar(row):
    """Recognize reviewed uncertain native numerals without choosing a value."""
    expression = row.get("source_expression", "")
    calendar_count = (
        row.get("subject") == "calendar calculation"
        and row.get("role") == "historical_input"
        and row.get("source_parameter_kind")
        in (
            "source_year_count",
            "source_month_count",
            "source_day_count",
            "source_cycle_count",
            "source_week_count",
        )
        and row.get("reference") is None
        and row.get("event_id") is None
        and row.get("model_name") is None
        and "not_an_additional_raw_reading" in row.get("flags", [])
    )
    comparison_operand = (
        row.get("source_parameter_kind") == "comparison_multiplier"
        and row.get("subject") in BODY_CALCULATIONS
        and row.get("role") in ("historical_input", "calculation_intermediate")
        and row.get("reference") is None
        and row.get("event_id") is None
        and row.get("model_name") is None
        and "not_an_additional_raw_reading" in row.get("flags", [])
    )
    table_alternative = (
        row.get("source_parameter_kind") == "unlabelled_table_value"
        and row.get("subject") == "Moon calculation"
        and row.get("role") == "source_alternative"
        and row.get("reference") is None
        and row.get("event_id") is None
        and row.get("model_name") is None
        and (row.get("variant_of_id") is not None or bool(row.get("variant_of_key")))
        and {"not_an_additional_raw_reading", "alternative_suggestion_not_applied"}
        <= set(row.get("flags", []))
    )
    letter_numeral = (
        row.get("source_parameter_kind") == "arithmetic_intermediate"
        and row.get("subject") == "Moon calculation"
        and row.get("role") == "calculation_intermediate"
        and row.get("reference") is None
        and row.get("event_id") is None
        and row.get("model_name") is None
        and "not_an_additional_raw_reading" in row.get("flags", [])
    )
    scale_label = (
        row.get("source_parameter_kind") == "instrument_scale_value"
        and row.get("subject") == "instrument"
        and row.get("role") == "historical_input"
        and row.get("reference") is None
        and row.get("event_id") is None
        and row.get("model_name") is None
        and "not_an_additional_raw_reading" in row.get("flags", [])
    )
    native_model = (
        row.get("source_parameter_kind") == "model_length"
        and row.get("subject") in BODY_CALCULATIONS
        and row.get("role") in ("historical_input", "calculation_intermediate")
        and row.get("reference") is None
        and row.get("event_id") is None
        and row.get("model_name") is None
        and "not_an_additional_raw_reading" in row.get("flags", [])
        and isinstance(row.get("source_scalar_scale"), str)
        and re.fullmatch(r"[1-9]\d*", row["source_scalar_scale"]) is not None
    )
    native_trigonometric = (
        row.get("source_parameter_kind") in ("scaled_sine", "sine_increment_per_source_second")
        and row.get("subject") in BODY_CALCULATIONS
        and (
            row.get("role") in ("historical_input", "calculation_intermediate")
            or (
                row.get("role") == "editorial_variant"
                and (row.get("variant_of_id") is not None or row.get("variant_of_key"))
                and "alternative_suggestion_not_applied" in row.get("flags", [])
            )
        )
        and row.get("reference") is None
        and row.get("event_id") is None
        and row.get("model_name") is None
        and "not_an_additional_raw_reading" in row.get("flags", [])
        and isinstance(row.get("source_scalar_scale"), str)
        and re.fullmatch(r"[1-9]\d*", row["source_scalar_scale"]) is not None
    )
    if (
        row.get("quantity") != "source_scalar"
        or not (
            row.get("role") == "recorded_reading"
            or scale_label
            or table_alternative
            or letter_numeral
            or native_model
            or native_trigonometric
            or comparison_operand
            or calendar_count
        )
        or "source_notation_unresolved" not in row.get("flags", [])
        or row.get("direction") is not None
        or (
            row.get("source_scalar_scale") is not None
            and not (native_model or native_trigonometric)
        )
        or not isinstance(expression, str)
        or len(expression) > 80
    ):
        return False
    if calendar_count:
        return (
            re.fullmatch(
                r"(?:[0-9]*\s*\[(?:numeral:\s*)?\?\]\s*[0-9]*|[0-9]+\s*\[fraction:\s*\?\])",
                expression,
            )
            is not None
        )
    if table_alternative:
        return re.fullmatch(r"\d+\?", expression) is not None
    if comparison_operand:
        return (
            re.fullmatch(
                r"(?:\d+\[\?\]\d*|⟦\d+(?:/\d+)+⟧|\d+\s+\d+/\[\?\]|\d+\s+(?:0|☩))",
                expression,
            )
            is not None
        )
    if native_model:
        return (
            "[?]" in expression
            and re.search(r"\d", expression) is not None
            and re.fullmatch(r"[0-9\[\]?/⁄.\s]+", expression) is not None
        )
    if native_trigonometric:
        literal = re.sub(r"\[numeral:\s*\?\]", "[?]", expression)
        return (
            "[?]" in literal
            and re.search(r"\d", literal) is not None
            and re.fullmatch(r"[0-9\[\]?.\s]+", literal) is not None
        ) or (
            row["source_parameter_kind"] == "sine_increment_per_source_second"
            and re.fullmatch(r"\d{2,}", literal) is not None
        )
    if letter_numeral:
        return re.fullmatch(r"\d+S", expression) is not None
    if scale_label:
        return (
            "[?]" in expression
            and re.search(r"\d", expression) is not None
            and re.fullmatch(r"[0-9\[\]?]+", expression) is not None
        )
    if row.get("source_parameter_kind") == "instrument_chord":
        return (
            row.get("subject") == "Sun"
            and row.get("reference") is None
            and re.fullmatch(r"\d+\[\?\]\d*", expression) is not None
        )
    return row.get("source_parameter_kind") == "instrument_linear_reading" and (
        (
            "[?]" in expression
            and re.search(r"\d", expression) is not None
            and re.fullmatch(r"[0-9\[\]?/⁄.\s]+", expression) is not None
        )
        # A reviewed comma-separated native reading need not be a decimal.
        # Preserve its notation without choosing a scale or component split.
        or re.fullmatch(r"[0-9]+,[0-9]+[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]?", expression) is not None
    )


def unresolved_source_distance(row):
    """Keep a queried Earth-radius reading without selecting its magnitude."""
    expression = row.get("source_expression")
    return (
        row.get("quantity") == "distance_in_semidiameters"
        and row.get("source_semidiameter_body") == "Earth"
        and row.get("reference") == "Earth"
        and row.get("role") in ("historical_input", "reduction", "calculation_intermediate")
        and row.get("direction") is None
        and row.get("zodiac_sign") is None
        and {"source_notation_unresolved", "not_an_additional_raw_reading"}
        <= set(row.get("flags", []))
        and isinstance(expression, str)
        and "?" in expression
        and re.search(r"\d", expression) is not None
        and re.fullmatch(r"[0-9/⁄\[\]?\s]+", fraction_text(expression)) is not None
    )


def native_distance_value(components, units):
    """Normalize written base, sixtieth and sixtieth-squared length places."""
    if not components or not set(components) <= set(units):
        raise ValueError("Invalid native distance components")
    leading_unit = next(unit for unit in units if unit in components)
    value = 0
    for index, unit in enumerate(units):
        token = fraction_text(components.get(unit, "0")).strip()
        if not re.fullmatch(r"\d+(?:/\d+)?(?:\s+\d+/\d+)?", token):
            raise ValueError("Invalid unsigned native distance component")
        part = number(token)
        if part < 0 or (index and unit != leading_unit and part >= 60):
            raise ValueError("Native distance subunit out of range")
        value += part / 60**index
    return value, next(unit for unit in reversed(units) if unit in components)


def normalize_quantity(assertion):
    result = dict(
        status="unsupported",
        magnitude=None,
        unit=None,
        magnitude_degrees=None,
        signed_magnitude=None,
        least_component_unit=None,
    )
    if assertion.get("quantity") == "temporal_hour_count":
        result["unit"] = "source_temporal_hour"
        if assertion.get("direction") is not None or assertion.get("zodiac_sign") is not None:
            raise ValueError("Temporal-hour counts have no angular orientation")
    if "source_zodiac_sector" in assertion:
        sector = assertion["source_zodiac_sector"]
        sign = assertion.get("zodiac_sign")
        literal = assertion.get("source_expression", "").strip()
        match = re.fullmatch(
            r"(first|second|third) (?:face|decan)(?: ([A-Za-z]+|[♈♉♊♋♌♍♎♏♐♑♒♓]))?",
            literal,
        )
        if (
            not isinstance(sector, dict)
            or set(sector) != {"kind", "ordinal"}
            or sector["kind"] != "decan"
            or type(sector["ordinal"]) is not int
            or sector["ordinal"] not in (1, 2, 3)
            or assertion["quantity"] != "ecliptic_longitude"
            or assertion.get("role") != "historical_input"
            or assertion.get("components")
            or assertion.get("incomplete")
            or assertion.get("direction") is not None
            or sign not in ZODIAC_SIGNS
            or match is None
            or ("first", "second", "third").index(match[1]) + 1 != sector["ordinal"]
            or (match[2] is not None and match[2] not in (sign, ZODIAC_SIGNS[sign]))
            or "source_notation_unresolved" in assertion.get("flags", [])
        ):
            raise ValueError(
                "Zodiac sector requires matching literal ordinal and sign without a point value"
            )
        lower = (sector["ordinal"] - 1) * 10
        origin = 30 * tuple(ZODIAC_SIGNS).index(sign)
        result.update(
            unit="arcsecond",
            normalization_issue="coordinate_sector_not_scalar",
            zodiac_sign=sign,
            longitude_origin="start_of_named_sign",
            within_sign_range_degrees=[str(lower), str(lower + 10)],
            zodiac_longitude_range_degrees=[str(origin + lower), str(origin + lower + 10)],
            range_bounds="lower_inclusive_upper_exclusive",
        )
        return result
    if assertion.get("quantity") == "angular_area":
        components = assertion.get("components") or {}
        literal = fraction_text(assertion.get("source_expression", "")).strip()
        match = re.fullmatch(r"(\d+(?:\s+\d+/\d+|/\d+)?) square degrees?", literal)
        if (
            match is None
            or set(components) != {"scalar"}
            or number(match[1]) != number(fraction_text(components["scalar"]))
            or assertion.get("direction") is not None
            or assertion.get("zodiac_sign") is not None
            or assertion.get("reference") is not None
            or assertion.get("incomplete")
            or assertion.get("role") not in ("historical_input", "calculation_intermediate")
            or "not_an_additional_raw_reading" not in assertion.get("flags", [])
        ):
            raise ValueError("Sky area requires complete literal square-degree units")
        result.update(
            status="exact",
            magnitude=str(number(match[1])),
            unit="square_degree",
            least_component_unit="scalar",
        )
        return result
    if assertion.get("quantity") == "stellar_magnitude_class":
        result["unit"] = "source_visual_magnitude_class"
        components = assertion.get("components") or {}
        if assertion.get("direction") is not None or assertion.get("zodiac_sign") is not None:
            raise ValueError("Stellar magnitude classes have no angular orientation")
        if "source_notation_unresolved" in assertion.get("flags", []):
            if components or assertion.get("incomplete"):
                raise ValueError("Unresolved magnitude class cannot acquire a scalar")
            result["normalization_issue"] = "source_notation_unresolved"
            return result
        if assertion.get("incomplete"):
            if components:
                raise ValueError("Incomplete magnitude class cannot acquire a scalar")
            result["status"] = "incomplete"
            return result
        if not components:
            return result
        literal = assertion.get("source_expression", "")
        for word, value in assertion.get("source_word_numbers", {}).items():
            if SOURCE_WORD_NUMBERS.get(word) != value:
                raise ValueError("Unreviewed source word number")
            literal = re.sub(r"\b" + re.escape(word) + r"\b", value, literal)
        match = re.fullmatch(r"(\d+(?:\s+\d+/\d+|/\d+)?)[.:\-]?", fraction_text(literal).strip())
        if (
            set(components) != {"scalar"}
            or match is None
            or number(match[1]) != number(fraction_text(str(components["scalar"])))
            or number(match[1]) <= 0
        ):
            raise ValueError("Magnitude class requires its complete native numerical expression")
        result.update(
            status="exact", magnitude=str(number(match[1])), least_component_unit="scalar"
        )
        return result
    if assertion.get("quantity") == "unclassified_numeric_expression":
        if (
            assertion.get("components")
            or assertion.get("incomplete")
            or assertion.get("direction") is not None
        ):
            raise ValueError(
                "Unclassified numerical expression cannot choose component units or direction"
            )
        result.update(
            unit="source_numeric_expression",
            normalization_issue="physical_quantity_or_units_unresolved",
        )
        return result
    if "source_notation_unresolved" in assertion.get("flags", []):
        quantity = assertion.get("quantity")
        chord = unresolved_instrument_scalar(assertion)
        visual_fraction = unresolved_visual_fraction(assertion)
        distance = unresolved_source_distance(assertion)
        native_length = quantity == "source_sexagesimal_length"
        proportional = quantity == "proportional_minutes"
        clock = (
            quantity == "recorded_clock"
            and assertion.get("role") == "recorded_clock"
            and assertion.get("subject") == "observing clock"
            and assertion.get("reference") is None
            and assertion.get("direction") is None
            and "absolute_time_unestablished" in assertion.get("flags", [])
        )
        drift = (
            quantity == "clock_drift"
            and assertion.get("role") == "calibration"
            and assertion.get("subject") == "observing clock"
            and assertion.get("reference") is None
            and assertion.get("direction") is None
        )
        calculation_interval = (
            quantity == "clock_elapsed_time"
            and (
                assertion.get("role") == "historical_input"
                or (
                    assertion.get("role") == "historical_prediction"
                    and assertion.get("source_prediction_kind") == "eclipse_ephemeris"
                )
            )
            and assertion.get("subject") in HISTORICAL_INTERVAL_BODIES
            and assertion.get("reference") is None
            and assertion.get("direction") is None
            and {"not_an_observing_clock", "not_an_additional_raw_reading"}
            <= set(assertion.get("flags", []))
        )
        native_eclipse = (
            quantity == "eclipse_extent"
            and assertion.get("source_extent_unit") == "digit"
            and assertion.get("role") in ("historical_input", "historical_prediction")
            and assertion.get("subject") in ("Sun", "Moon", "Sun and Moon")
            and assertion.get("reference") is None
            and assertion.get("direction") is None
            and assertion.get("zodiac_sign") is None
            and {"not_an_observing_clock", "not_an_additional_raw_reading"}
            <= set(assertion.get("flags", []))
        )
        if (
            (
                quantity not in ANGLE_QUANTITIES | {"calculation_epoch", "temporal_hour_count"}
                and not clock
                and not drift
                and not calculation_interval
                and not native_eclipse
                and not chord
                and not visual_fraction
                and not distance
                and not native_length
                and not proportional
            )
            or assertion.get("components")
            or assertion.get("incomplete")
            or (
                (native_length or proportional)
                and (
                    assertion.get("direction") is not None
                    or assertion.get("zodiac_sign") is not None
                )
            )
        ):
            raise ValueError(
                "Unresolved notation requires reviewed angular, time or native units without interpreted components"
            )
        result.update(
            unit="source_temporal_hour"
            if quantity == "temporal_hour_count"
            else "source_fraction"
            if visual_fraction
            else "source_semidiameter"
            if distance
            else "source_length_part"
            if native_length
            else "ratio"
            if proportional
            else "source_eclipse_digit"
            if native_eclipse
            else "source_scalar"
            if chord
            else "second_of_time"
            if quantity == "calculation_epoch" or clock or drift or calculation_interval
            else ANGULAR_RATES.get(quantity, "arcsecond"),
            normalization_issue="source_notation_unresolved",
        )
        return result
    if assertion.get("incomplete"):
        quantity = assertion["quantity"]
        unit = (
            "source_temporal_hour"
            if quantity == "temporal_hour_count"
            else ANGULAR_RATES.get(quantity, "arcsecond")
            if quantity in ANGLE_QUANTITIES
            else "second_of_time"
            if quantity in TIME_QUANTITIES
            else None
        )
        result.update(status="incomplete", unit=unit)
        return result
    components = assertion.get("components")
    if not components:
        if (
            assertion.get("quantity") == "eclipse_extent"
            and assertion.get("source_extent_unit") == "digit"
        ):
            result["unit"] = "source_eclipse_digit"
        return result
    quantity = assertion["quantity"]
    if "ordinal_degree" in components or "ordinal_degree_evidence" in assertion:
        evidence = assertion.get("ordinal_degree_evidence")
        literal = re.fullmatch(
            r"(\d+)′ of the (\d+)(?:st|nd|rd|th) degree of ([A-Za-z]+)(?: [♈♉♊♋♌♍♎♏♐♑♒♓])?",
            assertion.get("source_expression", ""),
        )
        if (
            quantity != "ecliptic_longitude"
            or set(components) != {"ordinal_degree", "arcminute"}
            or not literal
            or not isinstance(evidence, dict)
            or set(evidence) != {"line", "expression"}
            or type(evidence["line"]) is not int
            or assertion.get("direction") is not None
            or assertion.get("zodiac_sign") != literal[3]
            or str(components["ordinal_degree"]) != literal[2]
            or str(components["arcminute"]) != literal[1]
            or not 1 <= int(literal[2]) <= 30
            or not 0 <= int(literal[1]) < 60
            or evidence["expression"] != f"{int(literal[2]) - 1}° {literal[1]}′ of {literal[3]}"
        ):
            raise ValueError("Ordinal longitude lacks matching explicit source coordinate")
        interpreted = dict(assertion)
        interpreted.pop("ordinal_degree_evidence")
        interpreted["components"] = {"degree": str(int(literal[2]) - 1), "arcminute": literal[1]}
        result = normalize_quantity(interpreted)
        result.update(
            source_ordinal_degree=literal[2],
            ordinal_degree_interpretation="completed_degrees_before_named_ordinal",
        )
        return result
    if "source_angular_units_unresolved" in assertion:
        if (
            assertion["source_angular_units_unresolved"] is not True
            or quantity not in ("calculation_angle", "parallax_angle", "angular_diameter")
            or assertion.get("direction") is not None
            or assertion.get("zodiac_sign") is not None
            or not 2 <= len(components) <= 4
            or set(components) != {f"component_{n}" for n in range(1, len(components) + 1)}
        ):
            raise ValueError("Invalid unresolved angular components")
        values = []
        for n in range(1, len(components) + 1):
            token = fraction_text(components[f"component_{n}"]).strip()
            if not re.fullmatch(r"\d+(?:/\d+)?(?:\s+\d+/\d+)?", token):
                raise ValueError("Invalid unresolved component number")
            values.append(str(number(token)))
        result.update(
            unit="arcsecond",
            source_components=values,
            normalization_issue="angular_component_units_unresolved",
        )
        return result
    if quantity == "source_sexagesimal_length":
        units = ("source_part", "part_minute", "part_second")
        if (
            not set(components) <= set(units)
            or not components
            or assertion.get("direction") is not None
            or assertion.get("zodiac_sign") is not None
        ):
            raise ValueError("Native length requires unsigned sexagesimal parts")
        values = [number(fraction_text(components.get(u, "0"))) for u in units]
        if values[0] < 0 or any(not 0 <= v < 60 for v in values[1:]):
            raise ValueError("Native length component out of range")
        result.update(
            status="exact",
            unit="source_length_part",
            magnitude=str(values[0] + values[1] / 60 + values[2] / 3600),
            least_component_unit=next(u for u in reversed(units) if u in components),
        )
        return result
    if quantity == "source_scale_ratio":
        if (
            set(components) != {"source_part", "reference_scale"}
            or assertion.get("direction") is not None
            or assertion.get("zodiac_sign") is not None
        ):
            raise ValueError("Invalid source-scale components or orientation")
        values = {}
        for unit, token in components.items():
            token = fraction_text(token).strip()
            if not re.fullmatch(r"\d+(?:/\d+)?(?:\s+\d+/\d+)?", token):
                raise ValueError("Invalid source-scale number")
            values[unit] = number(token)
        part, whole = values["source_part"], values["reference_scale"]
        if part < 0 or whole <= 0:
            raise ValueError("Invalid relative source scale")
        result.update(
            status="exact",
            magnitude=str(part / whole),
            unit="ratio",
            least_component_unit="source_part",
            source_scale_part=str(part),
            source_reference_scale=str(whole),
        )
        return result
    if quantity == "proportional_minutes":
        if (
            not set(components)
            <= {"proportional_minute", "proportional_second", "proportional_third"}
            or assertion.get("direction") is not None
            or assertion.get("zodiac_sign") is not None
        ):
            raise ValueError("Invalid proportional-minute components or orientation")
        values = {}
        for unit, token in components.items():
            token = fraction_text(token).strip()
            if not re.fullmatch(r"\d+(?:/\d+)?(?:\s+\d+/\d+)?", token):
                raise ValueError("Invalid proportional component")
            values[unit] = number(token)
        minute = values.get("proportional_minute", Fraction())
        second = values.get("proportional_second", Fraction())
        third = values.get("proportional_third", Fraction())
        ratio = minute / 60 + second / 3600 + third / 216000
        second_limit = 60 if "proportional_minute" in components else 3601
        third_limit = (
            60 if {"proportional_minute", "proportional_second"} & set(components) else 216001
        )
        if (
            not 0 <= minute <= 60
            or not 0 <= second < second_limit
            or not 0 <= third < third_limit
            or ratio > 1
        ):
            raise ValueError("Proportional component out of range")
        result.update(
            status="exact",
            magnitude=str(ratio),
            unit="ratio",
            least_component_unit="proportional_third"
            if "proportional_third" in components
            else "proportional_second"
            if "proportional_second" in components
            else "proportional_minute",
        )
        return result
    if quantity == "angle_component":
        if (
            set(components) not in ({"degree"}, {"arcminute"})
            or assertion.get("direction") is not None
            or assertion.get("zodiac_sign") is not None
        ):
            raise ValueError("Unreviewed angle-component unit or orientation")
        component = next(iter(components))
        token = fraction_text(components[component]).strip()
        if not re.fullmatch(r"\d+(?:/\d+)?(?:\s+\d+/\d+)?", token):
            raise ValueError("Invalid unsigned angle component")
        result.update(
            status="exact",
            magnitude=str(number(token)),
            unit="source_angle_component",
            least_component_unit=component,
        )
        return result
    if quantity == "clock_component":
        if (
            set(components) != {"minute"}
            or assertion.get("direction") is not None
            or assertion.get("zodiac_sign") is not None
        ):
            raise ValueError("Unreviewed clock-component unit or orientation")
        token = fraction_text(components["minute"]).strip()
        if not re.fullmatch(r"\d+(?:/\d+)?(?:\s+\d+/\d+)?", token):
            raise ValueError("Invalid unsigned clock component")
        result.update(
            status="exact",
            magnitude=str(number(token)),
            unit="source_clock_component",
            least_component_unit="minute",
        )
        return result
    if quantity == "eclipse_extent":
        if assertion.get("source_extent_unit") == "digit":
            literal = (
                " ".join(f["source_expression"] for f in assertion["source_fragments"])
                if "source_fragments" in assertion
                else assertion.get("source_expression", "")
            ).strip()
            for word, value in assertion.get("source_word_numbers", {}).items():
                if SOURCE_WORD_NUMBERS.get(word) != value:
                    raise ValueError("Unreviewed source word number")
                literal = re.sub(r"\b" + re.escape(word) + r"\b", value, literal)
            literal = fraction_text(literal).strip()
            separator = r"(?:\s*,\s*|\s+)"
            minute = r"(?P<minute>\d+)(?:′|\s+minutes?)"
            second = r"(?P<second>\d+)(?:″|\s+seconds?)"
            subunits = minute + "(?:" + separator + second + ")?"
            patterns = (
                r"(?P<digit>\d+)\s+digits?(?:" + separator + subunits + ")?",
                r"(?P<digit>\d+)\.(?P<minute>\d+)′\s+(?P<second>\d+)″",
                subunits,
                second,
            )
            if isinstance(assertion.get("unit_basis"), str) and assertion["unit_basis"].strip():
                tabular_separator = r"(?:\s*\|\s*|\s+)"
                native_digit = r"\d+(?:\s+\d+/\d+|/\d+)?"
                patterns += (
                    r"(?P<digit>\d+)"
                    + tabular_separator
                    + r"(?P<minute>\d+)"
                    + "(?:"
                    + tabular_separator
                    + r"(?P<second>\d+))?",
                    r"(?P<digit>\d+)",
                    r"(?P<digit>"
                    + native_digit
                    + r")(?:\s+(?:T\.\s+)?(?P<minute>\d+)′)?(?:\s+(?:Tot\.|T\.))?",
                )
            match = next((m for pattern in patterns if (m := re.fullmatch(pattern, literal))), None)
            if (
                not match
                or assertion.get("direction") is not None
                or assertion.get("zodiac_sign") is not None
            ):
                raise ValueError("Eclipse digits require literal native sexagesimal units")
            places = match.groupdict()
            minute, second = places.get("minute"), places.get("second")
            expected = {"digit": places["digit"]} if places.get("digit") is not None else {}
            if minute is not None:
                expected["digit_minute"] = minute
            if second is not None:
                expected["digit_second"] = second
            if (
                components != expected
                or not 0 <= int(minute or "0") < 60
                or not 0 <= int(second or "0") < 60
            ):
                raise ValueError("Eclipse digit components differ from their source")
            result.update(
                status="exact",
                unit="source_eclipse_digit",
                magnitude=str(
                    number(places.get("digit") or "0")
                    + Fraction(int(minute or "0"), 60)
                    + Fraction(int(second or "0"), 3600)
                ),
                least_component_unit="digit_second"
                if second is not None
                else "digit_minute"
                if minute is not None
                else "digit",
            )
            return result
        if "source_extent_unit" in assertion:
            raise ValueError("Unknown native eclipse extent unit")
        if assertion.get("role") == "recorded_reading":
            match = re.fullmatch(
                r"(\d+(?:\s+\d+/\d+)?)(?:\s+(\d+))?",
                fraction_text(assertion.get("source_expression", "")).strip(),
            )
            expected = {"point": match[1]} if match else {}
            if match and match[2] is not None:
                expected["point_minute"] = match[2]
            if (
                not match
                or "source_visual_estimate" not in assertion.get("flags", [])
                or not assertion.get("unit_basis")
                or components != expected
                or assertion.get("direction") is not None
                or assertion.get("zodiac_sign") is not None
                or not 0 <= int(match[2] or "0") < 60
            ):
                raise ValueError("Observed eclipse digits require literal native components")
            result.update(
                status="exact",
                unit="source_eclipse_point",
                magnitude=str(number(match[1]) + Fraction(int(match[2] or "0"), 60)),
                least_component_unit="point_minute" if match[2] is not None else "point",
            )
            return result
        match = re.fullmatch(
            r"(\d+)\s+points?\s+(\d+)′", assertion.get("source_expression", "").strip()
        )
        if (
            not match
            or set(components) != {"point", "point_minute"}
            or assertion.get("direction") is not None
            or assertion.get("zodiac_sign") is not None
            or any(str(components[k]) != match[i] for i, k in ((1, "point"), (2, "point_minute")))
            or not 0 <= int(match[2]) < 60
        ):
            raise ValueError("Eclipse points require literal points and sexagesimal minutes")
        result.update(
            status="exact",
            magnitude=str(Fraction(int(match[1])) + Fraction(int(match[2]), 60)),
            unit="source_eclipse_point",
            least_component_unit="point_minute",
        )
        return result
    if quantity in ("correction_ratio", "separation_ratio", "source_fraction", "source_scalar"):
        component = {"source_fraction": "fraction", "source_scalar": "scalar"}.get(
            quantity, "ratio"
        )
        if (
            set(components) != {component}
            or assertion.get("direction") is not None
            or assertion.get("zodiac_sign") is not None
        ):
            raise ValueError("Invalid correction ratio units or orientation")
        token = fraction_text(components[component]).strip()
        if not re.fullmatch(r"\d+(?:/\d+)?(?:\s+\d+/\d+)?", token):
            raise ValueError("Invalid unsigned correction ratio")
        result.update(
            status="exact",
            magnitude=str(number(token)),
            unit=quantity if quantity in ("source_fraction", "source_scalar") else "ratio",
            least_component_unit=component,
        )
        return result
    if quantity in ("distance_in_paces", "distance_in_stadia"):
        if (
            set(components) != {"scalar"}
            or assertion.get("direction") is not None
            or assertion.get("zodiac_sign") is not None
        ):
            raise ValueError("Paces require one unsigned native count")
        value, _ = native_distance_value(components, ("scalar",))
        if quantity == "distance_in_stadia":
            literal = re.fullmatch(
                r"(\d+(?:\s+\d+/\d+|/\d+)?) stadia",
                fraction_text(assertion.get("source_expression", "")).strip(),
            )
            if (
                literal is None
                or number(literal[1]) != value
                or assertion.get("role") not in ("historical_input", "calculation_intermediate")
            ):
                raise ValueError("Stadia require their complete literal native unit and count")
        result.update(
            status="exact",
            magnitude=str(value),
            unit="source_stadium" if quantity == "distance_in_stadia" else "source_pace",
            least_component_unit="scalar",
        )
        return result
    if quantity in SOURCE_MILE_UNITS:
        if assertion.get("direction") is not None or assertion.get("zodiac_sign") is not None:
            raise ValueError("Historical mile distance requires unsigned native length")
        if set(components) == {"scalar"}:
            value = number(fraction_text(components["scalar"]))
            least = "scalar"
        else:
            value, least = native_distance_value(components, ("mile", "mile_minute", "mile_second"))
        if value < 0:
            raise ValueError("Historical mile distance cannot be negative")
        result.update(
            status="exact",
            magnitude=str(value),
            unit=SOURCE_MILE_UNITS[quantity],
            least_component_unit=least,
        )
        return result
    if quantity == "distance_in_semidiameters":
        if assertion.get("direction") is not None or assertion.get("zodiac_sign") is not None:
            raise ValueError("Invalid source-distance units or orientation")
        value, least = native_distance_value(
            components, ("semidiameter", "semidiameter_minute", "semidiameter_second")
        )
        result.update(
            status="exact",
            magnitude=str(value),
            unit="source_semidiameter",
            least_component_unit=least,
        )
        return result
    if quantity in ANGLE_QUANTITIES:
        units = (
            ("sign_count", "degree", "arcminute", "arcsecond")
            if "sign_count" in components
            else ("sexagena", "degree", "arcminute", "arcsecond")
            if "sexagena" in components
            else ("degree", "arcminute", "arcsecond")
        )
        units += (
            "arcsexagesimal_third",
            "arcsexagesimal_fourth",
            "arcsexagesimal_fifth",
            "arcsexagesimal_sixth",
            "arcsexagesimal_seventh",
            "arcsexagesimal_eighth",
            "arcsexagesimal_ninth",
            "arcsexagesimal_tenth",
        )
        base = ANGULAR_RATES.get(quantity, "arcsecond")
    elif quantity in TIME_QUANTITIES:
        native_calculation_days = (
            quantity == "calculation_epoch"
            and assertion.get("role") == "calculation_epoch"
            and assertion.get("subject") in ("Sun", "Moon")
            and {"not_an_additional_raw_reading", "not_an_observing_clock"}
            <= set(assertion.get("flags", []))
        )
        fractional_day = quantity == "clock_elapsed_time" and bool(
            set(DAY_FRACTION_UNITS) & set(components)
        )
        units = (
            ("day", *DAY_FRACTION_UNITS)
            if fractional_day
            else ("day", "hour", "minute", "second", "time_third", "time_fourth", "time_fifth")
            if (quantity == "clock_elapsed_time" or native_calculation_days) and "day" in components
            else ("hour", "minute", "second", "time_third", "time_fourth", "time_fifth")
        )
        base = "source_temporal_hour" if quantity == "temporal_hour_count" else "second_of_time"
    else:
        return result
    if not set(components) <= set(units):
        raise ValueError("Quantity/component unit mismatch")
    total = Fraction()
    degree_outside_sign = False
    first_written = next((i for i, unit in enumerate(units) if unit in components), 0)
    for index, unit in enumerate(units):
        if unit not in components:
            continue
        token = fraction_text(components[unit]).strip()
        if not re.fullmatch(r"\d+(?:/\d+)?(?:\s+\d+/\d+)?", token):
            raise ValueError("Invalid unsigned component")
        value = number(token)
        limit = 24 if unit == "hour" and "day" in components else 60
        leading_unbounded = (
            quantity
            in (
                "clock_elapsed_time",
                "clock_correction",
                "temporal_hour_count",
                "right_ascension_difference",
            )
            or quantity in ANGLE_QUANTITIES
            or quantity in ANGULAR_RATES
        ) and index == first_written
        noncanonical_degree = unit == "degree" and "sign_count" in components and value > 30
        degree_outside_sign = degree_outside_sign or noncanonical_degree
        if value < 0 or (
            index > 0 and not leading_unbounded and not noncanonical_degree and value >= limit
        ):
            raise ValueError("Component out of range")
        total += (
            value
            * {
                "sign_count": 108000,
                "sexagena": 216000,
                "day": 86400,
                "day_minute": 1440,
                "day_second": 24,
                "day_third": Fraction(2, 5),
                "day_fourth": Fraction(1, 150),
                "day_fifth": Fraction(1, 9000),
                "day_sixth": Fraction(1, 540000),
                "degree": 3600,
                "hour": 3600,
                "arcminute": 60,
                "minute": 60,
                "arcsecond": 1,
                "arcsexagesimal_third": Fraction(1, 60),
                "arcsexagesimal_fourth": Fraction(1, 3600),
                "arcsexagesimal_fifth": Fraction(1, 60**3),
                "arcsexagesimal_sixth": Fraction(1, 60**4),
                "arcsexagesimal_seventh": Fraction(1, 60**5),
                "arcsexagesimal_eighth": Fraction(1, 60**6),
                "arcsexagesimal_ninth": Fraction(1, 60**7),
                "arcsexagesimal_tenth": Fraction(1, 60**8),
                "second": 1,
                "time_third": Fraction(1, 60),
                "time_fourth": Fraction(1, 3600),
                "time_fifth": Fraction(1, 216000),
            }[unit]
        )
        result["least_component_unit"] = unit
    if degree_outside_sign:
        result.update(
            status="unsupported",
            unit=base,
            normalization_issue="degree_outside_sign",
            source_components=[
                str(number(fraction_text(components[u]))) for u in units if u in components
            ],
        )
        return result
    if quantity == "temporal_hour_count":
        total /= 3600
    result.update(status="exact", magnitude=str(total), unit=base)
    if base == "arcsecond":
        result["magnitude_degrees"] = str(total / 3600)
        if assertion.get("direction") in ("north", "south"):
            result["signed_magnitude"] = str(
                total * (-1 if assertion["direction"] == "south" else 1)
            )
    sign = assertion.get("zodiac_sign")
    if sign is not None:
        if "sexagena" in components or "sign_count" in components:
            raise ValueError("Angular counts are not named zodiac signs")
        if (
            quantity not in ("ecliptic_longitude", "orbital_longitude")
            or sign not in ZODIAC_SIGNS
            or assertion.get("direction") is not None
        ):
            raise ValueError("Invalid sign-relative longitude interpretation")
        result.update(
            zodiac_sign=sign,
            longitude_origin="start_of_named_sign",
        )
        if total > 30 * 3600:
            result.update(
                status="unsupported",
                magnitude=None,
                signed_magnitude=None,
                magnitude_degrees=None,
                normalization_issue="degree_outside_sign",
                source_components=[
                    str(number(fraction_text(components[u]))) for u in units if u in components
                ],
            )
        else:
            result["zodiac_longitude_degrees"] = str(
                total / 3600 + 30 * tuple(ZODIAC_SIGNS).index(sign)
            )
    return result


def zodiac_arithmetic_values(norms):
    """Explicit opt-in conversion for arithmetic in the common zodiac frame."""
    if any(
        n["unit"] != "arcsecond" or n.get("status") != "exact" or n.get("magnitude") is None
        for n in norms
    ) or not any("zodiac_sign" in n for n in norms):
        raise ValueError("Zodiac-frame arithmetic requires angles and a named zodiac origin")
    values = []
    for n in norms:
        value = Fraction(n["magnitude"])
        if "zodiac_sign" in n:
            sign = n["zodiac_sign"]
            if sign not in ZODIAC_SIGNS or n.get("longitude_origin") != "start_of_named_sign":
                raise ValueError("Unestablished zodiac origin")
            absolute = Fraction(n["zodiac_longitude_degrees"]) * 3600
            if absolute != value + tuple(ZODIAC_SIGNS).index(sign) * 108000:
                raise ValueError("Inconsistent zodiac-relative and absolute values")
            value = absolute
        values.append(value)
    return values
