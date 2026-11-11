"""Review preparation: shared catalogue responsibilities."""

from .review_state import read
from .review_state import rows
from .review_state import source_texts
from .review_state import edition_hashes
import copy
import hashlib
from pathlib import Path
import re
from .core import digest, fraction_text
from .recovery import write_json_atomic


def partial_number_start(text, start):
    before = text[:start]
    return bool(re.search(r"[\w/⁄.]$", before) or re.search(r"\d\s*[/⁄.]\s*$", before))


def complete_angle_sequence(text, candidate, units):
    """Complete an explicitly requested staged angle without changing staging indices."""
    from .narrative_staging import NUMBER, VULGAR

    fragment = candidate.get("expression_kind") != "angle"
    if partial_number_start(text, candidate["char_start"]) or (
        fragment and re.search(r"\d[\s.,/⁄·:]*$", text[: candidate["char_start"]])
    ):
        raise ValueError("Angle completion requires a complete numerical expression start")
    token = rf"(?:{NUMBER})(?:[ \t]+[{VULGAR}])?"
    if fragment and re.search(
        rf"{token}\s*(?:degrees?\b|arcminutes?\b|minutes?\b|arcseconds?\b|seconds?\b|"
        r"[°′'″\"ᵍᴾ]|\^[goP]\^)[\s,]*(?:and\s*)?$",
        text[: candidate["char_start"]],
        re.I,
    ):
        raise ValueError("Angle completion requires the complete numerical unit sequence")
    if fragment:
        canonical = ["degree", "arcminute", "arcsecond"]
        if (
            candidate.get("status") != "uninterpreted_numeric_fragment"
            or not isinstance(units, list)
            or not units
            or units != [unit for unit in canonical if unit in units]
        ):
            raise ValueError("Worded angle completion requires reviewed angular component units")
        marks = {
            "degree": r"(?:degrees?\b|gr\.|°|ᵍ|ᴾ|\^[goP]\^)",
            "arcminute": r"(?:arcminutes?\b|minutes?\b|[′'])",
            "arcsecond": r"(?:arcseconds?\b|seconds?\b|[″\"])",
        }
        pattern = r"\s*(?:,\s*)?(?:and\s+)?".join(rf"{token}\s*{marks[unit]}" for unit in units)
    else:
        if units not in (["degree", "arcminute"], ["degree", "arcminute", "arcsecond"]):
            raise ValueError("Complete angle sequence requires reviewed angular component units")
        pattern = (
            rf"{token}\s*(?:gr\.|°|ᵍ|ᴾ|\^[goP]\^)\s*(?:/\s*)?"
            rf"{token}\s*(?:[′']|(?:arcminutes?|minutes?)\b)"
            rf"(?:\s*(?:and\s+)?{token}\s*(?:[″\"]|(?:arcseconds?|seconds?)\b))?"
        )
    match = re.compile(pattern, re.I).match(text, candidate["char_start"])
    if match is None or re.match(
        rf"\s*(?:[?…]|\.{{2,}}|\[\s*[?0-9]|[+−.,/⁄·:-]?\s*[0-9{VULGAR}]|and\s+[+−-]?\s*[0-9{VULGAR}])",
        text[match.end() :] if match else "",
        re.I,
    ):
        raise ValueError("Complete angle sequence requires an unqueried complete expression")
    return dict(
        candidate,
        source_expression=match.group(),
        char_end=match.end(),
        expression_kind="angle",
        components={},
        flags=[
            flag
            for flag in candidate.get("flags", [])
            if flag != "possible_numeric_continuation_unresolved"
        ],
    )


