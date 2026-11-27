"""Catalogue asset names, including read compatibility for earlier releases."""

import json
from pathlib import Path


def catalog_files(manifest, *, uncompressed=False):
    """Accept one complete naming family; never mix or guess asset paths."""
    names = set(manifest.get("output_hashes", {}))
    # A working catalogue is unpacked. Public releases compress the database, and from
    # schema 7 the CSV as well.
    families = ((".sqlite", ".csv"), (".sqlite.gz", ".csv"), (".sqlite.gz", ".csv.gz"))
    for stem in ("tychonides", "mars"):
        for packing in families:
            database, csv = (stem + suffix for suffix in packing)
            if names == {database, csv}:
                if uncompressed and database.endswith(".gz"):
                    raise ValueError("Processing requires an uncompressed working catalogue")
                return database, csv
    raise ValueError("Unexpected release file set")


def working_files(directory):
    manifest = json.loads((Path(directory) / "manifest.json").read_text(encoding="utf-8"))
    return catalog_files(manifest, uncompressed=True)
