"""Resolve only explicitly reviewed, vertically carried table components."""

import re

from .core import fraction_text


def carry_unit_matches(quantity, unit):
    """Keep angular and native proportional leading places dimensionally distinct."""
    from .normalization import ANGLE_QUANTITIES

    return (quantity in ANGLE_QUANTITIES and unit in ("degree", "arcminute", "arcsecond")) or (
        quantity == "proportional_minutes" and unit == "proportional_minute"
    )


def table_carry_origin(row, review, lines):
    """Return the nearest printed leading component inside a source-bound scope."""
    from .assembly import cell_intervals

    declaration = row.get("table_carry")
    columns = row.get("source_columns")
    if (
        not isinstance(declaration, dict)
        or set(declaration) != {"rule_key", "unit", "column"}
        or not carry_unit_matches(row.get("quantity"), declaration.get("unit"))
        or row.get("column") is not None
        or row.get("inherited_components")
        or row.get("source_component_addends")
        or row.get("source_fragments")
        or not isinstance(columns, list)
        or len(columns) < 2
        or any(type(c) is not int for c in columns)
        or columns != list(range(columns[0], columns[-1] + 1))
        or type(declaration.get("column")) is not int
        or declaration["column"] != columns[0]
        or declaration.get("rule_key") not in row.get("context_keys", [])
    ):
        raise ValueError("Table carry requires one reviewed leading angular or proportional column")
    context = next(
        (c for c in review.get("contexts", []) if c["key"] == declaration["rule_key"]),
        None,
    )
    value = context.get("value") if context else None
    locus = context.get("lines", []) if context else []
    if (
        context is None
        or context.get("kind") != "source_observation_context"
        or len(locus) != 1
        or type(locus[0]) is not int
        or not isinstance(value, dict)
        or set(value) != {"record_type", "line_start", "line_end", "source_expression"}
        or value.get("record_type") != "source_table_carry_rule"
        or any(type(value.get(k)) is not int for k in ("line_start", "line_end"))
        or not review["line_start"]
        <= locus[0]
        < value["line_start"]
        <= row["line"]
        <= value["line_end"]
        <= review["line_end"]
        or not isinstance(value.get("source_expression"), str)
        or len(value["source_expression"]) < 20
        or value["source_expression"] not in lines[locus[0] - 1]
        or not all(
            s.lstrip().startswith("|") for s in lines[value["line_start"] - 1 : value["line_end"]]
        )
    ):
        raise ValueError("Table carry lacks an explicit bound rule and uninterrupted table scope")
    column = declaration["column"]
    for line in range(row["line"], value["line_start"] - 1, -1):
        text = lines[line - 1]
        slots = cell_intervals(text, declared_table=True)
        if not 1 <= column <= len(slots):
            raise ValueError("Table carry column outside source table")
        left, right = slots[column - 1]
        literal = text[left:right].strip()
        if not literal:
            continue
        # A separate proposal never replaces the printed origin carried below it.
        if re.fullmatch(r".+?\s+\[recte: \d+(?:/\d+)?(?:\s+\d+/\d+)?\]", fraction_text(literal)):
            literal = re.sub(r"\s+\[recte: .+\]$", "", literal)
        if not re.fullmatch(r"\d+(?:/\d+)?(?:\s+\d+/\d+)?", fraction_text(literal)):
            raise ValueError("Table carry encountered an unresolved or nonnumeric leading cell")
        return dict(
            unit=declaration["unit"],
            source_expression=literal,
            source_line=line,
            source_column=column,
            rule_key=declaration["rule_key"],
        )
    raise ValueError("Table carry has no printed origin inside its reviewed scope")
