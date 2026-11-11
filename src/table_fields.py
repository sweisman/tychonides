"""Expand explicitly reviewed native coordinate fields in physical table rows."""

import re

from .normalization import ZODIAC_SIGNS, fraction_text
from .table_relationships import literal_label
from .table_staging import main_text, split_cells


def apply_clock_fields(row, declaration, text):
    """Select a reviewed H/M suffix without interpreting or inheriting its date."""
    from .assembly import cell_intervals

    context = row.get("row_context")
    column = row.get("column")
    if (
        not isinstance(declaration, dict)
        or set(declaration) != {"separator", "absent_values"}
        or declaration["separator"] not in ("·", ":")
        or not isinstance(declaration["absent_values"], list)
        or row.get("quantity")
        not in {
            "recorded_clock",
            "transit_clock",
            "annotated_time",
            "calculation_epoch",
            "expected_clock",
        }
        or row.get("component_units") != ["hour", "minute"]
        or type(column) is not int
        or any(k in row for k in ("char_start", "char_end", "source_columns", "source_fragments"))
        or not text.lstrip().startswith("|")
        or not isinstance(context, dict)
        or not isinstance(context.get("columns"), dict)
        or column not in context["columns"].values()
    ):
        raise ValueError("Clock fields require a reviewed physical H/M date-clock column")
    separator = declaration["separator"]
    absent = declaration["absent_values"]
    # Retain native labels, including anomalous days; do not validate a calendar.
    day = r"\d{1,2}"
    month = r"[^\W\d_]+\.?\s*"
    if any(
        not isinstance(value, str)
        or len(value) > 150
        or "\n" in value
        or "\r" in value
        or separator in value
        or (
            any(c.isdigit() for c in value)
            and (
                re.fullmatch(month + day, value) is None
                or re.search(r"\b(?:horae?|hours?|minutes?|seconds?|[hms])(?=\W|\d|$)", value, re.I)
            )
        )
        for value in absent
    ) or len(set(absent)) != len(absent):
        raise ValueError("Absent clocks require explicit nonnumeric or month/day labels")
    slots = cell_intervals(text, declared_table=True)
    if not 1 <= column <= len(slots):
        raise ValueError("Clock column is outside the physical table")
    left, right = slots[column - 1]
    native = text[left:right]
    if row["source_expression"] != main_text(native):
        raise ValueError("Clock fields cannot replace an independently selected expression")
    if native.strip() in absent:
        return False
    marks = list(re.finditer(re.escape(separator), native))
    if len(marks) not in (1, 2):
        raise ValueError("Clock fields require a complete hour/minute suffix")
    if (
        len(marks) == 2
        and re.fullmatch(rf"(?:{month})?{day}", native[: marks[0].start()].strip()) is None
    ):
        raise ValueError("Clock prefix must retain a native month/day or day label")
    hour_start = marks[0].end() if len(marks) == 2 else 0
    hour = native[hour_start : marks[-1].start()]
    minute = native[marks[-1].end() :]
    number = r"\d+(?:\s+\d+/\d+|/\d+)?"
    if any(re.fullmatch(number, fraction_text(v).strip()) is None for v in (hour, minute)):
        raise ValueError("Clock fields require complete unsigned hour/minute components")
    start = left + hour_start + len(hour) - len(hour.lstrip())
    end = left + len(native.rstrip())
    row.update(source_expression=text[start:end], char_start=start, char_end=end)
    return True


