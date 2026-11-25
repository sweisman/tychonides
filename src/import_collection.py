"""Import source data or merge working catalogues in protected storage.

This command does not publish third-party artifacts or acquire image pixels.
"""

import argparse
import hashlib
from contextlib import closing
import csv
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile

from .catalog_release import adapt_source_quantities, encoded, write_catalogue
from .core import digest
from .recovery import write_json_atomic
from .release_transaction import publish
from .release_validation import validate_release

PROTECTED_ROOT = Path(__file__).resolve().parents[1] / "work/combined-catalogue"
WORK_ROOT = PROTECTED_ROOT.parent


def _identifier(name):
    return '"' + name.replace('"', '""') + '"'


def _reconciled_locus_claim(current, new):
    evidence_rank = {
        ("page_unestablished", None): 0,
        ("provisional_source_page", "automatic_page_index"): 1,
        ("mapped_source_page", "reviewed_quantity_citation"): 2,
    }
    claims = []
    identities = []
    for row in (current, new):
        identity = {
            k: v
            for k, v in row.items()
            if k not in {"quantity_ids", "context_ids", "printed_page", "status", "page_basis"}
        }
        page = row.get("printed_page")
        rank = evidence_rank.get((row["status"], row.get("page_basis")))
        if rank is None or (rank == 0) != (page is None):
            return None
        if page is not None and (type(page) is not int or page < 1):
            return None
        identities.append(identity)
        claims.append((rank, page, row["status"], row.get("page_basis")))
    known_pages = {page for _, page, _, _ in claims if page is not None}
    if identities[0] != identities[1] or len(known_pages) > 1:
        return None
    _, page, status, basis = max(claims, key=lambda claim: claim[0])
    return dict(identities[0], printed_page=page, status=status, page_basis=basis)


def _merge_locus_links(db):
    """Combine backlinks and retain the strongest evidence for an agreed page."""
    pairs = db.execute(
        "SELECT m.id, m.data_json, s.data_json, m.status, s.status, m.printed_page, s.printed_page "
        "FROM main.source_loci m JOIN incoming.source_loci s USING (id) "
        "WHERE m.data_json IS NOT s.data_json OR m.status IS NOT s.status "
        "OR m.printed_page IS NOT s.printed_page"
    ).fetchall()
    for (
        identifier,
        retained,
        incoming,
        retained_status,
        incoming_status,
        old_page,
        new_page,
    ) in pairs:
        current, new = json.loads(retained), json.loads(incoming)
        if (current["status"], new["status"]) != (retained_status, incoming_status) or (
            current["printed_page"],
            new["printed_page"],
        ) != (old_page, new_page):
            raise ValueError("Inconsistent source locus status: " + identifier)
        quantities = set(current.get("quantity_ids", [])) | set(new.get("quantity_ids", []))
        contexts = {
            (r["context_id"], r["scope_id"])
            for row in (current, new)
            for r in row.get("context_ids", [])
        }
        current = _reconciled_locus_claim(current, new)
        if current is None:
            raise ValueError("Conflicting source locus evidence: " + identifier)
        current["quantity_ids"] = sorted(quantities)
        current["context_ids"] = [
            dict(context_id=context, scope_id=scope) for context, scope in sorted(contexts)
        ]
        db.execute(
            "UPDATE main.source_loci SET data_json=?, status=?, printed_page=? WHERE id=?",
            (encoded(current), current["status"], current["printed_page"], identifier),
        )


