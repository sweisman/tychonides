"""Project a combined research catalogue into a portable public release."""

import argparse
import csv
from contextlib import closing
import gzip
import json
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile

from .catalog_release import encoded
from .catalog_enrichment import (
    PUBLIC_CSV_COLUMNS,
    enrich_catalogue,
    load_registry,
)
from .core import digest
from .recovery import write_json_atomic
from .release_transaction import publish
from .release_validation import validate_release
from .catalog_indexes import create_indexes
from .catalog_files import working_files

IMAGE_FIELDS = {
    "DATE_OBS",
    "DAY_OBS",
    "EXPTIME",
    "FILTER",
    "INSTRUME",
    "OBJECT",
    "OBSTYPE",
    "RLEVEL",
    "SITEID",
    "TELID",
    "frame_id",
    "version_id",
    "observation_date",
    "exposure_time",
    "reduction_level",
    "site_id",
    "instrument_id",
    "telescope_id",
    "target_name",
    "primary_optical_element",
}
PRIVATE = re.compile(
    r"/home/|/site/repo/|~/|JSESSIONID|anubis-auth|local_pixel_path|(?<![\w-])Bearer ", re.I
)


def publish_collection(source, output, release_id=None):
    if release_id is None:
        import tomllib

        release_id = (
            "tychonides-"
            + tomllib.loads(
                (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
            )["project"]["version"]
        )
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output or source.is_relative_to(output) or output.is_relative_to(source):
        raise ValueError("Public and working catalogues must be separate")
    validate_release(source)
    source_database, source_csv = working_files(source)
    original_hashes = {n: digest(source / n) for n in (source_database, source_csv)}
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".public-", dir=output) as directory:
        stage = Path(directory)
        shutil.copyfile(source / source_database, stage / "tychonides.sqlite")
        with closing(sqlite3.connect(stage / "tychonides.sqlite")) as db:
            enrich_catalogue(db, load_registry())
            create_indexes(db)
            with db:
                db.execute(
                    "UPDATE artifacts SET content=NULL, redistribution_status='source_terms_apply_reference_only'"
                )
                for sid, frame, version, payload in db.execute(
                    "SELECT source_id,frame_id,version_id,metadata_json FROM images"
                ).fetchall():
                    clean = {k: v for k, v in json.loads(payload).items() if k in IMAGE_FIELDS}
                    db.execute(
                        "UPDATE images SET metadata_json=? WHERE source_id=? AND frame_id=? AND version_id=?",
                        (encoded(clean), sid, frame, version),
                    )
                for key in (
                    "publication_status",
                    "release_id",
                    "historical_release",
                    "modern_quantities",
                    "external_image_versions",
                    "historical_subset_release",
                    "historical_subset_version",
                    "historical_subset_version_kind",
                ):
                    db.execute("DELETE FROM metadata WHERE key=?", (key,))
                meta = dict(
                    publication_status="research_catalogue",
                    release_id=release_id,
                    code_license="AGPL-3.0-or-later",
                    data_license="CC0-1.0",
                    license_scope="Project contributions; third-party sources retain their terms",
                    image_pixels_included=False,
                    source_artifact_bytes_included=False,
                )
                db.execute("UPDATE metadata SET value_json='5' WHERE key='schema_version'")
                for key, value in meta.items():
                    db.execute("INSERT INTO metadata VALUES (?,?)", (key, encoded(value)))
            counts = {
                key: db.execute("SELECT count(*) FROM " + table).fetchone()[0]
                for key, table in [
                    ("quantities", "quantities"),
                    ("groups", "groups"),
                    ("sources", "sources"),
                    ("images", "images"),
                    ("artifacts", "artifacts"),
                    ("controls", "control_links"),
                    ("interpretations", "interpretations"),
                ]
            }
            per_source = dict(
                db.execute("SELECT source_id,count(*) FROM quantities GROUP BY source_id")
            )
            for (table,) in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall():
                for row in db.execute(f'SELECT * FROM "{table}"'):
                    if any(isinstance(v, str) and PRIVATE.search(v) for v in row):
                        raise ValueError("Private material remains in public projection: " + table)
            db.row_factory = sqlite3.Row
            from .csv_projection import project_csv

            columns = (*PUBLIC_CSV_COLUMNS, "normalized_json")
            with (stage / "tychonides.csv").open("w", encoding="utf-8", newline="") as outgoing:
                writer = csv.DictWriter(outgoing, fieldnames=columns)
                writer.writeheader()
                writer.writerows(project_csv(db, columns))
            db.commit()
            db.execute("PRAGMA page_size=4096")
            db.execute("VACUUM")
        with (stage / "tychonides.csv").open(encoding="utf-8") as stream:
            if any(PRIVATE.search(line) for line in stream):
                raise ValueError("Private material remains in CSV")
        with (
            (stage / "tychonides.sqlite").open("rb") as incoming,
            (stage / "tychonides.sqlite.gz").open("wb") as outgoing,
        ):
            with gzip.GzipFile(filename="", mode="wb", fileobj=outgoing, mtime=0) as compressed:
                shutil.copyfileobj(incoming, compressed)
        manifest = dict(
            release_id=release_id,
            schema_version=5,
            status="research_catalogue",
            index_contract=1,
            vocabulary_contract=1,
            **counts,
            quantities_by_source=per_source,
            code_license="AGPL-3.0-or-later",
            data_license="CC0-1.0",
            license_scope=meta["license_scope"],
            sqlite_sha256=digest(stage / "tychonides.sqlite"),
            output_hashes={
                n: digest(stage / n) for n in ("tychonides.sqlite.gz", "tychonides.csv")
            },
            download_urls={
                name: f"https://github.com/sweisman/tychonides/releases/download/{release_id}/{name}"
                for name in ("tychonides.sqlite.gz", "tychonides.csv")
            },
        )
        write_json_atomic(stage / "manifest.json", manifest)
        validate_release(stage)
        if any(digest(source / n) != checksum for n, checksum in original_hashes.items()):
            raise ValueError("Working input changed during publication")
        publish(stage, output, manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="work/combined-catalogue/expanded", type=Path)
    parser.add_argument(
        "--output", required=True, type=Path, help="Staging directory for Release assets"
    )
    parser.add_argument("--release-id", required=True)
    args = parser.parse_args()
    print(json.dumps(publish_collection(args.source, args.output, args.release_id), indent=2))


if __name__ == "__main__":
    main()
