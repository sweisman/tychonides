"""Qualifications for tabulated eclipse predictions with heterogeneous sources."""

from .normalization import normalize_quantity


def validate_eclipse_ephemeris(row, norm):
    """Accept only the declared eclipse columns, without inventing a phase or model."""
    if "source_prediction_kind" not in row:
        return False
    model = row.get("model_name")
    named = model in (
        "Alphonsine",
        "Prutenic",
        "Tycho Brahe",
        "Lansbergian",
        "Wendelen",
        "Kepler",
        "Boulliau",
        "Danish",
        "Parisian",
        "Philolaic",
        "Rudolphine",
        "Atlantic",
        "Tychonic",
    ) and not any(key in row for key in ("source_model_attribution", "source_model_label"))
    unnamed = model is None and (
        row.get("source_model_attribution"),
        row.get("source_model_label"),
    ) in (
        ("unnamed_as_stated", "old ephemeris"),
        ("unestablished_from_canon", "ephemerides"),
        ("unnamed_as_stated", "ephemerides"),
        ("unnamed_as_stated", "tables"),
    )
    if (
        row["source_prediction_kind"] != "eclipse_ephemeris"
        or row.get("role") != "historical_prediction"
        or row.get("subject") not in ("Sun", "Moon")
        or any(row.get(key) is not None for key in ("reference", "direction", "event_id"))
        or not (named or unnamed)
        or not {"not_an_additional_raw_reading", "not_an_observing_clock"}
        <= set(row.get("flags", []))
        or not isinstance(row.get("unit_basis"), str)
        or not row["unit_basis"].strip()
        or norm != normalize_quantity(row)
    ):
        raise ValueError(
            "Eclipse ephemeris requires its source model and prediction qualifications"
        )
    quantity = row.get("quantity")
    if quantity == "calculation_epoch":
        valid = (
            norm["unit"] == "second_of_time"
            and norm["status"] == "exact"
            and row.get("source_eclipse_phase")
            in ("beginning", "immersion", "middle", "end", "unstated")
            and row.get("time_reference")
            in ("source_after_noon", "source_after_midnight_label", "source_clock_origin_unstated")
            and "absolute_time_unestablished" in row.get("flags", [])
            and "source_extent_unit" not in row
        )
    elif quantity == "clock_elapsed_time":
        valid = norm["unit"] == "second_of_time" and (
            norm["status"] == "exact"
            or (
                norm["status"] == "unsupported"
                and "source_notation_unresolved" in row.get("flags", [])
                and not row.get("components")
            )
        )
        valid = valid and not any(
            key in row for key in ("source_eclipse_phase", "time_reference", "source_extent_unit")
        )
    elif quantity == "eclipse_extent":
        valid = (
            row.get("source_extent_unit") == "digit"
            and norm["unit"] == "source_eclipse_digit"
            and norm["status"] in ("exact", "unsupported")
            and not any(key in row for key in ("source_eclipse_phase", "time_reference"))
        )
    else:
        valid = False
    if not valid:
        raise ValueError("Eclipse ephemeris quantity, units, phase or clock reference disagree")
    return True
