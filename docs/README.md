# Documentation

Tychonides provides a downloadable research catalog. Historical prediction engines,
correction experiments, parallax and aberration studies, and the interactive
explorer are planned. Start with the route that matches your purpose.

## Use the Data

1. [Download and query the catalog](../resources/catalog/README.md) — files,
   example queries, current coverage and reuse terms.
2. [Read the terminology](catalog-terms.md) — what exact, reviewed, verified and
   eligible mean.
3. [Understand the values](catalog-data-dictionary.md#worked-numerical-examples) —
   signs, original and derived values, zodiac origins and observing clocks.

The [verification contract](data-workflow.md#what-verification-checks) explains
what the download checks establish. Using the release does not require rebuilding
the extraction pipeline.

## Sources and Coverage

| Page | What it answers |
| --- | --- |
| [Source directory](data-sources.md) | Which collections are ingested, what remains planned, and which observations are in scope? |
| [Published editions and witnesses](sources.md) | Where can I read the books and check their original printed sources? |
| [Tycho’s Mars coverage](mars-catalog-status.md) | What does the four-volume historical Mars selection contain, and what remains unresolved? |
| [Supplementary historical coverage](historical-books-ingestion.md) | What material is represented from the seven additional historical editions? |
| [Pafko’s independent transcription](pafko-validation-status.md) | How was the independently entered workbook reconciled, and which properties agree? |
| [Edition findings](edition-findings.md) | Which discrepancies and interpretation questions have been documented? |
| [Correction review policy](edition-issues.md) | How are edition errors, printed variants and pipeline defects distinguished? |

## Research

| Page | Purpose |
| --- | --- |
| [Research program](research-plan.md) | Questions, milestones, model-comparison rules and visualization requirements. |
| [Historical evidence for modern analysis](historical-findings.md) | Located passages, historical claims and questions for validation. |
| [Historical and modern corrections](correction-comparisons.md) | Correction scenarios, shared errors, uncertainty and sensitivity procedures. |

## Reproduce or Contribute

1. [Run the public worked example](worked-example.md).
2. [Follow the processing workflow](data-workflow.md) for installation,
   verification, acquisition and packaging.
3. [Apply the ingestion strategy](ingestion-strategy.md) to source selection,
   faithful capture and proportional checks.

For detailed authoring, use the [historical review format](review-reference.md)
and [historical record casebook](observation-methods.md). Full historical rebuilds
require the source bindings and review inputs described in the
[reproducibility boundary](data-workflow.md#reproducibility-boundary).

## Technical References

| Reference | Contents |
| --- | --- |
| [Catalog design](catalog-design.md) | Identities, evidence layers and the consolidated representation. |
| [Data dictionary](catalog-data-dictionary.md) | CSV fields, scientific metadata and numerical interpretation. |
| [Database schema](database-schema.md) | SQL tables, views, columns, relationships and indexes. |
| [Historical vocabulary](historical-data-dictionary.md) | Historical quantity types, roles and units. |
| [Modern vocabulary](modern-data-dictionary.md) | Modern quantity types, roles and source notation. |
| [Normalization conventions](normalization-conventions.md) | Conversion methods and time-scale labels. |
| [Numerical integrity](catalog-integrity-audit.md) | Numerical safeguards and documented interpretation limits. |

Vocabulary and schema references are maintained with their generators. Narrative
guides explain how to use those definitions without maintaining a second schema.
