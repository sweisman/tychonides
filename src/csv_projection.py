"""Canonical spreadsheet representation of selected database interpretations."""

from fractions import Fraction
import json
import sqlite3


def project_csv(db, columns):
    db.row_factory = sqlite3.Row
    dates = dict(db.execute("SELECT id,data_json FROM dates"))
    sources = {
        r["id"]: json.loads(r["data_json"]) for r in db.execute("SELECT id,data_json FROM sources")
    }
    quantities = {r["id"]: dict(r) for r in db.execute("SELECT * FROM quantities")}
    interpretations = {
        (r["quantity_id"], r["version"]): dict(r)
        for r in db.execute("SELECT * FROM interpretations")
    }
    for row in db.execute("SELECT * FROM catalogue ORDER BY id"):
        row = dict(row)
        q = quantities[row["id"]]
        i = interpretations[row["id"], row["version"]]
        original = json.loads(q["original_json"])
        norm = json.loads(i["normalized_json"])
        result = dict(q, **{k: v for k, v in row.items() if k not in q})
        result.update(row)
        result.update(
            interpretation_version=row["version"],
            original_quantity=original["quantity"],
            original_subject=original["subject"],
            original_normalization_status=original["normalized"]["status"],
            direction=original.get("direction"),
            record_status=original.get("record_status"),
            flags_json=i["flags_json"],
            components_json=i["components_json"],
            normalized_json=i["normalized_json"],
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
            result["source_url"] = source.get("translation_pdf") or source.get("url")
        yield {key: result.get(key) for key in columns}


def same_cell(key, actual, expected):
    if key.endswith("_json"):
        try:
            return json.loads(actual) == json.loads(expected)
        except (ValueError, TypeError):
            return False
    return actual == ("" if expected is None else str(expected))
