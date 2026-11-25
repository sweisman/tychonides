# Project status

This page records what Tychonides has finished, what is under way, and what
comes next. The [research program](research-plan.md) defines the objectives and
milestones. The [source directory](data-sources.md) defines catalog coverage.
Finished analyses are collected on the [studies page](studies.md).

Last updated November 25, 2026.

## Objectives

| Objective | Status | Done so far | Next step |
| --- | --- | --- | --- |
| Observation catalog | Available, [audit under way](#audit-of-the-tycho-log-records) | [Release 1.3.2](../resources/catalog/README.md#download) holds 710,420 quantities from Tycho’s four logs, seven supplementary books, and modern optical collections. The records of the four logs are audited and corrected. | The audit of the other works, then the [planned acquisitions](data-sources.md#planned-ingestions) |
| Mars apparent motion and geometry | Nine oppositions compared | [The 1595 retrograde passage](mars-apparent-motion.md) and [the oppositions of 1580 to 1600](mars-oppositions.md) compare Tycho’s reductions with four constructions and the JPL DE441 ephemeris. | The 1600 opposition, once the calendar of its entries is recorded |
| Historical model comparison | Printed predictions compared | The [printed predictions study](printed-predictions.md) compares every table and ephemeris position the logs print for the five planets with the log and DE441. The opposition study covers Mars near opposition. | The Moon, once the hours of its entries are recorded, then independently reconstructed tables and Ursus’s formulation where the sources permit |
| Mars, Jupiter, and Saturn parallax | One campaign tested | [Recorded and modern corrections](planetary-parallax-comparisons.md) are compared. [The Mars-to-star distances of 1587](mars-parallax-1587.md) are tested for a parallax. | The campaign of 1582 and 1583, then parallax feasibility |
| Mercury and Venus parallax | Initial calculations | [Historical reductions and the 1590 Venus experiment](mercury-venus-parallax.md) are recomputed under historical and modern assumptions. | Parallax feasibility |
| Accuracy and refraction | Tables compared | The [refraction tables](refraction-tables.md) of Tycho and Riccioli are set against modern refraction. The [planetary comparisons](planetary-parallax-comparisons.md) vary distance and refraction independently. In 1595 Tycho’s Mars longitudes agree with DE441 to about one arcminute where the log prints a usable hour. | The tables that lack recorded altitudes, then the observations behind the tables and calibrated observing sessions |
| Kepler and opposition tables | Table checked | Longomontanus’s fourteen oppositions [reproduce from DE441](mars-oppositions.md#the-opposition-table-against-de441) within 4′ in longitude. Tycho’s [solar theory](solar-theory.md) reproduces from his printed intervals, and his altitude corrections account for the seasonal pattern in the table’s instants. | The steps from the log’s readings to each tabulated opposition |
| Interactive visualization | Planned | [Visualization plan](visualization-plan.md) | Catalog explorer |
| Stellar aberration | Planned | | |
| Other planets and records | Planned | The catalog covers the planets, Sun, Moon, comets, and stars in Tycho’s logs. | |

## State of the catalog rows

Of the 150,443 quantities from Tycho’s four logs in release 1.3.2:

| State | Quantities | Share |
| --- | ---: | ---: |
| Exact value with an assigned type, subject, and role | 57,441 | 38% |
| Exact value with a type, subject withdrawn by the audit | 94 | under 1% |
| Exact value, type not yet assigned | 24,806 | 16% |
| Printed expression kept, no numerical interpretation yet | 68,091 | 45% |
| Incomplete value | 11 | under 1% |

The studies draw mainly on the first row. In the database’s `metadata` table,
`normalization_counts` now covers the whole catalog. The entries written for
the first Mars selection of 17,043 quantities are kept under
`first_mars_selection`. The manifest gives the totals by source.

## Audit of the Tycho log records

Release 1.3.2 carries the corrections from an audit of the records of Tycho’s
four log volumes in release 1.3.1. Each correction cites the printed label or
date line it rests on and keeps the earlier interpretation beside it. No
printed expression or exact value changed.

The audit covered the 150,443 quantities from the four logs. It did not cover
the seven supplementary books (303,175 quantities) or the modern collections
(256,802 quantities). Those have had only the checks that every release runs
on the whole catalog. Their audit is the [next step](#next-up). Its first
tests have found two kinds of fault that release 1.3.2 does not correct. In
the books, about a hundred longitudes of an apogee or a node are recorded as
the place of the Sun or planet itself. In two of the JPL Washington series,
338 coordinates that the observers did not measure to the second stand with
zero seconds.

The records of Tycho’s four log volumes entered the catalog in two ways. The
Mars records came first, under rules that were revised each time the page
showed a new layout. The records for every other body followed, almost
entirely automatically. The audit applies the same tests to both groups.

1. **Labels.** Each typed value in a table is compared with the label of its
   own cell, its row, and its column, with any label printed inside the
   column, and with the sentence that introduces the table.
2. **Dates.** Each dated value is compared with the date line above it, with
   any section heading or calculation title between the two, and with a day
   printed on its own row or in the day column of its table.
3. **Ephemeris.** Each dated declination, longitude, latitude, and altitude of
   the Moon and the five planets is compared with the range the body covered
   that day, from JPL Horizons, widened by a margin for refraction and
   parallax.
4. **Sample.** 142 typed values that no test flagged were drawn at random and
   read against the edition.

| | Other bodies | Mars |
| --- | ---: | ---: |
| Dated values | 104,700 | 16,651 |
| Flagged by a date test | 10,959 | 945 |
| Flagged by a label test | 1,235 | about 250 |
| Dated declinations outside the ephemeris range | 5% to 20% by body | 1% |
| Wrong type or subject among sampled values that no test flagged | 2 of 98 | 0 of 44 |

The counts are those of release 1.3.1. A flagged value is a candidate. Reading
the candidates against the edition gives two different results.

**Mars.** The flagged values were examined group by group, and each doubtful
group was read in the edition. Footnotes, which follow the entries they
annotate, were not traced one by one. No Mars value was found with a wrong
date or subject. One was found with a wrong type: a distance of Mars from a
star in Virgo stood as an altitude (*Opera Omnia* XI p. 181). The Mars records
follow sub-headings, days printed on a row, and labels printed inside a table
as the page has them.

**Other bodies.** The largest groups of each kind were read. Nearly all are
faults of one family. Context is kept past the place where the page replaces
it.

- **Dates.** An entry’s date is kept under a later heading that was not read
  as a date (“The following day, which was 3 March”), under a calculation
  headed for another day (“For the place of Saturn on 4 December” carries 30
  December), through yearly and monthly tables that print a day on each row,
  and through undated appendices such as the star catalog that follows the
  observations of 1589.
- **Subject.** A block’s body is kept on a value whose label names another
  object. Declinations of Regulus, Spica, and Aldebaran, taken to test the
  instrument, stand as the planet’s or the Moon’s. Altitudes and azimuths of the Sun stand
  as those of Venus.
- **Kind.** A column heading is kept below a label inside the table that
  replaces it. A heading that names the equator altitude used and then the
  column’s kind, “Altitude æquat. 34 9 50 — Declin.”, is read by its first
  word.
- **Role.** In tables that compare places “from the observations” with
  Copernican and Alphonsine ones, the computed rows are marked as Tycho’s
  reductions.

Some candidates are faithful to the print and are set aside as questions
about the source. Three sessions on Jupiter headed 29 and 30 January, printed
among the observations of 1590 (XII pp. 39 to 40), give declinations near 7°.
Jupiter stood 5.6° south on that date in 1590 and 7.0° north a year earlier.
The catalog records no calendar for the entries of 1599 and 1600, as the
[Mars oppositions study](mars-oppositions.md) notes.

**Corrections in release 1.3.2.** Each flagged group was decided by a written
rule that reads the page: the date line, heading, or title above the value,
the day and month columns of its table, and the labels of its row and column.
A decision for a single page was made only after that page was read.

| Outcome | Values |
| --- | ---: |
| Re-dated to the date the page prints for the value | 6,430 |
| Date withdrawn, because the page prints none for the value | 2,472 |
| Retyped from the label of the row or column | 240 |
| Flagged by a date test and kept, because the heading or row states no other date | 1,796 |
| Flagged by a label test and kept, because the column heading agrees with the type | 420 |
| Date candidates left open | 261 |
| Label candidates left open | 598 |

All but one of the corrected values belong to the records for bodies other
than Mars. A withdrawn date is not replaced. The value keeps its expression
and its place in the source and carries no date, as in the star catalog that
follows the observations of 1589 and in table rows that print a day without a
month. Of the 240 retyped values, 51 take another quantity type, 32 another
body, and 63 a star or reference point that the label names. The other 94
carry a label for an object that the catalog’s subject list does not hold.
They are marked as unassigned table entries, no longer as readings of the
planet.

The rebuilt catalog was compared with release 1.3.1 value by value. The 9,142
revisions fall on 9,127 values, and no other value differs in type, subject,
role, date, expression, or exact value. The ephemeris test had no part in
choosing a correction. Rerun on the corrected catalog, it flags 713 values in
place of 964. Of the 251 it no longer flags, 156 were re-dated, 73 were
retyped, and 22 had a date withdrawn. It flags no corrected value that it did
not flag before.

**Still open.**

- 261 dated values whose printed date the rules do not settle. They keep the
  date of release 1.3.1.
- 598 values whose label may replace their type or subject. Most stand beside
  a label printed inside a column of values, which may belong to the values
  below it. They keep the type and subject of release 1.3.1.
- The roles. The computed rows of the comparison tables are still marked as
  Tycho’s reductions.
- The groups that the ephemeris test still flags. Not all have been read.

**Limits.** The checks were made against the project’s editions of the logs,
not against scans of the printed pages. Clock times and values the catalog
leaves unclassified were not sampled. Values typed inside prose are covered
only by the ephemeris test and the sample. The label tests differ in
precision, and the small flagged groups are not all read. Among the sampled
values that no test flagged, 2 of 98 for the other bodies had a wrong type or
subject, so faults of this kind remain where no test looks. The printed
expressions and their exact values are not in question. The release check
recomputes them.

Check the date, type, and subject of a Tycho log record for a body other than
Mars against the printed page before relying on it. The studies on this site
select their inputs by written rules. [Each selection was rerun](studies.md) on
release 1.3.2. Four of the six earlier studies select the same inputs. The
printed predictions study had flagged a Venus entry that stood 51° from the
ephemeris. With the date its heading prints, the entry lies 3′ away.

## Milestones

The research program gives each milestone’s
[deliverable and completion criterion](research-plan.md#next-research-milestones).

| Milestone | Status |
| --- | --- |
| First astronomical subset | Open. The 1595 inputs are a date-level selection. Observing times, sites, instruments, and correction states are not yet established for them. |
| Historical calculation reconstruction | Open. |
| First observation–prediction comparison | A date-level comparison is published for 1595. A measurement-level comparison is open. |
| Parallax feasibility | Open. The published correction comparisons are groundwork, not recovery experiments. |
| Scientific visualization | Open. |

## Done to date

| Date | Result |
| --- | --- |
| November 26, 2026 | Catalog 1.3.2: corrections from the audit of the Tycho log records. 6,430 values take the date the page prints for them, 2,472 give up a date carried from an earlier entry, and 240 are retyped from their labels. 710,420 quantities and 115,972 source groups. |
| November 25, 2026 | [Audit of the Tycho log records](#audit-of-the-tycho-log-records): label, date, ephemeris, and sample tests on every record of the four logs. The Mars records hold one mistyped reading. The records for the other bodies hold 10,959 date candidates and 1,235 label candidates of one family. |
| November 25, 2026 | Study: [The parallax of Mars in 1587](mars-parallax-1587.md). Five pairs of sessions give −312″ to 289″. The distances fix neither the 302″ in the log nor the 13″ of DE441. |
| November 25, 2026 | Study: [Tycho’s solar theory](solar-theory.md). His apogee and eccentricity reproduce from the printed intervals. His 3′ solar parallax and small refraction displace the equinoxes by three hours and enlarge the eccentricity by 6%. |
| November 25, 2026 | Reproduction: [the opposition table against DE441](mars-oppositions.md#the-opposition-table-against-de441). All fourteen longitudes fall within 4′. The tabulated instants differ by up to three hours in a seasonal pattern that matches a solar equation 7′ too large. |
| November 25, 2026 | Study: [Printed predictions for the Moon and planets](printed-predictions.md). Alphonsine longitudes of Saturn run 2.9° ahead in 1590 and 1591 while the Copernican ones stay within 10′. Copernican longitudes of Mars are within 37′ away from opposition. |
| November 25, 2026 | Verification: the release check now recomputes 123,591 exact historical values from their printed expressions, reports any check it skips, guards the totals in the source directory, and decompresses the database once beside the download. |
| November 25, 2026 | Review of the two parallax studies: every table now regenerates from a script and committed inputs, the printed inputs are tied to catalog entries, and the Venus scenario comparison covers all seven pairs of March 1590. |
| November 25, 2026 | Study: [Historical refraction tables against modern refraction](refraction-tables.md). Tycho’s fixed-star table stays within 1′ of modern refraction from 4° to 16° and stops at 20°. His solar table runs 4½′ higher. |
| November 25, 2026 | Study: [Mars at the oppositions of 1580 to 1600](mars-oppositions.md). Tycho’s longitudes agree with a modern ephemeris within 5′ at nine oppositions. The printed table predictions miss by up to 4.7°. |
| November 25, 2026 | Review of the 1595 Mars study: inputs selected from the catalog by a written rule, printed hours used, the JPL DE441 ephemeris added, and sensitivity, validation, and prediction tables published with a regeneration test. |
| November 25, 2026 | Study: [Mars reverses direction in 1595](mars-apparent-motion.md), with its inputs, residuals, figure, and script. |
| November 25, 2026 | Study: [Mars, Jupiter, and Saturn corrections](planetary-parallax-comparisons.md) and [Mercury and Venus parallax](mercury-venus-parallax.md). |
| November 25, 2026 | Catalog 1.3.1: four-volume review of Tycho’s logs. 710,420 quantities and 115,972 source groups. |
| November 25, 2026 | Catalog 1.3.0: full coverage of Tycho’s logs, adding Mercury, comets, fixed stars, and the new star of 1572. |
| November 25, 2026 | Catalog 1.2.0: Sun, Saturn, and Venus from Tycho’s logs. |
| November 25, 2026 | Catalog 1.1.0: Jupiter and the Moon from Tycho’s logs. |
| November 18, 2026 | Catalog 1.0.1: qualified JPL placeholder fields and uncertain declination signs. |
| November 10, 2026 | Catalog 1.0.0: first public release, with Tycho’s Mars records, seven supplementary books, modern optical collections, and the reconciliation with Pafko’s transcription. |

The [catalog release notes](../CHANGELOG.md) describe each release.

## Next up

1. **Audit of the other works.** Apply the label, date, ephemeris, and sample
   tests to the seven supplementary books and the modern collections, and
   compare the records of the books with the current editions. Correct what
   the tests find in a further release.
2. **Open candidates in the Tycho logs.** Settle the 261 dates and 598 labels
   that the [audit](#audit-of-the-tycho-log-records) left open, and the roles
   of the computed rows in the comparison tables.
3. **Printed predictions of the Moon.** Record the hours of the 59 lunar
   predictions and of the log’s values beside them, then add the Moon to the
   [published comparison](printed-predictions.md).
4. **The 1600 opposition.** Establish the calendar of the 1599 to 1601 entries
   from the printed pages, then add that opposition.
5. **Refraction tables.** Record the altitude of each entry in Tycho’s lunar
   table, Longomontanus’s tables, and Riccioli’s reprint, then add them to the
   [published comparison](refraction-tables.md). Reproduce Tycho’s refraction
   values from the solar altitudes behind them.
6. **Printed calculations.** Reproduce selected historical results at their
   stated epochs from the documented parameters, beginning with the steps from
   the log’s readings to each tabulated opposition and the parallax campaign
   of 1582 and 1583.
7. **Parallax feasibility.** Test what diurnal parallax the observations could
   recover at their actual cadence under declared error assumptions.
8. **Catalog explorer.** Build the first interactive view of the catalog.
