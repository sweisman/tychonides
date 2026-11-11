# Database schema reference

Schema version 5. Exact values are rational strings; SQL null means unknown or inapplicable, never zero.
JSON preserves structured qualifications. Foreign keys below identify relationship targets.
See the [historical terms](historical-data-dictionary.md), [modern terms](modern-data-dictionary.md) and [normalization conventions](normalization-conventions.md).

## artifacts

Source-file identities and checksums. Public content is null; source documents are not bundled.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `artifacts.source_id` | TEXT | PK 1; sources.id | Source registry identity. |
| `artifacts.sha256` | TEXT | PK 2;  | SHA-256 of the original artifact or image bytes. |
| `artifacts.media_type` | TEXT | — | Media type when established. |
| `artifacts.retrieved_at` | TEXT | — | Recorded acquisition time. |
| `artifacts.redistribution_status` | TEXT | — | Whether source bytes are included and how source terms apply. |
| `artifacts.content` | BLOB | — | Source-file bytes; null in public releases. |
| `artifacts.metadata_json` | TEXT | — | Structured metadata for this artifact or image. |

## catalogue

Current interpretation plus usable derived conversions and citations.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `catalogue.id` | TEXT | — | Stable identity in this table; links use the indicated foreign keys. |
| `catalogue.source_id` | TEXT | — | Source registry identity. |
| `catalogue.artifact_sha256` | TEXT | — | Checksum identifying the source-file version. |
| `catalogue.source_entry_id` | TEXT | — | Original source-local entry identifier. |
| `catalogue.locator` | TEXT | — | Source-native row, line, page or frame locator. |
| `catalogue.volume` | INTEGER | — | Dreyer Opera Omnia volume for historical records; null for other collections. |
| `catalogue.printed_page` | INTEGER | — | Printed bibliographic page, not automatically a PDF image index. |
| `catalogue.expression` | TEXT | — | Literal source numeric expression. |
| `catalogue.role` | TEXT | — | Evidential role; see the quantity and role reference. |
| `catalogue.event_id` | TEXT | — | Associated source group. |
| `catalogue.series_id` | TEXT | — | Associated source series. |
| `catalogue.version` | INTEGER | — | Interpretation version; zero preserves the initial interpretation. |
| `catalogue.quantity` | TEXT | — | Quantity type; see the quantity and role reference. |
| `catalogue.subject` | TEXT | — | Measured or calculated object. |
| `catalogue.reference_object` | TEXT | — | Other endpoint or comparison object, if recorded. |
| `catalogue.status` | TEXT | — | Normalization status: exact, incomplete, unsupported or source_expression. |
| `catalogue.unit` | TEXT | — | Unit or encoded source notation; modern notation formats are documented separately. |
| `catalogue.value_exact` | TEXT | — | Original normalized scalar as a rational string. Historical magnitudes are unsigned; native modern scalars retain source signs. |
| `catalogue.signed_value_exact` | TEXT | — | Explicit signed historical normalization, when established. |
| `catalogue.derived_value_exact` | TEXT | — | Unsigned magnitude of an existing modern conversion or scalar, as an exact rational string. |
| `catalogue.derived_signed_value_exact` | TEXT | — | The same value retaining its recorded or converted sign. |
| `catalogue.derived_unit` | TEXT | — | Physical unit of the exposed conversion; separate from its encoded input notation. |
| `catalogue.derived_value_decimal` | REAL | — | Floating-point convenience for derived_value_exact. |
| `catalogue.derived_signed_value_decimal` | REAL | — | Floating-point convenience for derived_signed_value_exact. |
| `catalogue.derived_method` | TEXT | — | Recorded conversion method, or source_scalar for a value already in physical units. |
| `catalogue.derived_time_scale` | TEXT | — | Explicit time convention of the result; UT is not silently made UTC or UT1. |
| `catalogue.derived_timestamp` | TEXT | — | Existing derived timestamp, with conversion method; not inferred for undated historical clocks. |
| `catalogue.source_url` | TEXT | — | Original public source-file URL. |
| `catalogue.source_page_url` | TEXT | — | Deep link supported by explicit PDF index or archive page metadata; null when unverified. |
| `catalogue.source_line_number` | INTEGER | — | One-based source-file line number where explicitly stated by the locator. |

