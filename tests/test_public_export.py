import json
import unittest
from src import publication_export


class PublicExportTests(unittest.TestCase):
    def test_export_drops_private_provenance_and_unknown_future_fields(self):
        private = "/private/library/book_prepub.md"
        row = dict(
            pafko_id="Sheet1:874",
            volume=13,
            pafko_page=45,
            source_page=45,
            pafko_date="1596-01-31",
            source_date="1596-01-31",
            source_record_id=private + ":5080:2",
            quote="PRIVATE SOURCE WORDING",
            future_context={"path": private},
            source_magnitude_arcsec="56280",
            preferred_magnitude_arcsec="56280",
            target="Aldebaran",
            role="calibration",
            mars_selection="excluded_other_target",
            comparison_status="disagreement",
            preferred_basis="source_scan_review",
            flags=["hemisphere_unresolved"],
            source_check="source_supports_translation_and_target_correction",
        )
        registry = [
            dict(
                volume=13,
                original_scan="https://example.org/scan",
                translation_page="https://example.org/book",
                translation_pdf="https://example.org/book.pdf",
            )
        ]
        result = publication_export.public_records([row], registry)
        self.assertEqual(result[0]["record_id"], "pafko-874")
        self.assertEqual(result[0]["preferred_magnitude_arcsec"], "56280")
        self.assertEqual(result[0]["mars_selection"], "excluded_other_target")
        self.assertNotIn(private, json.dumps(result))
        self.assertNotIn("PRIVATE SOURCE WORDING", json.dumps(result))
        self.assertNotIn("future_context", result[0])

    def test_paths_hidden_in_expected_numeric_or_flag_fields_are_rejected(self):
        row = dict(pafko_id="Sheet1:8", volume=12, preferred_magnitude_arcsec="/private/secret")
        with self.assertRaises(ValueError):
            publication_export.public_records([row], [])
        row = dict(pafko_id="Sheet1:8", volume=12, flags=["/private/secret"])
        with self.assertRaises(ValueError):
            publication_export.public_records([row], [])

    def test_unknown_target_text_is_not_published_as_a_name(self):
        row = dict(pafko_id="Sheet1:8", volume=12, target="/private/secret")
        with self.assertRaises(ValueError):
            publication_export.public_records([row], [])


if __name__ == "__main__":
    unittest.main()
