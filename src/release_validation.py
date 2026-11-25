"""Validate a downloaded release without private extraction inputs."""

import argparse
from contextlib import closing
import csv
from fractions import Fraction
import gzip
import os
import shutil
import tempfile
import json
from pathlib import Path
import re
import sqlite3
import tomllib
from urllib.parse import unquote, urlsplit

from .catalog_release import CSV_COLUMNS
from .catalog_enrichment import PUBLIC_CSV_COLUMNS
from .core import digest
from .catalog_files import catalog_files
from .csv_projection import project_csv, same_cell


def validate_derived_values(db, schema):
    from .catalog_enrichment import derived_fields
    from .numeric_integrity import (
        JPL_COORDINATE_BOUNDS,
        JPL_COORDINATE_FLAGS,
        jpl_coordinate_issue,
        validate_conversion,
    )

    query = """
        SELECT c.*, q.source_payload_json, i.flags_json
        FROM catalogue c JOIN quantities q ON q.id=c.id
        JOIN interpretations i ON i.quantity_id=c.id AND i.version=c.version
    """
    if schema >= 6:
        query += """
            LEFT JOIN source_lines l USING(source_id,artifact_sha256,locator)
        """
        query = query.replace("i.flags_json", "i.flags_json, l.raw_line", 1)
    query += """ WHERE q.source_payload_json IS NOT NULL
                 OR (q.source_id GLOB 'jpl-*' AND
                    (q.source_entry_id GLOB '*:declination' OR
                     q.source_entry_id GLOB '*:right_ascension'))"""
    for row in db.execute(query):
        identifier = row["id"]
        payload = json.loads(row["source_payload_json"] or "{}")
        if schema >= 6 and row["source_id"].startswith("jpl-"):
            quantity = row["source_entry_id"].rsplit(":", 1)[-1]
            unit = {
                "declination": "signed_ddmmss_centisecond",
                "right_ascension": "hhmmss_millisecond",
            }.get(quantity)
            if unit is not None:
                start, end = JPL_COORDINATE_BOUNDS[unit]
                literal = (row["raw_line"] or "")[start:end]
                if (
                    not literal.strip()
                    or row["expression"] != literal
                    or payload.get("literal") != literal
                    or payload.get("source_id") != row["source_id"]
                    or payload.get("unit") != unit
                    or row["unit"] != unit
                    or row["quantity"] != quantity
                    or row["value_exact"] is not None
                    or row["signed_value_exact"] is not None
                    or payload.get("normalized", {}).get("magnitude") is not None
                ):
                    raise ValueError("JPL coordinate differs from native field: " + identifier)
                issue = jpl_coordinate_issue(row["source_id"], unit, literal)
                flags = JPL_COORDINATE_FLAGS.intersection(json.loads(row["flags_json"]))
                if flags != ({issue} if issue else set()):
                    raise ValueError("JPL published flags differ from native field: " + identifier)
        if schema >= 5:
            validate_conversion(payload, legacy_jpl=schema == 5)
        expected = derived_fields(payload)
        if any(row[key] != value for key, value in expected.items()):
            raise ValueError("Derived columns differ from preserved conversion: " + identifier)


MODERN_SOURCE_PREFIXES = ("cds", "jjmo", "jpl", "usno")
PUBLISHED_MANIFEST_FIELDS = (
    "schema_version",
    "vocabulary_contract",
    "index_contract",
    "sqlite_sha256",
    "groups",
    "sources",
    "images",
    "artifacts",
    "controls",
    "interpretations",
    "quantities_by_source",
)


def validate_marked_values(db):
    """Recompute exact historical values whose printed expression carries every unit mark.

    An expression qualifies when it binds completely and its finest marked unit is the
    interpretation's least component unit, so no other table cell contributes to the value.
    Returns the number of values recomputed.
    """
    from .core import number
    from .numeric_integrity import explicit_angular_components, explicit_postfix_clock_components

    scale = {
        "degree": 3600,
        "arcminute": 60,
        "arcsecond": 1,
        "hour": 3600,
        "minute": 60,
        "second": 1,
    }
    parsers = {
        "arcsecond": explicit_angular_components,
        "second_of_time": explicit_postfix_clock_components,
    }
    checked = 0
    for identifier, expression, unit, value, least in db.execute(
        """SELECT c.id, c.expression, c.unit, c.value_exact,
                  json_extract(i.normalized_json, '$.least_component_unit')
           FROM catalogue c JOIN quantities q ON q.id=c.id
           JOIN interpretations i ON i.quantity_id=c.id AND i.version=c.version
           WHERE q.source_payload_json IS NULL AND c.status='exact'
             AND c.unit IN ('arcsecond','second_of_time') AND c.value_exact IS NOT NULL"""
    ):
        parts = parsers[unit](expression or "")
        if parts is None or list(parts)[-1] != least:
            continue
        if Fraction(value) != sum(number(text) * scale[name] for name, text in parts.items()):
            raise ValueError("Exact value differs from its marked expression: " + identifier)
        checked += 1
    return checked


