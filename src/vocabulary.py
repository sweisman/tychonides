"""Definitions and coverage checks for every published quantity and convention."""

from importlib.resources import files
import json
from pathlib import Path


def load_vocabulary(kind):
    return json.loads(
        files(__package__).joinpath(f"data/{kind}_vocabulary.json").read_text(encoding="utf-8")
    )


def validate_vocabulary(db, docs_root=None):
    from .source_registry import historical_sources

    books = sorted(historical_sources())
    historical = "(q.source_id LIKE 'tycho-%'"
    if books:
        historical += " OR q.source_id IN (" + ",".join("?" for _ in books) + ")"
    historical += ")"
    for kind, condition in (("historical", historical), ("modern", "NOT " + historical)):
        spec = load_vocabulary(kind)
        text = (
            None
            if docs_root is None
            else (Path(docs_root) / f"docs/{kind}-data-dictionary.md").read_text(encoding="utf-8")
        )
        for field in ("quantity", "role", "unit"):
            # Include earlier interpretations as well as the current catalogue view.
            column = "q.role" if field == "role" else "i." + field
            values = db.execute(
                f"SELECT DISTINCT {column} FROM quantities q JOIN interpretations i ON i.quantity_id=q.id WHERE {condition}",
                books,
            )
            for (value,) in values:
                if value is not None and (
                    value not in spec[field] or (text is not None and f"`{value}`" not in text)
                ):
                    raise ValueError(f"Undocumented {kind} {field}: {value}")
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='derived_values'").fetchone():
        return
    spec = load_vocabulary("normalization")
    text = (
        None
        if docs_root is None
        else (Path(docs_root) / "docs/normalization-conventions.md").read_text(encoding="utf-8")
    )
    for field, definitions in spec.items():
        for (value,) in db.execute(
            f"SELECT DISTINCT {field} FROM derived_values WHERE {field} IS NOT NULL"
        ):
            if value not in definitions or (text is not None and f"`{value}`" not in text):
                raise ValueError(f"Undocumented {field}: {value}")
    units = load_vocabulary("historical")["unit"] | load_vocabulary("modern")["unit"]
    for (value,) in db.execute(
        "SELECT DISTINCT derived_unit FROM derived_values WHERE derived_unit IS NOT NULL"
    ):
        if value not in units:
            raise ValueError("Undocumented derived_unit: " + value)


def render_vocabulary(kind):
    titles = {
        "historical": "Historical quantity and role reference",
        "modern": "Modern quantity and role reference",
        "normalization": "Normalization conventions",
    }
    lines = [
        "# " + titles[kind],
        "",
        "These terms describe source meanings and explicit conversions; they do not establish observational independence or apply new corrections.",
        "",
        "See the [database schema](database-schema.md) and [catalog dictionary](catalog-data-dictionary.md).",
        "",
    ]
    presentation = json.loads(
        files(__package__)
        .joinpath("data/vocabulary_introductions.json")
        .read_text(encoding="utf-8")
    )
    if kind in presentation:
        lines += [presentation[kind], ""]
    for field, entries in load_vocabulary(kind).items():
        lines += ["## " + field, "", "| Term | Meaning |", "| --- | --- |"]
        lines += [f"| `{term}` | {meaning} |" for term, meaning in sorted(entries.items())]
        lines += [""]
    return "\n".join(lines)


def validate_reference_pages(root):
    for kind, name in (
        ("historical", "historical-data-dictionary.md"),
        ("modern", "modern-data-dictionary.md"),
        ("normalization", "normalization-conventions.md"),
    ):
        path = Path(root) / "docs" / name
        if path.read_text(encoding="utf-8") != render_vocabulary(kind):
            raise ValueError("Stale generated reference: " + name)
