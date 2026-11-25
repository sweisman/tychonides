"""Append reviewed interpretations of previously unresolved log readings."""

from collections.abc import Iterable
import json
import re

from .catalog_release import WORKING_CATALOGUE_VIEW, encoded, source_value_hash
from .core import fraction_text, number
from .normalization import ANGLE_QUANTITIES, normalize_quantity
from .numeric_integrity import (
    NUMBER,
    completed_log_components,
    declared_component_units,
    explicit_angular_components,
    explicit_postfix_clock_components,
    explicit_time_components,
    log_point_form_components,
    log_zodiac_column_sign,
    split_zodiac_notation,
    unmarked_components,
    validate_units,
)
from .public_assertions import public_assertion


def apply_log_page_reviews(db, decisions: Iterable[dict]):
    """Correct working citations while retaining the original reading and page evidence."""
    pages = {}
    loci = {}
    for decision in decisions:
        identifier = decision["quantity_id"]
        volume = decision["volume"]
        previous = decision["previous_printed_page"]
        corrected = decision["printed_page"]
        source = db.execute(
            "SELECT volume,source_id,printed_page,expression FROM quantities WHERE id=?",
            (identifier,),
        ).fetchone()
        if (
            identifier in pages
            or not 10 <= volume <= 13
            or type(corrected) is not int
            or corrected < 1
            or corrected == previous
            or source != (volume, f"tycho-oo-{volume}", previous, decision["source_expression"])
        ):
            raise ValueError("Reviewed page differs from its frozen source reading: " + identifier)
        pages[identifier] = (previous, corrected)
        for locus_id, old_page, data in db.execute(
            """
            SELECT l.id,l.printed_page,l.data_json
            FROM locus_quantities AS link JOIN source_loci AS l ON l.id=link.locus_id
            WHERE link.quantity_id=? AND l.status='mapped_source_page'
            """,
            (identifier,),
        ):
            if old_page != previous or loci.setdefault(locus_id, (previous, corrected, data)) != (
                previous,
                corrected,
                data,
            ):
                raise ValueError("Page reviews disagree on a shared printed locus: " + locus_id)

    for locus_id, (previous, corrected, data) in loci.items():
        if any(
            pages.get(other) != (previous, corrected)
            for (other,) in db.execute(
                "SELECT quantity_id FROM locus_quantities WHERE locus_id=?", (locus_id,)
            )
        ):
            raise ValueError("Every reading at a shared printed locus needs page evidence")
        record = json.loads(data)
        if record.get("printed_page") != previous:
            raise ValueError("Frozen locator disagrees with its indexed printed page")
        record.update(
            previous_printed_page=previous,
            printed_page=corrected,
            page_basis="reviewed_quantity_citation",
        )
        db.execute(
            "UPDATE source_loci SET printed_page=?,data_json=? WHERE id=?",
            (corrected, encoded(record), locus_id),
        )
    db.executemany(
        "UPDATE quantities SET printed_page=? WHERE id=?",
        ((corrected, identifier) for identifier, (_, corrected) in pages.items()),
    )
    return len(pages)