def scratch_directory(assets):
    """Unpack beside the assets when possible; the system temporary directory is often memory."""
    return assets if os.access(assets, os.W_OK) else None


def validate_csv(db, path, columns, count):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(columns):
            raise ValueError("CSV columns differ from the documented export contract")
        projected = iter(project_csv(db, columns))
        candidate = next(projected, None)
        seen = set()
        for row in reader:
            key = row["id"]
            if key in seen:
                raise ValueError("Duplicate or unknown CSV identity")
            seen.add(key)
            if candidate is not None and candidate["id"] == key:
                expected = candidate
                candidate = next(projected, None)
            else:
                # Accept existing exports presented in a different row order.
                expected = next(project_csv(db, columns, identifier=key), None)
                if expected is None:
                    raise ValueError("Duplicate or unknown CSV identity")
            for field in columns:
                if not same_cell(field, row[field], expected[field]):
                    raise ValueError("CSV/database value mismatch: " + key + ":" + field)
    if len(seen) != count or count != db.execute("SELECT count(*) FROM catalogue").fetchone()[0]:
        raise ValueError("Release quantity counts or identities differ")


def validate_release(directory, assets_dir=None, keep_database=None):
    """Verify a release. A compressed database is unpacked once and kept at keep_database if given."""
    directory = Path(directory).resolve()
    assets = Path(assets_dir).resolve() if assets_dir is not None else directory
    if (directory / ".pending-release").exists():
        raise ValueError("Release promotion is incomplete; recover before verification")
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object")
    if not isinstance(manifest.get("output_hashes"), dict):
        raise ValueError("Manifest requires an output_hashes object")
    if type(manifest.get("quantities")) is not int or manifest["quantities"] < 0:
        raise ValueError("Manifest requires a nonnegative integer quantities count")
    # Optional manifest fields skip their checks. Each skipped check is reported.
    skipped = ["schema_version"] if "schema_version" not in manifest else []
    schema = manifest.get("schema_version", 3)
    if schema not in (3, 4, 5, 6):
        raise ValueError("Unsupported catalogue schema version")
    database_name, csv_name = catalog_files(manifest)
    compressed = database_name.endswith(".gz")
    if compressed and not re.fullmatch(r"[0-9a-f]{64}", str(manifest.get("sqlite_sha256", ""))):
        raise ValueError("Compressed manifest requires a valid sqlite_sha256 checksum")
    if "download_urls" in manifest:
        expected_urls = {
            name: f"https://github.com/sweisman/tychonides/releases/download/{manifest.get('release_id')}/{name}"
            for name in manifest["output_hashes"]
        }
        if manifest["download_urls"] != expected_urls:
            raise ValueError("Manifest download_urls must match its release_id and file names")
    for name, expected in manifest["output_hashes"].items():
        if not re.fullmatch(r"[0-9a-f]{64}", str(expected)):
            raise ValueError("Invalid SHA-256 checksum for " + name)
        if not (assets / name).is_file():
            raise ValueError("Missing release file: " + name)
        if digest(assets / name) != expected:
            raise ValueError("Release checksum mismatch: " + name)
    recomputed = None
    with tempfile.TemporaryDirectory(
        prefix=".tychonides-verify-", dir=scratch_directory(assets)
    ) as temporary:
        database = assets / database_name
        if compressed:
            database = Path(temporary) / "tychonides.sqlite"
            with (
                gzip.open(assets / database_name, "rb") as incoming,
                database.open("wb") as outgoing,
            ):
                shutil.copyfileobj(incoming, outgoing)
            if digest(database) != manifest["sqlite_sha256"]:
                raise ValueError("Uncompressed database checksum mismatch")
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
            if manifest.get("vocabulary_contract") == 1:
                from .vocabulary import validate_vocabulary

                validate_vocabulary(db)
            else:
                skipped.append("vocabulary_contract")
            if manifest.get("index_contract") == 1:
                from .catalog_indexes import validate_indexes

                validate_indexes(db)
            else:
                skipped.append("index_contract")
            if (
                db.execute("PRAGMA integrity_check").fetchone()[0] != "ok"
                or db.execute("PRAGMA foreign_key_check").fetchall()
            ):
                raise ValueError("Database integrity or relationship failure")
            db.row_factory = sqlite3.Row
            if schema >= 4:
                validate_derived_values(db, schema)
                if db.execute(
                    "SELECT count(*) FROM sources WHERE title IS NULL OR author IS NULL OR publisher IS NULL OR date IS NULL OR date_kind IS NULL"
                ).fetchone()[0]:
                    raise ValueError("Source bibliography is incomplete")
            if schema >= 6:
                recomputed = validate_marked_values(db)
            columns = PUBLIC_CSV_COLUMNS if schema >= 4 else CSV_COLUMNS
            if schema >= 5:
                columns += ("normalized_json",)
            for key, table in (
                ("groups", "groups"),
                ("sources", "sources"),
                ("images", "images"),
                ("artifacts", "artifacts"),
                ("controls", "control_links"),
                ("interpretations", "interpretations"),
            ):
                if key not in manifest:
                    skipped.append(key)
                elif manifest[key] != db.execute("SELECT count(*) FROM " + table).fetchone()[0]:
                    raise ValueError("Manifest count differs: " + key)
            if "quantities_by_source" not in manifest:
                skipped.append("quantities_by_source")
            elif manifest["quantities_by_source"] != dict(
                db.execute("SELECT source_id,count(*) FROM quantities GROUP BY source_id")
            ):
                raise ValueError("Manifest counts differ: quantities_by_source")
            validate_csv(db, assets / csv_name, columns, manifest["quantities"])
        if compressed and keep_database is not None:
            kept = Path(keep_database).resolve()
            kept.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(database, kept)
    return {
        "release_id": manifest.get("release_id"),
        "quantities": manifest["quantities"],
        "status": "verified",
        "marked_values_recomputed": recomputed,
        "skipped_checks": skipped,
    }


