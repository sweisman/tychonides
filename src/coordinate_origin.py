"""Source-bound projection of reviewed named-sign coordinate origins."""

import hashlib
import json
import re
from fractions import Fraction
from pathlib import Path

from .normalization import ZODIAC_SIGNS, normalize_quantity


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def literal_signs(text):
    aliases = {"Scorpio": ("Scorpio", "Scorpius"), "Capricorn": ("Capricorn", "Capricornus")}
    return {
        sign
        for sign, glyph in ZODIAC_SIGNS.items()
        if glyph in text
        or any(re.search(r"\b" + name + r"\b", text) for name in aliases.get(sign, (sign,)))
    }


def frame_sign(frame, row):
    """Recognize the two already-reviewed frame schemas without guessing scope."""
    value = frame.get("value")
    if frame.get("kind") != "source_coordinate_frame" or not isinstance(value, dict):
        return None
    sign = value.get("zodiac_sign")
    if sign not in ZODIAC_SIGNS:
        return None
    if (
        value.get("coordinate") == row["quantity"]
        and value.get("longitude_origin") == "start_of_named_sign"
    ):
        return sign
    if (
        value.get("subject") == row["subject"]
        and type(value.get("line_start")) is int
        and type(value.get("line_end")) is int
        and value["line_start"] <= row["line"] <= value["line_end"]
        and isinstance(value.get("source_expression"), str)
        and literal_signs(value["source_expression"]) == {sign}
    ):
        return sign
    return None


def apply_coordinate_origin_reviews(work, compiled, texts):
    path = Path(work) / "coordinate_origin_reviews.json"
    if not path.exists():
        return {}
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Coordinate-origin reviews must be a list")
    rows = {r["id"]: r for r in compiled["assertions"]}
    frames = {}
    for context in compiled["contexts"]:
        key = (context["review_id"], context["id"])
        if key in frames:
            raise ValueError("Duplicate review-scoped context identity")
        frames[key] = context
    decisions, seen = {}, set()
    for review in records:
        if (
            not isinstance(review, dict)
            or set(review)
            != {
                "id",
                "assertion_id",
                "review_id",
                "context_id",
                "original_sha256",
                "frame_sha256",
                "reason",
                "evidence",
            }
            or not isinstance(review["id"], str)
            or not review["id"]
            or review["id"] in seen
            or not isinstance(review["reason"], str)
            or not review["reason"]
        ):
            raise ValueError("Invalid coordinate-origin review")
        row = rows.get(review["assertion_id"])
        frame = frames.get((review["review_id"], review["context_id"]))
        if (
            row is None
            or row["id"] in decisions
            or row["review_id"] != review["review_id"]
            or fingerprint(row) != review["original_sha256"]
            or row["quantity"] not in ("ecliptic_longitude", "orbital_longitude")
            or "zodiac_sign" in row
            or "zodiac_sign_basis_context_id" in row
            or row.get("direction") is not None
            or "source_zodiac_identification_uncertain" in row.get("flags", [])
            or row["normalized"]["status"] != "exact"
            or normalize_quantity(row) != row["normalized"]
            or not 0 <= Fraction(row["normalized"]["magnitude_degrees"]) < 30
            or {"sign_count", "sexagena"} & set(row.get("components", {}))
        ):
            raise ValueError(
                "Coordinate-origin review differs from its frozen source interpretation"
            )
        expression = (
            " ".join(f["source_expression"] for f in row.get("source_fragments", []))
            or row["source_expression"]
        )
        printed = literal_signs(expression)
        if review["context_id"] is None:
            if review["frame_sha256"] is not None or len(printed) != 1:
                raise ValueError("Direct coordinate origin requires one literal sign")
            sign = next(iter(printed))
        else:
            if (
                frame is None
                or row["source_id"] != frame["source_id"]
                or frame["id"] not in row.get("context_ids", [])
                or fingerprint(frame) != review["frame_sha256"]
            ):
                raise ValueError("Coordinate origin differs from its reviewed source frame")
            sign = frame_sign(frame, row)
        signs = {
            frame_sign(frames[(row["review_id"], cid)], row)
            for cid in row.get("context_ids", [])
            if (row["review_id"], cid) in frames
        }
        signs.discard(None)
        if sign is None or signs - {sign} or (frame is not None and signs != {sign}):
            raise ValueError("Missing or contradictory reviewed coordinate origin")
        if printed and printed != {sign}:
            raise ValueError("Reviewed coordinate origin contradicts the literal sign")
        evidence = review["evidence"]
        allowed = (
            set(frame["lines"] if frame is not None else [])
            | {row["line"]}
            | {f["line"] for f in row.get("source_fragments", [])}
        )
        lines = texts[row["source_id"]].splitlines()
        if (
            not isinstance(evidence, list)
            or not evidence
            or any(
                not isinstance(item, dict)
                or set(item) != {"line", "source_expression"}
                or type(item["line"]) is not int
                or item["line"] not in allowed
                or not 1 <= item["line"] <= len(lines)
                or not isinstance(item["source_expression"], str)
                or not item["source_expression"]
                or lines[item["line"] - 1].count(item["source_expression"]) != 1
                or sign not in literal_signs(item["source_expression"])
                for item in evidence
            )
        ):
            raise ValueError("Coordinate-origin review lacks literal sign evidence")
        original = dict(row)
        normalization = normalize_quantity(dict(row, zodiac_sign=sign))
        native = {
            k: v
            for k, v in normalization.items()
            if k not in ("zodiac_sign", "longitude_origin", "zodiac_longitude_degrees")
        }
        if native != row["normalized"]:
            raise ValueError("Coordinate-origin projection cannot change native numerical values")
        row.update(zodiac_sign=sign, normalized=normalization)
        if frame is not None:
            row["zodiac_sign_basis_context_id"] = frame["id"]
        decisions[row["id"]] = dict(before=original, after=dict(row))
        seen.add(review["id"])
    return decisions
