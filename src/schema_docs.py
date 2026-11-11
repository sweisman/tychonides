"""Generate and verify the database reference from the released schema."""

import argparse
import gzip
from contextlib import closing, contextmanager
from importlib.resources import files
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
from .vocabulary import validate_vocabulary

TABLES = {
    "metadata": "Release-level metadata, limitations and license scope.",
    "sources": "Bibliographic source registry; publication dates are distinguished from access dates.",
    "artifacts": "Source-file identities and checksums. Public content is null; source documents are not bundled.",
    "groups": "Source observing or calculation groups; membership does not establish independence or simultaneity.",
    "quantities": "Preserved source expressions and source-scoped identities.",
    "images": "Externally hosted image-version metadata; no image pixels or local paths.",
    "interpretations": "Original and explicitly revised interpretations; highest version is current.",
    "contexts": "Source qualifications keyed by context identity and review scope.",
    "quantity_contexts": "Links quantities to qualified contexts.",
    "group_contexts": "Links groups to qualified contexts.",
    "source_loci": "Public source locations, including provisional or unknown-page qualifications.",
    "locus_quantities": "Links source locations to quantities.",
    "locus_contexts": "Links source locations to qualified contexts.",
    "dates": "Recorded date claims, without inventing accepted absolute epochs.",
    "quantity_dates": "Links quantities to recorded date claims.",
    "group_dates": "Links groups to recorded date claims.",
    "series": "Source associations of repeated readings.",
    "series_quantities": "Links quantities to their source series.",
    "derivations": "Source-reported calculations and independently recorded arithmetic checks.",
    "derivation_inputs": "Ordered input quantities for identified calculations.",
    "control_links": "Links Pafko control identities to quantities; not a second observing program.",
    "quantity_links": "Typed links between quantities, including alternatives and source relationships.",
    "derived_values": "Existing exact conversions exposed as typed fields; original interpretations remain unchanged.",
    "source_lines": "One literal fixed-width line per source, artifact version and locator.",
    "quantity_citations": "Source-file links and explicitly supported page/line locations.",
    "catalogue": "Current interpretation plus usable derived conversions and citations.",
    "source_records": "Original payloads, reconstructing raw_line from source_lines without duplication.",
    "diagrams": "Contexts whose kind is source_diagram.",
}
COLUMNS = {
    "key": "Metadata key.",
    "value_json": "JSON value or source qualification.",
    "id": "Stable identity in this table; links use the indicated foreign keys.",
    "author": "Author or responsible institution, distinct from the observing individual.",
    "work_id": "Bibliographic work identifier, when established.",
    "edition_id": "Edition identifier, when established.",
    "title": "Source title.",
    "volume": "Dreyer Opera Omnia volume for historical records; null for other collections.",
    "data_json": "Additional structured source or relationship metadata.",
    "source_id": "Source registry identity.",
    "sha256": "SHA-256 of the original artifact or image bytes.",
    "media_type": "Media type when established.",
    "retrieved_at": "Recorded acquisition time.",
    "redistribution_status": "Whether source bytes are included and how source terms apply.",
    "content": "Source-file bytes; null in public releases.",
    "metadata_json": "Structured metadata for this artifact or image.",
    "clock_quantity_id": "Linked observing clock quantity, if explicitly associated.",
    "epoch_quantity_id": "Linked calculation epoch quantity; not a substitute for an observing clock.",
    "printed_page": "Printed bibliographic page, not automatically a PDF image index.",
    "expression": "Literal source numeric expression.",
    "role": "Evidential role; see the quantity and role reference.",
    "event_id": "Associated source group.",
    "series_id": "Associated source series.",
    "original_json": "Original interpretation payload; shared fixed-width lines live in source_lines.",
    "components_json": "Exact original sexagesimal components or explicit null.",
    "uncertainty_json": "Stated uncertainty and qualifications; missing values are not zero.",
    "artifact_sha256": "Checksum identifying the source-file version.",
    "source_entry_id": "Original source-local entry identifier.",
    "locator": "Source-native row, line, page or frame locator.",
    "scientific_metadata_json": "Timing, reference-frame, correction and other scientific metadata.",
    "source_payload_json": "Native source payload; source_records reconstructs its raw_line where applicable.",
    "frame_id": "Archive frame identifier.",
    "version_id": "Archive image-version identifier.",
    "archive_md5": "MD5 supplied by the image archive.",
    "bytes": "Verified external image byte count.",
    "public_url": "Public archive link.",
    "quantity_id": "Linked quantity identity.",
    "version": "Interpretation version; zero preserves the initial interpretation.",
    "quantity": "Quantity type; see the quantity and role reference.",
    "subject": "Measured or calculated object.",
    "reference_object": "Other endpoint or comparison object, if recorded.",
    "status": "Normalization status: exact, incomplete, unsupported or source_expression.",
    "unit": "Unit or encoded source notation; modern notation formats are documented separately.",
    "value_exact": "Original normalized scalar as a rational string. Historical magnitudes are unsigned; native modern scalars retain source signs.",
    "signed_value_exact": "Explicit signed historical normalization, when established.",
    "normalized_json": "Full preserved normalization payload.",
    "flags_json": "Structured quality and interpretation flags.",
    "revision_json": "Evidence for an explicitly versioned interpretation change.",
    "context_id": "Context identity, always interpreted together with scope_id.",
    "scope_id": "Opaque review-scope identifier; prevents unrelated contexts with the same ID from merging.",
    "kind": "Source-context or relationship type.",
    "locator_json": "Structured source locator.",
    "locus_id": "Public source-location identity.",
    "date_id": "Recorded date-claim identity.",
    "group_id": "Source group identity.",
    "output_quantity_id": "Calculation output quantity.",
    "derivation_id": "Source calculation identity.",
    "ordinal": "Input position in the ordered calculation.",
    "control_id": "Pafko workbook control identity.",
    "from_id": "Originating quantity.",
    "to_id": "Related quantity.",
    "publisher": "Publishing or distributing institution.",
    "date": "Citation date qualified by date_kind; not necessarily the date of observation or publication.",
    "date_kind": "publication_date, publication_year, original_publication_year (the underlying edition rather than its translation), updated_date, source_filename_date, generated_date, accessed or catalogue_record_date.",
    "raw_line": "Exact source-file line, stored once for its artifact version and locator.",
    "source_url": "Original public source-file URL.",
    "source_page_url": "Deep link supported by explicit PDF index or archive page metadata; null when unverified.",
    "source_line_number": "One-based source-file line number where explicitly stated by the locator.",
    "derived_value_exact": "Unsigned magnitude of an existing modern conversion or scalar, as an exact rational string.",
    "derived_signed_value_exact": "The same value retaining its recorded or converted sign.",
    "derived_unit": "Physical unit of the exposed conversion; separate from its encoded input notation.",
    "derived_value_decimal": "Floating-point convenience for derived_value_exact.",
    "derived_signed_value_decimal": "Floating-point convenience for derived_signed_value_exact.",
    "derived_method": "Recorded conversion method, or source_scalar for a value already in physical units.",
    "derived_time_scale": "Explicit time convention of the result; UT is not silently made UTC or UT1.",
    "derived_timestamp": "Existing derived timestamp, with conversion method; not inferred for undated historical clocks.",
}


