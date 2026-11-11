"""Build a portable catalogue draft from verified extraction outputs.

Interpretations are versioned; original quantities and qualified contexts remain
intact. Drafts stay in the excluded workspace pending public projection/audit.
"""

import argparse
import copy
from contextlib import closing
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import shutil
import tempfile

from .core import digest
from .recovery import write_json_atomic
from .release_transaction import publish, recover
from .catalog_indexes import create_indexes
from .source_registry import public_sources


CSV_COLUMNS = (
    "id",
    "source_id",
    "artifact_sha256",
    "source_entry_id",
    "locator",
    "volume",
    "printed_page",
    "expression",
    "quantity",
    "role",
    "subject",
    "reference_object",
    "status",
    "unit",
    "value_exact",
    "signed_value_exact",
    "value_decimal",
    "value_degrees_decimal",
    "interpretation_version",
    "event_id",
    "original_quantity",
    "original_subject",
    "original_normalization_status",
    "direction",
    "record_status",
    "flags_json",
    "uncertainty_json",
    "components_json",
    "scientific_metadata_json",
    "date_claims_json",
    "source_url",
)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def source_value_hash(row):
    fields = (
        "id",
        "volume",
        "source_expression",
        "quantity",
        "subject",
        "reference",
        "role",
        "direction",
        "components",
        "normalized",
        "flags",
    )
    return hashlib.sha256(encoded({k: row.get(k) for k in fields}).encode()).hexdigest()


def normalize_minute_motion(expression):
    match = re.fullmatch(r"\s*(?:(\d+)″\s*)?(\d+)‴\s*", expression)
    if not match or int(match[2]) >= 60:
        raise ValueError("Expected explicit angular seconds/thirds per source minute")
    parts = {"arcsexagesimal_third": match[2]}
    if match[1] is not None:
        parts["arcsecond"] = match[1]
    return dict(
        status="exact",
        unit="arcsecond_per_source_minute",
        magnitude=str(Fraction(match[1] or "0") + Fraction(int(match[2]), 60)),
        magnitude_degrees=None,
        signed_magnitude=None,
        least_component_unit="arcsexagesimal_third",
        components=parts,
    )


def scope_id(review_id):
    return hashlib.sha256(review_id.encode()).hexdigest()


def adapt_source_quantities(records):
    """Adapt source/artifact-qualified exports without historical coercions.

    Source-local IDs and complete payloads remain available. This changes the
    representation only; source acceptance and astrometric reductions are not
    inferred here.
    """
    source = []
    published = []
    events = {}
    seen = set()

    def identity(kind, sid, artifact, local):
        return (
            kind + "-" + hashlib.sha256(encoded([sid, artifact, local]).encode()).hexdigest()[:32]
        )

    for original in records:
        row = copy.deepcopy(original)
        sid, artifact, local = (row.get(k) for k in ("source_id", "artifact_sha256", "id"))
        if (
            not all(isinstance(s, str) and s for s in (sid, artifact, local))
            or not re.fullmatch(r"[0-9a-f]{64}", artifact)
            or not row.get("locator")
            or not isinstance(row.get("normalized"), dict)
            or not row["normalized"].get("unit")
        ):
            raise ValueError(
                "Source export requires identities, checksum, locator and explicit unit"
            )
        aid = identity("quantity", sid, artifact, local)
        if aid in seen:
            raise ValueError("Repeated source/artifact/entry identity")
        seen.add(aid)
        norm = copy.deepcopy(row["normalized"])
        magnitude = norm.get("magnitude")
        if magnitude is not None:
            Fraction(magnitude)
        norm.setdefault(
            "status",
            "exact"
            if magnitude is not None
            else "incomplete"
            if "incomplete_coordinate" in row.get("flags", [])
            else "source_expression",
        )
        norm.setdefault("magnitude_degrees", None)
        norm.setdefault("signed_magnitude", None)
        local_event = row.get("event_id")
        event_id = identity("event", sid, artifact, local_event) if local_event else None
        canonical = dict(
            row,
            id=aid,
            source_entry_id=local,
            source_expression=row["literal"],
            reference=row.get("reference"),
            review_id=sid + ":" + artifact,
            context_ids=[],
            components=row.get("components", {}),
            normalized=norm,
            event_id=event_id,
            source_payload=copy.deepcopy(original),
        )
        source.append(canonical)
        published.append(
            {
                k: copy.deepcopy(v)
                for k, v in canonical.items()
                if k not in ("review_id", "context_ids", "source_payload")
            }
        )
        if event_id:
            event = events.setdefault(
                event_id,
                dict(
                    id=event_id,
                    source_id=sid,
                    artifact_sha256=artifact,
                    source_entry_id=local_event,
                    review_id=canonical["review_id"],
                    context_ids=[],
                    clock_assertion_id=None,
                    epoch_assertion_id=None,
                    clock_candidate_ids=[],
                    observation_epoch_quantity_ids=[],
                ),
            )
            if row["quantity"] in ("recorded_clock", "transit_clock"):
                event["clock_candidate_ids"].append(aid)
                event["clock_assertion_id"] = (
                    aid if len(event["clock_candidate_ids"]) == 1 else None
                )
            if row["quantity"] == "recorded_epoch":
                event["observation_epoch_quantity_ids"].append(aid)
    return source, published, list(events.values())


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE metadata(key TEXT PRIMARY KEY,value_json TEXT NOT NULL);
CREATE TABLE sources(id TEXT PRIMARY KEY,author TEXT,work_id TEXT,edition_id TEXT,title TEXT,volume INTEGER,data_json TEXT NOT NULL);
CREATE TABLE artifacts(source_id TEXT REFERENCES sources(id),sha256 TEXT,media_type TEXT,retrieved_at TEXT,
 redistribution_status TEXT,content BLOB,metadata_json TEXT NOT NULL,PRIMARY KEY(source_id,sha256));
