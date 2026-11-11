import unittest


class PublicDerivationTests(unittest.TestCase):
    def module(self):
        from src import public_checkpoint

        return public_checkpoint

    def fixture(self):
        ids = ["assertion-v12-" + c * 20 for c in "abc"]
        assertions = [
            dict(id=aid, normalized=dict(status="exact", unit="arcsecond", magnitude=value))
            for aid, value in zip(ids, ["87765", "80", "87690"], strict=True)
        ]
        row = dict(
            id="derivation-v12-" + "d" * 20,
            operation="difference",
            input_ids=ids[:2],
            output_id=ids[2],
            computed_magnitude="87685",
            arithmetic_agrees=False,
            text_original="PRIVATE",
            private_source="/private",
        )
        return row, {r["id"]: r for r in assertions}

    def test_historical_disagreement_is_published_without_changing_output(self):
        row, assertions = self.fixture()
        result = self.module().public_derivation(row, assertions)
        self.assertFalse(result["arithmetic_agrees"])
        self.assertEqual(result["computed_magnitude"], "87685")
        self.assertEqual(assertions[row["output_id"]]["normalized"]["magnitude"], "87690")
        self.assertNotIn("PRIVATE", str(result))
        self.assertNotIn("private_source", result)

    def test_tampered_calculations_missing_targets_and_units_fail_closed(self):
        row, assertions = self.fixture()
        for change in (
            dict(computed_magnitude="87690"),
            dict(arithmetic_agrees=True),
            dict(output_id="missing"),
        ):
            candidate = dict(row, **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.module().public_derivation(candidate, assertions)
        assertions[row["input_ids"][0]]["normalized"]["unit"] = "second_of_time"
        with self.assertRaises(ValueError):
            self.module().public_derivation(row, assertions)

    def test_unspecified_historical_algorithms_remain_uncomputed(self):
        row, assertions = self.fixture()
        row.update(
            operation="historical_adoption_unspecified",
            computed_magnitude=None,
            arithmetic_agrees=None,
        )
        result = self.module().public_derivation(row, assertions)
        self.assertIsNone(result["computed_magnitude"])
        self.assertIsNone(result["arithmetic_agrees"])
        row["computed_magnitude"] = "87685"
        with self.assertRaises(ValueError):
            self.module().public_derivation(row, assertions)
