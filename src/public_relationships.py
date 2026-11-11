"""Public relationships: shared catalogue responsibilities."""

import re
from fractions import Fraction
from .catalog import (
    ANGLE_QUANTITIES,
    zodiac_arithmetic_values,
)


def identifier(value, kind):
    if value is not None and not re.fullmatch(
        rf"{kind}-(?:v1[0-3]|s[a-z][a-z0-9-]+)-[0-9a-f]{{20}}", value
    ):
        raise ValueError("Unexpected public identifier")
    return value


def public_derivation(row, assertions):
    allowed = {
        "sum",
        "difference",
        "mean",
        "sum_modulo_360_degrees",
        "difference_modulo_360_degrees",
        "sum_modulo_360_in_zodiac_frame",
        "difference_modulo_360_in_zodiac_frame",
        "historical_adoption",
        "historical_adoption_unspecified",
        "historical_reduction_unspecified",
    }
    op = row["operation"]
    inputs = row["input_ids"]
    output = row["output_id"]
    if (
        op not in allowed
        or not isinstance(inputs, list)
        or not inputs
        or any(a not in assertions for a in [*inputs, output])
    ):
        raise ValueError("Invalid public derivation operation or target")
    if (
        op
        in ("difference", "difference_modulo_360_degrees", "difference_modulo_360_in_zodiac_frame")
        and len(inputs) != 2
    ):
        raise ValueError("Difference requires two inputs")
    if op == "mean" and len(inputs) < 2:
        raise ValueError("Mean requires at least two inputs")
    computed = row.get("computed_magnitude")
    agrees = row.get("arithmetic_agrees")
    norms = [assertions[aid]["normalized"] for aid in [*inputs, output]]
    if op in (
        "sum",
        "difference",
        "mean",
        "sum_modulo_360_degrees",
        "difference_modulo_360_degrees",
        "sum_modulo_360_in_zodiac_frame",
        "difference_modulo_360_in_zodiac_frame",
    ) and all(n["status"] == "exact" for n in norms):
        if len({n["unit"] for n in norms}) != 1:
            raise ValueError("Public derivation units differ")
        values = (
            zodiac_arithmetic_values(norms)
            if op in ("sum_modulo_360_in_zodiac_frame", "difference_modulo_360_in_zodiac_frame")
            else [Fraction(n["magnitude"]) for n in norms]
        )
        expected = (
            values[0] - values[1]
            if op
            in (
                "difference",
                "difference_modulo_360_degrees",
                "difference_modulo_360_in_zodiac_frame",
            )
            else sum(values[:-1], Fraction())
        )
        if op == "mean":
            expected /= len(inputs)
        if op in (
            "sum_modulo_360_degrees",
            "difference_modulo_360_degrees",
            "sum_modulo_360_in_zodiac_frame",
            "difference_modulo_360_in_zodiac_frame",
        ):
            if norms[0]["unit"] != "arcsecond":
                raise ValueError("Circular arithmetic requires angular quantities")
            expected %= 360 * 3600
        if (
            computed != str(expected)
            or type(agrees) is not bool
            or agrees != (expected == values[-1])
        ):
            raise ValueError("Public derivation arithmetic differs from source records")
    elif computed is not None or agrees is not None:
        raise ValueError("Unspecified derivation must remain uncomputed")
    return dict(
        id=identifier(row["id"], "derivation"),
        operation=op,
        input_ids=[identifier(a, "assertion") for a in inputs],
        output_id=identifier(output, "assertion"),
        computed_magnitude=computed,
        unit=norms[-1]["unit"],
        arithmetic_agrees=agrees,
        **(
            dict(arithmetic_frame="zodiac_zero")
            if op in ("sum_modulo_360_in_zodiac_frame", "difference_modulo_360_in_zodiac_frame")
            else {}
        ),
    )


