"""Catalogue asset names, including read compatibility for earlier releases."""

import json
from pathlib import Path


def catalog_files(manifest, *, uncompressed=False):
    """Accept one complete naming family; never mix or guess asset paths."""
    names = set(manifest.get("output_hashes", {}))
    for stem in ("tychonides", "mars"):
        for suffix in (".sqlite", ".sqlite.gz"):
            database, csv = stem + suffix, stem + ".csv"
            if names == {database, csv}:
                if uncompressed and suffix.endswith(".gz"):
                    raise ValueError("Processing requires an uncompressed working catalogue")
                return database, csv
    raise ValueError("Unexpected release file set")


def working_files(directory):
    manifest = json.loads((Path(directory) / "manifest.json").read_text(encoding="utf-8"))
    return catalog_files(manifest, uncompressed=True)
