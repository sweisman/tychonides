# Tychonides catalog

**710,420 quantities and 115,972 source groups** from Tycho Brahe’s four
observing volumes, seven further historical books, JJMO experiments, and JPL,
USNO, Carlsberg, and Tokyo optical observations.
The catalog also includes source references, historical calculations and
metadata for 1,963 image versions from Las Cumbres Observatory.
Some quantities have no group, and some groups contain no quantity.

Mars is the first research target. Tycho’s logs also preserve observations of
the Sun, Moon, other planets, comets, fixed stars, and the new star of 1572,
along with the calculations and instrument records that give them context.
[Full log coverage](../../docs/data-sources.md#full-log-coverage)

## Download

Release **tychonides-1.3.3** provides the verified catalog as GitHub Release
assets. Data files are retained by release version, with their checksums in Git.
No separate storage service is required.

- **[Complete SQLite database](https://github.com/sweisman/tychonides/releases/download/tychonides-1.3.3/tychonides.sqlite.gz)** — decompress once to obtain
  `tychonides.sqlite`. All numerical records, source identities, contextual relationships
  and interpretation versions are in this one database.
- **[CSV](https://github.com/sweisman/tychonides/releases/download/tychonides-1.3.3/tychonides.csv)** — one row per quantity, with exact values, decimal
  conveniences and scientific qualifications.

The repository keeps the [manifest](manifest.json) with download and uncompressed database
checksums. Compression reduces download size, without changing SQLite contents.

Releases 1.3.2 and 1.3.3 carry the corrections from two audits. In the
[Tycho log records](../../docs/status.md#audit-of-the-tycho-log-records) for
bodies other than Mars, 6,430 values take the date the page prints for them,
2,472 give up a date carried over from an earlier entry, and 240 are retyped
from their labels. In the
[supplementary books](../../docs/status.md#audit-of-the-other-works), 98
longitudes of an apogee, a perigee, or a node take their printed subject. Each
keeps its earlier interpretation in the database. Candidates remain open in
both audits, and the audit of the books and the modern collections is less
complete than the audit of the logs. Check a date, a type, or a subject
against the printed page before relying on it.

After installing the package from a source checkout, run
`./scripts/download-catalog downloads` to fetch, verify and decompress both
downloads in one command. Existing catalog files are preserved; choose a fresh
destination when fetching another version. The [README](../../README.md#quick-start)
shows installation and an example query.

## Sources and interpretation

For a guide to the coverage pages, field definitions and processing methods,
see the [documentation index](../../docs/README.md).

The [data sources directory](../../docs/data-sources.md) lists the books and
observing programs. Tycho’s four observing volumes contribute 150,443 quantities.
The [Jupiter and Moon selections](../../docs/data-sources.md#jupiter-and-moon-coverage)
add 36,453 quantities to the original Mars selection. The
[Sun, Saturn, and Venus selections](../../docs/data-sources.md#sun-saturn-and-venus-coverage)
add 46,300 quantities. The [full-log intake](../../docs/data-sources.md#full-log-coverage)
adds 50,622 quantities and reuses earlier records for matched source occurrences.
The [interpretation review](../../docs/data-sources.md#interpretation-review)
adds 25 quantities and documents the revised readings and citations.
The [seven-book extension](../../docs/historical-books-ingestion.md)
adds 303,175 quantities across the selected editions, with 4,078 selected regions
given review decisions. The 256,802 modern quantities preserve source
notation, timing conventions, frames, limb information and correction histories.
Original modern values and separately derived conversions remain distinct.

The seven-book coverage page gives the breakdown by interpretation status. Some numerical edition-note
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

The affected JPL meridian series contain 803 all-zero position fields treated as
missing placeholders. These rows retain the literal fields and carry
`jpl_zero_placeholder` with no derived coordinate. Another 192 zero-degree
declinations in Washington 6b, Washington 6c and Tokyo have a blank sign in
series where signed values are uncertain near the equator. They carry
`jpl_declination_sign_indeterminate` with an unsigned magnitude and a null
signed coordinate. Other explicitly signed values still convert normally.

In Washington 6b and 6c, 350 right ascensions and declinations stand as whole
minutes with zero seconds. The USNO publication of the same observation prints
338 of them without seconds, and the other 12 have no USNO record in the
catalog. These fields retain their literal text and carry
`jpl_zero_seconds_placeholder` with no derived coordinate. Seven of them are
also among the zero-degree declinations with a blank sign. Those seven carry
both flags and no derived coordinate.

The catalog retains 360 individually recorded JPL/USNO candidate links.
Wider comparisons by target and epoch found additional potential overlaps in
JPL, USNO, Carlsberg and Tokyo publications. Source occurrences remain separate.
Image records identify external files; they do
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
source-specific interpretation. The CSV contains `normalized_json`, the
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
