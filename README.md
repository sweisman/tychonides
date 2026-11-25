# Tychonides

<p align="center">
  <img src="assets/tychonides-logo.png" alt="Tychonides logo: Mars tracing a retrograde loop against the stars within a golden astronomical instrument." width="160">
</p>

_Finishing what Tycho Brahe started._

**Reopen the observations that transformed astronomy.**

Against the background stars, Mars slows, reverses direction, and resumes its course.
An astronomical model must explain that whole path and its timing. Tycho Brahe’s
measurements made the problem precise; Kepler used them to develop his account of
planetary motion.

Tychonides returns to the recorded evidence, bringing historical angles, clock
readings, observing notes and calculations together with modern optical
observations in one source-linked catalog. Tycho Brahe’s observations anchor a
growing collection spanning many authors, works and observing programs, with planets, the Sun and
Moon, comets and stars all contributing to the investigation.

The program connects data acquisition to historical model reconstruction,
comparisons of contemporary and modern corrections, distance investigations and
an interactive sky-and-orbit explorer. Further works and datasets will extend
the same common catalog. See the [research plan](docs/research-plan.md).

## Available now

The [downloadable catalog](resources/catalog/README.md#download) provides original numerical
expressions, exact conversions, contextual relationships, source citations and
verification tools in a single database and CSV export. Use it to inspect the
evidence, compare source accounts and develop analyses. The
[source directory](docs/data-sources.md#ingested-historical-sources) lists the
historical and modern collections already available, with coverage and
interpretation limits.

The [1595 Mars comparison](docs/mars-apparent-motion.md) follows a retrograde
passage through four models. The [opposition study](docs/mars-oppositions.md)
sets Tycho’s Mars longitudes and the tables of his day against a modern
ephemeris. The [printed predictions study](docs/printed-predictions.md) does
the same for every planet the logs compare with a table. The
[solar theory study](docs/solar-theory.md) rebuilds Tycho’s apogee and
eccentricity from his printed equinoxes. The
[refraction study](docs/refraction-tables.md) sets the printed tables of Tycho
and Riccioli beside modern refraction. The
[1587 parallax study](docs/mars-parallax-1587.md) tests his distances of Mars
from the stars for a parallax. The
[planetary correction comparisons](docs/planetary-parallax-comparisons.md)
show how historical and modern distance and refraction assumptions change the
results. The [studies page](docs/studies.md) lists each finished analysis with
its inputs and how to rerun it. The [status page](docs/status.md) shows what is
done and what comes next, and the [research milestones](docs/research-plan.md#next-research-milestones)
cover predictive tests, parallax feasibility, and the interactive explorer.

Historical readings come from the published editions. Their numerical accuracy
has no corpus-wide estimate. The Tycho subset has no accepted absolute observing
timestamps. You can verify the released files, check individual readings against
their citations, and run the public worked example. Rebuilding the historical
catalog requires unpublished extraction and review inputs.

## One sky, several models

The same observations can be approached through several astronomical systems:

| Model | Geometry to investigate |
| --- | --- |
| Ptolemaic | Earth-centered deferents and epicycles, with their documented parameters. |
| Copernican | Earth and the planets moving around the Sun, using the historical constructions. |
| Tychonic | The Sun moving around Earth, with the planets moving around the Sun. |
| Modern heliocentric | Elliptical orbits and numerical planetary ephemerides. |

The comparison concerns the directions each specified model predicts at the times
of the observations. Some different descriptions produce the same relative motion
and therefore the same directions. A change of viewing frame must be distinguished
from a change in the model’s predictions.

## What can the observations tell us?

- **Motion:** the shape and timing of retrograde loops, oppositions and changes in
  apparent celestial positions.
- **Distance:** constraints from orbital geometry and the much smaller shift in
  direction caused by a change of observing position, called parallax.
- **Measurement:** the effects of instruments, clock conventions and atmospheric
  refraction on the recorded angles.
- **Theory:** how an instrument reading became a corrected coordinate, an adopted
  position or a value in a planetary table.

A raw reading and a calculated position answer different questions. Tychonides
preserves that distinction, along with repeated readings, printed corrections and
uncertain interpretations. Diurnal parallax and orbital triangulation likewise
remain separate approaches to distance.

The recorded observations remain the common evidence when corrections change.
Analyses compare contemporary tables, beginning with
[Tycho’s refraction values](docs/refraction-tables.md), with modern
calculations, making the effect of each correction choice visible.
The [correction comparison design](docs/correction-comparisons.md) describes these
alternatives and their assumptions.

## Read the sources

The [source guide](docs/sources.md) links public Ars Astronomica editions and PDFs,
original printed witnesses and modern source collections. Catalog citations
identify the publication and its page or native record location, so a numerical
result can be followed back to its source. The
[source directory](docs/data-sources.md) explains each collection’s contribution
and the evidence needed to use it in an analysis.

## A second transcription: Pafko’s Mars workbook

For his [visualization project](https://www.pafko.com/tycho/), Wayne Pafko manually
entered records from Tycho’s printed observation logs into an
[Excel workbook](https://www.pafko.com/tycho/mars.xls). It contains source quotations,
sexagesimal components and decimal-degree conversions. It was created separately
from the Ars Astronomica editions and the Tychonides extraction, so it is an
independent transcription of the same pages.

The original reconciliation linked all **923 workbook rows** to source entries.
Pafko’s quotations and the edition agree in unsigned magnitude for **906** rows,
including **125** that also agree in hemisphere. Sixteen differed and one source
value was incomplete. **685** rows received no source check, and source checks
include structural review as well as reading checks. The workbook also informed
parser development, so the agreement checks the readings and is not an
independent test of the method. See the [validation results and limits](docs/pafko-validation-status.md).

## Quick start

From a source checkout, with Python 3.11+, Bash, curl, jq, gzip and SQLite:

```sh
python -m pip install .
./scripts/download-catalog downloads
sqlite3 downloads/tychonides.sqlite "SELECT subject, quantity, count(*) AS quantities FROM catalogue GROUP BY subject, quantity ORDER BY quantities DESC LIMIT 10;"
```

For download-only use and units, see the [catalog guide](resources/catalog/README.md).
The download command retrieves the version pinned by this checkout, verifies it
and produces the ready-to-query database. Large data files are versioned GitHub
Release assets; cloning the repository alone does not download them.

## Start here

| Your goal | Reading route |
| --- | --- |
| See what is done and what is next | [Status](docs/status.md) → [studies](docs/studies.md) |
| Understand the project | [Research program](docs/research-plan.md) → [sources and coverage](docs/data-sources.md) |
| Use the data | [Catalog guide](resources/catalog/README.md) → [worked values](docs/catalog-data-dictionary.md#worked-numerical-examples) → [source uses](docs/data-sources.md#intended-uses) |
| Verify or contribute | [Workflow](docs/data-workflow.md) → [ingestion strategy](docs/ingestion-strategy.md) → [public worked example](docs/worked-example.md) → [tests](https://github.com/sweisman/tychonides/tree/main/tests) |

The [documentation index](docs/README.md) guides readers through source coverage,
research, processing and technical references. See also the
[observing policy](docs/data-sources.md#observing-policy).

_Tychonides_ means “son of Tycho.” At Stjerneborg, Tycho placed a successor
alongside astronomy’s great figures: after Copernicus and himself came
Tychonides, whose verse addresses him as father and asks to carry on his work.
An astronomer yet to make his mark already had a place among the greats.
See [Tycho’s account in _Epistolarum Astronomicarum Libri_](https://arsastronomica.com/works/tycho-brahe-epistolarum-astronomicarum-libri/)
([pp.279–280](https://books.arsastronomica.com/Tycho_Brahe_Epistolarum_Astronomicarum_Libri.pdf#page=279)).

Accounts differ on whether the figure represented his young son or a hoped-for
future heir ([Ann Blair](https://dash.harvard.edu/bitstreams/7312037c-7b4b-6bd4-e053-0100007fdf3b/download),
[Dreyer](https://en.wikisource.org/wiki/Page:Tycho_brahe.djvu/130)). The wider
invitation is clear: in the [_Mechanica_](https://arsastronomica.com/works/tycho-brahe-astronomiae-instauratae-mechanica/)
([p.144](https://books.arsastronomica.com/Tycho_Brahe_Astronomiae_Instauratae_Mechanica.pdf#page=144)),
Tycho encourages future practitioners to adapt and improve his work.

**Tychonides takes up that invitation: bring the observations back into calculation,
and turn unresolved questions into new discoveries.**

[Code: AGPL-3.0-or-later](LICENSE) · [Data: CC0-1.0, with source terms preserved](DATA_LICENSE.md).

[tychonides.com](https://tychonides.com) · an [Ars Astronomica](https://arsastronomica.com/) project.
