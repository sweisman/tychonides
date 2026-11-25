from contextlib import closing
import importlib
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from src.import_collection import import_collection, read_collection
from src.catalog_release import write_catalogue


class WorkingCatalogueMergeTests(unittest.TestCase):
    def test_page_review_preserves_original_and_corrects_shared_citation(self):
        from test_catalog_release import CatalogueReleaseTests

        from src.catalog_release import CSV_COLUMNS
        from src.csv_projection import project_csv
        from src.log_interpretations import apply_log_page_reviews

        source, public, contexts = CatalogueReleaseTests().fixture()
        identifiers = [row["id"] for row in source]
        locus = dict(
            id="locus-shared",
            source_id="tycho-oo-11",
            printed_page=334,
            status="mapped_source_page",
            page_basis="reviewed_quantity_citation",
            quantity_ids=identifiers,
            context_ids=[],
        )
        decisions = [
            dict(
                quantity_id=row["id"],
                volume=11,
                previous_printed_page=334,
                printed_page=335,
                source_expression=row["source_expression"],
            )
            for row in source
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_catalogue(
                root, source, public, contexts, [], [], [], [], [], [], {}, loci=[locus]
            )
            with closing(sqlite3.connect(root / "tychonides.sqlite")) as db:
                with self.assertRaisesRegex(ValueError, "shared printed locus"), db:
                    apply_log_page_reviews(db, decisions[:1])
                originals = db.execute(
                    "SELECT id,original_json FROM quantities ORDER BY id"
                ).fetchall()
                with db:
                    self.assertEqual(apply_log_page_reviews(db, decisions), 2)
                self.assertEqual(
                    db.execute("SELECT id,original_json FROM quantities ORDER BY id").fetchall(),
                    originals,
                )
                self.assertEqual(
                    {int(row["printed_page"]) for row in project_csv(db, CSV_COLUMNS)}, {335}
                )
                indexed, current = db.execute(
                    "SELECT printed_page,data_json FROM source_loci WHERE id=?", (locus["id"],)
                ).fetchone()
                self.assertEqual(indexed, 335)
                self.assertEqual(json.loads(current)["previous_printed_page"], 334)

    def test_reading_revision_keeps_the_original_and_exports_the_reviewed_sign(self):
        from test_catalog_release import CatalogueReleaseTests

        from src.catalog_release import CSV_COLUMNS, source_value_hash
        from src.csv_projection import project_csv
        from src.log_interpretations import apply_log_interpretations
        from src.normalization import normalize_quantity

        source, public, contexts = CatalogueReleaseTests().fixture()
        reading = dict(
            source[0],
            source_expression="13° 24",
            role="unresolved",
            quantity="unclassified_numeric_expression",
            subject="unassigned table entry",
            flags=["source_notation_unresolved"],
        )
        reading["normalized"] = normalize_quantity(reading)
        projection = dict(
            public[0],
            **{k: reading[k] for k in ("role", "quantity", "subject", "flags", "normalized")},
        )
        interpretation = dict(
            quantity="declination",
            role="recorded_coordinate",
            subject="fixed star",
            reference=None,
            direction="north",
            components={"degree": "13", "arcminute": "24", "arcsecond": "30"},
            zodiac_sign=None,
            flags=[],
        )
        decision = dict(
            quantity_id=reading["id"],
            volume=11,
            column=2,
            printed_page=334,
            source_expression=reading["source_expression"],
            source_value_sha256=source_value_hash(reading),
            occurrence=[3, 9],
            interpretation=interpretation,
            normalized=normalize_quantity(interpretation),
            basis=dict(
                interpretation,
                designation="The sixth star",
                label="Declination, north",
                column=2,
                completed_source_field=dict(expression="13° 24′ 30″", occurrence=[3, 14]),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_catalogue(root, [reading], [projection], contexts[:1], [], [], [], [], [], [], {})
            with closing(sqlite3.connect(root / "tychonides.sqlite")) as db:
                original = tuple(db.execute("SELECT * FROM quantities").fetchone())
                altered = dict(
                    decision,
                    interpretation=dict(
                        interpretation, components={"degree": "14", "arcminute": "24"}
                    ),
                )
                with self.assertRaisesRegex(ValueError, "explicit places"), db:
                    apply_log_interpretations(db, [altered])
                with db:
                    apply_log_interpretations(db, [decision])
                selected = next(project_csv(db, CSV_COLUMNS))
                self.assertEqual(
                    (
                        selected["role"],
                        selected["direction"],
                        selected["signed_value_exact"],
                        selected["interpretation_version"],
                        selected["expression"],
                    ),
                    ("recorded_coordinate", "north", "48270", 1, "13° 24′ 30″"),
                )
                self.assertEqual(tuple(db.execute("SELECT * FROM quantities").fetchone()), original)
                self.assertEqual(
                    [
                        row[0]
                        for row in db.execute(
                            "SELECT version FROM interpretations ORDER BY version"
                        )
                    ],
                    [0, 1],
                )

    def test_missing_locus_page_can_be_completed_but_conflicting_pages_are_rejected(self):
        from src.import_collection import _reconciled_locus_claim

        unknown = dict(id="example-locus", printed_page=None, status="page_unestablished")
        indexed = dict(
            unknown,
            printed_page=7,
            status="provisional_source_page",
            page_basis="automatic_page_index",
        )
        self.assertEqual(_reconciled_locus_claim(unknown, indexed), indexed)
        self.assertEqual(_reconciled_locus_claim(indexed, unknown), indexed)
        self.assertIsNone(_reconciled_locus_claim(indexed, dict(indexed, printed_page=8)))

    def test_merge_set_unions_backlinks_at_a_shared_source_locus(self):
        from test_catalog_release import CatalogueReleaseTests

        from src.import_collection import merge_catalogue_set

        source, public, contexts = CatalogueReleaseTests().fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = [root / "first", root / "second"]
            for i, path in enumerate(inputs):
                locus = dict(
                    id="example-locus",
                    source_id="tycho-oo-11",
                    printed_page=1 if i else None,
                    status="mapped_source_page" if i else "page_unestablished",
                    page_basis="reviewed_quantity_citation" if i else None,
                    quantity_ids=[source[i]["id"]],
                    context_ids=[],
                )
                write_catalogue(
                    path,
                    [source[i]],
                    [public[i]],
                    [contexts[i]],
                    [],
                    [],
                    [],
                    [],
                    [],
                    [],
                    {},
                    loci=[locus],
                )
            output = root / "merged"
            with patch("src.import_collection.WORK_ROOT", root):
                merge_catalogue_set([*inputs, inputs[0]], output)
            with closing(sqlite3.connect(output / "tychonides.sqlite")) as db:
                payload = json.loads(db.execute("SELECT data_json FROM source_loci").fetchone()[0])
                self.assertEqual(payload["page_basis"], "reviewed_quantity_citation")
                self.assertEqual(
                    db.execute("SELECT status, printed_page FROM source_loci").fetchone(),
                    ("mapped_source_page", 1),
                )
                expected = sorted(row["id"] for row in source)
                self.assertEqual(payload["quantity_ids"], expected)
                self.assertEqual(
                    db.execute(
                        "SELECT quantity_id FROM locus_quantities ORDER BY quantity_id"
                    ).fetchall(),
                    [(identifier,) for identifier in expected],
                )

    def inputs(self, root):
        from test_catalog_release import CatalogueReleaseTests

        source, public, contexts = CatalogueReleaseTests().fixture()
        for name, index in (("base", 0), ("additional", 1)):
            write_catalogue(
                root / name,
                [source[index]],
                [public[index]],
                [contexts[index]],
                [],
                [],
                [],
                [],
                [],
                [],
                {},
            )
        return source, public, contexts

    def merge(self, root, base, additional, output, **kwargs):
        module = importlib.import_module("src.import_collection")
        function = getattr(module, "merge_catalogues", None)
        self.assertTrue(callable(function), "Working catalogue merge is unavailable")
        with patch.object(module, "WORK_ROOT", root, create=True):
            return function(base, additional, output, **kwargs)

    def test_preserves_both_catalogues_and_qualified_contexts_without_changing_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.inputs(root)
            inputs = {
                path: path.read_bytes()
                for name in ("base", "additional")
                for path in (root / name).iterdir()
                if path.is_file()
            }
            manifest = self.merge(
                root, root / "base", root / "additional", root / "merged", repeat=True
            )
            self.assertEqual(manifest["quantities"], 2)
            with closing(sqlite3.connect(root / "merged/tychonides.sqlite")) as db:
                self.assertEqual(
                    set(db.execute("SELECT expression,value_exact FROM catalogue")),
                    {("59‴", None), ("1′", "60")},
                )
                self.assertEqual(
                    db.execute(
                        "SELECT count(*) FROM contexts WHERE context_id='shared'"
                    ).fetchone()[0],
                    2,
                )
                self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
            for path, before in inputs.items():
                self.assertEqual(path.read_bytes(), before)

    def test_identical_source_identities_are_retained_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.inputs(root)
            manifest = self.merge(root, root / "base", root / "base", root / "merged")
            self.assertEqual(manifest["quantities"], 1)

    def test_merge_refreshes_the_native_quantity_count(self):
        from src.core import digest

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.inputs(root)
            with closing(sqlite3.connect(root / "base/tychonides.sqlite")) as db, db:
                db.execute("INSERT INTO metadata VALUES ('modern_quantities','999')")
            path = root / "base/manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["output_hashes"]["tychonides.sqlite"] = digest(root / "base/tychonides.sqlite")
            path.write_text(json.dumps(manifest), encoding="utf-8")
            self.merge(root, root / "base", root / "additional", root / "merged")
            with closing(sqlite3.connect(root / "merged/tychonides.sqlite")) as db:
                self.assertEqual(
                    db.execute(
                        "SELECT value_json FROM metadata WHERE key='modern_quantities'"
                    ).fetchone()[0],
                    "0",
                )

    def test_conflicting_context_preserves_the_previous_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, public, contexts = self.inputs(root)
            self.merge(root, root / "base", root / "additional", root / "merged")
            old = {p.name: p.read_bytes() for p in (root / "merged").iterdir() if p.is_file()}
            contexts[0]["value"] = {"side": "different source statement"}
            write_catalogue(
                root / "conflict",
                [source[0]],
                [public[0]],
                [contexts[0]],
                [],
                [],
                [],
                [],
                [],
                [],
                {},
            )
            with self.assertRaisesRegex(ValueError, "Conflicting.*contexts"):
                self.merge(root, root / "base", root / "conflict", root / "merged")
            self.assertEqual(
                {p.name: p.read_bytes() for p in (root / "merged").iterdir() if p.is_file()}, old
            )

    def test_incompatible_tables_are_rejected_instead_of_dropped(self):
        from src.core import digest

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.inputs(root)
            database = root / "additional/tychonides.sqlite"
            with closing(sqlite3.connect(database)) as db, db:
                db.execute("CREATE TABLE additional_scientific_data(id TEXT PRIMARY KEY)")
                db.execute("INSERT INTO additional_scientific_data VALUES ('retained-evidence')")
            path = root / "additional/manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["output_hashes"]["tychonides.sqlite"] = digest(database)
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "schema"):
                self.merge(root, root / "base", root / "additional", root / "merged")


class CollectionImportTests(unittest.TestCase):
    def test_export_cannot_inject_a_conversion_into_unchanged_source(self):
        with tempfile.TemporaryDirectory() as directory:
            database, export = self.fixture(Path(directory))
            before = database.read_bytes()
            row = json.loads(export.read_text(encoding="utf-8"))
            row["derived_normalization"] = dict(
                magnitude="999", unit="arcsecond", method="sexagesimal_conversion"
            )
            export.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "independently recomputed"):
                read_collection(database, export)
            self.assertEqual(database.read_bytes(), before)

    def fixture(self, root):
        database = root / "input.sqlite"
        payload = dict(
            id="same-local-id",
            subject="Mars",
            quantity="declination",
            role="reduced_coordinate",
            literal="12",
            unit="arcsecond",
            locator="row 1",
            event_id="event-1",
            platform="ground",
            technique="optical",
            time_scale="UT",
            coordinate_origin="geocentric",
        )
        checksum = hashlib.sha256(b"original artifact").hexdigest()
        with closing(sqlite3.connect(database)) as db, db:
            db.executescript("""CREATE TABLE sources(id,url);
            CREATE TABLE artifacts(source,sha256,retrieved_at,content);
            CREATE TABLE quantities(source,artifact,id,payload,magnitude,unit);
            CREATE TABLE images(frame_id,version_id,sha256,archive_md5,path,bytes,metadata);""")
            db.execute("INSERT INTO sources VALUES (?,?)", ("modern", "https://example.org/data"))
            db.execute(
                "INSERT INTO artifacts VALUES (?,?,?,?)",
                ("modern", checksum, "2026-01-01", b"original artifact"),
            )
            db.execute(
                "INSERT INTO quantities VALUES (?,?,?,?,?,?)",
                ("modern", checksum, payload["id"], json.dumps(payload), "12", "arcsecond"),
            )
        export = root / "quantities.jsonl"
        export.write_text(
            json.dumps(
                dict(
                    payload,
                    source_id="modern",
                    artifact_sha256=checksum,
                    normalized={"magnitude": "12", "unit": "arcsecond"},
                )
            )
            + "\n",
            encoding="utf-8",
        )
        return database, export

    def test_roundtrip_preserves_history_and_repeat_is_idempotent(self):
        from test_catalog_release import CatalogueReleaseTests

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database, export = self.fixture(root)
            source, published, contexts = CatalogueReleaseTests().fixture()
            write_catalogue(root / "base", source, published, contexts, [], [], [], [], [], [], {})
            with patch("src.import_collection.PROTECTED_ROOT", root):
                first = import_collection(database, export, root / "base", root / "combined")
                second = import_collection(database, export, root / "base", root / "combined")
            self.assertEqual(first, second)
            self.assertEqual(first["quantities"], 3)
            base_manifest = root / "base/manifest.json"
            legacy = json.loads(base_manifest.read_text(encoding="utf-8"))
            for name in list(legacy["output_hashes"]):
                old_name = name.replace("tychonides.", "mars.")
                (root / "base" / name).rename(root / "base" / old_name)
                legacy["output_hashes"][old_name] = legacy["output_hashes"].pop(name)
            base_manifest.write_text(json.dumps(legacy), encoding="utf-8")
            with patch("src.import_collection.PROTECTED_ROOT", root):
                imported_legacy = import_collection(
                    database, export, root / "base", root / "legacy-import"
                )
            self.assertEqual(first, imported_legacy)
            with closing(sqlite3.connect(root / "combined/tychonides.sqlite")) as db:
                original = json.loads(
                    db.execute(
                        "SELECT source_payload_json FROM quantities WHERE source_id='modern'"
                    ).fetchone()[0]
                )
                self.assertEqual(original["time_scale"], "UT")
                self.assertEqual(original["normalized"]["magnitude"], "12")

    def test_changed_export_and_duplicate_identity_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            database, export = self.fixture(Path(directory))
            original = export.read_text(encoding="utf-8")
            export.write_text(original + original, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                read_collection(database, export)
            row = json.loads(original)
            row["literal"] = "13"
            export.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed"):
                read_collection(database, export)

    def test_public_output_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "protected"):
            import_collection(
                "missing.sqlite", "missing.jsonl", "resources/mars", "resources/imported"
            )

    def test_unknown_overlap_group_names_candidate_and_side(self):
        from test_catalog_release import CatalogueReleaseTests

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database, export = self.fixture(root)
            source, public, contexts = CatalogueReleaseTests().fixture()
            write_catalogue(root / "base", source, public, contexts, [], [], [], [], [], [], {})
            candidates = root / "overlaps.json"
            candidates.write_text(
                json.dumps(
                    [{"left_source": "missing", "left_artifact": "a" * 64, "left_event": "none"}]
                ),
                encoding="utf-8",
            )
            with patch("src.import_collection.PROTECTED_ROOT", root):
                with self.assertRaisesRegex(ValueError, "Overlap candidate 0: unknown left"):
                    import_collection(
                        database, export, root / "base", root / "combined", candidates
                    )