def apply_log_interpretations(db, decisions: Iterable[dict]):
    """Bind decisions to frozen readings and select their new versions."""
    inserted = []
    for decision in decisions:
        identifier = decision["quantity_id"]
        source = db.execute(
            """
            SELECT q.expression, q.original_json, q.components_json, q.source_id,
                   q.printed_page, i.version, i.quantity, i.status
            FROM catalogue c JOIN quantities q ON q.id=c.id
            JOIN interpretations i ON i.quantity_id=c.id AND i.version=c.version
            WHERE q.id=?
            """,
            (identifier,),
        ).fetchone()
        if source is None:
            raise ValueError("Missing reviewed log reading: " + identifier)
        expression, original, components, source_id, page, version, quantity, status = source
        frozen = dict(
            json.loads(original), source_expression=expression, components=json.loads(components)
        )
        frozen["normalized"] = normalize_quantity(frozen)
        if (
            source_id != f"tycho-oo-{decision['volume']}"
            or not 10 <= decision["volume"] <= 13
            or frozen["role"] != "unresolved"
            or quantity != "unclassified_numeric_expression"
            or status != "unsupported"
            or version != 0
            or page != decision["printed_page"]
            or expression != decision["source_expression"]
            or source_value_hash(frozen) != decision["source_value_sha256"]
        ):
            raise ValueError(
                "Interpretation review differs from its frozen log reading: " + identifier
            )
        interpretation = decision["interpretation"]
        basis = decision["basis"]
        expected_fields = {
            "quantity",
            "subject",
            "role",
            "reference",
            "direction",
            "components",
            "zodiac_sign",
            "flags",
        }
        if (
            set(interpretation) != expected_fields
            or interpretation["quantity"]
            not in ANGLE_QUANTITIES
            | {"stellar_magnitude_class", "annotated_time", "recorded_clock", "unclassified_time"}
            or any(
                interpretation[key] != basis.get(key)
                for key in ("quantity", "subject", "role", "direction", "reference")
            )
            or not basis.get("designation")
            or not basis.get("label")
            or basis.get("column") != decision["column"]
        ):
            raise ValueError("Log interpretation requires reviewed source labels and roles")
        updated = dict(frozen, **interpretation)
        completed = basis.get("completed_source_field")
        if completed:
            field = completed["expression"]
            start, end = decision["occurrence"]
            first, last = completed["occurrence"]
            if (
                first < 0
                or not first <= start < end <= last
                or len(field) != last - first
                or len(field) <= len(expression)
                or field[start - first : end - first] != expression
                or completed_log_components(field, clock=updated["quantity"] == "annotated_time")
                != updated["components"]
            ):
                raise ValueError(
                    "Reviewed completion must retain the original source interval and explicit places"
                )
            updated["source_expression"] = field
            expression = field
        validate_units(expression, updated["components"], quantity=updated["quantity"])
        if updated["quantity"] == "stellar_magnitude_class":
            units = ("scalar",)
        elif updated["quantity"] in {"annotated_time", "recorded_clock", "unclassified_time"}:
            units = ("hour", "minute", "second")
        else:
            units = ("degree", "arcminute", "arcsecond")
        parts = updated["components"]
        value, sign = split_zodiac_notation(expression)
        sign_witness = basis.get("sign_witness")
        if sign_witness:
            annotated_value, annotated_sign = split_zodiac_notation(sign_witness)
            if sign is not None or annotated_value != value or not annotated_sign:
                raise ValueError("Zodiac witness must label the complete reading")
            sign = annotated_sign
        sign_column = basis.get("sign_column_witness")
        if sign_column:
            marker = log_zodiac_column_sign(sign_column["expression"])
            if (
                updated["quantity"] != "ecliptic_longitude"
                or sign is not None
                or marker is None
                or sign_column["column"] != decision["column"]
                or not basis["layout_line"] <= sign_column["line"] <= decision["line"]
            ):
                raise ValueError(
                    "Inherited zodiac origin lacks a printed sign in the longitude column"
                )
            sign = marker
        if interpretation["zodiac_sign"] != sign:
            raise ValueError("Reviewed sign differs from the recorded zodiac glyph")
        note = basis.get("point_form_note")
        if note and (
            updated["quantity"] != "ecliptic_longitude"
            or not sign
            or note.get("printed_page") != page
            or not note.get("marker")
            or log_point_form_components(value) != parts
        ):
            raise ValueError(
                "The edition's point-form notation does not support these angular places"
            )
        if (
            updated["quantity"] in {"annotated_time", "recorded_clock", "unclassified_time"}
            and (explicit_clock := explicit_time_components(expression)) is not None
            and explicit_clock != parts
        ):
            raise ValueError("Reviewed time differs from the recorded clock places")
        if heading := basis.get("unit_heading"):
            declared = declared_component_units(heading)
            if (
                not declared
                or declared != tuple(unit for unit in units if unit in parts)
                or unmarked_components(value, declared) != parts
            ):
                raise ValueError("Inherited places differ from the printed unit heading")
        if witness := basis.get("unit_witness"):
            witness_value, _ = split_zodiac_notation(witness["expression"])
            witnessed = explicit_angular_components(witness_value)
            places = tuple(witnessed or ())
            literal = (
                value.removesuffix("′")
                if sign_column and places == ("degree", "arcminute")
                else value
            )
            if not witnessed or unmarked_components(literal, places) != parts:
                raise ValueError("Inherited places differ from the marked column witness")
        if clock_witness := basis.get("clock_unit_witness"):
            witnessed = explicit_postfix_clock_components(clock_witness["expression"])
            if not witnessed or unmarked_components(value, tuple(witnessed)) != parts:
                raise ValueError("Inherited clock places differ from the marked column witness")
        if (
            not parts
            or set(parts) - set(units)
            or [number(fraction_text(parts[unit])) for unit in units if unit in parts]
            != [number(token) for token in re.findall(NUMBER, fraction_text(expression))]
        ):
            raise ValueError("Log interpretation components differ from the recorded numerals")
        updated["normalized"] = normalize_quantity(updated)
        result = public_assertion(updated)
        norm = result["normalized"]
        if norm["status"] != "exact" or norm != decision["normalized"]:
            raise ValueError("The reviewed log conversion does not reproduce exactly")
        revision = dict(
            kind="log_reading_interpretation",
            role=updated["role"],
            direction=updated["direction"],
            source_designation=basis["designation"],
            source_label=basis["label"],
            printed_page=page,
            column=decision["column"],
        )
        if updated["quantity"] == "stellar_magnitude_class":
            revision["source_class_text"] = basis["source_class_text"]
        elif updated["quantity"] in {"annotated_time", "recorded_clock"}:
            revision["source_clock_text"] = basis["source_class_text"]
            if "source_clock_field" in basis:
                revision["source_clock_field"] = basis["source_clock_field"]
        if heading:
            revision["source_unit_heading"] = heading
        if witness:
            revision["source_unit_witness"] = witness
        if sign_witness:
            revision["source_sign_witness"] = sign_witness
        if sign_column:
            revision["source_sign_column_witness"] = sign_column
        if note:
            revision["source_point_form_note"] = note
        if clock_witness:
            revision["source_clock_unit_witness"] = clock_witness
        if completed:
            revision["completed_source_expression"] = completed["expression"]
            revision["previous_source_expression"] = frozen["source_expression"]
        db.execute(
            "INSERT INTO interpretations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                identifier,
                version + 1,
                updated["quantity"],
                updated["subject"],
                updated["reference"],
                norm["status"],
                norm["unit"],
                norm["magnitude"],
                norm["signed_magnitude"],
                encoded(norm),
                encoded(parts),
                encoded(result["flags"]),
                encoded(revision),
            ),
        )
        inserted.append(identifier)
    if inserted:
        db.execute("DROP VIEW catalogue")
        db.execute(WORKING_CATALOGUE_VIEW)
    return inserted
