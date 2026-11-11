import unittest
from src.core import extract_text


class InlineLabelTests(unittest.TestCase):
    def extract(self, text):
        return extract_text(text, "book", dict(year=1595, volume=12))

    def test_wrapped_calibration_label_does_not_create_or_displace_mars_readings(self):
        rows = self.extract("""### 25 October
Mars was observed.
| Time | Distance | Declination | Altitude |
|---|---|---|---|
| 6^h^ 10^m^ | 20° 17′ | 17° 32′ | 14° 17′ |
| | | 17° 34′ | |
| | The declination | 15° 41′ | Altitude of Aldebaran |
| | of Aldebaran | 15° 40⅓′ | 15° 30′ |
| 7^h^ 54^m^ | 20° 16′ | 17° 30½′ | Altitude of Mars |
| | | 17° 31′ | |
""")
        self.assertEqual(
            [r["magnitude_arcsec"] for r in rows], ["63120", "63240", "63030", "63060"]
        )
        self.assertTrue(all(r["column"] == 3 for r in rows))

    def test_altitude_transit_block_uses_a_declination_column_temporarily(self):
        rows = self.extract("""### 27 October
Mars was observed.
| Time | | Declination | Star west |
|---|---|---|---|
| 12^h^ 20^m^ | Mars crossed | | |
| | the meridian, having the altitude | | |
| | by the steel instrument | 51° 29⅓′ | |
| | by the revolving instrument | 51° 28¾′ | |
| | Declination of Mars | 17° 25⅙′ | |
| | | 17° 24½′ | |
| | The bright star of the jaw, west, was then | | 6 24 |
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["62710", "62670"])

    def test_inline_altitude_heading_prevents_a_false_parallel_declination(self):
        rows = self.extract("""### 29 June
| Time | Distance of Mars | Declination of Mars | |
|---|---|---|---|
| | Distance of Mars from Aries | | Altitude of Mars |
| 1^h^ 18^m^ | 50° 21′ | 10° 46′ | 16° 12′ |
| | | 10° 45⅔′ | |
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["38760", "38740"])

    def test_declination_label_in_first_column_does_not_turn_later_clocks_into_angles(self):
        rows = self.extract("""### 26 January
| H. M. | Distance of Mars | Declination of Mars |
|---|---|---|
| Declination of Mars | | 20 45 |
| | | 20 44¾ |
| Afterwards Mars from Gemini | | |
| 6 54⅔ | 39 58½ | 20 45 |
| | | 20 44¾ |
""")
        self.assertEqual([r["column"] for r in rows], [3, 3, 3, 3])

    def test_wrapped_subject_and_hemisphere_complete_a_vertical_declination_label(self):
        rows = self.extract("""### 29 January
Mars was observed.
| | | |
|---|---|---|
| Declination | 21 4 | |
| ♂ B. [north] | 21 4¾ | |
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["75840", "75885"])
        self.assertEqual(rows[1]["arcsec"], "75885")

    def test_inline_label_assigns_a_blank_value_column_beside_a_star_column(self):
        rows = self.extract("""### 27 November
Mars was observed.
| | | Pegasus west |
|---|---|---|
| 7^h^ 2^m^ 20^s^ | Mars crossed | |
| | through the meridian, having an altitude | |
| by the steel instrument | 32° 49½′ | |
| Declination of Mars, with one | 1° 15½′ | 37 0 |
| | 1° 15′ | |
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["4530", "4500"])
        self.assertTrue(all(r["column"] == 2 for r in rows))

    def test_explicit_value_position_overrides_an_inherited_schema(self):
        rows = self.extract("""### 6 December
| Time | Distance of Mars | Declination of Mars | Altitude |
|---|---|---|---|
| 8^h^ 30^m^ | 30° 1′ | 16° 25′ | |

| | | | |
|---|---|---|---|
| Declination of Mars by the armillae | 16° 25⅙′ | | |
| | 16° 25′ | | |
""")
        self.assertEqual([r["column"] for r in rows], [3, 2, 2])

    def test_label_does_not_assign_a_named_star_column_as_its_value(self):
        rows = self.extract("""### 3 January
| Corrected clock | Distance of Mars | | Orion east |
|---|---|---|---|
| 6^h^ 15½^m^ | 45° 51′ | Declination of Mars | 53 48 |
| 6^h^ 20^m^ | 45° 51⅔′ | 7° 45′ | |
| | | 7° 45½′ | |
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["27900", "27930"])
        self.assertTrue(all(r["column"] == 3 for r in rows))


if __name__ == "__main__":
    unittest.main()
