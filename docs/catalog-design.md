# Catalog design

The Tychonides catalog represents observations and related calculations from
historical books and modern observing programs. Mars is the first target;
Tycho’s material in _Opera Omnia_ X–XIII supplies its historical core.
Its [public sources](sources.md) include published books, Ars Astronomica PDFs
and original scans. Pafko’s spreadsheet supplies an independent comparison set
for Mars. The [source directory](data-sources.md) describes the wider collections
and observing policy.

## Representation

Source witnesses, passages, quantities, observing context, groups, derivations and
review decisions have distinct identities. One printed row can contain several
quantities; repeated readings need not be independent observations. The
[ingestion strategy](ingestion-strategy.md) describes their relationships and the
[data dictionary](catalog-data-dictionary.md) defines their fields.

Original readings and exact sexagesimal fractions remain separate from corrections
and interpretations. Direct measurements, calibrations, adopted parameters,
predictions and historical reductions retain their roles. Missing figures and
unsupported forms remain explicit.

## Coverage and source checks

The historical Mars inventory covers tables, prose, annotations and diagrams, including Mars
references in mixed-target material. Screening and inspected coverage are reported
separately. Bibliographic locations, recorded dates, clock associations and source
layout establish identities; numerical agreement does not select a match.

Source checks preserve incomplete and disputed readings. Dates, clock origins,
hemispheres, instruments and observing sites require evidence at the appropriate
scope. The [edition-issue policy](edition-issues.md) separates transcription errors,
printed variants and computational extraction problems.

## Publication

The [Tychonides catalog](../resources/catalog/README.md) supplies one self-contained
SQLite database and a convenient CSV export, with a numerical dictionary,
bibliographic citations, coverage and file
fingerprints. Scientific selections require the relevant observing and reduction
interpretations; a catalog entry alone does not establish readiness for orbital
fitting or parallax estimation.

## Reproducibility

The numerical release identifies its files, exact units, source citations and interpretation limits. The published books and scans permit independent extraction and comparison.
