from contextlib import closing
import csv
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from src.catalog_release import write_catalogue
from src.publish_collection import PRIVATE, publish_collection


from src.release_validation import validate_release


class PrivacyScanTests(unittest.TestCase):
    def test_distinguishes_the_water_bearer_from_credentials(self):
        self.assertIsNone(
            PRIVATE.search("The left Hand of the Water-bearer [Sinistra manus Aquarii]")
        )
        for literal in ("Bearer secret", "Authorization: Bearer secret", '"token":"bearer secret"'):
            with self.subTest(literal=literal):
                self.assertIsNotNone(PRIVATE.search(literal))


class PublicCollectionTests(unittest.TestCase):
    def test_jpl_legacy_rows_are_requalified_and_cannot_pass_with_a_fabricated_sign(self):
        from src.catalog_release import adapt_source_quantities
        from src.core import digest
        from src.csv_projection import project_csv
        from src.numeric_integrity import recompute_conversion

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = []
            for number, literal in enumerate((" 00000000", " 00571072", "-00571072"), 1):
                unit = "signed_ddmmss_centisecond"
                native = dict(
                    source_id="jpl-wash6a" if number == 1 else "jpl-wash6c",
                    artifact_sha256="a" * 64,
                    id=f"line:{number}:declination",
                    subject="Mars",
                    quantity="declination",
                    role="reduction",
                    literal=literal,
                    locator=f"line {number}",
                    raw_line="P" + " " * 49 + literal,
                    unit=unit,
                    normalized={"magnitude": None, "unit": unit},
                )
                native["derived_normalization"] = recompute_conversion(native, legacy_jpl=True)
                rows.append(native)
            source, public, groups = adapt_source_quantities(rows)
            write_catalogue(
                root / "working",
                source,
                public,
                [],
                groups,
                [],
                [],
                [],
                [{"id": native["source_id"]} for native in (rows[0], rows[1])],
                [],
                {},
                artifacts=[
                    {"source_id": native["source_id"], "sha256": native["artifact_sha256"]}
                    for native in (rows[0], rows[1])
                ],
            )
            publish_collection(root / "working", root / "public")
            database = root / "check.sqlite"
            database.write_bytes(
                gzip.decompress((root / "public/tychonides.sqlite.gz").read_bytes())
            )
            with closing(sqlite3.connect(database)) as db:
                db.row_factory = sqlite3.Row
                query = "SELECT derived_value_exact,derived_signed_value_exact FROM catalogue ORDER BY locator"
                self.assertEqual(
                    [tuple(row) for row in db.execute(query)],
                    [(None, None), ("85768/25", None), ("85768/25", "-85768/25")],
                )
                for table, assignment, message in (
                    ("derived_values", "derived_signed_value_exact='85768/25'", "Derived columns"),
                    ("interpretations", "flags_json='[]'", "published flags"),
                ):
                    key = db.execute("SELECT id FROM catalogue WHERE locator='line 2'").fetchone()[
                        0
                    ]
                    db.execute("SAVEPOINT fabricated")
                    db.execute(f"UPDATE {table} SET {assignment} WHERE quantity_id=?", (key,))
                    public = root / "public"
                    csv_path = public / "tychonides.csv.gz"
                    with gzip.open(csv_path, "rt", encoding="utf-8", newline="") as stream:
                        columns = csv.DictReader(stream).fieldnames
                    text = io.StringIO(newline="")
                    writer = csv.DictWriter(text, columns)
                    writer.writeheader()
                    writer.writerows(project_csv(db, columns))
                    rewritten = text.getvalue().encode("utf-8")
                    csv_path.write_bytes(gzip.compress(rewritten))
                    altered = db.serialize()
                    gzip_path = public / "tychonides.sqlite.gz"
                    gzip_path.write_bytes(gzip.compress(altered))
                    manifest_path = public / "manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest["sqlite_sha256"] = sha256(altered).hexdigest()
                    manifest["csv_sha256"] = sha256(rewritten).hexdigest()
                    for path in (csv_path, gzip_path):
                        manifest["output_hashes"][path.name] = digest(path)
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        validate_release(public)
                    db.execute("ROLLBACK TO fabricated")
                    db.execute("RELEASE fabricated")

    def test_modern_values_are_queryable_and_shared_lines_roundtrip(self):
        from src.catalog_release import adapt_source_quantities

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            row = dict(
                source_id="usno-w1",
                artifact_sha256="a" * 64,
                id="line:1:dec",
                subject="Mars",
                quantity="declination",
                role="reduction",
                literal="-16 50 32.96",
                locator="line 1",
                raw_line="Mars -16 50 32.96",
                normalized={"magnitude": None, "unit": "sexagesimal_degree"},
                derived_normalization={
                    "magnitude": "-1515824/25",
                    "unit": "arcsecond",
                    "method": "sexagesimal_conversion",
                },
            )
            other = dict(row, id="line:1:dec-copy")
            source, public, groups = adapt_source_quantities([row, other])
            write_catalogue(
                root / "working",
                source,
                public,
                [],
                groups,
                [],
                [],
                [],
                [{"id": "usno-w1", "url": "https://example.org/data"}],
                [],
                {},
                artifacts=[{"source_id": "usno-w1", "sha256": "a" * 64}],
            )
            publish_collection(root / "working", root / "public")
            path = root / "check.sqlite"
            path.write_bytes(gzip.decompress((root / "public/tychonides.sqlite.gz").read_bytes()))
            with closing(sqlite3.connect(path)) as db:
                result = db.execute(
                    "SELECT value_exact,derived_value_exact,derived_signed_value_exact,derived_unit,source_line_number FROM catalogue LIMIT 1"
                ).fetchone()
                self.assertEqual(result, (None, "1515824/25", "-1515824/25", "arcsecond", 1))
                self.assertEqual(db.execute("SELECT count(*) FROM source_lines").fetchone()[0], 1)
                native = json.loads(
                    db.execute(
                        "SELECT source_payload_json FROM source_records WHERE source_entry_id=?",
                        (row["id"],),
                    ).fetchone()[0]
                )
                self.assertEqual(native, row)
                for field in ("original_json", "scientific_metadata_json", "source_payload_json"):
                    self.assertNotIn(
                        "raw_line",
                        json.loads(
                            db.execute("SELECT " + field + " FROM quantities LIMIT 1").fetchone()[0]
                        ),
                    )

    def test_compressed_release_preserves_values_and_excludes_private_image_paths(self):
        from test_catalog_release import CatalogueReleaseTests

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, public, contexts = CatalogueReleaseTests().fixture()
            images = [
                dict(
                    source_id="tycho-oo-11",
                    frame_id="1",
                    version_id="2",
                    sha256="a" * 64,
                    metadata={"local_pixel_path": "/home/private/image.fits", "EXPTIME": 10},
                )
            ]
            write_catalogue(
                root / "working",
                source,
                public,
                contexts,
                [],
                [],
                [],
                [],
                [],
                [],
                {},
                images=images,
            )
            first = publish_collection(root / "working", root / "public")
            second = publish_collection(root / "working", root / "public")
            self.assertEqual(first, second)
            self.assertEqual(validate_release(root / "public")["quantities"], 2)
            data = gzip.decompress((root / "public/tychonides.sqlite.gz").read_bytes())
            self.assertNotIn(b"/home/private", data)
            path = root / "check.sqlite"
            path.write_bytes(data)
            with closing(sqlite3.connect(path)) as db:
                plan = db.execute(
                    "EXPLAIN QUERY PLAN SELECT id FROM quantity_contexts WHERE context_id=? AND scope_id=?",
                    ("context", "scope"),
                ).fetchall()
                self.assertTrue(any("SEARCH quantity_contexts USING" in r[3] for r in plan), plan)
                self.assertEqual(
                    json.loads(db.execute("SELECT metadata_json FROM images").fetchone()[0]),
                    {"EXPTIME": 10},
                )
                self.assertEqual(
                    db.execute("SELECT count(*) FROM interpretations").fetchone()[0], 2
                )
                # The published counts cover the whole catalogue, not an earlier selection.
                self.assertEqual(
                    json.loads(
                        db.execute(
                            "SELECT value_json FROM metadata WHERE key='normalization_counts'"
                        ).fetchone()[0]
                    ),
                    {"exact": 1, "unsupported": 1},
                )
            with (root / "public/tychonides.sqlite.gz").open("ab") as stream:
                stream.write(b"changed")
            with self.assertRaisesRegex(ValueError, "checksum"):
                validate_release(root / "public")

    def test_unexpected_private_payload_blocks_export(self):
        from test_catalog_release import CatalogueReleaseTests

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, public, contexts = CatalogueReleaseTests().fixture()
            contexts[0]["value"] = {"unexpected": "/home/private/data"}
            write_catalogue(root / "working", source, public, contexts, [], [], [], [], [], [], {})
            with self.assertRaisesRegex(ValueError, "Private material"):
                publish_collection(root / "working", root / "public")
