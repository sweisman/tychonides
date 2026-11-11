# Independent Transcription Validation: Pafko’s Mars Records

Wayne Pafko’s independently entered [workbook](https://www.pafko.com/tycho/mars.xls)
provides a control set for the extraction and numerical interpretation of Tycho’s
*Thesaurus Observationum*, *Opera Omnia* X–XIII. The comparison uses the
[published editions](sources.md) and preserves disagreements and incomplete values.

## Reconciliation result

Every one of the **923 workbook rows has a unique source identity**. No rows were dropped to improve agreement.

| Volume | Workbook rows | Magnitude agreement | Quotation difference | Incomplete source value |
| --- | ---: | ---: | ---: | ---: |
| X | 36 | 35 | 1 | 0 |
| XI | 169 | 167 | 2 | 0 |
| XII | 623 | 614 | 8 | 1 |
| XIII | 95 | 90 | 5 | 0 |
| Total | 923 | 906 | 16 | 1 |

Of the 906 magnitude agreements, 125 also agree in explicitly recoverable hemisphere. An unsigned agreement is not confirmation of a signed coordinate. The 16 quotation differences, 28 internal quotation/numerical conflicts, and 14 numerical-sign conflicts against source hemispheres have source-review evidence. These categories overlap and must not be added as independent error counts. Structural reviews are distinct from reviews of numerical glyphs; the complete set has not received an independent image audit of every figure.

Pafko's workbook contains source quotations, sexagesimal numerical components, and signed decimal degrees. The books use sexagesimal notation, including fractional minutes. Their agreement is checked with exact rational arithmetic before any decimal rounding. Original values remain intact; preferred readings and review decisions are separate.

## The incomplete record

Workbook row 751 corresponds to the **second parallel declination at 8h18⅙ on 30 October 1595**, Volume XII, printed p. 452. The print itself gives **“17…”**. Both the final edition and the workbook preserve the incomplete expression.

Its source identity is established, but its full numerical value is not recoverable from this printed witness. The normalized preferred magnitude remains null. Completing it would require additional primary evidence, such as the underlying manuscript; neither the workbook's numerical cells, the neighbouring reading, nor a modern prediction can supply the missing digits. This is a documented exception, so an unqualified claim that all 923 numerical values are confirmed would be false.

## Dates, clocks, targets, and roles

Date and page disagreements have been checked against the printed headings and layout. Pafko sometimes carries an earlier heading forward; in several January 1587 reductions he explicitly queries February and adopts February numerically. The catalog preserves that interpretation alongside the printed January dates. A preferred recorded date reproduces the historical label; it is not an independently established civil timestamp.

Timing differences include omitted seconds, misread fractions, assignment of the preceding distance's clock to a later declination, and confusion between raw and corrected clocks. Some clocks belong to calculations rather than additional observations. Hours expressing distance from the meridian are hour angles and cannot become observing times. A source-reviewed null preferred clock overrides provisional forward filling.

Use preferred dates, clocks, and printed pages together with their evidence bases. The provisional extraction remains visible for audit. Calendar, astronomical-day origin, local time, and AM/PM interpretation are not yet converted into absolute timestamps.

The workbook includes calculated reductions and two Aldebaran calibration readings. These remain in workbook reconciliation while being distinguished from a raw Mars selection. Automatically assigned roles and inherited signs still require scientific review before modeling; the catalog's selection fields retain that requirement.
For example, XII p.283 contains a separately stated 10°9′30″ Mars declination
used in the July 22 calculation. Its workbook link validates that source entry;
it does not make the calculation input an additional raw reading.
On XII p.283, the later July 25 declination at 1h34½m has no direct workbook
control. The earlier recorded value and the calculation input have separate
links, although all three print 10°14½′. Equal values do not merge their source
identities or establish statistical independence.

No final-edition transcription or translation error has been confirmed in the discrepancies reviewed so far. A suspicious recorded number can already be present in the print: for example, Volume XII p. 446 prints 5h35⅙ within a sequence otherwise using 3h clocks. The edition preserves it. Record the anomaly separately from a proposed correction; do not silently emend it.

## Reproducibility and readiness

The pipeline retains all rows, immutable workbook values, input fingerprints, independent extraction, source-bound decisions, and separate JSON/CSV outcomes and derived catalogs. The numerical export provides source citations and explicitly defined fields. Source citations and review decisions identify the basis for each result.

The [published editions and PDFs](sources.md) supply the comparison readings. Numerical results retain their source citations and recorded values; the [catalog design](catalog-design.md) describes their representation.

This reconciliation supplies independent controls for the historical Mars subset of the [Tychonides catalog](../resources/catalog/README.md). That subset also represents declinations, separations, altitudes and supporting records outside the workbook's selection, preserving their distinct quantities and reduction roles. Astronomical analysis requires appropriate clock, calendar, site, instrument and uncertainty interpretations; reconciliation alone does not establish readiness for orbit fitting or parallax estimation. The [research program](research-plan.md) describes those investigations.