def calculation_angle_selections(text, staged, sequences, *, marked_subunits=False):
    """Select marked angles in an explicitly reviewed homogeneous calculation block."""
    from .narrative_staging import VULGAR

    if type(marked_subunits) is not bool:
        raise ValueError("Marked subunits require an explicit boolean review")
    if marked_subunits and re.search(
        r"\b(?:hours?|horae|horis|days?)\b|\d\s*(?:\^h\^|ʰ|h\b)|\b[HD]\.\s*\d|"
        r"\d+\s+(?:complete\s+)?signs?\b|\d,\d|\d\s+[/⁄]\s*\d|\d\.\d",
        text,
        re.I,
    ):
        raise ValueError(
            "Marked angular subunits require explicit review of clocks or numerical context"
        )
    canonical = ["degree", "arcminute", "arcsecond"]
    if not isinstance(sequences, list) or any(
        not isinstance(units, list)
        or not units
        or units != [unit for unit in canonical if unit in units]
        for units in sequences
    ):
        raise ValueError("Invalid reviewed calculation block component sequences")
    if text.lstrip().startswith("|") or re.search(r"\[recte\s*:", text, re.I):
        raise ValueError("Calculation block requires explicit review of tables or alternatives")
    selections = []
    for index, expression in enumerate(staged["expressions"]):
        if expression["expression_kind"] != "angle":
            continue
        if (
            expression.get("components") is None
            or expression.get("rendering_layer") != "main"
            or "possible_numeric_continuation_unresolved" in expression.get("flags", [])
            or re.match(r"\s*(?:\[\s*)?(?:\?|…|\.{2,})", text[expression["char_end"] :])
            or partial_number_start(text, expression["char_start"])
        ):
            raise ValueError("Calculation block angle requires explicit review")
        selections.append(dict(column=None, expression_index=index))
    covered_end = -1
    occupied = [
        (expression["char_start"], expression["char_end"])
        for expression in staged["expressions"]
        if expression["expression_kind"] == "angle"
    ]
    unit_start = (
        r"(?:gr\.|degrees?|arcminutes?|minutes?|arcseconds?|seconds?|[′'″\"])"
        if marked_subunits
        else r"(?:gr\.|(?:degrees?|arcminutes?|minutes?|arcseconds?|seconds?)\b)"
    )
    for index, fragment in enumerate(staged["material"]["numeric_fragments"]):
        if (
            fragment["status"] != "uninterpreted_numeric_fragment"
            or fragment["char_start"] < covered_end
            or (
                marked_subunits
                and any(start <= fragment["char_start"] < end for start, end in occupied)
            )
            or not re.match(
                rf"\s*(?:[{VULGAR}]\s*)?{unit_start}",
                text[fragment["char_end"] :],
                re.I,
            )
        ):
            continue
        matches = []
        for units in sequences:
            try:
                completed = complete_angle_sequence(text, fragment, units)
            except ValueError:
                continue
            matches.append((completed["char_end"], units))
        if not matches:
            raise ValueError("Calculation block worded angle requires explicit review")
        covered_end, units = max(matches, key=lambda match: match[0])
        selections.append(
            dict(
                column=None,
                fragment_index=index,
                complete_angle_sequence=True,
                component_units=units,
            )
        )
    return selections


def attach_table_row_context(batch, row, declaration, text, context_index):
    """Bind declared literal label columns and an explicitly reviewed sign column."""
    from .assembly import cell_intervals

    if (
        not isinstance(declaration, dict)
        or set(declaration)
        not in (
            {"key_prefix", "columns"},
            {"key_prefix", "columns", "zodiac_sign_column"},
        )
        or not isinstance(declaration.get("key_prefix"), str)
        or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", declaration["key_prefix"])
        or not isinstance(declaration.get("columns"), dict)
        or not declaration["columns"]
        or any(
            not isinstance(key, str)
            or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", key)
            or key in ("record_type", "source_columns")
            or type(column) is not int
            or column < 1
            for key, column in declaration["columns"].items()
        )
        or not text.lstrip().startswith("|")
    ):
        raise ValueError("Invalid reviewed table row context")
    slots = cell_intervals(text, declared_table=True)

    def literal(column):
        if type(column) is not int or not 1 <= column <= len(slots):
            raise ValueError("Row context column outside the physical table")
        start, end = slots[column - 1]
        return text[start:end].strip()

    def attach(context):
        key = context["key"]
        if key in context_index:
            if context_index[key] != context:
                raise ValueError("Conflicting reviewed table row context")
        else:
            batch.setdefault("contexts", []).append(context)
            context_index[key] = context
        if key not in row["context_keys"]:
            row["context_keys"].append(key)

    line = row["line"]
    prefix = f"{declaration['key_prefix']}-{line}"
    attach(
        dict(
            key=prefix,
            kind="source_observation_context",
            lines=[line],
            value=dict(
                record_type="source_table_row",
                source_columns=dict(declaration["columns"]),
                **{key: literal(column) for key, column in declaration["columns"].items()},
            ),
        )
    )
    if "zodiac_sign_column" in declaration:
        if (
            row.get("zodiac_sign") is None
            or row.get("zodiac_sign_basis_key") is not None
            or row.get("zodiac_sign_inherited_from_key") is not None
        ):
            raise ValueError("Row sign column requires one explicit reviewed sign")
        key = prefix + "-zodiac"
        attach(
            dict(
                key=key,
                kind="source_coordinate_frame",
                lines=[line],
                value=dict(
                    subject=row["subject"],
                    zodiac_sign=row["zodiac_sign"],
                    line_start=line,
                    line_end=line,
                    source_expression=literal(declaration["zodiac_sign_column"]),
                ),
            )
        )
        row["zodiac_sign_basis_key"] = key


