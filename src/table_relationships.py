"""Bind reviewed table labels and authority conventions without using values."""

import re

from .table_staging import split_cells


def literal_label(value):
    """Remove markup while retaining uncertainty and editorial annotations."""
    return value.replace("*", "").replace("`", "").strip()


def apply_table_relationships(row, rule, authorities, lines, state):
    """Return source context after binding a declared pair and authority."""
    allowed = {
        "label_column",
        "authority_policy",
        "context_prefix",
        "pairs",
        "subject",
        "reference_labels",
        "literal_references",
    }
    context = row.get("row_context")
    if (
        not isinstance(rule, dict)
        or set(rule) - allowed
        or row.get("quantity") != "angular_separation"
        or row.get("direction") is not None
        or not isinstance(context, dict)
        or not isinstance(context.get("columns"), dict)
        or not isinstance(rule.get("context_prefix"), str)
        or re.fullmatch(r"[a-z][a-z0-9-]{0,63}", rule["context_prefix"]) is None
    ):
        raise ValueError("Relationships require reviewed separation columns and row evidence")
    authority = authorities.get(rule.get("authority_policy"))
    if (
        not isinstance(authority, dict)
        or set(authority) != {"column", "repeat", "values"}
        or not isinstance(authority["repeat"], list)
        or any(not isinstance(v, str) for v in authority["repeat"])
        or not isinstance(authority["values"], dict)
    ):
        raise ValueError("Missing or invalid reviewed table authority policy")
    line = row["line"]
    text = lines[line - 1]
    if not text.lstrip().startswith("|"):
        raise ValueError("Table relationships need a physical table row")
    cells = split_cells(text)
    label_column, authority_column = rule.get("label_column"), authority["column"]
    heading_authority = authority_column is None
    if heading_authority and (authority["repeat"] or set(authority["values"]) != {""}):
        raise ValueError("Heading authority requires one explicit role and no repetitions")
    evidence_columns = (label_column,) if heading_authority else (label_column, authority_column)
    if label_column == authority_column or any(
        type(c) is not int or not 1 <= c <= len(cells) or c not in context["columns"].values()
        for c in evidence_columns
    ):
        raise ValueError("Relationship columns require retained literal evidence")
    if "last_line" in state and (
        line <= state["last_line"]
        or (
            (
                not literal_label(cells[label_column - 1])
                or (
                    not heading_authority
                    and literal_label(cells[authority_column - 1]) in authority["repeat"]
                )
            )
            and any(
                t.strip() and not t.lstrip().startswith("|")
                for t in lines[state["last_line"] : line - 1]
            )
        )
    ):
        raise ValueError("Relationship inheritance crosses a non-table source boundary")
    label = literal_label(cells[label_column - 1])
    if label:
        if "pairs" in rule:
            if not isinstance(rule["pairs"], dict):
                raise ValueError("Reviewed endpoint pairs must be a mapping")
            if any(k in rule for k in ("subject", "reference_labels", "literal_references")):
                raise ValueError("Choose paired labels or one fixed principal star")
            pair = rule["pairs"].get(label)
        else:
            references = rule.get("reference_labels")
            reference = (
                references.get(label)
                if isinstance(references, dict)
                else label
                if rule.get("literal_references") is True
                else None
            )
            pair = dict(subject=rule.get("subject"), reference=reference)
        pair_line = line
    else:
        pair, pair_line = state.get("pair"), state.get("pair_line")
    if (
        not isinstance(pair, dict)
        or set(pair) != {"subject", "reference"}
        or any(not isinstance(v, str) or not v.strip() for v in pair.values())
        or pair["subject"] == pair["reference"]
    ):
        raise ValueError("Unknown or missing reviewed endpoint pair")
    printed_authority = "" if heading_authority else literal_label(cells[authority_column - 1])
    if printed_authority in authority["repeat"]:
        decision = state.get("authority")
        authority_line = state.get("authority_line")
        authority_label = state.get("authority_label")
    else:
        decision = authority["values"].get(printed_authority)
        authority_line, authority_label = line, None if heading_authority else printed_authority
    if (
        not isinstance(decision, dict)
        or set(decision) != {"role", "context_keys"}
        or decision["role"]
        not in {
            "historical_input",
            "recorded_reading",
            "adopted_value",
            "reduction",
            "calculation_intermediate",
            "repeated_reading",
        }
        or not isinstance(decision["context_keys"], list)
        or not decision["context_keys"]
        or any(not isinstance(k, str) or not k for k in decision["context_keys"])
    ):
        raise ValueError("Unknown or missing reviewed source authority")
    values = {**pair, "role": decision["role"]}
    if any(row.get(k) not in (None, v) for k, v in values.items()):
        raise ValueError("Printed relationship conflicts with an explicit endpoint or role")
    row.update(values)
    state.update(
        pair=pair,
        pair_line=pair_line,
        authority=decision,
        authority_line=authority_line,
        authority_label=authority_label,
        last_line=line,
    )
    key = f"{rule['context_prefix']}-{line}"
    return dict(
        key=key,
        kind="source_observation_context",
        lines=sorted({pair_line, authority_line, line}),
        value=dict(
            record_type="source_table_relationship",
            label_as_printed=cells[label_column - 1].strip(),
            authority_as_printed=None if heading_authority else cells[authority_column - 1].strip(),
            subject=pair["subject"],
            reference=pair["reference"],
            authority_basis_label=authority_label,
            pair_inherited=not bool(label),
            authority_inherited=printed_authority in authority["repeat"],
        ),
    ), [*decision["context_keys"], key]