CREATE TABLE groups(id TEXT PRIMARY KEY,clock_quantity_id TEXT REFERENCES quantities(id) DEFERRABLE INITIALLY DEFERRED,
 epoch_quantity_id TEXT REFERENCES quantities(id) DEFERRABLE INITIALLY DEFERRED,data_json TEXT NOT NULL);
CREATE TABLE quantities(id TEXT PRIMARY KEY,volume INTEGER,printed_page INTEGER,
 expression TEXT NOT NULL,role TEXT NOT NULL,event_id TEXT REFERENCES groups(id),series_id TEXT,
 original_json TEXT NOT NULL,components_json TEXT NOT NULL,uncertainty_json TEXT NOT NULL,
 source_id TEXT NOT NULL REFERENCES sources(id),artifact_sha256 TEXT,source_entry_id TEXT NOT NULL,locator TEXT,
 scientific_metadata_json TEXT NOT NULL,source_payload_json TEXT,
 UNIQUE(source_id,artifact_sha256,source_entry_id),
 FOREIGN KEY(source_id,artifact_sha256) REFERENCES artifacts(source_id,sha256));
CREATE TABLE images(source_id TEXT REFERENCES sources(id),frame_id TEXT,version_id TEXT,sha256 TEXT NOT NULL,
 archive_md5 TEXT,bytes INTEGER,public_url TEXT,metadata_json TEXT NOT NULL,PRIMARY KEY(source_id,frame_id,version_id));
CREATE TABLE interpretations(quantity_id TEXT REFERENCES quantities(id),version INTEGER NOT NULL,
 quantity TEXT NOT NULL,subject TEXT,reference_object TEXT,status TEXT NOT NULL,unit TEXT,value_exact TEXT,
 signed_value_exact TEXT,normalized_json TEXT NOT NULL,components_json TEXT NOT NULL,flags_json TEXT NOT NULL,
 revision_json TEXT,PRIMARY KEY(quantity_id,version));
CREATE TABLE contexts(context_id TEXT,scope_id TEXT,kind TEXT NOT NULL,value_json TEXT NOT NULL,
 source_id TEXT REFERENCES sources(id),locator_json TEXT NOT NULL,
 PRIMARY KEY(context_id,scope_id));
CREATE TABLE quantity_contexts(id TEXT REFERENCES quantities(id),context_id TEXT,scope_id TEXT,
 PRIMARY KEY(id,context_id,scope_id),FOREIGN KEY(context_id,scope_id) REFERENCES contexts(context_id,scope_id));
CREATE TABLE group_contexts(id TEXT REFERENCES groups(id),context_id TEXT,scope_id TEXT,
 PRIMARY KEY(id,context_id,scope_id),FOREIGN KEY(context_id,scope_id) REFERENCES contexts(context_id,scope_id));
CREATE TABLE source_loci(id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES sources(id),printed_page INTEGER,
 status TEXT NOT NULL,data_json TEXT NOT NULL);
