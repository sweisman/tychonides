import unittest

from src.catalog_enrichment import derived_fields, page_url


class DerivedValuesTests(unittest.TestCase):
    def test_signed_declination_has_separate_magnitude_and_sign(self):
        payload = {
            "derived_normalization": {
                "magnitude": "-1515824/25",
                "unit": "arcsecond",
                "method": "JPL_fixed_width_conversion",
            }
        }
        result = derived_fields(payload)
        self.assertEqual(result["derived_value_exact"], "1515824/25")
        self.assertEqual(result["derived_signed_value_exact"], "-1515824/25")
        self.assertEqual(result["derived_unit"], "arcsecond")
        self.assertEqual(payload["derived_normalization"]["magnitude"], "-1515824/25")

    def test_epoch_and_clock_keep_their_scales(self):
        epoch = derived_fields(
            {
                "time_scale": "UT_as_documented",
                "derived_normalization": {
                    "magnitude": "1234567/10",
                    "unit": "julian_day",
                    "method": "JPL_fixed_width_conversion",
                },
            }
        )
        self.assertEqual(epoch["derived_time_scale"], "UT_as_documented")
        clock = derived_fields(
            {
                "time_scale": "EDT",
                "derived_normalization": {
                    "timestamp": "2003-09-17T01:00:00+00:00",
                    "method": "source_EDT_UTC_minus_4",
                },
            }
        )
        self.assertEqual(clock["derived_time_scale"], "UTC")
        self.assertIsNone(clock["derived_value_exact"])

    def test_incomplete_coordinate_does_not_get_invented_value(self):
        self.assertIsNone(
            derived_fields({"normalized": {"magnitude": None}})["derived_value_exact"]
        )

    def test_pdf_locator_uses_explicit_index_not_printed_page(self):
        source = {"url": "https://example.org/report.pdf"}
        self.assertEqual(page_url(source, "PDF page 15, row 3"), source["url"] + "#page=15")
        self.assertIsNone(page_url(source, None, 15))
