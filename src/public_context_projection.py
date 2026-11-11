"""Project reviewed source-position metadata into self-contained public locators."""

import copy
import hashlib
import json
import re
from collections import defaultdict
from collections import Counter

from .catalog_release import scope_id
from .catalog import source_key as catalogue_source_key


def source_key(record):
    # Existing public Tycho contexts already carry both bibliographic fields.
    return record["volume"] if record.get("volume") is not None else catalogue_source_key(record)


def value_hash(value):
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()


LINE_MAPS = {
    "instrument_by_line",
    "corresponding_time_keys_by_line",
    "ordinals_by_lines",
    "transit_instruments_by_line",
    "line_labels",
    "scope_by_line",
    "blank_columns_by_line",
    "source_quality_by_line",
    "interpreted_labels",
    "source_labels",
}
PRIVATE_TOKENS = ("/home/", "/site/", "/tmp/", "recovery/", "data/mars", "prepub", "batch_")
OPERATIONAL_FIELDS = {
    "batch_page_index",
    "projection",
    "projection_status",
    "import_status",
    "ingestion_status",
    "review_id",
    "review_basis",
    "review_scope",
    "followup_queue",
    "future_planet_import_queue",
    "supplementary_queue",
    "scan_access_pending",
    "required_in_final_clock_projection",
    "required_in_final_context_projection",
    "required_in_final_instrument_projection",
    "context_qualifications_and_model_scale_reference_segments_required_in_final_dataset",
    "source_diagram_and_triangle_scopes_required_in_final_projection",
    "cross_reference_followup_pending",
    "note_region_queued_for_companion_inspection",
    "external_record_queued_not_imported_here",
    "queued_Venus_stellar_reduction_parameter",
    "queued_other_target_record",
    "queued_supporting_solar_calculation",
    "Moon_measurements_queued_under_own_target",
    "complete_Venus_only_table_queued",
    "lunar_record_queued_separately",
    "retained_for_later_lunar_ingestion",
    "note3_already_reviewed_for_March5",
    "no_new_diagram_count",
    "not_modern_project_history",
    "legacy238_not_a_printed_page_or_scan_locator",
    "legacy_source_page_not_assigned_as_printed_page",
    "Moon_Sun_and_Venus_measurements_not_imported_as_Mars",
    "Venus_quantities_not_imported_as_Mars",
    "adjacent_Jupiter_row_not_imported",
    "font_note_following_November_dates_not_imported",
    "intervening_saturn_values_not_imported",
    "later_November_dates_not_imported",
    "lunar_quantities_not_imported_under_mars_heading",
    "no_claim_of_full_companion_import",
    "non_mars_numbers_not_imported_merely_from_adjacency",
    "non_mars_quantities_not_imported",
    "non_mars_rows_not_imported",
    "numeric_jupiter_reductions_imported_here",
    "other_planet_rows_imported",
    "pole_star_readings_not_imported_as_Mars_support",
    "preceding_Jupiter_Saturn_readings_not_imported",
    "preceding_Venus_Moon_Jupiter_rows_not_imported",
    "preceding_Venus_Moon_values_not_imported",
    "preceding_Venus_declinations_not_imported",
    "preceding_Venus_rows_not_imported",
    "preceding_other_planet_rows_not_imported",
    "source_margin_calculation_separately_imported",
    "target_readings_not_imported_by_this_reference",
}
PUBLIC_FIELD_NAMES = {
    "full_annotation_scope_unassigned_unless_separately_reviewed": "full_annotation_scope_unassigned",
    "numerical_variants_keep_prior_review_states": "numerical_variants_retained_separately",
    "degree_minute_interpretation_reviewed": "degree_minute_interpretation",
    "reviewed_forward_column_inheritance": "forward_column_inheritance",
    "reviewed_leo_column_inheritance": "leo_column_inheritance",
    "reviewed_year": "source_year",
    "geometry_scope_is_this_review": "geometry_scope_is_current_source_passage",
    "complete_contextual_clocks_required_before_numeric_difference_check": "clock_completion_needed_for_numerical_comparison",
}