def validate_documentation(root):
    root = Path(root)
    dictionary = (root / "docs/catalog-data-dictionary.md").read_text(encoding="utf-8")
    missing = [field for field in PUBLIC_CSV_COLUMNS if "`" + field + "`" not in dictionary]
    if missing:
        raise ValueError("Undocumented CSV fields: " + ", ".join(missing))
    from .vocabulary import validate_reference_pages

    validate_reference_pages(root)
    validate_release_references(root)
    validate_documented_totals(root)
    pages = [
        root / "README.md",
        root / "resources/catalog/README.md",
        *sorted((root / "docs").glob("*.md")),
    ]
    validate_links(pages)


def validate_links(pages):
    """Require every local link to reach a file and, in Markdown, an existing heading."""
    for page in pages:
        for target in re.findall(r"\]\(([^\s)]+)\)", page.read_text(encoding="utf-8")):
            link = urlsplit(target)
            if link.scheme or link.netloc:
                continue
            linked = page.parent / unquote(link.path) if link.path else page
            if not linked.exists():
                raise ValueError("Broken local documentation link: " + str(page) + ": " + target)
            if linked.is_dir():
                linked = linked / "README.md"
            if (
                link.fragment
                and linked.suffix == ".md"
                and linked.is_file()
                and unquote(link.fragment)
                not in heading_anchors(linked.read_text(encoding="utf-8"))
            ):
                raise ValueError("Broken documentation anchor: " + str(page) + ": " + target)


def heading_anchors(text):
    """Anchors the website generates for a page's headings, plus explicit ones."""
    text = re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)
    anchors, seen = set(re.findall(r"<a\s+(?:id|name)=\"([^\"]+)\"", text)), {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.M):
        label = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
        label = re.sub(r"(?<!\w)[*_]+|[*_]+(?!\w)|`", "", label)
        label = re.sub(r"[^\w\- ]", "", label.strip().lower()).replace(" ", "-")
        count = seen.get(label, 0)
        anchors.add(f"{label}-{count}" if count else label)
        seen[label] = count + 1
    return anchors