## contexts

Source qualifications keyed by context identity and review scope.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `contexts.context_id` | TEXT | PK 1;  | Context identity, always interpreted together with scope_id. |
| `contexts.scope_id` | TEXT | PK 2;  | Opaque review-scope identifier; prevents unrelated contexts with the same ID from merging. |
| `contexts.kind` | TEXT | — | Source-context or relationship type. |
| `contexts.value_json` | TEXT | — | JSON value or source qualification. |
| `contexts.source_id` | TEXT | sources.id | Source registry identity. |
| `contexts.locator_json` | TEXT | — | Structured source locator. |

## control_links

Links Pafko control identities to quantities; not a second observing program.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `control_links.control_id` | TEXT | PK 1;  | Pafko workbook control identity. |
| `control_links.quantity_id` | TEXT | quantities.id | Linked quantity identity. |

## dates

Recorded date claims, without inventing accepted absolute epochs.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `dates.id` | TEXT | PK 1;  | Stable identity in this table; links use the indicated foreign keys. |
| `dates.data_json` | TEXT | — | Additional structured source or relationship metadata. |

## derivation_inputs

Ordered input quantities for identified calculations.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `derivation_inputs.derivation_id` | TEXT | PK 1; derivations.id | Source calculation identity. |
| `derivation_inputs.ordinal` | INTEGER | PK 2;  | Input position in the ordered calculation. |
| `derivation_inputs.quantity_id` | TEXT | quantities.id | Linked quantity identity. |

## derivations

Source-reported calculations and independently recorded arithmetic checks.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `derivations.id` | TEXT | PK 1;  | Stable identity in this table; links use the indicated foreign keys. |
| `derivations.output_quantity_id` | TEXT | quantities.id | Calculation output quantity. |
| `derivations.data_json` | TEXT | — | Additional structured source or relationship metadata. |

## derived_values

Existing exact conversions exposed as typed fields; original interpretations remain unchanged.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `derived_values.quantity_id` | TEXT | PK 1; quantities.id | Linked quantity identity. |
| `derived_values.derived_value_exact` | TEXT | — | Unsigned magnitude of an existing modern conversion or scalar, as an exact rational string. |
| `derived_values.derived_signed_value_exact` | TEXT | — | The same value retaining its recorded or converted sign. |
| `derived_values.derived_unit` | TEXT | — | Physical unit of the exposed conversion; separate from its encoded input notation. |
| `derived_values.derived_value_decimal` | REAL | — | Floating-point convenience for derived_value_exact. |
| `derived_values.derived_signed_value_decimal` | REAL | — | Floating-point convenience for derived_signed_value_exact. |
| `derived_values.derived_method` | TEXT | — | Recorded conversion method, or source_scalar for a value already in physical units. |
| `derived_values.derived_time_scale` | TEXT | — | Explicit time convention of the result; UT is not silently made UTC or UT1. |
| `derived_values.derived_timestamp` | TEXT | — | Existing derived timestamp, with conversion method; not inferred for undated historical clocks. |

## diagrams

Contexts whose kind is source_diagram.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `diagrams.context_id` | TEXT | — | Context identity, always interpreted together with scope_id. |
| `diagrams.scope_id` | TEXT | — | Opaque review-scope identifier; prevents unrelated contexts with the same ID from merging. |
| `diagrams.kind` | TEXT | — | Source-context or relationship type. |
| `diagrams.value_json` | TEXT | — | JSON value or source qualification. |
| `diagrams.source_id` | TEXT | — | Source registry identity. |
| `diagrams.locator_json` | TEXT | — | Structured source locator. |

## group_contexts

Links groups to qualified contexts.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `group_contexts.id` | TEXT | PK 1; groups.id | Stable identity in this table; links use the indicated foreign keys. |
| `group_contexts.context_id` | TEXT | PK 2; contexts.context_id | Context identity, always interpreted together with scope_id. |
| `group_contexts.scope_id` | TEXT | PK 3; contexts.scope_id | Opaque review-scope identifier; prevents unrelated contexts with the same ID from merging. |

