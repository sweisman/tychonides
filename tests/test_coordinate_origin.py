import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.normalization import normalize_quantity


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


class CoordinateOriginTests(unittest.TestCase):
    def case(self, canonical=False):
        text = "Taurus: 6° 54′"
        row = dict(
            id="q",
            key="q",
            source_id="book",
            review_id="r",
            line=1,
            quantity="ecliptic_longitude",
            role="historical_input",
            subject="Mars",
            reference=None,
            direction=None,
            source_expression="6° 54′",
            components={"degree": "6", "arcminute": "54"},
            context_ids=["c"],
        )
        row["normalized"] = normalize_quantity(row)
        value = dict(
            coordinate="ecliptic_longitude",
            zodiac_sign="Taurus",
            longitude_origin="start_of_named_sign",
            source_basis="Sign explicitly stated",
        )
        if canonical:
            value = dict(
                subject="Mars",
                zodiac_sign="Taurus",
                line_start=1,
                line_end=1,
                source_expression="Taurus",
            )
        context = dict(
            id="c",
            key="frame",
            source_id="book",
            review_id="r",
            kind="source_coordinate_frame",
            lines=[1],
            value=value,
            text_original=text,
        )
        proof = dict(
            id="origin-q",
            assertion_id="q",
            review_id="r",
            context_id="c",
            original_sha256=fingerprint(row),
            frame_sha256=fingerprint(context),
            reason="Project the explicitly reviewed source sign.",
            evidence=[dict(line=1, source_expression="Taurus")],
        )
        return text, row, context, proof

    def apply(self, row, contexts, proof, text):
        from src.coordinate_origin import apply_coordinate_origin_reviews

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / "coordinate_origin_reviews.json").write_text(
                json.dumps([proof]), encoding="utf-8"
            )
            return apply_coordinate_origin_reviews(
                work, {"assertions": [row], "contexts": contexts}, {"book": text}
            )

    def test_reviewed_named_sign_adds_absolute_longitude_without_changing_native_values(self):
        for canonical in (False, True):
            text, row, context, proof = self.case(canonical)
            original = copy.deepcopy(row)
            decisions = self.apply(row, [context], proof, text)
            self.assertEqual(row["normalized"]["zodiac_longitude_degrees"], "369/10")
            self.assertEqual(row["normalized"]["magnitude"], original["normalized"]["magnitude"])
            self.assertEqual(row["components"], original["components"])
            self.assertEqual(row["id"], original["id"])
            self.assertEqual(row["source_expression"], original["source_expression"])
            self.assertEqual(decisions["q"]["before"], original)
            self.assertEqual(decisions["q"]["after"], row)
            self.assertEqual(row["zodiac_sign_basis_context_id"], "c")

    def test_frame_identity_is_scoped_to_its_source_review(self):
        text, row, context, proof = self.case()
        other = copy.deepcopy(context)
        other["review_id"] = "other"
        other["value"]["zodiac_sign"] = "Aries"
        self.apply(row, [other, context], proof, text)
        self.assertEqual(row["normalized"]["zodiac_sign"], "Taurus")

    def test_literal_sign_can_supply_origin_without_an_inherited_frame(self):
        _text, row, _context, proof = self.case()
        row["source_expression"] = "6° 54′ ♉"
        row["context_ids"] = []
        proof.update(
            context_id=None,
            frame_sha256=None,
            original_sha256=fingerprint(row),
            evidence=[dict(line=1, source_expression="6° 54′ ♉")],
        )
        self.apply(row, [], proof, row["source_expression"])
        self.assertEqual(row["normalized"]["zodiac_longitude_degrees"], "369/10")
        self.assertNotIn("zodiac_sign_basis_context_id", row)

    def test_literal_origin_accepts_bound_continuation_and_rejects_other_signs(self):
        _text, row, _context, proof = self.case()
        row["source_expression"] = "6"
        row["source_fragments"] = [
            dict(line=1, source_expression="6"),
            dict(line=2, source_expression="° 54′ of Taurus"),
        ]
        row["context_ids"] = []
        proof.update(
            context_id=None,
            frame_sha256=None,
            original_sha256=fingerprint(row),
            evidence=[dict(line=2, source_expression="° 54′ of Taurus")],
        )
        self.apply(row, [], proof, "6\n° 54′ of Taurus")
        self.assertEqual(row["normalized"]["zodiac_longitude_degrees"], "369/10")
        for case in ("unbound", "ambiguous", "conflict", "uncertain"):
            _text, row, context, proof = self.case()
            row["source_expression"] = "6° 54′ ♉"
            proof.update(
                context_id=None, frame_sha256=None, evidence=[dict(line=1, source_expression="♉")]
            )
            if case == "unbound":
                row["source_expression"] = "6° 54′"
            elif case == "ambiguous":
                row["source_expression"] += " ⟦♈/♉⟧"
            elif case == "conflict":
                context["value"]["zodiac_sign"] = "Aries"
            else:
                row["flags"] = ["source_zodiac_identification_uncertain"]
            proof["original_sha256"] = fingerprint(row)
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.apply(row, [context], proof, "6° 54′ ♉")

    def test_changed_values_frames_or_unbound_sign_evidence_are_rejected(self):
        for case in ("number", "frame", "scope", "evidence", "glyph", "ambiguous"):
            text, row, context, proof = self.case()
            contexts = [context]
            if case == "number":
                row["components"]["degree"] = "7"
            elif case == "frame":
                context["value"]["zodiac_sign"] = "Aries"
            elif case == "scope":
                proof["review_id"] = "other"
            elif case == "evidence":
                proof["evidence"] = [dict(line=1, source_expression="Aries")]
            elif case == "glyph":
                row["source_expression"] += " ♈"
                proof["original_sha256"] = fingerprint(row)
            else:
                other = copy.deepcopy(context)
                other["id"] = "c2"
                other["value"]["zodiac_sign"] = "Aries"
                contexts.append(other)
                row["context_ids"].append("c2")
                proof["original_sha256"] = fingerprint(row)
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.apply(row, contexts, proof, text)

    def test_unresolved_and_terminal_degree_coordinates_are_not_silently_converted(self):
        for terminal in (False, True):
            text, row, context, proof = self.case()
            if terminal:
                row["components"] = {"degree": "30"}
            else:
                row["components"] = {}
                row["flags"] = ["source_notation_unresolved"]
            row["normalized"] = normalize_quantity(row)
            proof["original_sha256"] = fingerprint(row)
            with self.subTest(terminal=terminal), self.assertRaises(ValueError):
                self.apply(row, [context], proof, text)
