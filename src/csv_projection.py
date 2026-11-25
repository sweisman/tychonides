"""Canonical spreadsheet representation of selected database interpretations."""

from fractions import Fraction
import json
import sqlite3


def project_csv(db, columns, *, identifier=None):
    db.row_factory = sqlite3.Row
    dates = dict(db.execute("SELECT id,data_json FROM dates"))
    sources = {
        r["id"]: json.loads(r["data_json"]) for r in db.execute("SELECT id,data_json FROM sources")
    }
    query = """
        SELECT c.*, q.original_json, q.uncertainty_json, q.scientific_metadata_json,
               i.flags_json, i.components_json, i.normalized_json, i.revision_json
        FROM catalogue c JOIN quantities q ON q.id=c.id
        JOIN interpretations i ON i.quantity_id=c.id AND i.version=c.version
    """
    rows = (
        db.execute(query + " ORDER BY c.id")
        if identifier is None
        else db.execute(query + " WHERE c.id=?", (identifier,))
    )
    for row in rows:
        row = dict(row)
        original = json.loads(row["original_json"])
        norm = json.loads(row["normalized_json"])
        revision = json.loads(row["revision_json"] or "{}")
        direction = original.get("direction")
        if revision.get("kind") == "log_reading_interpretation":
            direction = revision.get("direction")
            metadata = json.loads(row["scientific_metadata_json"])
            metadata["interpretation_review"] = revision
            row["scientific_metadata_json"] = json.dumps(
                metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
        row.update(
            interpretation_version=row["version"],
            original_quantity=original["quantity"],
            original_subject=original["subject"],
            original_normalization_status=original["normalized"]["status"],
            direction=direction,
            record_status=original.get("record_status"),
            value_decimal=float(Fraction(row["value_exact"]))
            if row["value_exact"] is not None
            else None,
            value_degrees_decimal=float(Fraction(norm["magnitude_degrees"]))
            if norm.get("magnitude_degrees") is not None
            else None,
            date_claims_json=json.dumps(
                [json.loads(dates[d]) for d in original.get("source_date_claim_ids", [])],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
        if "source_url" not in row:
            source = sources[row["source_id"]]
            row["source_url"] = source.get("translation_pdf") or source.get("url")
        yield {key: row.get(key) for key in columns}


def same_cell(key, actual, expected):
    if key.endswith("_json"):
        try:
            return json.loads(actual) == json.loads(expected)
        except (ValueError, TypeError):
            return False
    return actual == ("" if expected is None else str(expected))
