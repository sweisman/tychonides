# Catalog releases

## 1.0.0 — initial public release

A source-linked catalog of **577,020 quantities in 91,626 source groups**,
combining historical astronomical books and modern terrestrial optical datasets.
The selection includes recorded measurements, reductions, corrections, model
parameters and worked calculations, with their evidential roles kept explicit.
See the [source directory](docs/data-sources.md) and
[historical coverage](docs/historical-books-ingestion.md).

- One SQLite database and matching CSV, with source citations, preserved
  numerical expressions, exact conversions, contextual relationships and
  explicitly unresolved interpretations.
- Independent transcription controls from all 923 rows of Pafko’s Mars workbook,
  with disagreements and incomplete readings documented.
- Full CSV/database parity, source and quantity counts, relationship and index
  checks, and independent verification of supported modern conversions.
- Public schema and vocabulary references, interpretation guidance, an
  executable worked example and self-contained parser tests.
- Complete Solar System tables from eight JPL meridian series, USNO W1J00/W2J00,
  Carlsberg I/256 and Tokyo I/188, retaining native target identifiers, time scales,
  coordinate origins, quality flags and published correction fields. Existing
  Mars identities are preserved.

Original source documents and image pixels remain external. Catalog entries
are source quantities, not counts of independent observations. Historical model
engines, correction comparisons, parallax studies and the interactive explorer
follow the [research program](docs/research-plan.md), including the post-launch
stellar-aberration study.

Code is AGPL-3.0-or-later; project data contributions are CC0-1.0, with third-party
source terms preserved.