CREATE TABLE locus_quantities(locus_id TEXT REFERENCES source_loci(id),quantity_id TEXT REFERENCES quantities(id),
 PRIMARY KEY(locus_id,quantity_id));
CREATE TABLE locus_contexts(locus_id TEXT REFERENCES source_loci(id),context_id TEXT,scope_id TEXT,
 PRIMARY KEY(locus_id,context_id,scope_id),FOREIGN KEY(context_id,scope_id) REFERENCES contexts(context_id,scope_id));
CREATE TABLE dates(id TEXT PRIMARY KEY,data_json TEXT NOT NULL);
CREATE TABLE quantity_dates(quantity_id TEXT REFERENCES quantities(id),date_id TEXT REFERENCES dates(id),PRIMARY KEY(quantity_id,date_id));
CREATE TABLE group_dates(group_id TEXT REFERENCES groups(id),date_id TEXT REFERENCES dates(id),PRIMARY KEY(group_id,date_id));
CREATE TABLE series(id TEXT PRIMARY KEY,data_json TEXT NOT NULL);
CREATE TABLE series_quantities(series_id TEXT REFERENCES series(id),quantity_id TEXT REFERENCES quantities(id),PRIMARY KEY(series_id,quantity_id));
CREATE TABLE derivations(id TEXT PRIMARY KEY,output_quantity_id TEXT REFERENCES quantities(id),data_json TEXT NOT NULL);
CREATE TABLE derivation_inputs(derivation_id TEXT REFERENCES derivations(id),ordinal INTEGER,quantity_id TEXT REFERENCES quantities(id),PRIMARY KEY(derivation_id,ordinal));
CREATE TABLE control_links(control_id TEXT PRIMARY KEY,quantity_id TEXT NOT NULL REFERENCES quantities(id));
CREATE TABLE quantity_links(from_id TEXT REFERENCES quantities(id) DEFERRABLE INITIALLY DEFERRED,
 to_id TEXT REFERENCES quantities(id) DEFERRABLE INITIALLY DEFERRED,kind TEXT NOT NULL,PRIMARY KEY(from_id,to_id,kind));
CREATE VIEW diagrams AS SELECT * FROM contexts WHERE kind='source_diagram';
CREATE VIEW source_records AS SELECT id,source_id,artifact_sha256,source_entry_id,expression,components_json,
 COALESCE(source_payload_json,original_json) AS source_payload_json FROM quantities;
CREATE VIEW catalogue AS SELECT q.id,q.source_id,q.artifact_sha256,q.source_entry_id,q.locator,
 q.volume,q.printed_page,q.expression,q.role,q.event_id,q.series_id,
 i.version,i.quantity,i.subject,i.reference_object,i.status,i.unit,i.value_exact,i.signed_value_exact
 FROM quantities q JOIN interpretations i ON i.quantity_id=q.id
 WHERE i.version=(SELECT MAX(j.version) FROM interpretations j WHERE j.quantity_id=q.id);
