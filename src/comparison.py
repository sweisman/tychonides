"""Align by metadata and printed order; compare values only after alignment."""

from fractions import Fraction

from .core import hemisphere


def quote_sign(text):
    import re

    # Instrument names such as southern armillae do not describe Mars's hemisphere.
    tail = re.split(r"\bDecl(?:inatio|in|ination)?\.?", text, flags=re.I)[-1]
    tail = re.split(r"\bper\b|\bin Arm", tail, flags=re.I)[0]
    # "ex alt. m." means from meridian altitude; its m. is not a hemisphere.
    tail = re.sub(r"\bex\s+alt(?:it)?\.?\s*(?:m|merid)\.", "", tail, flags=re.I)
    return hemisphere(tail)


def audit_conversion(p):
    quoted = p.get("quote_magnitude_arcsec")
    components = p.get("arcsec")
    if quoted is None or components is None:
        return "unresolved"
    if Fraction(quoted) != abs(Fraction(components)):
        return "magnitude_conflict"
    sign = quote_sign(p.get("quote", ""))
    if sign and Fraction(components) and (Fraction(components) > 0) != (sign > 0):
        return "sign_conflict"
    if p.get("component_conversion_consistent") is False:
        return "component_decimal_conflict"
    return "consistent" if sign else "magnitude_consistent_sign_unresolved"


def compatible(p, r):
    return not (
        p.get("time_key")
        and r.get("time_key")
        and p["time_key"] not in (r["time_key"], r.get("time_match_key"))
    )


def compare_pair(p, r):
    # Backward-compatible inputs for callers without quotation fields.
    historical = "quote" in p
    pval = p.get("quote_magnitude_arcsec") if historical else p.get("arcsec")
    rval = r.get("magnitude_arcsec") if historical else r.get("arcsec")
    blockers = set(r.get("flags", [])) - {"hemisphere_unresolved", "derived_or_editorial"}
    if pval is None or rval is None or blockers:
        return dict(status="unresolved", delta_arcsec=None, hemisphere_status="unresolved")
    delta = Fraction(rval) - Fraction(pval)
    if delta:
        return dict(status="disagreement", delta_arcsec=str(delta), hemisphere_status="unresolved")
    if not historical:
        return dict(status="exact", delta_arcsec="0", hemisphere_status="consistent")
    p_sign = quote_sign(p.get("quote", ""))
    r_signed = r.get("arcsec")
    r_sign = (
        (1 if Fraction(r_signed) > 0 else -1)
        if r_signed is not None and Fraction(r_signed)
        else None
    )
    if p_sign and r_sign:
        if p_sign != r_sign:
            return dict(status="disagreement", delta_arcsec="0", hemisphere_status="conflict")
        return dict(status="exact", delta_arcsec="0", hemisphere_status="consistent")
    return dict(status="magnitude_agreement", delta_arcsec="0", hemisphere_status="unresolved")


def compare_records(pafko, extracted, review_links=None):
    from .alignment import compare_records as align

    return align(pafko, extracted, review_links)
