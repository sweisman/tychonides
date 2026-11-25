"""Guards added after the November 2026 review of the verifier and parsers."""

from contextlib import closing
from fractions import Fraction
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from src.catalog_release import write_catalogue
from src.core import angle, digest, number, quote_angle, recorded_clock, time_key
from src.publish_collection import publish_collection
from src.release_validation import (
    PUBLISHED_MANIFEST_FIELDS,
    validate_marked_values,
    validate_release,
    validate_release_references,
)


class ParserHardeningTests(unittest.TestCase):
    def test_number_takes_one_whole_part_and_fractions(self):
        self.assertEqual(number("18 1/12"), Fraction(217, 12))
        self.assertEqual(number("5"), 5)
        self.assertEqual(number("1/2"), Fraction(1, 2))
        with self.assertRaisesRegex(ValueError, "Several whole numbers"):
            number("3 17")

    def test_zero_denominators_are_unknown_notation(self):
        self.assertIsNone(angle("5/0° 3′"))
        self.assertIsNone(time_key("2/0^h^ 3^m^"))
        self.assertIsNone(recorded_clock("H. 5/0"))
        self.assertIsNone(quote_angle("Decl. 12 5/0"))
        self.assertEqual(angle("5° 3′"), 18180)

    def test_clock_keys_reject_sixty_or_more_minutes_or_seconds(self):
        self.assertEqual(time_key("2^h^ 46 1/2^m^"), "9990")
        self.assertIsNone(time_key("2^h^ 70^m^"))
        self.assertIsNone(time_key("2^h^ 10^m^ 60^s^"))


class MarkedValueTests(unittest.TestCase):
    def database(self, rows):
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE catalogue(id, version, expression, unit, value_exact, status)")
        db.execute("CREATE TABLE quantities(id, source_payload_json)")
        db.execute("CREATE TABLE interpretations(quantity_id, version, normalized_json)")
        for identifier, expression, unit, value, least in rows:
            db.execute(
                "INSERT INTO catalogue VALUES (?, 1, ?, ?, ?, 'exact')",
                (identifier, expression, unit, value),
            )
            db.execute("INSERT INTO quantities VALUES (?, NULL)", (identifier,))
            db.execute(
                "INSERT INTO interpretations VALUES (?, 1, ?)",
                (identifier, json.dumps({"least_component_unit": least})),
            )
        return closing(db)

    def test_marked_expressions_are_recomputed(self):
        rows = [
            ("angle", "23° 18 1/12′", "arcsecond", "83885", "arcminute"),
            ("clock", "2^h^ 46½^m^", "second_of_time", "9990", "minute"),
            # The minutes of this value stand in another table cell.
            ("cell", "13^g^", "arcsecond", "49200", "arcminute"),
            # No unit marks, so the expression alone does not fix the value.
            ("bare", "34 5½", "arcsecond", "122730", "arcminute"),
        ]
        with self.database(rows) as db:
            self.assertEqual(validate_marked_values(db), 2)

    def test_a_value_that_differs_from_its_expression_is_rejected(self):
        with self.database([("angle", "23° 18′", "arcsecond", "83885", "arcminute")]) as db:
            with self.assertRaisesRegex(ValueError, "differs from its marked expression: angle"):
                validate_marked_values(db)


class ReleaseCheckReportingTests(unittest.TestCase):
    def setUp(self):
        from test_catalog_release import CatalogueReleaseTests

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source, public, contexts = CatalogueReleaseTests().fixture()
        draft = self.root / "draft"
        write_catalogue(draft, source, public, contexts, [], [], [], [], [], [], {})
        self.release = self.root / "public"
        publish_collection(draft, self.release)

    def test_absent_optional_fields_are_reported_as_skipped_checks(self):
        self.assertNotIn("groups", validate_release(self.release)["skipped_checks"])
        path = self.release / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        del manifest["groups"]
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertIn("groups", validate_release(self.release)["skipped_checks"])

    def test_the_database_is_unpacked_once_beside_the_assets_and_can_be_kept(self):
        kept = self.root / "kept" / "tychonides.sqlite"
        result = validate_release(self.release, keep_database=kept)
        self.assertEqual(result["status"], "verified")
        manifest = json.loads((self.release / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(digest(kept), manifest["sqlite_sha256"])
        self.assertEqual(
            sorted(path.name for path in self.release.iterdir()),
            sorted(["manifest.json", *manifest["output_hashes"]]),
        )

    def test_a_published_manifest_must_carry_every_checked_field(self):
        catalog = self.root / "checkout/resources/catalog"
        catalog.mkdir(parents=True)
        manifest = dict.fromkeys(PUBLISHED_MANIFEST_FIELDS, 1) | {"release_id": "tychonides-0.0.0"}
        del manifest["index_contract"]
        (catalog / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "omits checked fields: index_contract"):
            validate_release_references(self.root / "checkout")


if __name__ == "__main__":
    unittest.main()
