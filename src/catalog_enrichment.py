"""Explicit, versioned presentation of existing conversions and source citations."""

from fractions import Fraction
import json
import re

from .catalog_release import CSV_COLUMNS, encoded

DERIVED_COLUMNS = (
    "derived_value_exact",
    "derived_signed_value_exact",
    "derived_unit",
    "derived_value_decimal",
    "derived_signed_value_decimal",
    "derived_method",
    "derived_time_scale",
    "derived_timestamp",
)
PUBLIC_CSV_COLUMNS = CSV_COLUMNS + DERIVED_COLUMNS + ("source_page_url", "source_line_number")


def derived_fields(payload):
    """Expose a stored conversion; do not recompute astronomical corrections."""
    result = dict.fromkeys(DERIVED_COLUMNS)
    converted = payload.get("derived_normalization")
    if converted is None:
        converted = payload.get("normalized", {})
        method = "source_scalar"
    else:
        method = converted.get("method")
    magnitude = converted.get("magnitude")
    if magnitude is not None:
        value = Fraction(magnitude)
        result.update(
            derived_value_exact=str(abs(value)),
            derived_signed_value_exact=str(value),
            derived_value_decimal=float(abs(value)),
            derived_signed_value_decimal=float(value),
            derived_unit=converted.get("unit"),
            derived_method=method,
        )
    if converted.get("timestamp"):
        result.update(derived_timestamp=converted["timestamp"], derived_method=method)
    if magnitude is not None or converted.get("timestamp"):
        result["derived_time_scale"] = converted.get("time_scale") or (
            "UTC"
            if converted.get("method") == "source_EDT_UTC_minus_4"
            else payload.get("time_scale")
        )
    return result


def page_url(source, locator, printed_page=None):
    """Use only explicit PDF indices or verified publisher page mappings."""
    url = source.get("url") or source.get("translation_pdf")
    match = re.search(r"PDF page (\d+)", locator or "")
    if match and url and ".pdf" in url:
        return url.split("#")[0] + "#page=" + match[1]
    mapped = source.get("page_urls", {}).get(str(printed_page))
    return mapped


def enrich_catalogue(db, registry):
    db.executescript("""
    CREATE TABLE derived_values(
      quantity_id TEXT PRIMARY KEY REFERENCES quantities(id),
      derived_value_exact TEXT, derived_signed_value_exact TEXT, derived_unit TEXT,
      derived_value_decimal REAL, derived_signed_value_decimal REAL, derived_method TEXT,
      derived_time_scale TEXT, derived_timestamp TEXT);
    CREATE TABLE source_lines(
      source_id TEXT, artifact_sha256 TEXT, locator TEXT, raw_line TEXT NOT NULL,
      PRIMARY KEY(source_id,artifact_sha256,locator),
      FOREIGN KEY(source_id,artifact_sha256) REFERENCES artifacts(source_id,sha256));
    CREATE TABLE quantity_citations(
      quantity_id TEXT PRIMARY KEY REFERENCES quantities(id),
      source_url TEXT NOT NULL, source_page_url TEXT, source_line_number INTEGER, locator TEXT);
    ALTER TABLE sources ADD COLUMN publisher TEXT;
    ALTER TABLE sources ADD COLUMN date TEXT;
    ALTER TABLE sources ADD COLUMN date_kind TEXT;
    """)
    sources = {}
    for sid, data in db.execute("SELECT id,data_json FROM sources").fetchall():
        existing = json.loads(data)
        if sid not in registry:
            raise ValueError("Missing bibliographic metadata for source: " + sid)
        record = dict(existing, **registry[sid])
        for key in ("title", "author", "publisher", "date", "date_kind"):
            if not record.get(key):
                raise ValueError("Missing source citation field: " + sid + ":" + key)
        sources[sid] = record
        db.execute(
            "UPDATE sources SET title=?,author=?,publisher=?,date=?,date_kind=?,data_json=? WHERE id=?",
            (
                record["title"],
                record["author"],
                record["publisher"],
                record["date"],
                record["date_kind"],
                encoded(record),
                sid,
            ),
        )
    for row in db.execute(
        "SELECT id,source_id,artifact_sha256,locator,printed_page,original_json,scientific_metadata_json,source_payload_json FROM quantities"
    ).fetchall():
        identifier, sid, artifact, locator, printed_page, original, scientific, payload = row
        if payload:
            native = json.loads(payload)
            from .numeric_integrity import validate_conversion

            validate_conversion(native)
            values = derived_fields(native)
            db.execute(
                "INSERT INTO derived_values VALUES (?,?,?,?,?,?,?,?,?)",
                (identifier, *(values[k] for k in DERIVED_COLUMNS)),
            )
            raw = native.get("raw_line")
            if raw is not None:
                prior = db.execute(
                    "SELECT raw_line FROM source_lines WHERE source_id=? AND artifact_sha256=? AND locator=?",
                    (sid, artifact, locator),
                ).fetchone()
                if prior and prior[0] != raw:
                    raise ValueError("Conflicting original lines at one source locator")
                db.execute(
                    "INSERT OR IGNORE INTO source_lines VALUES (?,?,?,?)",
                    (sid, artifact, locator, raw),
                )
                for column, text in (
                    ("original_json", original),
                    ("scientific_metadata_json", scientific),
                    ("source_payload_json", payload),
                ):
                    data = json.loads(text)
                    data.pop("raw_line", None)
                    db.execute(
                        f"UPDATE quantities SET {column}=? WHERE id=?", (encoded(data), identifier)
                    )
        source = sources[sid]
        line = re.fullmatch(r"line (\d+)", locator or "")
        db.execute(
            "INSERT INTO quantity_citations VALUES (?,?,?,?,?)",
            (
                identifier,
                source.get("url") or source.get("translation_pdf"),
                page_url(source, locator, printed_page),
                int(line[1]) if line else None,
                locator,
            ),
        )
    db.executescript("""
    DROP VIEW catalogue;
    CREATE VIEW catalogue AS SELECT q.id,q.source_id,q.artifact_sha256,q.source_entry_id,q.locator,
      q.volume,q.printed_page,q.expression,q.role,q.event_id,q.series_id,
      i.version,i.quantity,i.subject,i.reference_object,i.status,i.unit,i.value_exact,i.signed_value_exact,
      d.derived_value_exact,d.derived_signed_value_exact,d.derived_unit,
      d.derived_value_decimal,d.derived_signed_value_decimal,d.derived_method,
      d.derived_time_scale,d.derived_timestamp,c.source_url,c.source_page_url,c.source_line_number
      FROM quantities q JOIN interpretations i ON i.quantity_id=q.id
      LEFT JOIN derived_values d ON d.quantity_id=q.id
      JOIN quantity_citations c ON c.quantity_id=q.id
      WHERE i.version=(SELECT MAX(j.version) FROM interpretations j WHERE j.quantity_id=q.id);
    DROP VIEW source_records;
    CREATE VIEW source_records AS SELECT q.id,q.source_id,q.artifact_sha256,q.source_entry_id,
      q.expression,q.components_json,
      CASE WHEN l.raw_line IS NOT NULL THEN json_set(q.source_payload_json,'$.raw_line',l.raw_line)
           ELSE COALESCE(q.source_payload_json,q.original_json) END AS source_payload_json
      FROM quantities q LEFT JOIN source_lines l USING(source_id,artifact_sha256,locator);
    """)
    db.execute("INSERT OR REPLACE INTO metadata VALUES ('schema_version','4')")


def load_registry():
    from importlib.resources import files

    return json.loads(
        files(__package__).joinpath("data/source_metadata.json").read_text(encoding="utf-8")
    )
