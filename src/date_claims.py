"""Public projections of reviewed source-date components, never observing epochs."""

import re

from .catalog import source_fields, source_key


MONTHS = {
    alias: index
    for index, aliases in enumerate(
        (
            ("JANUARIJ", "JANUARII", "JANUARY", "JAN"),
            ("FEBRUARIJ", "FEBRUARII", "FEBRUARY", "FEB"),
            ("MARTIJ", "MARTII", "MARCH"),
            ("APRILIS", "APRIL", "APR"),
            ("MAIJ", "MAII", "MAY"),
            ("JUNIJ", "JUNII", "IUNIJ", "IUNII", "JUNE"),
            ("JULIJ", "JULII", "IULIJ", "IULII", "JULY"),
            ("AUGUSTI", "AVGUSTI", "AUGUST", "AUG"),
            ("SEPTEMBRIS", "SEPTEMBER", "SEPT"),
            ("OCTOBRIS", "OCTOBER", "OCT"),
            ("NOUEMBRIS", "NOVEMBRIS", "NOVEMBER", "NOV"),
            ("DECEMBRIS", "DECEMBER", "DEC"),
        ),
        1,
    )
    for alias in aliases
}
DAYPARTS = {
    "AM": "before_noon",
    "A. M.": "before_noon",
    "A.M.": "before_noon",
    "ANTE MERIDIEM": "before_noon",
    "BEFORE NOON": "before_noon",
    "FORENOON": "before_noon",
    "BEFORE MIDDAY": "before_noon",
    "P. M.": "after_noon",
    "PM": "after_noon",
    "P.M.": "after_noon",
    "POST MERIDIEM": "after_noon",
    "AFTERNOON": "after_noon",
    "AFTER NOON": "after_noon",
    "AFTER MIDDAY": "after_noon",
    "POMERID.": "after_noon",
    "MANE": "morning",
    "MORNING": "morning",
    "IN THE MORNING": "morning",
    "AD VESPERAS": "evening",
    "AD VESPEREM": "evening",
    "VESPERI": "evening",
    "EVENING": "evening",
    "MERIDIE": "noon",
    "NOON": "noon",
    "NOCTE": "night",
    "NIGHT": "night",
    "POST MEDIAM NOCTEM": "after_midnight",
    "AFTER MIDNIGHT": "after_midnight",
    "IN M. N. SEQ.": "following_midnight",
    "ANTE MEDIAM NOCTEM": "before_midnight",
    "BEFORE MIDNIGHT": "before_midnight",
}


def component(value, minimum, maximum):
    if value is not None and (type(value) is not int or not minimum <= value <= maximum):
        raise ValueError("Invalid reviewed date component")
    return value


