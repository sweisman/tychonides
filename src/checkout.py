"""Friendly boundary for commands that require the extraction workspace."""

from pathlib import Path


def require_checkout(parser):
    root = Path(__file__).resolve().parents[1]
    if not (root / "tests").is_dir() or not (root / "pyproject.toml").is_file():
        parser.error(
            "Run this processing command from a source checkout; the installed package does not include the extraction workspace."
        )
    return root
