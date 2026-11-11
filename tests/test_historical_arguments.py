import hashlib
import unittest

from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion, validate_links


class HistoricalArgumentTests(unittest.TestCase):
    def row(self):
        return dict(
            id="assertion-v12-" + "a" * 20,
            volume=12,
            printed_page=151,
            subject="Mars",
            reference=None,
            quantity="ecliptic_longitude",
            role="historical_input",
        )

    def test_sexagenae_are_sixty_degrees_and_keep_the_source_origin(self):
        row = self.row()
        row.update(
            components={"sexagena": "4", "degree": "26", "arcminute": "38"},
            source_longitude_origin="source_equinox",
            argument_name="equated_longitude",
        )
        row["normalized"] = normalize_quantity(row)
        self.assertEqual(row["normalized"]["magnitude"], "959880")
        self.assertEqual(row["normalized"]["magnitude_degrees"], "7999/30")
        result = public_assertion(row)
        self.assertEqual(result.get("source_longitude_origin"), "source_equinox")
        self.assertEqual(result.get("argument_name"), "equated_longitude")
        row["source_longitude_origin"] = "first_star_of_Aries"
        self.assertEqual(
            public_assertion(row).get("source_longitude_origin"), "first_star_of_Aries"
        )
        row["source_longitude_origin"] = "private frame note"
        with self.assertRaises(ValueError):
            public_assertion(row)
        row["zodiac_sign"] = "Sagittarius"
        with self.assertRaises(ValueError):
            normalize_quantity(row)

    def test_editorial_latitude_component_is_not_an_original_prediction(self):
        row = self.row()
        row.update(
            quantity="ecliptic_latitude",
            role="editorial_addition",
            model_name="Alphonsine",
            editorial_component_units=["arcminute"],
            flags=["source_editorial_computation"],
            components={"degree": "5", "arcminute": "4"},
        )
        row["normalized"] = normalize_quantity(row)
        result = public_assertion(row)
        self.assertEqual(result.get("model_name"), "Alphonsine")
        self.assertEqual(result.get("editorial_component_units"), ["arcminute"])
        row["role"] = "historical_prediction"
        with self.assertRaises(ValueError):
            public_assertion(row)

    def test_prediction_epoch_link_targets_a_calculation_epoch(self):
        text = "10h 2°"
        sha = hashlib.sha256(text.encode()).hexdigest()
        common = dict(line=1, span_id="s", reference=None, unit_basis="Explicit time and degree")
        epoch = dict(
            common,
            key="epoch",
            quantity="calculation_epoch",
            subject="calculation epoch",
            role="calculation_epoch",
            source_expression="10h",
            components={"hour": "10"},
        )
        prediction = dict(
            common,
            key="prediction",
            quantity="ecliptic_longitude",
            subject="Mars",
            role="historical_prediction",
            model_name="Prutenic",
            source_expression="2°",
            components={"degree": "2"},
            calculation_epoch_key="epoch",
        )
        batch = dict(
            id="review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=sha,
            basis=dict(kind="source_review", printed_page=151),
            assertions=[epoch, prediction],
            span_decisions=[
                dict(span_id="s", decision="include", reason="Shared prediction epoch")
            ],
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        rows = compile_catalogue([batch], {12: text}, [span])["assertions"]
        bykey = {r["key"]: r for r in rows}
        self.assertEqual(bykey["prediction"].get("calculation_epoch_id"), bykey["epoch"]["id"])
        out = [public_assertion(r) for r in rows]
        validate_links(out, [])
        self.assertEqual(
            next(r for r in out if r["role"] == "historical_prediction").get(
                "calculation_epoch_id"
            ),
            bykey["epoch"]["id"],
        )
        prediction["calculation_epoch_key"] = "prediction"
        with self.assertRaises(ValueError):
            compile_catalogue([batch], {12: text}, [span])
