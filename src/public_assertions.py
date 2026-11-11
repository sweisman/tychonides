"""Public assertions: shared catalogue responsibilities."""

from .normalization import (
    BODY_CALCULATIONS,
    HISTORICAL_INTERVAL_BODIES,
    normalize_quantity,
    VISUAL_REFERENCE_KINDS,
    unresolved_instrument_scalar,
    unresolved_visual_fraction,
    unresolved_source_distance,
    SOURCE_MILE_UNITS,
    SOURCE_WORD_NUMBERS,
    comparison_numeric_text,
)
from .public_relationships import identifier
import re
from fractions import Fraction
from .core import number, fraction_text
from .catalog import (
    ANGLE_QUANTITIES,
    source_key,
    source_fields,
    ANGULAR_RATES,
    ZODIAC_SIGNS,
    validate_reference_status,
    source_numeric_text,
)
from .public_policy import SUBJECTS
from .public_policy import REFERENCES
from .public_policy import QUANTITIES
from .public_policy import ROLES
from .public_policy import FLAGS
from .public_policy import FLAGS_EQUAL_VALUE
from .source_comparisons import project_size_comparison


def public_assertion(row, *, source_registry=()):
    key = source_key(row)
    if isinstance(key, str) and key not in source_registry:
        raise ValueError("Unregistered historical source")
    if row["subject"] not in SUBJECTS or row["reference"] not in REFERENCES:
        raise ValueError("Unreviewed public endpoint label")
    if row["quantity"] not in QUANTITIES or row["role"] not in ROLES:
        raise ValueError("Unreviewed public quantity/role")
    calendar_count = (
        row["subject"] == "calendar calculation"
        and row["quantity"] == "source_scalar"
        and (
            row["role"] in ("historical_input", "calculation_intermediate")
            or (row["role"] == "editorial_variant" and row.get("variant_of_id") is not None)
        )
        and row.get("source_parameter_kind")
        in (
            "source_year_count",
            "source_month_count",
            "source_day_count",
            "source_cycle_count",
            "source_week_count",
        )
        and row["reference"] is None
        and row.get("direction") is None
        and row.get("event_id") is None
        and row.get("model_name") is None
        and "not_an_additional_raw_reading" in row.get("flags", [])
    )
    if row["subject"] == "calendar calculation" and not calendar_count:
        raise ValueError("Calendar calculation requires an attributed native calendar count")
    if row["role"] == "source_alternative" and (
        row.get("variant_of_id") is None
        or not {"alternative_suggestion_not_applied", "not_an_additional_raw_reading"}
        <= set(row.get("flags", []))
    ):
        raise ValueError("Source alternative requires its original and explicit unapplied status")
    missing_reference = validate_reference_status(row)
    if (
        row["quantity"] in {"angular_separation", "angular_offset"}
        and row["reference"] is None
        and not missing_reference
    ):
        label = (
            "Angular separation" if row["quantity"] == "angular_separation" else "Angular offset"
        )
        raise ValueError(label + " requires both endpoints")
    from .source_locator import validate_page_locator

    page_locator = (
        validate_page_locator(row["source_page_locator"]) if "source_page_locator" in row else None
    )
    note_marker = row.get("edition_note_marker")
    edition_note = (
        isinstance(note_marker, str)
        and re.fullmatch(r"\[\^[\w-]+\]", note_marker) is not None
        and row["printed_page"] is None
        and row["role"] in ("editorial_addition", "editorial_variant", "editorial_suggestion")
        and {"source_annotation_variant", "not_an_additional_raw_reading"}
        <= set(row.get("flags", []))
        and (
            row["role"] == "editorial_addition"
            or "alternative_suggestion_not_applied" in row.get("flags", [])
        )
        and row.get("annotation_of_id") is not None
        and row["annotation_of_id"] != row["id"]
        and row.get("event_id") is None
    )
    if "edition_note_marker" in row and not edition_note:
        raise ValueError("Edition note citation requires a linked, unapplied editorial annotation")
    if (not isinstance(key, str) and key not in (10, 11, 12, 13)) or not (
        (type(row["printed_page"]) is int and row["printed_page"] > 0)
        or (row["printed_page"] is None and page_locator is not None)
        or edition_note
    ):
        raise ValueError("Public assertion needs a bibliographic page")
    norm = row["normalized"]
    from .source_predictions import validate_eclipse_ephemeris
    from .source_coordinate_products import project_coordinate_product

    tabulated_eclipse_prediction = validate_eclipse_ephemeris(row, norm)
    coordinate_product = project_coordinate_product(row, norm)
    equal_value = "source_value_equal_to_id" in row or FLAGS_EQUAL_VALUE in row.get("flags", [])
    equal_clock = (
        row["quantity"] == "recorded_clock"
        and row["role"] == "recorded_clock"
        and row["subject"] == "observing clock"
        and row["reference"] is None
    )
    equal_separation = row["quantity"] == "angular_separation" and row["role"] in (
        "recorded_reading",
        "repeated_reading",
        "calibration",
    )
    repeated_equal = row.get("source_equality_kind") == "repeated_measurement"
    if "source_equality_kind" in row and not (
        repeated_equal and equal_value and equal_separation and row["role"] == "repeated_reading"
    ):
        raise ValueError("Invalid repeated-measurement equality")
    if equal_value and (
        row.get("source_value_equal_to_id") is None
        or FLAGS_EQUAL_VALUE not in row.get("flags", [])
        or row.get("components")
        or not (equal_clock or equal_separation)
        or row.get("direction") is not None
        or (
            norm["status"] != "exact"
            and not (
                repeated_equal
                and norm["status"] == "unsupported"
                and "source_notation_unresolved" in row.get("flags", [])
                and norm.get("normalization_issue") == "source_notation_unresolved"
            )
        )
        or norm["unit"] != ("second_of_time" if equal_clock else "arcsecond")
        or norm["signed_magnitude"] is not None
    ):
        raise ValueError(
            "Stated equal value requires an explicit relation, unsigned angle and no invented components"
        )
    unresolved = row.get("source_angular_units_unresolved")
    notation_unresolved = "source_notation_unresolved" in row.get("flags", [])
    unresolved_chord = unresolved_instrument_scalar(row)
    parts = row.get("components") or {}
    noncanonical_degree = (
        row["quantity"] in ANGLE_QUANTITIES
        and not row.get("incomplete")
        and "sign_count" in parts
        and "degree" in parts
        and number(fraction_text(parts["degree"])) > 30
    )
    if row.get("zodiac_sign") is not None:
        expected_named_sign = normalize_quantity(row)
        noncanonical_degree = noncanonical_degree or (
            expected_named_sign.get("normalization_issue") == "degree_outside_sign"
        )
    if noncanonical_degree:
        if norm != normalize_quantity(row):
            raise ValueError("Noncanonical source components cannot export an adopted scalar")
    elif row["quantity"] == "unclassified_numeric_expression":
        expression = row.get("source_expression")
        numeric_expression = expression
        words = row.get("source_word_numbers", {})
        if not isinstance(words, dict):
            raise ValueError("Unclassified word numerals require a reviewed mapping")
        for word, value in words.items():
            if (
                not isinstance(word, str)
                or not isinstance(value, str)
                or SOURCE_WORD_NUMBERS.get(word) != value
                or not isinstance(numeric_expression, str)
            ):
                raise ValueError("Unreviewed unclassified word numeral")
            numeric_expression, count = re.subn(
                r"\b" + re.escape(word) + r"\b", value, numeric_expression
            )
            if not count:
                raise ValueError("Unclassified word numeral lacks literal evidence")
        recorded_pair = (
            row["role"] == "recorded_reading"
            and row["subject"] == "comet head"
            and {"limb_or_instrument_setting_unresolved", "reference_antecedent_unresolved"}
            <= set(row.get("flags", []))
            and isinstance(expression, str)
            and re.fullmatch(r"\d+\.\s+\d+\.", expression)
        )
        calculation = (
            row["role"] in ("calculation_intermediate", "historical_input")
            and row["subject"]
            in BODY_CALCULATIONS | {"Mars", "unidentified astronomical calculation"}
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        # These labels can denote angular places, clock components or calendar
        # arguments. Retain the complete literal without choosing a dimension.
        numeric_expression = (
            re.sub(
                r"\b(?:days?|hours?|minutes?|seconds?|thirds?|fourths?|parts?)\b",
                "",
                numeric_expression,
                flags=re.I,
            )
            if isinstance(numeric_expression, str)
            else numeric_expression
        )
        if isinstance(numeric_expression, str):
            numeric_expression = numeric_expression.replace(r"\|", "|")
        if (
            not (recorded_pair or calculation)
            or row["reference"] is not None
            or row.get("direction") is not None
            or row.get("components")
            or not isinstance(expression, str)
            or not 1 <= len(expression) <= 80
            or not re.search(r"\d", fraction_text(numeric_expression))
            or not re.fullmatch(r"[0-9¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞°′″‴⁗.,\[\]?+/:|()\s-]+", numeric_expression)
            or norm["status"] != "unsupported"
            or norm["unit"] != "source_numeric_expression"
            or norm.get("normalization_issue") != "physical_quantity_or_units_unresolved"
            or any(
                norm[k] is not None
                for k in (
                    "magnitude",
                    "magnitude_degrees",
                    "signed_magnitude",
                    "least_component_unit",
                )
            )
        ):
            raise ValueError(
                "Unclassified numerical expression requires a numeric-only literal and unresolved units"
            )
    elif unresolved is not None:
        parts = row.get("components", {})
        calculation_scope = (
            row["quantity"] == "calculation_angle"
            and row["subject"] in ("Mars", "Mars calculation", "Moon calculation")
            and row["reference"] is None
        )
        lunar_model_scope = (
            row["quantity"] in ("parallax_angle", "angular_diameter")
            and row["subject"] == "Moon"
            and row["reference"] == ("Earth" if row["quantity"] == "parallax_angle" else None)
        )
        if (
            unresolved is not True
            or not (calculation_scope or lunar_model_scope)
            or row.get("direction") is not None
            or row["role"] not in ("historical_input", "calculation_intermediate")
            or "not_an_additional_raw_reading" not in row.get("flags", [])
            or norm["status"] != "unsupported"
            or norm["unit"] != "arcsecond"
            or norm["least_component_unit"] is not None
            or any(
                norm[k] is not None for k in ("magnitude", "magnitude_degrees", "signed_magnitude")
            )
            or norm.get("normalization_issue") != "angular_component_units_unresolved"
            or not 2 <= len(parts) <= 4
            or set(parts) != {f"component_{n}" for n in range(1, len(parts) + 1)}
            or norm.get("source_components")
            != [
                str(number(fraction_text(parts[f"component_{n}"])))
                for n in range(1, len(parts) + 1)
            ]
        ):
            raise ValueError("Unreviewed unresolved angular components")
        if any(
            not isinstance(v, str) or not re.fullmatch(r"\d+(?:/[1-9]\d*)?", v)
            for v in norm["source_components"]
        ):
            raise ValueError("Invalid unresolved numeric component")
    elif notation_unresolved:
        visual_fraction = unresolved_visual_fraction(row)
        native_distance = unresolved_source_distance(row)
        native_part_length = row["quantity"] == "source_sexagesimal_length"
        proportional = row["quantity"] == "proportional_minutes"
        time_epoch = row["quantity"] == "calculation_epoch"
        recorded_clock = (
            row["quantity"] == "recorded_clock"
            and row["role"] == "recorded_clock"
            and row["subject"] == "observing clock"
            and row["reference"] is None
            and row.get("direction") is None
            and "absolute_time_unestablished" in row.get("flags", [])
        )
        clock_drift = (
            row["quantity"] == "clock_drift"
            and row["role"] == "calibration"
            and row["subject"] == "observing clock"
            and row["reference"] is None
            and row.get("direction") is None
        )
        calculation_interval = (
            row["quantity"] == "clock_elapsed_time"
            and (row["role"] == "historical_input" or tabulated_eclipse_prediction)
            and row["subject"] in HISTORICAL_INTERVAL_BODIES
            and row["reference"] is None
            and row.get("direction") is None
            and {"not_an_observing_clock", "not_an_additional_raw_reading"}
            <= set(row.get("flags", []))
        )
        native_eclipse = (
            row["quantity"] == "eclipse_extent" and row.get("source_extent_unit") == "digit"
        )
        magnitude_class = row["quantity"] == "stellar_magnitude_class"
        expected_unit = (
            "source_temporal_hour"
            if row["quantity"] == "temporal_hour_count"
            else "source_visual_magnitude_class"
            if magnitude_class
            else "source_fraction"
            if visual_fraction
            else "source_semidiameter"
            if native_distance
            else "source_length_part"
            if native_part_length
            else "ratio"
            if proportional
            else "source_eclipse_digit"
            if native_eclipse
            else "source_scalar"
            if unresolved_chord
            else "second_of_time"
            if time_epoch or recorded_clock or clock_drift or calculation_interval
            else ANGULAR_RATES.get(row["quantity"], "arcsecond")
        )
        if (
            (
                row["quantity"]
                not in ANGLE_QUANTITIES | {"calculation_epoch", "temporal_hour_count"}
                and not recorded_clock
                and not clock_drift
                and not calculation_interval
                and not unresolved_chord
                and not visual_fraction
                and not native_distance
                and not native_part_length
                and not proportional
                and not magnitude_class
                and not native_eclipse
            )
            or row.get("components")
            or row.get("incomplete")
            or (
                time_epoch
                and (
                    row["role"] != "calculation_epoch"
                    or row["subject"] not in ("Mars", "Sun", "Moon")
                    or not {"not_an_observing_clock", "not_an_additional_raw_reading"}
                    <= set(row.get("flags", []))
                )
            )
            or norm["status"] != "unsupported"
            or norm["unit"] != expected_unit
            or norm.get("normalization_issue") != "source_notation_unresolved"
            or "source_components" in norm
            or any(
                norm[k] is not None
                for k in (
                    "magnitude",
                    "magnitude_degrees",
                    "signed_magnitude",
                    "least_component_unit",
                )
            )
        ):
            raise ValueError("Unresolved source notation cannot export an interpreted scalar")
    elif "source_zodiac_sector" in row:
        if norm != normalize_quantity(row) or "not_an_additional_raw_reading" not in row.get(
            "flags", []
        ):
            raise ValueError("Zodiac sector requires verified range normalization")
    elif "source_components" in norm or "normalization_issue" in norm:
        raise ValueError("Unresolved components require explicit source unit uncertainty")
    if row["quantity"] == "separation_difference" and (
        row["reference"] is None
        or row["reference"] == row["subject"]
        or norm["unit"] != "arcsecond"
        or row["role"] not in ("historical_input", "reduction", "historical_comparison")
    ):
        raise ValueError(
            "Separation change requires distinct endpoints and a historical angle role"
        )
    if norm["status"] not in ("exact", "incomplete", "unsupported"):
        raise ValueError("Unknown normalization status")
    if norm["status"] == "incomplete" and any(
        norm[k] is not None for k in ("magnitude", "magnitude_degrees", "signed_magnitude")
    ):
        raise ValueError("Incomplete source quantities cannot export a numerical magnitude")
    if norm["unit"] not in {
        "arcsecond",
        "second_of_time",
        "source_temporal_hour",
        "source_semidiameter",
        "ratio",
        "source_clock_component",
        "source_angle_component",
        "source_fraction",
        "source_scalar",
        "source_numeric_expression",
        "source_visual_magnitude_class",
        "source_eclipse_point",
        "source_eclipse_digit",
        "source_length_part",
        "source_pace",
        "source_stadium",
        "square_degree",
        *SOURCE_MILE_UNITS.values(),
        *ANGULAR_RATES.values(),
    }:
        raise ValueError("Unknown normalized unit")
    if (norm["unit"] == "source_scalar") != (row["quantity"] == "source_scalar"):
        raise ValueError("Source scalar quantity/unit mismatch")
    if row["quantity"] == "distance_in_stadia" or norm["unit"] == "source_stadium":
        if (
            row["quantity"] != "distance_in_stadia"
            or norm["unit"] != "source_stadium"
            or norm != normalize_quantity(row)
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError("Stadia require their unchanged native length normalization")
    if row["quantity"] == "angular_area" or norm["unit"] == "square_degree":
        if (
            row["quantity"] != "angular_area"
            or norm["unit"] != "square_degree"
            or norm != normalize_quantity(row)
        ):
            raise ValueError("Sky area requires its unchanged square-degree value")
    if row["quantity"] == "temporal_hour_count" or norm["unit"] == "source_temporal_hour":
        if (
            row["quantity"] != "temporal_hour_count"
            or norm["unit"] != "source_temporal_hour"
            or row["reference"] is not None
            or norm != normalize_quantity(row)
        ):
            raise ValueError("Temporal-hour count requires its unchanged native unit and value")
    if (
        row["quantity"] == "stellar_magnitude_class"
        or norm["unit"] == "source_visual_magnitude_class"
    ):
        if (
            row["quantity"] != "stellar_magnitude_class"
            or norm["unit"] != "source_visual_magnitude_class"
            or (
                row["role"]
                not in (
                    "recorded_reading",
                    "historical_input",
                    "adopted_value",
                    "editorial_variant",
                )
                and not (
                    row["role"] == "source_alternative"
                    and row.get("variant_of_id") is not None
                    and row.get("event_id") is None
                    and "alternative_suggestion_not_applied" in row.get("flags", [])
                )
            )
            or row["reference"] is not None
            or row.get("direction") is not None
            or row.get("model_name") is not None
            or (
                row["role"] != "recorded_reading"
                and "not_an_additional_raw_reading" not in row.get("flags", [])
            )
            or norm != normalize_quantity(row)
        ):
            raise ValueError(
                "Native stellar magnitude requires its source class and qualifications"
            )
    if row["quantity"] in SOURCE_MILE_UNITS or norm["unit"] in SOURCE_MILE_UNITS.values():
        if (
            norm["unit"] != SOURCE_MILE_UNITS.get(row["quantity"])
            or row["role"] not in ("historical_input", "calculation_intermediate")
            or "not_an_additional_raw_reading" not in row.get("flags", [])
            or norm != normalize_quantity(row)
        ):
            raise ValueError("Historical mile distance requires verified native units")
    if row["quantity"] == "distance_in_paces" or norm["unit"] == "source_pace":
        if (
            row["quantity"] != "distance_in_paces"
            or norm["unit"] != "source_pace"
            or row["role"] not in ("historical_input", "calculation_intermediate")
            or "not_an_additional_raw_reading" not in row.get("flags", [])
            or norm != normalize_quantity(row)
        ):
            raise ValueError("Pace distance requires verified native units")
    eclipse_extent = row["quantity"] == "eclipse_extent"
    if (norm["unit"] in ("source_eclipse_point", "source_eclipse_digit")) != eclipse_extent:
        raise ValueError("Eclipse point quantity/unit mismatch")
    native_digits = row.get("source_extent_unit") == "digit"
    if "source_extent_unit" in row and (
        not eclipse_extent
        or not native_digits
        or norm["unit"] != "source_eclipse_digit"
        or row["role"] not in ("historical_prediction", "historical_input")
    ):
        raise ValueError("Native eclipse digits require a verified source calculation")
    if eclipse_extent and (
        row["role"]
        not in (
            ("historical_prediction", "historical_input")
            if native_digits
            else ("historical_prediction", "recorded_reading")
        )
        or row["subject"]
        not in (("Moon", "Sun", "Sun and Moon") if native_digits else ("Moon", "Sun"))
        or row["reference"] is not None
        or (
            row.get("model_name") not in (None, "Alphonsine", "Magini", "Origanus", "Tycho Brahe")
            and not tabulated_eclipse_prediction
        )
        or not {"not_an_additional_raw_reading", "not_an_observing_clock"}
        <= set(row.get("flags", []))
        or norm != normalize_quantity(row)
    ):
        raise ValueError("Eclipse extent requires a verified native tabular quantity")
    if (
        eclipse_extent
        and row["role"] == "recorded_reading"
        and (
            row.get("model_name") is not None
            or "source_visual_estimate" not in row.get("flags", [])
        )
    ):
        raise ValueError("Observed eclipse extent cannot acquire model attribution")
    predicted_eclipse_digits = False
    native_length = row["quantity"] == "source_sexagesimal_length"
    native_length_variant = (
        native_length
        and row["role"] == "editorial_variant"
        and row.get("variant_of_id") is not None
        and row.get("annotation_of_id") == row.get("variant_of_id")
        and row.get("event_id") is None
        and {"source_annotation_variant", "alternative_suggestion_not_applied"}
        <= set(row.get("flags", []))
    )
    if (norm["unit"] == "source_length_part") != native_length:
        raise ValueError("Native length quantity/unit mismatch")
    if native_length and (
        (
            row["role"] not in ("historical_input", "calculation_intermediate")
            and not native_length_variant
        )
        or row["subject"] not in BODY_CALCULATIONS
        or row["reference"] is not None
        or "not_an_additional_raw_reading" not in row.get("flags", [])
        or norm != normalize_quantity(row)
    ):
        raise ValueError("Native length requires verified nonangular components")
    if row["quantity"] == "source_scalar" and not unresolved_chord:
        catalogue_count = (
            row["subject"] in {"fixed stars"} | BODY_CALCULATIONS
            and row["role"] in ("historical_input", "calculation_intermediate")
            and row.get("source_parameter_kind") == "source_record_count"
            and row.get("model_name") is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        historical = (
            (
                row["role"] == "historical_input"
                or (
                    row["role"] == "editorial_variant"
                    and row.get("source_parameter_kind")
                    in ("source_year_count", "source_month_count")
                    and row.get("variant_of_id") is not None
                    and row.get("annotation_of_id") == row.get("variant_of_id")
                    and row.get("event_id") is None
                    and row.get("model_name") is None
                    and {"source_annotation_variant", "alternative_suggestion_not_applied"}
                    <= set(row.get("flags", []))
                )
                or (
                    row["role"] == "printed_correction"
                    and row.get("source_parameter_kind") == "comparison_multiplier"
                    and row.get("variant_of_id") is not None
                    and row.get("event_id") is None
                    and row.get("model_name") is None
                    and "alternative_suggestion_not_applied" in row.get("flags", [])
                )
                or (
                    row["role"] == "source_alternative"
                    and row["subject"] == "Moon calculation"
                    and row.get("source_parameter_kind") == "unlabelled_table_value"
                )
            )
            and row["subject"]
            in BODY_CALCULATIONS | {"stellar calibration calculation", "comet calculation"}
            and row.get("source_parameter_kind")
            in (
                "eccentricity_as_stated",
                "tabular_argument_unit_unstated",
                "unresolved_instruction_count",
                "comparison_multiplier",
                "unlabelled_table_value",
                "source_record_count",
                "source_year_count",
                "source_month_count",
            )
            and (
                row["subject"] == "Mars calculation"
                or (
                    row["subject"]
                    in BODY_CALCULATIONS | {"comet calculation", "stellar calibration calculation"}
                    and row.get("source_parameter_kind") == "comparison_multiplier"
                )
                or row.get("source_parameter_kind") in ("source_year_count", "source_month_count")
                or (
                    row["subject"] == "Moon calculation"
                    and row.get("source_parameter_kind") == "unlabelled_table_value"
                )
            )
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        visual = (
            row["role"] == "recorded_reading"
            and row["subject"] in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
            and row.get("source_parameter_kind") == "visual_coefficient_as_stated"
            and row.get("model_name") is None
            and {"source_visual_estimate", "geometry_interpretation_unestablished"}
            <= set(row.get("flags", []))
            and norm["magnitude"] is not None
            and Fraction(norm["magnitude"]) > 0
        )
        calculation = (
            row["subject"]
            in BODY_CALCULATIONS | {"comet calculation", "stellar calibration calculation"}
            and (
                row["role"] in ("historical_input", "calculation_intermediate")
                or (row["role"] == "editorial_addition" and edition_note)
                or (
                    row["role"] == "editorial_variant"
                    and row.get("variant_of_id") is not None
                    and row.get("event_id") is None
                    and "alternative_suggestion_not_applied" in row.get("flags", [])
                )
            )
            and row.get("source_parameter_kind")
            in (
                "trigonometric_radius",
                "scaled_sine",
                "sine_increment_per_source_second",
                "scaled_secant",
                "scaled_tangent",
                "arithmetic_intermediate",
            )
            and row.get("model_name") is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        unscaled_sine = (
            row["subject"] in ("stellar calibration calculation", "planetary motion calculation")
            and row["role"] == "historical_input"
            and row.get("source_parameter_kind") == "sine_value_scale_unstated"
            and row.get("model_name") is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        model_length = (
            row["subject"] in BODY_CALCULATIONS
            and (
                row["role"]
                in ("historical_input", "calculation_intermediate", "source_alternative")
                or (
                    row["role"] == "editorial_variant"
                    and row.get("variant_of_id") is not None
                    and row.get("annotation_of_id") == row.get("variant_of_id")
                    and row.get("event_id") is None
                    and {"source_annotation_variant", "alternative_suggestion_not_applied"}
                    <= set(row.get("flags", []))
                )
            )
            and row.get("source_parameter_kind") == "model_length"
            and row.get("model_name") is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
            and norm["magnitude"] is not None
            and Fraction(norm["magnitude"]) > 0
        )
        instrument_chord = (
            row["role"] in ("recorded_reading", "source_alternative")
            and row["subject"] == "Sun"
            and row.get("source_parameter_kind") == "instrument_chord"
            and row.get("model_name") is None
            and norm["magnitude"] is not None
            and Fraction(norm["magnitude"]) >= 0
        )
        calculated_chord = (
            row["role"] in ("historical_input", "calculation_intermediate", "reduction")
            and row["subject"] in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
            and row.get("source_parameter_kind") == "calculated_chord"
            and row.get("model_name") is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
            and norm["magnitude"] is not None
            and Fraction(norm["magnitude"]) >= 0
        )
        instrument_linear = (
            row["role"] == "recorded_reading"
            and row.get("source_parameter_kind") == "instrument_linear_reading"
            and row.get("model_name") is None
            and norm["magnitude"] is not None
            and Fraction(norm["magnitude"]) > 0
        )
        instrument_construction = (
            row["subject"] == "instrument"
            and row["role"] == "historical_input"
            and row.get("event_id") is None
            and row.get("model_name") is None
            and row.get("source_parameter_kind")
            in (
                "instrument_dimension_cubits",
                "instrument_dimension_feet",
                "instrument_dimension_inches",
                "instrument_dimension_palms",
                "instrument_dimension_digits",
                "instrument_dimension_ratio",
                "instrument_count",
                "instrument_component_count",
                "instrument_circle_count",
                "instrument_scale_divisions",
                "instrument_scale_digit_count",
                "instrument_scale_value",
            )
            and "not_an_additional_raw_reading" in row.get("flags", [])
            and norm["magnitude"] is not None
            and Fraction(norm["magnitude"]) > 0
            and (
                row["source_parameter_kind"]
                in (
                    "instrument_dimension_cubits",
                    "instrument_dimension_feet",
                    "instrument_dimension_inches",
                    "instrument_dimension_palms",
                    "instrument_dimension_digits",
                    "instrument_dimension_ratio",
                    "instrument_circle_count",
                )
                or Fraction(norm["magnitude"]).denominator == 1
            )
        )
        clock_count = (
            row["subject"] == "observing clock"
            and row.get("model_name") is None
            and row["reference"] is None
            and norm["magnitude"] is not None
            and Fraction(norm["magnitude"]) > 0
            and Fraction(norm["magnitude"]).denominator == 1
            and (
                (
                    row.get("source_parameter_kind") == "clock_wheel_teeth"
                    and row["role"] == "calibration"
                    and "not_an_additional_raw_reading" in row.get("flags", [])
                )
                or (
                    row.get("source_parameter_kind")
                    in ("clock_complete_turns", "clock_additional_teeth")
                    and row["role"] == "recorded_reading"
                )
            )
        )
        eclipse_digits = (
            row["role"] == "recorded_reading"
            and row["subject"] in ("Moon", "Sun")
            and row.get("source_parameter_kind") == "eclipse_digit_count"
            and row.get("model_name") is None
            and "source_visual_estimate" in row.get("flags", [])
            and norm["magnitude"] is not None
            and Fraction(norm["magnitude"]) > 0
        )
        predicted_eclipse_digits = (
            row["role"] == "historical_prediction"
            and row["subject"] == "Moon"
            and row.get("source_parameter_kind") == "eclipse_digit_count"
            and row.get("model_name") == "Alphonsine"
            and {"not_an_additional_raw_reading", "not_an_observing_clock"}
            <= set(row.get("flags", []))
            and norm["magnitude"] is not None
            and Fraction(norm["magnitude"]) > 0
        )
        if (
            norm["status"] != "exact"
            or norm["least_component_unit"] != "scalar"
            or norm["magnitude_degrees"] is not None
            or norm["signed_magnitude"] is not None
            or row.get("direction") is not None
            or (row["reference"] is not None and not instrument_linear)
            or not (
                historical
                or catalogue_count
                or calendar_count
                or visual
                or calculation
                or unscaled_sine
                or model_length
                or instrument_chord
                or calculated_chord
                or instrument_linear
                or instrument_construction
                or clock_count
                or eclipse_digits
                or predicted_eclipse_digits
            )
        ):
            raise ValueError("Unreviewed unscaled source scalar")
        if model_length:
            scale = row.get("source_scalar_scale")
            if not isinstance(scale, str) or not re.fullmatch(r"[1-9]\d*", scale):
                raise ValueError("Model length requires its positive stated reference scale")
        elif calculation and row.get("source_parameter_kind") == "scaled_sine":
            scale = row.get("source_scalar_scale")
            if (
                not isinstance(scale, str)
                or not re.fullmatch(r"[1-9]\d*", scale)
                or not 0 <= Fraction(norm["magnitude"]) <= Fraction(scale)
            ):
                raise ValueError(
                    "Scaled sine requires its positive source scale and bounded native value"
                )
        elif calculation and row.get("source_parameter_kind") == "scaled_tangent":
            scale = row.get("source_scalar_scale")
            if not isinstance(scale, str) or not re.fullmatch(r"[1-9]\d*", scale):
                raise ValueError("Scaled tangent requires its positive stated radius scale")
        elif calculation and row.get("source_parameter_kind") == "sine_increment_per_source_second":
            scale = row.get("source_scalar_scale")
            if not isinstance(scale, str) or not re.fullmatch(r"[1-9]\d*", scale):
                raise ValueError("Sine increment requires its positive source radius scale")
        elif calculation and row.get("source_parameter_kind") == "scaled_secant":
            scale = row.get("source_scalar_scale")
            if (
                not isinstance(scale, str)
                or not re.fullmatch(r"[1-9]\d*", scale)
                or Fraction(norm["magnitude"]) < Fraction(scale)
            ):
                raise ValueError(
                    "Scaled secant requires a source scale and value at least that scale"
                )
        elif (
            calculation
            and row.get("source_parameter_kind") == "trigonometric_radius"
            and "source_scalar_scale" in row
        ):
            scale = row["source_scalar_scale"]
            if (
                not isinstance(scale, str)
                or not re.fullmatch(r"[1-9]\d*", scale)
                or Fraction(norm["magnitude"]) != Fraction(scale)
            ):
                raise ValueError("Trigonometric radius must equal its stated source scale")
        elif calculated_chord:
            scale = row.get("source_scalar_scale")
            if not isinstance(scale, str) or not re.fullmatch(r"[1-9]\d*", scale):
                raise ValueError("Calculated chord requires its positive stated radius scale")
            if Fraction(norm["magnitude"]) > 2 * Fraction(
                scale
            ) and "source_quality_note_present" not in row.get("flags", []):
                raise ValueError(
                    "Printed chord beyond twice its radius requires a source qualification"
                )
        elif instrument_chord and "source_scalar_scale" in row:
            scale = row["source_scalar_scale"]
            if (
                not isinstance(scale, str)
                or not re.fullmatch(r"[1-9]\d*", scale)
                or Fraction(norm["magnitude"]) > 2 * Fraction(scale)
            ):
                raise ValueError("Instrument chord exceeds its stated source scale")
        elif "source_scalar_scale" in row:
            raise ValueError(
                "Source scale metadata requires a scaled trigonometric value or model length"
            )
    elif "source_scalar_scale" in row and not (
        (
            unresolved_chord
            and row.get("source_parameter_kind")
            in ("model_length", "scaled_sine", "sine_increment_per_source_second")
        )
        or (
            native_length
            and isinstance(row["source_scalar_scale"], str)
            and re.fullmatch(r"[1-9]\d*", row["source_scalar_scale"]) is not None
        )
    ):
        raise ValueError("Source scale metadata requires a scalar or verified native length scale")
    if (
        row["quantity"] == "source_scalar"
        and row.get("source_parameter_kind") == "source_record_count"
        and Fraction(norm["magnitude"]).denominator != 1
    ):
        raise ValueError("Source record count must be a whole literal count")
    if (norm["unit"] == "source_fraction") != (row["quantity"] == "source_fraction"):
        raise ValueError("Source fraction quantity/unit mismatch")
    if row["quantity"] == "source_fraction":
        lunar_limb = (
            row["subject"] == "Moon lower horn"
            and row["reference"] == "Mars"
            and row["role"] == "recorded_reading"
            and row.get("source_fraction_kind") == "lunar_diameter"
            and row.get("comparison_relation") == "limb_separation_as_stated"
            and {
                "source_visual_estimate",
                "geometry_interpretation_unestablished",
                "source_upper_bound",
            }
            <= set(row.get("flags", []))
            and norm["magnitude"] is not None
            and 0 < Fraction(norm["magnitude"]) < 1
        )
        calibration = (
            row["role"] == "calibration"
            and row.get("source_fraction_kind") == "calibration_difference_unit_unstated"
            and row.get("comparison_relation") == "less_than_both_as_stated"
            and row["subject"] == "Aldebaran"
            and row["reference"] == "northern horn of Taurus"
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        historical = (
            row["role"] == "historical_correction"
            and row.get("source_fraction_kind") == "latitude_reconciliation"
            and row.get("comparison_relation") in ("greater_than_computed", "less_than_computed")
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        proximity = (
            row["role"] == "recorded_reading"
            and row.get("source_fraction_kind") == "comparative_line_proximity"
            and row.get("comparison_relation") == "nearer_by_fraction_as_stated"
            and {"source_visual_estimate", "geometry_interpretation_unestablished"}
            <= set(row.get("flags", []))
            and norm["magnitude"] is not None
            and 0 < Fraction(norm["magnitude"]) < 1
        )
        lunar = (
            row["subject"] in ("Moon", "Moon centre")
            and row["reference"] == "Aldebaran"
            and row["role"] in ("recorded_reading", "historical_input")
            and {"source_visual_estimate", "geometry_interpretation_unestablished"}
            <= set(row.get("flags", []))
            and norm["magnitude"] is not None
            and Fraction(norm["magnitude"]) > 0
            and (
                (
                    row.get("source_fraction_kind") == "lunar_illuminated_portion"
                    and row.get("comparison_relation")
                    in ("separation_as_stated", "greater_than_reference_fraction")
                )
                or (
                    row.get("source_fraction_kind")
                    in ("lunar_semidiameter", "lunar_reference_unstated")
                    and row.get("comparison_relation") == "latitude_offset_as_stated"
                )
            )
            and (
                row.get("comparison_relation") != "greater_than_reference_fraction"
                or "source_lower_bound" in row.get("flags", [])
            )
        )
        unresolved_visual = unresolved_visual_fraction(row)
        visual_native = (
            row.get("source_fraction_kind") in VISUAL_REFERENCE_KINDS
            and row["reference"] is not None
            and row["role"] in ("recorded_reading", "historical_input")
            and {"source_visual_estimate", "geometry_interpretation_unestablished"}
            <= set(row.get("flags", []))
            and (
                unresolved_visual
                or (norm["magnitude"] is not None and Fraction(norm["magnitude"]) > 0)
            )
            and row.get("comparison_relation")
            in (
                "separation_as_stated",
                "greater_than_reference_fraction",
                "less_than_reference_fraction",
                "at_least_reference_fraction",
                "at_most_reference_fraction",
            )
            and (
                row["role"] != "historical_input"
                or "not_an_additional_raw_reading" in row.get("flags", [])
            )
            and (
                row["comparison_relation"]
                not in ("greater_than_reference_fraction", "at_least_reference_fraction")
                or "source_lower_bound" in row.get("flags", [])
            )
            and (
                row["comparison_relation"]
                not in ("less_than_reference_fraction", "at_most_reference_fraction")
                or "source_upper_bound" in row.get("flags", [])
            )
        )
        if (
            (
                not unresolved_visual
                and (norm["status"] != "exact" or norm["least_component_unit"] != "fraction")
            )
            or (
                unresolved_visual
                and (
                    norm["status"] != "unsupported"
                    or norm["magnitude"] is not None
                    or norm["least_component_unit"] is not None
                )
            )
            or norm["magnitude_degrees"] is not None
            or norm["signed_magnitude"] is not None
            or row.get("direction") is not None
            or row.get("model_name") is not None
            or not (
                visual_native
                or lunar_limb
                or calibration
                or lunar
                or (
                    (historical or proximity)
                    and row["subject"] == "Mars"
                    and row["reference"] is None
                )
            )
        ):
            raise ValueError("Unreviewed source fraction or comparison scope")
    elif "source_fraction_kind" in row:
        raise ValueError("Fraction interpretation requires a source fraction")
    if (norm["unit"] == "source_angle_component") != (row["quantity"] == "angle_component"):
        raise ValueError("Angle-component quantity/unit mismatch")
    if row["quantity"] == "instrument_dimension_angle" or row["subject"] == "Radius brass channel":
        if (
            row["quantity"] != "instrument_dimension_angle"
            or row["subject"] != "Radius brass channel"
            or row["role"] != "historical_input"
            or row["reference"] is not None
            or row.get("direction") is not None
            or norm["status"] != "exact"
            or norm["unit"] != "arcsecond"
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError(
                "Instrument dimension is not a celestial position, parallax or applied correction"
            )
    if row["quantity"] == "angle_component" and (
        row["role"] not in ("editorial_variant", "editorial_suggestion")
        or row.get("direction") is not None
        or (
            row["role"] == "editorial_suggestion"
            and "alternative_suggestion_not_applied" not in row.get("flags", [])
        )
        or norm["status"] != "exact"
        or norm["least_component_unit"] not in ("degree", "arcminute")
        or norm["magnitude_degrees"] is not None
        or norm["signed_magnitude"] is not None
        or row.get("event_id") is not None
        or row.get("annotation_of_id") is None
        or not {
            "source_annotation_variant",
            "not_a_complete_angle",
            "not_an_additional_raw_reading",
        }
        <= set(row.get("flags", []))
    ):
        raise ValueError(
            "Angle component requires a linked editorial annotation, not a complete angle"
        )
    if (norm["unit"] == "source_clock_component") != (row["quantity"] == "clock_component"):
        raise ValueError("Clock-component quantity/unit mismatch")
    if row["quantity"] == "clock_component" and (
        row["role"] != "editorial_variant"
        or row["subject"] != "observing clock"
        or row["reference"] is not None
        or row.get("direction") is not None
        or norm["status"] != "exact"
        or norm["least_component_unit"] != "minute"
        or norm["magnitude_degrees"] is not None
        or norm["signed_magnitude"] is not None
        or row.get("event_id") is not None
        or row.get("annotation_of_id") is None
        or not {"source_annotation_variant", "not_an_observing_clock"} <= set(row.get("flags", []))
    ):
        raise ValueError(
            "Clock component requires a linked editorial annotation, not an observing time"
        )
    if row["quantity"] == "horizon_inclination" and (
        (row["subject"], row["reference"]) not in (("Mars", "Mercury"), ("Mercury", "Mars"))
        or row.get("direction") is not None
        or norm["unit"] != "arcsecond"
        or row["role"] not in ("historical_input", "recorded_reading", "contextual_coordinate")
    ):
        raise ValueError("Unreviewed horizon inclination relationship")
    if (norm["unit"] == "ratio") != (
        row["quantity"]
        in ("correction_ratio", "separation_ratio", "proportional_minutes", "source_scale_ratio")
    ):
        raise ValueError("Public correction ratio quantity/unit mismatch")
    if norm["unit"] == "ratio" and (
        norm["magnitude_degrees"] is not None
        or norm["signed_magnitude"] is not None
        or row.get("direction") is not None
    ):
        raise ValueError("Invalid public correction ratio normalization")
    if row["quantity"] == "correction_ratio" and norm["least_component_unit"] != "ratio":
        raise ValueError("Correction ratio needs ratio precision unit")
    if row["quantity"] == "proportional_minutes":
        coefficient_variant = (
            row["role"] == "editorial_variant"
            and row.get("variant_of_id") is not None
            and row.get("variant_of_id") != row["id"]
            and row.get("annotation_of_id") == row.get("variant_of_id")
            and row.get("event_id") is None
            and {"source_annotation_variant", "alternative_suggestion_not_applied"}
            <= set(row.get("flags", []))
        )
        exact_coefficient = (
            norm["status"] == "exact"
            and norm["least_component_unit"]
            in ("proportional_minute", "proportional_second", "proportional_third")
            and norm["magnitude"] is not None
            and 0 <= Fraction(norm["magnitude"]) <= 1
        )
        unresolved_coefficient = notation_unresolved and norm["status"] == "unsupported"
        if (
            not (exact_coefficient or unresolved_coefficient)
            or (
                row["role"] not in ("historical_input", "calculation_intermediate", "reduction")
                and not coefficient_variant
            )
            or row["subject"]
            not in (
                "Mars",
                "Moon",
                "Saturn",
                "Jupiter",
                "Venus",
                "Mercury",
                "fixed stars",
                "Saturn, Jupiter and Mars calculation",
                "planetary motion calculation",
            )
            or row["reference"] is not None
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError("Unreviewed proportional coefficient or scale")
    scale_parts = {key: norm.get(key) for key in ("source_scale_part", "source_reference_scale")}
    if row["quantity"] == "source_scale_ratio":
        geometry = (
            row["subject"] == "eccentric centre of Mars"
            and row["reference"] == "Earth"
            and "source_parameter_kind" not in row
        )
        eccentricity = (
            row["subject"] == "Mars calculation"
            and row["reference"] is None
            and row.get("source_parameter_kind") == "eccentricity_as_stated"
        )
        if (
            row["role"] != "historical_input"
            or not (geometry or eccentricity)
            or norm["status"] != "exact"
            or norm["least_component_unit"] != "source_part"
            or "not_an_additional_raw_reading" not in row.get("flags", [])
            or any(
                not isinstance(v, str) or not re.fullmatch(r"\d+(?:/[1-9]\d*)?", v)
                for v in scale_parts.values()
            )
        ):
            raise ValueError("Unreviewed source-scale ratio or endpoints")
        part, whole = (
            Fraction(scale_parts[key]) for key in ("source_scale_part", "source_reference_scale")
        )
        if whole <= 0 or Fraction(norm["magnitude"]) != part / whole:
            raise ValueError("Inconsistent source-scale ratio")
    elif any(v is not None for v in scale_parts.values()):
        raise ValueError("Source-scale parts require a source-scale ratio")
    if norm["unit"] in ANGULAR_RATES.values() or row["quantity"] in ANGULAR_RATES:
        if norm["unit"] != ANGULAR_RATES.get(row["quantity"]):
            raise ValueError("Public angular motion quantity/unit mismatch")
        if norm["magnitude_degrees"] is not None or norm["signed_magnitude"] is not None:
            raise ValueError("Angular motion is a rate, not a signed angular position")
    if (norm["unit"] == "source_semidiameter") != (row["quantity"] == "distance_in_semidiameters"):
        raise ValueError("Public source-distance quantity/unit mismatch")
    if norm["unit"] == "source_semidiameter" and (
        (
            norm["least_component_unit"]
            not in ("semidiameter", "semidiameter_minute", "semidiameter_second")
            and not (unresolved_source_distance(row) and norm["least_component_unit"] is None)
        )
        or norm["magnitude_degrees"] is not None
        or norm["signed_magnitude"] is not None
        or row.get("direction") is not None
    ):
        raise ValueError("Invalid public source-distance normalization")
    if norm["least_component_unit"] in ("day_minute", "day_second", "day_third") and (
        row["quantity"] != "clock_elapsed_time" or norm["unit"] != "second_of_time"
    ):
        raise ValueError("Sexagesimal day parts require an elapsed duration")
    if norm["least_component_unit"] not in (
        None,
        "sign_count",
        "sexagena",
        "degree",
        "arcminute",
        "arcsecond",
        "day",
        "arcsexagesimal_third",
        "arcsexagesimal_fourth",
        "arcsexagesimal_fifth",
        "arcsexagesimal_sixth",
        "arcsexagesimal_seventh",
        "arcsexagesimal_eighth",
        "arcsexagesimal_ninth",
        "arcsexagesimal_tenth",
        "day_minute",
        "day_second",
        "day_third",
        "day_fourth",
        "day_fifth",
        "day_sixth",
        "hour",
        "minute",
        "second",
        "time_third",
        "time_fourth",
        "time_fifth",
        "semidiameter",
        "semidiameter_minute",
        "semidiameter_second",
        "mile",
        "mile_minute",
        "mile_second",
        "ratio",
        "proportional_minute",
        "proportional_second",
        "proportional_third",
        "point",
        "point_minute",
        "digit",
        "digit_minute",
        "digit_second",
        "source_part",
        "part_minute",
        "part_second",
        "fraction",
        "scalar",
    ):
        raise ValueError("Unknown recorded precision unit")
    numeric = {}
    for key in ("magnitude", "magnitude_degrees", "signed_magnitude"):
        value = norm[key]
        if value is not None:
            if not isinstance(value, str) or not re.fullmatch(r"-?\d+(?:/[1-9]\d*)?", value):
                raise ValueError("Invalid exact public number")
            Fraction(value)
        numeric[key] = value
    if row.get("direction") not in (None, "north", "south", "east", "west"):
        raise ValueError("Unknown public direction")
    if row.get("record_status") not in (None, "recorded", "cancelled"):
        raise ValueError("Unknown public status")
    ordinal = row.get("ordinal")
    if ordinal is not None and (type(ordinal) is not int or ordinal < 1):
        raise ValueError("Invalid ordinal")
    if any(flag not in FLAGS for flag in row.get("flags", [])):
        raise ValueError("Unreviewed public quality flag")
    if row["quantity"] == "polar_distance" and (
        row.get("direction") is not None or norm["signed_magnitude"] is not None
    ):
        raise ValueError("Polar distance is not a signed declination")
    if row["quantity"] == "unclassified_angle" or "measurement_type_unresolved" in row.get(
        "flags", []
    ):
        if (
            row["quantity"] != "unclassified_angle"
            or not (
                (
                    row["role"] in ("recorded_reading", "source_alternative")
                    and "measurement_type_unresolved" in row.get("flags", [])
                )
                or (
                    row["role"] == "historical_input"
                    and "not_an_additional_raw_reading" in row.get("flags", [])
                )
            )
            or row.get("direction") is not None
            or row["reference"] is not None
            or row.get("model_name") is not None
            or norm["unit"] != "arcsecond"
            or norm["signed_magnitude"] is not None
        ):
            raise ValueError(
                "Unclassified angle must retain its unresolved type without a directional or model interpretation"
            )
    if "source_quality_note_later_hand" in row.get("flags", []) and (
        row["quantity"] != "angular_separation"
        or row["role"] != "calibration"
        or norm["unit"] != "arcsecond"
        or "source_quality_note_present" not in row.get("flags", [])
    ):
        raise ValueError(
            "Later-hand quality attribution requires a qualified calibration separation"
        )
    if "source_future_meridian_reduction" in row.get("flags", []) and (
        row["quantity"] != "angular_separation"
        or row["role"] != "adopted_value"
        or norm["unit"] != "arcsecond"
    ):
        raise ValueError("Future meridian reduction requires a source adopted separation")
    if "source_joint_motion_unallocated" in row.get("flags", []) and (
        row["quantity"] != "angular_daily_motion"
        or row["role"] != "historical_input"
        or row["subject"] not in ("Mars", "Jupiter", "Venus", "Mercury")
        or row["reference"] not in ("Sun", "simple Sun", "mean Sun")
        or norm["unit"] != "arcsecond_per_source_day"
    ):
        raise ValueError(
            "Joint motion requires a source daily term with planetary and solar endpoints"
        )
    if "source_unit_inherited" in row.get("flags", []) and (
        row["quantity"] != "distance_in_semidiameters"
        or row.get("source_semidiameter_body") != "Earth"
    ):
        raise ValueError("Unreviewed inherited distance unit")
    if "source_horizontal_parallax" in row.get("flags", []) and (
        row["quantity"] != "parallax_angle"
        or row["reference"] != "Earth"
        or norm["unit"] != "arcsecond"
    ):
        raise ValueError("Horizontal parallax flag requires an Earth-referenced parallax angle")
    if "source_completed_hour_uninterpreted" in row.get("flags", []) and (
        row["quantity"] != "calculation_epoch"
        or row["role"] != "calculation_epoch"
        or norm["unit"] != "second_of_time"
        or norm["least_component_unit"] != "hour"
        or row.get("direction") is not None
    ):
        raise ValueError("Completed-hour qualification requires an hour-valued calculation epoch")
    if row.get("source_component_label") not in (
        None,
        "inf.",
        "sup.",
        "one pinnule",
        "other pinnule",
        "both pinnules",
        "with both",
        "with one",
        "with the other",
        "declination",
        "right_ascension",
    ):
        raise ValueError("Unknown public source component label")
    if row.get("source_component_label") in ("declination", "right_ascension") and (
        row["quantity"] != "refraction_angle"
        or row["role"] != "historical_correction"
        or "not_an_additional_raw_reading" not in row.get("flags", [])
    ):
        raise ValueError(
            "Equatorial refraction components require a qualified historical correction"
        )
    if row.get("source_component_label") in ("with both", "with one", "with the other") and (
        row["quantity"] != "declination"
        or row["role"]
        not in ("recorded_coordinate", "recorded_reading", "repeated_reading", "calibration")
        or "limb_or_instrument_setting_unresolved" not in row.get("flags", [])
    ):
        raise ValueError("Unresolved component label requires a qualified recorded declination")
    if row.get("source_pair_position") not in (None, 1, 2):
        raise ValueError("Unknown public paired-row position")
    out = {key: row[key] for key in ("printed_page", "quantity", "role", "subject", "reference")}
    if tabulated_eclipse_prediction:
        out["source_prediction_kind"] = "eclipse_ephemeris"
    if edition_note:
        out["edition_note_marker"] = note_marker
    if native_digits:
        out["source_extent_unit"] = "digit"
    if page_locator is not None:
        out["source_page_locator"] = page_locator
    out.update(source_fields(source_key(row)))
    out.update(
        id=identifier(row["id"], "assertion"),
        direction=row.get("direction"),
        event_id=identifier(row.get("event_id"), "event"),
        variant_of_id=identifier(row.get("variant_of_id"), "assertion"),
        series_id=identifier(row.get("series_id"), "context"),
        ordinal=ordinal,
        record_status=row.get("record_status"),
        flags=list(row.get("flags", [])),
        normalized=dict(
            status=norm["status"],
            unit=norm["unit"],
            least_component_unit=norm["least_component_unit"],
            **numeric,
        ),
    )
    if "source_scalar_scale" in row:
        out["source_scalar_scale"] = row["source_scalar_scale"]
    out.update(project_size_comparison(row))
    if row["quantity"] == "unclassified_numeric_expression":
        out["numeric_expression_original"] = row["source_expression"]
        if row.get("source_word_numbers"):
            out["source_word_numbers"] = dict(row["source_word_numbers"])
        out["normalized"]["normalization_issue"] = "physical_quantity_or_units_unresolved"
    if row["quantity"] == "separation_ratio":
        endpoints = row.get("separation_ratio_denominator")
        if (
            not isinstance(endpoints, list)
            or len(endpoints) != 2
            or any(not isinstance(e, str) or e not in REFERENCES or e is None for e in endpoints)
            or endpoints[0] == endpoints[1]
            or row["reference"] not in endpoints
            or row["subject"] in endpoints
            or row["role"] != "recorded_reading"
            or norm["status"] != "exact"
            or norm["least_component_unit"] != "ratio"
            or Fraction(norm["magnitude"]) <= 0
            or not {"source_visual_estimate", "source_approximate"} <= set(row.get("flags", []))
        ):
            raise ValueError(
                "Visual separation ratio requires reviewed endpoints and approximate estimate status"
            )
        out["separation_ratio_denominator"] = list(endpoints)
    elif "separation_ratio_denominator" in row:
        raise ValueError("Separation baseline requires a separation ratio")
    instrument_biases = {"instrument_altitude_bias", "instrument_separation_bias"}
    if row["quantity"] in instrument_biases or "source_bias_direction" in row:
        altitude = (
            row["quantity"] == "instrument_altitude_bias"
            and row["subject"] == "Benatky altitude instruments"
            and row.get("source_bias_direction") == "high"
            and row.get("source_correction_application")
            == "corrected_where_found_individual_application_unestablished"
        )
        separation = (
            row["quantity"] == "instrument_separation_bias"
            and row["subject"] == "sextant separations"
            and row.get("source_bias_direction") == "low"
            and row.get("source_correction_application") == "individual_application_unestablished"
        )
        augsburg = (
            row["quantity"] == "instrument_separation_bias"
            and row["subject"] == "Augsburg instrument separations"
            and row.get("source_correction_application") == "individual_application_unestablished"
            and row.get("source_bias_direction") in ("high", "low")
            and row.get("source_correction_operation")
            == {"high": "subtract", "low": "add"}[row["source_bias_direction"]]
        )
        quadrant = (
            row["quantity"] == "instrument_altitude_bias"
            and row["subject"] == "Aldebaran and Mars"
            and row.get("source_instrument_label") == "quadrant"
            and row.get("source_bias_direction") == "high"
            and row.get("source_correction_operation") == "subtract"
            and row.get("source_correction_application") == "historical_reduction_as_stated"
            and row.get("event_id") is not None
            and "historical_reduction_context" in row.get("flags", [])
        )
        if (
            not (altitude or separation or augsburg or quadrant)
            or row["role"] != "historical_correction"
            or row["reference"] is not None
            or row.get("direction") is not None
            or (row.get("event_id") is not None and not quadrant)
            or ("source_correction_operation" in row and not (augsburg or quadrant))
            or norm["status"] != "exact"
            or norm["unit"] != "arcsecond"
            or number(norm["magnitude"]) <= 0
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError(
                "Instrument bias requires its qualified source scope and correction application"
            )
        out.update(
            source_bias_direction=row["source_bias_direction"],
            source_correction_application=row["source_correction_application"],
        )
        if augsburg or quadrant:
            out["source_correction_operation"] = row["source_correction_operation"]
    if row["quantity"] == "declination_correction":
        historical_scope = row["role"] == "historical_correction" and row["subject"] == "Mars"
        calculation_scope = (
            row["role"] == "calculation_intermediate"
            and row["subject"] in BODY_CALCULATIONS | {"ecliptic point"}
            and row.get("event_id") is None
            and "not_an_observing_clock" in row.get("flags", [])
        )
        if (
            row.get("source_correction_operation") not in ("add", "subtract")
            or "source_correction_application" in row
            or not (historical_scope or calculation_scope)
            or row["reference"] is not None
            or row.get("direction") is not None
            or norm["status"] != "exact"
            or norm["unit"] != "arcsecond"
            or number(norm["magnitude"]) <= 0
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError("Unreviewed source declination correction or operation")
        out["source_correction_operation"] = row["source_correction_operation"]
    elif row["quantity"] not in instrument_biases and (
        "source_correction_application" in row or "source_correction_operation" in row
    ):
        application = row.get("source_correction_application")
        targeted_application = (
            (application == "applied_to_following_distances" and row["subject"] == "Jupiter")
            or (application == "not_yet_added_as_stated" and row["subject"] in ("Mars", "Jupiter"))
            or (application == "conditional_not_reported_applied" and row["subject"] == "Mars")
        )
        instructed = (
            application == "instruction_not_reported_applied"
            and row["subject"] == "Radius separations"
        )
        if (
            not (targeted_application or instructed)
            or row.get("source_correction_operation") != "add"
            or row["quantity"] != "separation_correction"
            or row["role"] != "historical_correction"
            or row["reference"] is not None
            or row.get("direction") is not None
            or norm["status"] != "exact"
            or norm["unit"] != "arcsecond"
            or number(norm["magnitude"]) <= 0
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError("Unreviewed source correction application or operation")
        out.update(
            source_correction_application=row["source_correction_application"],
            source_correction_operation=row["source_correction_operation"],
        )
    if "source_unit_notation" in row:
        from .normalization import interpret_part_minute_notation

        _, expected_components = interpret_part_minute_notation(row)
        actual = row.get("components") or {}
        if set(actual) != set(expected_components) or any(
            number(fraction_text(actual[k])) != number(fraction_text(v))
            for k, v in expected_components.items()
        ):
            raise ValueError("Source unit notation differs from recorded components")
        out["source_unit_notation"] = row["source_unit_notation"]
    if "source_tabular_application" in row:
        if (
            row["source_tabular_application"] != "hours_by_arcminutes"
            or row["quantity"] != "calculation_angle"
            or not (
                row["role"] == "historical_input"
                or (
                    row["role"] == "editorial_variant"
                    and row.get("variant_of_id") is not None
                    and "alternative_suggestion_not_applied" in row.get("flags", [])
                )
            )
            or row["subject"] != "planetary motion calculation"
            or row.get("reference") is not None
            or row.get("direction") is not None
            or row.get("zodiac_sign") is not None
            or "not_an_additional_raw_reading" not in row.get("flags", [])
            or not (
                row.get("source_unit_notation") == "tabular_dms_terminal_half"
                or (
                    norm["status"] == "unsupported"
                    and "source_notation_unresolved" in row.get("flags", [])
                    and not row.get("components")
                )
            )
        ):
            raise ValueError("Tabular application requires its qualified source interpretation")
        out["source_tabular_application"] = row["source_tabular_application"]
    if "source_digit_restorations" in row:
        from .numeric_integrity import NUMBER, validate_units

        parsed = source_numeric_text(row, row["source_expression"])
        order = row.get("source_component_order")
        components = row.get("components", {})
        if (
            not isinstance(order, list)
            or not order
            or any(not isinstance(u, str) for u in order)
            or len(set(order)) != len(order)
            or set(order) != set(components)
            or [number(m.group()) for m in re.finditer(NUMBER, parsed)]
            != [number(fraction_text(components[u])) for u in order]
            or norm != normalize_quantity(row)
        ):
            raise ValueError("Restored digits differ from the source components")
        validate_units(parsed, components, order=order, quantity=row["quantity"])
        out["source_digit_restorations"] = list(row["source_digit_restorations"])
        out["source_component_order"] = list(order)
    if "source_number_grouping" in row:
        parsed = source_numeric_text(row, row["source_expression"])
        component = {
            "distance_in_semidiameters": "semidiameter",
            "source_sexagesimal_length": "source_part",
        }.get(row["quantity"], "scalar")
        if row["quantity"] in SOURCE_MILE_UNITS and set(row.get("components", {})) == {"mile"}:
            component = "mile"
        if set(row.get("components", {})) != {component} or number(parsed) != number(
            fraction_text(row["components"][component])
        ):
            raise ValueError("Grouped source scalar differs from its literal")
        out["source_number_grouping"] = row["source_number_grouping"]
    if row["quantity"] == "source_scale_ratio":
        out["normalized"].update(scale_parts)
    if unresolved or noncanonical_degree:
        out["normalized"].update(
            source_components=list(norm["source_components"]),
            normalization_issue=norm["normalization_issue"],
        )
    elif notation_unresolved:
        out["normalized"]["normalization_issue"] = norm["normalization_issue"]
    if "source_angular_count_unit" in row:
        if (
            row["source_angular_count_unit"] != "sign_count"
            or row["quantity"] != "calculation_angle"
            or row.get("argument_name")
            not in (
                "commutation_anomaly",
                "eccentric_anomaly",
                "equated_anomaly",
                "latitude_argument",
                "node_before_apogee_distance",
            )
            or row["subject"] != "Mars"
            or row["reference"] is not None
            or row.get("direction") is not None
            or "sign_count" not in row.get("components", {})
            or norm["status"] != "exact"
            or norm["unit"] != "arcsecond"
            or row["role"] not in ("historical_input", "calculation_intermediate")
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError("Unreviewed source angular count unit")
        out["source_angular_count_unit"] = "sign_count"
    if "source_editorial_component_units" in row:
        if (
            row["source_editorial_component_units"] != ["sign_count"]
            or row["quantity"] != "calculation_angle"
            or row.get("argument_name") != "node_before_apogee_distance"
            or row["role"] != "historical_input"
            or row.get("source_angular_count_unit") != "sign_count"
            or "sign_count" not in row.get("components", {})
        ):
            raise ValueError("Unreviewed partly editorial source argument")
        out["source_editorial_component_units"] = ["sign_count"]
    if (
        "source_zodiac_candidate" in row
        or "source_zodiac_candidates" in row
        or "source_zodiac_identification_uncertain" in row.get("flags", [])
    ):
        multiple = "source_zodiac_candidates" in row
        candidates = (
            row.get("source_zodiac_candidates")
            if multiple
            else [row.get("source_zodiac_candidate")]
        )
        if (
            not isinstance(candidates, list)
            or not (2 <= len(candidates) <= 12 if multiple else len(candidates) == 1)
            or any(not isinstance(sign, str) or sign not in ZODIAC_SIGNS for sign in candidates)
            or len(set(candidates)) != len(candidates)
            or (multiple and "source_zodiac_candidate" in row)
        ):
            raise ValueError("Invalid source zodiac candidate declaration")
        if multiple:
            expression = (
                " ".join(f["source_expression"] for f in row.get("source_fragments", []))
                or row["source_expression"]
            )
            printed_candidates = {
                name
                for name, glyph in ZODIAC_SIGNS.items()
                if glyph in expression or re.search(r"\b" + re.escape(name) + r"\b", expression)
            }
            if set(candidates) != printed_candidates:
                raise ValueError("Zodiac candidates differ from the literal alternatives")
        if (
            row["quantity"] != "ecliptic_longitude"
            or row["role"] != "historical_input"
            or row["subject"]
            not in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
            or row["reference"] is not None
            or row.get("direction") is not None
            or norm["status"] != "exact"
            or norm["unit"] != "arcsecond"
            or "zodiac_sign" in norm
            or row.get("zodiac_sign") is not None
            or not {"not_an_additional_raw_reading", "source_zodiac_identification_uncertain"}
            <= set(row.get("flags", []))
        ):
            raise ValueError("Unreviewed tentative zodiac identification")
        if multiple:
            out["source_zodiac_candidates"] = list(candidates)
        else:
            out["source_zodiac_candidate"] = candidates[0]
    for key in ("source_component_label", "source_pair_position"):
        if key in row:
            out[key] = row[key]
    if "source_repeat_count" in row or "source_repetition_label" in row:
        count = row.get("source_repeat_count")
        label = row.get("source_repetition_label")
        if (
            type(count) is not int
            or not isinstance(label, str)
            or count
            != {
                "semel": 1,
                "once": 1,
                "bis": 2,
                "twice": 2,
                "ter": 3,
                "three times": 3,
                "four times": 4,
                "semel atque iterum": 2,
            }.get(label)
            or row["quantity"] != "angular_separation"
            or row["role"] not in ("recorded_reading", "repeated_reading", "calibration")
            or "source_repetition_note_present" not in row.get("flags", [])
        ):
            raise ValueError("Unreviewed source repetition claim or scope")
        out.update(source_repeat_count=count, source_repetition_label=label)
    if "source_instrument_label" in row:
        label = row["source_instrument_label"]
        quadrant_bias = (
            label == "quadrant"
            and row["quantity"] == "instrument_altitude_bias"
            and row.get("source_correction_application") == "historical_reduction_as_stated"
        )
        altitude = (
            label
            in (
                "sextant",
                "quadrant",
                "greatest quadrant",
                "solid quadrant",
                "revolving quadrant",
                "revolving instrument",
                "lesser quadrant",
                "steel instrument",
                "steel quadrant",
                "iron quadrant",
                "mural quadrant",
            )
            and row["quantity"] == "altitude"
            and row["role"] in ("recorded_reading", "repeated_reading", "calibration")
        )
        declination = (
            label == "armillae"
            and row["quantity"] == "declination"
            and row["role"] in ("recorded_coordinate", "repeated_reading", "calibration")
        )
        radius_summary = (
            label == "Radius"
            and row["quantity"] == "ecliptic_latitude"
            and row["role"] == "historical_input"
            and row["subject"] == "Mars"
            and row["reference"] is None
            and {"not_an_additional_raw_reading", "source_quality_note_present"}
            <= set(row.get("flags", []))
        )
        radius_separation = (
            label == "Radius"
            and row["quantity"] == "angular_separation"
            and row["role"] in ("recorded_reading", "calibration")
        )
        sextant_separation = (
            label in ("sextant", "astronomical arc")
            and row["quantity"] == "angular_separation"
            and row["reference"] is not None
            and row["role"] in ("recorded_reading", "repeated_reading", "calibration")
        )
        lunar_diameter = (
            label in ("Radius", "sextant", "sextant and Radius")
            and row["quantity"] == "angular_diameter"
            and row["subject"] == "Moon"
            and row["reference"] is None
            and row["role"] == "recorded_reading"
        )
        armillae_distance = (
            label in ("armillae", "equatorial armillae")
            and row["quantity"] == "meridian_distance"
            and row["role"] in ("recorded_reading", "calibration")
            and row["subject"] in ("tail of Leo", "Spica")
            and row["reference"] == "meridian"
            and row.get("direction") == "east"
        )
        if (
            not (
                altitude
                or declination
                or radius_summary
                or radius_separation
                or sextant_separation
                or lunar_diameter
                or armillae_distance
                or quadrant_bias
            )
            or norm["unit"] != "arcsecond"
        ):
            raise ValueError("Unreviewed source instrument or quantity scope")
        out["source_instrument_label"] = label
    if "source_instrument_qualifier" in row:
        largest = (
            row["source_instrument_qualifier"] == "largest"
            and row.get("source_instrument_label") == "armillae"
            and row["quantity"] == "declination"
            and row["role"] in ("recorded_coordinate", "repeated_reading")
        )
        radius_only = (
            row["source_instrument_qualifier"] == "only"
            and row.get("source_instrument_label") == "Radius"
            and row["quantity"] == "ecliptic_latitude"
            and row["role"] == "historical_input"
        )
        if not (largest or radius_only) or norm["unit"] != "arcsecond":
            raise ValueError("Unreviewed source instrument qualifier or scope")
        out["source_instrument_qualifier"] = row["source_instrument_qualifier"]
    if "source_correction_scope" in row:
        scope = row["source_correction_scope"]
        if (
            scope != "current_observing_sequence"
            or row["quantity"] != "clock_correction"
            or row["role"] != "historical_correction"
            or row["subject"] != "observing clock"
            or norm["unit"] != "second_of_time"
            or not {"clock_runs_fast", "clock_correction_not_applied"} <= set(row.get("flags", []))
        ):
            raise ValueError("Unreviewed source clock rule scope")
        out["source_correction_scope"] = scope
    if "source_parallax_context" in row or "source_parallax_operation" in row:
        ra = (
            row.get("source_parallax_context") == "right_ascension_collection"
            and row.get("source_parallax_operation") == "add"
            and row["quantity"] == "parallax_angle"
        )
        ecliptic = (
            row.get("source_parallax_context") == "ecliptic_coordinate_reduction"
            and row.get("source_parallax_operation") in ("add", "subtract")
            and row["quantity"] in ("longitude_correction", "latitude_correction")
            and row.get("direction") is None
        )
        if (
            not (ra or ecliptic)
            or row["role"] != "historical_correction"
            or row["subject"] != "Mars"
            or row["reference"] != "Earth"
            or norm["unit"] != "arcsecond"
            or "historical_parallax_not_detection" not in row.get("flags", [])
        ):
            raise ValueError("Unreviewed source parallax instruction or context")
        out.update(
            source_parallax_context=row["source_parallax_context"],
            source_parallax_operation=row["source_parallax_operation"],
        )
    if row["quantity"] == "orbital_longitude" or "source_coordinate_frame" in row:
        frame_subject = (
            row["subject"] == "Mars" and row.get("source_coordinate_state") == "true"
        ) or (
            row["subject"] == "Moon centre" and row.get("source_coordinate_state") in (None, "true")
        )
        legacy_reduction = (
            row["role"] == "reduction"
            and frame_subject
            and row["reference"] is None
            and norm.get("zodiac_sign") in ZODIAC_SIGNS
        )
        calculated_coordinate = (
            row["role"] in ("historical_input", "calculation_intermediate")
            and row["subject"] in {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}
            and row["reference"] in (None, "Earth", "Sun")
            and row.get("event_id") is None
            and "not_an_observing_clock" in row.get("flags", [])
            and (norm.get("zodiac_sign") in ZODIAC_SIGNS or "sign_count" in parts)
        )
        if (
            row["quantity"] != "orbital_longitude"
            or row.get("source_coordinate_frame") != "own_orbit_as_stated"
            or not (legacy_reduction or calculated_coordinate)
            or row.get("direction") is not None
            or row.get("model_name") is not None
            or norm["unit"] != "arcsecond"
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError("Unreviewed source orbital coordinate frame")
        out["source_coordinate_frame"] = row["source_coordinate_frame"]
    if "source_coordinate_state" in row:
        state = row["source_coordinate_state"]
        adopted_declination_input = (
            row["quantity"] == "declination"
            and state in ("true", "apparent")
            and row["role"] == "historical_input"
            and row["subject"] == "Mars"
            and row["reference"] is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        corrected_declination_input = (
            row["quantity"] == "declination"
            and state == "corrected_as_stated"
            and row["role"] == "historical_input"
            and row["subject"] == "Mars"
            and row["reference"] is None
            and norm["status"] == "exact"
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        corrected_longitude_input = (
            row["quantity"] == "ecliptic_longitude"
            and state == "corrected_as_stated"
            and row["role"] == "historical_input"
            and row["subject"] == "Mars"
            and row["reference"] is None
            and row.get("direction") is None
            and norm["status"] == "exact"
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        if state == "corrected_as_stated" and not (
            corrected_declination_input or corrected_longitude_input
        ):
            raise ValueError("Corrected-as-stated label requires a separate adopted Mars input")
        stellar_calibration_reference = (
            row["quantity"] == "declination"
            and state == "true"
            and (row["role"], row["subject"])
            in (("expected_calibration", "heart of Scorpio"), ("adopted_value", "Spica"))
            and row["reference"] is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        true_stellar_separation = (
            row["quantity"] == "angular_separation"
            and state == "true"
            and row["role"] == "reduction"
            and row["subject"] == "Spica"
            and row["reference"] == "heart of Scorpio"
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        true_meridian_declination = (
            row["quantity"] == "declination"
            and state == "true"
            and row["role"] == "reduction"
            and row["subject"] == "Mars"
            and row["reference"] is None
            and row.get("source_reduction_method") == "meridian_altitude"
            and row.get("source_reduction_references") == []
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        parallax_free_lunar = (
            state == "free_of_parallax"
            and row["quantity"] == "angular_separation"
            and row["subject"] == "Moon"
            and row["reference"] == "Aldebaran"
            and row["role"] == "reduction"
            and row.get("direction") is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        if state == "free_of_parallax" and not parallax_free_lunar:
            raise ValueError("Parallax-free distance must retain its reduced lunar source scope")
        if (
            state
            not in (
                "refracted",
                "apparent",
                "true",
                "free_of_refraction",
                "corrected_as_stated",
                "parallax_included_as_stated",
                "parallax_adjustment_pending_as_stated",
                "parallax_possibly_insufficient_as_stated",
                "free_of_parallax",
            )
            or (
                row["quantity"]
                not in ("ecliptic_longitude", "ecliptic_latitude", "orbital_longitude")
                and not (
                    adopted_declination_input
                    or corrected_declination_input
                    or stellar_calibration_reference
                    or true_stellar_separation
                    or true_meridian_declination
                    or parallax_free_lunar
                )
            )
            or (
                row["role"] not in ("reduction", "historical_input", "adopted_value")
                and not stellar_calibration_reference
            )
            or norm["unit"] != "arcsecond"
        ):
            raise ValueError("Unreviewed source coordinate state")
        included_role = row["role"] == "reduction" or (
            row["role"] == "historical_input"
            and row.get("source_parameter_kind") == "greatest_northern_latitude"
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        if state == "parallax_included_as_stated" and (
            row["quantity"] not in ("ecliptic_longitude", "ecliptic_latitude")
            or not included_role
            or row["subject"] != "Mars"
            or row["reference"] is not None
            or "historical_parallax_not_detection" not in row.get("flags", [])
        ):
            raise ValueError(
                "Included-parallax label requires the reviewed historical coordinate reduction"
            )
        if state == "parallax_adjustment_pending_as_stated" and (
            row["quantity"] != "ecliptic_latitude"
            or row["role"] != "historical_input"
            or row["subject"] != "Mars"
            or row["reference"] is not None
            or not {"not_an_additional_raw_reading", "historical_parallax_not_detection"}
            <= set(row.get("flags", []))
        ):
            raise ValueError(
                "Pending parallax label requires an unadjusted source input and no invented correction"
            )
        if state == "parallax_possibly_insufficient_as_stated" and (
            row["quantity"] != "ecliptic_latitude"
            or row["role"] != "historical_input"
            or row["subject"] != "Mars"
            or row["reference"] is not None
            or not {
                "not_an_additional_raw_reading",
                "source_quality_note_present",
                "historical_parallax_not_detection",
            }
            <= set(row.get("flags", []))
        ):
            raise ValueError("Possible parallax shortfall requires a qualified source input")
        out["source_coordinate_state"] = state
    if "source_parameter_kind" in row:
        longitude_parameter = (
            row["source_parameter_kind"]
            in ("longitude_of_greatest_latitude", "northern_node_longitude")
            and row["quantity"] == "ecliptic_longitude"
            and row.get("direction") is None
        )
        latitude_parameter = row["quantity"] == "ecliptic_latitude" and (
            (
                row["source_parameter_kind"] == "greatest_northern_latitude"
                and row.get("direction") == "north"
            )
            or (
                row["source_parameter_kind"] == "greatest_southern_latitude"
                and row.get("direction") == "south"
            )
        )
        scalar_parameter = row["quantity"] == "source_scalar" and norm["unit"] == "source_scalar"
        scale_parameter = (
            row["quantity"] == "source_scale_ratio"
            and row.get("source_parameter_kind") == "eccentricity_as_stated"
        )
        parameter_role = row["role"] == "historical_input" or (
            latitude_parameter and row["role"] == "reduction"
        )
        if not (scalar_parameter or scale_parameter) and (
            not (longitude_parameter or latitude_parameter)
            or not parameter_role
            or row["subject"] != "Mars"
            or row["reference"] is not None
            or norm["unit"] != "arcsecond"
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError("Unreviewed source orbital parameter or role")
        out["source_parameter_kind"] = row["source_parameter_kind"]
    if "source_reduction_method" in row or "source_reduction_references" in row:
        method = row.get("source_reduction_method")
        refs = row.get("source_reduction_references")
        meridian_declination = (
            method == "meridian_altitude"
            and row["quantity"] == "declination"
            and row["role"] == "reduction"
            and row["subject"] in ("Mars", "Regulus")
            and row["reference"] is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        if (
            method
            not in (
                "comparison_directions",
                "meridian_altitude",
                "angular_distances",
                "small_globe",
                "largest_globe",
                "great_brass_globe",
                "weighted_latitude_combination",
                "parallax_subtraction",
                "adoption",
            )
            or (
                row["quantity"]
                not in ("ecliptic_longitude", "ecliptic_latitude", "right_ascension")
                and not meridian_declination
            )
            or row["role"] not in ("reduction", "adopted_value")
            or not isinstance(refs, list)
            or any(not isinstance(ref, str) or ref not in REFERENCES for ref in refs)
            or len(set(refs)) != len(refs)
        ):
            raise ValueError("Unreviewed coordinate reduction method or references")
        if (method in ("comparison_directions", "angular_distances")) != bool(refs):
            raise ValueError("Coordinate reduction references do not match the method")
        if method in ("small_globe", "largest_globe", "great_brass_globe") and (
            row["subject"]
            not in (("Mars", "head of Medusa") if method == "great_brass_globe" else ("Mars",))
            or row["quantity"] not in ("ecliptic_longitude", "ecliptic_latitude")
            or row["role"] != "reduction"
            or row["reference"] is not None
            or refs
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError(
                "Globe reduction labels require their reviewed historical coordinate subjects"
            )
        out.update(source_reduction_method=method, source_reduction_references=list(refs))
    if "source_adoption_preference" in row:
        preference = row["source_adoption_preference"]
        if (
            preference is None
            or preference not in REFERENCES
            or row["quantity"] != "right_ascension"
            or row["role"] != "adopted_value"
            or row.get("source_reduction_method") != "adoption"
            or norm["unit"] != "arcsecond"
        ):
            raise ValueError("Unreviewed source adoption preference or scope")
        out["source_adoption_preference"] = preference
    if "source_adoption_preferences" in row:
        preferences = row["source_adoption_preferences"]
        if (
            not isinstance(preferences, list)
            or len(preferences) < 2
            or any(not isinstance(ref, str) or ref not in REFERENCES for ref in preferences)
            or len(set(preferences)) != len(preferences)
            or "source_adoption_preference" in row
            or row["quantity"] != "right_ascension"
            or row["role"] != "adopted_value"
            or row.get("source_reduction_method") != "adoption"
            or norm["unit"] != "arcsecond"
        ):
            raise ValueError("Unreviewed source adoption preferences or scope")
        out["source_adoption_preferences"] = list(preferences)
    if row["quantity"] == "correction_ratio":
        kind = row.get("correction_ratio_kind")
        if (
            kind
            not in (
                "separation_to_declination_refraction",
                "jupiter_to_mean_solar_parallax",
                "latitude_difference_weight",
                "copernican_prosthaphaeresis_fraction",
            )
            or (
                row["reference"] is None
                and kind
                not in ("latitude_difference_weight", "copernican_prosthaphaeresis_fraction")
            )
            or row["role"] not in ("historical_input", "historical_correction")
        ):
            raise ValueError("Unreviewed correction ratio relationship")
        if kind == "latitude_difference_weight" and (
            row["reference"] is not None or row["role"] != "historical_correction"
        ):
            raise ValueError("Latitude weight is a correction ratio without a reference body")
        if kind == "jupiter_to_mean_solar_parallax" and (
            row["subject"] != "Jupiter" or row["reference"] != "Sun"
        ):
            raise ValueError("Unreviewed source parallax ratio endpoints")
        if kind == "copernican_prosthaphaeresis_fraction" and (
            row["subject"] != "Mars"
            or row["reference"] is not None
            or row["role"] != "historical_correction"
            or row.get("model_name") != "Copernicus"
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError("Unreviewed Copernican fractional instruction")
        out["correction_ratio_kind"] = kind
    elif "correction_ratio_kind" in row:
        raise ValueError("Ratio relationship requires a correction ratio")
    if row["quantity"] == "source_fraction":
        out.update(
            source_fraction_kind=row["source_fraction_kind"],
            comparison_relation=row["comparison_relation"],
        )
    if "source_semidiameter_body" in row:
        if (
            row["source_semidiameter_body"] not in ("Earth", "Jupiter")
            or row["quantity"] != "distance_in_semidiameters"
            or norm["unit"] != "source_semidiameter"
        ):
            raise ValueError("Unreviewed source semidiameter body")
        out["source_semidiameter_body"] = row["source_semidiameter_body"]
    if "source_distance_model" in row:
        if (
            row["source_distance_model"] != "Copernicus"
            or row["quantity"] != "distance_in_semidiameters"
            or row["role"] not in ("historical_input", "reduction")
            or row["subject"] != "Mars"
            or row["reference"] != "Earth"
            or row.get("direction") is not None
            or row.get("source_semidiameter_body") != "Earth"
            or norm["status"] != "exact"
            or norm["unit"] != "source_semidiameter"
            or Fraction(norm["magnitude"]) <= 0
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError(
                "Source distance model requires an adopted or source-derived Earth-radius distance"
            )
        out["source_distance_model"] = row["source_distance_model"]
    if "parallax_component" in row:
        if (
            row["parallax_component"] not in ("altitude", "longitude", "latitude")
            or row["quantity"] != "parallax_angle"
            or row["role"] not in ("reduction", "historical_input")
            or row["subject"] not in ("Mars", "Moon", "New Star of 1572")
            or row["reference"] != "Earth"
            or row.get("direction") is not None
            or norm["status"] != "exact"
            or norm["unit"] != "arcsecond"
            or norm["signed_magnitude"] is not None
            or "not_an_additional_raw_reading" not in row.get("flags", [])
            or (
                row["role"] == "historical_input"
                and "historical_parallax_not_detection" not in row.get("flags", [])
            )
        ):
            raise ValueError(
                "Parallax component requires an Earth-referenced historical reduction or qualified input"
            )
        out["parallax_component"] = row["parallax_component"]
    if "calculation_epoch_id" in row:
        out["calculation_epoch_id"] = identifier(row["calculation_epoch_id"], "assertion")
    if "zodiac_sign_inherited_from_id" in row:
        origin = row["zodiac_sign_inherited_from_id"]
        if row["quantity"] != "ecliptic_longitude" or origin is None or origin == row["id"]:
            raise ValueError("Invalid public zodiac origin link")
        out["zodiac_sign_inherited_from_id"] = identifier(origin, "assertion")
    if "zodiac_inheritance_kind" in row:
        if (
            row["zodiac_inheritance_kind"] != "same_ephemeris_statement"
            or row.get("zodiac_sign_inherited_from_id") is None
            or row["role"] != "historical_prediction"
            or row.get("model_name") not in ("Stadius", "Carelli")
        ):
            raise ValueError("Unreviewed zodiac inheritance kind")
        out["zodiac_inheritance_kind"] = row["zodiac_inheritance_kind"]
    if "source_longitude_origin" in row:
        origin = row["source_longitude_origin"]
        if (
            row["quantity"] != "ecliptic_longitude"
            or origin
            not in ("first_star_of_Aries", "first_point_of_Aries_as_stated", "source_equinox")
            or "zodiac_sign" in norm
        ):
            raise ValueError("Unreviewed or conflicting source longitude origin")
        out["source_longitude_origin"] = origin
    if "argument_name" in row:
        complement = (
            row["argument_name"] == "latitude_complement"
            and row["quantity"] == "calculation_angle"
            and row["role"] == "calculation_intermediate"
            and row["subject"] == "Mars"
            and row["reference"] is None
            and row.get("direction") is None
        )
        node = (
            row["quantity"] == "calculation_angle"
            and row["subject"] == "Mars"
            and row["reference"] is None
            and row.get("direction") is None
            and (
                (
                    row["argument_name"] == "node_distance"
                    and row["role"] in ("historical_input", "reduction")
                )
                or (
                    row["argument_name"] == "node_distance_correction"
                    and row["role"] == "historical_correction"
                )
            )
        )
        opposition = (
            row["quantity"] == "calculation_angle"
            and row["subject"] == "Mars"
            and row["reference"] is None
            and row.get("direction") is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
            and (
                (
                    row["argument_name"] == "simple_planetary_longitude"
                    and row["role"] in ("historical_input", "reduction")
                )
                or (
                    row["argument_name"] in ("apogee_longitude", "prosthaphaeresis", "anomaly")
                    and row["role"] == "historical_input"
                )
                or (
                    row["argument_name"] == "commutation_correction"
                    and row["role"] == "historical_correction"
                )
            )
        )
        latitude_argument = (
            row["quantity"] == "calculation_angle"
            and row["subject"] == "Mars"
            and row["reference"] is None
            and row.get("direction") is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
            and (
                (
                    row["argument_name"] == "latitude_argument"
                    and row["role"] in ("historical_input", "calculation_intermediate")
                )
                or (
                    row["argument_name"] == "latitude_argument_correction"
                    and row["role"] == "historical_correction"
                )
                or (
                    row["argument_name"] == "apogee_shift"
                    and row["role"] == "historical_correction"
                )
                or (
                    row["argument_name"] == "node_before_apogee_distance"
                    and row["role"] == "historical_input"
                )
                or (
                    row["argument_name"] == "apogee_to_latitude_maximum"
                    and (
                        row["role"] in ("historical_input", "historical_correction")
                        or (
                            row["role"] == "editorial_addition"
                            and row.get("annotation_of_id") is not None
                        )
                    )
                )
            )
        )
        lunar_source_argument = (
            row["argument_name"] in ("parallax_longitude_side_as_stated", "node_distance")
            and row["quantity"] == "calculation_angle"
            and row["role"] == "historical_input"
            and row["subject"] == "Moon centre"
            and row["reference"] is None
            and row.get("direction") is None
            and norm["unit"] == "arcsecond"
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        if not (
            complement or node or opposition or latitude_argument or lunar_source_argument
        ) and (
            row["quantity"]
            not in ("calculation_angle", "ecliptic_longitude", "longitude_correction")
            or row["argument_name"]
            not in (
                "mean_longitude",
                "equated_longitude",
                "mean_apogee_motion",
                "eccentric_anomaly",
                "commutation_anomaly",
                "eccentric_equation",
                "equated_anomaly",
                "precession_offset",
                "simple_solar_longitude",
            )
        ):
            raise ValueError("Unreviewed historical argument")
        out["argument_name"] = row["argument_name"]
    if "source_adjustment_sign" in row:
        if (
            row["source_adjustment_sign"] not in ("plus", "minus")
            or row["quantity"] != "calculation_angle"
            or row.get("argument_name") != "apogee_shift"
            or row["role"] != "historical_correction"
            or row["subject"] != "Mars"
            or row["reference"] is not None
            or row.get("direction") is not None
            or norm["unit"] != "arcsecond"
        ):
            raise ValueError("Unreviewed model parameter adjustment sign")
        out["source_adjustment_sign"] = row["source_adjustment_sign"]
    editorial = "editorial_component_units" in row
    if editorial:
        if (
            row["role"] != "editorial_addition"
            or row.get("model_name") != "Alphonsine"
            or row["quantity"] != "ecliptic_latitude"
            or row["editorial_component_units"] != ["arcminute"]
            or "source_editorial_computation" not in row.get("flags", [])
        ):
            raise ValueError("Unreviewed editorial component attribution")
        out["editorial_component_units"] = ["arcminute"]
    eclipse_prediction = (
        row["quantity"] == "calculation_epoch"
        and row["role"] == "historical_prediction"
        and row["subject"] in ("Moon", "Sun")
        and row["reference"] is None
        and row.get("direction") is None
        and row.get("model_name")
        in ("Alphonsine", "Stadius", "Prutenic", "Magini", "Origanus", "Tycho Brahe")
        and row.get("source_eclipse_phase") in ("beginning", "middle", "end")
        and norm["status"] == "exact"
        and norm["unit"] == "second_of_time"
        and {
            "not_an_additional_raw_reading",
            "not_an_observing_clock",
            "absolute_time_unestablished",
        }
        <= set(row.get("flags", []))
    )
    unnamed_eclipse_prediction = (
        row["quantity"] == "calculation_epoch"
        and row["role"] == "historical_prediction"
        and row["subject"] == "Moon"
        and row["reference"] is None
        and row.get("direction") is None
        and row.get("model_name") is None
        and row.get("source_model_attribution") == "unnamed_as_stated"
        and row.get("source_model_label") in ("tables for Vienna", "tables", "Calculation")
        and row.get("source_eclipse_phase") in ("beginning", "middle", "end")
        and row.get("time_reference") in ("source_after_noon", "source_after_midnight_label")
        and norm["status"] == "exact"
        and norm["unit"] == "second_of_time"
        and {
            "not_an_additional_raw_reading",
            "not_an_observing_clock",
            "absolute_time_unestablished",
        }
        <= set(row.get("flags", []))
    )
    if "source_eclipse_phase" in row:
        if not (eclipse_prediction or unnamed_eclipse_prediction or tabulated_eclipse_prediction):
            raise ValueError("Unreviewed model eclipse phase or timing role")
        out["source_eclipse_phase"] = row["source_eclipse_phase"]
    if row["quantity"] == "inferred_time" or "time_inference_basis" in row:
        if (
            row["quantity"] != "inferred_time"
            or row["role"] != "reduction"
            or row.get("time_inference_basis")
            not in (
                "equatorial_distance",
                "eclipse_midpoint",
                "comparison_star_altitude",
                "observed_altitude",
            )
            or norm["unit"] != "second_of_time"
        ):
            raise ValueError("Unreviewed inferred time or basis")
        out["time_inference_basis"] = row["time_inference_basis"]
    if "source_time_scale" in row:
        if (
            row["source_time_scale"] not in ("apparent", "equal")
            or row["quantity"] not in ("recorded_clock", "calculation_epoch", "inferred_time")
            or norm["unit"] != "second_of_time"
        ):
            raise ValueError(
                "Source time scale requires an explicit historical time representation"
            )
        out["source_time_scale"] = row["source_time_scale"]
    if equal_value:
        out["source_value_equal_to_id"] = identifier(row["source_value_equal_to_id"], "assertion")
        if repeated_equal:
            out["source_equality_kind"] = "repeated_measurement"
    if "time_reference" in row:
        allowed = {
            "sunset_from_noon": {"calculation_epoch"},
            "padua_from_noon": {"calculation_epoch"},
            "author_clock_from_noon": {"calculation_epoch"},
            "author_clock_origin_unstated": {"calculation_epoch"},
            "source_clock_origin_unstated": {"calculation_epoch", "inferred_time"},
            "source_after_noon": {"calculation_epoch", "inferred_time"},
            "source_after_sunset": {"calculation_epoch"},
            "elapsed_since_sunset": {"clock_elapsed_time"},
            "elapsed_before_sunrise": {"clock_elapsed_time"},
            "elapsed_before_twilight": {"clock_elapsed_time"},
            "elapsed_after_meridian_transit": {"clock_elapsed_time"},
            "elapsed_before_meridian_transit": {"clock_elapsed_time"},
            "elapsed_after_lunar_quadrature": {"clock_elapsed_time"},
            "elapsed_after_prior_observations": {"clock_elapsed_time"},
            "elapsed_after_stellar_meridian_transit": {"clock_elapsed_time"},
            "elapsed_after_acronychal_position": {"clock_elapsed_time"},
            "source_midnight_label": {"calculation_epoch"},
            "source_after_midnight_label": {"calculation_epoch", "inferred_time"},
            "between_site_meridians": {"meridian_time_difference"},
        }
        reference = row["time_reference"]
        if (
            reference not in allowed
            or row["quantity"] not in allowed[reference]
            or norm["unit"] != "second_of_time"
        ):
            raise ValueError("Unreviewed or mismatched time reference")
        if reference == "elapsed_before_sunrise" and (
            row["role"] != "recorded_reading" or row.get("direction") is not None
        ):
            raise ValueError("Before-sunrise interval requires a recorded duration")
        if reference == "elapsed_before_twilight" and (
            row["role"] != "recorded_reading" or row.get("direction") is not None
        ):
            raise ValueError("Before-twilight interval requires a recorded duration")
        if reference in ("elapsed_after_meridian_transit", "elapsed_before_meridian_transit") and (
            row["role"] != "recorded_reading"
            or row["subject"] != "Mars"
            or row.get("direction") is not None
        ):
            raise ValueError("Meridian-relative interval requires a recorded Mars duration")
        if reference == "elapsed_after_lunar_quadrature" and (
            row["role"] != "recorded_reading"
            or row["subject"] != "Moon"
            or row.get("direction") is not None
            or "source_approximate" not in row.get("flags", [])
        ):
            raise ValueError("Lunar phase interval requires its approximate Moon scope")
        if reference in (
            "elapsed_after_prior_observations",
            "elapsed_after_stellar_meridian_transit",
            "elapsed_after_acronychal_position",
        ):
            endpoint = (
                "head of Hydra" if reference == "elapsed_after_stellar_meridian_transit" else None
            )
            role = (
                "historical_input"
                if reference == "elapsed_after_acronychal_position"
                else "recorded_reading"
            )
            if (
                row["role"] != role
                or row["subject"] != "Mars"
                or row["reference"] != endpoint
                or (
                    reference == "elapsed_after_acronychal_position"
                    and "not_an_additional_raw_reading" not in row.get("flags", [])
                )
                or row.get("direction") is not None
                or "source_approximate" not in row.get("flags", [])
            ):
                raise ValueError(
                    "Relative interval requires its recorded Mars scope, endpoint and approximation"
                )
        if reference == "source_midnight_label" and (
            row["role"] != "calculation_epoch" or norm["magnitude"] != "43200"
        ):
            raise ValueError(
                "Reviewed midnight label requires the source twelve-hour calculation epoch"
            )
        if (
            reference == "source_after_midnight_label"
            and row["role"] != "calculation_epoch"
            and not eclipse_prediction
            and not unnamed_eclipse_prediction
            and not tabulated_eclipse_prediction
            and not (
                row["quantity"] == "inferred_time"
                and row["role"] == "reduction"
                and row.get("time_inference_basis") in ("equatorial_distance", "eclipse_midpoint")
            )
        ):
            raise ValueError("After-midnight reference requires a source calculation epoch")
        out["time_reference"] = reference
    if row.get("time_reference") == "elapsed_after_prior_observations":
        anchor = row.get("source_time_anchor_event_id")
        if anchor is None or anchor == row.get("event_id"):
            raise ValueError("Prior-observation interval requires a different source group")
        out["source_time_anchor_event_id"] = identifier(anchor, "event")
    elif "source_time_anchor_event_id" in row:
        raise ValueError("Source time anchor requires a prior-observation interval")
    model = row.get("model_name")
    witness_comparison = "comparison_sources" in row or "comparison_label_original" in row
    if witness_comparison:
        sources = row.get("comparison_sources")
        components = row.get("components", {})
        unsigned_comparison = row.get("comparison_relation") == "unsigned_difference_as_stated"
        if (
            not isinstance(sources, list)
            or len(sources) != 2
            or any(not isinstance(s, str) or not s.strip() or len(s) > 160 for s in sources)
            or sources[0] == sources[1]
            or model is not None
            or row.get("event_id") is not None
            or row.get("direction") is not None
            or row["reference"] is None
            or row["reference"] == row["subject"]
            or not components
            or (len(components) != 1 and not unsigned_comparison)
            or not set(components) <= {"degree", "arcminute", "arcsecond"}
            or "comparison_quantity" in row
            or norm["status"] != "exact"
            or norm["unit"] != "arcsecond"
            or norm["signed_magnitude"] is not None
            or norm != normalize_quantity(row)
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError("Source comparison requires two attributed, distinct readings")
        literal = comparison_numeric_text(row, row["source_expression"])
        if not unsigned_comparison and number(literal) != number(
            fraction_text(next(iter(components.values())))
        ):
            raise ValueError("Comparison component differs from its literal magnitude")
    angular_size_comparison = "comparison_quantity" in row
    if angular_size_comparison and (
        row["role"] != "historical_comparison"
        or row["quantity"] != "calculation_angle"
        or row["subject"] not in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
        or row["reference"] is not None
        or row.get("direction") is not None
        or model not in ("Copernicus", "Alphonsine", "Prutenic", "Stadius")
        or row["comparison_quantity"] not in ("parallax_angle", "angular_diameter")
        or row.get("comparison_relation")
        not in ("model_smaller_than_source", "model_larger_than_source")
        or norm["status"] != "exact"
        or norm["unit"] != "arcsecond"
        or norm["signed_magnitude"] is not None
        or norm != normalize_quantity(row)
        or "not_an_additional_raw_reading" not in row.get("flags", [])
        or (
            row["comparison_quantity"] == "parallax_angle"
            and "historical_parallax_not_detection" not in row.get("flags", [])
        )
    ):
        raise ValueError("Angular size comparison requires a verified source-attributed difference")
    motion_shortfall = (
        row["quantity"] == "angular_motion_difference"
        and row["role"] == "historical_comparison"
        and model in ("Copernicus", "Alphonsine", "Prutenic", "Stadius")
        and row["subject"] == "Mars"
        and row["reference"] is None
        and row.get("direction") is None
        and row.get("event_id") is None
        and row.get("comparison_relation") == "angular_motion_shortfall_over_source_interval"
        and norm["status"] == "exact"
        and norm["unit"] == "arcsecond"
        and norm["signed_magnitude"] is None
        and "not_an_additional_raw_reading" in row.get("flags", [])
    )
    if (
        row["quantity"] == "angular_motion_difference"
        or row.get("comparison_relation") == "angular_motion_shortfall_over_source_interval"
    ) and not motion_shortfall:
        raise ValueError(
            "Motion shortfall requires a source-attributed angular interval comparison"
        )
    interval_prediction = (
        row["role"] == "historical_prediction"
        and model in ("Copernicus", "Alphonsine")
        and row["subject"] == "Mars"
        and row["quantity"] == "longitude_difference"
        and row["reference"] is None
        and row.get("direction") is None
        and row.get("event_id") is None
        and norm["status"] == "exact"
        and norm["unit"] == "arcsecond"
        and "not_an_additional_raw_reading" in row.get("flags", [])
        and row.get("prediction_relation")
        in ("retrograde_change_over_source_interval", "direct_change_over_source_interval")
    )
    if "prediction_relation" in row:
        if not interval_prediction:
            raise ValueError("Unreviewed interval prediction relation")
        out["prediction_relation"] = row["prediction_relation"]
    ephemeris_bodies = {"Moon", "Mars", "Venus", "Mercury", "Jupiter", "Saturn"}
    ephemeris_prediction = (
        row["role"] == "historical_prediction"
        and model in ("Stadius", "Carelli", "Leovitius", "Prutenic", "Alphonsine")
        and row["subject"] in ephemeris_bodies
        and norm["status"] == "exact"
        and norm["unit"] == "arcsecond"
        and "not_an_additional_raw_reading" in row.get("flags", [])
        and (
            (
                row["quantity"] == "ecliptic_longitude"
                and row.get("direction") is None
                and row["reference"] is None
                and norm.get("zodiac_sign") in ZODIAC_SIGNS
            )
            or (
                row["quantity"] == "ecliptic_latitude"
                and row.get("direction") in (None, "north", "south")
                and row["reference"] is None
                and 0 <= number(norm["magnitude"]) <= 90 * 3600
            )
            or (
                row["quantity"]
                in ("angular_separation", "longitude_difference", "latitude_difference")
                and row.get("direction") is None
                and row["reference"] in ephemeris_bodies
                and row["reference"] != row["subject"]
            )
        )
    )
    unnamed_model = "source_model_attribution" in row or "source_model_label" in row
    if unnamed_model and not unnamed_eclipse_prediction and not tabulated_eclipse_prediction:
        author_calculation = (
            (
                row.get("source_model_label") == "our calculation"
                or (
                    row.get("source_model_label") == "our own rectification"
                    and row["subject"] == "Sun"
                )
            )
            and row["subject"] in ephemeris_bodies | {"Sun"}
            and row["role"] == "historical_prediction"
            and (
                (
                    row["quantity"] == "ecliptic_longitude"
                    and row.get("argument_name") == "equated_longitude"
                    and (
                        norm.get("zodiac_sign") in ZODIAC_SIGNS
                        or "zodiac_sign_unstated" in row.get("flags", [])
                    )
                )
                or (
                    row["quantity"] == "ecliptic_latitude"
                    and "argument_name" not in row
                    and "hemisphere_unspecified" in row.get("flags", [])
                    and norm.get("magnitude") is not None
                    and 0 <= number(norm["magnitude"]) <= 90 * 3600
                )
            )
        )
        reviewed_label = (
            row.get("source_model_label") == "our restitution" and row["subject"] == "Mars"
        ) or author_calculation
        prediction = (
            row["role"] == "historical_prediction"
            and row["quantity"] in ("calculation_angle", "ecliptic_longitude")
            and row.get("argument_name") == "equated_longitude"
            and (row["quantity"] == "calculation_angle" or norm.get("zodiac_sign") in ZODIAC_SIGNS)
        ) or author_calculation
        comparison = (
            row["role"] == "historical_comparison"
            and row["quantity"] == "longitude_difference"
            and row.get("comparison_relation") == "coordinate_difference"
        )
        if (
            model is not None
            or row.get("source_model_attribution") != "unnamed_as_stated"
            or not reviewed_label
            or not (prediction or comparison)
            or row["reference"] is not None
            or row.get("direction") is not None
            or norm["status"] != "exact"
            or norm["unit"] != "arcsecond"
            or norm["signed_magnitude"] is not None
            or "not_an_additional_raw_reading" not in row.get("flags", [])
        ):
            raise ValueError(
                "Unnamed source model requires its reviewed label and explicit attribution uncertainty"
            )
        out.update(
            source_model_attribution="unnamed_as_stated",
            source_model_label=row["source_model_label"],
        )
    elif unnamed_eclipse_prediction or (tabulated_eclipse_prediction and unnamed_model):
        out.update(
            source_model_attribution=row["source_model_attribution"],
            source_model_label=row["source_model_label"],
        )
    source_difference = "source_difference_relation" in row or "source_difference_reference" in row
    if source_difference:
        jupiter = (
            row.get("source_difference_relation") in ("excess", "deficit")
            and row.get("source_difference_reference") == "limited_position_as_stated"
            and row["quantity"] in ("longitude_difference", "latitude_difference")
            and row["subject"] == "Jupiter"
        )
        stellar = (
            row.get("source_difference_relation") == "deficit"
            and row.get("source_difference_reference") == "stellar_reference_declination_unstated"
            and row["quantity"] == "declination_difference"
            and row["subject"] == "Aldebaran"
            and norm["status"] == "exact"
            and number(norm["magnitude"]) > 0
        )
        if (
            not (jupiter or stellar)
            or row["role"] != "historical_comparison"
            or row["reference"] is not None
            or row.get("direction") is not None
            or model is not None
            or norm["status"] != "exact"
            or norm["unit"] != "arcsecond"
            or "not_an_additional_raw_reading" not in row.get("flags", [])
            or editorial
            or any(
                k in row
                for k in ("comparison_relation", "source_comparison_sign", "lower_bound_inclusive")
            )
        ):
            raise ValueError("Unreviewed source coordinate comparison relation or reference")
        out.update(
            source_difference_relation=row["source_difference_relation"],
            source_difference_reference=row["source_difference_reference"],
        )
    elif coordinate_product is not None:
        out["source_coordinate_product"] = coordinate_product
    elif motion_shortfall:
        out.update(model_name=model, comparison_relation=row["comparison_relation"])
    elif angular_size_comparison:
        out.update(
            model_name=model,
            comparison_quantity=row["comparison_quantity"],
            comparison_relation=row["comparison_relation"],
        )
    elif witness_comparison:
        out.update(
            comparison_sources=list(row["comparison_sources"]),
            comparison_relation=row["comparison_relation"],
            source_comparison_sign=row["source_comparison_sign"],
        )
        if "comparison_label_original" in row:
            out["comparison_label_original"] = row["comparison_label_original"]
    elif row["role"] in ("historical_prediction", "historical_comparison") or editorial:
        polar_prediction = (
            row["role"] == "historical_prediction"
            and row["quantity"] == "polar_distance"
            and row["subject"] == "Polaris"
            and model in ("Tycho Brahe", "Alphonsine")
            and row["reference"] is None
            and row.get("direction") is None
            and "not_an_additional_raw_reading" in row.get("flags", [])
        )
        named_models = (
            ("Copernicus", "Alphonsine", "Prutenic", "Stadius")
            if row["role"] == "historical_comparison"
            else ("Copernicus", "Alphonsine", "Prutenic", "Tycho Brahe", "Stadius")
        ) + ("Magini", "Origanus", "Scala")
        if (
            (
                not unnamed_model
                and not ephemeris_prediction
                and not eclipse_prediction
                and not tabulated_eclipse_prediction
                and not predicted_eclipse_digits
                and not eclipse_extent
                and not interval_prediction
                and not polar_prediction
                and (
                    model not in named_models
                    or row["subject"]
                    not in (
                        ("Sun", "Moon", "Mars", "Venus", "Mercury", "Jupiter", "Saturn")
                        + (("lunar ascending node",) if model in ("Stadius", "Tycho Brahe") else ())
                        if row["role"] == "historical_prediction"
                        or model in ("Magini", "Origanus", "Scala")
                        else ("Mars", "Moon")
                    )
                    or row["quantity"]
                    not in (
                        ("clock_elapsed_time", "longitude_difference", "latitude_difference")
                        if row["role"] == "historical_comparison"
                        else ("ecliptic_longitude", "ecliptic_latitude", "angular_daily_motion")
                    )
                )
            )
            or row.get("event_id") is not None
            or (
                row["role"] == "historical_prediction"
                and model == "Stadius"
                and "not_an_additional_raw_reading" not in row.get("flags", [])
            )
        ):
            raise ValueError("Historical prediction requires reviewed model attribution")
        out["model_name"] = model
        if row["role"] == "historical_comparison":
            if row["quantity"] == "clock_elapsed_time":
                if (
                    norm["unit"] != "second_of_time"
                    or row.get("comparison_relation")
                    not in ("earlier_than_author", "differs_from_author")
                    or type(row.get("lower_bound_inclusive")) is not bool
                    or "source_lower_bound" not in row.get("flags", [])
                ):
                    raise ValueError("Historical timing comparison requires a relation and bound")
                out.update(
                    comparison_relation=row["comparison_relation"],
                    lower_bound_inclusive=row["lower_bound_inclusive"],
                )
            else:
                relation = row.get("comparison_relation")
                if (
                    norm["unit"] != "arcsecond"
                    or relation
                    not in ("coordinate_difference", "latitude_change_over_source_interval")
                    or (
                        relation == "latitude_change_over_source_interval"
                        and row["quantity"] != "latitude_difference"
                    )
                    or "lower_bound_inclusive" in row
                ):
                    raise ValueError("Historical angular comparison requires a reviewed relation")
                out["comparison_relation"] = relation
    elif model is not None:
        argument = row["quantity"] == "calculation_angle" and (
            (row.get("argument_name") == "prosthaphaeresis" and row["role"] == "historical_input")
            or (
                row.get("argument_name") == "commutation_correction"
                and row["role"] == "historical_correction"
            )
        )
        fraction = (
            row["quantity"] == "correction_ratio"
            and row.get("correction_ratio_kind") == "copernican_prosthaphaeresis_fraction"
        )
        if (
            model != "Copernicus"
            or row["subject"] != "Mars"
            or row["reference"] is not None
            or row.get("direction") is not None
            or "not_an_additional_raw_reading" not in row.get("flags", [])
            or not (argument or fraction)
        ):
            raise ValueError(
                "Model attribution requires a reviewed prediction or source calculation argument"
            )
        out["model_name"] = model
    if "source_comparison_sign" in row and not witness_comparison:
        sign = row["source_comparison_sign"]
        model = (
            sign in ("plus", "minus")
            and row["role"] == "historical_comparison"
            and row["quantity"] in ("longitude_difference", "latitude_difference")
            and row.get("comparison_relation") == "coordinate_difference"
        )
        recap_role = row["role"] == "calculation_intermediate" or (
            row["role"] == "editorial_variant"
            and row.get("annotation_of_id") is not None
            and row.get("comparison_relation") == "computed_minus_observed"
        )
        recap = (
            sign in ("plus", "minus", "equal")
            and recap_role
            and row["quantity"] == "latitude_difference"
            and row["subject"] == "Mars"
            and row["reference"] is None
            and row.get("direction") is None
            and row.get("model_name") is None
            and row.get("comparison_relation")
            in ("observed_minus_computed", "computed_minus_observed")
            and (sign != "equal" or norm["magnitude"] == "0")
        )
        if not (model or recap) or norm["unit"] != "arcsecond":
            raise ValueError("Unreviewed source model-comparison sign")
        out["source_comparison_sign"] = sign
        if recap:
            out["comparison_relation"] = row["comparison_relation"]
    if "observing_site" in row or "observer_names" in row:
        names = row.get("observer_names")
        site = row.get("observing_site")
        if names == ["David Fabricius"] and site is None:
            if row["quantity"] not in (
                "angular_separation",
                "altitude",
                "clock_elapsed_time",
            ) or row["role"] not in ("recorded_reading", "repeated_reading", "calibration"):
                raise ValueError(
                    "Fabricius raw attribution requires a direct reading without an inferred site"
                )
            out["observer_names"] = list(names)
        elif names == ["Thaddaeus Hagecius"] and site is None:
            angle = row["quantity"] in ("angular_separation", "altitude") and row["role"] in (
                "recorded_reading",
                "repeated_reading",
                "calibration",
            )
            clock = (
                row["quantity"] == "recorded_clock"
                and row["role"] == "recorded_clock"
                and row["subject"] == "observing clock"
                and row["reference"] is None
            )
            if not (angle or clock):
                raise ValueError(
                    "Hagecius attribution requires a raw angle or observing clock without an inferred site"
                )
            out["observer_names"] = list(names)
        elif site in ("Uraniborg", "Girsitzæ", "Benatky", "Copenhagen"):
            raw = (
                site in ("Uraniborg", "Girsitzæ", "Benatky")
                and row["quantity"]
                in (
                    "declination",
                    "angular_separation",
                    "altitude",
                    "meridian_distance",
                    "recorded_clock",
                )
                and row["role"]
                in (
                    "recorded_coordinate",
                    "recorded_reading",
                    "repeated_reading",
                    "calibration",
                    "recorded_clock",
                )
            )
            account = (
                site == "Copenhagen"
                and row["role"] == "reduction"
                and (
                    row["quantity"] == "inferred_time"
                    or (
                        row["quantity"] in ("ecliptic_longitude", "ecliptic_latitude")
                        and row.get("source_reduction_method") in ("small_globe", "largest_globe")
                    )
                )
            )
            if "observer_names" in row or not (raw or account):
                raise ValueError(
                    "Source observing site requires a reviewed role without inferred observer names"
                )
            out["observing_site"] = site
        else:
            if (
                site != "Padua"
                or not isinstance(names, list)
                or not all(isinstance(name, str) for name in names)
                or not (
                    names == ["Magini"]
                    or (len(names) == 2 and set(names) == {"Magini", "Gellius Sascerides"})
                )
            ):
                raise ValueError("Unreviewed observing site or observer attribution")
            out.update(observing_site="Padua", observer_names=list(names))
    if "geometry_label" in row or "geometry_column" in row:
        if (
            row["quantity"] != "calculation_angle"
            or row.get("geometry_label")
            not in (
                None,
                "CA",
                "AC",
                "BA",
                "AB",
                "BC",
                "BAC",
                "ACB",
                "DA",
                "AD",
                "DC",
                "CD",
                "DAC",
                "CAD",
                "DAB",
                "ABD",
                "DB",
                "BD",
                "CB",
                "DBC",
                "DBA",
                "CBA",
                "CAB",
            )
            or type(row.get("geometry_column")) is not int
            or row["geometry_column"] not in (1, 2)
        ):
            raise ValueError("Invalid public calculation geometry label")
        out.update(geometry_label=row.get("geometry_label"), geometry_column=row["geometry_column"])
    control = row.get("workbook_control_id")
    if control is not None:
        if not re.fullmatch(r"Sheet1:\d+", control):
            raise ValueError("Invalid public workbook identity")
        out["workbook_control_id"] = control
    if row.get("annotation_of_id") is not None:
        out["annotation_of_id"] = identifier(row["annotation_of_id"], "assertion")
    alternative = row.get("editorial_reference_alternative")
    if missing_reference:
        out["source_reference_status"] = row["source_reference_status"]
    proposal_status = row.get("editorial_reference_status")
    if "editorial_reference_status" in row and (
        proposal_status not in ("tentative", "restored_from_witness")
        or not missing_reference
        or alternative is None
    ):
        raise ValueError("Invalid editorial reference status")
    if alternative is not None:
        if (
            alternative not in REFERENCES
            or alternative is None
            or alternative == row["reference"]
            or row["quantity"] != "angular_separation"
            or not (
                (missing_reference and proposal_status in ("tentative", "restored_from_witness"))
                or (
                    not missing_reference
                    and "source_endpoint_editorially_disputed" in row.get("flags", [])
                )
            )
        ):
            raise ValueError("Invalid printed editorial endpoint alternative")
        out["editorial_reference_alternative"] = alternative
        if proposal_status is not None:
            out["editorial_reference_status"] = proposal_status
    if "editorial_subject_alternative" in row or "editorial_subject_status" in row:
        subject_alternative = row.get("editorial_subject_alternative")
        subject_status = row.get("editorial_subject_status")
        if (
            not isinstance(subject_alternative, str)
            or subject_alternative not in SUBJECTS
            or subject_alternative == row["subject"]
            or subject_status != "correction_as_stated"
            or row["quantity"] not in ANGLE_QUANTITIES
            or row["role"]
            not in ("calibration", "recorded_reading", "recorded_coordinate", "repeated_reading")
            or "source_endpoint_editorially_disputed" not in row.get("flags", [])
        ):
            raise ValueError("Invalid editorial recorded-subject correction")
        out.update(
            editorial_subject_alternative=subject_alternative,
            editorial_subject_status=subject_status,
        )
    if "source_columns" in row:
        columns = row["source_columns"]
        if (
            row.get("column") is not None
            or not isinstance(columns, list)
            or len(columns) < 2
            or any(type(c) is not int or c < 1 for c in columns)
            or columns != list(range(columns[0], columns[-1] + 1))
        ):
            raise ValueError("Invalid public multi-column binding")
        out["source_columns"] = list(columns)
    if "source_date_claim_ids" in row:
        ids = row["source_date_claim_ids"]
        if not isinstance(ids, list) or any(
            not isinstance(cid, str) or identifier(cid, "context") != cid for cid in ids
        ):
            raise ValueError("Invalid public source-date links")
        out["source_date_claim_ids"] = sorted(set(ids))
    if "zodiac_sign_basis_context_id" in row:
        basis_context = row["zodiac_sign_basis_context_id"]
        if (
            not isinstance(basis_context, str)
            or row["quantity"] not in ("ecliptic_longitude", "orbital_longitude")
            or row.get("zodiac_sign") not in ZODIAC_SIGNS
            or norm.get("zodiac_sign", row["zodiac_sign"]) != row["zodiac_sign"]
            or basis_context not in row.get("context_ids", [])
        ):
            raise ValueError("Named-sign origin requires its bound source context")
        out["zodiac_sign_basis_context_id"] = identifier(basis_context, "context")
    if "source_zodiac_sector" in row:
        out["source_zodiac_sector"] = dict(row["source_zodiac_sector"])
        out["normalized"] = dict(norm)
    elif any(
        key in norm for key in ("zodiac_sign", "longitude_origin", "zodiac_longitude_degrees")
    ):
        sign = norm.get("zodiac_sign")
        longitude = norm.get("zodiac_longitude_degrees")
        if (
            row["quantity"] not in ("ecliptic_longitude", "orbital_longitude")
            or sign not in ZODIAC_SIGNS
            or norm.get("longitude_origin") != "start_of_named_sign"
        ):
            raise ValueError("Invalid public zodiac origin")
        if noncanonical_degree:
            out["normalized"].update(
                zodiac_sign=sign,
                longitude_origin=norm["longitude_origin"],
            )
        elif not isinstance(longitude, str) or not re.fullmatch(r"\d+(?:/[1-9]\d*)?", longitude):
            raise ValueError("Invalid public zodiac longitude")
        else:
            degree = Fraction(norm["magnitude_degrees"])
            if (
                not 0 <= degree <= 30
                or degree != Fraction(norm["magnitude"]) / 3600
                or Fraction(longitude) != degree + 30 * tuple(ZODIAC_SIGNS).index(sign)
            ):
                raise ValueError("Inconsistent public zodiac conversion")
            out["normalized"].update(
                zodiac_sign=sign,
                longitude_origin=norm["longitude_origin"],
                zodiac_longitude_degrees=longitude,
            )
    if "ordinal_degree" in (row.get("components") or {}) or "ordinal_degree_evidence" in row:
        if norm != normalize_quantity(row):
            raise ValueError("Ordinal longitude differs from supported source interpretation")
        out["normalized"].update(
            source_ordinal_degree=norm["source_ordinal_degree"],
            ordinal_degree_interpretation=norm["ordinal_degree_interpretation"],
        )
        out["ordinal_degree_evidence"] = dict(row["ordinal_degree_evidence"])
    if "source_fragment_pages" in row:
        pages = row["source_fragment_pages"]
        if (
            not isinstance(pages, list)
            or not pages
            or (
                any(type(p) is not int or p < 1 for p in pages)
                and not (
                    pages == [None] and row["printed_page"] is None and page_locator is not None
                )
            )
            or len(set(pages)) != len(pages)
            or pages[0] != row["printed_page"]
        ):
            raise ValueError("Source fragment pages require ordered bibliographic page numbers")
        out["source_fragment_pages"] = pages
    if "source_component_carry" in row:
        from .table_components import carry_unit_matches

        carry = row["source_component_carry"]
        if (
            not isinstance(carry, dict)
            or set(carry)
            != {
                "unit",
                "source_line",
                "source_column",
                "source_expression",
                "source_printed_page",
                "rule_context_id",
            }
            or not carry_unit_matches(row["quantity"], carry.get("unit"))
            or type(carry.get("source_line")) is not int
            or not 1 <= carry["source_line"] < row["line"]
            or type(carry.get("source_column")) is not int
            or carry["source_column"] < 1
            or type(carry.get("source_printed_page")) is not int
            or carry["source_printed_page"] < 1
            or carry.get("rule_context_id") not in row.get("context_ids", [])
            or not isinstance(carry.get("source_expression"), str)
            or not re.fullmatch(
                r"\d+(?:/\d+)?(?:\s+\d+/\d+)?", fraction_text(carry["source_expression"])
            )
            or carry["unit"] not in row.get("components", {})
            or number(fraction_text(carry["source_expression"]))
            != number(fraction_text(row["components"][carry["unit"]]))
            or norm != normalize_quantity(row)
        ):
            raise ValueError("Invalid public carried-component evidence")
        out["source_component_carry"] = dict(carry)
        out["source_component_carry"]["rule_context_id"] = identifier(
            carry["rule_context_id"], "context"
        )
        from .catalog_release import scope_id

        out["source_component_carry"]["rule_scope_id"] = scope_id(row["review_id"])
    return out
