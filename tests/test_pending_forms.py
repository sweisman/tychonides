import unittest
from src.core import extract_text


class PendingFormsTests(unittest.TestCase):
    def extract(self, text):
        return extract_text(
            "### 16 January\nMars was observed.\n" + text, "book", dict(year=1587, volume=11)
        )

    def test_editorial_at_does_not_hide_observation_prose(self):
        rows = self.extract("[At] 4^h^ 51^m^, declination of ♂ 1° 21′ north with a single pinnule.")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["time_key"], "17460")
        self.assertEqual(rows[0]["arcsec"], "4860")

    def test_local_fractional_prose_clock_overrides_previous_table_clock(self):
        rows = self.extract("""| Time | Distance of Mars | Declination |
|---|---|---|
| 8^h^ 10^m^ | 30° 1′ | |

For deriving its parallax. At 8¾^h^ the declination of ♂ was 3° 29⅔′, twice.
""")
        self.assertEqual(rows[0]["time_key"], "31500")

    def test_declination_cell_can_also_report_a_separate_altitude(self):
        rows = self.extract("""| Time | Reading | Value |
|---|---|---|
| 5^h^ 12⅔^m^ | Declination of Mars, north | 1° 21½′. Altitude 25° 30′ |
""")
        self.assertEqual([r["arcsec"] for r in rows], ["4890"])

    def test_repeated_label_keeps_declination_quantity(self):
        rows = self.extract("""| Time | Reading | Value |
|---|---|---|
| 10^h^ 43^m^ | Declination of Mars, north | 6° 25′ |
| | Repeated | 6° 25′ |
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["23100", "23100"])

    def test_second_pinnule_in_prose_and_temporary_separation_column(self):
        rows = self.extract("""| Time | Declination of Mars, north |
|---|---|
| 4^h^ 16^m^ | 9° 6½′ |
| | Between Mars and Regulus, by the sextant |
| 4^h^ 28^m^ | 16° 14′ |

Repeated declination of Mars, north: 9° 5½′; with the other: 9° 5′.
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["32790", "32730", "32700"])

    def test_reference_star_annotation_does_not_relabel_a_separate_declination_column(self):
        rows = self.extract("""| Time | Distance of Mars | Declination | Orion east |
|---|---|---|---|
| 6 51⅙ Afterwards Mars crossed the meridian | | | |
| The bright star of Orion was then at | | | 36 3 |
| | | 19 40 | |
| | | 19 40⅓ | |
""")
        self.assertEqual([r["magnitude_arcsec"] for r in rows], ["70800", "70820"])

    def test_uppercase_unit_tags_preserve_the_recorded_clock(self):
        rows = self.extract("""| Time | Reading | Value |
|---|---|---|
| 6^H^11½^M^ corr. | Declination of Mars | 21 4¼ B. |
""")
        self.assertEqual(rows[0]["time_key"], "22290")

    def test_named_night_heading_resets_prior_date_and_clock(self):
        rows = self.extract("""| Time | Declination of Mars |
|---|---|
| 12^h^ 30^m^ | 20° 1′ |

**Nocte quæ præceßit 20 Januarij.** [The night that preceded 20 January]

| | |
|---|---|
| Declination of Mars | 21°26′40″B. |
""")
        self.assertEqual(rows[-1]["date"], "1587-01-20")
        self.assertIsNone(rows[-1]["time_key"])

    def test_source_bound_column_review_recovers_a_specific_unlabelled_reading(self):
        text = "### 16 January\nMars was observed.\n| Time | Distance | Value |\n|---|---|---|\n| 7^h^ | 30° 1′ | 12° 10′ |\n"
        self.assertEqual(extract_text(text, "book", dict(year=1587)), [])
        rows = extract_text(text, "book", dict(year=1587, _include_record_ids={"book:5:3"}))
        self.assertEqual([r["id"] for r in rows], ["book:5:3"])
        self.assertEqual(rows[0]["magnitude_arcsec"], "43800")
        self.assertEqual(rows[0]["extraction_basis"], "source_bound_review_column")

    def test_clock_in_a_date_heading_applies_to_its_reduction(self):
        rows = self.extract("""On 15 April at H.9 50, the distance between Mars and Gemini was taken.

| | |
|---|---|
| Declination of Mars | 17 38¾ |
""")
        self.assertEqual(rows[0]["date"], "1587-04-15")
        self.assertEqual(rows[0]["time_key"], "35400")

    def test_explicit_same_day_phase_heading_retains_the_named_date(self):
        rows = self.extract("""#### On the same day, P. M.
| Time | Declination of Mars |
|---|---|
| 15^h^ 52^m^ | 1° 23′ 25″ |

#### In the evening of the same day
| Time | Declination of Mars |
|---|---|
| 7^h^ 55^m^ | 4° 5¼′ |
""")
        self.assertEqual([r["date"] for r in rows], ["1587-01-16", "1587-01-16"])


if __name__ == "__main__":
    unittest.main()
