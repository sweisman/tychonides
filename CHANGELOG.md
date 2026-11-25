# Catalog releases

## 1.3.1

The four-volume Tycho review adds 22,578 versioned interpretations while
preserving the original readings and identities. It recovers 32 missing page
citations and adds 25 distinct quantities and 1,657 context records. The
release contains **710,420 quantities and 115,972 source groups**. [Review coverage and remaining evidence](docs/data-sources.md#interpretation-review)

## 1.3.0

The catalog adds **50,622 quantities** from Tycho’s four observing volumes.
Coverage includes Mercury, all seven comet accounts, fixed stars and stellar
catalogs, the 1573 follow-up readings of the new star of 1572, and supporting
clock, instrument, calibration, and reduction evidence. Shared source
occurrences retain their existing identities. The release contains
**710,395 quantities and 115,972 source groups**.
[Full log coverage and interpretation limits](docs/data-sources.md#full-log-coverage)

## 1.2.0

The catalog adds 19,173 Sun, 11,504 Saturn, and 15,623 Venus quantities from
Tycho’s four observing volumes, including solar eclipse records, meridian
altitudes, clocks, and historical reductions. Shared readings retain their
existing identities. Six earlier date claims gained or corrected a year based
on the printed section headings. The release contains **659,773 quantities and
113,575 source groups**. [Coverage by volume](docs/data-sources.md#sun-saturn-and-venus-coverage)

## 1.1.0

The catalog adds 12,560 quantities from the Jupiter selection and 23,893
from the Moon selection across all four volumes of Tycho’s observing logs.
The selections include eclipses, occultations, observing clocks, calibration
readings, and historical reductions. Shared occurrences retain their existing
records. The release contains **613,473 quantities and 101,336 source groups**.
[Coverage by volume](docs/data-sources.md#jupiter-and-moon-coverage)

## 1.0.1

This revision qualifies **803** all-zero JPL fields as missing placeholders and
withholds the sign for **192** nonzero declinations with an uncertain hemisphere.
The native fields and all record identities are preserved.

Three counted-sign entries with 30° and positive lower components now have
unresolved interpretations. Exact 30° endpoints retain their existing
interpretations. Earlier interpretations remain in the database.

The verifier checks the affected JPL values and flags against the preserved
fixed-width fields. Historical parsing now distinguishes attached note markers
and clock abbreviations from numerical components and hemisphere indicators.
The documentation defines the scope of the Pafko comparison, historical
reproducibility, and the treatment of cross-publication overlap.

## 1.0.0 — initial public release

A source-linked catalog of **577,020 quantities and 91,626 source groups**,
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
