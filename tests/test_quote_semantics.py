import unittest
from src.comparison import audit_conversion, quote_sign


class QuoteSemanticsTests(unittest.TestCase):
    def test_meridian_altitude_modifier_cannot_supply_the_declination_hemisphere(self):
        self.assertIsNone(quote_sign("Declin. ex alt. m. 5 35 15"))
        self.assertIsNone(quote_sign("Declin. ex alt. merid. 5 35 15"))
        self.assertIsNone(quote_sign("Declin. ex altit. merid. 11 18"))
        self.assertEqual(quote_sign("Declin. M. 5 35 15"), -1)
        self.assertEqual(quote_sign("Declin. Merid. 12 2 40"), -1)
        p = dict(quote="Declin. ex alt. m. 5 35 15", quote_magnitude_arcsec="20115", arcsec="20115")
        self.assertEqual(audit_conversion(p), "magnitude_consistent_sign_unresolved")

    def test_unsigned_quote_does_not_hide_numeric_sign_conflict_with_the_source(self):
        from src.core import compare_records

        p = dict(
            id="p",
            volume=12,
            page=44,
            date="1590-03-04",
            time_key="100",
            quote="9 26",
            quote_magnitude_arcsec="33960",
            arcsec="-33960",
        )
        source = dict(
            id="s",
            volume=12,
            page=44,
            date="1590-03-04",
            time_key="100",
            magnitude_arcsec="33960",
            arcsec="33960",
            flags=[],
            hemisphere_basis="explicit_label_or_value",
        )
        row = compare_records([p], [source])[0]
        self.assertEqual(row["status"], "magnitude_agreement")
        self.assertEqual(row["conversion_status"], "magnitude_consistent_sign_unresolved")
        self.assertEqual(row["numeric_source_sign_status"], "conflict")
        self.assertEqual(row["source_hemisphere_basis"], "explicit_label_or_value")

    def test_clock_m_in_prose_cannot_override_an_explicit_northern_declination(self):
        from src.core import extract_text

        rows = extract_text(
            "### 14 January\nMars was observed.\nAt H.4⅔ P. M. N., its declination B. would have been16° 27′ 6″.\n",
            "book",
            dict(year=1585, volume=10),
        )
        self.assertEqual(rows[0]["arcsec"], "59226")

    def test_direction_adjective_immediately_before_declination_is_retained(self):
        from src.core import extract_text

        rows = extract_text(
            "### 14 January\nMars was observed.\nThe southern declination of Mars was16° 27′.\n",
            "book",
            dict(year=1585, volume=10),
        )
        self.assertEqual(rows[0]["arcsec"], "-59220")
        self.assertEqual(rows[0]["hemisphere_basis"], "explicit_label_or_value")

    def test_prose_instrument_orientation_does_not_supply_a_hemisphere(self):
        from src.core import extract_text

        rows = extract_text(
            "### 14 January\nMars was observed.\nDeclination of Mars was16° 27′ by the southern armillae.\n",
            "book",
            dict(year=1585, volume=10),
        )
        self.assertIsNone(rows[0]["arcsec"])

    def test_prose_explicit_hemisphere_can_scope_the_next_same_day_reading(self):
        from src.core import extract_text

        rows = extract_text(
            "### 14 January\nMars was observed.\nDeclination of ♂23° 7′ B.\nDeclination of ♂23° 8′.\n",
            "book",
            dict(year=1585, volume=10),
        )
        self.assertEqual(rows[1]["arcsec"], "83280")
        self.assertEqual(rows[1]["hemisphere_basis"], "same_date_context")


if __name__ == "__main__":
    unittest.main()
