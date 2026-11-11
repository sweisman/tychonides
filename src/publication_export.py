"""Explicit public field whitelist; working provenance and excerpts never pass through."""

import re
from fractions import Fraction
from urllib.parse import urlsplit


NUMBERS = (
    "pafko_time_key",
    "pafko_quote_magnitude_arcsec",
    "pafko_converted_arcsec",
    "source_time_key",
    "source_magnitude_arcsec",
    "source_signed_arcsec",
    "preferred_magnitude_arcsec",
    "preferred_recorded_time_key",
)
ENUMS = {
    "target": {"Mars", "Aldebaran"},
    "role": {"observation", "derived", "calibration"},
    "mars_selection": {
        "review_required",
        "excluded_other_target",
        "excluded_derived_or_calibration",
        "candidate_mars_requires_scientific_review",
    },
    "comparison_status": {
        "exact",
        "magnitude_agreement",
        "disagreement",
        "unmatched",
        "ambiguous",
        "unresolved",
    },
    "conversion_status": {
        "consistent",
        "magnitude_conflict",
        "sign_conflict",
        "component_decimal_conflict",
        "magnitude_consistent_sign_unresolved",
        "unresolved",
    },
    "preferred_basis": {"source_scan_review", "source_text_unverified"},
    "date_basis": {"source_scan_review", "source_text_unverified"},
    "time_basis": {"source_scan_review", "source_text_unverified"},
    "page_basis": {"source_scan_review", "source_text_unverified"},
    "source_check": {
        "not_reviewed",
        "source_supports_translation",
        "source_supports_quote_and_translation",
        "magnitude_agreement_scan_verified",
        "partial_source_check",
        "source_supports_translation_and_target_correction",
        "source_structure_verified",
    },
    "date_status": {"consistent", "conflict", "unresolved"},
    "time_status": {"consistent", "conflict", "unresolved"},
    "page_status": {"consistent", "conflict", "unresolved"},
    "hemisphere_status": {"consistent", "conflict", "unresolved"},
    "numeric_source_sign_status": {"consistent", "conflict", "unresolved"},
    "source_hemisphere_basis": {"explicit_label_or_value", "same_date_context"},
}
FLAGS = {
    "hemisphere_unresolved",
    "derived_or_editorial",
    "column_role_unresolved",
    "value_unresolved",
    "source_uncertainty",
}


def public_records(catalogue, registry):
    sources = {r["volume"]: r for r in registry}
    records = []
    seen = set()
    for row in catalogue:
        match = re.fullmatch(r"Sheet1:(\d+)", row["pafko_id"])
        if not match:
            raise ValueError("Unrecognized public record identity")
        identifier = "pafko-" + match[1]
        if identifier in seen:
            raise ValueError("Duplicate public record identity")
        seen.add(identifier)
        volume = row["volume"]
        if volume not in (10, 11, 12, 13):
            raise ValueError("Unknown source volume")
        result = dict(record_id=identifier, volume=volume, release_status="provisional_validation")
        for key in ("pafko_page", "source_page", "preferred_source_page"):
            value = row.get(key)
            if value is not None and (type(value) is not int or value < 1):
                raise ValueError("Invalid printed page")
            result[key] = value
        for key in ("pafko_date", "source_date", "preferred_recorded_date"):
            value = row.get(key)
            if value is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError("Invalid recorded date")
            result[key] = value
        for key in NUMBERS:
            value = row.get(key)
            result[key] = str(Fraction(value)) if value is not None else None
        for key, choices in ENUMS.items():
            value = row.get(key)
            if value is not None and value not in choices:
                raise ValueError(f"Unreviewed public field: {key}")
            result[key] = value
        flags = row.get("flags", [])
        if not isinstance(flags, list) or any(f not in FLAGS for f in flags):
            raise ValueError("Unknown public flag")
        result["flags"] = list(flags)
        for key in ("original_scan", "translation_page", "translation_pdf"):
            value = sources.get(volume, {}).get(key)
            if value is not None:
                parsed = urlsplit(value)
                if (
                    parsed.scheme != "https"
                    or not parsed.hostname
                    or parsed.username
                    or parsed.password
                ):
                    raise ValueError("Public citation must be an HTTPS URL")
            result[key] = value
        records.append(result)
    return records
