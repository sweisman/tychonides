"""Review state: shared catalogue responsibilities."""

import copy
import json
from pathlib import Path
import re
from fractions import Fraction
from .core import digest

REPO = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(s) for s in Path(path).read_text(encoding="utf-8").splitlines() if s]


def path_key(path):
    path = Path(path).resolve()
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def checked_hashes(base, expected):
    base = Path(base).resolve()
    for name, sha in expected.items():
        path = (base / name).resolve()
        if not path.is_relative_to(base):
            raise ValueError("Manifest path outside its input directory")
        if not path.is_file() or digest(path) != sha:
            raise ValueError("Stale or changed manifest artifact: " + name)


def preserve_rows(prior, current, direction_reviews=None, control_reviews=None):
    indexed = {a["id"]: a for a in current}
    if len(indexed) != len(current):
        raise ValueError("Duplicate public quantity identity")
    direction_reviews = direction_reviews or {}
    control_reviews = control_reviews or {}
    if set(direction_reviews) - {a["id"] for a in prior}:
        raise ValueError("Direction review lacks a prior quantity")
    if set(control_reviews) - {a["id"] for a in prior}:
        raise ValueError("Control review lacks a prior quantity")
    revised = []
    changed = []
    for a in prior:
        expected = copy.deepcopy(a)
        review = direction_reviews.get(a["id"])
        if a["id"] in control_reviews:
            control = control_reviews[a["id"]]
            if (
                not isinstance(control, str)
                or not re.fullmatch(r"Sheet1:\d+", control)
                or a.get("workbook_control_id") not in (None, control)
            ):
                raise ValueError("Control review cannot replace an established source identity")
            expected["workbook_control_id"] = control
        if review:
            old, new = review.get("old_direction"), review.get("new_direction")
            if (
                old not in ("north", "south")
                or new not in ("north", "south")
                or old == new
                or a.get("direction") != old
                or a["normalized"].get("signed_magnitude")
                != str(Fraction(a["normalized"]["magnitude"]) * (-1 if old == "south" else 1))
            ):
                raise ValueError("Direction review differs from its prior normalization")
            expected["direction"] = new
            expected["normalized"]["signed_magnitude"] = str(
                Fraction(a["normalized"]["magnitude"]) * (-1 if new == "south" else 1)
            )
            revised.append(a["id"])
        if indexed.get(a["id"]) != expected:
            changed.append(a["id"])
    if changed:
        raise ValueError(
            "Previously verified quantities changed or disappeared: " + ", ".join(changed[:3])
        )
    return revised


def source_texts(work, source_root):
    from .publication import read_witness

    root = Path(source_root).resolve()
    texts = {}
    for witness in read(Path(work) / "witnesses.json"):
        texts[witness["volume"]] = read_witness(root, work, witness)
    return texts


def edition_hashes(work):
    return {w["volume"]: w["edition_sha256"] for w in read(Path(work) / "witnesses.json")}
