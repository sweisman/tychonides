import unittest
from src.core import extract_text, compare_records


class FullSetTests(unittest.TestCase):
    def test_unique_page_clock_match_exposes_wrong_date(self):
        p = dict(id="p", volume=12, page=139, date="1591-01-23", time_key="22070", arcsec="100")
        r = dict(p, id="r", date="1591-01-28", arcsec="200")
        result = compare_records([p], [r])[0]
        self.assertEqual(result["candidate_ids"], ["r"])
        self.assertEqual(result["status"], "disagreement")
        self.assertEqual(result["date_status"], "conflict")
        self.assertEqual(result["source_date"], "1591-01-28")

    def test_equal_measurement_cannot_choose_among_dates(self):
        p = dict(id="p", volume=12, page=139, date="1591-01-23", time_key="22070", arcsec="100")
        rs = [dict(p, id="a", date="1591-01-28"), dict(p, id="b", date="1591-01-29", arcsec="200")]
        self.assertNotIn(compare_records([p], rs)[0]["status"], ["exact", "disagreement"])

    def test_running_header_latin_date_and_volume(self):
        text = """# Batch 031 — PDF pages 61–62
<!-- PDF p. 61 -->
[Running header: 44    1596]
## DIE 2 JANUARIJ, VESPERI.
Mars was observed.
| H. M. | Declination of Mars |
|---|---|
| 6 10 | 18 15 |
"""
        rows = extract_text(text, "source", {"volume": 13})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["volume"], 13)
        self.assertEqual(rows[0]["date"], "1596-01-02")
        self.assertEqual(rows[0]["page"], 44)
        self.assertEqual(rows[0]["pdf_page"], 61)

    def test_on_english_date_and_1586_year(self):
        text = """<!-- PDF p. 77 -->
[Running header: 1586   63]
#### *On 23 September [DIE 23 SEPTEMBRIS.]*
| Time | Declination of Mars, north |
|---|---|
| 5^h^ 12^m^ | 18° 5½′ |
"""
        rows = extract_text(text, "source", {"volume": 11})
        self.assertEqual(rows[0]["date"], "1586-09-23")
        self.assertEqual(rows[0]["volume"], 11)

    def test_matching_includes_volume(self):
        p = dict(id="p", volume=10, page=44, date="1582-01-02", time_key=None, arcsec="1")
        r = dict(p, id="s", volume=11)
        self.assertEqual(compare_records([p], [r])[0]["status"], "unmatched")


if __name__ == "__main__":
    unittest.main()
