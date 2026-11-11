import unittest
from src.core import compare_records


def reading(identifier, clock, value, **other):
    return dict(
        id=identifier, volume=12, page=44, date="1590-03-04", time_key=clock, arcsec=value, **other
    )


class OrderAlignmentTests(unittest.TestCase):
    def test_anchor_interval_excludes_an_untimed_row_before_the_interval(self):
        ps = [reading("p1", "100", "1"), reading("p2", "200", "2"), reading("p3", "300", "3")]
        rs = [
            reading("extra", None, "99"),
            reading("r1", "100", "1"),
            reading("r2", None, "22"),
            reading("r3", "300", "3"),
        ]
        results = compare_records(ps, rs)
        self.assertEqual(results[1]["candidate_ids"], ["r2"])
        self.assertEqual(results[1]["status"], "disagreement")

    def test_neighbouring_clock_anchors_disambiguate_same_time_readings(self):
        ps = [
            reading("p1", "100", "1"),
            reading("p2", "200", "2"),
            reading("p3", "200", "3"),
            reading("p4", "300", "4"),
        ]
        rs = [
            reading("r0", "50", "5"),
            reading("r1", "100", "1"),
            reading("r2", "200", "200"),
            reading("r3", "200", "300"),
            reading("r4", "300", "4"),
        ]
        result = compare_records(ps, rs)
        self.assertEqual([r["candidate_ids"] for r in result], [["r1"], ["r2"], ["r3"], ["r4"]])
        self.assertEqual(
            [r["status"] for r in result], ["exact", "disagreement", "disagreement", "exact"]
        )

    def test_equal_metadata_with_an_extra_source_row_stays_ambiguous(self):
        ps = [reading("p1", "100", "1"), reading("p2", "100", "2")]
        rs = [reading("r1", "100", "1"), reading("r2", "100", "2"), reading("r3", "100", "999")]
        self.assertTrue(all(r["status"] == "ambiguous" for r in compare_records(ps, rs)))

    def test_conflicting_clock_is_not_hidden_by_printed_order(self):
        ps = [reading("p1", "100", "1")]
        rs = [reading("r1", "300", "1")]
        self.assertEqual(compare_records(ps, rs)[0]["status"], "unmatched")

    def test_scan_identity_is_an_order_anchor_for_neighbouring_records(self):
        ps = [reading("p1", None, "1"), reading("p2", None, "2"), reading("p3", None, "3")]
        rs = [
            reading("extra", None, "99"),
            reading("r1", None, "1"),
            reading("r2", None, "2"),
            reading("r3", None, "3"),
        ]
        result = compare_records(ps, rs, {"p2": "r2"})
        self.assertEqual(result[0]["status"], "ambiguous")
        self.assertEqual(result[2]["candidate_ids"], ["r3"])
        self.assertEqual(result[2]["status"], "exact")

    def test_crossing_reviewed_identities_do_not_silently_reorder_a_volume(self):
        ps = [reading("p1", None, "1"), reading("p2", None, "2")]
        rs = [reading("r1", None, "1"), reading("r2", None, "2")]
        with self.assertRaises(ValueError):
            compare_records(ps, rs, {"p1": "r2", "p2": "r1"})


if __name__ == "__main__":
    unittest.main()
