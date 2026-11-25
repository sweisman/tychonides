# Data sources

Tychonides brings historical observing books and modern Earth-based measurements
into a common catalog. This directory lists both ingested collections and planned
acquisitions. Recorded readings, reduced coordinates, calibration data and model
predictions retain their distinct roles and source identities.

**Available** means included in a downloadable release. **Planned** means
identified for future acquisition; it does not imply numerical coverage.

[Ingested historical sources](#ingested-historical-sources) ·
[Modern observing programs](#modern-observing-programs) ·
[Planned ingestions](#planned-ingestions)

## Observing policy

Observation ingestion is limited to **ground-based and airborne visual/optical
observations**, including observations by eye, photographic and electronic
measurements, and infrared or ultraviolet observations. **Space-based observations
and radar measurements are excluded.** Record platform, method and spectral band
where known; unresolved provenance must be resolved before admitting a new
observational collection. These are selection requirements, not a claim that the
current importer automatically enforces every one of them.

A catalog’s geocentric or topocentric reduction label does not identify its
observing platform. Preserve reduced terrestrial observations and their correction
dependencies. Model predictions, format documentation and reference/calibration
resources may support the research but are not admitted as additional observations.
Citing a reference resource does not authorize importing its excluded observing
records. Record model and reference provenance, including any dependence on
space-based or radar measurements, explicitly.

## Intended uses

| Collection | Principal contribution | Interpretation required for an analysis |
| --- | --- | --- |
| Tycho’s recorded material | Historical motion, measurement practice, reductions and selected distance investigations | Timing, signs, measurement type, site/instrument and correction state. |
| Seven supplementary historical books | Observations of multiple bodies, historical corrections, model parameters and worked calculations | Observer attribution, publication lineage, numerical role, native units and unresolved interpretations. |
| Pafko’s transcription | Independent transcription controls | Which properties agree; these remain the same underlying observations. |
| JJMO instrument settings | Reconstruction of observing and parallax procedures | Calibration, motion estimation, timing, geometry and uncertainty. |
| JPL/USNO coordinate products | Comparisons using documented reduced observations | Origin, frame, time scale, limb conventions and corrections already applied. |
| LCO image metadata | Identification of external image versions | Pixel availability, spectral band, timing, image suitability, astrometric calibration and measurement extraction. |

Eligibility belongs to a [named analysis](catalog-terms.md), not to an entire
collection merely because it has been imported. In particular, already applied
parallax corrections remain dependencies of reduced coordinate products.

## Ingested Historical Sources

| Source | Material | Availability |
| --- | --- | --- |
| Tycho Brahe, *Thesaurus Observationum*, Opera Omnia X–XIII | Mars observations, clocks, calibrations, historical calculations and supporting records across four volumes | [Available: 17,043 quantities](../resources/catalog/README.md) |
| Tycho Brahe, *Thesaurus Observationum*, Opera Omnia X–XIII | Jupiter and Moon observations and reductions, with directly related solar and stellar calibration | [Available: 36,453 quantities](#jupiter-and-moon-coverage) |
| Tycho Brahe, *Thesaurus Observationum*, Opera Omnia X–XIII | Sun, Saturn, and Venus observations, reductions, and supporting records | [Available: 46,300 additional quantities](#sun-saturn-and-venus-coverage) |
| Tycho Brahe, *Thesaurus Observationum*, Opera Omnia X–XIII | Mercury, seven comet accounts, fixed-star observations and catalogs, follow-up readings of the new star of 1572, and supporting records | [Available: 50,647 additional quantities](#full-log-coverage) |
| [Wayne Pafko, Mars transcription](https://www.pafko.com/tycho/) | Independent transcription used to reconcile entries in Tycho’s books | 923 linked validation controls; not an additional observing program |
| Tycho Brahe, [*Astronomiae Instauratae Progymnasmata*](https://arsastronomica.com/works/tycho-brahe-astronomiae-instauratae-progymnasmata/) (1610 edition) | Observations, refraction tables, reference coordinates and distance investigations | [22,910 quantities](historical-books-ingestion.md) |
| Longomontanus, [*Astronomia Danica*](https://arsastronomica.com/works/longomontanus-astronomia-danica/) (1640) | Observations, planetary parameters and historical model formulations | [35,349 quantities](historical-books-ingestion.md) |
| Origanus, [*Ephemerides Brandenburgicae*](https://arsastronomica.com/works/david-origanus-ephemerides-brandenburgicae/) (1609), supplied introductory edition | Calendars, conventions, tables and astronomical examples; no claim of complete daily ephemeris volumes | [88,727 quantities](historical-books-ingestion.md) |
| Snellius, [*Observationes Hassiacae*](https://arsastronomica.com/works/willebrord-snellius-observationes-hassiacae/) (1618) | Hessian observations and records attributed to other astronomers | [6,189 quantities](historical-books-ingestion.md) |
| Ursus, [*Fundamentum Astronomicum*](https://arsastronomica.com/works/nicolaus-reimers-ursus-fundamentum-astronomicum/) (1588) | Geometry, reductions and planetary theory | [43 quantities](historical-books-ingestion.md) |
| Riccioli, [*Astronomia Reformata*](https://arsastronomica.com/works/giovanni-battista-riccioli-astronomia-reformata/) (1665) | Collected observations, numerical theories, refraction and parallax | [114,155 quantities](historical-books-ingestion.md) |
| Riccioli, [*Almagestum Novum*](https://arsastronomica.com/works/giovanni-battista-riccioli-almagestum-novum-tomus-primus-pars-prior/) (1651), supplied tome-I edition | Observations, astronomical tables and numerical model evidence | [35,802 quantities](historical-books-ingestion.md) |

The supplementary books contribute 303,175 quantities across all bodies within
their selected editions. [Coverage and limitations](historical-books-ingestion.md)
distinguish quantity rows, contextual annotation literals and unresolved cases.
The [book source guide](sources.md) links editions, PDFs and original witnesses.
The [historical evidence guide](historical-findings.md) identifies relevant sections
and distinguishes new observations from repeated accounts of earlier evidence.

### Jupiter and Moon coverage

The catalog extends coverage of the four-volume observing logs from Mars to
Jupiter and the Moon. The Moon selection includes dedicated observing sections,
eclipses, occultations, and comparisons recorded elsewhere in the logs. Both
selections include directly related solar and stellar readings, clock settings,
refraction, parallax, and historical reductions. [Editions and printed witnesses](sources.md)

| Opera Omnia volume | New quantities in the Jupiter selection | New quantities in the Moon selection |
| --- | ---: | ---: |
| X | 1,096 | 4,714 |
| XI | 2,896 | 6,278 |
| XII | 4,879 | 10,243 |
| XIII | 3,689 | 2,658 |
| **Total** | **12,560** | **23,893** |

The Jupiter and Moon selections contribute 36,453 quantities across 9,710
source groups. Reconciliation by source location identified 1,578 shared
occurrences whose existing records are reused. The totals include calibration
data and calculations alongside observations. For 16,071 quantities, the
catalog preserves the literal reading and source location with its numerical
interpretation still unresolved. Analysis eligibility requires separate
review of the measurement role, time convention, reference objects, and
applied corrections. [Catalog terminology](catalog-terms.md)

Together, the Mars, Jupiter, and Moon selections contribute 53,496 quantities
from Tycho’s four observing volumes.

### Sun, Saturn, and Venus coverage

The verified source bundles cover all four volumes. The solar selection includes
meridian altitudes, declinations, clock readings, eclipse records, and related
instrument, refraction, and parallax evidence. The Saturn and Venus selections
include observing sections, mixed-target passages, and the historical reductions
and reference readings that accompany them. [Editions and printed witnesses](sources.md)

| Opera Omnia volume | Sun | Saturn | Venus | Total added quantities |
| --- | ---: | ---: | ---: | ---: |
| X | 5,676 | 750 | 3,132 | 9,558 |
| XI | 7,263 | 1,933 | 4,226 | 13,422 |
| XII | 4,512 | 3,960 | 6,356 | 14,828 |
| XIII | 1,722 | 4,861 | 1,909 | 8,492 |
| **Total** | **19,173** | **11,504** | **15,623** | **46,300** |

The additions span 12,239 source groups and include 595 separate context entries.
The quantity totals cover observations, calibration values, and calculations.
Verified source matches reuse existing readings. Unresolved expressions retain
their original notation and citations. Through the Sun, Saturn, and Venus
selections, Tycho’s four observing volumes contribute 99,796 quantities. Year
assignments for shared date claims follow the printed section headings.

### Full Log Coverage

The expanded coverage draws on the final editions of all four volumes. It
includes Mercury, the comet accounts for 1577–1578, 1580, 1582, 1585, 1590,
1593, and 1596, fixed-star observing sections and catalogs, and the 1573
follow-up readings of the new star of 1572. A sweep across the complete log
bodies also captured comparison readings, clock and instrument entries,
correction and reduction material, and separate notes about observing
circumstances. [Editions and printed witnesses](sources.md)

| Opera Omnia volume | Added in the 1.3.0 intake | Quantities in 1.3.1 |
| --- | ---: | ---: |
| X | 11,737 | 31,772 |
| XI | 14,807 | 40,132 |
| XII | 12,417 | 49,829 |
| XIII | 11,661 | 28,710 |
| **Total** | **50,622** | **150,443** |

The 1.3.0 additions span 2,397 source groups and include 1,698 separate observing
context records. The release reuses existing records for matched source
occurrences and preserves 46,423 of the added quantities as cited literal
expressions with unresolved numerical interpretation. Its addition totals
exclude 45 candidate spans flagged for overlap and 32 candidates awaiting
printed page citations.

#### Interpretation review

[Release 1.3.1](../resources/catalog/README.md#download) contains **710,420 quantities**. The review
classifies 8,341 of the initially unresolved entries and establishes exact
values for another 14,234 whose uses remain open. It also recovers the complete
expressions for three earlier readings while preserving their original
fragments and identities.

The review accounts for all 45 whole-log overlap flags and 249 earlier
matching flags. Two possible locations remain for one daily-motion entry.
It recovers all 32 missing page citations on 19 lines and corrects eight
reading citations and three context locators in Volume X. The supplements
contribute 25 distinct quantities and 1,657 context records.

Of the 23,848 initially unresolved entries that still lack an exact conversion,
1,478 are documentary context, including star identifiers and calendar
labels. Most of the remainder need evidence for the unit places or the
purpose of a standalone number. Dates, clock origins, and observational
roles retain their source qualifications. [Catalog terminology](catalog-terms.md)

## Modern observing programs

| Source | Imported material | Availability |
| --- | --- | --- |
| [John J. McCarthy Observatory, 2001 experiment](https://www.mccarthyobservatory.org/pdfs/pm020102.pdf) | Five early/late observing pairs, original dial settings, EDT clocks, calibration and reported results | [Available](../resources/catalog/README.md) |
| [John J. McCarthy Observatory, 2003 experiment](https://www.mccarthyobservatory.org/pdfs/pm031117.pdf) | 31 Mars/star readings, 12 calibration pairs, original settings and reported calculations | [Available](../resources/catalog/README.md) |
| JPL optical transit compilation: [Washington 6a](https://ssd.jpl.nasa.gov/dat/planets/trnstswash6a.txt), [6b](https://ssd.jpl.nasa.gov/dat/planets/trnstswash6b.txt), [6c](https://ssd.jpl.nasa.gov/dat/planets/trnstswash6c.txt), [9-inch](https://ssd.jpl.nasa.gov/dat/planets/trnstswash9.txt) | Complete selections: 15,625; 3,204; 2,301; and 3,970 source rows respectively, across all recorded targets | [Available](../resources/catalog/README.md) |
| [JPL Herstmonceux](https://ssd.jpl.nasa.gov/dat/planets/trnstsherst.txt), [La Palma](https://ssd.jpl.nasa.gov/dat/planets/trnstslplma.txt), [Tokyo](https://ssd.jpl.nasa.gov/dat/planets/trnststokyo.txt), [Bordeaux](https://ssd.jpl.nasa.gov/dat/planets/trnstsbordx.txt) | Complete selections: 2,976; 3,904; 342; and 473 rows respectively, including planets and satellites | [Available](../resources/catalog/README.md) |
| [USNO W1J00 and W2J00, VizieR I/334](https://cdsarc.cds.unistra.fr/viz-bin/cat/I/334) | Complete Solar System tables: 4,383 and 11,566 rows, including minor planets; UT1 epochs, limb and instrument information, and W1 absolute-minus-Hipparcos differences | [Available](../resources/catalog/README.md) |
| [Carlsberg Meridian Catalogs 1–11, I/256](https://cdsarc.cds.unistra.fr/viz-bin/cat/I/256) | Complete `planet.dat`: 25,848 rows, with TT epochs, apparent positions, available magnitudes and quality flags | [Available](../resources/catalog/README.md) |
| [Tokyo PMC88, I/188](https://cdsarc.cds.unistra.fr/viz-bin/cat/I/188) | Complete `planets` table: 664 rows, with UT1 epochs, positions, applied phase corrections, published residuals and available magnitudes | [Available](../resources/catalog/README.md) |
| [Las Cumbres Observatory archive](https://archive.lco.global/) | Metadata and checksum identities for 1,963 verified science-file versions | [Available metadata](../resources/catalog/README.md); image pixels remain external |

The modern numerical imports contain **256,802 quantities**. Observing rows, individual
quantities, calibration pairs and image versions are different counting units.
The twelve digital Solar System tables contain 75,256 source rows and 256,485
quantities. The other 317 quantities belong to JJMO records. Existing Mars
identities are retained: the full-table extension adds 247,900 quantities rather
than importing the earlier 8,585 quantities again.

There are 360 individually recorded candidate JPL/USNO overlaps. Additional
cross-publication overlap warnings accompany the complete digital tables,
including JPL/Carlsberg and JPL/Tokyo products. Both source occurrences are
retained; these totals do not establish a count of independent observations.

UT, UT1, TT, UTC and EDT remain distinct source conventions. Original coordinate
frames, limb labels and correction histories accompany the values. Reduced
coordinates do not become raw readings through import.

Carlsberg’s Geographos positions remain topocentric, as its documentation specifies;
its other planetary-table positions are geocentric. Minor-planet numbers and
original names are retained, including spelling variants, separately from satellite
identities. Tokyo phase corrections remain already-applied source quantities and
are not applied again. Native JPL station codes are preserved, including `9501`
in the La Palma file.

Washington 6a also contains 832 pairs of printed residual fields. Their native
expressions are preserved in SQLite’s `source_lines`; they are supporting source
context, outside the quantity-row totals above. The linked JPL format description
does not specify their numerical scale, so no physical-unit conversion is assigned.
See the [native-field query](../resources/catalog/README.md#inspect-native-jpl-residual-fields).

Companion mean stellar catalogs, Carlsberg weather, extinction and photometric
series remain [separate queued selections](data-sources.md#digital-companion-collections).
They are not included in these numerical coverage totals.

## Planned Ingestions

The following selections are planned. Where a work or collection is already partly
ingested, only the additional material specified below is queued. Historical
findings and analysis questions are described in the [evidence guide](historical-findings.md).

### Historical Works and Records

| Planned acquisition | Material | Prerequisite |
| --- | --- | --- |
| Further works by Tycho, including cited material in *Opera Omnia* V and VIII | Mars commentary, calculations, correspondence and supplementary observations | Identify editions and cited passages; establish relationships to the logs. |
| Hevelius and other Ars Astronomica authors | Historical observations, reductions and supporting tables | Select the works, editions and numerical sections. |
| Origanus, daily ephemeris volumes beyond the ingested *Introductio* | Dated predictions and supporting tables | Identify the volumes and years actually available; keep predictions distinct from observations. |
| Riccioli, parts of *Almagestum Novum* beyond the selected Tome I, Part 1 edition | Additional observations, tables and theories | Identify the exact parts and editions before selecting numerical material. |
| Mästlin’s ephemerides and other external tables cited in the logs | Historical prediction and reduction inputs | Identify the cited editions and tables; references alone do not establish their numerical contents. |
| Lalande’s publication of the 1593 Mars observations, *Mémoires de l’Académie* (1757), p.411 ff. | An additional publication witness to Tycho’s observations | Locate the published pages and establish their relationship to Bartholin’s copy. [Citation context](historical-findings.md#earlier-mars-editions-and-manuscript-witnesses). |
| Additional Copenhagen, Paris and Vienna manuscript witnesses described by Dreyer | Observing entries, copies, variants and calculations absent from other witnesses | Identify the manuscripts and accessible scans; define a bounded selection. |

### Stellar Observing Books Awaiting Transcription

These books go through the separate transcription/translation pipeline before
catalog ingestion. Their scans and unverified OCR are not direct catalog inputs.

| Planned publication | Selection | Prerequisite |
| --- | --- | --- |
| Paris Observatory, observations for 1858, published in 1861: [Gambey mural circle, pp.225–454](https://www.persee.fr/doc/aopo_2022-8635_1861_num_14_1_1035) | Dated stellar readings, environmental columns, instrumental corrections and published coordinates | Transcription/translation of tables, headings and reduction instructions. |
| Same Paris volume: [meridian telescope, pp.1–223](https://www.persee.fr/doc/aopo_2022-8635_1861_num_14_1_1033) | Transit clocks, wire counts, observer corrections, clock calibration and published right ascensions | Process with the mural-circle section while retaining separate instrument identities. |
| [Greenwich observations for 1856](https://books.google.co.uk/books?id=JSVHAAAAcAAJ&pg=PP5), including the [instrument and reduction introduction](https://articles.adsabs.harvard.edu/pdf/1858GOAMM..18....1A) | Stellar sequences and calibration records from the Transit Circle and Reflex Zenith Tube | Transcription/translation; establish the numerical-table selection. |
| Selected adjacent Greenwich years from the [digitized-volume index](https://www.royalobservatorygreenwich.org/articles.php?article=932) | Extend the selected stellar sequences | Choose exact years and editions after assessing the 1856 coverage. |

### Digital Companion Collections

| Planned collection | Tables or material | Prerequisite |
| --- | --- | --- |
| [Carlsberg I/256](https://cdsarc.cds.unistra.fr/viz-bin/cat/I/256), stellar tables | Mean stellar positions and annual reference-star positions, including `stars.dat`, `fk5u.dat` and `fk5l.dat` | Define table coverage; preserve mean epochs and reference-system dependencies. |
| [USNO I/334](https://cdsarc.cds.unistra.fr/viz-bin/cat/I/334), stellar tables | W1J00 and W2J00 mean stellar catalogs | Preserve separate coordinate epochs, uncertainty estimates and calibration dependencies. |
| [Tokyo I/188](https://cdsarc.cds.unistra.fr/viz-bin/cat/I/188), stellar catalog | PMC88 mean stellar positions and associated fields | Preserve mean epochs and the catalog’s coordinate conventions. |
| Carlsberg meteorological and extinction tables | `met*.dat` and `ext.dat` | Size the selection explicitly; preserve timestamps, environmental units and acceptance flags. |
| Carlsberg photometric time series | Variable-star, nova and suspected-variable magnitude tables | Select tables and retain object identifiers, epochs and photometric qualifications. |

### Additional Modern Collections

Other public terrestrial and airborne optical datasets will be added when
identified. Each selection needs a source, observing platform, measurement method,
time conventions, reduction history and redistribution terms before acquisition.

## Supporting sources

The catalog also retains source identities for the
[JJMO instrument description](https://www.mccarthyobservatory.org/pdfs/pm020425.pdf),
[JPL optical format specification](https://ssd.jpl.nasa.gov/dat/planets/optical_format.txt),
[USNO reduction publication](https://arxiv.org/abs/1605.09780), and supporting
stellar catalogs. These are not extra Mars observing sequences.
Captured [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/) responses are model
comparison artifacts, separately identified from observations.

The [combined download](../resources/catalog/README.md) contains both historical
and modern numerical records in one catalog. Project contributions are
[CC0-1.0](../DATA_LICENSE.md); third-party sources retain their own terms.
Original reports and image pixels are linked rather than bundled.

Future books and online collections will be listed here with their coverage,
observational role and availability. See the [research program](research-plan.md)
for how these sources support model comparisons, corrections and distance studies.
