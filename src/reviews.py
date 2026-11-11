"""Bind source reviews to immutable inputs and derive a separate working catalogue."""

from copy import deepcopy
from fractions import Fraction


def prepare_reviews(pafko, observations, decisions, source_hashes, workbook_sha256):
    rows = deepcopy(observations)
    by_id = {r["id"]: r for r in rows}
    ps = {p["id"]: p for p in pafko}
    latest = {d["pafko_id"]: d for d in decisions}
    links, accepted = {}, {}
    for pid, d in latest.items():
        identity = d.get("identity")
        if not identity or pid not in ps:
            continue
        r = by_id.get(identity.get("source_record_id"))
        if r is None:
            raise ValueError(f"Reviewed source identity is absent: {pid}")
        if (
            not d.get("evidence")
            or not identity.get("source_sha256")
            or not identity.get("workbook_sha256")
        ):
            raise ValueError(f"Review lacks evidence or input fingerprints: {pid}")
        if (
            identity["source_sha256"] != source_hashes.get(r["source"])
            or identity["workbook_sha256"] != workbook_sha256
        ):
            raise ValueError(f"Review input fingerprint changed: {pid}")
        if r.get("volume") != ps[pid].get("volume"):
            raise ValueError(f"Review crosses source volumes: {pid}")
        if r["id"] in links.values():
            raise ValueError("Reviewed identities must be one to one")
        if (
            d.get("source_scan_magnitude_arcsec") is not None
            and Fraction(d["source_scan_magnitude_arcsec"]) < 0
        ):
            raise ValueError(f"Reviewed magnitude must be unsigned: {pid}")
        cleared = set(d.get("resolved_flags", [])) & {"column_role_unresolved"}
        r["flags"] = [f for f in r.get("flags", []) if f not in cleared]
        r["reviewed_flags"] = sorted(set(r.get("reviewed_flags", [])) | cleared)
        # Annotate reviewed interpretation; retain original source role separately.
        if d.get("verified_role"):
            r["extracted_role"] = r.get("role")
            r["role"] = d["verified_role"]
        if d.get("verified_target"):
            r["reviewed_target"] = d["verified_target"]
        links[pid] = r["id"]
        accepted[pid] = d
    return rows, links, accepted


def derived_catalogue(pafko, observations, outcomes, accepted_reviews):
    results = {r["pafko_id"]: r for r in outcomes}
    if len(results) != len(outcomes) or set(results) != {p["id"] for p in pafko}:
        raise ValueError("Catalogue requires exactly one outcome per requested workbook row")
    sources = {r["id"]: r for r in observations}
    catalogue = []
    for p in pafko:
        result = results[p["id"]]
        ids = result.get("candidate_ids", [])
        source = sources[ids[0]] if result.get("alignment_basis") and len(ids) == 1 else None
        review = accepted_reviews.get(p["id"], {})
        scan_value = review.get("source_scan_magnitude_arcsec")
        source_value = source.get("magnitude_arcsec") if source else None
        source_date = source.get("date") if source else None
        source_clock = source.get("time_key") if source else None
        preferred_date = review.get("verified_date", source_date)
        preferred_clock = review.get("verified_time_key", source_clock)
        blockers = (
            set(source.get("flags", [])) - {"hemisphere_unresolved", "derived_or_editorial"}
            if source
            else set()
        )
        preferred = scan_value if scan_value is not None else source_value if not blockers else None
        basis = (
            "source_scan_review"
            if scan_value is not None
            else "source_text_unverified"
            if preferred is not None
            else None
        )
        target = review.get("verified_target")
        role = review.get("verified_role") or (source.get("role") if source else None)
        selection = (
            "excluded_other_target"
            if target and target != "Mars"
            else "excluded_derived_or_calibration"
            if role in ("derived", "calibration")
            else "candidate_mars_requires_scientific_review"
            if target == "Mars"
            else "review_required"
        )
        catalogue.append(
            dict(
                pafko_id=p["id"],
                volume=p.get("volume"),
                pafko_page=p.get("page"),
                pafko_date=p.get("date"),
                pafko_time_key=p.get("time_key"),
                pafko_quote_magnitude_arcsec=p.get("quote_magnitude_arcsec"),
                pafko_converted_arcsec=p.get("arcsec"),
                pafko_decimal_degrees=p.get("converted_degrees"),
                source_record_id=source["id"] if source else None,
                source_page=source.get("page") if source else None,
                preferred_source_page=review.get(
                    "verified_page", source.get("page") if source else None
                ),
                page_basis="source_scan_review"
                if "verified_page" in review
                else "source_text_unverified"
                if source and source.get("page")
                else None,
                source_date=source.get("date") if source else None,
                source_time_key=source.get("time_key") if source else None,
                preferred_recorded_date=preferred_date,
                preferred_recorded_time_key=preferred_clock,
                date_basis="source_scan_review"
                if "verified_date" in review
                else "source_text_unverified"
                if source_date
                else None,
                time_basis="source_scan_review"
                if "verified_time_key" in review
                else "source_text_unverified"
                if source_clock
                else None,
                source_magnitude_arcsec=source_value,
                source_signed_arcsec=source.get("arcsec") if source else None,
                preferred_magnitude_arcsec=preferred,
                preferred_basis=basis,
                target=target,
                role=role,
                mars_selection=selection,
                comparison_status=result["status"],
                conversion_status=result.get("conversion_status"),
                source_check=review.get("status", result.get("source_check", "not_reviewed")),
                date_status=result.get("date_status", "unresolved"),
                time_status=result.get("time_status", "unresolved"),
                page_status=result.get("page_status", "unresolved"),
                flags=source.get("flags", []) if source else [],
                hemisphere_status=result.get("hemisphere_status", "unresolved"),
            )
        )
        catalogue[-1].update(
            numeric_source_sign_status=result.get("numeric_source_sign_status", "unresolved"),
            source_hemisphere_basis=result.get("source_hemisphere_basis"),
        )
    return catalogue
