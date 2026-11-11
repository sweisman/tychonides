import copy
import csv
from contextlib import closing
import gc
import importlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import warnings


class CatalogueReleaseTests(unittest.TestCase):
    def test_coordinate_product_authorities_survive_both_exports_with_scoped_context(self):
        source, published, contexts = self.fixture()
        product = dict(
            authorities=["Ptolemy", "al-Battānī", "Alfonso", "Copernicus"],
            basis_context_id="shared",
        )
        source[1]["source_coordinate_product"] = copy.deepcopy(product)
        published[1]["source_coordinate_product"] = copy.deepcopy(product)
        contexts[1]["value"] = dict(
            record_type="source_coordinate_product_attribution",
            authorities=product["authorities"],
            source_label="Ptolemy, al-Battānī, Alfonso, Copernicus",
            scientific_role="historical_prediction",
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.module().write_catalogue(
                output, source, published, contexts, [], [], [], [], [], [], {}
            )
            with closing(sqlite3.connect(output / "tychonides.sqlite")) as db:
                metadata = json.loads(
                    db.execute(
                        "SELECT scientific_metadata_json FROM quantities WHERE id=?",
                        (source[1]["id"],),
                    ).fetchone()[0]
                )
                evidence = db.execute(
                    "SELECT c.value_json FROM quantity_contexts q JOIN contexts c "
                    "USING(context_id,scope_id) WHERE q.id=? AND q.context_id=?",
                    (source[1]["id"], "shared"),
                ).fetchall()
            self.assertEqual(metadata["source_coordinate_product"], product)
            self.assertEqual(len(evidence), 1)
            self.assertEqual(json.loads(evidence[0][0])["authorities"], product["authorities"])
            with (output / "tychonides.csv").open(encoding="utf-8") as handle:
                row = next(r for r in csv.DictReader(handle) if r["id"] == source[1]["id"])
            self.assertEqual(
                json.loads(row["scientific_metadata_json"])["source_coordinate_product"], product
            )

    def module(self):
        self.assertIsNotNone(
            importlib.util.find_spec("src.catalog_release"),
            "The self-contained catalogue exporter is missing",
        )
        return importlib.import_module("src.catalog_release")

    def fixture(self):
        sources = []
        published = []
        for n, review, expression, quantity, subject, norm in (
            (
                "a",
                "r1",
                "59‴",
                "calculation_angle",
                "Mars calculation",
                dict(status="unsupported", unit="arcsecond", magnitude=None, signed_magnitude=None),
            ),
            (
                "b",
                "r2",
                "1′",
                "declination",
                "Mars",
                dict(status="exact", unit="arcsecond", magnitude="60", signed_magnitude=None),
            ),
        ):
            row = dict(
                id="assertion-v11-" + n * 20,
                volume=11,
                printed_page=334,
                review_id=review,
                source_expression=expression,
                quantity=quantity,
                subject=subject,
                reference=None,
                role="historical_input",
                direction=None,
                components={},
                normalized=norm,
                flags=["not_an_additional_raw_reading"],
                context_ids=["shared"],
                event_id=None,
                series_id=None,
                uncertainty=dict(numeric=None),
            )
            sources.append(row)
            published.append(
                {
                    k: copy.deepcopy(v)
                    for k, v in row.items()
                    if k not in ("review_id", "source_expression", "context_ids", "uncertainty")
                }
            )
        contexts = [
            dict(
                id="shared",
                review_id="r1",
                kind="source_observation_context",
                value={"side": "north"},
            ),
            dict(
                id="shared",
                review_id="r2",
                kind="source_observation_context",
                value={"side": "south"},
            ),
        ]
        return sources, published, contexts

    def test_explicit_angular_thirds_keep_the_source_minute_denominator(self):
        m = self.module()
        for expression, want in (("59‴", "59/60"), ("2″\u00a025‴", "29/12")):
            out = m.normalize_minute_motion(expression)
            self.assertEqual(out["magnitude"], want)
            self.assertEqual(out["unit"], "arcsecond_per_source_minute")
            self.assertEqual(out["least_component_unit"], "arcsexagesimal_third")
        for expression in ("1ᵈ 59′ 8″ 10‴", "2″ 60‴", "59", "2′25‴"):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                m.normalize_minute_motion(expression)

    def test_split_numerical_expression_keeps_every_fragment_in_both_exports(self):
        source, published, contexts = self.fixture()
        source[1].update(
            source_expression="0°",
            source_fragments=[
                dict(line=10, span_id="private-binding-1", source_expression="0°"),
                dict(line=11, span_id="private-binding-2", source_expression="1′"),
            ],
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.module().write_catalogue(
                output, source, published, contexts, [], [], [], [], [], [], {}
            )
            with closing(sqlite3.connect(output / "tychonides.sqlite")) as db:
                metadata = json.loads(
                    db.execute(
                        "SELECT scientific_metadata_json FROM quantities WHERE id=?",
                        (source[1]["id"],),
                    ).fetchone()[0]
                )
            self.assertEqual(metadata["source_numeric_fragments"], ["0°", "1′"])
            self.assertNotIn("private-binding", json.dumps(metadata))
            with (output / "tychonides.csv").open(encoding="utf-8") as handle:
                row = next(r for r in csv.DictReader(handle) if r["id"] == source[1]["id"])
            self.assertEqual(
                json.loads(row["scientific_metadata_json"])["source_numeric_fragments"],
                ["0°", "1′"],
            )

    def test_database_preserves_qualified_contexts_and_original_interpretation(self):
        m = self.module()
        source, published, contexts = self.fixture()
        before = copy.deepcopy(source)
        revision = dict(
            id="interpretation-minute-motion",
            quantity_id=source[0]["id"],
            source_value_sha256=m.source_value_hash(source[0]),
            kind="angular_minutely_motion",
            subject="Mars",
            basis="Explicit minute-motion label in the Mars calculation; stated angular thirds.",
        )
        with tempfile.TemporaryDirectory() as d:
            result = m.write_catalogue(
                Path(d), source, published, contexts, [], [], [], [], [], [revision], {}
            )
            with closing(sqlite3.connect(Path(d) / "tychonides.sqlite")) as db:
                self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(db.execute("SELECT COUNT(*) FROM contexts").fetchone()[0], 2)
                sides = db.execute(
                    "SELECT q.id,c.value_json FROM quantity_contexts q JOIN contexts c USING(context_id,scope_id) ORDER BY q.id"
                ).fetchall()
                self.assertEqual([json.loads(v)["side"] for _, v in sides], ["north", "south"])
                versions = db.execute(
                    "SELECT version,quantity,value_exact FROM interpretations WHERE quantity_id=? ORDER BY version",
                    (source[0]["id"],),
                ).fetchall()
                self.assertEqual(
                    versions,
                    [(0, "calculation_angle", None), (1, "angular_minutely_motion", "59/60")],
                )
                current = db.execute(
                    "SELECT quantity,subject,value_exact,expression FROM catalogue WHERE id=?",
                    (source[0]["id"],),
                ).fetchone()
                self.assertEqual(current, ("angular_minutely_motion", "Mars", "59/60", "59‴"))
            self.assertEqual(result["quantities"], 2)
            self.assertEqual(source, before)
            self.assertIn("59/60", (Path(d) / "tychonides.csv").read_text())

    def test_revisions_and_links_fail_closed_when_their_source_is_missing_or_changed(self):
        m = self.module()
        source, published, contexts = self.fixture()
        revision = dict(
            id="revision",
            quantity_id=source[0]["id"],
            source_value_sha256=m.source_value_hash(source[0]),
            kind="angular_minutely_motion",
            subject="Mars",
            basis="Explicit source units.",
        )
        for altered, ctx, revs in (
            ([dict(source[0], source_expression="58‴"), source[1]], contexts, [revision]),
            (source, contexts[:1], []),
        ):
            with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
                m.write_catalogue(Path(d), altered, published, ctx, [], [], [], [], [], revs, {})

    def test_reviewed_altitude_classification_keeps_original_numbers_and_instrument_uncertainty(
        self,
    ):
        m = self.module()
        source, published, contexts = self.fixture()
        for row in (source[1], published[1]):
            row.update(
                quantity="unclassified_angle",
                role="recorded_reading",
                flags=["measurement_type_unresolved", "instrument_identity_unestablished"],
            )
        source[1]["components"] = {"degree": "33", "arcminute": "6"}
        for row in (source[1], published[1]):
            row["normalized"].update(magnitude="119160", unit="arcsecond")
        review = dict(
            id="altitude-classification",
            quantity_id=source[1]["id"],
            source_value_sha256=m.source_value_hash(source[1]),
            kind="source_quantity_classification",
            quantity="altitude",
            basis="Reviewed altitude column, printed page 175.",
            source_evidence_sha256="a" * 64,
        )
        with tempfile.TemporaryDirectory() as d:
            m.write_catalogue(
                Path(d), source, published, contexts, [], [], [], [], [], [review], {}
            )
            with closing(sqlite3.connect(Path(d) / "tychonides.sqlite")) as db:
                versions = db.execute(
                    "SELECT quantity,value_exact,flags_json FROM interpretations WHERE quantity_id=? ORDER BY version",
                    (source[1]["id"],),
                ).fetchall()
                self.assertEqual(
                    [(q, n) for q, n, _ in versions],
                    [("unclassified_angle", "119160"), ("altitude", "119160")],
                )
                self.assertEqual(json.loads(versions[-1][2]), ["instrument_identity_unestablished"])

    def test_same_inputs_reproduce_both_single_file_database_and_csv(self):
        m = self.module()
        source, published, contexts = self.fixture()
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "one", Path(d) / "two"
            m.write_catalogue(a, source, published, contexts, [], [], [], [], [], [], {})
            m.write_catalogue(b, source, published, contexts, [], [], [], [], [], [], {})
            self.assertEqual(
                (a / "tychonides.sqlite").read_bytes(), (b / "tychonides.sqlite").read_bytes()
            )
            self.assertEqual(
                (a / "tychonides.csv").read_bytes(), (b / "tychonides.csv").read_bytes()
            )

    def test_release_is_self_contained_reproducible_and_preserves_the_verified_draft(self):
        m = self.module()
        source, published, contexts = self.fixture()
        with tempfile.TemporaryDirectory() as d:
            draft, one, two = (Path(d) / name for name in ("draft", "release-one", "release-two"))
            original = m.write_catalogue(
                draft, source, published, contexts, [], [], [], [], [], [], {}
            )
            before = (draft / "tychonides.sqlite").read_bytes()
            for output in (one, two):
                m.promote_catalogue(draft, output, "mars-1.0.0", {})
            self.assertEqual((draft / "tychonides.sqlite").read_bytes(), before)
            self.assertEqual(
                (one / "tychonides.sqlite").read_bytes(), (two / "tychonides.sqlite").read_bytes()
            )
            self.assertEqual(
                (one / "tychonides.csv").read_bytes(), (draft / "tychonides.csv").read_bytes()
            )
            with closing(sqlite3.connect(one / "tychonides.sqlite")) as db:
                self.assertEqual(
                    json.loads(
                        db.execute(
                            "SELECT value_json FROM metadata WHERE key=?", ("publication_status",)
                        ).fetchone()[0]
                    ),
                    "research_catalogue",
                )
                self.assertEqual(
                    db.execute("SELECT count(*) FROM catalogue").fetchone()[0],
                    original["quantities"],
                )
            (draft / "tychonides.csv").write_text("changed")
            with self.assertRaises(ValueError):
                m.promote_catalogue(draft, Path(d) / "rejected", "mars-1.0.0", {})

    def test_export_closes_its_database_before_returning(self):
        m = self.module()
        source, published, contexts = self.fixture()
        gc.collect()
        with tempfile.TemporaryDirectory() as d, warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ResourceWarning)
            m.write_catalogue(Path(d), source, published, contexts, [], [], [], [], [], [], {})
            gc.collect()
            self.assertEqual(
                [str(w.message) for w in caught if issubclass(w.category, ResourceWarning)], []
            )

    def test_repeated_identical_context_pointers_are_one_relationship(self):
        m = self.module()
        source, published, contexts = self.fixture()
        source[0]["context_ids"] = ["shared", "shared"]
        events = [dict(id="group", review_id="r1", context_ids=["shared", "shared"])]
        with tempfile.TemporaryDirectory() as d:
            try:
                m.write_catalogue(
                    Path(d), source, published, contexts, events, [], [], [], [], [], {}
                )
            except sqlite3.IntegrityError as error:
                self.fail("Identical context pointers are the same relation: " + str(error))
            with closing(sqlite3.connect(Path(d) / "tychonides.sqlite")) as db:
                self.assertEqual(
                    db.execute("SELECT COUNT(*) FROM quantity_contexts").fetchone()[0], 2
                )
                self.assertEqual(db.execute("SELECT COUNT(*) FROM group_contexts").fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM contexts").fetchone()[0], 2)

    def test_csv_preserves_bounds_and_unknown_statistical_uncertainty(self):
        m = self.module()
        source, published, contexts = self.fixture()
        source[1]["flags"] = published[1]["flags"] = ["source_lower_bound"]
        source[1]["uncertainty"] = {
            "numeric": None,
            "basis": "Recorded lower bound; not an exact measured position.",
        }
        with tempfile.TemporaryDirectory() as d:
            m.write_catalogue(Path(d), source, published, contexts, [], [], [], [], [], [], {})
            with (Path(d) / "tychonides.csv").open(newline="") as stream:
                row = list(csv.DictReader(stream))[1]
            self.assertIn("flags_json", row, "CSV must preserve the lower-bound qualification")
            self.assertEqual(json.loads(row["flags_json"]), ["source_lower_bound"])
            self.assertIsNone(json.loads(row["uncertainty_json"])["numeric"])
            self.assertEqual(row["value_exact"], "60")

    def test_csv_includes_numeric_conveniences_dates_and_source_scale_qualifications(self):
        m = self.module()
        source, published, contexts = self.fixture()
        for row in (source[1], published[1]):
            row.update(quantity="model_length", source_scalar_scale="10000")
            row["normalized"].update(unit="model_length", magnitude="25/2")
        published[1]["source_date_claim_ids"] = ["date"]
        date = dict(id="date", year=1590, month=3, day=4, calendar=None, absolute_timestamp=None)
        with tempfile.TemporaryDirectory() as d:
            m.write_catalogue(Path(d), source, published, contexts, [], [date], [], [], [], [], {})
            with (Path(d) / "tychonides.csv").open(newline="") as stream:
                row = list(csv.DictReader(stream))[1]
            self.assertEqual(row["value_exact"], "25/2")
            self.assertEqual(float(row["value_decimal"]), 12.5)
            self.assertEqual(
                json.loads(row["scientific_metadata_json"])["source_scalar_scale"], "10000"
            )
            self.assertEqual(json.loads(row["date_claims_json"]), [date])

    def test_variants_have_navigable_quantity_relationships(self):
        m = self.module()
        source, published, contexts = self.fixture()
        variant = copy.deepcopy(source[1])
        variant.update(
            id="assertion-v11-" + "c" * 20, source_expression="2′", role="editorial_variant"
        )
        variant["normalized"]["magnitude"] = "120"
        source.append(variant)
        out = copy.deepcopy(published[1])
        out.update(id=variant["id"], role="editorial_variant", variant_of_id=source[1]["id"])
        out["normalized"]["magnitude"] = "120"
        published.append(out)
        with tempfile.TemporaryDirectory() as d:
            m.write_catalogue(Path(d), source, published, contexts, [], [], [], [], [], [], {})
            with closing(sqlite3.connect(Path(d) / "tychonides.sqlite")) as db:
                self.assertIn(
                    "quantity_links",
                    {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")},
                )
                self.assertEqual(
                    db.execute("SELECT from_id,to_id,kind FROM quantity_links").fetchall(),
                    [(variant["id"], source[1]["id"], "variant_of_id")],
                )

    def test_multiple_sources_keep_artifact_versions_and_native_scientific_metadata(self):
        m = self.module()
        source = []
        published = []
        sources = [
            dict(
                id="jjmo-2003",
                title="JJMO report",
                kind="observation_report",
                work_id="jjmo-mars",
                edition_id="2003",
            ),
            dict(
                id="usno-w1",
                title="W1J00",
                kind="catalogue",
                work_id="w1j00",
                edition_id="catalogue-release",
            ),
        ]
        artifacts = []
        for i, sid, sha, scale, origin in (
            (1, "jjmo-2003", "a" * 64, "EDT", None),
            (2, "usno-w1", "b" * 64, "UT1", "geocentric"),
            (3, "usno-w1", "c" * 64, "UT1", "geocentric"),
        ):
            artifacts.append(
                dict(
                    source_id=sid,
                    sha256=sha,
                    media_type="text/plain",
                    redistribution_status="unreviewed",
                )
            )
            row = dict(
                id="quantity-" + str(i),
                source_id=sid,
                artifact_sha256=sha,
                source_entry_id="line:1:value",
                locator="PDF page 3, row 1" if i == 1 else "line 1",
                source_expression="0.125" if i == 1 else "2450000.5",
                quantity="micrometer_setting" if i == 1 else "recorded_epoch",
                subject="Mars",
                reference=None,
                role="instrument_reading" if i == 1 else "reduction",
                review_id=sid,
                components={},
                context_ids=[],
                normalized=dict(
                    status="exact",
                    unit="inch" if i == 1 else "julian_day",
                    magnitude="1/8" if i == 1 else "4900001/2",
                    signed_magnitude=None,
                ),
                flags=[],
                time_scale=scale,
                platform="ground",
                technique="optical",
                observer_code="A",
            )
            if origin:
                row.update(
                    coordinate_origin=origin,
                    coordinate_frame="true_equator_equinox_of_date",
                    corrections=[dict(kind="horizontal_parallax_declination", status="applied")],
                )
            source.append(row)
            published.append(
                {
                    k: copy.deepcopy(v)
                    for k, v in row.items()
                    if k not in ("review_id", "context_ids")
                }
            )
        with tempfile.TemporaryDirectory() as d:
            try:
                m.write_catalogue(
                    Path(d),
                    source,
                    published,
                    [],
                    [],
                    [],
                    [],
                    [],
                    sources,
                    [],
                    {},
                    artifacts=artifacts,
                )
            except (KeyError, TypeError, sqlite3.Error) as error:
                self.fail(
                    "Modern source contract must fit without Tycho placeholders: " + str(error)
                )
            with closing(sqlite3.connect(Path(d) / "tychonides.sqlite")) as db:
                rows = db.execute(
                    "SELECT source_id,artifact_sha256,source_entry_id,volume,locator,scientific_metadata_json FROM quantities ORDER BY id"
                ).fetchall()
                self.assertEqual(
                    [r[:5] for r in rows],
                    [
                        (sources[0]["id"], "a" * 64, "line:1:value", None, "PDF page 3, row 1"),
                        ("usno-w1", "b" * 64, "line:1:value", None, "line 1"),
                        ("usno-w1", "c" * 64, "line:1:value", None, "line 1"),
                    ],
                )
                payloads = [json.loads(r[5]) for r in rows]
                self.assertEqual([r["time_scale"] for r in payloads], ["EDT", "UT1", "UT1"])
                self.assertNotIn("coordinate_origin", payloads[0])
                self.assertEqual(payloads[1]["coordinate_origin"], "geocentric")
                self.assertEqual(payloads[1]["corrections"][0]["status"], "applied")
                self.assertNotIn("observer", payloads[0])
                self.assertEqual(payloads[0]["observer_code"], "A")

    def test_images_reference_external_versions_instead_of_copying_large_files(self):
        m = self.module()
        image = dict(
            source_id="lco",
            frame_id="123",
            version_id="7",
            sha256="d" * 64,
            archive_md5="e" * 32,
            bytes=8000000,
            public_url="https://archive-api.lco.global/frames/123/",
            metadata=dict(
                reduction_level=0,
                exposure_start="2020-10-01T00:00:00",
                time_scale="UTC",
                platform="ground",
            ),
        )
        with tempfile.TemporaryDirectory() as d:
            try:
                m.write_catalogue(
                    Path(d),
                    [],
                    [],
                    [],
                    [],
                    [],
                    [],
                    [],
                    [dict(id="lco", title="LCO Mars")],
                    [],
                    {},
                    images=[image],
                )
            except (TypeError, sqlite3.Error) as error:
                self.fail("Versioned external FITS references must be representable: " + str(error))
            with closing(sqlite3.connect(Path(d) / "tychonides.sqlite")) as db:
                self.assertEqual(
                    db.execute("SELECT frame_id,version_id,sha256,bytes FROM images").fetchone(),
                    ("123", "7", "d" * 64, 8000000),
                )
                self.assertEqual(
                    json.loads(db.execute("SELECT metadata_json FROM images").fetchone()[0])[
                        "reduction_level"
                    ],
                    0,
                )
            self.assertLess((Path(d) / "tychonides.sqlite").stat().st_size, 1000000)

    def test_source_export_adapter_preserves_native_payload_and_namespaces_events(self):
        m = self.module()
        adapter = getattr(m, "adapt_source_quantities", None)
        self.assertTrue(callable(adapter), "A source-neutral export boundary is required")
        rows = []
        for sid, sha, scale in (("jjmo", "a" * 64, "EDT"), ("w1", "b" * 64, "UT1")):
            rows.append(
                dict(
                    source_id=sid,
                    artifact_sha256=sha,
                    id="line:1:clock",
                    event_id="line:1",
                    subject="Mars",
                    quantity="recorded_clock",
                    role="recorded_clock",
                    literal="12:30",
                    unit="clock_expression",
                    normalized=dict(magnitude=None, unit="clock_expression"),
                    time_scale=scale,
                    locator="line 1",
                    platform="ground",
                    technique="optical",
                    derived_normalization=dict(
                        timestamp="2003-08-01T16:30:00+00:00", method="source_EDT_UTC_minus_4"
                    )
                    if sid == "jjmo"
                    else None,
                )
            )
        source, _published, events = adapter(rows)
        self.assertEqual(len({r["id"] for r in source}), 2)
        self.assertEqual(len({e["id"] for e in events}), 2)
        self.assertEqual([r["source_entry_id"] for r in source], ["line:1:clock"] * 2)
        self.assertEqual([r["time_scale"] for r in source], ["EDT", "UT1"])
        self.assertEqual([r["source_payload"] for r in source], rows)
        self.assertTrue(all(r.get("volume") is None for r in source))
        self.assertEqual([e["clock_assertion_id"] for e in events], [r["id"] for r in source])
        self.assertEqual(source, adapter(rows)[0])

    def test_book_authors_and_editions_do_not_collide_on_volume_or_become_observers(self):
        m = self.module()
        source, published, contexts = self.fixture()
        registry = [
            dict(
                id="brahe-book",
                author="Tycho Brahe",
                work_id="thesaurus",
                edition_id="english",
                volume=11,
            ),
            dict(
                id="longomontanus-book",
                author="Longomontanus",
                work_id="astronomia-danica",
                edition_id="1640",
                volume=11,
            ),
        ]
        source[0]["source_id"] = "brahe-book"
        source[1]["source_id"] = "longomontanus-book"
        with tempfile.TemporaryDirectory() as d:
            m.write_catalogue(
                Path(d), source, published, contexts, [], [], [], [], registry, [], {}
            )
            with closing(sqlite3.connect(Path(d) / "tychonides.sqlite")) as db:
                self.assertEqual(
                    db.execute(
                        "SELECT author,work_id,edition_id,volume FROM sources ORDER BY id"
                    ).fetchall(),
                    [
                        ("Tycho Brahe", "thesaurus", "english", 11),
                        ("Longomontanus", "astronomia-danica", "1640", 11),
                    ],
                )
                self.assertEqual(
                    [
                        json.loads(r[0])
                        for r in db.execute("SELECT scientific_metadata_json FROM quantities")
                    ],
                    [{}, {}],
                )

    def test_volume_alone_cannot_assign_an_unidentified_work_to_tycho(self):
        m = self.module()
        source, published, contexts = self.fixture()
        with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
            m.write_catalogue(
                Path(d),
                source,
                published,
                contexts,
                [],
                [],
                [],
                [],
                [dict(volume=11, author="Longomontanus", title="Astronomia Danica")],
                [],
                {},
            )
        source[0]["id"] = published[0]["id"] = "new-source-local-row"
        with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
            m.write_catalogue(Path(d), source, published, contexts, [], [], [], [], [], [], {})

    def test_context_citations_are_available_without_the_source_library(self):
        m = self.module()
        source, published, contexts = self.fixture()
        contexts[0].update(
            source_id="tycho-oo-11", locator=dict(printed_pages=[334], role="source_evidence_pages")
        )
        with tempfile.TemporaryDirectory() as d:
            m.write_catalogue(Path(d), source, published, contexts, [], [], [], [], [], [], {})
            with closing(sqlite3.connect(Path(d) / "tychonides.sqlite")) as db:
                columns = {r[1] for r in db.execute("PRAGMA table_info(contexts)")}
                self.assertIn(
                    "source_id", columns, "Context evidence needs its own source identity"
                )
                self.assertEqual(
                    json.loads(
                        db.execute(
                            "SELECT locator_json FROM contexts WHERE source_id=?", ("tycho-oo-11",)
                        ).fetchone()[0]
                    )["printed_pages"],
                    [334],
                )

    def test_native_identifiers_are_not_confused_with_cross_record_links(self):
        m = self.module()
        rows = []
        for local, value in (("assertion-native-entry", "1/10"), ("alternative", "1/5")):
            rows.append(
                dict(
                    source_id="modern",
                    artifact_sha256="a" * 64,
                    id=local,
                    locator=local,
                    literal=value,
                    unit="inch",
                    quantity="micrometer_setting",
                    subject="Mars",
                    role="instrument_reading",
                    normalized=dict(magnitude=value, unit="inch"),
                )
            )
        source, published, events = m.adapt_source_quantities(rows)
        published[1]["variant_of_id"] = source[0]["id"]
        with tempfile.TemporaryDirectory() as d:
            try:
                m.write_catalogue(
                    Path(d),
                    source,
                    published,
                    [],
                    events,
                    [],
                    [],
                    [],
                    [dict(id="modern")],
                    [],
                    {},
                    artifacts=[dict(source_id="modern", sha256="a" * 64)],
                )
            except ValueError as error:
                self.fail("Source-local IDs are identifiers, not relationships: " + str(error))
            with closing(sqlite3.connect(Path(d) / "tychonides.sqlite")) as db:
                self.assertEqual(
                    db.execute("SELECT from_id,to_id,kind FROM quantity_links").fetchall(),
                    [(source[1]["id"], source[0]["id"], "variant_of_id")],
                )

    def test_public_loci_have_navigable_source_and_quantity_links(self):
        m = self.module()
        source, published, contexts = self.fixture()
        loci = [
            dict(
                id="locus",
                source_id="tycho-oo-11",
                printed_page=334,
                status="mapped_source_page",
                quantity_ids=[source[0]["id"]],
                context_ids=[],
            )
        ]
        with tempfile.TemporaryDirectory() as d:
            try:
                m.write_catalogue(
                    Path(d), source, published, contexts, [], [], [], [], [], [], {}, loci=loci
                )
            except TypeError as error:
                self.fail(
                    "Public source positions must be stored in the single catalogue: " + str(error)
                )
            with closing(sqlite3.connect(Path(d) / "tychonides.sqlite")) as db:
                self.assertEqual(
                    db.execute(
                        "SELECT l.source_id,l.printed_page,q.quantity_id FROM source_loci l JOIN locus_quantities q ON q.locus_id=l.id"
                    ).fetchall(),
                    [("tycho-oo-11", 334, source[0]["id"])],
                )


if __name__ == "__main__":
    unittest.main()
