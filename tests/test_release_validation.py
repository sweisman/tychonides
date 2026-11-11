from contextlib import closing, redirect_stderr, redirect_stdout
import csv
import io
import json
import shutil
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from src.catalog_release import write_catalogue
from src.core import digest
from src.publish_collection import publish_collection
from src.release_validation import main, validate_documentation, validate_release
from src.schema_docs import render, validate_schema_docs


class ReleaseValidationTests(unittest.TestCase):
    def test_registered_books_use_historical_vocabulary_without_a_tycho_prefix(self):
        from src.vocabulary import load_vocabulary, validate_vocabulary

        vocabularies = {kind: load_vocabulary(kind) for kind in ("historical", "modern")}
        vocabularies["modern"]["quantity"].pop("calculation_angle", None)
        with closing(sqlite3.connect(":memory:")) as db:
            db.execute("CREATE TABLE quantities(id TEXT, source_id TEXT, role TEXT)")
            db.execute("CREATE TABLE interpretations(quantity_id TEXT, quantity TEXT, unit TEXT)")
            db.execute(
                "INSERT INTO quantities VALUES ('q', 'brahe-progymnasmata-erara', 'historical_input')"
            )
            db.execute("INSERT INTO interpretations VALUES ('q', 'calculation_angle', 'arcsecond')")
            with patch("src.vocabulary.load_vocabulary", side_effect=vocabularies.__getitem__):
                validate_vocabulary(db)
                db.execute("UPDATE quantities SET source_id='modern-example'")
                with self.assertRaisesRegex(ValueError, "Undocumented modern quantity"):
                    validate_vocabulary(db)

    def rename_assets_to_legacy(self, directory):
        manifest_path = directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for name in list(manifest["output_hashes"]):
            legacy = name.replace("tychonides.", "mars.")
            (directory / name).rename(directory / legacy)
            manifest["output_hashes"][legacy] = manifest["output_hashes"].pop(name)
            if "download_urls" in manifest:
                manifest["download_urls"][legacy] = (
                    manifest["download_urls"].pop(name).replace("/" + name, "/" + legacy)
                )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest

    def test_legacy_assets_remain_readable_and_publish_with_project_names(self):
        from src.catalog_release import promote_catalogue

        legacy = self.rename_assets_to_legacy(self.release)
        self.assertEqual(validate_release(self.release)["quantities"], 2)
        output = self.root / "renamed"
        manifest = publish_collection(self.release, output)
        self.assertEqual(set(manifest["output_hashes"]), {"tychonides.sqlite.gz", "tychonides.csv"})
        self.assertTrue(manifest["release_id"].startswith("tychonides-"))
        self.assertFalse((output / "mars.sqlite.gz").exists())
        for name, checksum in legacy["output_hashes"].items():
            self.assertEqual(digest(self.release / name), checksum)
        promoted = self.root / "promoted"
        promote_catalogue(self.release, promoted, "tychonides-2.4.0", {})
        self.assertEqual(validate_release(promoted)["quantities"], 2)
        self.rename_assets_to_legacy(output)
        self.assertEqual(validate_release(output)["quantities"], 2)

    def test_mixed_legacy_and_current_names_are_rejected(self):
        path = self.release / "tychonides.csv"
        path.rename(self.release / "mars.csv")
        self.manifest(
            lambda m: m["output_hashes"].update(
                {"mars.csv": m["output_hashes"].pop("tychonides.csv")}
            )
        )
        with self.assertRaisesRegex(ValueError, "file set"):
            validate_release(self.release)

    def test_zodiac_context_survives_public_packaging(self):
        from test_catalog_release import CatalogueReleaseTests

        source, public, contexts = CatalogueReleaseTests().fixture()
        for records in (source, public):
            for row in records:
                row["normalized"].update(
                    longitude_origin="start_of_named_sign",
                    zodiac_sign="Gemini",
                    magnitude_degrees="1223/60",
                    zodiac_longitude_degrees="4823/60",
                    least_component_unit="arcminute",
                )
        public[1]["zodiac_sign_inherited_from_key"] = "source-column"
        draft = self.root / "zodiac"
        write_catalogue(draft, source, public, contexts, [], [], [], [], [], [], {})
        output = self.root / "zodiac-public"
        publish_collection(draft, output)
        validate_release(output)
        with (output / "tychonides.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            norm = json.loads(row["normalized_json"])
            self.assertEqual(norm["zodiac_longitude_degrees"], "4823/60")
            self.assertEqual(norm["longitude_origin"], "start_of_named_sign")
            self.assertEqual(
                float(row["value_degrees_decimal"]),
                float(__import__("fractions").Fraction("1223/60")),
            )

    def test_every_exported_column_is_checked_even_after_rehashing(self):
        public = self.root / "complete"
        publish_collection(self.release, public)
        self.release = public
        path = public / "tychonides.csv"
        original = path.read_bytes()
        with path.open(encoding="utf-8", newline="") as stream:
            columns = next(csv.reader(stream))
        for index, name in enumerate(columns):
            with self.subTest(column=name):
                path.write_bytes(original)
                value = '{"fabricated":true}' if name.endswith("_json") else "fabricated"
                self.csv_change(
                    lambda rows, index=index, value=value: rows[1].__setitem__(index, value)
                )
                with self.assertRaises(ValueError):
                    validate_release(public)

    def test_all_published_manifest_counts_are_checked(self):
        public = self.root / "counts"
        publish_collection(self.release, public)
        self.release = public
        original = (public / "manifest.json").read_bytes()
        for name in (
            "groups",
            "sources",
            "images",
            "artifacts",
            "controls",
            "interpretations",
            "quantities_by_source",
        ):
            with self.subTest(count=name):
                (public / "manifest.json").write_bytes(original)
                self.manifest(
                    lambda m, name=name: m.update(
                        {name: {"invented": 999999} if name == "quantities_by_source" else 999999}
                    )
                )
                with self.assertRaisesRegex(ValueError, "count"):
                    validate_release(public)

    def setUp(self):
        from test_catalog_release import CatalogueReleaseTests

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source, public, contexts = CatalogueReleaseTests().fixture()
        self.release = self.root / "release"
        write_catalogue(self.release, source, public, contexts, [], [], [], [], [], [], {})

    def manifest(self, change):
        path = self.release / "manifest.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        change(value)
        path.write_text(json.dumps(value), encoding="utf-8")

    def csv_change(self, change):
        path = self.release / "tychonides.csv"
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.reader(stream))
        change(rows)
        with path.open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerows(rows)
        self.manifest(lambda m: m["output_hashes"].update({"tychonides.csv": digest(path)}))

    def test_missing_compressed_checksum_is_actionable(self):
        public = self.root / "public"
        publish_collection(self.release, public)
        self.release = public
        self.manifest(lambda m: m.pop("sqlite_sha256"))
        with self.assertRaisesRegex(
            ValueError, "Compressed manifest requires a valid sqlite_sha256"
        ):
            validate_release(self.release)

    def test_manifest_can_verify_separately_downloaded_assets(self):
        manifest_dir = self.root / "manifest-only"
        manifest_dir.mkdir()
        shutil.copyfile(self.release / "manifest.json", manifest_dir / "manifest.json")
        self.assertEqual(
            validate_release(manifest_dir, assets_dir=self.release)["status"], "verified"
        )
        with self.assertRaisesRegex(ValueError, "Missing release file"):
            validate_release(manifest_dir)

    def test_compressed_database_checksum_mismatch(self):
        public = self.root / "public"
        publish_collection(self.release, public)
        self.release = public
        self.manifest(lambda m: m.update(sqlite_sha256="a" * 64))
        with self.assertRaisesRegex(ValueError, "Uncompressed database checksum mismatch"):
            validate_release(self.release)

    def test_file_checksum_mismatch(self):
        self.manifest(lambda m: m["output_hashes"].update({"tychonides.csv": "a" * 64}))
        with self.assertRaisesRegex(ValueError, "Release checksum mismatch"):
            validate_release(self.release)

    def test_unsupported_schema(self):
        self.manifest(lambda m: m.update(schema_version=999))
        with self.assertRaisesRegex(ValueError, "Unsupported catalogue schema"):
            validate_release(self.release)

    def test_download_urls_must_match_release_identity(self):
        self.manifest(
            lambda m: m.update(
                download_urls={
                    "tychonides.sqlite": "https://github.com/sweisman/tychonides/releases/download/wrong/tychonides.sqlite",
                    "tychonides.csv": "https://github.com/sweisman/tychonides/releases/download/wrong/tychonides.csv",
                }
            )
        )
        with self.assertRaisesRegex(ValueError, "download_urls"):
            validate_release(self.release)

    def test_incomplete_promotion(self):
        (self.release / ".pending-release").touch()
        with self.assertRaisesRegex(ValueError, "promotion is incomplete"):
            validate_release(self.release)

    def test_invalid_manifest_shape(self):
        for value, message in (
            ([], "JSON object"),
            ({}, "output_hashes"),
            ({"output_hashes": {}, "quantities": "2"}, "integer quantities"),
        ):
            with self.subTest(value=value):
                (self.release / "manifest.json").write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    validate_release(self.release)

    def test_unexpected_file_set(self):
        self.manifest(lambda m: m["output_hashes"].update({"other": "a" * 64}))
        with self.assertRaisesRegex(ValueError, "file set"):
            validate_release(self.release)

    def test_bad_checksum_and_missing_file(self):
        self.manifest(lambda m: m["output_hashes"].update({"tychonides.csv": "bad"}))
        with self.assertRaisesRegex(ValueError, "Invalid SHA"):
            validate_release(self.release)
        self.manifest(lambda m: m["output_hashes"].update({"tychonides.csv": "a" * 64}))
        (self.release / "tychonides.csv").unlink()
        with self.assertRaisesRegex(ValueError, "Missing release file"):
            validate_release(self.release)

    def test_header_drift(self):
        self.csv_change(lambda rows: rows[0].__setitem__(0, "wrong_id"))
        with self.assertRaisesRegex(ValueError, "CSV columns"):
            validate_release(self.release)

    def test_duplicate_identity(self):
        self.csv_change(lambda rows: rows.append(rows[1]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_release(self.release)

    def test_value_mismatch_even_with_updated_file_hash(self):
        self.csv_change(lambda rows: rows[1].__setitem__(rows[0].index("expression"), "changed"))
        with self.assertRaisesRegex(ValueError, "value mismatch"):
            validate_release(self.release)

    def test_quantity_count_mismatch(self):
        self.manifest(lambda m: m.update(quantities=3))
        with self.assertRaisesRegex(ValueError, "counts"):
            validate_release(self.release)

    def test_missing_csv_row(self):
        self.csv_change(lambda rows: rows.pop())
        with self.assertRaisesRegex(ValueError, "counts or identities"):
            validate_release(self.release)

    def test_schema_documentation_drift(self):
        docs = self.root / "docs"
        docs.mkdir()
        with closing(sqlite3.connect(self.release / "tychonides.sqlite")) as db:
            text = render(db)
            (docs / "database-schema.md").write_text(
                text.replace("`quantities.expression`", "removed"), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "quantities.expression"):
                validate_schema_docs(db, self.root)

    def test_new_modern_quantity_requires_documentation(self):
        docs = self.root / "docs"
        docs.mkdir()
        with closing(sqlite3.connect(self.release / "tychonides.sqlite")) as db:
            db.execute("UPDATE quantities SET source_id='modern-example'")
            db.execute("UPDATE interpretations SET quantity='unregistered_quantity'")
            (docs / "database-schema.md").write_text(render(db), encoding="utf-8")
            (docs / "modern-data-dictionary.md").write_text("", encoding="utf-8")
            (docs / "historical-data-dictionary.md").write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Undocumented modern quantity"):
                validate_schema_docs(db, self.root)

    def test_cli_verifies_downloads_and_public_documentation(self):
        public = self.root / "public"
        publish_collection(self.release, public)
        args = ["tychonides-verify", str(public), "--docs-root", str(Path(__file__).parents[1])]
        output = io.StringIO()
        with patch("sys.argv", args), redirect_stdout(output):
            main()
        self.assertEqual(json.loads(output.getvalue())["status"], "verified")

    def test_cli_manifest_error_has_no_traceback(self):
        self.manifest(lambda m: m.pop("output_hashes"))
        error = io.StringIO()
        with patch("sys.argv", ["tychonides-verify", str(self.release)]), redirect_stderr(error):
            with self.assertRaises(SystemExit) as caught:
                main()
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("output_hashes", error.getvalue())
        self.assertNotIn("Traceback", error.getvalue())

    def test_missing_csv_documentation_is_reported(self):
        (self.root / "docs").mkdir()
        (self.root / "docs/catalog-data-dictionary.md").write_text("", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Undocumented CSV fields"):
            validate_documentation(self.root)

    def test_historical_vocabulary_and_derived_conventions_are_checked(self):
        public = self.root / "public"
        publish_collection(self.release, public)
        from src.vocabulary import validate_vocabulary
        import gzip

        database = self.root / "vocabulary.sqlite"
        database.write_bytes(gzip.decompress((public / "tychonides.sqlite.gz").read_bytes()))
        with closing(sqlite3.connect(database)) as db:
            validate_vocabulary(db)
            db.execute("UPDATE interpretations SET quantity='unknown_historical_type'")
            with self.assertRaisesRegex(ValueError, "Undocumented historical quantity"):
                validate_vocabulary(db)
            db.rollback()
            identifier = db.execute("SELECT id FROM quantities LIMIT 1").fetchone()[0]
            db.execute(
                "INSERT INTO derived_values(quantity_id,derived_method) VALUES (?,?)",
                (identifier, "unknown_conversion"),
            )
            with self.assertRaisesRegex(ValueError, "Undocumented derived_method"):
                validate_vocabulary(db)
            db.rollback()
            for column, value in (
                ("derived_time_scale", "UNSPECIFIED_SCALE"),
                ("derived_unit", "unknown_physical_unit"),
            ):
                db.execute(
                    f"INSERT INTO derived_values(quantity_id,{column}) VALUES (?,?)",
                    (identifier, value),
                )
                with self.assertRaisesRegex(ValueError, "Undocumented " + column):
                    validate_vocabulary(db)
                db.rollback()

    def test_reverse_relationship_index_is_required_by_manifest(self):
        public = self.root / "public"
        manifest = publish_collection(self.release, public)
        import gzip

        database = self.root / "index-check.sqlite"
        database.write_bytes(gzip.decompress((public / "tychonides.sqlite.gz").read_bytes()))
        with closing(sqlite3.connect(database)) as db:
            db.execute("DROP INDEX quantity_contexts_reverse")
        (public / "tychonides.sqlite.gz").write_bytes(gzip.compress(database.read_bytes(), mtime=0))
        manifest["output_hashes"]["tychonides.sqlite.gz"] = digest(public / "tychonides.sqlite.gz")
        manifest["sqlite_sha256"] = digest(database)
        (public / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Missing or incompatible catalogue index"):
            validate_release(public)