## group_dates

Links groups to recorded date claims.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `group_dates.group_id` | TEXT | PK 1; groups.id | Source group identity. |
| `group_dates.date_id` | TEXT | PK 2; dates.id | Recorded date-claim identity. |

## groups

Source observing or calculation groups; membership does not establish independence or simultaneity.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `groups.id` | TEXT | PK 1;  | Stable identity in this table; links use the indicated foreign keys. |
| `groups.clock_quantity_id` | TEXT | quantities.id | Linked observing clock quantity, if explicitly associated. |
| `groups.epoch_quantity_id` | TEXT | quantities.id | Linked calculation epoch quantity; not a substitute for an observing clock. |
| `groups.data_json` | TEXT | — | Additional structured source or relationship metadata. |

## images

Externally hosted image-version metadata; no image pixels or local paths.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `images.source_id` | TEXT | PK 1; sources.id | Source registry identity. |
| `images.frame_id` | TEXT | PK 2;  | Archive frame identifier. |
| `images.version_id` | TEXT | PK 3;  | Archive image-version identifier. |
| `images.sha256` | TEXT | — | SHA-256 of the original artifact or image bytes. |
| `images.archive_md5` | TEXT | — | MD5 supplied by the image archive. |
| `images.bytes` | INTEGER | — | Verified external image byte count. |
| `images.public_url` | TEXT | — | Public archive link. |
| `images.metadata_json` | TEXT | — | Structured metadata for this artifact or image. |

## interpretations

Original and explicitly revised interpretations; highest version is current.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `interpretations.quantity_id` | TEXT | PK 1; quantities.id | Linked quantity identity. |
| `interpretations.version` | INTEGER | PK 2;  | Interpretation version; zero preserves the initial interpretation. |
| `interpretations.quantity` | TEXT | — | Quantity type; see the quantity and role reference. |
| `interpretations.subject` | TEXT | — | Measured or calculated object. |
| `interpretations.reference_object` | TEXT | — | Other endpoint or comparison object, if recorded. |
| `interpretations.status` | TEXT | — | Normalization status: exact, incomplete, unsupported or source_expression. |
| `interpretations.unit` | TEXT | — | Unit or encoded source notation; modern notation formats are documented separately. |
| `interpretations.value_exact` | TEXT | — | Original normalized scalar as a rational string. Historical magnitudes are unsigned; native modern scalars retain source signs. |
| `interpretations.signed_value_exact` | TEXT | — | Explicit signed historical normalization, when established. |
| `interpretations.normalized_json` | TEXT | — | Full preserved normalization payload. |
| `interpretations.components_json` | TEXT | — | Exact original sexagesimal components or explicit null. |
| `interpretations.flags_json` | TEXT | — | Structured quality and interpretation flags. |
| `interpretations.revision_json` | TEXT | — | Evidence for an explicitly versioned interpretation change. |

## locus_contexts

Links source locations to qualified contexts.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `locus_contexts.locus_id` | TEXT | PK 1; source_loci.id | Public source-location identity. |
| `locus_contexts.context_id` | TEXT | PK 2; contexts.context_id | Context identity, always interpreted together with scope_id. |
| `locus_contexts.scope_id` | TEXT | PK 3; contexts.scope_id | Opaque review-scope identifier; prevents unrelated contexts with the same ID from merging. |

## locus_quantities

Links source locations to quantities.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `locus_quantities.locus_id` | TEXT | PK 1; source_loci.id | Public source-location identity. |
| `locus_quantities.quantity_id` | TEXT | PK 2; quantities.id | Linked quantity identity. |

## metadata

Release-level metadata, limitations and license scope.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `metadata.key` | TEXT | PK 1;  | Metadata key. |
| `metadata.value_json` | TEXT | — | JSON value or source qualification. |

## quantities

