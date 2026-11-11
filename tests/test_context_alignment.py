import unittest

from src.core import extract_text, compare_records


HEAD = '[QA: p. 58 opening. Running head: "1590" (centre) "44" (right)]\n### 4 March\n'


class ContextTests(unittest.TestCase):
    def test_page_continuation_keeps_schema_and_both_clock_readings(self):
        state = {}
        first = (
            HEAD
            + """Mars was observed.
| Time | Distance of Mars from Spica | Declination | Altitude | Star |
|---|---|---|---|---|
| 11^h^ 28^m^ | 20° 1′ | 27° 27′ | | |
"""
        )
        extract_text(first, "first", state)
        second = """[QA: p. 59 opening. Running head: "1590" (centre) "45" (right)]
| | | | | |
|---|---|---|---|---|
| 11 45½; corrected 11 47 [11 47 corr.] | Meridian altitude of Mars | | | |
| | | 27 27⅔ | | |
| | Distance from a comparison star | 27 27⅓ | | |
"""
        rows = extract_text(second, "second", state)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["magnitude_arcsec"], "98840")
        self.assertIn("42420", (rows[1]["time_key"], rows[1]["time_match_key"]))
        self.assertEqual(rows[1]["schema_basis"], "previous_page_same_date")

    def test_observation_table_ends_computation_context(self):
        text = (
            HEAD
            + """Calculation of the place of Mars.
| Line | Value |
|---|---|
| True declination of Mars | 9° 27′ |

| Time | Distance of Mars from Spica | Declination |
|---|---|---|
| 7^h^ 5^m^ | 30° 1′ | 9° 26′ |
"""
        )
        rows = extract_text(text, "test", {})
        self.assertIn("derived_or_editorial", rows[0]["flags"])
        self.assertNotIn("derived_or_editorial", rows[1]["flags"])

    def test_bare_time_and_corrected_time_keep_original_group(self):
        text = (
            HEAD
            + """Mars was observed.
| | | |
|---|---|---|
| 7 5½ | Altitude of Mars | 8° 43′ |
| | Declination of Mars | 24° 48′ |

| Time | Distance of Mars from Spica | Declination |
|---|---|---|
| 6^h^ 19^m^ 30^s^ | 30° 1′ | 19° 3′ |
| 7^h^ 21^m^ corrected [corr.] | | 19° 0⅓′ |
"""
        )
        rows = extract_text(text, "test", {})
        self.assertEqual(rows[0]["time_key"], "25530")
        self.assertEqual(rows[2]["time_match_key"], rows[1]["time_key"])
        self.assertEqual(rows[2]["time_key"], "26460")

    def test_local_mars_subject_and_transit_time_survive_table_break(self):
        text = (
            HEAD
            + """Mars was observed.
| Hours, minutes | Distance of Mars from Spica | Declination | Altitude |
|---|---|---|---|
| 8^h^ 23^m^ | 30° 1′ | 10° 32′ | 20° 1′ |
| 9^h^ 5⅓^m^ | Mars crossed the meridian | | |

| | | |
|---|---|---|
| by the steel instrument | 23° 34′ | |
| Declination [Decl.] | 10° 32′ with both | 49 16 |
"""
        )
        rows = extract_text(text, "test", {})
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["time_key"], "32720")
        self.assertEqual(rows[1]["magnitude_arcsec"], "37920")

    def test_context_sign_does_not_cross_date_or_target(self):
        text = (
            HEAD
            + """| Time | Declination of Mars, north |
|---|---|
| 7^h^ 0^m^ | 9° 26′ |

| Time | Declination of Mars |
|---|---|
| 8^h^ 0^m^ | 9° 27′ |

### 5 March
| Time | Declination of Mars |
|---|---|
| 7^h^ 0^m^ | 9° 28′ |
"""
        )
        rows = extract_text(text, "test", {})
        self.assertEqual(rows[1]["arcsec"], "34020")
        self.assertEqual(rows[1]["hemisphere_basis"], "same_date_context")
        self.assertIsNone(rows[2]["arcsec"])

    def test_other_star_and_derived_readings_stay_separate(self):
        text = (
            HEAD
            + """Mars was observed.
| Time | Distance of Mars from Spica | Declination of Spica |
|---|---|---|
| 7^h^ 0^m^ | 30° 1′ | 9° 26′ |

Calculation of the place of Mars.
| Line | Value |
|---|---|
| True declination of Mars, south | 9° 27′ |
"""
        )
        rows = extract_text(text, "test", {})
        self.assertEqual(len(rows), 1)
        self.assertIn("derived_or_editorial", rows[0]["flags"])


def record(identifier, value, **extra):
    return dict(
        id=identifier,
        page=44,
        date="1590-03-04",
        time_key="25500",
        arcsec=value,
        magnitude_arcsec=value,
        flags=[],
        **extra,
    )


class AlignmentTests(unittest.TestCase):
    def test_corrected_clock_group_cannot_steal_raw_clock_readings(self):
        ps = [record("p1", "100"), record("p2", "200"), record("p3", "300")]
        ps[0]["time_key"] = "100"
        ps[1]["time_key"] = ps[2]["time_key"] = "200"
        rs = [record("s1", "100"), record("s2", "200")]
        for r in rs:
            r.update(time_key="100", time_match_key="200")
        results = compare_records(ps, rs)
        self.assertTrue(all(r["status"] == "ambiguous" for r in results))

    def test_repeated_readings_align_by_order_even_when_numbers_disagree(self):
        pafko = [record("p1", "100"), record("p2", "200")]
        source = [record("s1", "200"), record("s2", "100")]
        results = compare_records(pafko, source)
        self.assertEqual([r["candidate_ids"] for r in results], [["s1"], ["s2"]])
        self.assertEqual([r["status"] for r in results], ["disagreement", "disagreement"])
        self.assertEqual(results[0]["alignment_basis"], "time_group_printed_order")

    def test_unequal_groups_remain_ambiguous(self):
        results = compare_records([record("p1", "100")], [record("s1", "100"), record("s2", "200")])
        self.assertEqual(results[0]["status"], "ambiguous")

    def test_quote_agreement_and_conversion_conflict_are_separate(self):
        p = record(
            "p1",
            "-33960",
            quote="Decl. [MS] B. 9 26",
            quote_magnitude_arcsec="33960",
            converted_degrees=-9.433333333333334,
        )
        s = record("s1", "33960")
        result = compare_records([p], [s])[0]
        self.assertEqual(result["status"], "exact")
        self.assertEqual(result["conversion_status"], "sign_conflict")

    def test_unsigned_agreement_is_not_signed_validation(self):
        p = record("p1", "-33960", quote="9 26", quote_magnitude_arcsec="33960")
        s = record("s1", None)
        s["magnitude_arcsec"] = "33960"
        s["flags"] = ["hemisphere_unresolved"]
        result = compare_records([p], [s])[0]
        self.assertEqual(result["status"], "magnitude_agreement")
        self.assertEqual(result["hemisphere_status"], "unresolved")


if __name__ == "__main__":
    unittest.main()