"""


SCIENCE_FIELDS = (
    "platform",
    "technique",
    "time_scale",
    "date",
    "precision",
    "exposure_start",
    "exposure_midpoint",
    "exposure_end",
    "exposure_duration",
    "exposure_midpoint_status",
    "stated_uncertainty",
    "coordinate_origin",
    "coordinate_frame",
    "equinox",
    "equinox_code",
    "position_endpoint",
    "ra_limb",
    "dec_limb",
    "site",
    "observer",
    "observer_code",
    "observatory_telescope_code",
    "telescope",
    "instrument",
    "catalogue_code",
    "clamp_code",
    "circle_code",
    "observation_type",
    "reduction_system",
    "corrections",
    "correction_history_status",
    "dependency",
    "adapter_version",
    "mars_relation",
    "description",
    "derived_normalization",
)
CORE_FIELDS = {
    "id",
    "source_id",
    "artifact_sha256",
    "source_entry_id",
    "locator",
    "volume",
    "printed_page",
    "source_expression",
    "literal",
    "quantity",
    "role",
    "subject",
    "reference",
    "direction",
    "normalized",
    "flags",
    "event_id",
    "series_id",
    "record_status",
    "components",
    "uncertainty",
}


def write_catalogue(
    output,
    source,
    published,
    contexts,
    events,
    dates,
    derivations,
    series,
    sources,
    revisions,
    metadata,
    *,
    artifacts=(),
    images=(),
    loci=(),
):
    """Write a crash-safe internal draft, rejecting lost identities or relations."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    recover(output)
    src = {r["id"]: r for r in source}
    pub = {r["id"]: r for r in published}
    if len(src) != len(source) or len(pub) != len(published) or src.keys() != pub.keys():
        raise ValueError("Source and published quantity identities differ or repeat")
    revised = {}
    revision_ids = set()
    for review in revisions:
        row = src.get(review.get("quantity_id"))
        if (
            row is None
            or review.get("source_value_sha256") != source_value_hash(row)
            or row["id"] in revised
            or review.get("id") in revision_ids
            or not review.get("basis")
        ):
            raise ValueError("Interpretation review differs from its preserved source")
        rate = (
            review.get("kind") == "angular_minutely_motion"
            and row["quantity"] == "calculation_angle"
            and row["role"] == "historical_input"
            and not row.get("components")
            and row["normalized"]["status"] == "unsupported"
            and review.get("subject") in ("Mars", "simple Sun")
        )
        classification = (
            review.get("kind") == "source_quantity_classification"
            and review.get("quantity") == "altitude"
            and row["quantity"] == "unclassified_angle"
            and row["role"] == "recorded_reading"
            and row["subject"] == "Mars"
            and row["normalized"]["status"] == "exact"
            and row["normalized"]["unit"] == "arcsecond"
            and set(row.get("components", {})) == {"degree", "arcminute"}
            and "measurement_type_unresolved" in row["flags"]
            and re.fullmatch(r"[0-9a-f]{64}", review.get("source_evidence_sha256", ""))
        )
        if not (rate or classification):
            raise ValueError("Unreviewed interpretation change")
        revised[row["id"]] = review
        revision_ids.add(review["id"])
    qualified = {(r["id"], scope_id(r["review_id"])): r for r in contexts}
    if len(qualified) != len(contexts):
        raise ValueError("Repeated qualified context identity")
    current = []
    with tempfile.TemporaryDirectory(prefix=".catalogue-", dir=output) as temporary:
        staging = Path(temporary)
        database = staging / "tychonides.sqlite"
        with closing(sqlite3.connect(database)) as db:
            db.executescript(SCHEMA)
            create_indexes(db)
            with db:
                meta = dict(
                    metadata,
                    publication_status="internal_draft_pending_public_projection_and_completeness_audit",
                    schema_version=3,
                )
                db.executemany(
                    "INSERT INTO metadata VALUES (?,?)",
                    [(k, encoded(v)) for k, v in sorted(meta.items())],
                )
                registry = {}
                for record in sources:
                    sid = record.get("id") or record.get("source_id")
                    if sid is None:
                        volume = record.get("volume")
                        if volume not in (10, 11, 12, 13) or not record.get(
                            "translation_pdf", ""
                        ).startswith(
                            "https://books.arsastronomica.com/Tycho_Brahe_Thesaurus_Observationum_"
                        ):
                            raise ValueError(
                                "A source needs its own identity; volume alone is insufficient"
                            )
                        sid = "tycho-oo-" + str(volume)
                        record = dict(
                            record,
                            author="Tycho Brahe",
                            work_id="brahe-thesaurus-observationum",
                            edition_id="ars-astronomica-english",
                        )
                    if sid in registry:
                        raise ValueError("Repeated source identity")
                    registry[sid] = dict(record, id=sid)

                def source_id(row):
                    if row.get("source_id"):
                        if row["source_id"] not in registry:
                            raise ValueError("Quantity names an unregistered source")
                        return row["source_id"]
                    if row.get("volume") not in (10, 11, 12, 13) or not re.fullmatch(
                        "assertion-v" + str(row.get("volume")) + r"-[0-9a-f]{20}", row["id"]
                    ):
                        raise ValueError("Non-Tycho records require an explicit source identity")
                    sid = "tycho-oo-" + str(row["volume"])
                    registry.setdefault(
                        sid,
                        dict(
                            id=sid,
                            volume=row["volume"],
                            author="Tycho Brahe",
                            work_id="brahe-thesaurus-observationum",
                            edition_id="ars-astronomica-english",
                        ),
                    )
                    return sid

                source_ids = {aid: source_id(row) for aid, row in src.items()}
                for sid, record in sorted(registry.items()):
                    db.execute(
                        "INSERT INTO sources VALUES (?,?,?,?,?,?,?)",
                        (
                            sid,
                            record.get("author"),
                            record.get("work_id"),
                            record.get("edition_id"),
                            record.get("title"),
                            record.get("volume"),
                            encoded(record),
                        ),
                    )
                for artifact in sorted(artifacts, key=lambda r: (r["source_id"], r["sha256"])):
                    db.execute(
                        "INSERT INTO artifacts VALUES (?,?,?,?,?,?,?)",
                        (
                            artifact["source_id"],
                            artifact["sha256"],
                            artifact.get("media_type"),
                            artifact.get("retrieved_at"),
                            artifact.get("redistribution_status"),
                            artifact.get("content"),
                            encoded({k: v for k, v in artifact.items() if k != "content"}),
                        ),
                    )
                for image in sorted(
                    images, key=lambda r: (r["source_id"], r["frame_id"], r["version_id"])
                ):
                    db.execute(
                        "INSERT INTO images VALUES (?,?,?,?,?,?,?,?)",
                        (
                            image["source_id"],
                            image["frame_id"],
                            image["version_id"],
                            image["sha256"],
                            image.get("archive_md5"),
                            image.get("bytes"),
                            image.get("public_url"),
                            encoded(image.get("metadata", {})),
                        ),
                    )
                for event in sorted(events, key=lambda r: r["id"]):
                    values = {
                        k: event[k]
                        for k in (
                            "subject",
                            "kind",
                            "flags",
                            "source_id",
                            "artifact_sha256",
                            "source_entry_id",
                            "clock_candidate_ids",
                            "observation_epoch_quantity_ids",
                        )
                        if k in event
                    }
                    db.execute(
                        "INSERT INTO groups VALUES (?,?,?,?)",
                        (
                            event["id"],
                            event.get("clock_assertion_id"),
                            event.get("epoch_assertion_id"),
                            encoded(values),
                        ),
                    )
                date_by_id = {d["id"]: d for d in dates}
                for date in sorted(dates, key=lambda r: r["id"]):
                    db.execute("INSERT INTO dates VALUES (?,?)", (date["id"], encoded(date)))
                for (cid, sid), context in sorted(qualified.items()):
                    db.execute(
                        "INSERT INTO contexts VALUES (?,?,?,?,?,?)",
                        (
                            cid,
                            sid,
                            context["kind"],
                            encoded(context.get("value")),
                            context.get("source_id"),
                            encoded(context.get("locator", {})),
                        ),
                    )
                for aid, row in sorted(src.items()):
                    public = pub[aid]
                    scientific = {k: v for k, v in public.items() if k not in CORE_FIELDS}
                    scientific.update({k: row[k] for k in SCIENCE_FIELDS if k in row})
                    if row.get("source_fragments"):
                        scientific["source_numeric_fragments"] = [
                            fragment["source_expression"] for fragment in row["source_fragments"]
                        ]
                    db.execute(
                        "INSERT INTO quantities VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            aid,
                            row.get("volume"),
                            public.get("printed_page"),
                            row["source_expression"],
                            row["role"],
                            row.get("event_id"),
                            row.get("series_id"),
                            encoded(public),
                            encoded(row.get("components")),
                            encoded(row.get("uncertainty")),
                            source_ids[aid],
                            row.get("artifact_sha256"),
                            row.get("source_entry_id", aid),
                            row.get("locator"),
                            encoded(scientific),
                            encoded(row["source_payload"]) if "source_payload" in row else None,
                        ),
                    )
                    versions = [
                        (
                            0,
                            public["quantity"],
                            public["subject"],
                            public.get("reference"),
                            public["normalized"],
                            row.get("components"),
                            public.get("flags", []),
                            None,
                        )
                    ]
                    if aid in revised:
                        review = revised[aid]
                        if review["kind"] == "angular_minutely_motion":
                            norm = normalize_minute_motion(row["source_expression"])
                            parts = norm.pop("components")
                            versions.append(
                                (
                                    1,
                                    review["kind"],
                                    review["subject"],
                                    None,
                                    norm,
                                    parts,
                                    [
                                        f
                                        for f in public.get("flags", [])
                                        if f != "source_notation_unresolved"
                                    ],
                                    review,
                                )
                            )
                        else:
                            versions.append(
                                (
                                    1,
                                    review["quantity"],
                                    public["subject"],
                                    public.get("reference"),
                                    public["normalized"],
                                    row["components"],
                                    [
                                        f
                                        for f in public.get("flags", [])
                                        if f != "measurement_type_unresolved"
                                    ],
                                    review,
                                )
                            )
                    for (
                        version,
                        quantity,
                        subject,
                        reference,
                        norm,
                        parts,
                        flags,
                        review,
                    ) in versions:
                        db.execute(
                            "INSERT INTO interpretations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (
                                aid,
                                version,
                                quantity,
                                subject,
                                reference,
                                norm["status"],
                                norm.get("unit"),
                                norm.get("magnitude"),
                                norm.get("signed_magnitude"),
                                encoded(norm),
                                encoded(parts),
                                encoded(flags),
                                encoded(review) if review else None,
                            ),
                        )
                    last = versions[-1]
                    for field, value in public.items():
                        if field in (
                            "source_entry_id",
                            "source_id",
                            "artifact_id",
                            "work_id",
                            "edition_id",
                        ):
                            continue
                        targets = (
                            [value]
                            if field.endswith("_id")
                            else value
                            if field.endswith("_ids") and isinstance(value, list)
                            else []
                        )
                        for target in dict.fromkeys(
                            t
                            for t in targets
                            if isinstance(t, str) and t.startswith(("assertion-", "quantity-"))
                        ):
                            if target not in pub:
                                raise ValueError(
                                    "Quantity relationship targets a missing source quantity"
                                )
                            db.execute(
                                "INSERT INTO quantity_links VALUES (?,?,?)", (aid, target, field)
                            )
                    for cid in dict.fromkeys(row.get("context_ids", [])):
                        key = (cid, scope_id(row["review_id"]))
                        if key not in qualified:
                            raise ValueError("Quantity context lacks its review-qualified payload")
                        db.execute("INSERT INTO quantity_contexts VALUES (?,?,?)", (aid, *key))
                    for date_id in public.get("source_date_claim_ids", []):
                        db.execute("INSERT INTO quantity_dates VALUES (?,?)", (aid, date_id))
                    if public.get("workbook_control_id"):
                        db.execute(
                            "INSERT INTO control_links VALUES (?,?)",
                            (public["workbook_control_id"], aid),
                        )
                for event in sorted(events, key=lambda r: r["id"]):
                    for cid in dict.fromkeys(event.get("context_ids", [])):
                        key = (cid, scope_id(event["review_id"]))
                        if key not in qualified:
                            raise ValueError("Group context lacks its review-qualified payload")
                        db.execute("INSERT INTO group_contexts VALUES (?,?,?)", (event["id"], *key))
                    for date_id in event.get("source_date_claim_ids", []):
                        db.execute("INSERT INTO group_dates VALUES (?,?)", (event["id"], date_id))
                for locus in sorted(loci, key=lambda r: r["id"]):
                    db.execute(
                        "INSERT INTO source_loci VALUES (?,?,?,?,?)",
                        (
                            locus["id"],
                            locus["source_id"],
                            locus.get("printed_page"),
                            locus["status"],
                            encoded(locus),
                        ),
                    )
                    for aid in dict.fromkeys(locus.get("quantity_ids", [])):
                        db.execute("INSERT INTO locus_quantities VALUES (?,?)", (locus["id"], aid))
                    for key in locus.get("context_ids", []):
                        db.execute(
                            "INSERT INTO locus_contexts VALUES (?,?,?)",
                            (locus["id"], key["context_id"], key["scope_id"]),
                        )
                for group in sorted(series, key=lambda r: r["id"]):
                    db.execute("INSERT INTO series VALUES (?,?)", (group["id"], encoded(group)))
                    for aid in group["assertion_ids"]:
                        db.execute("INSERT INTO series_quantities VALUES (?,?)", (group["id"], aid))
                for derivation in sorted(derivations, key=lambda r: r["id"]):
                    db.execute(
                        "INSERT INTO derivations VALUES (?,?,?)",
                        (derivation["id"], derivation.get("output_id"), encoded(derivation)),
                    )
                    for n, aid in enumerate(derivation["input_ids"]):
                        db.execute(
                            "INSERT INTO derivation_inputs VALUES (?,?,?)",
                            (derivation["id"], n, aid),
                        )
                if db.execute("PRAGMA foreign_key_check").fetchall():
                    raise ValueError("Catalogue contains dangling relationships")
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Invalid SQLite catalogue")
            counts = {
                name: db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
                for name, table in (
                    ("quantities", "quantities"),
                    ("groups", "groups"),
                    ("qualified_contexts", "contexts"),
                    ("interpretations", "interpretations"),
                    ("controls", "control_links"),
                    ("diagrams", "diagrams"),
                )
            }
            from .csv_projection import project_csv

            current = list(project_csv(db, CSV_COLUMNS))
        columns = CSV_COLUMNS
        with (staging / "tychonides.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(current)
        manifest = dict(
            status="internal_draft_not_public_release",
            **counts,
            output_hashes={n: digest(staging / n) for n in ("tychonides.sqlite", "tychonides.csv")},
        )
        publish(staging, output, manifest)
    return manifest


def promote_catalogue(draft, output, release_id, metadata):
    """Package verified files locally; never modify the draft or deploy them."""
    draft, output = Path(draft).resolve(), Path(output).resolve()
    if (draft / ".pending-release").exists():
        raise ValueError("Draft promotion is incomplete; recover the draft first")
    if output.is_relative_to(draft) or draft.is_relative_to(output):
        raise ValueError("Release and draft directories must be separate")
    if not isinstance(release_id, str) or not re.fullmatch(
        r"(?:tychonides|mars)-[0-9]+\.[0-9]+\.[0-9]+", release_id
    ):
        raise ValueError("Invalid release identity")
    allowed = {
        "coverage",
        "normalization_counts",
        "limitations",
        "counting_units",
        "source_reference_screening",
    }
    if set(metadata) - allowed:
        raise ValueError("Unreviewed public release metadata field")
    manifest = json.loads((draft / "manifest.json").read_text(encoding="utf-8"))
    from .catalog_files import catalog_files

    draft_files = catalog_files(manifest, uncompressed=True)
    for name in draft_files:
        if digest(draft / name) != manifest["output_hashes"][name]:
            raise ValueError("Draft differs from its verified manifest")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".release-", dir=output) as temporary:
        staging = Path(temporary)
        for old, new in zip(draft_files, ("tychonides.sqlite", "tychonides.csv"), strict=True):
            shutil.copyfile(draft / old, staging / new)
        with closing(sqlite3.connect(staging / "tychonides.sqlite")) as db:
            with db:
                values = dict(
                    metadata, publication_status="research_catalogue", release_id=release_id
                )
                for key, value in sorted(values.items()):
                    db.execute(
                        "INSERT OR REPLACE INTO metadata VALUES (?,?)", (key, encoded(value))
                    )
            if (
                db.execute("PRAGMA foreign_key_check").fetchall()
                or db.execute("PRAGMA integrity_check").fetchone()[0] != "ok"
            ):
                raise ValueError("Invalid release database")
            if db.execute("SELECT COUNT(*) FROM catalogue").fetchone()[0] != manifest["quantities"]:
                raise ValueError("Release quantity count differs from verified draft")
        result = {
            k: manifest[k]
            for k in (
                "quantities",
                "groups",
                "qualified_contexts",
                "interpretations",
                "controls",
                "diagrams",
            )
        }
        result.update(
            release_id=release_id,
            status="research_catalogue",
            schema_version=3,
            **metadata,
            output_hashes={
                name: digest(staging / name) for name in ("tychonides.sqlite", "tychonides.csv")
            },
        )
        publish(staging, output, result)
    return result


