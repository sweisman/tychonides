"""A cited altitude fragment through review, normalization and catalogue export.

Run from a source checkout: python -m examples.altitude
The excerpt identity belongs to this example, not the complete book or release.
"""

import csv
import hashlib
import json
from pathlib import Path
import tempfile

from src.catalog import compile_catalogue
from src.catalog_release import write_catalogue
from src.public_checkpoint import public_assertion
from src.source_registry import public_sources


def main():
    # Opera Omnia X, p.245, 18 January 1583: altitude at the lower head of
    # Gemini's meridian transit. Timing and instrument relationships are omitted
    # from this deliberately single-quantity example, not inferred from it.
    text = "partium 63 3, exactly, as before.\n"
    sha = hashlib.sha256(text.encode()).hexdigest()
    span = dict(id="example-span", volume=10, edition_sha256=sha, line_start=1, line_end=1)
    assertion = dict(
        key="altitude",
        line=1,
        span_id=span["id"],
        source_expression="63 3",
        quantity="altitude",
        role="recorded_reading",
        subject="lower head of Gemini",
        reference=None,
        direction=None,
        components=dict(degree="63", arcminute="3"),
        flags=[],
        uncertainty=dict(numeric=None, basis="No statistical uncertainty inferred"),
        unit_basis="Degrees and minutes in the stated altitude; Opera Omnia X p.245",
    )
    review = dict(
        id="example-altitude-review",
        volume=10,
        edition_sha256=sha,
        line_start=1,
        line_end=1,
        interval_sha256=hashlib.sha256(text.rstrip("\n").encode()).hexdigest(),
        basis=dict(kind="final_edition_review", printed_page=245),
        span_decisions=[
            dict(span_id=span["id"], decision="include", reason="Cited altitude fragment")
        ],
        assertions=[assertion],
    )
    row = compile_catalogue([review], {10: text}, [span])["assertions"][0]
    published = public_assertion(row)
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        write_catalogue(output, [row], [published], [], [], [], [], [], public_sources(), [], {})
        with (output / "tychonides.csv").open(encoding="utf-8", newline="") as stream:
            exported = next(csv.DictReader(stream))
    assert exported["value_exact"] == "226980"
    assert exported["value_degrees_decimal"] == "63.05"
    print(
        json.dumps(
            dict(
                citation="Tycho Brahe, Opera Omnia X, p.245, 18 January 1583",
                source_expression=row["source_expression"],
                review=assertion,
                normalized=published["normalized"],
                exported={
                    key: exported[key]
                    for key in (
                        "expression",
                        "quantity",
                        "subject",
                        "role",
                        "unit",
                        "value_exact",
                        "signed_value_exact",
                        "value_degrees_decimal",
                        "printed_page",
                    )
                },
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