def materialize_review(review, text, spans):
    """Expand reviewed cell groups without inferring targets or event associations."""
    from .catalog import SOURCE_WORD_NUMBERS, normalize_quantity, source_numeric_text, source_key
    from .coordinate_staging import parse_coordinate
    from .table_staging import main_text, parse_clock, split_cells

    batch = copy.deepcopy(review)
    relationship_rules = batch.pop("table_relationship_rules", {})
    table_authorities = batch.pop("table_authorities", {})
    if not isinstance(relationship_rules, dict) or not isinstance(table_authorities, dict):
        raise ValueError("Reviewed table relationship policies must be mappings")
    relationship_states = {}
    groups = batch.pop("cell_groups", [])
    defaults = batch.pop("assertion_defaults", {})
    event_rows = batch.pop("row_events", {})
    included = batch.pop("included_span_starts", [])
    reason = batch.pop("span_review_reason", "Source interval and roles explicitly reviewed")
    selected = [
        s
        for s in spans
        if source_key(s) == source_key(batch)
        and batch["line_start"] <= s["line_start"] <= s["line_end"] <= batch["line_end"]
    ]
    if "span_decisions" not in batch:
        batch["span_decisions"] = [
            dict(
                span_id=s["id"],
                decision="include" if s["line_start"] in included else "context",
                reason=reason,
            )
            for s in selected
        ]
    lines = text.splitlines()
    prose_candidates = {}

    def prose_for(line):
        from .narrative_staging import stage_span

        if line not in prose_candidates:
            prose_candidates[line] = stage_span(
                dict(
                    id=f"review-source-line-{line}",
                    volume=source_key(batch),
                    edition_sha256=batch["edition_sha256"],
                    line_start=line,
                    line_end=line,
                    block_kind="paragraph",
                    text_original=lines[line - 1],
                )
            )
        return prose_candidates[line]

    batch.setdefault(
        "interval_sha256",
        hashlib.sha256(
            "\n".join(lines[batch["line_start"] - 1 : batch["line_end"]]).encode()
        ).hexdigest(),
    )
    assertions = batch.setdefault("assertions", [])
    context_index = None
    for group in groups:
        settings = {
            k: v
            for k, v in group.items()
            if k
            not in (
                "cells",
                "line_range",
                "calculation_angles",
                "worded_component_sequences",
                "marked_subunits",
                "table_items",
            )
        }
        if "worded_component_sequences" in group and "calculation_angles" not in group:
            raise ValueError("Worded sequences require a reviewed calculation block")
        if "marked_subunits" in group and "calculation_angles" not in group:
            raise ValueError("Marked subunits require a reviewed calculation block")
        if "line_range" in group:
            bounds = group["line_range"]
            if (
                "cells" in group
                or not isinstance(bounds, list)
                or len(bounds) != 2
                or any(type(n) is not int for n in bounds)
                or not batch["line_start"] <= bounds[0] <= bounds[1] <= batch["line_end"]
            ):
                raise ValueError("Reviewed row range must be inclusive and inside the review")
            selections = [dict(line=n) for n in range(bounds[0], bounds[1] + 1)]
        else:
            selections = group["cells"]
        if "calculation_angles" in group:
            policy = {**defaults, **settings}
            if (
                group["calculation_angles"] is not True
                or "line_range" not in group
                or policy.get("quantity") != "calculation_angle"
                or policy.get("role")
                not in ("historical_input", "calculation_intermediate", "reduction")
                or "not_an_additional_raw_reading"
                not in [*defaults.get("flags", []), *settings.get("flags", [])]
                or not policy.get("context_keys")
                or any(k in policy for k in ("components", "component_units", "source_columns"))
                or policy.get("column") is not None
            ):
                raise ValueError(
                    "Angle collection requires a reviewed homogeneous calculation block"
                )
            selections = [
                dict(line=selection["line"], **angle)
                for selection in selections
                for angle in calculation_angle_selections(
                    lines[selection["line"] - 1],
                    prose_for(selection["line"]),
                    group.get("worded_component_sequences", []),
                    marked_subunits=group.get("marked_subunits", False),
                )
            ]
        if "table_items" in group:
            from .table_items import expand_selections

            selections = expand_selections(selections, group["table_items"])
        for selection in selections:
            cell = (
                dict(line=selection[0], column=selection[1])
                if isinstance(selection, list)
                else selection
            )
            row = {**defaults, **settings, **cell}
            omit_empty = row.pop("omit_empty_source_columns", False)
            if type(omit_empty) is not bool or (
                omit_empty and ("source_columns" not in row or "source_expression" in row)
            ):
                raise ValueError("Empty-column omission requires reviewed physical source columns")
            relationship_keys = []
            if "table_items" in group:
                from .table_items import bind_item

                context = bind_item(row, group["table_items"], lines, selected)
                contexts = batch.setdefault("contexts", [])
                if any(c["key"] == context["key"] for c in contexts):
                    raise ValueError("Duplicate table item context identity")
                contexts.append(context)
                if context_index is not None:
                    context_index[context["key"]] = context
                relationship_keys.append(context["key"])
            relationship_rule = row.pop("table_relationships", None)
            if relationship_rule is not None:
                from .table_relationships import apply_table_relationships

                if (
                    not isinstance(relationship_rule, str)
                    or relationship_rule not in relationship_rules
                ):
                    raise ValueError("Unknown reviewed table relationship rule")
                context, relationship_keys = apply_table_relationships(
                    row,
                    relationship_rules[relationship_rule],
                    table_authorities,
                    lines,
                    relationship_states.setdefault(relationship_rule, {}),
                )
                batch.setdefault("contexts", []).append(context)
            if "source_columns" in row and "source_expression" not in row:
                from .assembly import cell_intervals

                columns = row["source_columns"]
                line = row["line"]
                if (
                    type(line) is not int
                    or not batch["line_start"] <= line <= batch["line_end"]
                    or row.get("column") is not None
                    or any(k in row for k in ("char_start", "char_end"))
                    or not isinstance(columns, list)
                    or len(columns) < 2
                    or any(type(c) is not int for c in columns)
                    or columns != list(range(columns[0], columns[-1] + 1))
                ):
                    raise ValueError("Reviewed source columns must be consecutive table cells")
                slots = cell_intervals(lines[line - 1], declared_table=True)
                if not 1 <= columns[0] <= columns[-1] <= len(slots):
                    raise ValueError("Reviewed source columns outside the table")
                if omit_empty and all(
                    not lines[line - 1][slots[c - 1][0] : slots[c - 1][1]].strip() for c in columns
                ):
                    continue
                left, right = slots[columns[0] - 1][0], slots[columns[-1] - 1][1]
                expression = lines[line - 1][left:right]
                # Match the compiler's treatment of a separately printed editorial correction.
                expression = re.sub(r"\s+\[recte: \d+(?:[′″])?\]$", "", expression)
                row.update(
                    column=None,
                    source_expression=expression,
                    char_start=left,
                    char_end=left + len(expression),
                )
                row.setdefault(
                    "key", f"{row['quantity']}-{line}-columns-{'-'.join(map(str, columns))}"
                )
            line, column = row["line"], row["column"]
            completion = row.pop("complete_angle_sequence", False)
            if type(completion) is not bool or (
                completion and (("expression_index" in row) == ("fragment_index" in row))
            ):
                raise ValueError("Angle completion requires an explicit staged expression selector")
            fragment = False
            if "fragment_index" in row or "expression_index" in row:
                fragment = "fragment_index" in row
                index = row.pop("fragment_index" if fragment else "expression_index")
                if (
                    type(index) is not int
                    or index < 0
                    or type(line) is not int
                    or not batch["line_start"] <= line <= batch["line_end"]
                    or column is not None
                    or any(k in row for k in ("source_expression", "char_start", "char_end"))
                    or (fragment and "expression_index" in row)
                ):
                    raise ValueError("Invalid or conflicting staged prose selector")
                staged = prose_for(line)
                candidates = (
                    staged["material"]["numeric_fragments"] if fragment else staged["expressions"]
                )
                if index >= len(candidates):
                    raise ValueError("Staged prose selector outside source expressions")
                candidate = candidates[index]
                if completion:
                    candidate = complete_angle_sequence(
                        lines[line - 1], candidate, row.get("component_units")
                    )
                    if fragment:
                        row.setdefault("key", f"{row['quantity']}-{line}-fragment-angle-{index}")
                        fragment = False
                if fragment:
                    units = row.get("component_units")
                    raw = source_numeric_text(row, candidate["source_expression"]).strip()
                    before = lines[line - 1][: candidate["char_start"]]
                    after = lines[line - 1][candidate["char_end"] :]
                    explicit_unit = r"degrees?|arcminutes?|arcseconds?|hours?|minutes?|seconds?"
                    unit_suffix = re.match(
                        r"\s*(?:[°′″'\"]|\^[hmsg]\^|(?:" + explicit_unit + r")\b)", after, re.I
                    )
                    if unit_suffix:
                        from .normalization import ANGLE_QUANTITIES, TIME_QUANTITIES

                        if row["quantity"] not in ANGLE_QUANTITIES | TIME_QUANTITIES | {
                            "source_sexagesimal_length",
                            "distance_in_semidiameters",
                        }:
                            raise ValueError(
                                "Explicit units cannot become an untyped native scalar"
                            )
                        candidate = dict(
                            candidate, char_end=candidate["char_end"] + unit_suffix.end()
                        )
                        candidate["source_expression"] = lines[line - 1][
                            candidate["char_start"] : candidate["char_end"]
                        ]
                        after = after[unit_suffix.end() :]
                    if (
                        candidate["status"] != "uninterpreted_numeric_fragment"
                        or not isinstance(units, list)
                        or len(units) != 1
                        or row.get("source_number_grouping") not in (None, "comma_thousands")
                        or re.fullmatch(r"\d+(?:\s+\d+/\d+|/\d+)?", raw) is None
                        or any(
                            key in row
                            for key in (
                                "components",
                                "source_fragments",
                                "source_word_numbers",
                                "source_digit_restorations",
                                "source_unit_notation",
                                "source_component_addends",
                                "source_note_marker_original",
                                "inherited_components",
                            )
                        )
                        or re.search(r"\d[\s.,/⁄·:]*$", before)
                        or re.match(r"(?:[.,/⁄·:]\s*\d|\s+\d|\s*[?…]|\s*\.{2,}|\s*\[[\d?])", after)
                        or (unit_suffix and re.match(r"\s+and\s+\d", after, re.I))
                        or re.search(r"\b(?:" + explicit_unit + r"|[HMSPG]\.)\s*$", before, re.I)
                        or re.search(
                            r"\d(?:\s+\d+/\d+|/\d+)?\s*(?:"
                            + explicit_unit
                            + r")[\s,]*(?:and\s*)?$",
                            fraction_text(before),
                            re.I,
                        )
                    ):
                        raise ValueError(
                            "Native fragment requires a complete independent unsigned number and reviewed unit"
                        )
                elif "possible_numeric_continuation_unresolved" in candidate["flags"]:
                    raise ValueError(
                        "Staged prose selector requires a complete numerical expression"
                    )
                if (
                    not fragment
                    and candidate["components"] is None
                    and not (
                        row.get("components") == {}
                        and "component_units" not in row
                        and "source_notation_unresolved" in row.get("flags", [])
                    )
                ):
                    raise ValueError(
                        "Staged prose expression is unresolved; retain an explicit review"
                    )
                row.update(
                    (k, candidate[k]) for k in ("source_expression", "char_start", "char_end")
                )
                selector = "fragment" if fragment else "expression"
                row.setdefault("key", f"{row['quantity']}-{line}-{selector}-{index}")
                if (
                    not fragment
                    and "component_units" not in row
                    and "components" not in row
                    and candidate["components"] is not None
                ):
                    row["components"] = candidate["components"]
            expression = (
                row["source_expression"]
                if "source_expression" in row
                else main_text(split_cells(lines[line - 1])[column - 1])
            )
            row["source_expression"] = expression
            table_fields = row.pop("table_fields", None)
            if table_fields is not None:
                from .table_fields import apply_table_fields

                apply_table_fields(row, table_fields, lines[line - 1])
                expression = row["source_expression"]
            clock_fields = row.pop("clock_fields", None)
            if clock_fields is not None:
                from .table_fields import apply_clock_fields

                if not apply_clock_fields(row, clock_fields, lines[line - 1]):
                    continue
                expression = row["source_expression"]
            partial_unresolved = False
            declared_units = row.pop("component_units", None)
            partial_policy = row.pop("incomplete_component_policy", None)
            if partial_policy is not None:
                from .normalization import ANGLE_QUANTITIES

                if (
                    partial_policy != "unresolved"
                    or row["quantity"] not in ANGLE_QUANTITIES
                    or not isinstance(declared_units, list)
                    or len(declared_units) < 2
                    or "table_carry" in row
                    or "components" in row
                ):
                    raise ValueError(
                        "Incomplete components require an explicit unresolved angular policy"
                    )
            if declared_units is not None:
                if (
                    "components" in row
                    or not isinstance(declared_units, list)
                    or not declared_units
                    or any(not isinstance(u, str) for u in declared_units)
                    or len(set(declared_units)) != len(declared_units)
                ):
                    raise ValueError(
                        "Choose explicit components or distinct declared component units"
                    )
                numeric = (
                    " ".join(fragment["source_expression"] for fragment in row["source_fragments"])
                    if "source_fragments" in row
                    else expression
                )
                marker = row.get("source_note_marker_original")
                if marker and numeric.endswith(marker):
                    numeric = numeric[: -len(marker)]
                for word, value in row.get("source_word_numbers", {}).items():
                    if SOURCE_WORD_NUMBERS.get(word) != value:
                        raise ValueError("Unreviewed source word number")
                    numeric = re.sub(r"\b" + re.escape(word) + r"\b", value, numeric)
                numeric = source_numeric_text(row, numeric)
                if re.search(r"[+−-]\s*\d", numeric):
                    raise ValueError("Signed components require an explicit review")
                tokens = re.findall(r"\d+(?:\s+\d+/\d+|/\d+)?", numeric)
                carry = None
                literal_units = declared_units
                if "table_carry" in row:
                    from .table_components import table_carry_origin

                    carry = table_carry_origin(row, batch, lines)
                    if declared_units[0] != carry["unit"]:
                        raise ValueError("Carried component differs from the first declared unit")
                    if carry["source_line"] < line:
                        literal_units = declared_units[1:]
                partial = (
                    partial_policy == "unresolved" and 0 < len(tokens) == len(literal_units) - 1
                )
                if not partial and len(tokens) != len(literal_units):
                    raise ValueError("Literal component count differs from declared units")
                if partial:
                    partial_unresolved = True
                    row["components"] = {}
                    row["flags"] = [*row.get("flags", []), "source_notation_unresolved"]
                else:
                    row["components"] = dict(zip(literal_units, tokens, strict=True))
                if carry is not None:
                    row["components"][carry["unit"]] = carry["source_expression"]
                if fragment:
                    from .numeric_integrity import validate_units

                    validate_units(numeric, row["components"], quantity=row["quantity"])
                if "source_digit_restorations" in row:
                    row.setdefault("source_component_order", list(declared_units))
                normalize_quantity(row)
            elif "components" not in row:
                if "source_unit_notation" in row:
                    from .normalization import interpret_part_minute_notation

                    _, row["components"] = interpret_part_minute_notation(row)
                else:
                    numeric = expression
                    marker = row.get("source_note_marker_original")
                    if marker and numeric.endswith(marker):
                        numeric = numeric[: -len(marker)]
                    parsed = (
                        parse_clock(numeric, "")
                        if row["quantity"]
                        in (
                            "recorded_clock",
                            "transit_clock",
                            "calculation_epoch",
                            "annotated_time",
                            "hour_angle",
                            "temporal_hour_count",
                        )
                        else parse_coordinate(numeric)
                    )
                    if parsed["components"] is None:
                        raise ValueError(
                            f"Reviewed cell {line}:{column} requires explicit numeric components"
                        )
                    row["components"] = parsed["components"]
            row.setdefault("key", f"{row['quantity']}-{line}-{column}")
            row.setdefault(
                "span_id",
                next(s["id"] for s in selected if s["line_start"] <= line <= s["line_end"]),
            )
            row.setdefault("event_key", event_rows.get(str(line)))
            for field in ("flags", "context_keys"):
                row[field] = list(
                    dict.fromkeys(
                        [
                            *defaults.get(field, []),
                            *settings.get(field, []),
                            *cell.get(field, []),
                            *(relationship_keys if field == "context_keys" else []),
                        ]
                    )
                )
            if partial_unresolved and "source_notation_unresolved" not in row["flags"]:
                row["flags"].append("source_notation_unresolved")
            row_context = row.pop("row_context", None)
            if row_context is not None:
                if context_index is None:
                    context_index = {c["key"]: c for c in batch.get("contexts", [])}
                attach_table_row_context(batch, row, row_context, lines[line - 1], context_index)
            assertions.append(row)
    return batch