def build_release(workspace, output, revisions):
    from .review_workflow import checked_hashes, REPO
    from .public_context_projection import project_contexts, validate_projection
    from .source_bindings import load_bindings

    work = Path(workspace)
    read = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
    rows = lambda p: [
        json.loads(line) for line in Path(p).read_text(encoding="utf-8").splitlines() if line
    ]
    checkpoint = read(work / "recovery_checkpoint.json")
    if checkpoint["checkpoint_status"] != "verified_resume_ready":
        raise ValueError("Finish the current extraction checkpoint first")
    if not Path(output).resolve().is_relative_to(work.resolve()):
        raise ValueError("Internal drafts must remain inside the excluded catalogue workspace")
    checked_hashes(REPO, read(work / checkpoint["last_verified"]["artifact_snapshot"]))
    public = REPO / "work/mars-checkpoint-export"
    events = rows(work / "events.jsonl")
    event_dates = {
        r["id"]: r.get("source_date_claim_ids", []) for r in rows(public / "event_groups.jsonl")
    }
    events = [dict(e, source_date_claim_ids=event_dates[e["id"]]) for e in events]
    contexts = rows(work / "contexts.jsonl")
    source = rows(work / "assertions.jsonl")
    maps = {
        v: read(work / ("provenance_v" + str(v) + ".json"))
        for v in sorted({c["volume"] for c in contexts})
    }
    approvals = read(work / "public_context_approvals.json")
    contexts, loci = project_contexts(
        contexts,
        maps,
        quantities=source,
        events=events,
        approvals=approvals,
        bindings=load_bindings(work),
    )
    projection = validate_projection(contexts, loci, source, events)
    result = write_catalogue(
        output,
        source,
        rows(public / "reviewed_assertions.jsonl"),
        contexts,
        events,
        rows(public / "date_claims.jsonl"),
        rows(public / "derivations.jsonl"),
        rows(public / "series_groups.jsonl"),
        public_sources(),
        read(revisions),
        dict(
            coverage=read(public / "summary.json")["inspection"],
            interpretation_basis="Explicit source labels and units; no modern epochs inferred.",
        ),
        loci=loci,
    )
    checked_hashes(REPO, read(work / checkpoint["last_verified"]["artifact_snapshot"]))
    write_json_atomic(
        work / "recovery/public-context-projection-verification.json",
        dict(
            projection,
            catalogue_manifest=result,
            approval_sha256=digest(work / "public_context_approvals.json"),
            source_numeric_changes=0,
            public_release_complete=False,
        ),
    )
    return result


