import tempfile
import unittest
from pathlib import Path
from src.publication import extract_publications


class PublicationTests(unittest.TestCase):
    def test_ending_page_note_supplies_provenance_for_preceding_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            d = root / "brahe/thesaurus_observationum_vol4/translation"
            d.mkdir(parents=True)
            body = "### 20 January\n| | |\n|---|---|\n| Declination of Mars | 21°26′40″B. |\n"
            (d / "batch_119.md").write_text(
                "<!-- PDF p. 237 -->\n"
                + body
                + '[QA: PDF p. 237 = printed p. 220. Running head "220" left, "1600" centred.]\n'
            )
            (d / "brahe_thesaurus_observationum_vol4_prepub.md").write_text(body)
            rows, _ = extract_publications(root, [13])
            self.assertEqual(rows[0]["page"], 220)
            self.assertEqual(rows[0]["date"], "1600-01-20")

    def test_volume_four_uses_current_scan_not_old_batch_offset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            d = root / "brahe/thesaurus_observationum_vol4/translation"
            d.mkdir(parents=True)
            body = "## DIE 2 JANUARIJ.\nMars was observed.\n| Time | Declination of Mars |\n|---|---|\n| 6^h^ 10^m^ | 18 15 |\n"
            (d / "batch_030.md").write_text(
                "<!-- PDF p. 59 (printed p. 43) -->\n[Running header: 1596 43]\n" + body
            )
            (d / "brahe_thesaurus_observationum_vol4_prepub.md").write_text(body)
            rows, _ = extract_publications(root, [13])
            self.assertEqual(rows[0]["page"], 43)
            self.assertEqual(rows[0]["pdf_page"], 60)
            self.assertEqual(rows[0]["batch_pdf_page"], 59)

    def test_final_product_supplies_values_batches_only_supply_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            d = root / "brahe/thesaurus_observationum_vol3/translation"
            d.mkdir(parents=True)
            prefix = "### 4 March\n\n| Time | Declination of Mars, north |\n|---|---|\n"
            batch = (
                '[QA: PDF p. 58 — running head: "1590", page number "44"]\n'
                + prefix
                + "| 7^h^ 5^m^ | 9° 28′ |\n"
            )
            book = "# Observations of the year 1590\n" + prefix + "| 7^h^ 5^m^ | 9° 26′ |\n"
            (d / "batch_029.md").write_text(batch)
            (d / "brahe_thesaurus_observationum_vol3_prepub.md").write_text(book)
            records, hashes = extract_publications(root, [12])
            self.assertEqual(records[0]["value_original"], "9° 26′")
            self.assertIn("_prepub.md", records[0]["source"])
            self.assertIn("_prepub.md", " ".join(hashes))
            self.assertNotEqual(records[0]["magnitude_arcsec"], "34080")


if __name__ == "__main__":
    unittest.main()
