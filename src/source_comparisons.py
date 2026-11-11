"""Public meaning of native historical size comparisons, without reconstructing ratios."""

from .normalization import normalize_quantity

COMPARISON_FIELDS = {
    "source_comparison_measure",
    "source_comparison_endpoints",
    "source_comparison_relation",
    "source_comparison_term",
}
SIZE_ENDPOINTS = {
    "Sun",
    "Moon",
    "Earth",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "fixed stars",
    "New Star of 1572",
    "comet",
}


def project_size_comparison(row):
    """Retain explicit dimension, endpoint order and the source's inverse convention."""
    out = {}
    if "source_length_role" in row:
        role = row["source_length_role"]
        if (
            role
            not in (
                "radial_distance",
                "physical_diameter",
                "distance_adjustment",
                "orbital_radius",
                "orbital_diameter",
                "orbital_circumference",
                "construction_side",
            )
            or row["quantity"]
            not in (
                "distance_in_semidiameters",
                "distance_in_ordinary_miles",
                "distance_in_german_miles",
                "source_sexagesimal_length",
            )
            or row["role"]
            not in (
                "historical_input",
                "calculation_intermediate",
                "editorial_variant",
                "source_alternative",
            )
            or row["normalized"]["status"] != "exact"
            or row["normalized"] != normalize_quantity(row)
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError("Native length role requires a verified source length")
        out["source_length_role"] = role
    present = COMPARISON_FIELDS & row.keys()
    if "source_comparison_reference_unit" in row and not present:
        raise ValueError("Comparison reference unit requires its size comparison")
    if present:
        endpoints = row.get("source_comparison_endpoints")
        term = row.get("source_comparison_term")
        native_operand = (
            row["quantity"] == "source_sexagesimal_length"
            and row["normalized"]["unit"] == "source_length_part"
            and row.get("source_comparison_measure") in ("diameter", "radial_distance")
            and term in ("first_operand", "second_operand")
        )
        scalar = (
            row["quantity"] == "source_scalar"
            and row["normalized"]["unit"] == "source_scalar"
            and row.get("source_parameter_kind") == "comparison_multiplier"
        )
        if (
            present != COMPARISON_FIELDS
            or not isinstance(endpoints, list)
            or len(endpoints) != 2
            or any(not isinstance(e, str) or e not in SIZE_ENDPOINTS for e in endpoints)
            or endpoints[0] == endpoints[1]
            or row.get("source_comparison_measure")
            not in ("diameter", "bulk", "apparent_diameter", "radial_distance", "not_stated")
            or row.get("source_comparison_relation")
            not in ("first_larger", "first_smaller", "first_to_second_as_stated")
            or term
            not in (
                "factor",
                "first_operand",
                "second_operand",
                "additional_fraction",
                "subtracted_fraction",
                "additional_amount",
                "divisor",
            )
            or not (scalar or native_operand)
            or (
                row.get("source_comparison_measure") == "not_stated"
                and (
                    not scalar
                    or row.get("source_comparison_relation") != "first_to_second_as_stated"
                    or term not in ("first_operand", "second_operand")
                )
            )
            or row["role"] != "historical_input"
            or row.get("reference") is not None
            or row.get("direction") is not None
            or row.get("event_id") is not None
            or row.get("model_name") is not None
            or row["normalized"]["status"] != "exact"
            or row["normalized"] != normalize_quantity(row)
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError("Size comparison requires complete, source-attributed native operands")
        expected_subject = {
            "fixed stars": "fixed star calculation",
            "New Star of 1572": "New Star calculation",
        }.get(endpoints[0], endpoints[0] + " calculation")
        if row["subject"] != expected_subject:
            raise ValueError("Size comparison subject differs from its first endpoint")
        out.update((key, row[key]) for key in COMPARISON_FIELDS)
        if "source_comparison_reference_unit" in row:
            unit = row["source_comparison_reference_unit"]
            if row["source_comparison_measure"] != "radial_distance" or unit not in (
                "diameter",
                "semidiameter",
            ):
                raise ValueError(
                    "Native distance comparison requires a diameter or radius reference"
                )
            out["source_comparison_reference_unit"] = unit
    if "source_stellar_class" in row:
        value = row["source_stellar_class"]
        if (
            type(value) is not int
            or value not in range(1, 7)
            or row["quantity"] not in ("source_scalar", "angular_diameter")
            or not (
                row["subject"] in ("fixed stars", "fixed star calculation")
                or (present and "fixed stars" in row["source_comparison_endpoints"])
            )
            or row.get("reference") is not None
            or row.get("direction") is not None
        ):
            raise ValueError("Native stellar class requires a qualified fixed-star size assertion")
        out["source_stellar_class"] = value
    return out
