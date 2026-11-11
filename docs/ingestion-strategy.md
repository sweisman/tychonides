# Observation ingestion and normalization strategy

This strategy supports the [Tychonides research plan](research-plan.md) across historical works, celestial bodies and modern collections. Mars material across *Opera Omnia* X–XIII was the first historical acquisition. Pafko supplies an independent comparison subset for that material; his rows do not define the inventory or its measurement types. The [catalog design](catalog-design.md) and [data dictionary](catalog-data-dictionary.md) define the shared representation.

Imports follow the [observing policy](data-sources.md#observing-policy) and the parallel [ingestion program](research-plan.md#ingestion-program). Use the shared [catalog terminology](catalog-terms.md) when reporting conversion, review, verification and analysis eligibility.

## Representation

Use linked records for sources, observing events, individual measurements, contextual statements, and derivations. One printed row, one workbook row, one observing session, and one physical measurement are different units. Preserve their relationships rather than treating them as interchangeable observations.

| Record | What it represents | Essential fields |
| --- | --- | --- |
| Source witness | A printed edition, transcription, translation, or independent entry | Stable identifier, bibliographic citation, witness type, edition fingerprint, public link where available |
| Source span | The location supporting an assertion | Witness identifier, printed page, table/block and row/column or prose location; local image mapping kept separately |
| Event | A session or specific observing occurrence | Recorded date and time expressions, participants, site, observer and instrument when supported; unresolved associations remain explicit |
| Measurement | One stated quantity | Event link if established, quantity, subject and reference object, source value and units, role, source span, uncertainty and review state |
| Context statement | Information that affects interpretation | Clock correction, weather, doubtful reading, instrument change, heading, calibration purpose, or refraction statement, with the scope of its application |
| Derivation | A normalization or calculation | Inputs, operation or historical procedure, parameters, assumptions, output, version, and evidence |
| Review decision | An adjudication between witnesses or interpretations | Affected identifiers and input fingerprints, evidence, decision, superseded decision if any, and unresolved questions |

An event link may be provisional or absent. Two entries that appear to describe the same measurement remain separate witness assertions until their identity is established. Repeated pinnule readings remain separate measurements linked to the same event. A reported mean is a derived record linked to its component readings when those inputs are identifiable.

## Preserve the quantity actually recorded

The initial measurement vocabulary should include:

- Equatorial declination and right ascension; ecliptic longitude and latitude.
- Angular separation, with both endpoints identified or explicitly unresolved.
- Altitude and azimuth, with site, horizon/reference convention, and instrument context where known.
- Meridian transit, reference-star hour angle, observing clock reading, and clock correction as distinct timed quantities.
- Instrument calibration, including measurements of comparison stars within planetary passages.
- Historical refraction corrections, assumed parallax, computed coordinates, and other reductions, classified by their stated role.

A number called “parallax” in a calculation can be an adopted correction or model input. It must not become a measured parallax merely because of its label. Similarly, a value inferred from altitude is distinguishable from a direct armillary reading even when both are labeled declination.

Keep target identity, measurement type, and role independently reviewable. Record an unknown comparison star as unresolved; do not silently assign a modern catalog identity. Retain non-Mars calibrations and contextual records found in Mars passages, then select the appropriate targets and roles during analysis.

## Numerical normalization

Store original tokens, units, signs, precision, and explicit uncertainty without alteration. Alongside them, store a parsed quantity with an exact rational magnitude, its canonical unit, and a derivation reference. Rational values should serialize as numerator and denominator; convenient decimal columns are derived exports.

Angles normalize to exact arcseconds only after their units are established. Keep magnitude separate from hemisphere or direction. An unsigned declination can have a known magnitude and an unknown signed coordinate. Zodiacal positions retain their original sign and within-sign angle alongside any normalized longitude. Right ascension expressed in angular hours needs its unit interpretation recorded before conversion to degrees.

Clocks require semantic classification before normalization. For example, the 21 January 1585 passage on Volume X, printed p. 385 expresses Regulus's distance from the meridian in hours and minutes. That quantity cannot simply become the local observation time. Preserve raw and corrected clock expressions with their stated relationship; do not overwrite one with the other.

Recorded dates retain their calendar and day-origin status. A machine-sortable recorded date is not automatically a UTC timestamp. Absolute times require documented calendar, local-time or sidereal-time convention, observing site, day origin, and applicable corrections. Store uncertainty or a bounded interval when the evidence supports it; leave a conversion absent when assumptions are unresolved.

Do not insert modern refraction, precession, proper motion, light-time, or ephemeris corrections into normalized source readings. Add each as a separate derivation with an identified frame, epoch, observer, time scale, inputs, and assumptions. Keep apparent/geometric and topocentric/geocentric interpretations explicit where established.

The same recorded observations support alternative historical and modern correction
scenarios. Store the source’s reduction state and any correction already applied
before constructing those scenarios. Each result must identify its observation
inputs, correction sources or formulas, parameter values, operation order and output
interpretation. Unknown reduction histories remain unresolved rather than being
treated as uncorrected data. See [correction comparisons](correction-comparisons.md).

## Ingestion sequence

1. **Establish sources and controls.** Identify the selected editions and any independent transcriptions or controls. Compare the properties each control actually preserves. Pafko’s entry supplies this control for part of the Mars acquisition; another work need not have an equivalent independent entry.
2. **Inventory source coverage.** Locate relevant material throughout each selected edition, including mixed-target passages, prose, tables, reductions, annotations, and comparison tables. Follow the acquisition's explicit target scope. Track inspected page/block coverage; a parser returning no rows does not prove the absence of observations.
3. **Classify structures and quantities.** Select small examples spanning each table/prose form and measurement type. Establish headings, continuation rules, target changes, clocks, units, and roles before scaling that form. Keep exceptions with source evidence and regression cases.
4. **Extract source assertions.** Assign stable identifiers and source spans, preserve every recorded reading and contextual qualification, and keep uncertainty in grouping or interpretation explicit. Page mapping must not replace or silently alter the published numerical reading.
5. **Normalize in independent passes.** Parse numerical notation, then identify quantities and objects, establish dates/clocks and event associations, and add coordinate interpretations only where evidence permits. Each pass produces new fields or derivations rather than editing source assertions.
6. **Reconcile witnesses and review.** Use metadata and justified printed order to compare overlapping records. Keep quotation, numeric conversion, source scan, quantity/target, and date/time checks separate. Review conflicts and uncertain structures against the print.
   Document problems in the final transcription or translation through the [edition-issue policy](edition-issues.md), including suspected cases, evidence, confidence, and proposed corrections. Distinguish these from parser defects and errors already present in the historical source.
7. **Create scientific selections.** Define eligibility separately for orbital geometry, parallax, refraction, and accuracy studies. State required quantities, target and role, clock/frame assumptions, uncertainty treatment, repeated-reading grouping, and exclusion reasons.
8. **Freeze a reviewed release.** Export public bibliographic provenance and reviewed measurements through a strict whitelist. Include versions, checksums, a data dictionary, coverage and completeness metrics, reproduction commands, and outstanding review states.

## Reusable preparation and throughput

Establish each recurring table or prose structure once, then prepare its numerical
occurrences with shared extraction and normalization operations. Review the
block's units, endpoints, roles, dates and contextual scope together. Conventional
values should not require manually transcribed components or a separate
explanatory record for each numeral. Machine suggestions remain provisional;
numerical agreement cannot establish a target, role, sign or observing epoch.

Preserve exceptional notation and competing readings explicitly, with unresolved
values where necessary, while continuing the routine material. Ingestion records
historical calculations and their stated relationships; reproducing the author's
algorithm belongs to the analysis stage. Reliable numerical transcription does
not require routine image confirmation. Consult a scan for a specific unresolved
question that needs it.

Save source decisions individually for recovery, then append and export larger,
coherent bundles spanning multiple dates or sections. Reuse a validated
compilation only when its complete inputs and engine are unchanged. Reuse must
retain source-binding, duplicate-occurrence, prior-record preservation,
provenance and full CSV/SQLite parity checks. Changed or unverifiable inputs
require renewed validation. Semantic engine changes need regression and
reproducibility checks; routine data additions need one verified bundle build.

When adding a source adapter, retain shared staging and block preparation rather
than falling back to manual preparation of every quantity. Measure performance
against equivalent inputs and outputs, and track verified quantities and source
coverage separately. A larger candidate count alone does not demonstrate faster
completed ingestion.

### Reusable ingestion contract

This is the default procedure for every future acquisition and resumed source,
including works not yet listed in the import queue. Retain validated preparation
decisions; change them only for an evidenced source difference or processing
defect, with verification proportional to that change.

Starting another work does not reset this procedure. Reuse the shared staging
and materialization path, bounded block schema and applicable passed checks.
Preflight a representative example only when the schema is genuinely new.
If preparation falls back to per-number transcription, repeated context creation
or repeated unchanged builds, restore the established method before scaling
that pattern. Preserve the selected material and integrity checks throughout.

Apply this contract before scaling a recurring structure, both within a work and
when starting another one. Save its evidence in the existing acquisition
checkpoint; it does not require another tracker or a per-batch program.

After an interruption, resume the recorded incomplete stage without repeating
completed preparation or rewriting its verification plan. The same contract
applies to tables, journal entries, numerical prose, annotations and diagram
labels. Source-specific interpretation still requires its own evidence.

| Requirement | Evidence to retain |
| --- | --- |
| Reuse the established method | Shared parser and declarative schema, representative preflight, and the source assumptions under which they remain valid. |
| Prepare routine material in blocks | One staged source interval, shared units and bounded context, and occurrence selectors in printed order. The materializer supplies the numbers. |
| Review source-specific differences | Changed headers, notation, roles, targets, dates, signs and page boundaries, with explicit exceptions. Reusing a method does not transfer these facts between works. |
| Keep ingestion moving | Individually saved reviews assembled into a coherent export; independent unresolved cases remain visible without delaying ready material. |
| Verify according to the change | The checks in [Verification proportional to the change](#verification-proportional-to-the-change), with their input and output fingerprints. |
| Demonstrate numerical coverage | Required source occurrences accounted for as imported records or explicit pending exceptions, including tables, prose, annotations and diagrams within scope. |
| Resume without repeating work | Last verified bundle, prepared/appended state, next source interval, outstanding companions and any unverified engine changes. |

Per-number transcription, repeated context writing, routine scan confirmation
and repeated full builds for unchanged semantics are reasons to restore the
shared path before preparing more routine records. Diagnose the actual time
spent in preparation, compilation and export before changing the engine.
Preserve the acquisition's agreed scope and all integrity checks when improving
throughput.

### Starting another work

Apply this procedure to every additional work and celestial body, including
catalogs, ephemerides, correction tables and historical calculation prose.
It remains the default after a source change or interrupted session.
Adding a work changes the source bindings and reviewed schemas; it does not
justify a separate extraction pipeline. Apply these rules to every future
acquisition without narrowing its agreed targets or material to improve speed.
If routine records start requiring
individual numerical transcription or repeated context preparation, stop that
pattern and restore shared staging and block schemas before scaling further.
Preserve the acquisition scope and validation requirements when improving speed.

Use existing typed fields and shared parsers before introducing new machinery.
An exceptional reading can retain its literal expression, qualifications and an
explicitly unresolved normalization while routine records proceed. Extend shared
support when required to preserve scientific meaning or process a recurring
structure. Keep deferred normalization in the acquisition's outstanding-work
list; it must remain visible when assessing completion. Moving to another book
does not require redesigning a preparation method that already fits its material.

1. Bind the selected edition and fingerprint, establish the acquisition scope,
   and check existing source spans before preparing additions. Preserve earlier
   identities and import only missing occurrences or companions.
2. Classify recurring structures and confirm that shared staging exposes their
   numerical occurrences. Establish column or prose schemas and shared context
   from representative passages; retain individual record identities and
   differing qualifications. Extend the reusable adapter if necessary instead
   of preparing each conventional numeral by hand.
3. Preflight a representative block through the shared compiler and public
   projection. Check source bindings, complete unit sequences, roles, endpoints,
   dates and exception handling before scaling. Routine preparation then selects
   staged occurrences through declarative reviews; one-off inline creators must
   not duplicate the parser or manually encode every value.
4. Save prepared reviews atomically and collect them into substantial coherent
   bundles. Preserve unresolved readings, alternative interpretations and honest
   page-locator limits. A difficult expression or an unavailable exact scan
   locator need not hold up unrelated records with adequate source evidence.
   Name inspection, review and provenance artifacts by work and distinct part,
   section or interval. Check an existing artifact's identity before writing;
   repeated chapter titles must not replace evidence from an earlier part.
5. Append and export from the same validated compilation where supported. Run
   the required preservation and export checks once for routine additions;
   broaden verification when changed semantics or a demonstrated defect warrants
   it. After interruption, determine whether append completed before retrying.
6. Checkpoint verified counts, coverage, fingerprints, pending exceptions and
   the next bundle. Report completed throughput separately from staged
   candidates, and update the source directory and research status when the
   acquisition is complete.

### Preparation and resume checklist

Before scaling a recurring structure in any work, establish the following in the
existing acquisition checkpoint. Reuse valid evidence after interruption rather
than repeating completed preparation.
Read the active acquisition's checkpoint, not the checkpoint of an earlier
completed collection.

- **Source and scope:** the edition fingerprint, selected bodies and material,
  existing imported spans, and any missing numerical companions.
- **Shared preparation:** the staging parser and declarative table or prose
  schema, including units, endpoints, roles and bounded context. Conventional
  values come from source occurrences; they are not retyped into scripts or
  large inline creators. Shared context is declared once, with row-specific
  qualifications retained where needed.
  Include numerical caption and heading parameters as well as body cells;
  distinguish native shared group labels from repeats introduced by a flattened
  layout, and retain their source pages and column applications.
- **Representative validation:** a block that passes the shared compiler and
  public projection, plus regression evidence for any new interpretation logic.
  A vocabulary addition using an existing normalizer follows the lighter checks
  below.
- **Next bundle and exceptions:** a substantial coherent source interval,
  individually saved reviews and a bounded list of unresolved expressions or
  relationships. Preserve the author's stated numbers without requiring a
  reconstruction of the calculation. Consult images only for a specific question
  that needs them.
- **Recovery stage:** whether each review is prepared, appended or included in a
  verified export; retain the ledger and output fingerprints and the exact next
  action. Reuse the combined append/export compilation; after interruption,
  revalidate inputs and resume the first incomplete stage.

Before moving to another work or handing off processing, save these decisions
in the same acquisition checkpoint. Identify the reusable parser/schema and its
representative validation, the last verified bundle, the next source interval,
pending numerical companions, and any unverified engine changes. A change of
work or processing session retains the validated method and completed evidence.
Revisit it when the source structure changes or a specific defect requires it.

For established structures, target at least 5,000 new quantities per export where
the source permits. The fallback is 100 candidate regions or 1,000 quantities;
a completed major section or final remainder may be smaller. Never pad counts
to reach a threshold. Save individual reviews as they are prepared so larger
exports retain granular recovery. Finish ready
routine material while keeping independent exceptions visible in the outstanding
work list; optional reconstruction is a separate analysis task.

Use this decision order for each recurring block:

| Source structure | Preparation path |
| --- | --- |
| Conventional table | Reviewed physical columns and shared `cell_groups` with declared component units. |
| Supported angle or clock in prose | Shared staged `expression_index`, with the reviewed role and bounded context. |
| Native numerical prose | Shared staged `fragment_index` and reviewed component unit; declare supported grouping explicitly where needed. |
| Exceptional notation | A complete source-bound literal, fragments or addends through the shared compiler; retain an unresolved interpretation when necessary. |
| Recurring structure unsupported by staging | Extend the shared preparation operation, verify a representative case, then reuse it across the block. |

Select occurrences by source position and printed order. The selectors do not
establish endpoints, signs, dates or roles. Shared context must remain bounded
to the passages it supports; distinct attributions, observing sessions and
qualifications retain their own identities. Numerical values and components
come from the source through the shared materializer, rather than being copied
into preparation code.

Word-valued numbers need the same occurrence discipline. A repeated word in a
margin or heading can have a different meaning from its use beside a unit in
the calculation. Bind the reviewed, unit-qualified occurrence rather than the
first textual match. A correction to an already imported native count word
requires a fingerprinted review of the unchanged literal, its old and new
positions, and unique evidence containing the new occurrence and its unit.
Retain the original review, numerical interpretation and quantity identity;
validate the corrected occurrence through assembly before export.

Repeated manual preparation of conventional values or context, duplicate full
compilation, and optional reconstruction during extraction indicate a workflow
regression. Restore shared preparation before expanding that pattern. Reading a
section or recording its qualitative findings does not complete numerical
ingestion: missing tables, calculations and companions remain pending.
Unsupported word-valued numbers must also remain explicit records or outstanding
companions. Preparation must not conditionally drop them when a vocabulary
lookup fails. Reconcile the known numerical content with emitted records and
declared exceptions before closing the interval; build success alone cannot
establish that preparation selected every required expression.

Report throughput from verified additions and reviewed coverage over a stated
elapsed interval. Keep staged candidates and pending work separate; neither a
code change nor a larger batch proves a speedup by itself. These rules preserve
the full acquisition scope and scientific checks across works and resumptions.

When throughput falls, locate the cost in preparation, compilation or export
using existing stage timings or one representative bundle. Distinguish source
interpretation work from repeated mechanical processing. Record the bottleneck
and remedy in the existing acquisition checkpoint, then use the proportional
verification below. Prefer restoring shared preparation and eliminating
duplicate work before adding caches or other machinery. A new work inherits
this procedure and the validated preparation method; its differing source
structure determines which interpretation decisions need fresh evidence.

### Verification proportional to the change

Choose verification by what changed, rather than restarting every stage for
each review. All exported bundles retain source-binding, duplicate-occurrence,
normalization, provenance, relationship, prior-record and complete CSV/SQLite
parity checks.

Prepare complete chapters or substantial recurring blocks between checks.
Validate a genuinely new schema on a representative example, then apply it
across the block. Changes of author, target or page do not restart that
validation when the established schema still applies. Keep individual
reviews durable for recovery without making each review a processing batch.

Routine constituent reviews do not each require a separate preflight run or
report. Preflight a new schema once, then collect its routine occurrences into
the substantial bundle. Recheck changed interpretation logic with its affected
dependencies. Reuse
fingerprinted successful checks for unchanged material; do not repeatedly
compile the growing prepared packet. A failed check reruns its affected
subset. Check the complete accumulated bundle before append/export, retaining
all source-binding and scientific validation requirements.

| Change | Required verification |
| --- | --- |
| Routine records using established notation | One verified bundle build, including the accumulated bundle preflight; save individual reviews before the build. |
| A literal vocabulary addition using an unchanged normalizer | Existing focused checks and the next verified bundle build; no separate test for each source label. |
| Parsing, unit interpretation, normalization or projection semantics | Regression cases for the changed behavior, one full regression suite and two matching exports at the next substantial bundle; combine pending changes into that verification cycle. |
| Performance-only implementation change | Full regression suite and equality of complete outputs against captured reference inputs; unchanged downstream inputs do not require new exports. |
| Documentation alone | Relevant links and documentation contracts; no numerical rebuild. |

When resuming, verify the ledger and output fingerprints before deciding which
stage needs work. A prepared review is not an appended review, and an appended
review is not a verified export. Resume from the first incomplete or invalidated
stage. Preserve pending numerical companions and unresolved exceptions in the
acquisition record so larger bundles cannot conceal missing work.

Additional work must resolve a specific obstacle to faithful ingestion or
required validation. Use existing typed fields and shared preparation first;
preserve unresolved readings and queue deferred interpretation explicitly.
Use that order: supported representation, explicit unresolved representation,
then a necessary shared-code change. Once required checks pass, proceed to the
next source block. Reopen passed work only for changed inputs or specific defect
evidence; possible improvements do not create additional acceptance conditions.
Interrupt extraction only for an identified failing requirement that these
existing representations cannot satisfy. Otherwise continue the source block;
an isolated exception does not hold up independent ready material. Record an
actual interruption in the existing acquisition checkpoint so processing can
resume without repeating accepted work.
Routine acquisition does not require reconstructed calculations, routine
image confirmation, duplicate audits, new tracking systems or speculative
optimizations. Source-only additions need no full regression rerun or repeated
export. Completion documentation follows the completed acquisition; reusable
methodological findings are recorded once.

Faithfully preserved, explicitly unresolved notation is a valid ingestion
outcome. Completion accounts for these limits and any missing required records;
it does not require every expression to acquire a scalar or every historical
discrepancy to be resolved. Interpretation and astronomical reconstruction remain
separate work. An exception interrupts routine extraction only when required
evidence cannot be preserved or a required check fails.

The ingestion completion boundary is source coverage, faithful capture of the
relevant numerical material and supported context, successful required export
checks, and updated acquisition documentation. Analysis readiness, image audits,
reconstructed calculations, exhaustive derivation links and speculative
refactoring are not additional completion conditions. Preserve parser limits as
parser limits, with the source expression retained; do not mislabel them as
edition errors or silently omit the affected quantities.

## Storage and public access

The public catalog is one self-contained SQLite database and a CSV generated from its selected interpretations. Working JSON records retain extraction and review evidence; consumers do not need to assemble them. CSV includes complete per-value normalization and qualifications, while SQLite retains the full relationships. Additional formats require a concrete analytical need.

Catalog records cite the edition and printed page, with links to the published books and scans. Numerical releases identify their selection rules, units, interpretation and limitations.

The visualization tool should consume the same reviewed exports as the analyses. A point in a declination plot, an angular-separation measurement, or a historical reduction should expose its quantity and role. Sky coordinates reconstructed from separations remain derived positions linked to the underlying measurements. Missing coordinates must not be filled by a modern prediction and displayed as observations.

## Validation and readiness

Check exact arithmetic and unit bounds, references between records, source stability, date/time ambiguity, target and quantity changes, inherited context, and preservation of repeated readings and uncertainty. Review outputs should include all records, including rejected interpretations and unresolved cases.

Report coverage by volume, source span, date, measurement type, target, and role. Report Pafko overlap separately from newly recovered records, and distinguish candidate extractions from reviewed measurements. Publish a total only after defining its counting unit: source assertions, distinct measurements, events, sessions, and observing nights can yield different counts.

The next ingestion stage is ready when the benchmark has evidence-backed dispositions, the representation preserves the required distinctions, and representative source structures pass extraction and review checks. An astronomical subset needs its own readiness assessment; successful transcription alone does not establish fitness for an orbit or parallax fit.
