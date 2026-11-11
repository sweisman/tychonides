"""Reviewed endpoint, quantity and flag allowlists for public projection."""

from importlib.resources import files
import json

_POLICY = json.loads(
    files(__package__).joinpath("data/public_policy.json").read_text(encoding="utf-8")
)
SUBJECTS = set(_POLICY["SUBJECTS"])
REFERENCES = set(_POLICY["REFERENCES"])
QUANTITIES = set(_POLICY["QUANTITIES"])
ROLES = set(_POLICY["ROLES"])
FLAGS = set(_POLICY["FLAGS"])
FLAGS_EQUAL_VALUE = _POLICY["FLAGS_EQUAL_VALUE"]