Preserved source expressions and source-scoped identities.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `quantities.id` | TEXT | PK 1;  | Stable identity in this table; links use the indicated foreign keys. |
| `quantities.volume` | INTEGER | — | Dreyer Opera Omnia volume for historical records; null for other collections. |
| `quantities.printed_page` | INTEGER | — | Printed bibliographic page, not automatically a PDF image index. |
| `quantities.expression` | TEXT | — | Literal source numeric expression. |
| `quantities.role` | TEXT | — | Evidential role; see the quantity and role reference. |
| `quantities.event_id` | TEXT | groups.id | Associated source group. |
| `quantities.series_id` | TEXT | — | Associated source series. |
| `quantities.original_json` | TEXT | — | Original interpretation payload; shared fixed-width lines live in source_lines. |
| `quantities.components_json` | TEXT | — | Exact original sexagesimal components or explicit null. |
| `quantities.uncertainty_json` | TEXT | — | Stated uncertainty and qualifications; missing values are not zero. |
| `quantities.source_id` | TEXT | sources.id | Source registry identity. |
| `quantities.artifact_sha256` | TEXT | artifacts.sha256 | Checksum identifying the source-file version. |
| `quantities.source_entry_id` | TEXT | — | Original source-local entry identifier. |
| `quantities.locator` | TEXT | — | Source-native row, line, page or frame locator. |
| `quantities.scientific_metadata_json` | TEXT | — | Timing, reference-frame, correction and other scientific metadata. |
| `quantities.source_payload_json` | TEXT | — | Native source payload; source_records reconstructs its raw_line where applicable. |

## quantity_citations

Source-file links and explicitly supported page/line locations.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `quantity_citations.quantity_id` | TEXT | PK 1; quantities.id | Linked quantity identity. |
| `quantity_citations.source_url` | TEXT | — | Original public source-file URL. |
| `quantity_citations.source_page_url` | TEXT | — | Deep link supported by explicit PDF index or archive page metadata; null when unverified. |
| `quantity_citations.source_line_number` | INTEGER | — | One-based source-file line number where explicitly stated by the locator. |
| `quantity_citations.locator` | TEXT | — | Source-native row, line, page or frame locator. |

## quantity_contexts

Links quantities to qualified contexts.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `quantity_contexts.id` | TEXT | PK 1; quantities.id | Stable identity in this table; links use the indicated foreign keys. |
| `quantity_contexts.context_id` | TEXT | PK 2; contexts.context_id | Context identity, always interpreted together with scope_id. |
| `quantity_contexts.scope_id` | TEXT | PK 3; contexts.scope_id | Opaque review-scope identifier; prevents unrelated contexts with the same ID from merging. |

## quantity_dates

Links quantities to recorded date claims.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `quantity_dates.quantity_id` | TEXT | PK 1; quantities.id | Linked quantity identity. |
| `quantity_dates.date_id` | TEXT | PK 2; dates.id | Recorded date-claim identity. |

## quantity_links

Typed links between quantities, including alternatives and source relationships.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `quantity_links.from_id` | TEXT | PK 1; quantities.id | Originating quantity. |
| `quantity_links.to_id` | TEXT | PK 2; quantities.id | Related quantity. |
| `quantity_links.kind` | TEXT | PK 3;  | Source-context or relationship type. |

## series

Source associations of repeated readings.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `series.id` | TEXT | PK 1;  | Stable identity in this table; links use the indicated foreign keys. |
| `series.data_json` | TEXT | — | Additional structured source or relationship metadata. |

## series_quantities

Links quantities to their source series.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `series_quantities.series_id` | TEXT | PK 1; series.id | Associated source series. |
| `series_quantities.quantity_id` | TEXT | PK 2; quantities.id | Linked quantity identity. |

## source_lines

One literal fixed-width line per source, artifact version and locator.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `source_lines.source_id` | TEXT | PK 1; artifacts.source_id | Source registry identity. |
| `source_lines.artifact_sha256` | TEXT | PK 2; artifacts.sha256 | Checksum identifying the source-file version. |
| `source_lines.locator` | TEXT | PK 3;  | Source-native row, line, page or frame locator. |
| `source_lines.raw_line` | TEXT | — | Exact source-file line, stored once for its artifact version and locator. |

## source_loci

