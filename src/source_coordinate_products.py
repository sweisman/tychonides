"""Source-bound attribution of historical coordinates and coordinate comparisons."""

import re

from .normalization import normalize_quantity


COORDINATES = {"declination", "right_ascension", "ecliptic_longitude", "ecliptic_latitude"}
COMPARISONS = COORDINATES | {
    "declination_difference",
    "right_ascension_difference",
    "longitude_difference",
    "latitude_difference",
    "stated_angular_precision",
}


def _authorities(value):
    return (
        isinstance(value, list)
        and bool(value)
        and all(
            isinstance(name, str)
            and re.fullmatch(r"[^\W\d_][^\d/\\:@\r\n]{0,79}", name)
            and name == name.strip()
            for name in value
        )
        and len(value) == len(set(value))
    )


def bind_coordinate_product(assertion, contexts, lines, start, end, context_map):
    """Bind reviewed attribution to literal evidence without inferring an author."""
    if "source_coordinate_product" not in assertion:
        return None
    product = assertion["source_coordinate_product"]
    if not isinstance(product, dict) or set(product) != {"basis_key"}:
        raise ValueError("Historical coordinate product requires one attribution basis")
    key = product["basis_key"]
    basis = next((c for c in contexts if c["key"] == key), None)
    value = basis.get("value") if basis else None
    if (
        basis is None
        or key not in assertion.get("context_keys", [])
        or basis.get("kind") != "source_observation_context"
        or not isinstance(value, dict)
        or value.get("record_type") != "source_coordinate_product_attribution"
        or not _authorities(value.get("authorities"))
        or assertion.get("role") not in ("historical_prediction", "historical_comparison")
        or value.get("scientific_role") != assertion["role"]
        or not isinstance(value.get("source_label"), str)
        or not 1 <= len(value["source_label"]) <= 160
        or not basis.get("lines")
        or any(type(n) is not int or not start <= n <= end for n in basis["lines"])
        or not any(value["source_label"] in lines[n - 1] for n in basis["lines"])
        or not all(
            re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", value["source_label"])
            for name in value["authorities"]
        )
    ):
        raise ValueError("Historical coordinate product attribution lacks literal review evidence")
    return dict(authorities=list(value["authorities"]), basis_context_id=context_map[key])


def project_coordinate_product(row, norm):
    """Keep attributed products distinct from observations and other model contracts."""
    if "source_coordinate_product" not in row:
        return None
    product = row["source_coordinate_product"]
    role, quantity = row.get("role"), row.get("quantity")
    supported = (role == "historical_prediction" and quantity in COORDINATES) or (
        role == "historical_comparison" and quantity in COMPARISONS
    )
    if (
        not isinstance(product, dict)
        or set(product) != {"authorities", "basis_context_id"}
        or not _authorities(product.get("authorities"))
        or not isinstance(product.get("basis_context_id"), str)
        or not re.fullmatch(
            r"context-(?:v\d+|s[a-z][a-z0-9-]*)-[0-9a-f]{20}", product["basis_context_id"]
        )
        or product["basis_context_id"] not in row.get("context_ids", [])
        or not supported
        or row.get("reference") is not None
        or row.get("event_id") is not None
        or row.get("model_name") is not None
        or any(
            key in row
            for key in (
                "source_prediction_kind",
                "source_model_attribution",
                "source_model_label",
                "source_eclipse_phase",
                "source_extent_unit",
                "time_reference",
                "source_difference_relation",
                "source_difference_reference",
                "comparison_relation",
                "source_comparison_sign",
            )
        )
        or row.get("direction")
        not in (
            (None, "north", "south")
            if quantity in ("declination", "ecliptic_latitude")
            else (None,)
        )
        or "not_an_additional_raw_reading" not in row.get("flags", [])
        or norm["status"] != "exact"
        or norm["unit"] != "arcsecond"
        or norm != normalize_quantity(row)
    ):
        raise ValueError(
            "Historical coordinate product requires its bound attribution and angular role"
        )
    return dict(
        authorities=list(product["authorities"]), basis_context_id=product["basis_context_id"]
    )
