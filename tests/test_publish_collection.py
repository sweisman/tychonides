from contextlib import closing
import gzip
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