def _merge_catalogue_rows(db):
    """Merge the attached input without replacing any conflicting identity."""

    def tables(alias):
        return [
            r[0]
            for r in db.execute(
                f"SELECT name FROM {alias}.sqlite_master WHERE type='table' "
                "AND name!='metadata' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]

    names = tables("main")
    if tables("incoming") != names:
        raise ValueError("Incompatible catalogue table schema")
    columns = {}
    for name in names:
        quoted = _identifier(name)
        info = list(db.execute(f"PRAGMA main.table_info({quoted})"))
        other = list(db.execute(f"PRAGMA incoming.table_info({quoted})"))
        if [r[1:] for r in other] != [r[1:] for r in info]:
            raise ValueError("Incompatible catalogue column schema: " + name)
        columns[name] = [r[1] for r in info]
        fields = ",".join(_identifier(c) for c in columns[name])
        keys = [r[1] for r in sorted(info, key=lambda r: r[5]) if r[5]]
        order = ",".join(_identifier(c) for c in keys or columns[name])
        db.execute(
            f"INSERT OR IGNORE INTO main.{quoted} ({fields}) "
            f"SELECT {fields} FROM incoming.{quoted} ORDER BY {order}"
        )
    _merge_locus_links(db)
    for name in names:
        quoted = _identifier(name)
        same = " AND ".join(
            f"m.{_identifier(c)} IS s.{_identifier(c)}"
            for c in columns[name]
            if name != "source_loci" or c not in ("data_json", "status", "printed_page")
        )
        if db.execute(
            f"SELECT 1 FROM incoming.{quoted} s WHERE NOT EXISTS "
            f"(SELECT 1 FROM main.{quoted} m WHERE {same}) LIMIT 1"
        ).fetchone():
            raise ValueError("Conflicting or missing input row in " + name)


def merge_catalogues(base, additional, output, *, repeat=False):
    """Combine two compatible working catalogues."""
    return merge_catalogue_set((base, additional), output, repeat=repeat)


def _apply_working_date_reviews(db, reviews):
    """Apply source-reviewed year bindings to the copied baseline only."""
    for previous, reviewed in reviews:
        changed = {
            key
            for key in previous.keys() | reviewed.keys()
            if previous.get(key) != reviewed.get(key)
        }
        if (
            previous.keys() != reviewed.keys()
            or "year" not in changed
            or not changed <= {"year", "component_status"}
            or reviewed.get("claim_basis") != "reviewed_source_context"
            or reviewed.get("calendar_validation") != "not_performed"
            or reviewed.get("accepted_observing_date") is not None
            or reviewed.get("absolute_timestamp") is not None
            or type(reviewed["year"]) is not int
            or not 1 <= reviewed["year"] <= 9999
            or reviewed["component_status"]
            != (
                "complete_named_components"
                if all(reviewed.get(key) is not None for key in ("year", "month", "day"))
                else "partial_named_components"
            )
        ):
            raise ValueError("Working date review must bind only the source year")
        updated = db.execute(
            "UPDATE dates SET data_json=? WHERE id=? AND data_json=?",
            (encoded(reviewed), previous["id"], encoded(previous)),
        ).rowcount
        if updated != 1:
            raise ValueError("Reviewed date does not match the frozen baseline: " + previous["id"])


def _apply_working_locus_reviews(db, reviews):
    for previous, reviewed in reviews:
        if (
            previous.get("status") != "provisional_source_page"
            or previous.keys() != reviewed.keys()
            or {k for k in previous if previous[k] != reviewed[k]} != {"printed_page"}
            or type(reviewed["printed_page"]) is not int
            or reviewed["printed_page"] < 1
        ):
            raise ValueError("Working locus review must replace only a provisional printed page")
        updated = db.execute(
            "UPDATE source_loci SET data_json=?, printed_page=? WHERE id=? AND data_json=?",
            (encoded(reviewed), reviewed["printed_page"], previous["id"], encoded(previous)),
        ).rowcount
        if updated != 1:
            raise ValueError("Reviewed source locus does not match the frozen baseline")


def merge_catalogue_set(
    inputs, output, *, repeat=False, reviewed_dates=(), reviewed_loci=(), verified_manifests=None
):
    """Combine working catalogue bundles in a single verified export."""
    from .catalog_files import working_files
    from .catalog_release import CSV_COLUMNS
    from .csv_projection import project_csv

    inputs = tuple(dict.fromkeys(Path(p).resolve() for p in inputs))
    if not inputs:
        raise ValueError("Merge requires at least one input catalogue")
    output = Path(output).resolve()
    if not output.is_relative_to(WORK_ROOT.resolve()):
        raise ValueError("Working catalogue merges require protected working storage")
    if any(p.is_relative_to(output) or output.is_relative_to(p) for p in inputs):
        raise ValueError("Merge output overlaps its read-only inputs")
    snapshots, fingerprints = [], {}
    reviewed_dates = tuple(reviewed_dates)
    reviewed_loci = tuple(reviewed_loci)
    verified_manifests = verified_manifests or {}
    for directory in inputs:
        manifest_path = directory / "manifest.json"
        manifest_hash = digest(manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if verified_manifests.get(directory) == manifest_hash:
            # The caller has already checked this exact manifest and its assets.
            for filename, checksum in manifest["output_hashes"].items():
                if digest(directory / filename) != checksum:
                    raise ValueError("Previously verified input changed: " + filename)
        else:
            validate_release(directory)
        if manifest.get("schema_version", 3) != 3:
            raise ValueError("Merge requires unprojected working catalogue schema 3")
        database, _csv_name = working_files(directory)
        snapshots.append(directory / database)
        fingerprints[manifest_path] = manifest_hash
        fingerprints.update(
            {directory / name: checksum for name, checksum in manifest["output_hashes"].items()}
        )
    output.mkdir(parents=True, exist_ok=True)

    def build(stage):
        stage.mkdir()
        shutil.copyfile(snapshots[0], stage / "tychonides.sqlite")
        with closing(sqlite3.connect((stage / "tychonides.sqlite").as_uri(), uri=True)) as db:
            db.execute("PRAGMA foreign_keys=OFF")
            metadata = dict(db.execute("SELECT key,value_json FROM main.metadata"))
            with db:
                _apply_working_date_reviews(db, reviewed_dates)
                _apply_working_locus_reviews(db, reviewed_loci)
            for database in snapshots[1:]:
                db.execute("ATTACH DATABASE ? AS incoming", (database.as_uri() + "?mode=ro",))
                with db:
                    _merge_catalogue_rows(db)
                    for key, value in db.execute("SELECT key,value_json FROM incoming.metadata"):
                        if key in ("schema_version", "release_id", "publication_status"):
                            continue
                        if key in metadata and json.loads(metadata[key]) != json.loads(value):
                            raise ValueError("Conflicting catalogue metadata: " + key)
                        metadata[key] = value
                db.execute("DETACH DATABASE incoming")
            with db:
                metadata.update(
                    schema_version=encoded(3),
                    release_id=encoded("combined-catalogue-draft"),
                    publication_status=encoded(
                        "internal_combined_catalogue_not_cleared_for_distribution"
                    ),
                )
                if "modern_quantities" in metadata:
                    metadata["modern_quantities"] = encoded(
                        db.execute(
                            "SELECT count(*) FROM quantities WHERE source_payload_json IS NOT NULL"
                        ).fetchone()[0]
                    )
                db.executemany(
                    "INSERT OR REPLACE INTO metadata VALUES (?,?)", sorted(metadata.items())
                )
                if db.execute("PRAGMA foreign_key_check").fetchall():
                    raise ValueError("Merged catalogue has broken relationships")
            counts = {
                key: db.execute(f"SELECT count(*) FROM {_identifier(table)}").fetchone()[0]
                for key, table in (
                    ("quantities", "quantities"),
                    ("groups", "groups"),
                    ("sources", "sources"),
                    ("images", "images"),
                    ("artifacts", "artifacts"),
                    ("controls", "control_links"),
                    ("interpretations", "interpretations"),
                )
            }
            per_source = dict(
                db.execute("SELECT source_id,count(*) FROM quantities GROUP BY source_id")
            )
            db.row_factory = sqlite3.Row
            with (stage / "tychonides.csv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                writer.writerows(project_csv(db, CSV_COLUMNS))
        manifest = dict(
            status="internal_combined_catalogue_not_cleared_for_distribution",
            schema_version=3,
            release_id="combined-catalogue-draft",
            **counts,
            quantities_by_source=per_source,
            output_hashes={
                name: digest(stage / name) for name in ("tychonides.sqlite", "tychonides.csv")
            },
        )
        write_json_atomic(stage / "manifest.json", manifest)
        validate_release(stage)
        return manifest

    with tempfile.TemporaryDirectory(prefix=".merge-", dir=output) as temporary:
        root = Path(temporary)
        manifest = build(root / "first")
        if repeat and build(root / "repeat")["output_hashes"] != manifest["output_hashes"]:
            raise ValueError("Repeated catalogue exports differ")
        if any(digest(path) != checksum for path, checksum in fingerprints.items()):
            raise ValueError("An input changed during merge")
        manifest["repeat_outputs_identical"] = repeat
        write_json_atomic(root / "first/manifest.json", manifest)
        publish(root / "first", output, manifest)
    return manifest


def connect_readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def read_collection(database, quantities):
    rows = [
        json.loads(line)
        for line in Path(quantities).read_text(encoding="utf-8").splitlines()
        if line
    ]
    exported = {(r["source_id"], r["artifact_sha256"], r["id"]): r for r in rows}
    if len(exported) != len(rows):
        raise ValueError("Duplicate exported source identity")
    with closing(connect_readonly(database)) as db:
        db.execute("BEGIN")
        if (
            db.execute("PRAGMA integrity_check").fetchone()[0] != "ok"
            or db.execute("PRAGMA foreign_key_check").fetchall()
        ):
            raise ValueError("Input store failed integrity checks")
        originals = list(
            db.execute("SELECT source,artifact,id,payload,magnitude,unit FROM quantities")
        )
        if len(originals) != len(rows):
            raise ValueError("Export does not cover the complete store")
        for sid, artifact, identifier, payload, magnitude, unit in originals:
            row = exported.get((sid, artifact, identifier))
            if row is None:
                raise ValueError("Export omits a source quantity")
            native = {
                k: v
                for k, v in row.items()
                if k not in ("source_id", "artifact_sha256", "normalized", "derived_normalization")
            }
            if native != json.loads(payload) or row["normalized"] != {
                "magnitude": magnitude,
                "unit": unit,
            }:
                raise ValueError("Export changed an original source payload or scalar")
            from .numeric_integrity import qualify_retained_conversion

            qualify_retained_conversion(row)
        sources = [
            dict(id=sid, url=url)
            for sid, url in db.execute("SELECT id,url FROM sources ORDER BY id")
        ]
        artifacts = []
        for sid, checksum, retrieved, content in db.execute(
            "SELECT * FROM artifacts ORDER BY source,sha256"
        ):
            if hashlib.sha256(content).hexdigest() != checksum:
                raise ValueError("Source artifact checksum mismatch")
            artifacts.append(
                dict(
                    source_id=sid,
                    sha256=checksum,
                    retrieved_at=retrieved,
                    content=content,
                    redistribution_status="not_cleared_for_public_export",
                )
            )
        images = []
        for frame, version, checksum, md5, path, size, metadata in db.execute(
            "SELECT * FROM images ORDER BY frame_id,version_id"
        ):
            # The local pixel location remains in the protected import only.
            images.append(
                dict(
                    source_id="lco-archive",
                    frame_id=str(frame),
                    version_id=str(version),
                    sha256=checksum,
                    archive_md5=md5,
                    bytes=size,
                    public_url=f"https://archive-api.lco.global/frames/{frame}/",
                    metadata=dict(json.loads(metadata), local_pixel_path=path),
                )
            )
        if images:
            sources.append(
                dict(
                    id="lco-archive",
                    url="https://archive.lco.global/",
                    title="Las Cumbres Observatory archive",
                )
            )
    source, public, groups = adapt_source_quantities(rows)
    return source, public, groups, sources, artifacts, images


def import_collection(database, quantities, base, output, overlaps=None):
    database, quantities, base, output = map(
        lambda p: Path(p).resolve(), (database, quantities, base, output)
    )
    protected = PROTECTED_ROOT
    if not output.is_relative_to(protected):
        raise ValueError(
            "Imports containing third-party artifacts require protected working storage"
        )
    if any(p.is_relative_to(output) for p in (database, quantities, base)):
        raise ValueError("Import output overlaps its read-only inputs")
    from .catalog_files import working_files

    base_database, base_csv = working_files(base)
    inputs = [database, quantities, base / base_database, base / base_csv, base / "manifest.json"]
    if overlaps:
        inputs.append(Path(overlaps).resolve())
    fingerprints = {str(p): digest(p) for p in inputs}
    validate_release(base)
    source, public, groups, sources, artifacts, images = read_collection(database, quantities)
    contexts = []
    if overlaps:
        candidates = json.loads(Path(overlaps).read_text(encoding="utf-8"))
        group_map = {
            (g["source_id"], g["artifact_sha256"], g["source_entry_id"]): g["id"] for g in groups
        }
        for index, candidate in enumerate(candidates):
            links = []
            for side in ("left", "right"):
                key = tuple(
                    candidate.get(side + "_" + field) for field in ("source", "artifact", "event")
                )
                if key not in group_map:
                    raise ValueError(
                        f"Overlap candidate {index}: unknown {side} source/artifact/event {key!r}"
                    )
                links.append(group_map[key])
            contexts.append(
                dict(
                    id=f"overlap-candidate-{index}",
                    review_id="imported-overlap-candidates",
                    kind="candidate_same_observation",
                    value=dict(candidate, group_ids=links),
                )
            )
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".import-", dir=output) as temporary:
        stage = Path(temporary)
        modern = stage / "collection"
        write_catalogue(
            modern,
            source,
            public,
            contexts,
            groups,
            [],
            [],
            [],
            sources,
            [],
            {},
            artifacts=artifacts,
            images=images,
        )
        merged = stage / "merged"
        merged.mkdir()
        shutil.copyfile(base / base_database, merged / "tychonides.sqlite")
        with closing(sqlite3.connect((merged / "tychonides.sqlite").as_uri(), uri=True)) as db:
            # This is an isolated staged file. Validate every foreign key below
            # before accepting it; per-insert checks repeatedly scan large tables.
            db.execute("PRAGMA foreign_keys=OFF")
            db.execute("ATTACH DATABASE ? AS incoming", (str(modern / "tychonides.sqlite"),))
            db.execute(
                "ATTACH DATABASE ? AS original",
                (base.joinpath(base_database).as_uri() + "?mode=ro",),
            )
            with db:
                _merge_catalogue_rows(db)
                metadata = dict(
                    publication_status="internal_combined_catalogue_not_cleared_for_distribution",
                    release_id="combined-import-1",
                    historical_release="mars-1.0.0",
                    modern_quantities=len(source),
                    external_image_versions=len(images),
                )
                for key, value in metadata.items():
                    db.execute(
                        "INSERT OR REPLACE INTO metadata VALUES (?,?)", (key, encoded(value))
                    )
                if db.execute("PRAGMA foreign_key_check").fetchall():
                    raise ValueError("Combined catalogue has broken relationships")
            count = db.execute("SELECT count(*) FROM quantities").fetchone()[0]
            group_count = db.execute("SELECT count(*) FROM groups").fetchone()[0]
        with (merged / "tychonides.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = None
            for path in (base / base_csv, modern / "tychonides.csv"):
                with path.open(encoding="utf-8", newline="") as incoming:
                    reader = csv.DictReader(incoming)
                    if writer is None:
                        writer = csv.DictWriter(stream, fieldnames=reader.fieldnames)
                        writer.writeheader()
                    elif reader.fieldnames != writer.fieldnames:
                        raise ValueError("Incompatible CSV schemas")
                    writer.writerows(reader)
        if any(digest(Path(p)) != checksum for p, checksum in fingerprints.items()):
            raise ValueError("An input changed during import")
        manifest = dict(
            status="internal_combined_catalogue_not_cleared_for_distribution",
            schema_version=3,
            release_id="combined-import-1",
            quantities=count,
            groups=group_count,
            imported_quantities=len(source),
            imported_groups=len(groups),
            images=len(images),
            imported_artifacts=len(artifacts),
            overlap_candidates=len(contexts),
            output_hashes={n: digest(merged / n) for n in ("tychonides.sqlite", "tychonides.csv")},
        )
        write_json_atomic(merged / "manifest.json", manifest)
        validate_release(merged)
        publish(merged, output, manifest)
    write_json_atomic(
        output / "import-verification.json",
        dict(
            input_hashes=fingerprints,
            manifest=manifest,
            original_rows_preserved=True,
            input_files_unchanged=True,
            image_pixels_copied=False,
        ),
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--database", type=Path)
    mode.add_argument("--catalogue", type=Path, help="Additional unprojected working catalogue")
    parser.add_argument("--quantities", type=Path)
    parser.add_argument("--overlaps", type=Path)
    parser.add_argument("--base", default="work/combined-catalogue/expanded", type=Path)
    parser.add_argument("--output", default="work/combined-catalogue/imported", type=Path)
    parser.add_argument(
        "--repeat", action="store_true", help="Verify matching catalogue-merge exports"
    )
    args = parser.parse_args()
    from .checkout import require_checkout

    require_checkout(parser)
    if args.catalogue:
        if args.quantities or args.overlaps:
            parser.error("--catalogue cannot be combined with ETL export options")
        result = merge_catalogues(args.base, args.catalogue, args.output, repeat=args.repeat)
    else:
        if args.quantities is None or args.repeat:
            parser.error("--database requires --quantities; --repeat applies to catalogue merges")
        result = import_collection(
            args.database, args.quantities, args.base, args.output, args.overlaps
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
