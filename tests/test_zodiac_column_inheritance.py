import copy
import hashlib
import unittest

from src.catalog import compile_catalogue
from src.public_checkpoint import public_assertion, validate_links


class ZodiacColumnInheritanceTests(unittest.TestCase):
    def test_same_ephemeris_statement_can_share_an_explicit_sign_between_bodies(self):
        text = "According to Stadius: Moon 5°0′ ♋ and Mars 3°16′.\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        common = dict(
            line=1,
            span_id="s",
            quantity="ecliptic_longitude",
            role="historical_prediction",
            reference=None,
            model_name="Stadius",
            zodiac_sign="Cancer",
            context_keys=["statement"],
            flags=["not_an_additional_raw_reading"],
            unit_basis="Same reviewed ephemeris statement",
        )
        parent = dict(
            common,
            key="moon",
            subject="Moon",
            source_expression="5°0′ ♋",
            components={"degree": "5", "arcminute": "0"},
        )
        child = dict(
            common,
            key="mars",
            subject="Mars",
            source_expression="3°16′",
            components={"degree": "3", "arcminute": "16"},
            zodiac_sign_inherited_from_key="moon",
            zodiac_inheritance_kind="same_ephemeris_statement",
        )
        batch = dict(
            id="review",
            volume=10,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="final_edition_review", printed_page=5),
            assertions=[parent, child],
            events=[],
            contexts=[
                dict(
                    key="statement",
                    kind="source_observation_context",
                    lines=[1],
                    value="Stadius statement",
                )
            ],
            span_decisions=[
                dict(span_id="s", decision="include", reason="Named ephemeris statement")
            ],
        )
        spans = [dict(id="s", volume=10, edition_sha256=sha, line_start=1, line_end=1)]
        out = compile_catalogue([batch], {10: text}, spans)
        a = next(x for x in out["assertions"] if x["key"] == "mars")
        self.assertEqual(a["normalized"]["zodiac_longitude_degrees"], "1399/15")
        self.assertEqual(a["source_expression"], "3°16′")
        public = [public_assertion(x) for x in out["assertions"]]
        validate_links(public, [])
        from src.assembly import assemble

        self.assertEqual(len(assemble({10: text}, out["assertions"], [], [], [])["items"]), 2)
        self.assertEqual(
            next(x for x in public if x["id"] == a["id"])["zodiac_inheritance_kind"],
            "same_ephemeris_statement",
        )
        bad_public = copy.deepcopy(public)
        next(x for x in bad_public if x["id"] != a["id"])["subject"] = "Mars"
        with self.assertRaises(ValueError):
            validate_links(bad_public, [])
        for changes in (
            dict(model_name="Carelli"),
            dict(zodiac_inheritance_kind=None),
            dict(subject="Spica"),
            dict(column=1),
            dict(context_keys=[]),
        ):
            bad = copy.deepcopy(batch)
            bad["assertions"][1].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                compile_catalogue([bad], {10: text}, spans)

    def test_same_row_correction_inherits_sign_only_from_its_linked_original(self):
        text = "| 4°20′ ♋ | Corr. | 4 15² |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="s", volume=13, edition_sha256=sha, line_start=1, line_end=1)
        common = dict(
            line=1,
            span_id="s",
            quantity="ecliptic_longitude",
            subject="Mars",
            reference=None,
            zodiac_sign="Cancer",
            unit_basis="Correction of same row longitude",
            context_keys=["row"],
            flags=["not_an_additional_raw_reading"],
        )
        original = dict(
            common,
            key="original",
            column=1,
            role="reduction",
            source_expression="4°20′ ♋",
            components={"degree": "4", "arcminute": "20"},
        )
        corrected = dict(
            common,
            key="corrected",
            column=3,
            role="printed_correction",
            source_expression="4 15²",
            source_note_marker_original="²",
            components={"degree": "4", "arcminute": "15"},
            variant_of_key="original",
            zodiac_sign_inherited_from_key="original",
        )
        batch = dict(
            id="review",
            volume=13,
            edition_sha256=sha,
            line_start=1,
            line_end=1,
            interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=112),
            assertions=[original, corrected],
            events=[],
            contexts=[
                dict(key="row", kind="column_scope", lines=[1], value="Original and correction")
            ],
            span_decisions=[dict(span_id="s", decision="include", reason="Same row correction")],
        )
        result = compile_catalogue([batch], {13: text}, [span])
        out = {r["key"]: r for r in result["assertions"]}
        self.assertEqual(out["corrected"]["normalized"]["zodiac_longitude_degrees"], "377/4")
        self.assertEqual(out["corrected"]["variant_of_id"], out["original"]["id"])
        public = [public_assertion(r) for r in result["assertions"]]
        validate_links(public, [])
        for changes in (
            dict(variant_of_key=None),
            dict(column=1),
            dict(role="historical_input"),
            dict(context_keys=[]),
            dict(zodiac_sign="Aries"),
        ):
            bad = copy.deepcopy(batch)
            bad["assertions"][1].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                compile_catalogue([bad], {13: text}, [span])

    def fixture(self):
        text = "| 1° ♓ | 2° ♈ |\n| 3° | 4° |\n"
        sha = hashlib.sha256(text.encode()).hexdigest()
        span = dict(id="column-span", volume=12, edition_sha256=sha, line_start=1, line_end=2)
        assertions = []
        for key, line, column, expr, sign, model, origin in [
            ("first-a", 1, 1, "1° ♓", "Pisces", "Copernicus", None),
            ("first-b", 1, 2, "2° ♈", "Aries", "Alphonsine", None),
            ("later-a", 2, 1, "3°", "Pisces", "Copernicus", "first-a"),
            ("later-b", 2, 2, "4°", "Aries", "Alphonsine", "first-b"),
        ]:
            a = dict(
                key=key,
                line=line,
                column=column,
                span_id=span["id"],
                source_expression=expr,
                quantity="ecliptic_longitude",
                role="historical_prediction",
                subject="Mars",
                reference=None,
                model_name=model,
                zodiac_sign=sign,
                components={"degree": str(line + column - 1 if line == 1 else column + 2)},
                unit_basis="Reviewed separate longitude columns",
                context_keys=["columns"],
                flags=["not_an_additional_raw_reading"],
            )
            if origin:
                a["zodiac_sign_inherited_from_key"] = origin
            assertions.append(a)
        batch = dict(
            id="column-review",
            volume=12,
            edition_sha256=sha,
            line_start=1,
            line_end=2,
            interval_sha256=hashlib.sha256("\n".join(text.splitlines()).encode()).hexdigest(),
            basis=dict(kind="source_review", printed_page=291),
            span_decisions=[
                dict(
                    span_id=span["id"], decision="include", reason="Separate column scopes reviewed"
                )
            ],
            contexts=[
                dict(
                    key="columns",
                    kind="column_scope",
                    lines=[1, 2],
                    value="Two independently labelled columns",
                )
            ],
            assertions=assertions,
            events=[],
        )
        return text, [span], batch

    def test_inherited_sign_retains_literal_expression_and_column_origin(self):
        text, spans, batch = self.fixture()
        r = compile_catalogue([batch], {12: text}, spans)
        bykey = {a["key"]: a for a in r["assertions"]}
        later = bykey["later-a"]
        self.assertEqual(later["source_expression"], "3°")
        self.assertEqual(later.get("zodiac_sign_inherited_from_id"), bykey["first-a"]["id"])
        self.assertEqual(later["normalized"]["zodiac_longitude_degrees"], "333")
        public = [public_assertion(a) for a in r["assertions"]]
        self.assertEqual(
            next(a for a in public if a["id"] == later["id"]).get("zodiac_sign_inherited_from_id"),
            bykey["first-a"]["id"],
        )
        validate_links(public, [])

    def test_unreviewed_cross_column_role_or_sign_inheritance_is_rejected(self):
        text, spans, batch = self.fixture()
        for change in (
            {"zodiac_sign_inherited_from_key": "first-b"},
            {"zodiac_sign_inherited_from_key": "later-a"},
            {"zodiac_sign_inherited_from_key": "missing"},
            {"column": 2},
            {"role": "historical_input"},
            {"zodiac_sign": "Aries"},
            {"context_keys": []},
        ):
            bad = copy.deepcopy(batch)
            bad["assertions"][2].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                compile_catalogue([bad], {12: text}, spans)
        bad = copy.deepcopy(batch)
        del bad["assertions"][2]["zodiac_sign_inherited_from_key"]
        with self.assertRaises(ValueError):
            compile_catalogue([bad], {12: text}, spans)

    def test_public_origin_must_resolve_to_the_same_model_and_sign(self):
        text, spans, batch = self.fixture()
        r = compile_catalogue([batch], {12: text}, spans)
        public = [public_assertion(a) for a in r["assertions"]]
        bykey = {a["key"]: a for a in r["assertions"]}
        first = bykey["first-a"]["id"]
        later = bykey["later-a"]["id"]
        with self.assertRaises(ValueError):
            validate_links([a for a in public if a["id"] != first], [])
        for change in ({"model_name": "Alphonsine"}, {"zodiac_sign_inherited_from_id": later}):
            bad = copy.deepcopy(public)
            next(a for a in bad if a["id"] == first).update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_links(bad, [])
