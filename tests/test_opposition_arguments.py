import copy
import hashlib
import unittest

from src.catalog import compile_catalogue, normalize_quantity
from src.public_checkpoint import public_assertion


class OppositionArgumentsTests(unittest.TestCase):
    def row(self, quantity, components, **extra):
        row = dict(
            id="assertion-v12-" + "b" * 20,
            volume=12,
            printed_page=305,
            quantity=quantity,
            components=components,
            subject="Mars",
            reference=None,
            direction=None,
            role="historical_input",
            flags=["not_an_additional_raw_reading"],
        )
        row.update(extra)
        row["normalized"] = normalize_quantity(row)
        return row

    def test_simple_planetary_longitude_retains_sexagenae_without_a_modern_frame(self):
        row = self.row(
            "calculation_angle",
            dict(sexagena="5", degree="10", arcminute="52", arcsecond="28"),
            argument_name="simple_planetary_longitude",
        )
        try:
            out = public_assertion(row)
        except ValueError as error:
            self.fail("Source planetary argument must export: " + str(error))
        self.assertEqual(out["normalized"]["magnitude"], "1119148")
        self.assertEqual(out["normalized"]["magnitude_degrees"], "279787/900")
        self.assertEqual(out["argument_name"], "simple_planetary_longitude")
        self.assertNotIn("zodiac_sign", out["normalized"])
        for name, role in (
            ("apogee_longitude", "historical_input"),
            ("prosthaphaeresis", "historical_input"),
            ("commutation_correction", "historical_correction"),
        ):
            argument = self.row(
                "calculation_angle",
                {"degree": "3", "arcminute": "17"},
                argument_name=name,
                role=role,
                **({"model_name": "Copernicus"} if name != "apogee_longitude" else {}),
            )
            self.assertEqual(public_assertion(argument)["argument_name"], name)
        for change in (
            {"quantity": "ecliptic_longitude"},
            {"role": "recorded_coordinate"},
            {"subject": "Sun"},
        ):
            bad = copy.deepcopy(row)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)

    def test_copernican_fourteenth_part_is_a_fractional_instruction(self):
        text = "Add the 14th part of Copernicus\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        source = dict(
            key="fraction",
            line=1,
            span_id="s",
            source_expression="14th part",
            quantity="correction_ratio",
            components={"ratio": "1/14"},
            subject="Mars",
            reference=None,
            direction=None,
            role="historical_correction",
            correction_ratio_kind="copernican_prosthaphaeresis_fraction",
            model_name="Copernicus",
            source_word_numbers={"14th part": "1/14"},
            flags=["not_an_additional_raw_reading"],
            unit_basis="Reviewed fractional-part instruction",
        )
        span = dict(id="s", volume=12, edition_sha256=sha, line_start=1, line_end=1)
        batch = dict(
            id="opposition",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis={"kind": "source_review", "printed_page": 305},
            span_decisions=[dict(span_id="s", decision="context", reason="Reviewed fraction")],
            assertions=[source],
            events=[],
        )
        try:
            compiled = compile_catalogue([batch], {12: text}, [span])["assertions"][0]
            out = public_assertion(compiled)
        except ValueError as error:
            self.fail("Reviewed fractional instruction must compile and export: " + str(error))
        self.assertEqual(out["normalized"]["magnitude"], "1/14")
        self.assertEqual(out["normalized"]["unit"], "ratio")
        self.assertEqual(out["model_name"], "Copernicus")
        for change in (
            {"model_name": "Prutenic"},
            {"role": "recorded_reading"},
            {"reference": "Sun"},
        ):
            bad = copy.deepcopy(compiled)
            bad.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                public_assertion(bad)