def validate_links(assertions, events, series=()):
    aids = {r["id"] for r in assertions}
    eids = {r["id"] for r in events}
    sids = {r["id"] for r in series}
    byid = {r["id"]: r for r in assertions}
    if len(aids) != len(assertions) or len(eids) != len(events) or len(sids) != len(series):
        raise ValueError("Duplicate public identity")
    for row in assertions:
        if row["quantity"] == "unclassified_angle" and row["role"] == "source_alternative":
            original = byid.get(row.get("variant_of_id"))
            if (
                original is None
                or original["id"] == row["id"]
                or original["quantity"] != "unclassified_angle"
                or original["role"] != "recorded_reading"
                or "measurement_type_unresolved" not in original.get("flags", [])
                or any(
                    original.get(k) != row.get(k)
                    for k in ("volume", "subject", "reference", "direction")
                )
            ):
                raise ValueError(
                    "Unclassified alternative requires its matching unresolved recorded angle"
                )
        if "source_time_anchor_event_id" in row:
            anchor = row["source_time_anchor_event_id"]
            candidates = [
                a
                for a in assertions
                if a.get("event_id") == anchor
                and a["volume"] == row["volume"]
                and a["subject"] == "Mars"
                and a["quantity"] == "angular_separation"
                and a["role"] in ("recorded_reading", "repeated_reading")
            ]
            if anchor not in eids or anchor == row.get("event_id") or not candidates:
                raise ValueError("Missing earlier Mars reading group for source-relative time")
            if row.get("source_date_claim_ids") and not any(
                not a.get("source_date_claim_ids")
                or set(row["source_date_claim_ids"]) & set(a["source_date_claim_ids"])
                for a in candidates
            ):
                raise ValueError(
                    "Relative time anchor has a different reviewed source-date context"
                )
        if "source_value_equal_to_id" in row:
            target = byid.get(row["source_value_equal_to_id"])
            repeated = row.get("source_equality_kind") == "repeated_measurement"
            if (
                target is None
                or target["id"] == row["id"]
                or target.get("source_value_equal_to_id") is not None
                or any(
                    target.get(k) != row.get(k)
                    for k in (
                        "volume",
                        "source_id",
                        "quantity",
                        "subject",
                        "direction",
                        "normalized",
                    )
                )
                or (
                    repeated
                    and (
                        row["role"] != "repeated_reading"
                        or target["role"] not in ("recorded_reading", "repeated_reading")
                        or row["reference"] != target["reference"]
                    )
                )
                or (not repeated and target["role"] != row["role"])
            ):
                raise ValueError("Stated equal value has a missing, chained or mismatched original")
        if (
            row["quantity"] == "latitude_difference"
            and row["role"] == "editorial_variant"
            and "source_comparison_sign" in row
        ):
            target = byid.get(row.get("annotation_of_id"))
            if (
                target is None
                or target["quantity"] != "latitude_difference"
                or target["role"] != "calculation_intermediate"
                or any(
                    target.get(k) != row.get(k)
                    for k in ("volume", "subject", "reference", "comparison_relation")
                )
            ):
                raise ValueError(
                    "Earlier residual form requires its matching source comparison target"
                )
        if row["quantity"] == "angle_component":
            target = byid.get(row.get("annotation_of_id"))
            if (
                target is None
                or target["quantity"] not in ANGLE_QUANTITIES
                or any(target.get(k) != row.get(k) for k in ("volume", "subject", "reference"))
                or target["normalized"]["unit"] != "arcsecond"
            ):
                raise ValueError("Angle component requires a matching angle annotation target")
        if row["quantity"] == "clock_component":
            target = byid.get(row.get("annotation_of_id"))
            if (
                target is None
                or target["quantity"] not in ("recorded_clock", "transit_clock")
                or target["volume"] != row["volume"]
                or target["normalized"]["unit"] != "second_of_time"
            ):
                raise ValueError(
                    "Clock component requires a clock annotation target in the same volume"
                )
        if "zodiac_sign_inherited_from_id" in row:
            target = byid.get(row["zodiac_sign_inherited_from_id"])
            variant_origin = (
                target is not None
                and row.get("variant_of_id") == target["id"]
                and (
                    row["role"] in ("printed_correction", "editorial_variant")
                    or (
                        row["role"] == "source_alternative"
                        and {"alternative_suggestion_not_applied", "not_an_additional_raw_reading"}
                        <= set(row.get("flags", []))
                        and row["normalized"]["status"] == target["normalized"]["status"] == "exact"
                        and Fraction(row["normalized"]["magnitude"]) // 3600
                        == Fraction(target["normalized"]["magnitude"]) // 3600
                    )
                )
            )
            ephemeris_origin = (
                target is not None
                and row.get("zodiac_inheritance_kind") == "same_ephemeris_statement"
                and target.get("role") == row["role"] == "historical_prediction"
                and row.get("model_name") in ("Stadius", "Carelli")
                and target.get("model_name") == row["model_name"]
                and target["subject"] in ("Moon", "Mars", "Venus", "Mercury", "Jupiter", "Saturn")
                and row["subject"] in ("Moon", "Mars", "Venus", "Mercury", "Jupiter", "Saturn")
                and target["subject"] != row["subject"]
            )
            if (
                target is None
                or target["quantity"] != "ecliptic_longitude"
                or "zodiac_sign_inherited_from_id" in target
                or ("zodiac_inheritance_kind" in row and not ephemeris_origin)
                or (target.get("role") != row.get("role") and not variant_origin)
                or any(
                    target.get(k) != row.get(k)
                    for k in (
                        ("volume", "model_name", "source_parameter_kind")
                        if ephemeris_origin
                        else ("volume", "subject", "model_name", "source_parameter_kind")
                    )
                )
                or target["normalized"].get("zodiac_sign") is None
                or target["normalized"].get("zodiac_sign") != row["normalized"].get("zodiac_sign")
            ):
                raise ValueError("Missing or mismatched public zodiac origin")
        if "calculation_epoch_id" in row:
            target = byid.get(row["calculation_epoch_id"])
            if target is None or target["quantity"] != "calculation_epoch":
                raise ValueError("Missing public calculation epoch")
        if row["event_id"] is not None and row["event_id"] not in eids:
            raise ValueError("Missing public event")
        if row["variant_of_id"] is not None and row["variant_of_id"] not in aids:
            raise ValueError("Missing public variant original")
        if row.get("annotation_of_id") is not None and row["annotation_of_id"] not in aids:
            raise ValueError("Missing public annotation target")
        if row["series_id"] is not None and row["series_id"] not in sids:
            raise ValueError("Missing public series group")
    for row in events:
        for key in ("clock_assertion_id", "epoch_assertion_id"):
            if row[key] is not None and row[key] not in aids:
                raise ValueError("Missing public clock/epoch")
    for group in series:
        if set(group["assertion_ids"]) != {
            r["id"] for r in assertions if r["series_id"] == group["id"]
        }:
            raise ValueError("Invalid public series membership")