def validate_documented_totals(root):
    catalog = root / "resources/catalog"
    manifest = json.loads((catalog / "manifest.json").read_text(encoding="utf-8"))
    guide = (catalog / "README.md").read_text(encoding="utf-8")
    headline = f"**{manifest['quantities']:,} quantities and {manifest['groups']:,} source groups**"
    if headline not in guide:
        raise ValueError("Catalog guide totals differ from the manifest")
    sources = manifest.get("quantities_by_source", {})
    logs = sum(count for name, count in sources.items() if name.startswith("tycho-oo-"))
    modern = sum(
        count for name, count in sources.items() if name.split("-")[0] in MODERN_SOURCE_PREFIXES
    )
    books = manifest["quantities"] - logs - modern
    directory = (root / "docs/data-sources.md").read_text(encoding="utf-8")
    for statement in (
        f"**{manifest['quantities']:,} quantities**",
        f"**{logs:,}** |",
        f"contribute {books:,} quantities",
        f"contain **{modern:,} quantities**",
    ):
        if statement not in directory:
            raise ValueError("Source directory totals differ from the manifest: " + statement)

    pafko = json.loads((catalog / "pafko-validation.json").read_text(encoding="utf-8"))
    count = pafko["workbook_rows"]
    if count != manifest["controls"] or any(
        sum(pafko[key].values()) != count for key in ("baseline", "replay", "source_checks")
    ):
        raise ValueError("Pafko totals differ from the control count")
    baseline = pafko["baseline"]
    agreements = baseline["magnitude_agreement"] + baseline["exact"]
    total = f"| Total | {count} | {agreements} | {baseline['disagreement']} | {baseline['unresolved']} |"
    page = (root / "docs/pafko-validation-status.md").read_text(encoding="utf-8")
    home = (root / "README.md").read_text(encoding="utf-8")
    if total not in page or any(
        token not in home
        for token in (
            f"**{count} workbook rows**",
            f"**{agreements}**",
            f"**{baseline['exact']}**",
            f"**{pafko['source_checks']['not_reviewed']}**",
        )
    ):
        raise ValueError("Documented Pafko counts differ from the reconciliation tally")


def validate_release_references(root):
    """Reject a partially updated release in the current source checkout."""
    root = Path(root)
    manifest = json.loads((root / "resources/catalog/manifest.json").read_text(encoding="utf-8"))
    release_id = manifest["release_id"]
    missing = [field for field in PUBLISHED_MANIFEST_FIELDS if field not in manifest]
    if missing:
        raise ValueError("Published manifest omits checked fields: " + ", ".join(missing))
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    if release_id != "tychonides-" + project["project"]["version"]:
        raise ValueError("Release version differs between manifest and pyproject.toml")
    citation = (root / "CITATION.cff").read_text(encoding="utf-8")
    versions = re.findall(r"^version: (.+)$", citation, re.M)
    if versions != [release_id]:
        raise ValueError("Release version differs in CITATION.cff")
    for name in ("resources/catalog/README.md", "docs/data-workflow.md"):
        versions = re.findall(
            r"\b(?:tychonides|mars)-\d+\.\d+\.\d+\b", (root / name).read_text(encoding="utf-8")
        )
        if not versions or any(value != release_id for value in versions):
            raise ValueError("Release version missing or inconsistent in " + name)
    expected = {
        name: f"https://github.com/sweisman/tychonides/releases/download/{release_id}/{name}"
        for name in manifest["output_hashes"]
    }
    if manifest.get("download_urls") != expected:
        raise ValueError("Release download URLs differ from manifest version")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--docs-root", type=Path)
    parser.add_argument(
        "--assets-dir", type=Path, help="Downloaded files, if separate from the manifest directory"
    )
    parser.add_argument(
        "--keep-database",
        type=Path,
        help="Keep the verified, decompressed database at this path",
    )
    args = parser.parse_args()
    assets = (args.assets_dir or args.directory).resolve()
    if args.keep_database and args.keep_database.exists():
        parser.error("--keep-database path already exists: " + str(args.keep_database))
    try:
        with tempfile.TemporaryDirectory(
            prefix=".tychonides-verify-", dir=scratch_directory(assets)
        ) as hold:
            # One decompression serves the release checks, the schema check, and the caller.
            unpacked = args.keep_database or Path(hold) / "tychonides.sqlite"
            result = validate_release(args.directory, args.assets_dir, keep_database=unpacked)
            if args.docs_root:
                validate_documentation(args.docs_root)
                manifest = json.loads(
                    (args.directory / "manifest.json").read_text(encoding="utf-8")
                )
                if manifest.get("schema_version", 3) >= 4:
                    from .schema_docs import open_database, validate_schema_docs

                    name, _ = catalog_files(manifest)
                    with open_database(unpacked if unpacked.is_file() else assets / name) as db:
                        validate_schema_docs(db, args.docs_root)
    except (ValueError, OSError, sqlite3.DatabaseError) as error:
        parser.error(str(error))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