def apply_table_fields(row, declaration, text):
    """Read only the declared fields; preserve their literal row evidence."""
    allowed = {
        "subject_column",
        "subject_prefix",
        "direction_column",
        "direction_suffixes",
        "direction_prefixes",
        "unmarked_direction",
        "zodiac_from_expression",
        "value_before",
    }
    context = row.get("row_context")
    column = row.get("column")
    label_only = isinstance(declaration, dict) and set(declaration) <= {
        "subject_column",
        "subject_prefix",
    }
    split_fields = isinstance(declaration, dict) and set(declaration) <= {
        "subject_column",
        "subject_prefix",
        "direction_column",
        "direction_suffixes",
        "unmarked_direction",
    }
    split_value = "source_columns" in row
    if (
        not isinstance(declaration, dict)
        or not declaration
        or set(declaration) - allowed
        or row.get("quantity")
        not in {
            "declination",
            "altitude",
            "right_ascension",
            "ecliptic_longitude",
            "ecliptic_latitude",
            "stellar_magnitude_class",
        }
        or (row.get("quantity") == "stellar_magnitude_class" and not label_only)
        or (not split_value and type(column) is not int)
        or (split_value and (column is not None or not split_fields))
        or not text.lstrip().startswith("|")
        or "source_fragments" in row
        or (not split_value and any(key in row for key in ("char_start", "char_end")))
        or not isinstance(context, dict)
        or not isinstance(context.get("columns"), dict)
    ):
        raise ValueError(
            "Table fields require reviewed physical coordinate columns and row evidence"
        )
    cells = split_cells(text)
    if not split_value and not 1 <= column <= len(cells):
        raise ValueError("Coordinate value column is outside the table")
    prefix = declaration.get("subject_prefix")
    if "subject_prefix" in declaration and (
        "subject_column" not in declaration
        or not isinstance(prefix, str)
        or not prefix.strip()
        or len(prefix) > 160
        or "\n" in prefix
        or "\r" in prefix
    ):
        raise ValueError("Native subject prefix requires a reviewed scope and label column")
    if "unmarked_direction" in declaration and (
        declaration["unmarked_direction"] != "unknown" or "direction_suffixes" not in declaration
    ):
        raise ValueError("Unmarked direction can only remain unknown under a suffix policy")
    if "subject_column" in declaration:
        source_column = declaration["subject_column"]
        if (
            type(source_column) is not int
            or not 1 <= source_column <= len(cells)
            or source_column not in context["columns"].values()
        ):
            raise ValueError("Native subject column requires retained literal evidence")
        if prefix is None:
            subject = main_text(cells[source_column - 1])
        else:
            label = literal_label(cells[source_column - 1])
            subject = f"{prefix.strip()}: {label}" if label else ""
        if not subject or row.get("subject") not in (None, subject):
            raise ValueError("Native table subject conflicts with its declared target")
        row["subject"] = subject
    if "direction_column" in declaration:
        policy = declaration["direction_column"]
        if not isinstance(policy, dict) or set(policy) != {"column", "values"}:
            raise ValueError("A separate hemisphere needs a reviewed column and value map")
        source_column, mapping = policy["column"], policy["values"]
        if (
            row["quantity"] not in {"declination", "ecliptic_latitude"}
            or "direction_suffixes" in declaration
            or "direction_prefixes" in declaration
            or type(source_column) is not int
            or not 1 <= source_column <= len(cells)
            or source_column not in context["columns"].values()
            or not isinstance(mapping, dict)
            or not mapping
            or any(key not in {"", "A", "B", "N", "S"} for key in mapping)
            or any(
                value is not None if key == "" else value not in {"north", "south"}
                for key, value in mapping.items()
            )
        ):
            raise ValueError("Separate hemisphere requires coordinate units and retained evidence")
        label = literal_label(cells[source_column - 1])
        if label not in mapping or row.get("direction") not in (None, mapping[label]):
            raise ValueError(
                "Printed hemisphere is unknown or conflicts with the declared direction"
            )
        row["direction"] = mapping[label]
    if "value_before" in declaration:
        if declaration["value_before"] != ";" or column not in context["columns"].values():
            raise ValueError("A separated coordinate needs its complete source cell retained")
        expression = row["source_expression"]
        if ";" in expression:
            parts = expression.split(";")
            if len(parts) != 2 or any(not part.strip() for part in parts):
                raise ValueError("Multiple or empty coordinate fields need an explicit review")
            row["source_expression"] = parts[0].strip()
    if "direction_suffixes" in declaration:
        mapping = declaration["direction_suffixes"]
        if (
            row["quantity"] not in {"declination", "ecliptic_latitude"}
            or "direction_prefixes" in declaration
            or not isinstance(mapping, dict)
            or not mapping
            or any(key not in {"A", "B", "N", "S"} for key in mapping)
            or any(value not in {"north", "south"} for value in mapping.values())
        ):
            raise ValueError("Hemisphere suffixes need a reviewed coordinate convention")
        match = re.search(r"\s+([ABNS])$", row["source_expression"])
        if (
            match is None
            and declaration.get("unmarked_direction") == "unknown"
            and row.get("direction") is None
            and re.fullmatch(r"[\d\s/|°′″.,:·]+", fraction_text(row["source_expression"]))
        ):
            direction = None
        elif match is None or match[1] not in mapping:
            raise ValueError("Missing or unknown hemisphere suffix requires source review")
        else:
            direction = mapping[match[1]]
        if row.get("direction") not in (None, direction):
            raise ValueError("Printed hemisphere conflicts with the declared direction")
        row["direction"] = direction
    if "direction_prefixes" in declaration:
        mapping = declaration["direction_prefixes"]
        if (
            row["quantity"] not in {"declination", "ecliptic_latitude"}
            or not isinstance(mapping, dict)
            or not mapping
            or any(key not in {"A", "B", "N", "S", "North", "South"} for key in mapping)
            or any(value not in {"north", "south"} for value in mapping.values())
        ):
            raise ValueError("Hemisphere prefixes need a reviewed coordinate convention")
        match = re.match(
            r"^(North|South|[ABNS])\s+(?=\d|[¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])", row["source_expression"]
        )
        if (
            match is None
            or match[1] not in mapping
            or re.search(r"\b(?:North|South|[ABNS])\b", row["source_expression"][match.end() :])
        ):
            raise ValueError(
                "Missing, conflicting or unknown hemisphere prefix requires source review"
            )
        direction = mapping[match[1]]
        if row.get("direction") not in (None, direction):
            raise ValueError("Printed hemisphere conflicts with the declared direction")
        row["direction"] = direction
    if "zodiac_from_expression" in declaration:
        if (
            declaration["zodiac_from_expression"] is not True
            or row["quantity"] != "ecliptic_longitude"
        ):
            raise ValueError("Literal zodiac fields require a longitude and explicit opt-in")
        signs = {name for name, glyph in ZODIAC_SIGNS.items() if glyph in row["source_expression"]}
        if len(signs) != 1:
            raise ValueError("Missing or conflicting literal zodiac signs require source review")
        sign = next(iter(signs))
        if row.get("zodiac_sign") not in (None, sign) or any(
            key in row for key in ("zodiac_sign_basis_key", "zodiac_sign_inherited_from_key")
        ):
            raise ValueError("Literal zodiac sign conflicts with its declared coordinate origin")
        row["zodiac_sign"] = sign
