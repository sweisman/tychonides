"""Public bibliographic resources shared by checkout and installed commands."""

from importlib.resources import files
import json


def public_sources():
    return json.loads(
        files(__package__).joinpath("data/public_sources.json").read_text(encoding="utf-8")
    )


def historical_sources():
    """Registered supplementary books, distinct from the four Tycho log volumes."""
    from .catalog_enrichment import load_registry

    return {
        sid: record
        for sid, record in load_registry().items()
        if record.get("collection_kind") == "historical_book"
    }