def public_date_claim(context):
    if context["kind"] != "recorded_date":
        raise ValueError("Not a reviewed date context")
    cid = context["id"]
    volume = source_key(context)
    prefix = "s" + volume if isinstance(volume, str) else "v" + str(volume)
    if (
        (not isinstance(volume, str) and volume not in (10, 11, 12, 13))
        or not isinstance(cid, str)
        or not re.fullmatch(rf"context-{re.escape(prefix)}-[0-9a-f]{{20}}", cid)
    ):
        raise ValueError("Invalid reviewed date identity")
    value = context["value"]
    if not isinstance(value, dict):
        raise ValueError("Date projection requires structured review components")
    year = component(value.get("year"), 1, 9999)
    month = component(value.get("month"), 1, 12)
    day = component(value.get("day"), 1, 31)
    label = value.get("month_original")
    if label is not None:
        if not isinstance(label, str) or label.strip().upper().rstrip(".") not in MONTHS:
            raise ValueError("Unreviewed month label")
        mapped = MONTHS[label.strip().upper().rstrip(".")]
        if month is not None and month != mapped:
            raise ValueError("Conflicting reviewed month components")
        month = mapped
    label = value.get("daypart_original")
    if label is not None and (not isinstance(label, str) or label.strip().upper() not in DAYPARTS):
        raise ValueError("Unreviewed daypart label")
    daypart = DAYPARTS[label.strip().upper()] if label is not None else None
    calendar = context.get("calendar")
    origin = context.get("day_origin")
    if calendar not in (None, "Julian", "Gregorian"):
        raise ValueError("Unreviewed calendar claim")
    if origin not in (None, "midnight", "noon", "sunset", "sunrise"):
        raise ValueError("Unreviewed day-origin claim")
    out = dict(
        id=cid,
        **source_fields(volume),
        year=year,
        month=month,
        day=day,
        daypart=daypart,
        calendar=calendar,
        day_origin=origin,
        component_status="complete_named_components"
        if all(v is not None for v in (year, month, day))
        else "partial_named_components",
        claim_basis="reviewed_source_context",
        calendar_validation="not_performed",
        accepted_observing_date=None,
        absolute_timestamp=None,
    )
    if "source_date_role" in context:
        role = context["source_date_role"]
        if role not in (
            "observation_label",
            "planned_observation_label",
            "observation_label_variant",
            "calculation_target",
            "calculation_target_variant",
            "model_prediction",
            "editorial_date_comment",
        ):
            raise ValueError("Unreviewed source-date role")
        out["source_date_role"] = role
    if "source_day_relation" in context:
        relation = context["source_day_relation"]
        if (
            relation not in ("following_night", "preceding_night")
            or daypart != "night"
            or day is None
            or context.get("source_date_role") != "observation_label"
        ):
            raise ValueError(
                "Relative night requires its named day, night label and observation role"
            )
        out["source_day_relation"] = relation
    if (
        context.get("source_date_role")
        in ("observation_label_variant", "calculation_target_variant", "editorial_date_comment")
        or "source_date_witness" in context
    ):
        witness = context.get("source_date_witness")
        roles = {
            "printed_heading": {"observation_label"},
            "manuscript_reported_by_editor": {
                "observation_label_variant",
                "calculation_target_variant",
            },
            "editorial_comment": {"editorial_date_comment"},
        }
        if (
            not isinstance(witness, str)
            or witness not in roles
            or context.get("source_date_role") not in roles[witness]
        ):
            raise ValueError("Unreviewed or conflicting date witness attribution")
        out["source_date_witness"] = witness
    if context.get("source_date_role") == "model_prediction":
        model = context.get("model_name")
        relation = context.get("model_date_relation")
        subject = context.get("subject")
        eclipse_date = (
            model == "Tycho Brahe"
            and subject == "Moon"
            and relation == "middle_lunar_eclipse_on_named_day"
        )
        if not eclipse_date and (
            model not in ("Copernicus", "Prutenic", "Alphonsine", "Stadius")
            or not (
                (subject == "Sun" and relation == "solar_ingress_on_named_day")
                or (
                    subject in ("Mars", "Venus", "Mercury", "Jupiter")
                    and relation
                    in (
                        "retrograde_motion_begins",
                        "direct_motion_until_date",
                        "station_near_date",
                        "station_on_named_day",
                        "station_before_named_day",
                        "opposition_on_named_day",
                    )
                )
            )
        ):
            raise ValueError("Unreviewed model date attribution or relation")
        out.update(model_name=model, model_date_relation=relation, subject=subject)
    elif "model_name" in context or "model_date_relation" in context:
        raise ValueError("Model date metadata requires a model-prediction date claim")
    if "day_number_basis" in value:
        if value["day_number_basis"] != "completed_time_uninterpreted":
            raise ValueError("Unreviewed day-number basis")
        out["day_number_basis"] = value["day_number_basis"]
    if "day_rule" in value:
        rule = value["day_rule"]
        if (
            rule not in ("last_day_of_month", "following_named_day")
            or day is not None
            or month is None
            or "day_number_basis" in value
        ):
            raise ValueError("Unreviewed or conflicting relative day rule")
        if rule == "following_named_day":
            anchor = component(value.get("anchor_day"), 1, 31)
            if anchor is None or context.get("source_date_role") != "observation_label":
                raise ValueError("Following day requires its named observing-day anchor")
            out["anchor_day"] = anchor
        elif "anchor_day" in value:
            raise ValueError("Unexpected relative-day anchor")
        out["day_rule"] = rule
    elif "anchor_day" in value:
        raise ValueError("Date anchor requires an explicit relative-day rule")
    if "month_part" in value:
        if (
            value["month_part"] != "end"
            or month is None
            or day is not None
            or "day_rule" in value
            or "day_number_basis" in value
        ):
            raise ValueError("Unreviewed or conflicting month-part claim")
        out["month_part"] = "end"
    return out


def date_source(row):
    if row.get("source_id") is not None:
        return row["source_id"]
    if row.get("volume") is not None:
        return "tycho-oo-" + str(row["volume"])
    return None


