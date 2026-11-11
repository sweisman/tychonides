# Tychonides catalog

**577,020 quantities in 91,626 source groups**, combining the Mars selection from
Tycho Brahe’s four observational volumes, seven further historical books,
JJMO experiments and JPL, USNO, Carlsberg and Tokyo optical observations.
The catalog also includes source references, historical calculations and
metadata for 1,963 image versions from Las Cumbres Observatory.

Mars is the first research target. The seven supplementary books already extend
the catalog to other celestial bodies, corrections and historical theories.
Further bodies in Tycho's observation logs and additional collections remain
future acquisitions.

## Download

Release **tychonides-1.0.0** provides the verified catalog as GitHub Release
assets. Data files are retained by release version, with their checksums in Git.
No separate storage service is required.

- **[Complete SQLite database](https://github.com/sweisman/tychonides/releases/download/tychonides-1.0.0/tychonides.sqlite.gz)** — decompress once to obtain
  `tychonides.sqlite`. All numerical records, source identities, contextual relationships
  and interpretation versions are in this one database.
- **[CSV](https://github.com/sweisman/tychonides/releases/download/tychonides-1.0.0/tychonides.csv)** — one row per quantity, with exact values, decimal
  conveniences and scientific qualifications.

Release **tychonides-1.0.0**. Files are versioned GitHub Release assets; the repository
keeps the [manifest](manifest.json) with download and uncompressed database
checksums. Compression reduces download size, without changing SQLite contents.

After installing the package from a source checkout, run
`./scripts/download-catalog downloads` to fetch, verify and decompress both
downloads in one command. Existing catalog files are preserved; choose a fresh
destination when fetching another version. The [README](../../README.md#quick-start)
shows installation and an example query.

## Sources and interpretation

For a guide to the coverage pages, field definitions and processing methods,
see the [documentation index](../../docs/README.md).

The [data sources directory](../../docs/data-sources.md) lists the books and
observing programs. The original 17,043 historical quantities retain their
identities and interpretations. The [seven-book extension](../../docs/historical-books-ingestion.md)
adds 303,175 quantities across the selected editions, with 4,078 selected regions
given review decisions. The 256,802 modern quantities preserve source
notation, timing conventions, frames, limb information and correction histories.
Original modern values and separately derived conversions remain distinct.

The new books contribute 295,191 exact conversions, 486 incomplete quantities
and 7,498 unsupported or unresolved interpretations. Some numerical edition-note
expressions remain contextual evidence rather than separate quantity rows.
Source coverage does not establish observational independence, absolute timestamps
or eligibility for a particular analysis. Missing source panels and ambiguous
units or coordinate origins are documented rather than reconstructed.

The twelve complete digital Solar System tables contain 75,256 source rows and
256,485 quantities. They cover planets, planetary satellites, minor planets,
the Sun and a comet. The remaining modern quantities belong to the JJMO records.
USNO right ascensions and declinations with omitted seconds remain explicitly
incomplete; missing components are not replaced by zero. Numeric conversions and
supported clock conversions are exposed in dedicated columns. TT, UT1 and the
JPL source’s UT label remain distinct.

Rows and groups are not counts of independent observations. The 360 potential
JPL/USNO overlaps remain unmerged. Further source-level overlap warnings identify
related JPL, USNO, Carlsberg and Tokyo publications; the full table counts are not
additive counts of independent measurements. Image records identify external files; they do
not include pixels or establish an astrometric solution. Original reports and
supporting catalogs are cited rather than bundled as source documents.

## Inspect Mars declination records

The `catalogue` view selects the current interpretation. Display the source and
converted representations together before choosing values for an analysis:

```sql
SELECT id, source_id, role, expression, status,
       value_exact, signed_value_exact, unit,
       derived_value_exact, derived_signed_value_exact, derived_unit,
       derived_method, derived_time_scale, derived_timestamp,
       source_page_url, source_line_number
FROM catalogue
WHERE subject = 'Mars' AND quantity = 'declination';
```

This query is exploration, not a scientific selection. Target and quantity alone
do not establish a common coordinate frame, correction state, observing epoch or
evidential role. Define eligibility for the named analysis, keep shared sessions
and calibration dependencies together, and list exclusions. A missing signed value
is not zero. The [worked values](../../docs/catalog-data-dictionary.md#worked-numerical-examples)
explain original and derived columns, zodiac origins and clocks.

For a subsequent convenience query, `COALESCE` can select a derived value when
present, but always select its corresponding unit and retain the method and
source-specific interpretation. Schema 5 CSV contains `normalized_json`, the
complete selected normalization; SQLite retains the full relationship structure.
See [verification](../../docs/data-workflow.md#what-verification-checks),
[terminology](../../docs/catalog-terms.md) and [intended source uses](../../docs/data-sources.md#intended-uses).

## Inspect native JPL residual fields

Washington 6a has 832 source rows with additional printed residual pairs. They
remain literal source context in `source_lines`, outside the quantity-row totals.
The linked format description does not state their scale; the query returns the
printed fields without assigning angular or time units:

```sql
SELECT source_id, artifact_sha256, locator,
       substr(raw_line, 44, 6) AS ra_residual_source_expression,
       substr(raw_line, 61, 5) AS dec_residual_source_expression
FROM source_lines
WHERE source_id = 'jpl-wash6a'
  AND (trim(substr(raw_line, 44, 6)) <> ''
       OR trim(substr(raw_line, 61, 5)) <> '');
```

These fields are source-published residuals, not additional measured positions.
They are available in SQLite alongside native instrument, limb and catalog codes;
the quantity CSV covers the selected quantities and their normalization metadata.

## Reuse and citation


Project data contributions are **CC0-1.0**; third-party sources retain their
original terms. Software is **AGPL-3.0-or-later**. See
[data licensing](../../DATA_LICENSE.md) and [citation metadata](../../CITATION.cff).

An [Ars Astronomica](https://arsastronomica.com/) project.
