import unittest
from src.core import extract_text


class ContinuationTests(unittest.TestCase):
    def extract(self, text):
        return extract_text(text, "book", dict(volume=12, year=1591))

    def test_prose_hemisphere_cites_the_actual_book_line(self):
        rows = self.extract(
            "### 2 January\n\nMars was observed.\nDeclination of Mars, north: 18° 15′.\n"
        )
        self.assertEqual(rows[0]["line"], 4)
        self.assertEqual(rows[0]["hemisphere_locus"], "book:4")

    def test_same_page_blank_header_continues_a_dated_declination_table(self):
        rows = self.extract("""### 29 April
| Time | Distance of Mars | Southern declination of Mars | Altitude |
|---|---|---|---|
| 1^h^ 29^m^ | 28° 16′ | 24° 50′ | 7° 36′ |

An obstruction was noted.

| | | | |
|---|---|---|---|
| 1^h^ 47⅙^m^ | 49° 22′ | 24° 49⅚′ | 8° 15′ |
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["89400", "89390"])
        self.assertEqual(rows[1]["schema_basis"], "same_date_table_continuation")

    def test_label_without_value_scopes_following_pinnule_readings(self):
        rows = self.extract("""### 14 January
Mars was observed.
| Time | Reading | Value |
|---|---|---|
| 7^h^ 44½^m^ | Declination of Mars, north | |
| | with one pinnule | 1° 26′ |
| | with the other pinnule | 1° 25½′ |
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["5160", "5130"])
        self.assertEqual([r["time_key"] for r in rows], ["27870", "27870"])

    def test_changed_quantity_in_a_declination_column_stops_inheritance(self):
        rows = self.extract("""### 12 February
| Time | Declination of Mars |
|---|---|
| 6^h^ 20^m^ | 4° 45⅙′ |
| | Azimuth of Mars, west |
| 6^h^ 35^m^ | 80° 5′ |
""")
        self.assertEqual(len(rows), 1)

    def test_transit_clock_with_description_replaces_previous_clock(self):
        rows = self.extract("""### 2 January
| H. M. | Distance of Mars | Declination of Mars | Aldebaran east |
|---|---|---|---|
| 7 11 0 | 20 10⅓ | | |
| 7 12½ Mars crossed the meridian | | | |
| Declination of Mars | | 18 15 | |
""")
        self.assertEqual(rows[0]["time_key"], "25950")

    def test_bare_readings_allow_printed_brace_and_pinnule_annotation(self):
        rows = self.extract("""### 3 January
| H. M. | Distance of Mars | Declination of Mars |
|---|---|---|
| 6 18¾ | 15 46¼ | { 18 19⅚ } |
| 6 21⅚ | 15 46⅓ | } 18 20 with one [vno] |
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["65990", "66000"])


if __name__ == "__main__":
    unittest.main()