def structured_context_date_claim(context):
    """Expose reviewed named components while retaining their source qualifications."""
    value = context.get("value")
    if (
        context.get("kind") != "source_observation_context"
        or not isinstance(value, dict)
        or not {"year", "month_name", "day"} <= set(value)
    ):
        return None
    date = {"year": value["year"], "day": value["day"]}
    if value["month_name"] is not None:
        date["month_original"] = value["month_name"]
    adapted = dict(context, kind="recorded_date", value=date)
    for key in ("calendar", "day_origin"):
        if key in context and key in value and context[key] != value[key]:
            raise ValueError("Structured date has conflicting calendar or day-origin claims")
        adapted[key] = value.get(key, context.get(key))
    claim = public_date_claim(adapted)
    claim["claim_basis"] = "reviewed_structured_context"
    for original, public in (
        ("date_expression", "source_date_expression"),
        ("record_type", "source_context_record_type"),
        ("clock_convention", "source_clock_qualification"),
    ):
        item = value.get(original)
        if item is not None:
            if not isinstance(item, str):
                raise ValueError("Structured date qualification must be text")
            claim[public] = item
    return claim


def project_date_claims(contexts, assertions, events, *, include_structured_contexts=False):
    known = {r["id"] for r in contexts}
    scoped = {(r["id"], r.get("review_id")): r for r in contexts}
    dates = {}
    for context in contexts:
        if context["kind"] == "recorded_date":
            if context.get("source_date_role") == "model_prediction" and not any(
                k in context for k in ("model_name", "model_date_relation", "subject")
            ):
                # The immutable review may bind model attribution in a companion
                # row context. Resolve it within the same review and source only.
                candidates = {}
                for row in assertions:
                    if (
                        context["id"] not in row.get("context_ids", [])
                        or row.get("review_id") != context.get("review_id")
                        or source_key(row) != source_key(context)
                        or row.get("subject") != "Sun"
                    ):
                        continue
                    for cid in row.get("context_ids", []):
                        companion = scoped.get((cid, context.get("review_id")))
                        value = companion.get("value", {}) if companion else {}
                        if (
                            isinstance(value, dict)
                            and value.get("record_type") == "historical_model_ingress_row"
                            and source_key(companion) == source_key(context)
                            and value.get("sign") in ("Aries", "Cancer", "Libra", "Capricorn")
                            and all(
                                value.get(a) == context["value"].get(b)
                                for a, b in (
                                    ("year_label", "year"),
                                    ("month", "month"),
                                    ("day", "day"),
                                )
                            )
                        ):
                            candidates[cid] = value.get("model")
                if len(candidates) != 1:
                    raise ValueError("Model ingress date requires one source-bound attribution")
                context = dict(
                    context,
                    model_name=next(iter(candidates.values())),
                    model_date_relation="solar_ingress_on_named_day",
                    subject="Sun",
                )
            claim = public_date_claim(context)
        elif include_structured_contexts:
            claim = structured_context_date_claim(context)
        else:
            claim = None
        if claim is None:
            continue
        old = dates.get(claim["id"])
        if old is not None and old != claim:
            raise ValueError("Conflicting duplicate reviewed date identity")
        dates[claim["id"]] = claim

    def associations(rows):
        out = {}
        for row in rows:
            ids = row.get("context_ids", [])
            if not isinstance(ids, list) or any(cid not in known for cid in ids):
                raise ValueError("Missing reviewed context")
            selected = sorted({cid for cid in ids if cid in dates})
            if date_source(row) is not None and any(
                date_source(dates[cid]) != date_source(row) for cid in selected
            ):
                raise ValueError("Reviewed date context crosses source volumes")
            out[row["id"]] = selected
        return out

    return dict(
        date_claims=[dates[cid] for cid in sorted(dates)],
        assertion_date_ids=associations(assertions),
        event_date_ids=associations(events),
    )


def validate_date_links(assertions, events, date_claims, series=()):
    byid = {r["id"]: r for r in date_claims}
    if len(byid) != len(date_claims):
        raise ValueError("Duplicate public date identity")
    for row in [*assertions, *events, *series]:
        ids = row.get("source_date_claim_ids", [])
        if (
            not isinstance(ids, list)
            or len(set(ids)) != len(ids)
            or any(cid not in byid for cid in ids)
        ):
            raise ValueError("Missing or duplicate public date claim link")
        if date_source(row) is not None and any(
            date_source(byid[cid]) != date_source(row) for cid in ids
        ):
            raise ValueError("Public date claim crosses source volumes")
