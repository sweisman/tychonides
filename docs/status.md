# Project status

This page records what Tychonides has finished, what is under way, and what
comes next. The [research program](research-plan.md) defines the objectives and
milestones. The [source directory](data-sources.md) defines catalog coverage.
Finished analyses are collected on the [studies page](studies.md).

Last updated November 26, 2026.

## Objectives

| Objective | Status | Done so far | Next step |
| --- | --- | --- | --- |
| Observation catalog | Available, [audited](#audit-of-the-tycho-log-records) | [Release 1.3.4](../resources/catalog/README.md#download) holds 710,195 quantities from Tycho’s four logs, seven supplementary books, and modern optical collections. The records of the four logs are audited and corrected. The [other works](#audit-of-the-other-works) have had three audit passes. The open lists of both audits are closed. | The [planned acquisitions](data-sources.md#planned-ingestions) |
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

Of the 150,268 quantities from Tycho’s four logs in release 1.3.4:

| State | Quantities | Share |
| --- | ---: | ---: |
| Exact value with an assigned type, subject, and role | 57,553 | 38% |
| Exact value with a type, no subject | 113 | under 1% |
| Exact value, type not yet assigned | 24,604 | 16% |
| Printed expression kept, no numerical interpretation yet | 67,987 | 45% |
| Incomplete value | 11 | under 1% |

Release 1.3.3 held 150,443. The audit merged 175 records that repeated a
printed value or held a part of one into their readings. The first row of
this table as published for release 1.3.3 counted 1,467 typed readings that
had no subject, and one value that the public database holds without a
numerical interpretation. The audit read each typed reading without a
subject, and the 113 that remain are
[listed with their reasons](#audit-of-the-tycho-log-records).

The studies draw mainly on the first row. In the database’s `metadata` table,
`normalization_counts` now covers the whole catalog. The entries written for
the first Mars selection of 17,043 quantities are kept under
`first_mars_selection`. The manifest gives the totals by source.

## Audit of the Tycho log records

Release 1.3.2 carries the corrections from an audit of the records of Tycho’s
four log volumes in release 1.3.1. Each correction cites the printed label or
date line it rests on and keeps the earlier interpretation beside it. No
printed expression or exact value changed.

The audit covered the 150,443 quantities from the four logs. The seven
supplementary books (303,175 quantities) and the modern collections (256,802
quantities) have had a [first audit of their own](#audit-of-the-other-works).

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

**Open lists, closed after release 1.3.3.** The candidates that release 1.3.2
left open were read on the page, one group at a time. The logs were then read
again by label, by date line, and by reference star, and the typed readings
that carried no subject were read table by table. Last, every line that
prints a day of its own inside the entry of another day was read. The
corrections are in release 1.3.4.

| Outcome | Values |
| --- | ---: |
| Re-dated to the day that their row, column, heading, caption, or sentence prints | 2,720 |
| Date withdrawn, because the page prints none for the value | 182 |
| Type, body, object, or reference star revised from a printed label | 1,829 |
| Typed reading without a subject given the object and the role that its table prints | 1,275 |
| Reading left without a subject by release 1.3.2 given the object that its label names | 87 |
| Subject or reference star revised where a label gives the value as taken from a star | 175 |
| Subject revised from the heading of a column timed by a star | 169 |
| Role revised in the comparison tables | 380 |
| Role revised in the reckonings that the automated intake typed as readings | 980 |
| Typed value in prose given the body or star, and the role, that its sentence states | 12 |
| Refraction correction without a subject given the body or star of its table | 5 |
| Second record of one printed value merged into its reading | 153 |
| Reading given the whole expression that its table row prints | 11 |

- **Dates.** The 261 open values are decided: 120 are re-dated, 46 lose a
  date that the page does not print for them, and 95 are kept. The date line
  above each reading and the day printed on its own row were then compared
  again through all four volumes. Of the 2,720 re-dated readings, 1,884 stand
  in volume XIII, most of them in tables that print their own day and month
  on the row. A value is re-dated only to a day that its own row, column
  heading, heading, caption, or sentence prints. Two event groups that join altitudes
  of two days lose their date.
- **Days printed inside an entry.** The date test read headings and short
  date lines. It did not reach a sentence that opens “On 8 October” in the
  entry of the 10th, a heading that words its day at length, or a table
  column headed with a day. Every such line was then read: 159 lines that
  print a day which none of their dated values carried, 30 whose values
  carried it together with another day, 19 headings under which most values
  carried another day, and one table with two columns headed by a day. A
  value is re-dated where its own sentence prints the day for it: the day it
  was observed or found on, or the day of the opposition that the sentence
  derives. Rows that run on from such a line move with it. A day named for a
  comparison, an interval, or a reference to another entry leaves the value
  with the date of its entry, and so do the steps that follow without a day.
  The tables that follow a re-dated sentence were then compared with it.
  Three still carried the date of their entry, and their 41 values moved
  with their sentences. Last came the plain captions that name a day above
  a reckoning, such as “For the place of the Moon on 10 December”: 712
  captions. Under 39 of them some rows carried another day. Seven were
  faults, and their 83 values moved to the day of the caption. The other 32
  are notes of the editor, references to another entry, comparisons, and
  tables whose rows print their own days. In all, 804 values are re-dated
  and 26 lose their date. 45 lines are kept as they stand. The larger
  faults:
  - The observation of the solar eclipse of 1600 (XIII pp. 196–200) is
    headed “on 30 June, Old Style; 10 July, New Style.” Its 199 values
    carried 3 July, the day of the entry before. They now carry 10 July, in
    the style of the entries around it.
  - The calculation for 8 February 1595 (XII pp. 467–468), with the right
    ascension and declination of Venus, carried 7 March: 37 values.
  - A calculation of Jupiter’s place “from the observations made on 29
    June” 1593 (XII p. 278) carried 2 July, the entry in which it stands:
    36 values.
  - The place of Jupiter at its opposition of 25 March 1590 (XII p. 43)
    carried the 21st.
  - A letter of 1598 (XIII pp. 151–152) and the observations that Kepler
    sent in 1600 (XIII pp. 247–252) give observations day by day. Each run
    carried a single day from the section before it. Every line now has the
    day it opens with, in the years 1483 to 1599.
  - The notes on the opposition of Saturn in 1584 (X p. 320) carried 31
    March 1570, the date of an earlier observation copied above them.
  - An observation of Venus “on 9 January” 1587 (XI p. 204) stands in the
    entry of the 15th. The table under its sentence kept the 15th: 18
    values. The ephemeris test, rerun on the corrected catalog, pointed to
    the table. The correction rests on the sentence.
  - The investigation of the Moon’s motion “for 6 February” 1595 (XII
    p. 376) carried the 7th: 25 values. The later parts of a calculation of
    the Moon’s place “on 6 September” 1585 (X pp. 379–380) carried 28
    February, the heading above a run of calculations: 20 values. The same
    rerun of the ephemeris test pointed to the first, and the captions were
    then read throughout.
- **Labels.** Every run of open label candidates was read: 558 values in 218
  runs. Three further passes read the rows whose own label names another
  object than the one carried to the reading, the labels that point back to
  an object named just before (“the same,” “its declination”), the distances
  that kept the reference star of an earlier heading where their own row
  names another (212), and the columns headed “Distance from” a star, where
  the star and not the observed body stood as the subject (232). A value is
  revised where the page names another quantity, body, object, or reference
  star. The declinations that stood as those of Venus in the table of 17
  March 1595 (XII p. 470) are the Sun’s: the other columns of the table give
  the azimuth and the altitude of the Sun at its rising.
- **Stars without a name of their own.** A reading whose label names a star
  takes the catalog’s name for it where the label gives one. Otherwise it
  takes the subject “fixed star,” which 4,988 readings of the logs already
  carry. Release 1.3.2 left 94 retyped readings without a subject and
  described their labels as naming objects that the subject list does not
  hold. That was wrong for most of them. The lookup compared the printed
  words with the catalog’s names, so that “cor ♌” did not find “heart of
  Leo.” The labels were read again. 65 of the 94 now carry a name, among
  them 20 the heart of Leo and 15 the bright star of Aries, and 28 carry
  “fixed star.” 55 are places of a star that a reckoning starts from and are
  typed as inputs. The other 38 take back the role they had before their
  subject was withdrawn. One reading, labeled “Declination, cor.,” names no
  object and stays as it was.
- **Values taken from a star.** A right ascension “from Aldebaran” is the
  place of the object under study, found from that star. In 170 readings a
  star stood as the subject. 132 of them are right ascensions in the star
  entries of the catalog section of volume XI, each found from a reference
  star, where a query for the right ascension of Aldebaran returned the
  places of other stars. The other 38 are distances, differences, and places
  of the Moon, the planets, and three stars in volumes XI to XIII. Each
  reading now carries the object that its table gives the value to, with the
  star as its reference. Five readings found beside them are corrected too: a
  distance between two stars that carried Mercury, a meridian altitude of
  Jupiter that carried a star, a declination typed as an altitude, an arc of
  time typed as a right ascension, and a distance without its reference
  star.
- **Typed readings without a subject.** 1,349 readings of the logs had a
  type, no subject, and the role of an input. The automated intake had typed
  them from the heading of their column and given each that role. The 1,348
  that stand in tables were read, table by table. 1,275 take the body,
  comet, or star that the page names for
  them: the Sun 24, the Moon 3, Venus 2, Mercury 37, a comet 76, and stars
  1,133. They also take the role that the page shows: 658 are readings of
  the session, 393 are results worked out on the page, 6 are values set to
  be adopted, and 3 are places from tables. The other 215 are fed into a
  reckoning or stand in a table of star places, and keep the role of an
  input. 73 are kept as they were. Their tables name a point of the ecliptic
  or the letters of a figure, name no object at all, or print a quantity
  that the revision cannot retype.
- **Typed values in prose.** 14 longitudes that stand in sentences had a
  type, no subject, and the role of an input. 12 take the body or the star
  that their sentence names, and its role: the Moon in 7, Saturn in 2, and
  three stars. Two are points of the ecliptic and stay as they are. One
  value beside them, printed “latitude 2° 47′ 0″ M.” in the notes on the
  opposition of Saturn in 1585 (X p. 409), stood as a distance of Saturn
  from Aldebaran. It is the southern latitude of Saturn.
- **The remaining typed readings without a subject.** The corrected catalog
  was then searched for every typed reading that still had no subject. Seven
  stood in none of the lists above, because they are not typed as inputs.
  Five are refraction corrections. The catalog carries the like rows of the
  same entries as corrections of the body whose place the table reckons, and
  these five now follow them: four of Mercury (XI pp. 85 and 339, XII
  p. 476) and one of the bright star of Perseus (XI p. 299). A declination
  “by computation” (X p. 174) and an altitude of 20° (XI p. 333) name no
  object and stay as they are.
- **Records held twice.** The logs entered the catalog in two passes, and
  each kept a record of some table cells. In 153 cells the catalog held one
  printed value twice: as a reviewed reading and as a second record without
  a subject or, in one cell, without a date. The second record is merged
  into the reading, which lists it, and the catalog has 153 fewer
  quantities. Three of the second records carried p. 457 of volume XII for
  rows that stand on p. 458. No other log record has a page that runs behind
  the page of an earlier line. In 11 more rows the catalog held the degrees,
  minutes, and seconds of one value as three records. The reading now gives
  the row’s whole expression, and the 22 other records are merged into it.
- **Columns timed by a star.** Many tables time a session by a star and head
  a column with its name and “east” or “west.” The catalog leaves the
  quantity of these values unassigned. In 169 of them the body of the block
  stood as the subject, and the star now does. The further candidates of
  this test, which release 1.3.3 left open, were read with their tables. The
  113 that stay unchanged are values of the body itself, in rows that follow
  a star’s row or in tables that hold a star’s column.
- **Roles.** A place that its own row or line label gives to a named model,
  a set of tables, or an ephemeris is a prediction. A stated difference
  between such a place and the observed one is a comparison. An input is only
  what the page feeds into a calculation. A reduction is the author’s own
  result from observations.
- **Roles in the reckonings.** The automated intake typed the rows of a
  reckoning as readings. A selection of readings by role therefore returned
  results, steps, and star places with the observations. The hand-reviewed
  records type such rows by what their label says, and 980 readings in the
  tables of the automated intake now follow them. 539 values that a label
  introduces as a result (“Therefore the right ascension of the Moon,”
  “Corresponding longitude”) or names as a difference of ascension are
  reductions. 276 right ascensions and declinations of a star that a
  reckoning starts from are inputs. 157 values that a label sets, puts, or
  limits are adopted values. Eight sides and angles named by the letters of a
  figure are steps. Every group of labels was read, and 17 candidates keep
  their role, among them places read on the zodiacal armillae with a star
  “set” and declinations observed in the session. 105 of the 980 also carry
  another correction listed here. The rule reads the label of a
  table row. Values in prose, rows without a label of their own, and star
  places whose type is unassigned are outside it.
- **Ephemeris groups.** The test flags 713 values in release 1.3.3. Of these,
  203 are predictions, inputs, or corrections, which need not agree. Every
  remaining group that differs by 3° or more was read: 83 groups. Most are
  the faults above in a form the label rules did not read, such as a table of
  Spica or Arcturus inside the observations of Mercury, and are corrected
  with them. A calculation of the Moon’s place “from selected observations
  of 21, 22 and 23 December” 1594 (XII p. 328) carried the 23rd throughout.
  Its first part is headed for the 21st, and its 45 values now carry that
  day. The rest are faithful to the print. Rerun on the corrected catalog,
  the test flags 376 values. 219 are predictions, inputs, or corrections.
  The other 157 stand in 81 groups, and every group was read, the small
  differences included. 86 values in 23 groups are the
  [suspected readings](edition-findings.md) of volumes X to XII and the two
  Jupiter sessions printed under 1590, which the catalog keeps as printed.
  49 values in 37 groups stand in the entries of 1599 to 1601, whose
  calendar the catalog does not state. 22 values in 21 groups are kept
  because nothing on their page speaks against them: the early notes of
  1563 to 1570, three places of Mars taken from a globe, and eight values
  that pass the margin of the test by less than 1½°.

**Kept as they stand.** Every open list is decided. These records were read
and stay as they are, for the reason given.

- 73 typed readings without a subject. Their tables name a point of the
  ecliptic or the letters of a figure, or name no object. For three of them
  the page names another quantity, which a revision cannot give to a reading
  whose notation the catalog holds as unresolved.
- 35 readings that this audit left without a subject. The label shows that
  the body of the block is wrong for them and names no other object.
- Five more typed readings without a subject, none of which names an
  object: the two points of the ecliptic in prose, the reading labeled
  “Declination, cor.,” the declination “by computation,” and the altitude of
  20°. With the 73 and the 35 they are the 113 of the
  [table above](#state-of-the-catalog-rows).
- Three table cells that hold one printed value in two records, each with
  its date: a declination of Mars on 4 March 1587 (XI p. 183) and two of
  Jupiter on 31 December 1595 (XII p. 440). A revision merges only a second
  record that belongs to no observation of its own.
- Roles of the rows that the rule for the reckonings does not read. The 335
  typed readings of that kind were surveyed. Five were flagged and read on
  the page. One was a fault, the latitude of Saturn above.
- Records taken from a line that the edition sets wholly in brackets: 94
  records on 34 lines, 87 of them without a type. Such a line is the English
  of a heading, a bracketed entry of the print, or the edition’s own note on
  the page. The numbers in the edition’s notes repeat what the page prints,
  and the ones that carried a date have lost it.

**Limits.** The checks were made against the project’s editions of the logs.
Scans of the printed pages were read only for the
[suspected problems of the sources](#audit-of-the-other-works). Clock times
were not sampled. Values that the catalog leaves unclassified were tested for
their dates, for columns timed by a star, and for labels that give a value as
taken from a star, and not otherwise. A step that follows a dated sentence
without naming a day keeps the date of its entry, unless it runs on from that
sentence in so many words. A date that the audit moved asserts no calendar,
so the entries of 1599 to 1601, which mix the two styles, state the day as
printed and not its style. The label tests differ in precision. Three
classes were found while reading for another one, and no test had looked for
them: values taken from a star, the roles in the reckonings, and the days
printed inside an entry. Among the sampled values that no test flagged, 2 of
98 for the other bodies had a wrong type or subject, so faults of this kind
may remain where no test looks. The printed expressions and their exact
values are not in question. The release check recomputes them.

Check the date, type, and subject of a Tycho log record for a body other than
Mars against the printed page before relying on it. The studies on this site
select their inputs by written rules. [Each selection was rerun](studies.md) on
release 1.3.2. Four of the six earlier studies select the same inputs. The
printed predictions study had flagged a Venus entry that stood 51° from the
ephemeris. With the date its heading prints, the entry lies 3′ away.

## Audit of the other works

Release 1.3.3 carries the corrections from a first audit of the seven
supplementary books and the modern collections in release 1.3.2. A second
pass after that release ran the tests the first had left out. A third
compared every reading of the books with the current editions. Release 1.3.4
carries the 20 corrections of the second pass, the 1,629 roles set by the
rule for places computed from tables, and the 556 readings that the third
pass gave the expression their line prints. What waits on an edition or is
untested is listed below.

**The books.** Four tests were run on the 303,175 quantities.

1. **Named points.** Row labels, column headings, and the words before a
   value in prose were searched for an apogee, a perigee, an aphelion, or a
   node where the catalog gives the longitude of the Sun, the Moon, or a
   planet. The second pass read the 27 tables whose caption names such a
   point and the 300 table cells that the column test could not place.
2. **Ephemeris.** Each dated place of the Sun, the Moon, and the planets was
   compared with JPL Horizons, in both calendars where the record states
   none. Of 3,977 values tested, 227 were flagged.
3. **Dates.** Each value with one complete date was compared with the day and
   month printed for it: in the date columns of its table, in the nearest
   date at or above it, or in a day named after that date, as in “on the
   12th” and “the following day.” Six of the seven books hold such values,
   19,710 in all. 16,012 agree and 3,698 were flagged.
4. **Sample.** 100 exact values that no test flagged were drawn at random and
   read against the edition. 36 of them are coordinates of the Sun, the Moon,
   or a planet.

The first test found one family of fault. The longitude of an apogee, a
perigee, or a node was recorded as the longitude of the body. Other records
in the catalog already name such points, as in “Sun apogee” and “ascending
node of Mars.” Release 1.3.3 gives 98 values their printed subject in the same
form:

| Subject in release 1.3.3 | Values | Works |
| --- | ---: | --- |
| Sun apogee | 81 | Riccioli’s two works, Snellius, *Progymnasmata* |
| Sun perigee | 1 | *Astronomia Reformata* |
| Apogee of Saturn, Jupiter, or Mars | 6 | Longomontanus |
| Ascending node of Saturn, Jupiter, or Mars | 6 | Longomontanus |
| Node of Mercury or the Moon | 4 | *Almagestum Novum* |

Each correction cites the heading or the words that name the point and keeps
the earlier interpretation. The quantity type, the printed expression, and the
exact value did not change.

The second pass found the same fault in two more tables and one sentence.
These 15 corrections are in release 1.3.4:

| Subject after the second pass | Values | Locus |
| --- | ---: | --- |
| Sun apogee | 5 | Snellius, p. 105, table of the position of the Sun’s apogee |
| Ascending node of Saturn, Jupiter, or Mars | 3 | Longomontanus, p. 383, column of the northern intersection |
| Descending node of Saturn, Jupiter, or Mars | 3 | Longomontanus, p. 383, column of the southern intersection |
| Southern limit of Saturn, Jupiter, or Mars | 3 | Longomontanus, p. 383, column of the southern limit |
| Saturn, with the Sun as the reference | 1 | *Almagestum Novum*, p. 554, a place of Saturn “seen from the Sun” |

“Descending node” and “southern limit” are new subjects in the catalog, formed
like the existing ones. The other tables and cells that were read name no
point for their values or already carry the right subject. Among them are the
columns of the lunar apogee, which the catalog holds as calculation angles and
not as places of the Moon.

Of the 3,698 flagged dates, 2,772 stand in three kinds of layout that print
the date away from the value, and each kind was checked by its structure.
The 1,200 cells of the libration tables in *Astronomia Reformata* follow the
year of their row and the order of their month columns. The 583 cells of the
two solar ephemerides in the *Progymnasmata* follow the day of their row and
the order of their month columns. The 989 values in Origanus’s nativity
figures form one unbroken run for each of the 79 figures. 70 runs stand with
the year and day their own figure prints. In the other 9 the figure prints
the day and the year on separate lines, and the day was read. The other 926
were listed by passage beside the date the test saw instead. Most are rows of
a table that carries its day in a column, rows of the equinox tables whose
last columns print the day of the equinox, and steps of a worked example
whose date line stands far above. About twenty groups that the list did not
explain were read. The rest were judged from the list and not read one by
one. One group is a fault. Riccioli
reports Regiomontanus’s meridian observation “on 11 March at noon” of 1473
and finds the equinox on “the preceding day, the 10th.” Five values reduced
from the noon observation carried the day of the equinox. Release 1.3.4
gives them March 11, as the table under the passage does.

The date test left out 5,608 values that carry a year or a month alone, or
more than one date. They were tested afterwards for the year and the month
they claim. For 2,249 the year is printed on the line of the value, in the
rows of its table, or in the twelve lines above. 189 claim no year. The
other 3,170 were traced by group to the line that states their year. 2,196
are places and magnitudes in the star catalog of the *Progymnasmata*, which
its heading gives “for the completed year 1600.” 912 more in that book are
places of stars for the completed year 1585 and places and calculations for
the close of 1572, each under a heading or a sentence that says so. The
remaining 62 follow a year stated elsewhere in their passage. Among them are
Copernicus’s two observations of Spica, the comet of 1607 in Longomontanus,
an eclipse figure in Origanus, and the Mercury observations in *Astronomia
Reformata* whose year the edition findings question. Of the 507 values that
claim a month, 465 print it within the same reach, and the other 42 follow
the date at the head of their passage. No year or month is wrong. One value
keeps a single month where its sentence names two. Riccioli reports that
Hevelius saw Saturn round “in September and October, about the 20th degree
of ♓,” and the catalog dates the place to September.

The flagged groups of the ephemeris test with the largest differences were
read. All follow the edition. They are misprints of the original that the
edition keeps, some with its own correction beside them, steps of worked
examples, positions written in horoscope figures, and places computed by
other authors. They are questions about the sources, not faults of the
catalog. Origanus’s horoscope figures hold 81 of the flagged values, and only
the four with the largest differences were read. The 160 flagged values that
differ from the ephemeris by less than 3° were taken up afterwards. 96 are
predictions, inputs, or corrections, which need not agree. The other 64
stand on 20 pages, and all were read. None is a fault of the catalog. They
are mean places of worked examples, figures of a horoscope, observations of
earlier astronomers that the authors quote, cells of the libration tables,
and the suspected problems of the sources already listed in the edition
findings. The flagged dates in Snellius that were read belong to long
calculations whose date line stands far above them.

In the sample, one value of 100 had a wrong type. Longomontanus gives a lunar
distance in sixtieths of the Earth’s semidiameter, and the catalog records its
minutes as an angle. No sampled value had a wrong subject or date. Three had a
doubtful role.

**Readings against the current editions.** The fault in the sample was a
reading that held only part of what its line prints: the minutes of the
distance, without the whole parts before them. The editions have also been
revised since the catalog was made. The third pass therefore looked up each of
the 303,175 readings at its own place in the current edition of its book.
302,466 stand there whole. The other 709 were read.

- 518 are right as they stand. The edition prints the same numerals in
  another notation, in another order, or on another line, or the line prints
  two quantities side by side.
- The others led to 178 corrections. 77 readings in Longomontanus had lost
  the count of zodiac signs before their degrees. Others held hours without
  their minutes, degrees without their minutes, an interval without its days,
  or a length in sixtieths as an angle. In 27 the edition has changed the
  numerals since the catalog was made. The
  [edition findings](edition-findings.md#progymnasmata-readings-corrected-in-the-edition-after-ingestion)
  list those.
- 50 records held nothing but the rest of such an expression, as the whole
  parts of the sampled distance did. Each was merged into the reading it
  belongs to, and that reading lists it. The catalog has 50 fewer quantities.

A second test compared the numerals on each of the 62,105 lines that hold
readings with the same line of the current edition. 70 lines differ. The 30
readings on them that the first test had passed were read, and each prints
the same value as before.

244 further readings are values that the catalog had joined from neighboring
cells of a table row and listed under the first cell alone. Their expression
now gives the cells together, and their values did not change.

134 more are values whose parts do not stand side by side. In 94 the parts
are on one line with other text between them: a correction that the edition
sets inside the value, the second value of a cell that stacks two, or words
of the sentence. In 39 the parts are on separate lines, where a row leaves a
cell blank under the hour or degree of another row, or a sentence runs across
a line or page break. The expression now gives the parts in the order of the
value, with an ellipsis for what stands between, as in “365 days, 5^h^ …
24^m^ 38^s^.” Three of them print as one expression once the words between
are included. One cell prints 41 degrees within a sign, and it keeps its
whole expression and no value. No value changed. Two readings stay under
their first part: a number written as a word that runs on to the next line,
and an eclipse extent in digits.

1,345 values in the tables of the *Astronomia Reformata* take their degrees
from a row above, where their own cell is blank. Each was compared with the
nearest filled cell above it in the current edition. All agree.

Each of these changes is an edition reading, a third kind of revision beside
the reading and date revisions. It gives the reading the expression that the
cited line prints, converts it like any other reading, and keeps the earlier
expression and value in the review record.

**The modern collections.** A sample of observations of each body in each
collection was compared with the apparent place from JPL Horizons. The median
difference is 0.3″ to 1.0″ in all twelve collections tested. The outliers
were read and led to one fault. In the JPL series Washington 6b and 6c, 350
right ascensions and declinations stand as whole minutes with zero seconds.
The USNO publication of the same observation prints 338 of them without
seconds. The other 12 belong to observations that the USNO tables in the
catalog do not hold. Among the fields of these two series that do carry
seconds, the last digits are spread evenly, so a measured declination would
end in zero seconds about once in 6,000 times. Release 1.3.3 marks the 350
fields `jpl_zero_seconds_placeholder` and gives them no derived coordinate.
The printed fields are unchanged.

The second pass tested what the first had skipped and found no further fault.

- The first sample left out 7,895 observations of named minor planets, of
  Hyperion, and of a comet, and 15,416 Carlsberg observations outside the 25
  largest series. Every body in every collection is now sampled. The median
  difference is 0.6″ for 1,668 Carlsberg observations and 0.5″ for the two
  USNO series. The ten observations of Geographos differ more only when they
  are taken as geocentric. The source gives them as topocentric, and the
  catalog records that.
- 1,098 USNO observations print one of their two coordinates incompletely.
  Their complete coordinate has a median difference of 0.33″, and none
  exceeds 30″. The incomplete coordinate lies within its printed minute in
  1,097 of them.
- The 53 JJMO observations of 2001 and 2003 were checked against themselves.
  Each printed difference is the difference of its two settings, and each
  separation is the difference times the scale of its year, to the rounding
  of the printed figures.
- The two whole-minute right ascensions in the JPL series Washington 6a and
  Tokyo are measurements. Each agrees with JPL Horizons within about 1″, and the
  CDS publication of the Tokyo observation prints the same zero seconds. They
  stay unqualified.

**Waiting on the edition.**

- An interval in Longomontanus that the edition gives as “45 days 3 minutes
  42 [seconds]” where the printed page reads 45 days 3 hours 42 minutes. The
  catalog holds the edition’s wording without a value. It takes the printed
  reading once the edition is corrected.

**Suspected problems of the sources.** The audit met 29 places where a
printed value is in doubt, listed in the
[edition findings](edition-findings.md). Each was read on a scan of the
printed page. In 27 the scan reads as the edition does, so the doubt is
about the print or the observation itself: the year of Tycho’s Mercury observations in *Astronomia
Reformata*, the month of an eclipse example there, a row of its libration
tables, a day in the *Almagestum Novum*, a month in the *Progymnasmata*, the
unit of a lunar motion in Longomontanus, a day in Snellius, the year of two
Jupiter sessions in Tycho’s log, and nineteen single readings there. The catalog
keeps each as printed. Two are errors of the edition: the interval in
Longomontanus above, and the unit marks of the hourly table of the Sun’s
motion in the *Progymnasmata*, where the catalog already records the motion
as an angle.

**Kept as printed.** One USNO declination of the Sun, at JD 2443901.224 in
the first Washington series, is printed as −18° 37′ without seconds. It lies
8.4′ from the Sun’s place. The catalog marks it incomplete and gives it no
derived value.

**Roles.** On the rows of comparison tables that are labeled with an author
or a set of tables, the books gave most values the role of a historical
input and about 55 the role of a historical prediction. The
[rule for the logs](#audit-of-the-tycho-log-records) now applies to the
books: 1,629 such values become predictions or comparisons, 1,577 of them in
the *Astronomia Reformata*.

**Not tested.** Values the catalog leaves unclassified. The checks were made
against the project’s editions. Scans of the printed pages were read only for
the suspected problems above.

**Effect on the studies.** Every [study](studies.md) is rerun on each
release. On release 1.3.2 four of the six earlier studies selected the same
inputs. In the [printed predictions](printed-predictions.md) eight
predictions took corrected dates and the log gained one value. The Venus
longitudes on XII p. 71, which release 1.3.1 dated July 15, 1590 and the
study had flagged at 51° from DE441, take the printed September 1 and lie 3′
and 53′ away. Four Mercury predictions on XI p. 79 moved from October 29 to
October 25, 1586. The seven Venus pairs of March 1590, which release 1.3.1
dated December 20 from an earlier entry, took the days of their table, the
ones the [study](mercury-venus-parallax.md) had assigned. In the
[1587 parallax study](mars-parallax-1587.md) one distance had been typed as
an altitude. Without it the selection held 47 distances and the fit of both
nights gave 18″ ± 32″. On release 1.3.3 no selection changed.
On release 1.3.4 six select the same inputs. The 1587
parallax study selects the same 48 distances, and three readings that it
leaves out take a corrected reference star. The
[printed predictions](printed-predictions.md) keep their 485 predictions and
every difference from DE441. The log has 13 more values of its own on four
dates, and the differences from the log changed there. The 98 places that
release 1.3.4 newly types as predictions enter no comparison: the catalog
records no model name for 78 of them and no single date for 20.

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
| November 26, 2026 | Catalog 1.3.4: the open lists of [both](#audit-of-the-tycho-log-records) [audits](#audit-of-the-other-works), closed. In Tycho’s logs 2,720 values take the day that their row, column, heading, caption, or sentence prints, 182 give up a carried date, 4,807 take the type, subject, reference star, or role that their label prints, and 175 records that repeated a printed value or held a part of one are merged into their readings. In the books 1,629 places computed from tables become predictions or comparisons, and 556 readings take the expression their line prints. The [edition findings](edition-findings.md) list the 29 places where a printed value is in doubt. 710,195 quantities and 115,972 source groups. |
| November 26, 2026 | Second pass of the [audit of the other works](#audit-of-the-other-works): named points in captioned tables, dates in every book, and every body of the modern collections. 15 values take the subject or reference their page prints, and 5 take the day of their observation. The corrections are in release 1.3.4. Seven suspected problems of the sources moved to the [edition findings](edition-findings.md). |
| November 26, 2026 | [Printed predictions](printed-predictions.md): DE441 is taken at the printed hour of the calculation for 63 more predictions, and one mean longitude is left out. |
| November 26, 2026 | Catalog 1.3.3: corrections from a [first audit of the other works](#audit-of-the-other-works). 98 longitudes of an apogee, a perigee, or a node in the books take their printed subject. 350 whole-minute coordinates in two JPL series are marked as placeholders. 710,420 quantities and 115,972 source groups. |
| November 26, 2026 | Catalog 1.3.2: corrections from the audit of the Tycho log records. 6,430 values take the date the page prints for them, 2,472 give up a date carried from an earlier entry, and 240 are retyped from their labels. 710,420 quantities and 115,972 source groups. |
| November 25, 2026 | [Audit of the Tycho log records](#audit-of-the-tycho-log-records): label, date, ephemeris, and sample tests on every record of the four logs. The Mars records hold one mistyped reading. The records for the other bodies hold 10,959 date candidates and 1,235 label candidates of one family. |
| November 25, 2026 | Study: [The parallax of Mars in 1587](mars-parallax-1587.md). Five pairs of sessions give −312″ to 289″. The distances fix neither the 302″ in the log nor the 13″ of DE441. |
| November 25, 2026 | Study: [Tycho’s solar theory](solar-theory.md). His apogee and eccentricity reproduce from the printed intervals. His 3′ solar parallax and small refraction displace the equinoxes by three hours and enlarge the eccentricity by 6%. |
| November 25, 2026 | Reproduction: [the opposition table against DE441](mars-oppositions.md#the-opposition-table-against-de441). All fourteen longitudes fall within 4′. The tabulated instants differ by up to three hours in a seasonal pattern that matches a solar equation 7′ too large. |
| November 25, 2026 | Study: [Printed predictions for the Moon and planets](printed-predictions.md). Alphonsine longitudes of Saturn run 2.9° ahead in 1590 and 1591 while the Copernican ones stay within 10′. Copernican longitudes of Mars are within 37′ away from opposition. |
| November 25, 2026 | Verification: the release check now recomputes 123,591 exact historical values from their printed expressions, reports any check it skips, guards the totals in the source directory, and decompresses the database once beside the download. |
| November 25, 2026 | Review of the two parallax studies: every table now regenerates from a script and committed inputs, the printed inputs are tied to catalog entries, and the Venus scenario comparison covers all seven pairs of March 1590. |
| November 25, 2026 | Study: [Historical refraction tables against modern refraction](refraction-tables.md). Tycho’s fixed-star table stays within 1′ of modern refraction from 4° to 16° and stops at 20°. His solar table runs 4½′ higher. |
| November 25, 2026 | Review of the [Mars oppositions](mars-oppositions.md) study: one Copernican prediction of 1591, printed as 247° 42′ with no zodiac sign, is left out where it had been compared within the sign. The Copernican mean for 1591 moves from +48′ to −8′. |
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

1. **Two corrections in the editions.** The interval on p. 180 of
   Longomontanus and the unit marks of the hourly table of the Sun’s motion
   in the *Progymnasmata* are [errors of the edition](edition-findings.md).
   Once the interval is corrected, the catalog takes the printed reading.
2. **Model names for the predictions typed by the audit.** Release 1.3.4
   types 308 more values of the logs as predictions from their labels. A
   revision records the role and the label it rests on, and not the name of
   the table. Record the names. The 78 dated longitudes and latitudes of the
   Moon and the planets among them can then be considered for the
   [published comparison](printed-predictions.md). In the whole release, 319
   predictions and 57 comparisons of the logs and 3,399 predictions and 1,973
   comparisons of the other works carry no model name. The *Astronomia
   Reformata* holds 5,036 of them.
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
