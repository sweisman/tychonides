# Research program

Tychonides investigates celestial motion through Tycho Brahe’s observations and the
astronomical theories used to interpret them. Mars provides a common thread through
orbital geometry, historical model comparison, observational accuracy and distance.

The catalog provides recorded quantities and source context. Historical prediction
engines, correction comparisons and astronomical analyses are planned; the
milestones below define their completion criteria.

## Research strands

| Strand | Status | Research purpose |
| --- | --- | --- |
| Observation catalog | Mars and modern collections plus seven historical books ingested | Source-linked measurements, observing context, historical calculations and exact numerical representations. |
| Mars apparent motion and geometry | Planned | Retrograde loops, oppositions, inclination constraints and relative distances. |
| Historical model comparison | Planned | Ptolemaic, Copernican, Tychonic and modern formulations; Ursus and Longomontanus where source evidence permits. |
| Interactive visualization | Planned | Linked views of planetary geometry, observed directions, predictions and residuals. |
| Kepler and opposition tables | Planned | The passage from readings through reductions to constructed opposition tables. |
| Mars parallax | Planned | Diurnal-parallax sensitivity, observing geometry and the separate problem of orbital triangulation. |
| Accuracy and refraction | Planned | Compare Tycho’s and other historical correction values with modern calculations on the same recorded observations; assess instrument, timing and atmospheric effects. |
| Stellar aberration | Planned | Test whether dated terrestrial stellar observations and their calibration records permit an independent determination of annual aberration, with refraction, instrument and seasonal effects evaluated separately. Mean catalog positions and corrections already applied retain their distinct roles. |
| Other planets and records | Planned | Planetary, lunar, cometary and stellar observations within the same source-based approach. |

## Next research milestones

| Milestone | Deliverable | Completion criterion |
| --- | --- | --- |
| First astronomical subset | Versioned selection with measurement roles, signs, timing, sites, instruments, reference objects and correction states | Each selected value and epoch or interval has traceable evidence; exclusions, dependencies and supported alternatives are listed. |
| Historical calculation reconstruction | Selected printed examples and parameter tables implemented | Examples reproduce within declared tolerances; discrepancies and edition choices are documented. |
| First observation–prediction comparison | Predictions, residual table, plot and run configuration | An independent run reproduces the numbers; plotted points match the export and resolve to source records. |
| Parallax feasibility | Recovery experiments at the actual cadence under declared error assumptions | Report zero-signal false positives, recovery bias, uncertainty coverage, detectable range and confounding effects. A useful bound or sensitivity limit completes this milestone; a positive detection is not required. |
| Scientific visualization | Interactive views of the accepted calculations | A selected point resolves to the same observation, interpretation, prediction and residual as the analysis export. |

Historical reconstruction and targeted source extraction can proceed alongside
preparation of the first subset. Catalog expansion need not wait for an orbit fit,
and the wider program does not depend on detecting Tycho-era parallax.

## Ingestion program

