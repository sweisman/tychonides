import copy
import unittest

from src import reviews


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.p = dict(
            id="p",
            volume=13,
            page=45,
            date="1596-01-31",
            time_key="25040",
            quote="Decl. 15 28",
            quote_magnitude_arcsec="55680",
            arcsec="55680",
        )
        self.r = dict(
            id="book:20:2",
            source="book",
            volume=13,
            page=45,
            date="1596-01-31",
            time_key=None,
            flags=["hemisphere_unresolved"],
            magnitude_arcsec="56280",
            arcsec=None,
            role="observation",
        )
        self.decision = dict(
            pafko_id="p",
            status="source_supports_translation_and_target_correction",
            evidence="Named calibration, first declination in its block.",
            source_scan_magnitude_arcsec="56280",
            verified_target="Aldebaran",
            verified_role="calibration",
            identity=dict(
                source_record_id="book:20:2",
                source_sha256="bookhash",
                workbook_sha256="workbookhash",
            ),
        )

    def apply(self, decisions=None, hashes=None, workbook="workbookhash"):
        return reviews.prepare_reviews(
            [self.p],
            [self.r],
            [self.decision] if decisions is None else decisions,
            {"book": "bookhash"} if hashes is None else hashes,
            workbook,
        )

    def test_review_identifies_calibration_without_changing_either_transcription(self):
        before = copy.deepcopy((self.p, self.r, self.decision))
        obs, links, accepted = self.apply()
        self.assertEqual(links, {"p": "book:20:2"})
        self.assertEqual(obs[0]["role"], "calibration")
        self.assertEqual(obs[0]["reviewed_target"], "Aldebaran")
        self.assertEqual((self.p, self.r, self.decision), before)
        from src.comparison import compare_records

        outcomes = compare_records([self.p], obs, links)
        catalogue = reviews.derived_catalogue([self.p], obs, outcomes, accepted)
        row = catalogue[0]
        self.assertEqual(row["preferred_magnitude_arcsec"], "56280")
        self.assertEqual(row["pafko_quote_magnitude_arcsec"], "55680")
        self.assertEqual(row["target"], "Aldebaran")
        self.assertEqual(row["mars_selection"], "excluded_other_target")
        self.assertEqual(row["comparison_status"], "disagreement")

    def test_changed_source_or_workbook_invalidates_identity(self):
        with self.assertRaises(ValueError):
            self.apply(hashes={"book": "changed"})
        with self.assertRaises(ValueError):
            self.apply(workbook="changed")

    def test_missing_source_identity_cannot_be_recovered_using_a_matching_value(self):
        self.decision["identity"]["source_record_id"] = "absent"
        with self.assertRaises(ValueError):
            self.apply()

    def test_legacy_magnitude_review_does_not_override_an_unmatched_record(self):
        del self.decision["identity"]
        obs, links, accepted = self.apply()
        self.assertEqual(links, {})
        row = reviews.derived_catalogue(
            [self.p], obs, [dict(pafko_id="p", status="unmatched", candidate_ids=[])], accepted
        )[0]
        self.assertIsNone(row["preferred_magnitude_arcsec"])
        self.assertEqual(row["mars_selection"], "review_required")

    def test_incomplete_outcomes_cannot_silently_drop_workbook_rows(self):
        with self.assertRaises(ValueError):
            reviews.derived_catalogue([self.p], [self.r], [], {})

    def test_reviewed_recorded_date_and_clock_do_not_overwrite_witness_metadata(self):
        self.p["date"] = "1596-02-01"
        self.r["date"] = None
        self.decision.update(verified_date="1596-01-31", verified_time_key="25040")
        obs, links, accepted = self.apply()
        from src.comparison import compare_records

        outcomes = compare_records([self.p], obs, links)
        row = reviews.derived_catalogue([self.p], obs, outcomes, accepted)[0]
        self.assertEqual(row["preferred_recorded_date"], "1596-01-31")
        self.assertEqual(row["preferred_recorded_time_key"], "25040")
        self.assertEqual(row["date_basis"], "source_scan_review")
        self.assertEqual(row["pafko_date"], "1596-02-01")
        self.assertIsNone(row["source_date"])
        self.assertEqual(row["date_status"], "unresolved")

    def test_review_can_find_no_clock_instead_of_accepting_a_forward_filled_clock(self):
        self.r["time_key"] = "32760"
        self.decision["verified_time_key"] = None
        obs, links, accepted = self.apply()
        from src.comparison import compare_records

        row = reviews.derived_catalogue(
            [self.p], obs, compare_records([self.p], obs, links), accepted
        )[0]
        self.assertEqual(row["source_time_key"], "32760")
        self.assertIsNone(row["preferred_recorded_time_key"])
        self.assertEqual(row["time_basis"], "source_scan_review")

    def test_reviewed_page_does_not_overwrite_the_provisional_page_map(self):
        self.r["page"] = 457
        self.decision["verified_page"] = 458
        obs, links, accepted = self.apply()
        from src.comparison import compare_records

        row = reviews.derived_catalogue(
            [self.p], obs, compare_records([self.p], obs, links), accepted
        )[0]
        self.assertEqual(row["source_page"], 457)
        self.assertEqual(row["preferred_source_page"], 458)
        self.assertEqual(row["page_basis"], "source_scan_review")
        from src.publication_export import public_records

        row["pafko_id"] = "Sheet1:812"
        exported = public_records([row], [])[0]
        self.assertEqual(exported["preferred_source_page"], 458)

    def test_printed_ellipsis_cannot_be_completed_from_workbook_numeric_cells(self):
        self.p.update(quote="17...", quote_magnitude_arcsec=None, arcsec="61200")
        self.r.update(magnitude_arcsec=None, arcsec=None, flags=["value_unresolved"])
        self.decision["source_scan_magnitude_arcsec"] = None
        obs, links, accepted = self.apply()
        from src.comparison import compare_records

        row = reviews.derived_catalogue(
            [self.p], obs, compare_records([self.p], obs, links), accepted
        )[0]
        self.assertEqual(row["pafko_converted_arcsec"], "61200")
        self.assertIsNone(row["preferred_magnitude_arcsec"])
        self.assertEqual(row["comparison_status"], "unresolved")


if __name__ == "__main__":
    unittest.main()