def scientific_metadata(value):
    """Omit execution reminders while retaining scientific qualifications."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in OPERATIONAL_FIELDS:
                continue
            if key == "not_imported_as_additional_observing_record":
                result["additional_observing_record"] = not item
            elif key == "no_correction_applied_by_importer":
                result["catalogue_correction_applied"] = not item
            else:
                result[PUBLIC_FIELD_NAMES.get(key, key)] = scientific_metadata(item)
        return result
    if isinstance(value, list):
        return [scientific_metadata(x) for x in value]
    return value


def resolve_references(contexts, quantities, events=()):
    """Replace review-local selectors with typed catalogue references.

    An explicitly named foreign scope takes precedence. Missing selectors stay
    unresolved; uniqueness elsewhere in the catalogue is not matching evidence.
    """
    targets = defaultdict(list)
    for kind, records in (("quantity", quantities), ("context", contexts), ("group", events)):
        for row in records:
            if "key" not in row:
                continue
            ref = dict(kind=kind, id=row["id"])
            if kind == "context":
                ref["scope_id"] = scope_id(row["review_id"])
            targets[(row["review_id"], row["key"])].append(ref)

    def reference(c, key, field, container):
        stem = field.removesuffix("_keys").removesuffix("_key")
        prefixes = [stem]
        while "_" in stem:
            stem = stem.rsplit("_", 1)[0]
            prefixes.append(stem)
        scopes = []
        for prefix in prefixes:
            for suffix in ("_review_id", "_review", "_reviews"):
                found = container.get(prefix + suffix)
                if found:
                    scopes = found if isinstance(found, list) else [found]
                    break
            if scopes:
                break
        if not scopes:
            scopes = [c["review_id"]]
        found = [r for scope in scopes for r in targets[(scope, key)]]
        if not found and scopes == [c["review_id"]]:
            declared = [
                v for k, v in container.items() if k.endswith(("_review", "_review_id", "_reviews"))
            ]
            for value in declared:
                for scope in value if isinstance(value, list) else [value]:
                    found.extend(targets[(scope, key)])
        found = {json.dumps(r, sort_keys=True): r for r in found}
        if len(found) == 1:
            return next(iter(found.values()))
        if found:
            return dict(
                status="multiple_source_references", references=[found[k] for k in sorted(found)]
            )
        return dict(
            status="unresolved_source_reference",
            id="reference-" + value_hash([c["id"], c["review_id"], field, key])[:24],
        )

    def walk(v, c):
        if isinstance(v, dict):
            if "assertion_id" in v:
                # These explicit references already identify their source row.
                return {k: walk(x, c) for k, x in v.items() if k not in ("key", "review_id")}
            if "context_id" in v and "review_id" in v:
                return dict(kind="context", id=v["context_id"], scope_id=scope_id(v["review_id"]))
            out = {}
            for key, item in v.items():
                if key.endswith(("_review", "_review_id", "_reviews")) and not isinstance(
                    item, bool
                ):
                    continue
                if key in ("note_keys", "editorial_note_key"):
                    out[key.replace("_keys", "_markers").replace("_key", "_marker")] = item
                elif key.endswith("_key") and isinstance(item, str):
                    out[key[:-4] + "_ref"] = reference(c, item, key, v)
                elif key.endswith("_keys") and isinstance(item, list):
                    out[key[:-5] + "_refs"] = [reference(c, x, key, v) for x in item]
                elif (
                    key.endswith("_by_assertion_key")
                    or key == "reference_by_assertion_key"
                    or key == "geometry_keys"
                ) and isinstance(item, dict):
                    out[
                        key.replace("_by_assertion_key", "_by_quantity").replace(
                            "geometry_keys", "geometry_references"
                        )
                    ] = [
                        dict(reference=reference(c, k, key, v), value=walk(x, c))
                        for k, x in item.items()
                    ]
                elif key == "corresponding_time_keys_by_locus" and isinstance(item, dict):
                    out["corresponding_time_refs_by_locus"] = {
                        n: reference(c, x, key, v) for n, x in item.items()
                    }
                else:
                    out[key] = walk(item, c)
            return out
        if isinstance(v, list):
            return [walk(x, c) for x in v]
        return v

    return [dict(c, value=walk(c.get("value"), c)) for c in contexts]


def project_contexts(contexts, provenance, *, quantities=(), events=(), approvals=(), bindings=()):
    approvals = list(approvals)
    approved = {(a["context_id"], a["review_id"]): a for a in approvals}
    if len(approved) != len(approvals):
        raise ValueError("Repeated public context approval")
    relocations = {b["review_id"]: b for b in bindings}
    q_at = defaultdict(list)
    q_pages = defaultdict(set)
    q_scoped_pages = defaultdict(set)
    c_at = defaultdict(list)
    for q in quantities:
        key = (source_key(q), q["line"])
        q_at[key].append(q["id"])
        if type(q.get("printed_page")) is int and q["printed_page"] > 0:
            q_pages[key].add(q["printed_page"])
            q_scoped_pages[(*key, q.get("review_id"))].add(q["printed_page"])
    quantity_by_id = {q["id"]: q for q in quantities}
    contexts_by_scope = {(c["id"], scope_id(c["review_id"])): c for c in contexts}
    for c in contexts:
        for n in set(c.get("lines", [])) | ({c["line"]} if c.get("line") is not None else set()):
            c_at[(source_key(c), n)].append(
                dict(context_id=c["id"], scope_id=scope_id(c["review_id"]))
            )
    loci = {}
    used = set()
    result = []

    def relocate(c, n, key):
        if key == "compiled_anchor":
            return n
        binding = relocations.get(c["review_id"])
        if binding is None or (
            c["kind"] == "source_coordinate_frame" and key in ("line_start", "line_end")
        ):
            return n
        interval = binding["original_interval"]
        if interval["line_start"] <= n <= interval["line_end"]:
            return n + binding["line_offset"]
        supporting = {p["original_line"]: p["current_line"] for p in binding["supporting_lines"]}
        if n not in supporting:
            raise ValueError("Context position lacks a reviewed source relocation")
        return supporting[n]

    def locus(c, n, key):
        if type(n) is not int or n < 1:
            raise ValueError("Invalid source-position pointer")
        n = relocate(c, n, key)
        volume = source_key(c)
        sid = c.get("source_id") or "tycho-oo-" + str(volume)
        token = [sid, c.get("edition_sha256"), n]
        maps = provenance.get(volume, {})
        global_claim = maps.get(n, maps.get(str(n), {}))
        reviewed = q_pages[(volume, n)]
        split_page = len(reviewed | set(global_claim.get("pages", []))) > 1

        def scoped_page(record):
            pages = q_scoped_pages[(volume, n, record.get("review_id"))]
            if len(pages) > 1:
                raise ValueError("Conflicting reviewed pages within one source scope")
            scoped = provenance.get((volume, record.get("review_id")), {})
            claim = scoped.get(n, scoped.get(str(n), {})).get("page")
            return next(iter(pages)) if pages else claim

        if split_page:
            page = scoped_page(c)
            if type(page) is not int or page <= 0:
                raise ValueError("Cross-leaf source position requires a reviewed page scope")
            token.extend(["reviewed_page", page])
            reviewed = reviewed & {page}
        identifier = "locus-" + value_hash(token)[:24]
        if identifier not in loci:
            scoped = provenance.get((volume, c.get("review_id")), {}) if split_page else maps
            claim = scoped.get(n, scoped.get(str(n), {})).get("page")
            claim = claim if type(claim) is int and claim > 0 else None
            if not split_page:
                page = next(iter(reviewed)) if reviewed else claim
            loci[identifier] = dict(
                id=identifier,
                source_id=sid,
                printed_page=page,
                page_basis="reviewed_quantity_citation"
                if reviewed
                else "automatic_page_index"
                if claim is not None
                else None,
                status="mapped_source_page"
                if reviewed
                else "provisional_source_page"
                if claim is not None
                else "page_unestablished",
                quantity_ids=sorted(
                    q
                    for q in q_at[(volume, n)]
                    if not split_page or quantity_by_id[q].get("printed_page") == page
                ),
                context_ids=sorted(
                    (
                        p
                        for p in c_at[(volume, n)]
                        if not split_page
                        or scoped_page(contexts_by_scope[(p["context_id"], p["scope_id"])]) == page
                    ),
                    key=lambda p: (p["context_id"], p["scope_id"]),
                ),
            )
            if reviewed and claim is not None and claim != page:
                loci[identifier]["provisional_page_claim"] = claim
        return identifier

    def transform(value, c, path=(), line_bounds=False):
        if isinstance(value, dict):
            if "assertion_id" in value:
                target = quantity_by_id.get(value["assertion_id"])
                if target is None:
                    raise ValueError("Context names a missing source quantity")
                out = {
                    k: transform(x, c, (*path, k))
                    for k, x in value.items()
                    if k not in ("source_line", "key", "review_id")
                }
                if "source_line" in value:
                    out["source_locus_id"] = locus(
                        dict(target, kind="source_quantity"), target["line"], "compiled_anchor"
                    )
                return out
            out = {}
            for key, item in value.items():
                scalar = (
                    key == "line"
                    or key.endswith("_line")
                    or key in ("line_start", "line_end")
                    or (line_bounds and key in ("start", "end"))
                )
                if scalar and type(item) is int:
                    name = (key[:-5] if key.endswith("_line") else key) + "_locus_id"
                    if key == "line":
                        name = "source_locus_id"
                    if key in ("line_start", "line_end"):
                        name = "source_" + key[5:] + "_locus_id"
                    out[name] = locus(c, item, key)
                elif (
                    (key == "lines" or key.endswith("_lines") or key == "source_scope_line_range")
                    and isinstance(item, list)
                    and all(type(n) is int for n in item)
                ):
                    name = (key[:-6] if key.endswith("_lines") else "source") + "_locus_ids"
                    if key == "source_scope_line_range":
                        name = "source_scope_locus_range"
                    out[name] = [locus(c, n, key) for n in item]
                elif (
                    (
                        key in LINE_MAPS
                        or (key == "components" and c["id"] == "context-v11-9fe40791f44ff23a19ff")
                    )
                    and isinstance(item, dict)
                    and any(str(n).isdigit() for n in item)
                ):
                    name = key.replace("_by_lines", "_by_locus").replace("_by_line", "_by_locus")
                    if name == key:
                        name = key + "_by_locus"
                    out[name] = {
                        locus(c, int(n), key): transform(x, c, (*path, key, n))
                        for n, x in item.items()
                    }
                elif key == "source_section_headings" and isinstance(item, list):
                    out[key] = [
                        dict(
                            source_locus_id=locus(c, n, key),
                            heading=re.sub(r"\[\^[^\]]+\]", "", text),
                        )
                        for n, text in item
                    ]
                else:
                    out[key] = transform(item, c, (*path, key), line_bounds=key.endswith("_lines"))
            return out
        if isinstance(value, list):
            return [transform(v, c, (*path, "[]"), line_bounds=line_bounds) for v in value]
        if isinstance(value, str) and any(t in value for t in PRIVATE_TOKENS):
            raise ValueError("Unreviewed operational text in public context: " + c["id"])
        return value

    for context in contexts:
        c = copy.deepcopy(context)
        key = (c["id"], c["review_id"])
        approval = approved.get(key)
        if approval:
            if approval.get("original_value_sha256") != value_hash(
                c.get("value")
            ) or not approval.get("reason"):
                raise ValueError("Public context approval differs from its source payload")
            c["value"] = copy.deepcopy(approval["value"])
            used.add(key)
        c["value"] = transform(c.get("value"), c)
        c["source_id"] = c.get("source_id") or "tycho-oo-" + str(c["volume"])
        positions = list(
            dict.fromkeys(c.get("lines", []) + ([c["line"]] if c.get("line") is not None else []))
        )
        # Compiled context anchors have already been rebound; only positions
        # embedded in the original contextual payload need relocation.
        anchors = [locus(c, n, "compiled_anchor") for n in positions]
        annotation = isinstance(c["value"], dict) and "edition_annotation" in c["value"].get(
            "record_type", ""
        )
        c["locator"] = dict(
            source_locus_ids=anchors,
            role="attachment_and_scope_pages" if annotation else "source_evidence_pages",
        )
        result.append(c)
    if used != set(approved):
        raise ValueError("Public context approval has no matching source payload")
    resolved = resolve_references(result, quantities, events)
    return [dict(c, value=scientific_metadata(c["value"])) for c in resolved], [
        loci[k] for k in sorted(loci)
    ]


def validate_projection(contexts, loci, quantities, events):
    """Validate typed references without accepting unresolved selectors as links."""
    known = dict(
        quantity={q["id"] for q in quantities},
        group={e["id"] for e in events},
        context={(c["id"], scope_id(c["review_id"])) for c in contexts},
    )
    locations = {r["id"] for r in loci}
    counts = Counter()

    def walk(value):
        if isinstance(value, dict):
            kind = value.get("kind")
            if kind in known and "id" in value:
                key = (value["id"], value.get("scope_id")) if kind == "context" else value["id"]
                if key not in known[kind]:
                    raise ValueError("Dangling public " + kind + " reference")
                counts[kind + "_references"] += 1
            if "assertion_id" in value and value["assertion_id"] not in known["quantity"]:
                raise ValueError("Dangling explicit source quantity reference")
            if value.get("status") == "unresolved_source_reference":
                counts["unresolved_references"] += 1
            for k, x in value.items():
                if isinstance(k, str) and k.startswith("locus-") and k not in locations:
                    raise ValueError("Dangling public location key")
                if k.endswith("_locus_id") and x not in locations:
                    raise ValueError("Dangling public location reference")
                if k.endswith("_locus_ids") and any(n not in locations for n in x):
                    raise ValueError("Dangling public location references")
                walk(x)
        elif isinstance(value, list):
            for x in value:
                walk(x)

    for c in contexts:
        walk(c["value"])
        walk(c.get("locator", {}))
    return dict(
        contexts=len(contexts),
        source_loci=len(loci),
        references=dict(counts),
        location_statuses=dict(Counter(r["status"] for r in loci)),
        reviewed_locations_with_differing_automatic_page_claim=sum(
            "provisional_page_claim" in r for r in loci
        ),
        status="projected_references_validated_pending_release_audit",
    )