These are parallel workstreams, not a fixed import order. All follow the
[observing policy](data-sources.md#observing-policy) and [ingestion strategy](ingestion-strategy.md).

| Workstream | Material | Completion criterion for each release |
| --- | --- | --- |
| Remaining Tycho logs | Other planets, Sun, Moon, comets, stars and supporting records across all four volumes | Define the selected body/record scope, review its inventory, preserve cross-body relationships and publish coverage with unresolved cases. Reuse existing source occurrences rather than importing them twice. |
| Other works by Tycho | Relevant observations, calibrations, correction tables and model inputs, including the Progymnasmata | Identify work and edition, classify evidential roles and trace repeated accounts to their earlier records. |
| Other historical astronomers | Hevelius and other relevant authors in Ars Astronomica | Identify the available public work and edition before selecting passages; establish observer and publication lineage, units and eligibility. |
| Additional modern collections | Suitable datasets as they are found | Establish platform, measurement method, spectral band, timing, reduction history, provenance and redistribution terms before import. |

The [source directory](data-sources.md) lists ingested collections and planned
acquisitions with their prerequisites. [Historical evidence for modern analysis](historical-findings.md)
collects located passages, historical claims and interpretation questions. A source is
not counted as imported merely because its book or archive has been identified.

The [seven-book acquisition](historical-books-ingestion.md) is complete: 303,175
additional quantities cover all bodies within the selected editions. The remaining
non-Mars material in Tycho's observation logs, other works, Hevelius and newly found
modern datasets remain future acquisitions. Explicitly unresolved interpretations
are research inputs, not missing source regions to ingest again.

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
refraction predictions form a dedicated comparison; other corrections can vary
where their meaning and inputs are established.

The [correction comparison design](correction-comparisons.md) distinguishes values
as recorded, source-applied reductions, reconstructed historical corrections and
modern alternatives. Compatible combinations will expose how correction choices
affect the result. Unknown conditions remain explicit assumptions, and already
reduced values will not receive the same correction twice. This comparison is
planned; the current catalog preserves its source evidence and prerequisites.

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

Use [the Tychosium](https://ts.tychos.space/) as an interaction reference for a navigable astronomical simulation. Tychonides will connect that style of exploration to its own independently specified models and validated observations. Implementation technology and detailed screen design remain open.

### Visualization references

| Reference | Ideas to carry into Tychonides |
| --- | --- |
| [Pafko's Mars data visualization](https://www.pafko.com/tycho/observe.html) | Declination against time, with recorded observations and a calculated curve visually separated. Make this interactive with point selection, observation filters, residuals, and citations. |
| [Pafko's Mars motion visualizations](https://www.pafko.com/tycho/mars.html) | Celestial-sphere motion, observer sky views, and retrograde sequences. Link the sky view to the same date and selected reading as the time-series plot. |
| [Pafko's model illustrations](https://www.pafko.com/tycho/models.html) | Explain the geometry of different models alongside the observations and their predictions. |
| [The Tychosium](https://ts.tychos.space/) | Navigable simulation, camera exploration, and animated planetary geometry. |

Credit these as design references. Produce project-specific views from documented calculations and reviewed data; any reuse of their media or code requires suitable permission or licensing. A reader should be able to move from a recorded declination to its sky position, model geometry, and residual without losing the observation's identity.

### Views and controls

- A date control, play/pause, time-step and speed controls, and direct selection of an observing session or opposition.
- An orbital view with selectable viewing frame, observer, camera position, trails, and sight lines. Separate changes of reference frame from changes to the astronomical model.
- An observer's sky view showing apparent planetary paths and retrograde loops. Show comparison stars when their identities, positions, and epochs are established.
- Model selection for the specified Ptolemaic, Copernican, Tychonic, and modern variants. Display the formulation, parameter source, fit status, and dataset version with each prediction.
- Observation overlays with uncertainty where supported. Selecting a point opens its printed-page citation, review status, original-versus-derived role, and associated residual.
- Linked residual plots so readers can inspect where a model departs from the observations and distinguish repeated readings from independent observing sessions.

### Parallax and scale

When suitable data and forward calculations exist, add geocentric versus topocentric directions, observing-site and baseline controls, and a labeled magnification of the angular difference. Display the actual signal in angular units alongside any visual exaggeration. Keep diurnal parallax and orbital triangulation distinct, and state the assumed distance scale.

### Research integrity and reproducibility

Observed points, model predictions, historical reductions, fitted results, and illustrative geometry need distinct visual treatment and labels. Keep unresolved measurements visible through review filters; do not interpolate across gaps as though measurements existed. Exclude calibration stars from a Mars selection while retaining them in catalog inspection.

Equivalent relative trajectories expressed in different frames must produce equivalent apparent directions under equivalent observer assumptions. A camera change must not be presented as observational discrimination between cosmologies. Ptolemaic or other historical formulations need their own documented geometry; changing the origin of a modern trajectory is insufficient.

Provide shareable view settings and downloadable plots and plotted data with model parameters, data versions, filters, and time conventions. The viewer will connect the numerical catalog to public book and PDF citations, with shareable data and calculations.

### Visualization development

1. **Catalog explorer:** inspect the reviewed dataset and its completeness, provenance, and selection filters. Begin with declination versus recorded date; add a full sky path only when coordinate and clock normalization support it.
2. **Planetary geometry:** add animated orbital and observer views, with explicitly labeled illustrative geometry where observational inputs remain insufficient.
3. **Model comparison:** connect the independently tested prediction engines, synchronized observations, residual plots, and original-parameter versus refit controls.
4. **Parallax and broader records:** add the validated observer geometry and sensitivity results, then extend the shared interface to other planets and records.

Acceptance requires reproducible views, clear units and scale, traceable observations, visible review limitations, and agreement between plotted values and exported numerical results. Visualization work follows the data and model dependencies.


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
