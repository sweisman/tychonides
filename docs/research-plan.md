# Research program

Tychonides investigates celestial motion through Tycho Brahe’s observations and the
astronomical theories used to interpret them. Mars provides a common thread through
orbital geometry, historical model comparison, observational accuracy and distance.

The catalog provides recorded quantities and source context. The milestones below
guide historical reconstructions, correction comparisons, and tests of what the
observations can resolve.

<a id="research-strands"></a>

## Research objectives

| Strand | Research purpose |
| --- | --- |
| Observation catalog | Source-linked measurements and calculations from [Tycho’s four logs](data-sources.md#full-log-coverage), seven supplementary historical books, and modern optical collections. |
| Mars apparent motion and geometry | [The 1595 retrograde passage](mars-apparent-motion.md) compares 21 reductions on 16 dates with four model geometries and a modern ephemeris, including station dates, retrograde span, and model-relative distances. [The oppositions of 1580 to 1600](mars-oppositions.md) repeat the comparison under the same rules. |
| Historical model comparison | The 1595 study includes a geometry comparison at a common opposition longitude and a comparison with the Alphonsine and Copernican predictions printed in the log. Extend to independently reconstructed historical ephemerides, additional apparitions, and Ursus’s formulation where the sources permit. |
| Interactive visualization | Linked views of planetary geometry, observed directions, predictions and residuals. |
| Kepler and opposition tables | The passage from readings through reductions to constructed opposition tables. |
| Mars, Jupiter, and Saturn parallax | [Historically recorded and modern corrections](planetary-parallax-comparisons.md), with diurnal-parallax sensitivity and orbital triangulation as separate research questions. |
| Mercury and Venus parallax | [Historical reductions and the 1590 Venus experiment](mercury-venus-parallax.md), with historical and modern distance and refraction assumptions. |
| Accuracy and refraction | [The printed refraction tables](refraction-tables.md) of Tycho and Riccioli are compared with modern refraction. [Planetary correction comparisons](planetary-parallax-comparisons.md) vary distance and refraction independently. Extend to calibrated observing sessions and quantify instrument, timing, and atmospheric effects. |
| Stellar aberration | Test whether dated terrestrial stellar observations and their calibration records permit an independent determination of annual aberration, with refraction, instrument and seasonal effects evaluated separately. Mean catalog positions and corrections already applied retain their distinct roles. |
| Other planets and records | Planetary, lunar, cometary and stellar observations within the same source-based approach. |

The [status page](status.md) records where each objective and milestone stands.

## Next research milestones

| Milestone | Deliverable | Completion criterion |
| --- | --- | --- |
| First astronomical subset | Versioned selection with measurement roles, signs, timing, sites, instruments, reference objects and correction states | Each selected value and epoch or interval has traceable evidence; exclusions, dependencies and supported alternatives are listed. |
| Historical calculation reconstruction | Selected printed examples and parameter tables implemented | Examples reproduce within declared tolerances; discrepancies and edition choices are documented. |
| First observation–prediction comparison | Predictions, residual table, plot and run configuration | An independent run reproduces the numbers; plotted points match the export and resolve to source records. |
| Parallax feasibility | Recovery experiments at the actual cadence under declared error assumptions | Report zero-signal false positives, recovery bias, uncertainty coverage, detectable range and confounding effects. A useful bound or sensitivity limit completes this milestone; a positive detection is not required. |
| Scientific visualization | Interactive views of the accepted calculations | A selected point resolves to the same observation, interpretation, prediction and residual as the analysis export. |

The 1595 study provides a reproducible date-level comparison with source-linked
inputs, figures, and numerical residuals. Measurement-level comparisons require
justified observing times, instrument and site evidence, and correction states.
Historical reconstruction and targeted source extraction can proceed alongside
that work.

For Mars, the next steps move from repeating the date-level comparison at
additional oppositions to reproducing published calculations at their stated
epochs. Predictive comparisons will use documented historical parameters and
reserve whole apparitions for evaluating refitted models. Parallax feasibility
and interactive views can build on the validated observation and prediction
records.

## Ingestion program

These are parallel workstreams, not a fixed import order. All follow the
[observing policy](data-sources.md#observing-policy) and [ingestion strategy](ingestion-strategy.md).

| Workstream | Material | Completion criterion for each release |
| --- | --- | --- |
| Tycho’s four observing logs | Planets, the Sun and Moon, fixed stars, comets, the new star, and supporting observations and calculations | [Full log coverage](data-sources.md#full-log-coverage) documents source evidence and unresolved cases. Establish eligibility for each analysis. |
| Other works by Tycho | Relevant observations, calibrations, correction tables and model inputs, including the Progymnasmata | Identify work and edition, classify evidential roles and trace repeated accounts to their earlier records. |
| Other historical astronomers | Hevelius and other relevant authors in Ars Astronomica | Identify the available public work and edition before selecting passages; establish observer and publication lineage, units and eligibility. |
| Additional modern collections | Suitable datasets as they are found | Establish platform, measurement method, spectral band, timing, reduction history, provenance and redistribution terms before import. |

The [source directory](data-sources.md) lists ingested collections and planned
acquisitions with their prerequisites. [Historical evidence for modern analysis](historical-findings.md)
collects located passages, historical claims and interpretation questions. A source is
not counted as imported merely because its book or archive has been identified.

The [seven-book acquisition](historical-books-ingestion.md) adds 303,175
quantities across the selected editions. The [planned acquisitions](data-sources.md#planned-ingestions)
include further works by Tycho, Hevelius and others, and additional modern
datasets. Unresolved interpretations remain research inputs.

## Model-comparison protocol

| Mode | Question |
| --- | --- |
| Historical reconstruction | Does the implementation reproduce this edition’s geometry, parameters and procedures? |
| Prediction with published parameters | How do those specified historical predictions compare with the selected observations? |
| Refit and predictive evaluation | How well does the formulation predict observations withheld from a new fit? |

Each comparison records the formulation and edition, parameter sources, adjustable
parameters, selection rules, correction scenarios, residual definition and units,
and fitting/evaluation groups. Where known, identify observations used to establish
the historical parameters; otherwise mark that dependence unknown. Reproducing a
historical fit is not independent prediction.

Freeze selection and correction rules before comparing results. Keep repeated
readings, derived records and shared calibration dependencies in the same group;
withhold whole observing sessions, and whole oppositions when testing prediction
across apparitions. Report parameter estimates, training residuals and withheld
residuals separately. Corrections estimated from the data count as fitted parameters.
Equivalent physical trajectories expressed in heliocentric and Earth-centered
frames must pass an executable equality test for predicted observables under the
same observer assumptions. Specify tolerance and units before testing.

## Evidence and method

The [published editions and PDFs](sources.md) provide the source readings. A
machine-readable catalog connects each quantity to its bibliographic location,
measurement type, comparison object, original notation and interpretive qualifications.
The [ingestion strategy](ingestion-strategy.md) and [data dictionary](catalog-data-dictionary.md)
describe that representation.

The [Mars data](../resources/catalog/README.md) include readings and historical
calculations from all four observation volumes. [Coverage and limitations](mars-catalog-status.md)
defines their scope. Pafko’s independent entry supplies a comparison set; the full
catalog also includes material outside his selection. [Reconciliation results](pafko-validation-status.md)
and [edition findings](edition-findings.md) document source discrepancies separately
from astronomical interpretation.

Historical models require identified formulations and parameter sources. Comparisons
must distinguish original parameters from refitted ones and equivalent relative
trajectories from different predictions. Modern ephemerides provide a reference for
checking recorded quantities; they cannot supply missing historical readings.

Parallax studies require observer geometry, timing, refraction and instrument effects.
Orbital triangulation constrains relative distances under stated model assumptions;
diurnal parallax uses a terrestrial baseline. These are distinct measurements.

## Recorded observations and alternative corrections

The core evidence is Tycho’s and other astronomers’ recorded observations. Each
analysis will retain those readings and identify the adjustments applied to them.
The same eligible readings will be evaluated using the documented contemporary
tables or procedures and modern calculations. Tycho’s refraction values and modern
refraction predictions form a [dedicated comparison](refraction-tables.md); other
corrections can vary where their meaning and inputs are established.

The [correction comparison design](correction-comparisons.md) distinguishes values
as recorded, source-applied reductions, reconstructed historical corrections and
modern alternatives. Compatible combinations will expose how correction choices
affect the result. Unknown conditions remain explicit assumptions, and already
reduced values will not receive the same correction twice. The
[planetary examples](planetary-parallax-comparisons.md) show how changing one
assumption at a time affects a result. The catalog preserves the evidence
needed for comparisons at the level of individual observing sessions.

## Related Sources

The [historical evidence guide](historical-findings.md) locates passages for
observation comparisons, model reconstruction, corrections and distance studies.
It distinguishes recorded readings, adopted inputs, calculated results and
historical claims. Use the [published editions](sources.md) to follow their context.

The supplementary historical books are ingested within their
[stated edition limits](historical-books-ingestion.md). Longomontanus’s
[*Astronomia Danica*](https://arsastronomica.com/works/longomontanus-astronomia-danica/)
provides comparative geometries and a numerical Mars theory; the other collections
contribute observations, calibration material and calculation methods. Their
publication and reduction dependencies must be established before pooling values.

Modern terrestrial optical records provide additional comparisons. The
[source directory](data-sources.md) gives their coverage, observing policy and
correction dependencies. Registration of an image or a shared epoch alone does
not establish suitability for astrometry or an independent observing event.

## Interactive planetary visualization

A navigable sky-and-orbit explorer will link recorded observations, model
geometry, predictions, and residuals, so that a selected point resolves to the
same records as the analysis export. The [visualization plan](visualization-plan.md)
gives its design references, views and controls, integrity requirements, and
development order. Visualization work follows the data and model dependencies.

## Publication and reproducibility

The historical Mars subset of the [Tychonides catalog](../resources/catalog/README.md) supplies the
observations, source relationships and documented interpretation limits for
subsequent research. Historical model comparisons, correction experiments and
the interactive explorer build on that evidence.

One self-contained SQLite download and a convenient CSV export let readers use
the catalog without assembling processing intermediates or obtaining a
separate source library.

Data releases identify their sources, selection rules, units, interpretations and
limitations. Recorded values, corrections and derived results remain distinguishable.
Scientific claims require suitable uncertainty estimates and observations capable
of distinguishing the stated alternatives. The [catalog design](catalog-design.md)
sets out the representation and publication requirements.

## Further Acquisition

Ingested and planned collections share one [source directory](data-sources.md).
Expansion follows the observing policy, preserves source-specific roles and links
possible duplicate publications without counting them as independent observations.

An [Ars Astronomica](https://arsastronomica.com/) project.