def release_metadata(workspace, draft):
    work = Path(workspace)
    proof = json.loads(
        (work / "recovery/canonical-public-projection-verification.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = json.loads((Path(draft) / "manifest.json").read_text(encoding="utf-8"))
    if (
        proof.get("output_hashes") != manifest["output_hashes"]
        or not proof.get("ready_for_public_packaging")
        or not proof.get("repeat_artifacts_identical")
        or not proof.get("all_original_quantities_and_normalizations_preserved")
        or not proof.get("all_qualified_context_identities_preserved")
        or proof.get("foreign_keys") != "passed"
        or proof.get("field_audit", {}).get("matches") != {}
    ):
        raise ValueError("Finish verification of this draft before creating its public release")
    checkpoint = json.loads((work / "recovery_checkpoint.json").read_text(encoding="utf-8"))[
        "last_verified"
    ]
    screening = json.loads(
        (work / "recovery/full-source-reference-screening-audit.json").read_text(encoding="utf-8")
    )
    from .catalog_files import working_files

    database, _ = working_files(draft)
    with closing(
        sqlite3.connect((Path(draft).resolve() / database).as_uri() + "?mode=ro", uri=True)
    ) as db:
        inspection = json.loads(
            db.execute("SELECT value_json FROM metadata WHERE key='coverage'").fetchone()[0]
        )
        unclassified = db.execute(
            "SELECT COUNT(*) FROM catalogue WHERE quantity='unclassified_angle'"
        ).fetchone()[0]
    return dict(
        coverage=dict(
            source_lines_audited=sum(v["screened_lines"] for v in screening["volumes"]),
            selected_regions=checkpoint["candidate_regions"],
            reviewed_regions=checkpoint["inspected_regions"],
            inspected_source_lines=inspection["inspected_source_lines"],
        ),
        normalization_counts=proof["derived_normalizations"],
        source_reference_screening=dict(
            status=screening["status"],
            explicit_reference_lines=sum(
                v["explicit_reference_lines"] for v in screening["volumes"]
            ),
            limit="Explicit-reference screening does not prove completeness of implicit references.",
        ),
        counting_units=dict(
            quantity="One source quantity, including clocks, calibrations and calculations.",
            group="A source association, not an independent observation or accepted simultaneous event.",
        ),
        limitations=[
            "Recorded dates and contextual clocks are not accepted absolute timestamps.",
            f"{unclassified} angular quantities retain unresolved measurement types.",
            "Incomplete and unsupported expressions remain without invented numerical components.",
            "Historical corrections and calculated parallaxes do not establish modern accuracy or detections.",
            "Some contextual locations have only provisional page claims or an unknown physical page.",
        ],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default="work/mars-catalogue")
    parser.add_argument("--output", default="work/mars-catalogue/canonical")
    parser.add_argument("--interpretations")
    parser.add_argument("--release-directory")
    parser.add_argument("--release-id", help="Versioned catalogue identity for promotion")
    args = parser.parse_args()
    from .checkout import require_checkout

    require_checkout(parser)
    if args.release_directory:
        if not args.release_id:
            parser.error("--release-id is required when promoting a catalogue")
        result = promote_catalogue(
            args.output,
            args.release_directory,
            args.release_id,
            release_metadata(args.workspace, args.output),
        )
    else:
        if not args.interpretations:
            parser.error("--interpretations is required when building a draft")
        result = build_release(args.workspace, args.output, args.interpretations)
    print(encoded(result))


if __name__ == "__main__":
    main()
