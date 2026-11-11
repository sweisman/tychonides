import unittest
from src.core import extract_text


class TableRoleTests(unittest.TestCase):
    def extract(self, text):
        return extract_text(text, "book", dict(year=1589, volume=11))

    def test_declination_from_altitude_keeps_the_established_planet_target(self):
        rows = self.extract("""### 7 March
Mars was observed.
| Time | Reading | Value |
|---|---|---|
| 10 11⅔ | Declination from the altitude m. | 5° 35′ 15″ |
""")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["target"], "Mars")
        self.assertEqual(rows[0]["time_key"], "36700")
        self.assertIsNone(rows[0]["arcsec"])

    def test_instrument_qualifier_keeps_second_declination_in_the_value_column(self):
        rows = self.extract("""### 12 March
Mars was observed.
| Time | Reading | Instrument | Value |
|---|---|---|---|
| 2^h^ 35^m^ | Declination of Mars | | 13° 36½′ |
| | | with the other [alt.] | 13° 37′ |
| 2^h^ 44^m^ | Distance of Mars from Spica | | 24° 24′ |
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["48990", "49020"])

    def test_shifted_value_column_continues_and_stops_at_next_reading_label(self):
        rows = self.extract("""### 4 March
Mars was observed.
| Time | Reading | Distance from Leo | Azimuth of Mars | Altitude |
|---|---|---|---|---|
| 7^h^ 22^m^ | Declination of Mars | | 4° 47¾′ | 12° 49′ |
| 7^h^ 26^m^ | | | 4° 48′ | |
| 7^h^ 30^m^ | Between Mars and Spica | 5° 59¾′ | 77° 49′ | |
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["17265", "17280"])

    def test_reference_star_calibration_table_cannot_inherit_mars_target(self):
        rows = self.extract("""### 3 March
Mars was observed.
N.B. For the places of the fixed stars from which Mars was observed.
| Reading | Meridian altitude | Declination |
|---|---|---|
| The third in the wing of Virgo | 34° 56½′ | 0° 51′ |
""")
        self.assertEqual(rows, [])

    def test_prose_star_calibration_cannot_inherit_mars_target(self):
        rows = self.extract("""### 27 February
Mars was observed.
To test the armillae, we observed the lower star in the wheels.
It ought to have had a declination of 58° 34′.
""")
        self.assertEqual(rows, [])

    def test_explicitly_reviewed_calibration_identity_survives_mars_filtering(self):
        text = """### 31 January
Mars was observed.
To test the quadrants, Aldebaran was observed.
| Reading | Value |
|---|---|
| Declination | 15 38 |
| | 15 37¾ |
"""
        rows = extract_text(
            text, "book", dict(year=1596, volume=13, _include_record_ids={"book:6:2"})
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["target"], "other")
        self.assertEqual(rows[0]["magnitude_arcsec"], "56280")

    def test_later_clock_on_a_prose_line_does_not_retime_an_earlier_declination(self):
        rows = self.extract("""### 26 April
Mars was observed.
At H.9 M.50 it was observed.
Declination of Mars, north, was 16° 8½′. At H.10 M.25 the star was on the meridian.
""")
        self.assertEqual(rows[0]["time_key"], "35400")

    def test_hemisphere_after_a_prose_value_is_preserved(self):
        rows = self.extract("### 12 November\nMars was observed.\n- Declination of ♂ `23 7` B\n")
        self.assertEqual(rows[0]["arcsec"], "83220")
        self.assertEqual(rows[0]["hemisphere_basis"], "explicit_label_or_value")

    def test_explicit_hms_in_a_table_description_sets_the_clock(self):
        rows = self.extract("""### 5 March
Mars was observed.
| Reading | Value |
|---|---|
| H. 7 M. 14⅔ Distance of Mars from Aries | 42 8⅚ |
| Declination of Mars | 23 17⅓ |
""")
        self.assertEqual(rows[0]["time_key"], "26080")

    def test_seconds_in_a_prose_clock_are_not_dropped(self):
        rows = self.extract(
            "### 5 March\nMars was observed.\nH. 7 M. 2 S. 20, declination of Mars 1° 15½′.\n"
        )
        self.assertEqual(rows[0]["time_key"], "25340")

    def test_separate_bare_corrected_clock_row_keeps_both_clock_associations(self):
        rows = self.extract("""### 16 January
| H. M. | Distance of Mars | Declination of Mars |
|---|---|---|
| { 6 21⅓ | 19 48¼ | |
| { 6 8 corr. | | |
| | | 19 40 |
""")
        self.assertEqual(rows[0]["time_key"], "22080")
        self.assertEqual(rows[0]["time_match_key"], "22880")

    def test_explicit_at_clock_in_prose_does_not_inherit_a_previous_table_time(self):
        rows = self.extract(
            "### 17 May\nMars was observed.\nAt 11 30, declination of ♂ B. 12° 38½′.\n"
        )
        self.assertEqual(rows[0]["time_key"], "41400")

    def test_meridian_transit_description_allows_afterwards_before_mars(self):
        rows = self.extract("""### 16 January
| H. M. | Distance of Mars | Declination of Mars |
|---|---|---|
| 6 34 | 15 45⅙ | |
| 6 51⅙ Afterwards ♂ crossed the meridian, having an altitude | | |
| Declination of Mars | | 19 40 |
""")
        self.assertEqual(rows[0]["time_key"], "24670")

    def test_meridian_altitude_reduction_keeps_a_derived_role(self):
        rows = self.extract("""### 12 February
Mars was observed.
The meridian altitude gives a declination of 12° 27′.
""")
        self.assertEqual(rows[0]["role"], "derived")

    def test_time_of_day_subheading_keeps_its_date(self):
        rows = self.extract("""### 4 March
Mars was observed.
#### After noon
| Time | Declination of Mars |
|---|---|
| 7^h^ 22^m^ | 4° 47¾′ |
""")
        self.assertEqual(rows[0]["date"], "1589-03-04")

    def test_same_day_heading_and_following_morning_keep_explicit_dates(self):
        rows = self.extract("""### 3 March
Mars was observed.
#### On the same day, 3 March, P. M.
| Time | Declination of Mars |
|---|---|
| 7^h^ 48^m^ | 4° 38′ |

#### On 4 March
#### The following morning
| Time | Declination of Mars |
|---|---|
| 7^h^ 22^m^ | 4° 47¾′ |
""")
        self.assertEqual([r["date"] for r in rows], ["1589-03-03", "1589-03-04"])

    def test_explicit_day_of_current_month_can_return_to_a_previous_day(self):
        rows = self.extract("""### 5 March
Mars was observed.
#### On this day, the 4th, at 13½^h^ P. M.
| Time | Declination of Mars |
|---|---|
| 7^h^ 22^m^ | 4° 47¾′ |
""")
        self.assertEqual(rows[0]["date"], "1589-03-04")


if __name__ == "__main__":
    unittest.main()