def record_update_plan(work, batch):
    planned = {}
    for name, additions in batch.get("record_updates", {}).items():
        if name not in (
            "edition_issues.json",
            "coordinate_adjudications.json",
            "source_reference_reviews.json",
        ):
            raise ValueError("Unrecognized supplementary review ledger")
        before = read(work / name)
        after = list(before)
        indexed = {r["id"]: r for r in before}
        for record in additions:
            if record["id"] in indexed:
                if indexed[record["id"]] != record:
                    raise ValueError("Conflicting supplementary review identity")
            else:
                after.append(record)
                indexed[record["id"]] = record
        planned[name] = (before, after)
    return planned


def apply_record_updates(work, planned):
    backups = {}
    for name, (before, after) in planned.items():
        if before == after:
            continue
        path = work / name
        backup = work / "recovery" / (name + "-before-" + digest(path) + ".json")
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
        backups[name] = str(backup.relative_to(work))
        write_json_atomic(path, after)
    return backups


def inspect_range(workspace, source_root, volume, start, end):
    work = Path(workspace)
    text = source_texts(work, source_root)[volume]
    lines = text.splitlines()
    if not 1 <= start <= end <= len(lines):
        raise ValueError("Source interval outside the canonical edition")
    spans = [
        s
        for s in rows(work / "inventory_spans.jsonl")
        if s["volume"] == volume and s["line_start"] <= end and s["line_end"] >= start
    ]
    cells = [
        c
        for c in rows(work / "table_cells.jsonl")
        if c["volume"] == volume and start <= c["line"] <= end
    ]
    return dict(
        volume=volume,
        edition_sha256=edition_hashes(work)[volume],
        line_start=start,
        line_end=end,
        source_lines=[dict(line=n, text=lines[n - 1]) for n in range(start, end + 1)],
        candidate_spans=spans,
        staged_cells=cells,
        status="requires_source_review_not_accepted_observations",
    )