Public source locations, including provisional or unknown-page qualifications.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `source_loci.id` | TEXT | PK 1;  | Stable identity in this table; links use the indicated foreign keys. |
| `source_loci.source_id` | TEXT | sources.id | Source registry identity. |
| `source_loci.printed_page` | INTEGER | — | Printed bibliographic page, not automatically a PDF image index. |
| `source_loci.status` | TEXT | — | Source-location status, such as reviewed_quantity_citation or automatic_page_index; not a numerical normalization status. |
| `source_loci.data_json` | TEXT | — | Additional structured source or relationship metadata. |

## source_records

Original payloads, reconstructing raw_line from source_lines without duplication.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `source_records.id` | TEXT | — | Stable identity in this table; links use the indicated foreign keys. |
| `source_records.source_id` | TEXT | — | Source registry identity. |
| `source_records.artifact_sha256` | TEXT | — | Checksum identifying the source-file version. |
| `source_records.source_entry_id` | TEXT | — | Original source-local entry identifier. |
| `source_records.expression` | TEXT | — | Literal source numeric expression. |
| `source_records.components_json` | TEXT | — | Exact original sexagesimal components or explicit null. |
| `source_records.source_payload_json` | derived | — | Native source payload; source_records reconstructs its raw_line where applicable. |

## sources

Bibliographic source registry; publication dates are distinguished from access dates.

| Column | SQL type | Key / relationship | Meaning |
| --- | --- | --- | --- |
| `sources.id` | TEXT | PK 1;  | Stable identity in this table; links use the indicated foreign keys. |
| `sources.author` | TEXT | — | Author or responsible institution, distinct from the observing individual. |
| `sources.work_id` | TEXT | — | Bibliographic work identifier, when established. |
| `sources.edition_id` | TEXT | — | Edition identifier, when established. |
| `sources.title` | TEXT | — | Source title. |
| `sources.volume` | INTEGER | — | Dreyer Opera Omnia volume for historical records; null for other collections. |
| `sources.data_json` | TEXT | — | Additional structured source or relationship metadata. |
| `sources.publisher` | TEXT | — | Publishing or distributing institution. |
| `sources.date` | TEXT | — | Citation date qualified by date_kind; not necessarily the date of observation or publication. |
| `sources.date_kind` | TEXT | — | publication_date, publication_year, original_publication_year (the underlying edition rather than its translation), updated_date, source_filename_date, generated_date, accessed or catalogue_record_date. |

## Query indexes

Primary and unique keys cover forward links. These additional indexes support common filters and reverse traversal without changing any values.

| Index | Table and ordered columns |
| --- | --- |
| `quantities_event` | `quantities (event_id, id)` |
| `quantities_series` | `quantities (series_id, id)` |
| `quantities_page` | `quantities (source_id, printed_page, id)` |
| `quantities_role` | `quantities (role, id)` |
| `interpretations_type_subject` | `interpretations (quantity, subject, quantity_id, version)` |
| `groups_clock` | `groups (clock_quantity_id, id)` |
| `groups_epoch` | `groups (epoch_quantity_id, id)` |
| `contexts_source` | `contexts (source_id, context_id, scope_id)` |
| `quantity_contexts_reverse` | `quantity_contexts (context_id, scope_id, id)` |
| `group_contexts_reverse` | `group_contexts (context_id, scope_id, id)` |
| `source_loci_page` | `source_loci (source_id, printed_page, id)` |
| `locus_quantities_reverse` | `locus_quantities (quantity_id, locus_id)` |
| `locus_contexts_reverse` | `locus_contexts (context_id, scope_id, locus_id)` |
| `quantity_dates_reverse` | `quantity_dates (date_id, quantity_id)` |
| `group_dates_reverse` | `group_dates (date_id, group_id)` |
| `series_quantities_reverse` | `series_quantities (quantity_id, series_id)` |
| `derivations_output` | `derivations (output_quantity_id, id)` |
| `derivation_inputs_quantity` | `derivation_inputs (quantity_id, derivation_id)` |
| `control_links_quantity` | `control_links (quantity_id, control_id)` |
| `quantity_links_reverse` | `quantity_links (to_id, kind, from_id)` |

Context lookups retain both `context_id` and `scope_id`; equal labels from different source reviews cannot be merged. Filter current coordinates through the `catalogue` view. SQLite chooses indexes according to the query and data; no elapsed-time guarantee is implied.
