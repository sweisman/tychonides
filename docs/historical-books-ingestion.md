# Supplementary Historical Collections: Coverage and Limits

Seven historical editions contribute **303,175 quantities in 10,930 source groups**,
covering all celestial bodies and relevant supporting material in the selected
editions. All **4,078 selected source regions** have recorded review decisions.
These records join the earlier Mars and modern collections in the
[single Tychonides catalog](../resources/catalog/README.md).

| Work | Quantities | Selected regions with decisions | Material represented |
| --- | ---: | ---: | --- |
| Snellius, *Observationes Hassiacae* | 6,189 | 47 / 47 | Hessian, Bohemian and earlier observations, reductions and observer attributions |
| Brahe, *Progymnasmata* | 22,910 | 629 / 629 | Recorded observations, stellar and solar material, refraction, parallax and historical calculations |
| Longomontanus, *Astronomia Danica*, 1640 | 35,349 | 691 / 691 | Observations, reductions, planetary parameters, correction tables and worked calculations |
| Ursus, *Fundamentum Astronomicum* | 43 | 64 / 64 | Observational material, coordinate reductions and numerical evidence for the stated hypothesis |
| Origanus, *Ephemerides Brandenburgicae* | 88,727 | 275 / 275 | Material present in the supplied introductory edition, time conventions, correction tables and astronomical examples |
| Riccioli, *Astronomia Reformata* | 114,155 | 840 / 840 | Collected observations of all bodies, competing reductions, parameters and prediction tables |
| Riccioli, *Almagestum Novum*, supplied tome-I edition | 35,802 | 1,532 / 1,532 | Observations, astronomical tables, correction methods and numerical model evidence within this edition |

See the [source guide](sources.md) for published editions and witnesses. Other
books and the remaining planetary material in Tycho's four observation logs are
separate, deferred acquisitions. A citation to another work does not extend this
selection to that work.

## Selection and representation

The inventory covers prose, tables, notes and diagrams. Selected material includes
observations, historical reductions, corrections, ephemerides, model parameters
and relevant worked calculations. Unrelated exercises and general mathematical
tables without an identified astronomical application are excluded. Section
decisions include these exclusions; a reviewed region need not emit a quantity.

Each publication retains its own source identity. A reported observer and the
author compiling the book are separate attributions. Repeated publications of
an observation remain distinct source occurrences with supported links; they do
not become independent measurements. Dates, clock conventions, coordinate origins
and correction states require source evidence. Follow the existing
[observing policy](data-sources.md#observing-policy).

## Numerical coverage and limits

Of the new quantities, **295,191 have exact conversions**, **486 are incomplete**
and **7,498 retain unsupported or unresolved interpretations**. Exactness describes
rational arithmetic under the recorded interpretation, not observational accuracy.
An unresolved expression is preserved without an invented scalar. Counts include
historical inputs, calculations, adopted values, bounds and alternatives; they
are not counts of independent observations.

Edition notes can retain numerical expressions as contextual evidence rather
than separate quantity rows. Their definition and attachment scopes distinguish
editorial alternatives from recorded readings. Such contextual literals are not
included in the quantity totals, and editorial corrections remain unapplied
unless explicitly represented otherwise.

Important limits of the supplied material include:

- Origanus's introductory material is not the complete series of daily ephemeris
  volumes. Incomplete folded-table or diagram content cannot be supplied by
  extrapolation. Available diagram fields and descriptions remain represented.
- Some bare longitude components lack a supported zodiac origin, and some arc
  differences lack established component denominations. Their native numbers
  remain available without an adopted absolute coordinate or conversion.
- Set-valued editorial corrections and some exceptional compound expressions
  remain contextual or explicitly unresolved. Parser limits are distinct from
  defects in a source edition.
- Native dates, eras and clock expressions do not by themselves establish an
  absolute observing epoch, site, correction state or analysis eligibility.
- Citation ranges and provisional page claims remain qualified. An unknown
  individual scan leaf is not replaced with another edition's page offset.

Source review is not an independent image audit of every numeral. The numerical
transcriptions supply the readings; targeted print checks resolve specific
questions. See [terminology](catalog-terms.md), [edition findings](edition-findings.md)
and the [source guide](sources.md).

## Coverage and Research Use

An edition is complete when every inventoried section has a disposition, selected
passages have review outcomes, and accepted records pass numerical and provenance
checks. Unresolved interpretations remain visible without invented values.
Inventory coverage does not establish independent image review or scientific
eligibility.

The extension is collated into `tychonides.sqlite` and its CSV, preserving the
earlier catalog's records and interpretations. Release checks cover export
parity, relationships, source counts and preservation of earlier records.
Ingestion does not reconstruct the historical algorithms or fit astronomical
models. Those tasks follow the [research milestones](research-plan.md#next-research-milestones),
using a selection whose timing, geometry and evidential roles meet the requirements
of the named analysis.