@contextmanager
def open_database(path):
    path = Path(path).resolve()
    with tempfile.TemporaryDirectory(prefix="tychonides-schema-") as temporary:
        if path.suffix == ".gz":
            expanded = Path(temporary) / "catalogue.sqlite"
            with gzip.open(path, "rb") as incoming, expanded.open("wb") as outgoing:
                shutil.copyfileobj(incoming, outgoing)
            path = expanded
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            yield db


def vocabulary():
    return json.loads(
        files(__package__).joinpath("data/modern_vocabulary.json").read_text(encoding="utf-8")
    )


def render(db):
    lines = [
        "# Database schema reference",
        "",
        "Schema version 5. Exact values are rational strings; SQL null means unknown or inapplicable, never zero.",
        "JSON preserves structured qualifications. Foreign keys below identify relationship targets.",
        "See the [historical terms](historical-data-dictionary.md), [modern terms](modern-data-dictionary.md) and [normalization conventions](normalization-conventions.md).",
        "",
    ]
    for name, _kind in db.execute(
        "SELECT name,type FROM sqlite_master WHERE type IN ('table','view') ORDER BY name"
    ):
        if name not in TABLES:
            raise ValueError("Undocumented database object: " + name)
        lines += [
            "## " + name,
            "",
            TABLES[name],
            "",
            "| Column | SQL type | Key / relationship | Meaning |",
            "| --- | --- | --- | --- |",
        ]
        links = {
            r[3]: r[2] + "." + str(r[4])
            for r in db.execute("PRAGMA foreign_key_list(" + name + ")")
        }
        for _, column, sqltype, _notnull, _default, pk in db.execute(
            "PRAGMA table_info(" + name + ")"
        ):
            if column not in COLUMNS:
                raise ValueError("Undocumented column: " + name + "." + column)
            relation = ("PK " + str(pk) + "; " if pk else "") + links.get(column, "")
            meaning = COLUMNS[column]
            if name == "source_loci" and column == "status":
                meaning = "Source-location status, such as reviewed_quantity_citation or automatic_page_index; not a numerical normalization status."
            lines.append(
                f"| `{name}.{column}` | {sqltype or 'derived'} | {relation or '—'} | {meaning} |"
            )
        lines += [""]
    from .catalog_indexes import INDEXES

    lines += [
        "## Query indexes",
        "",
        "Primary and unique keys cover forward links. These additional indexes support common filters and reverse traversal without changing any values.",
        "",
        "| Index | Table and ordered columns |",
        "| --- | --- |",
    ]
    lines += [
        f"| `{name}` | `{table} ({', '.join(columns)})` |"
        for name, (table, columns) in INDEXES.items()
    ]
    lines += [
        "",
        "Context lookups retain both `context_id` and `scope_id`; equal labels from different source reviews cannot be merged. Filter current coordinates through the `catalogue` view. SQLite chooses indexes according to the query and data; no elapsed-time guarantee is implied.",
        "",
    ]
    return "\n".join(lines)


def validate_schema_docs(db, root):
    text = (Path(root) / "docs/database-schema.md").read_text(encoding="utf-8")
    for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')"):
        for column in db.execute("PRAGMA table_info(" + name + ")"):
            if "`" + name + "." + column[1] + "`" not in text:
                raise ValueError("Database documentation omits " + name + "." + column[1])
    validate_vocabulary(db, root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("--output", type=Path, default=Path("docs/database-schema.md"))
    args = parser.parse_args()
    with open_database(args.database) as db:
        text = render(db)
    args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
