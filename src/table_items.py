"""Bind matching, reviewed items in parallel lists within physical table cells."""

import re

from .assembly import cell_intervals


def expand_selections(selections, policy):
    if (
        not isinstance(policy, dict)
        or set(policy) - {"indices", "label_column", "reference_labels"}
        or not isinstance(policy.get("indices"), list)
        or not policy["indices"]
        or any(type(n) is not int or n < 0 for n in policy["indices"])
        or policy["indices"] != sorted(set(policy["indices"]))
        or type(policy.get("label_column")) is not int
        or policy["label_column"] < 1
    ):
        raise ValueError("Table items require distinct ordered indices and a label column")
    references = policy.get("reference_labels")
    if references is not None and (
        not isinstance(references, dict)
        or not references
        or any(
            not isinstance(k, str) or not k or not isinstance(v, str) or not v
            for k, v in references.items()
        )
    ):
        raise ValueError("Table item reference labels require a reviewed mapping")
    expanded = []
    for selection in selections:
        cell = (
            dict(line=selection[0], column=selection[1])
            if isinstance(selection, list)
            else selection
        )
        if not isinstance(cell, dict) or "table_item_index" in cell or "key" in cell:
            raise ValueError("Table item selection cannot override its generated identity")
        expanded.extend(dict(cell, table_item_index=n) for n in policy["indices"])
    return expanded


def _items(line, bounds):
    start, end = bounds
    boundaries = [(m.start(), m.end()) for m in re.finditer(r"<br\s*/?>", line[start:end], re.I)]
    result = []
    left = start
    for split_start, split_end in [*boundaries, (end - start, end - start)]:
        right = start + split_start
        raw = line[left:right]
        trimmed_start = left + len(raw) - len(raw.lstrip())
        trimmed_end = right - len(raw) + len(raw.rstrip())
        if trimmed_start >= trimmed_end:
            raise ValueError("Parallel table items cannot contain empty entries")
        result.append((trimmed_start, trimmed_end))
        left = start + split_end
    return result


def bind_item(row, policy, lines, spans):
    """Emit existing source-fragment evidence; leave numerical parsing unchanged."""
    columns = row.pop("source_columns", None)
    index = row.pop("table_item_index")
    line_number = row.get("line")
    if (
        not isinstance(columns, list)
        or not 2 <= len(columns) <= 4
        or any(type(c) is not int or c < 1 for c in columns)
        or columns != list(range(columns[0], columns[-1] + 1))
        or policy["label_column"] in columns
        or type(line_number) is not int
        or not 1 <= line_number <= len(lines)
        or row.get("column") is not None
        or any(
            k in row
            for k in (
                "key",
                "source_expression",
                "char_start",
                "char_end",
                "source_fragments",
                "source_continuation_context_key",
                "expression_index",
                "fragment_index",
                "table_fields",
                "clock_fields",
                "table_carry",
                "components",
            )
        )
    ):
        raise ValueError(
            "Table items require reviewed component columns without conflicting selectors"
        )
    line = lines[line_number - 1]
    slots = cell_intervals(line, declared_table=True)
    if max(*columns, policy["label_column"]) > len(slots):
        raise ValueError("Table item column outside the physical table")
    vectors = [_items(line, slots[c - 1]) for c in [*columns, policy["label_column"]]]
    if len({len(v) for v in vectors}) != 1 or index >= len(vectors[0]):
        raise ValueError(
            "Parallel table items must have matching cardinality and an existing index"
        )
    span = next((s for s in spans if s["line_start"] <= line_number <= s["line_end"]), None)
    if span is None:
        raise ValueError("Table item lies outside reviewed source spans")
    fragments = [
        dict(
            line=line_number,
            span_id=span["id"],
            source_expression=line[left:right],
            char_start=left,
            char_end=right,
        )
        for vector in vectors[:-1]
        for left, right in [vector[index]]
    ]
    left, right = vectors[-1][index]
    label = line[left:right]
    references = policy.get("reference_labels")
    if references is not None:
        if (
            row.get("quantity") != "angular_separation"
            or label not in references
            or row.get("reference") not in (None, references[label])
        ):
            raise ValueError("Table item requires an unambiguous reviewed reference label")
        row["reference"] = references[label]
    key = f"{row['quantity']}-{line_number}-columns-{'-'.join(map(str, columns))}-item-{index}"
    context_key = key + "-components"
    row.update(
        **fragments[0],
        column=columns[0],
        key=key,
        source_fragments=fragments,
        source_continuation_context_key=context_key,
    )
    return dict(
        key=context_key,
        kind="source_observation_context",
        lines=[line_number],
        value=dict(
            record_type="source_continuation",
            source_expression=label,
            source_columns=columns,
            item_index=index,
            label_column=policy["label_column"],
        ),
    )
