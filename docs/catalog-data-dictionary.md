# Tychonides catalog data dictionary

The [modern quantity, role and notation reference](modern-data-dictionary.md)
covers JJMO, JPL, USNO, Carlsberg, Tokyo and LCO. The [database schema reference](database-schema.md)
documents every table, view and column, including keys and relationships. CI checks
both against the released database so new vocabulary and fields cannot silently
outgrow the documentation.

See [catalog terminology](catalog-terms.md) for exact conversion, source review,
control agreement, release verification and analysis eligibility.

## Find a Definition

| Need | Section |
| --- | --- |
| Understand a value | [Worked examples](#worked-numerical-examples); [original and derived fields](#original-and-derived-fields) |
| Read the CSV | [Column contract](#csv-column-contract); [quantity fields](#quantity-fields) |
| Interpret units and signs | [Exact numbers and units](#exact-numbers-and-units); [conversion conventions](#quantity-types-and-conversion-conventions) |
| Interpret dates | [Dates and clocks](#dates-and-clocks) |
| Follow dependencies | [Source relationships](#source-relationships-and-interpretation); [derivations](#derivations) |
| Retain complete context | [Complete normalization](#complete-normalization-schema-5) |

The detailed definitions below describe source-specific representations. The
[schema reference](database-schema.md) gives SQL structure; the generated
[historical](historical-data-dictionary.md), [modern](modern-data-dictionary.md)
and [normalization](normalization-conventions.md) references define the vocabulary.

## Worked numerical examples

These compact examples explain field semantics; they are not additional catalog
observations. The [public worked example](worked-example.md) instead follows a
cited historical reading through executable normalization and export.

| Case | Representation | Interpretation |
| --- | --- | --- |
| Unknown declination hemisphere | `value_exact = "5400"`, `unit = "arcsecond"`, `signed_value_exact = null` | Magnitude is 1°30′. Null is neither zero nor north; a signed coordinate remains unestablished. |
| Modern source notation | Expression `-00 01 00`, source unit `sexagesimal_degree`, original scalar null; `derived_value_exact = "60"`, `derived_signed_value_exact = "-60"`, `derived_unit = "arcsecond"`, `derived_method = "sexagesimal_conversion"` | Preserve encoded notation and its independently checked physical conversion separately, including a negative coordinate whose degree component is zero. |
| Zodiac longitude | `20 23 ♊`: 20°23′ within Gemini; 80°23′ from zodiac zero | `normalized_json` holds `longitude_origin: start_of_named_sign`, `zodiac_sign: Gemini`, `magnitude_degrees: 1223/60` and `zodiac_longitude_degrees: 4823/60`. The within-sign degree decimal is about 20.3833, not 80.3833. Inherited signs retain their evidence and the same origin distinction. |
| Recorded clock | `H. 10 26′ 25″` → interpreted clock value 37,585 seconds of time → dated epoch absent until justified | A clock value alone establishes no calendar, day origin, meridian or time scale. A date and convention must support any later epoch; unsupported stages remain null. |

An explicit modern date and EDT convention can support a UTC conversion with a
date rollover, such as 23:30 EDT on 17 September to 03:30 UTC on 18 September.

A named-sign coordinate may retain an exact 30° endpoint, including 360° from
zodiac zero for 30° Pisces. A value beyond that endpoint retains its components,
known sign and origin with `normalization_issue=degree_outside_sign` and null
scalar values. It is neither carried into the next sign nor replaced by an
editorial alternative. Queried calculation intervals likewise retain their
source expression and `second_of_time` unit with no adopted scalar.
That mechanical conversion still does not establish exposure midpoint. Hours can
describe clock readings, durations or angular hour angles: inspect quantity and
unit before converting them.

## Original and derived fields

Original columns preserve the source normalization, including encoded notations.
For modern conversions use `derived_value_exact` (unsigned magnitude),
`derived_signed_value_exact`, and `derived_unit`. `derived_value_decimal` and
`derived_signed_value_decimal` are conveniences. `derived_method` identifies the
existing conversion; `derived_time_scale` and `derived_timestamp` keep timing
conventions explicit. These fields expose existing data without re-reducing it.

`source_page_url` links to a specific PDF page when its index is explicit, or to
an original scan leaf matched by the archive's printed-page metadata. It does not
assume the translation PDF has the same pagination as Dreyer. `source_line_number`
is the explicit one-based line number for fixed-width source files. The
`source_lines` table holds each literal line once, and `source_records` reconstructs
complete native payloads. A null deep link is an unverified locator, not a guess.

The [catalog](../resources/catalog/README.md) records quantities from
Tycho Brahe’s books with bibliographic citations, exact units and explicit
interpretive qualifications. The [published editions and PDFs](sources.md)
provide the original readings and their surrounding context.

## Files and counting units

| Download or database table | Contents |
| --- | --- |
| `tychonides.sqlite` | Self-contained catalog, source citations, original expressions, interpretations and relationships. |
| `tychonides.csv` | One row per quantity, with exact values, decimal conveniences, date claims and scientific qualifications. |
| `catalogue` | View of the current interpretation of each source quantity. |
| `quantities`, `interpretations` | Preserved source records and separately versioned interpretations. |
| `groups` | Source groupings and their clock or calculation-epoch links. |
| `series`, `series_quantities` | Ordered associations of repeated readings. |
| `dates`, `quantity_dates`, `group_dates` | Recorded date components, qualifications and associations. |
| `derivations` | Identified numerical inputs, outputs and arithmetic checks. |
| `contexts`, `quantity_contexts`, `group_contexts` | Scientific qualifications and their source scope. |
| `metadata`, `sources` | Release identity, coverage, limitations and public bibliographic citations. |
| `manifest.json` | File fingerprints identifying the numerical release. |

Either download can be used without processing intermediates. The SQLite file
contains the full relationships; CSV includes recorded date claims and source
qualifications as JSON fields. A quantity, printed row, source group,
observing session and independent measurement are different counting units. A
source block can be a table, paragraph, list, heading, note or diagram. Screening
coverage and inspected coverage remain separate.

A diagram label or later summary can restate a recorded angle. Such source
occurrences retain separate records and historical-input roles, with their
relationship to the original reading preserved. They do not establish additional
raw observations or independent repetitions.

## Source identities in the consolidated schema

Each source has its own identity, with author, work, edition and public citation
metadata. Volume and printed page are optional locators within a source; they
are not global source identifiers. Dataset rows, PDF pages, fixed-width lines
and image frames can retain their native locators without invented book numbers.

An occurrence is identified by source, artifact checksum and native entry ID.
Changed artifact bytes retain a separate version. The same row label in two
catalogs does not identify the same measurement, and overlap candidates do not
merge records. Existing historical quantity identities remain stable.

The representation supports instrument settings in inches or turns, angular
coordinates, recorded clocks and reduced catalog products. It preserves stated
EDT, UT, UT1 and UTC conventions, coordinate origin and frame, equinox codes,
limb/center labels, observer identifiers and correction histories separately.
The publication's author is not assumed to be the observer. A derived timestamp
or coordinate conversion remains distinguishable from the source expression.

Images have versioned identifiers, checksums, byte counts, public locators and
metadata. Large image files remain external to the catalog; measured centroids
and reductions can be represented as quantities with their own provenance.
These source-neutral facilities belong to the consolidated schema. The catalog
combines the four-volume Mars selection, [seven supplementary historical books](historical-books-ingestion.md)
and modern observing programs listed in the [source directory](data-sources.md).

The supplementary books include literal numerical evidence in edition-note
contexts that is not necessarily a separate quantity row. Contexts preserve
the note's definition and attachment scope, original or alternative readings and
their unapplied status. These literals do not increase quantity counts and should
not be treated as additional observations or silently substituted for source values.
SQLite retains the full context graph; a CSV quantity row contains its own selected
normalization and linked qualifications, not every standalone context in the book.

The consolidated database distinguishes `sources`, versioned `artifacts`,
`quantities`, observing `groups`, and `interpretations`. Relationships connect
quantities to dates, series, reductions, alternatives and contextual evidence.
Context identities include their source scope, so different qualifications
attached to the same passage remain distinct.

`source_loci` provide public location references linked to quantities and
contexts. A `reviewed_quantity_citation` has an accepted printed-page citation;
an `automatic_page_index` is provisional. Conflicting automatic claims remain
separate from reviewed citations. An unknown page remains null. Annotation
attachment pages identify the cited passage, without asserting where the
annotation itself was printed. Unresolved source references remain explicitly
unresolved rather than linking to a plausible neighbouring record.

A paragraph can span a leaf turn while occupying one line in the edition text.
Its different quantities can therefore have different, page-qualified loci.
Each locus links only the quantities and context scopes belonging to that page.
An unqualified page conflict is rejected; it is not settled by choosing one
page for the whole paragraph. Unambiguous source positions retain their existing
location identities.

`original_json` retains the source record's original interpretation;
`expression` and `components_json` preserve its numerical notation. The
`source_records` view also exposes native payloads supplied by additional source
adapters. `catalogue` selects the latest interpretation without removing earlier
versions. Type and unit interpretation changes do not create new observations.

In CSV, `value_exact` and `signed_value_exact` retain rational strings.
`value_decimal` and `value_degrees_decimal` are floating-point conveniences;
the degree field is present only where that conversion is defined. Magnitude
and hemisphere remain separate. `date_claims_json` contains the recorded date
statements, not accepted timestamps. `scientific_metadata_json` preserves scale
references, coordinate states, correction instructions and other qualifications.

## Quantity fields

### CSV column contract

Columns have a fixed order, verified against the exporter:

| Columns | Meaning |
| --- | --- |
| `id`, `source_id`, `artifact_sha256`, `source_entry_id`, `locator` | Quantity identity, source and artifact version, native identity and locator where available. |
| `volume`, `printed_page`, `expression` | Printed citation and original numerical expression. |
| `quantity`, `role`, `subject`, `reference_object` | Measurement type, evidential role and endpoints. |
| `status`, `unit`, `value_exact`, `signed_value_exact` | Normalization status, units and exact rational values. |
| `value_decimal`, `value_degrees_decimal` | Convenient decimal values; degree conversion only where defined. |
| `interpretation_version`, `event_id` | Selected interpretation and source group, where associated. |
| `original_quantity`, `original_subject`, `original_normalization_status` | Original classification before versioned interpretation changes. |
| `direction`, `record_status` | Recorded direction and qualification. |
| `flags_json`, `uncertainty_json`, `components_json` | Structured qualifications, uncertainty and original number components. |
| `scientific_metadata_json`, `date_claims_json`, `source_url` | Additional scientific context, recorded date statements and public source link. |

Nested series payloads retain `assertion_ids`, the associated quantity identifiers;
the database also exposes these through `series_quantities`. Date payloads retain
`claim_basis`, describing the evidence used to associate a recorded date. Neither
series membership nor a date claim establishes simultaneity or a modern timestamp.

`claim_basis=reviewed_structured_context` identifies named date components
projected from an existing source context. `source_date_expression` retains
the full reviewed label, including relative-night or incomplete-day wording;
`source_context_record_type` and `source_clock_qualification` retain the context's
classification and clock convention where supplied. An unspecified date role
remains unspecified. Missing calendars, day origins and epochs remain null.

Public locators do not provide reliable within-page coordinates for every reading.
Use the original numerical expression, subject, date context and printed page
together when checking a dense source page; an opaque locus ID is not a scan
coordinate or a public edition line number.

| Field | Meaning |
| --- | --- |
| `id` | Stable identity of the source quantity. |
| `volume`, `printed_page` | Dreyer’s _Opera Omnia_ volume and printed page. |
| `source_fragment_pages` | Optional ordered printed pages supplying parts of one continued quantity. The first is its primary `printed_page`; page fragments do not create additional observations. `[null]` retains an unknown printed numeral when an explicit `source_page_locator` supplies the physical scan citation. |
| `source_component_carry` | In `scientific_metadata_json`, evidence for a leading angular component or whole proportional coefficient supplied under an explicit source carry-down instruction. Angular quantities permit their stated leading angular place; `proportional_minutes` permits only `proportional_minute`. `unit`, `source_line`, `source_column`, `source_expression` and `source_printed_page` identify the nearest printed origin. A separate terminal `recte` proposal does not replace that printed origin. `rule_context_id` together with `rule_scope_id` identifies the qualified instruction context. The current expression retains its blank cell and printed lower components; an inherited component does not create another printed reading. |
| `source_page_locator` | Optional structured source PDF page (`source_pdf_page`) or contiguous range (`source_pdf_pages`), literal printed-page label and separate later-hand label. It permits a null `printed_page` when that numeral is unestablished; labels do not supply an invented page number. A range does not establish which page contains each row. Retained in scientific metadata. |
| `edition_note_marker` | Marker of a source-bound numerical edition note, such as `[^ed86]`, retained in `scientific_metadata_json`. An unpaged note has null `printed_page` and an `annotation_of_id` linking its preserved original quantity. Its role is editorial, it has no observing event, and proposed replacements remain unapplied. The marker identifies the note in the cited edition; the original quantity's page is not assigned to the note. |
| `source_numeric_fragments` | In `scientific_metadata_json`, the ordered literal parts of a quantity continued across source locations. `expression` retains the primary fragment; these parts and `components_json` preserve the complete numerical interpretation without exposing internal bindings. For example, `7^h^` and `29^m^` supply a recorded clock of 7 h 29 m. |
| `source_scope_locus_range` | Ordered start and end locus references for a source qualification covering several rows. These are bibliographic pointers, not numerical values or an additional observing group. |
| `quantity` | Altitude, declination, separation, clock, correction or other stated quantity. |
| `subject`, `reference` | The measured or calculated object and, where applicable, the other endpoint. |
| `source_reference_status` | `not_recorded` identifies an angular separation whose recorded or base-witness comparison endpoint is missing. `antecedent_unresolved`, with the corresponding caution flag, identifies an unestablished association with a source label. In either case `reference` remains null; neither a manuscript restoration nor a nearby star silently replaces the gap. Unexplained missing endpoints are rejected. |
| `editorial_reference_alternative`, `editorial_reference_status` | A separately retained editorial identification. For an unrecorded endpoint, `tentative` marks a proposal and `restored_from_witness` marks an explicit manuscript restoration. Neither becomes the original recorded reference. Existing disputed endpoint alternatives retain their original status. |
| `editorial_subject_alternative`, `editorial_subject_status` | An explicit editorial correction of an angular reading's subject. `correction_as_stated` preserves the alternative beside the unchanged recorded `subject` and angle; the source-dispute flag remains attached. |
| `role` | Instrument reading, calibration, historical input, reduction, prediction, adopted value or editorial contribution. |
| `prediction_relation` | `retrograde_change_over_source_interval` and `direct_change_over_source_interval` identify a named model's predicted decrease or increase in Mars's longitude over the source interval. Both retain angular units; the interval and any lower-bound qualification remain separate. |
| `parallax_component` | `altitude`, `longitude` or `latitude` identifies an Earth-referenced historical component. A calculated result has role `reduction`; a reused component retains `historical_input` and `historical_parallax_not_detection`. The source's component frame remains a separate qualification. |
| `comparison_quantity` | `parallax_angle` or `angular_diameter` for a source-stated angular difference between an attributed historical model and the author's result. The difference has quantity `calculation_angle` and role `historical_comparison`; it is not itself a parallax or diameter measurement. |
| `comparison_relation` | For these angular comparisons, `model_smaller_than_source` or `model_larger_than_source` preserves which result the source describes as smaller or larger. The magnitude remains unsigned, and the named model, source qualifications and observing-group link remain separate. Other comparison families retain their own documented relations. |
| `source_distance_model` | `Copernicus` preserves the explicit attribution of a Mars–Earth distance in Earth-radius units. The role distinguishes an adopted input from a source-derived result; neither is an observed distance or a modern ephemeris. |
| `source_prediction_kind` | `eclipse_ephemeris` identifies a reviewed tabulated eclipse prediction. Point times, elapsed durations and native digit extents retain distinct quantities and the role `historical_prediction`. Source table families, meridians and date conventions remain qualified by their cited canon. |
| `source_coordinate_product` | Source-bound attribution for a historical coordinate prediction or comparison. `authorities` preserves the literal authority labels governing that printed value; several named authorities do not multiply one printed value into independent measurements. `basis_context_id` identifies the attribution evidence within the quantity's scoped context links. Follow `quantity_contexts` and its `scope_id` when resolving it. The linked context records the source label and scientific role. These products have no observing-event association; exact conversion does not establish the accuracy of the coordinate or the historical calculation. |
| `source_eclipse_phase` | `beginning`, `middle` or `end` for an explicitly identified historical eclipse phase; `unstated` preserves the absence of a phase label in an eclipse ephemeris. These `calculation_epoch` quantities retain their model and native clock expression; they are not observing clocks. Durations and extents do not acquire a point-phase label. |
| `source_extent_unit` | Explicit `digit` for a native `eclipse_extent` input or prediction. Components `digit`, `digit_minute` and `digit_second` preserve sexagesimal subdivisions as `source_eclipse_digit`; for example, `10 digits 55′ 6″` is exactly 6551/600 digits. A period separating the whole digit from prime-marked subdivisions, as in `9.34′ 52″`, is not a decimal point. Commas may separate word-labeled places. Bare table places require their reviewed header units in `unit_basis`. A shared Sun-or-Moon conversion may retain subject `Sun and Moon` as one printed entry. A queried figure keeps `source_eclipse_digit`, empty interpreted components and no scalar. A standalone digit-minute or digit-second retains its own written component without adding a recorded whole digit. A source-bound continuation can join a separately glossed fractional component into one extent. No angular or diameter-fraction conversion is inferred. Legacy point notation retains its separate native unit and body scope. |
| `direction` | Explicitly supported north, south, east or west; otherwise null. |
| `source_component_label` | A stated limb or instrument-setting label, or `declination` / `right_ascension` for a historical equatorial refraction component. The latter labels retain angular units and historical-correction roles; they do not describe a modern vertical-ray refraction model. |
| `normalized` | Exact numerical representation, unit and recorded component precision. |
| `source_scalar_scale` | Stated whole-sine or radius reference for native sine and chord values, or reference length for `model_length`. The printed scalar is retained, rather than silently divided by this scale or converted to an angle. The source context identifies the reference segment. |
| `source_number_grouping` | Explicit integer grouping for a source scalar: `spaced_thousands` (including a trailing mixed fraction), `spaced_integer_digits`, `comma_thousands`, or `middot_integer_digits`. For example, the explicitly glossed `1068·57 [106857]` becomes the integer 106857 under the last convention. Native mile counts, whole Earth-radius counts and whole `source_part` lengths also permit `comma_thousands`. The literal stays unchanged. Grouping is rejected for angles, clocks and compound native distances; `52 semidiameters 25′` remains 52 + 25/60 radii. |
| `comma_thousands_mixed_fraction` | An explicit grouping interpretation for a complete comma-grouped number followed by a proper fraction, including a written vulgar fraction. `107,231 1/7` remains exactly 750618/7; `17,059½` remains exactly 34119/2. It does not change the stricter `comma_thousands` convention or permit trailing numbers/units to be discarded. |
| `source_unit_notation` | Explicitly reviewed notation handled by the shared parser: `parts_1_minutes`, `roman_sexagesimal_places`, `parts_slash_minutes`, `postfixed_minute_second_third_slashes`, `tabular_dms_terminal_half`, `paired_decimal_tenths` (native sine interpolation increments), or `dms_latitude_terminal_half_minute` (a declared 30-arcsecond latitude point, described below). Parts/slash notation reads `p. 41/35` as 41 degrees 35 minutes. The postfixed three-place notation reads `19 /6 // 1 ///` as 19 arcminutes, 6 arcseconds and 1 sexagesimal third. The tabular form requires its selected application below and consumes exactly three places; `0 0 2.` means 0 degrees, 0 minutes, 2½ seconds under that application. Its terminal point is a half-place marker, not a decimal separator or an inferred punctuation rule for other sources. Partial expressions and contradictory place marks are rejected. |
| `source_tabular_application` | `hours_by_arcminutes` identifies the selected use of a multipurpose proportional-motion table: hours applied to an arcminute daily motion produce degrees, arcminutes and arcseconds. This interpretation accompanies each exported value in scientific metadata. Other source applications remain in the table context and can assign different dimensions to the same three written fields. A queried entry retains this application but has no scalar; a linked editorial alternative remains unapplied. The selected use does not make the table an observation. |
| `source_zodiac_sector` | Explicit sector interpretation, currently `{"kind":"decan","ordinal":1}`, with ordinal 1–3 and an evidence-bound zodiac sign. This denotes a ten-degree sector, not a point coordinate. |
| `source_digit_restorations`, `source_component_order` | Explicitly reviewed bracketed digit completions and their numerical component order. For example, `5[4]′ 23″` retains its literal notation while the declared `5[4]` completion supplies 54 proportional minutes. Queried digits, numerical substitutions, partial token matches and conflicting units are rejected. The completion is edition evidence, not a correction chosen from a predicted value. |
| `event_id`, `series_id`, `ordinal` | Source-group and repeated-series relationships. |
| `variant_of_id`, `annotation_of_id` | Relationships to a preserved original quantity. |
| `source_value_equal_to_id` | An explicit source statement that a separation or recorded clock repeats an earlier value. Each record keeps its own wording, endpoints and date context. |
| `source_equality_kind` | `repeated_measurement` for a reading explicitly stated to be “the same.” It retains the same endpoints as its original and may repeat an unresolved value without supplying a number. |
| `source_date_claim_ids` | Date statements associated with the record; not accepted observing timestamps. |
| `calculation_epoch_id` | A separately stated calculation epoch, where identified. |
| `time_inference_basis` | Reviewed basis for an `inferred_time`; currently `equatorial_distance`, preserving a derived time without a recorded clock. |
| `source_time_scale` | Explicit historical `apparent` or `equal` time on a clock, calculation epoch or inferred time. It does not establish a modern time scale, calendar, meridian or absolute timestamp. |
| `source_coordinate_state` | Optional source label such as `refracted`, `apparent`, `free_of_refraction` or `true` on reviewed coordinates; a historical claim, not modern accuracy. A Mars declination explicitly adopted as a `historical_input` may retain `true`, `apparent` or `corrected_as_stated` without becoming a raw reading. The last label leaves the correction type, amount and original value unspecified. Reviewed stellar reference declinations and reduced stellar separations can retain `true` with their separate calibration or reduction roles. |
| `source_reduction_method`, `source_reduction_references` | Reviewed method and named comparison objects used to obtain a coordinate; separate from raw separation endpoints. |
| `source_adoption_preference` | Optional named comparison object favored in an adopted right ascension; a qualitative preference, without a numerical weight. |
| `source_adoption_preferences` | Two or more explicitly favored comparison objects, without numerical weights; used separately from the singular preference field. |
| `source_comparison_sign` | The source's sign on a stated difference; separate from celestial hemisphere and signed coordinate values. `not_stated` preserves an unsigned source-witness difference without inventing a plus or minus sign. Model, recap and source-witness comparisons retain their separately defined relations. |
| `comparison_sources` | For a stated separation comparison, two ordered source-version labels. These identify the first and second attributed readings, not independent observing sessions. |
| `comparison_label_original` | The literal sign label printed beside a separation difference, such as `plus`, `pl.`, `minus`, `min.` or `min⁹`; absent for an unsigned difference with no printed label. A superscript in this reviewed contraction is not a numerical component or a footnote marker. |
| `source_comparison_measure` | A native historical size comparison concerns `diameter`, `bulk`, `apparent_diameter` or `radial_distance`. `not_stated` preserves an unspecified dimension only for separate scalar operands in a `first_to_second_as_stated` ratio; it does not establish a diameter or bulk ratio. Scalars are dimensionless or source length operands, not SI measurements; no unprinted quotient is substituted. |
| `source_comparison_endpoints` | The two ordered bodies compared, retained with the stated measure. A comparison's calculation subject identifies the first endpoint. |
| `source_comparison_relation` | `first_larger`, `first_smaller` or `first_to_second_as_stated`. A source saying the Moon is 39 times smaller retains 39 with the inverse relation; the exporter does not replace it with 1/39. |
| `source_comparison_term` | `factor`, `divisor`, `additional_fraction`, `subtracted_fraction`, `additional_amount`, `first_operand` or `second_operand`. Printed ratio operands and supplements remain separate; ingestion does not divide them or silently add or subtract a fraction. An additional amount is not the body's full size factor. |
| `source_stellar_class` | A source's fixed-star size class, 1–6. Retained on its associated diameter or scalar assertion; it does not imply modern calibrated photometry. |
| `source_comparison_reference_unit` | For a native distance comparison, `diameter` or `semidiameter` of the second endpoint. Thus 576 Earth diameters remains 576 with its diameter reference, without being silently doubled into Earth radii. |
| `source_length_role` | Distinguishes `radial_distance`, `physical_diameter`, `distance_adjustment`, `orbital_radius`, `orbital_diameter`, `orbital_circumference` and `construction_side` in native length units. Sharing Earth-radius units does not make a physical body diameter a distance from Earth. |
| `source_repeat_count`, `source_repetition_label` | A source-reported count attached to one printed separation: `1` with `semel` or `once`, `2` with `bis`, `twice` or `semel atque iterum`, or `3` with `ter` or `three times`. Counts do not create additional readings or assigned clocks. |
| `source_semidiameter_body` | The body defining a reviewed distance unit; currently `Earth`, meaning Earth-radius units without a kilometer conversion. |
| `semidiameter`, `semidiameter_minute`, `semidiameter_second` | Native distance components in a source-named radius, 1/60 and 1/3600 of it. `19` radii, `50` minutes and `12` seconds becomes exactly 5951/300 radii. These are lengths, not angular or clock units. A queried distance has no adopted scalar; omitted places are not invented. |
| `mile`, `mile_minute`, `mile_second` | Native mile and its sexagesimal length places, retaining the quantity's German or ordinary mile. `46` miles and `49⅔` mile-minutes becomes exactly 8429/180 native miles. No SI conversion is implied; scalar mile counts remain supported separately. |
| `source_instrument_label` | An explicitly named instrument with reviewed quantity scope: `sextant`, `quadrant`, `solid quadrant`, `revolving quadrant`, `revolving instrument`, `lesser quadrant`, `steel instrument`, `steel quadrant`, `iron quadrant` or `mural quadrant` for altitudes; `armillae` for recorded declinations. The edition's broader `revolving instrument` label is not silently renamed. |
| `source_instrument_qualifier` | `largest` preserves the source's qualifier for armillae used for recorded declinations. It supplies no physical dimension or numerical precision. |
| `source_correction_scope` | Scope of a reviewed historical clock-fast rule: currently `current_observing_sequence`; the rule is retained without altering recorded clock values. |
| `record_status`, `flags` | Cancellation, approximation, uncertainty and other interpretive qualifications. |
| `workbook_control_id` | A source-identity link to Pafko’s independent entry, where established. |

A null value means the interpretation or component is not established. It does
not mean zero. Incomplete printed figures remain incomplete; numerical agreement
with a model cannot supply missing digits.

The Spica refraction table on XI p.84 separates altitude arguments
(`historical_input`, subject `Spica refraction table`), two equatorial
refraction components (`historical_correction`, subject `Spica`) and two
adopted stellar inputs (`adopted_value`). Its true declination is a stated
historical input, not a measured or modern reference position. Research use
of this table does not establish historical application to a Mars observation.

A normalized bound retains the printed threshold, not an exact measured value.
For example, the August 31, 1563 latitude on X p.3 is beyond 2° south:
`source_lower_bound` qualifies a magnitude threshold of 7,200 arcseconds.
The reviewed context retains the strict comparison; the signed latitude is
south of −2°, rather than equal to −2°. Approximate triangle descriptions do
not supply measured 60° or 90° angles. Early coordinates with unresolved
observational, reduction or tabular attribution remain `contextual_coordinate`;
the explicitly tabular September 20 positions are `historical_prediction`.

Supporting comet measurements retain `comet head` as their target. A description
of a tail directed toward Mars is separate source context. Apparent head size,
horizontal coordinates and stellar separations keep their own measurement types;
an unapplied instrumental-parallax correction remains distinct from celestial
parallax or a correction amount.

`angular_length` records an angular extent along an object, such as a comet's
tail, in exact arcseconds with a degree conversion. Its subject remains
`comet tail`; it is distinct from `angular_diameter` of the head and from
angular separation between two named objects. On XIII p.388, 4½° becomes
16,200 arcseconds without turning the dimness qualification into an error bar.

An explicitly reported advance over a dated interval can also use
`angular_length`, with subject `Mars` and role `reduction`. It is an angular
extent, not an absolute longitude. `angular_motion_difference` with role
`historical_comparison`, a named model and
`comparison_relation=angular_motion_shortfall_over_source_interval` records
a source-stated shortfall over that interval. The interval's duration remains
a separate `clock_elapsed_time`; neither quantity is an angular daily rate.

A clock row printing seconds alone retains only its `second` component and
the flags `clock_hour_unstated` and `clock_minute_unstated`. Source contexts
can supply separately evidenced hour and minute links and complete contextual
components. These derived components do not replace the printed expression
or establish an absolute timestamp.

An explicit “the same amount” (`tantundem`) or “by the same interval” can state a second separation without
repeating its numeral. The record retains that wording, empty numeric components,
`source_value_stated_equal` and a link to the earlier exact separation. Its
normalized value and precision come from the linked original; they are not a
second printed number or an independently established precision. Both records
retain their own comparison stars. Unstated equality, mismatched subjects,
reference chains and invented components are rejected.

A separate reading labeled “the same” uses `repeated_reading` and
`source_equality_kind: repeated_measurement`. Its original may be a recorded
or repeated reading, but its endpoints must agree. If the original notation
is unresolved, the repeated reading retains the equality link and null
numerical value. It does not recover the missing digits. Shared degree
components across several readings are bound to each reading's distinct
minute fragment; reusing those degrees does not duplicate the full reading.

“The hour as above” likewise retains empty numeric components and a link to an
earlier exact clock value. The normalized hour and precision are shared; the
source expressions, date claims and observing groups remain separate. The link
does not transfer an observing date or establish an absolute timestamp.

`source_alternative` preserves an alternative printed in the observational text
without identifying its author or asserting that it corrects the first value.
It links through `variant_of_id`, retains `alternative_suggestion_not_applied`
and `not_an_additional_raw_reading`, and never replaces its original. An
abbreviated alternative can inherit a component only from that linked original;
the original abbreviated expression and the inheritance remain explicit.
For example, the stellar separation “16°28′, or 30′” on XIII p.145 retains
16°28′ and the linked interpretation 16°30′, without choosing between them.

`source_model_attribution=unnamed_as_stated` and
`source_model_label=our restitution` preserve the p.155 comparison's wording
without assigning it to a named astronomer or system. `model_name` remains null.
Its partial longitude result retains `historical_prediction`; the reported
difference retains `historical_comparison`. An unstated zodiac sign or coordinate
frame stays unresolved, and agreement with one conditional observation branch
cannot identify the model or choose the branch.

In an eclipse ephemeris, `source_model_label=old ephemeris` with
`source_model_attribution=unnamed_as_stated` preserves an explicitly unnamed
source. `source_model_label=ephemerides` with
`source_model_attribution=unestablished_from_canon` instead records a row that
cannot be assigned through the printed source canon. These are different
qualifications. A year outside the canon is retained without silently changing
its digits to obtain a model attribution. Named table families do not imply
that their historical prediction engines have been reconstructed.

Native digit columns can contain `9 0′`, `13 T. 18′`, or `12½ Tot.` under their
reviewed unit headings. These retain, respectively, 9, 133/10 and 25/2 native
digits. The totality qualifier remains in the expression and source context;
it is not an angular unit. A categorical `Total` without a printed number
retains no scalar, rather than acquiring an assumed value of 12. Queried
durations likewise retain their expression without an adopted scalar.

The same unnamed attribution can accompany an explicitly named-sign longitude,
as in the p.221 test. Its Leo-relative expression and normalized zodiac longitude
remain separate. An unsigned model-difference magnitude does not acquire an
invented printed plus or minus sign. The argument label `anomaly` preserves the
source term without identifying a modern mean, eccentric or true anomaly.

`altitude_difference` preserves a source-reported difference between altitudes
as an unsigned angle. The reported difference remains separate from the input
altitudes and from a modern recomputation. On X p.243, the stated two-minute
difference between Aldebaran altitudes is retained even though the displayed
inputs differ by two and a half minutes. Its derivation records that discrepancy
without replacing the source result or applying an instrument correction.

`azimuth_correction` preserves an explicitly stated angular adjustment separately
from a recorded azimuth. Its source context distinguishes adding a number to a
logged bearing from moving an instrument's index. An adjustment already included
in a recorded value must not be applied a second time. The January 19, 1583
morning and evening records on X pp.245–246 illustrate these different operations.

`unclassified_angle` with `measurement_type_unresolved` preserves a numerical
angle whose measurement type has not been established. Its degree-and-minute
components can normalize exactly without becoming an altitude, azimuth or hour
angle. The east qualifier in the tail-of-Leo column on XIII p.142 remains source
context; no directional coordinate interpretation is assigned.
An incomplete angle can retain its known `arcsecond` unit while its magnitude,
degree conversion and signed magnitude remain null. A printed ellipsis is a
missing value, not zero or a replacement taken from another row.
`source_quantity_fragment` instead identifies a deliberately partial expression,
such as components separated by a leaf turn and an intervening table. Its known
components retain their units in `components_json`, but the partial record has
incomplete normalization and no complete scalar. Typed context links can connect
the parts. This flag does not claim that the printed numerals are damaged or
that the edition omitted them; a complete interpretation remains separate.

`source_unit_notation=dms_latitude_terminal_half_minute` records an explicitly
reviewed table convention in which a point following the latitude's minute
component adds 30 arcseconds. Thus `30° 33′.` retains its literal form and
normalizes to 30°33′30″. This convention applies to Tycho's latitude column in
Origanus's stellar tables, whose introduction states the rule. It does not
extend to other punctuation, longitude columns, or magnitude classes. A following
hemisphere letter is preserved separately in the source context and direction;
it does not change the point's numerical meaning.

An incomplete clock likewise retains its known `second_of_time` unit while all
numerical magnitudes remain null. A bracketed `[?]` inside a fraction belongs to
the original expression and must survive removal of bilingual apparatus.
`source_component_label=with both`, `with one` or `with the other` retains a qualification whose referent
is unresolved. It identifies one printed declination, without naming pinnules or
creating an additional numerical reading. The unresolved instrument/setting flag
remains explicit. Instrument labels on altitude readings do not apply to adjacent
declinations. An absent quantity-level label can coexist with a scoped instrument
statement in linked context. Use that scope explicitly; do not forward-fill an
instrument from adjacent records.

Source star names remain distinct from modern catalog identifications.
`head of Medusa` and `bright side of Perseus` preserve the printed comparison
objects. `Canicula`, `Lesser Dog` and `Greater Dog` retain their local labels;
the catalog does not merge them through an assumed alias.

On XIII p.44, the comparison star for the first three January 12 separations is
not recorded; the source note tentatively proposes the bright star of Aries.
Their numerical angles normalize exactly while their recorded `reference` stays
null. The editorial proposal is available separately for explicit analysis
scenarios; it is not a default observed endpoint.

## Exact numbers and units

`source_editorial_component_supply` marks a value that depends on an explicitly
supplied component in the edition, such as the degree in `[18] 21 37`. The
literal brackets remain in the original expression. Exact conversion follows
the stated supply; it does not establish that the component was inked in the
printed source. Per-quantity source context identifies the supplied place and
its status. This qualification is distinct from an unapplied `recte` alternative
and from a component mechanically carried under a source-bound table rule.

Elapsed durations can retain `day_minute`, `day_second` and `day_third` components:
these mean 1/60, 1/3600 and 1/216000 of a source day, respectively. They normalize
to 1,440, 24 and 2/5 seconds of time when a day is represented as 86,400 seconds. Ordinary clock
`minute` and `second` components retain their usual meanings. The original
notation remains unchanged; a degree/minute-style expression can represent a
sexagesimal number of days when its calculation and explicit conversion establish
that interpretation. This is a contextual unit assignment, never a global rule
for a printed `D.` or degree sign, and establishes no calendar timestamp.

`polar_distance` preserves a stated angular distance from a celestial pole.
It is not silently converted to declination or given a declination hemisphere.
The pole-star entry on XIII p.143 belongs to the stated March 1598 reference
epoch, without an observing day or absolute timestamp.

Unassigned numeric fragments retain their original expression and location in
source context while their subject, unit and interpretation remain unresolved.
They must not acquire a neighbouring star's identity or omitted angular
components merely to produce a number.

`instrument_dimension_angle` preserves an instrument dimension explicitly stated
in angular units. On XIII p.110, the Radius brass channel's stated ⅔ degree
normalizes to 2,400 arcseconds as a historical input. This is neither its
resulting error nor a celestial parallax or applied correction. Its linked
November 28–29 dates describe instrument use, not a dimension-measurement epoch.

Historical site settings retain descriptive subjects such as `Resterhafe pole
elevation` and `Resterhafe historical longitude` as angular inputs, separately
from Mars coordinates. An unknown longitude origin, sign, datum or measurement
epoch stays unknown. Instrument capability is supporting metadata: its normalized
angle and approximate qualification must be included in the final dataset even
when the explanatory paragraph lies outside the screened Mars spans.

The adopted 55°53′ pole elevation on X p.59 is a `calculation_angle` with subject
`observatory pole` and role `historical_input`. Its source accuracy claim mentions
one minute; the threshold normalizes to 60 arcseconds in the supporting metadata,
while verified statistical uncertainty remains null. The input has no assigned
measurement epoch or modern geographic datum.

`source_scale_ratio` preserves an explicit relative model scale. Its normalized
ratio retains `source_scale_part` and `source_reference_scale`: 9½ of 60 becomes
`19/120`, with operands `19/2` and `60`. The stated eccentric center of Mars and
Earth are the endpoints; this is neither a calibrated physical length nor a
measured Mars–Earth distance.

`separation_ratio` preserves an approximate visual comparison of two angular
separations. The numerator has the recorded `subject` and `reference`; the two
`separation_ratio_denominator` endpoints identify its baseline. For example,
Mars–lower Gemini head described as about double the head-to-head distance
normalizes to the dimensionless ratio `2`, with `source_visual_estimate` and
`source_approximate`. Exact numerical normalization does not imply an exact
observation, and no angular magnitude or modern stellar identity is supplied.

`source_parameter_kind=greatest_northern_latitude` identifies a historical
maximum-latitude parameter. A node-distance correction remains a calculation
angle with `argument_name=node_distance_correction`. Source recap differences
use the explicit `comparison_relation=observed_minus_computed` or
`computed_minus_observed` and
`source_comparison_sign=plus`, `minus` or `equal`; their magnitude stays
unsigned. These signs supply neither a latitude hemisphere nor an error bar.

A greatest-latitude parameter may also retain role `reduction` when the source
constructs it, as on XIII p.222. This source parameter is not automatically a
modern heliocentric orbital inclination. A longitude input explicitly marked
corrected can retain `source_coordinate_state=corrected_as_stated` without
supplying an unprinted original value or correction amount.

`proportional_minutes` preserves a historical sexagesimal coefficient: one
proportional minute is 1/60 of unity and one proportional second is 1/3600.
For example, 22 46 becomes the exact ratio `683/1800`. Components retain their
literal parts; `normalized.unit=ratio` supplies neither an angle nor a time.
`least_component_unit` distinguishes proportional minutes from stated seconds.
The same representation retains native sine coefficients on a radius of 60.
For example, a printed `1 29` under Riccioli's latitude-sine convention becomes
the ratio `89/3600`, preserving components 1 and 29. It is not a latitude of
1°29′: the source obtains the angular latitude through a subsequent calculation
and lookup. Source context identifies that application and its scale; adjacent
angular reduction and curtation entries retain angular units.
`calculation_angle` with `argument_name=node_distance` identifies the separate
angular argument used in the latitude investigation.

An editor-reported calculation-year alternative has
`source_date_role=calculation_target_variant` and a manuscript-witness label.
It remains a source claim alongside the printed year, attached to the same
quantities. Year-only table headings do not supply a month, day or epoch.

`source_coordinate_state=parallax_included_as_stated` preserves a historical
coordinate reduction's explicit included-parallax qualifier. It does not
supply a numerical correction, an uncorrected position or a modern reference
frame. The recorded coordinate stays unchanged; any later correction scenario
must establish what the source already included before applying another term.

`calculation_angle` with `argument_name=latitude_complement` preserves a stated
complement used in a historical reduction. It is a calculation intermediate,
distinct from the planet's latitude; no hemisphere is assigned to it.

`source_parallax_context=ecliptic_coordinate_reduction` identifies a historical
longitude or latitude correction explicitly described as parallax. Its
`source_parallax_operation` retains the printed `add` or `subtract` instruction;
the correction magnitude remains unsigned. These instructions are distinct
from signed coordinate changes and from a measured parallax. In particular,
subtracting from a southern latitude is not automatically subtraction in a
coordinate system whose positive direction is north.

`angle_component` preserves a separately reported degree or minute component. Its
`normalized.unit=source_angle_component` and `least_component_unit=degree` or `arcminute`
identify a literal component value, not a complete angular measurement or an
angle converted to arcseconds. The editorial variant links through
`annotation_of_id` to the printed angle with the same endpoints. It has no
observing event or inherited minutes, hemisphere or signed magnitude.

Numerical endnotes retain their own citation and interpretation. For example,
a separately reported `47′` component remains an `angle_component` linked to
the original angle; it does not supply that angle's missing or queried degree
and minute places. A complete alternative coordinate remains a separate
editorial quantity. `edition_note_marker` allows these records to be cited
without inventing a printed-page location for a collected endnote. The flat
`locator` field also carries the marker for direct use in CSV and SQL queries.

`clock_component` preserves a separately reported component of a clock reading.
Its `normalized.unit=source_clock_component` and `least_component_unit=minute`
mean that `magnitude` is the literal minute-component value, including a reported
60. It is neither seconds of elapsed time nor a complete clock reading. The
editorial variant links through `annotation_of_id` to its printed clock and
cannot be an event's clock. Missing components are not supplied or carried into
another hour. A complete clock still requires ordinary sexagesimal limits.

`normalized.magnitude` is an unsigned rational string, such as `125/2`.
`normalized.status` distinguishes exact conversion, incomplete figures and
unsupported notation. Exact conversion preserves the source number; it does not
establish observational accuracy.

`source_notation_unresolved` retains an angular statement whose notation or unit
does not yet support a chosen interpretation. `normalized.unit` records the
eventual conversion target, such as arcseconds; it does not assign an unprinted
unit to an unscaled source fraction. Scalar fields stay null and
`normalized.normalization_issue` records `source_notation_unresolved`. The literal
expression is preserved. This is an interpretation limit, not a transcription
error.

An uncertain native comparison operand can likewise retain `source_scalar`,
`source_parameter_kind=comparison_multiplier`, empty components and
`source_notation_unresolved`. For example, `⟦33/53⟧` retains two possible readings
without choosing either one or interpreting their slash as division. This
requires a historical calculation role with no observing event or direction;
the normalized unit is `source_scalar` and every numerical value stays null.

It also covers a source calculation epoch whose time-unit marks remain
unresolved. On XIII p.221 the model heading prints “H. 9 H. 32”; the native scan
agrees with the edition. The known quantity remains a `calculation_epoch` with
conversion target `second_of_time`, no chosen components and no scalar value.
The parallel “H. 9 M. 32” elsewhere on the page is retained as evidence without
silently replacing the heading. This is not an additional observing clock.

`unclassified_numeric_expression` preserves a computational or diagram numeral
whose physical quantity or units remain unestablished. Its normalization is
`unsupported`, with unit label `source_numeric_expression`, no components or
scalar magnitude, and issue `physical_quantity_or_units_unresolved`.
`numeric_expression_original` exports the bounded numeric literal, such as
“14′40″”, “80 49.” or “4.30 [?]”. A registered word numeral such as
`quadraginta` also retains its literal and verified `source_word_numbers`
mapping to `40`, while its physical units and scalar magnitude remain
unestablished. Unknown words, incorrect conversions and unused mappings are
rejected. This representation supports calculations for each named celestial
body; it does not turn them into raw observations. General prose and private
source fields are excluded.
These expressions do not become angles, times or proportional coefficients
merely because one interpretation could fit surrounding arithmetic.

| Unit | Meaning |
| --- | --- |
| `arcsecond` | Angular magnitude. |
| `second_of_time` | A recorded or inferred time, calculation epoch or interval, according to its quantity. |
| `arcsecond_per_source_day` | A historical daily-motion rate. |
| `source_semidiameter` | A distance expressed in the source’s semidiameter unit. |
| `ratio` | A dimensionless source ratio, proportional coefficient or correction rule. |
| `source_angle_component` | A separately reported degree or minute component, not a complete angle. |
| `source_clock_component` | A separately reported minute-component value, not a complete clock. |
| `source_visual_magnitude_class` | A native stellar visual class; no calibrated photometric passband or flux conversion is implied. |

`stellar_magnitude_class` preserves numerical classifications and their literal
punctuation: `3:`, `4.` and `3-` retain the written class and modifier. A fractional
class remains in that native scale. Nebulous descriptions such as `ne.` have no
scalar; a queried or alternative numerical class also remains without a scalar,
with its unresolved status explicit. Neither case means zero brightness.

A source's observed visual classification can have role `recorded_reading`;
tabulated or adopted classifications retain their respective roles. Comparisons
and bounds keep their qualifications. A statement that an object rivals Venus
or Jupiter supplies no numerical magnitude, and a disappearance report supplies
no invented limiting magnitude. Native classes are not calibrated fluxes or
modern photometric magnitudes.

An appearance report can also be a source group with color, visibility or
relative-brightness context and no numerical quantity. SQLite retains these
groups and their contexts. The quantity CSV does not manufacture a magnitude
for them.

Source catalog row identities such as “Aries catalog entry 1” identify the
constellation and printed order within that edition. They are not historical
printed star numbers or modern stellar identifications. The entry context
retains the original descriptor, magnitude notation, direction letter and source
marks. A catalog's reference year is a calculation epoch, not an observing
date for every entry.

`least_component_unit` records the last explicitly stated component, rather than
an inferred error bar. `magnitude_degrees` supplies an exact angular conversion
where appropriate. `signed_magnitude` is available only when the hemisphere is
established; an unsigned declination is not automatically northern.

Named zodiac signs retain their within-sign angle and a separate
`zodiac_longitude_degrees`. A sexagena contains 60 degrees; a zodiac sign contains
30. `source_longitude_origin` distinguishes the first star of Aries from a source
equinox. `first_point_of_Aries_as_stated` preserves the source's literal wording
without identifying it with modern tropical zero or the first star of Aries.
None of these conversions establishes a modern coordinate frame.

## Source relationships and interpretation

`source_component_label` preserves pinnule and other component labels. The label
`both pinnules` qualifies one stated quantity; it does not duplicate its value.
Likewise, a `bis` note can report a separation twice while printing its numerical
value once. Its repeat count qualifies that record; it does not create another
numeric assertion, event or observing time.
`Sun` identifies a solar observation; it remains distinct from the historical
calculation subjects `mean Sun` and `simple Sun`. A solar observation made for a
Mars investigation retains its solar target.
`source_pair_position` records paired-row or paired-column order without
establishing simultaneity or a physical limb identity.

`argument_name=parallax_longitude_side_as_stated` preserves the lunar
calculation's “side of longitude” in its printed angular units. The name does
not identify a modern geometrical formula. Moon-center reductions retain a
different subject from eastern-limb separations.
A shared event group does not establish statistical independence. A group’s
`clock_assertion_id` and `epoch_assertion_id` refer to different kinds of time.
Unstated clocks and common epochs remain null.
A calculation continued on another page can link to the original epoch and input
quantity IDs. Such a link does not duplicate the earlier quantity or create a
new observation. The source relationship must be established independently of
numerical agreement.
An adjacent calculation epoch does not supply an epoch for a separate stellar
result or an alternative method. Those relationships can remain unresolved.
Coordinate-state labels preserve the source’s column definitions. An absent
`source_coordinate_state` means that label has not been established in the
export; it does not mean the value is raw or uncorrected. Existing coordinate
records still require review of their correction history before further reduction.
`free_of_refraction` does not assert that parallax has also been removed. A later
parallax subtraction can lead to a separately labeled `true` coordinate.
`apparent` preserves the source's apparent-position label independently of
`refracted`. It does not identify which corrections have already been applied.
`afternoon` and `pomerid.` preserve an `after_noon` date-part claim without adding
twelve hours to a calculation epoch or accepting an absolute timestamp.
`source_parameter_kind=longitude_of_greatest_latitude` identifies a model
parameter rather than Mars's position. A named zodiac sign on that parameter
does not turn it into an observed longitude or an attributed prediction.
`zodiac_sign_inherited_from_id` links a longitude without a repeated glyph to
the earlier explicitly labeled value in its reviewed column, retaining the same
subject, role, model and parameter kind. A linked printed correction or editorial
variant can also inherit the sign from its original earlier in the same row;
the origin link and `variant_of_id` must identify that same original. Source
expressions remain unchanged; separate models cannot supply each other's sign
and inherited origins cannot form chains.
`source_reduction_method` distinguishes comparison directions, angular distances,
meridian altitude, weighted latitude combination, parallax subtraction and adoption.
Its reference list identifies source comparison objects for the first two methods;
other methods have an empty list. A Jupiter longitude obtained from Mars remains
a Jupiter coordinate, with Mars retained as a reduction reference.

An adopted right ascension can explicitly favor one comparison route. The
`source_adoption_preference` field preserves that named object separately from
the coordinate origin and the reduction-reference list. It supplies neither an
averaging formula nor a weight; the adoption algorithm can remain unstated.
When the source favors several routes, `source_adoption_preferences` retains
their names without assigning ranks or weights.
Right ascensions can likewise retain their comparison-star routes through these
fields. A star used to calculate a right ascension does not become that
coordinate's origin.
Attached note numbers are citation metadata, including a note placed before a
zodiac glyph; they do not enter the normalized angle or remove its sign.

`model_name` attributes historical predictions to Copernicus, Tycho Brahe, the Alphonsine or
Prutenic tables, or named ephemerides such as those of Stadius, Carelli, Magini,
Scala and Origanus. Ephemeris names
identify the cited tables; they do not establish a physical cosmology. These are source-published calculations, not outputs of a
newly implemented model. One written quantity can apply to several bodies: it
retains one identity and a primary subject, with the shared body scope in linked
source contexts. It must not be multiplied into independent observations.
Stadius attributions also cover quoted solar and lunar-node longitudes and
daily motions. The lunar node is a calculated orbital point. A date supplied
as an ephemeris argument is a `calculation_target`; this differs from a
model-predicted date of an ingress or station. Editorial date and motion
alternatives remain separate and unapplied.
`editorial_component_units` identifies components supplied
by an editor. `editorial_reference_alternative` retains a disputed reference point.
`observing_site` and `observer_names` retain supported historical attribution.
An explicit Uraniborg/Copenhagen distinction can retain a site without supplying
an observer's name. Site attribution does not establish a shared observing instant.
The `small_globe` and `largest_globe` reduction methods distinguish source-derived
Mars coordinates from instrument readings and historical table predictions.
A Mars declination with method `meridian_altitude` and role `reduction` preserves
the source's stated method without assigning a hemisphere, calculation epoch,
observatory latitude or particular instrument when those remain unspecified.
Predictions can belong to Mars or to a comparison planet such as Jupiter. Their
actual subjects and calculation epochs remain explicit; a comparison involving
Mars does not make every resulting coordinate a Mars observation.

Named Stadius/Carelli predictions can retain `longitude_difference` and
`latitude_difference` between two planetary endpoints. The source's unsigned
components stay separate. On X p.6, the May 30 values 10′ and 44′ do not supply
an observed great-circle separation or a direction for either component.

A recorded `latitude_difference` can retain the source's latitude qualification
without choosing a coordinate frame. The Mars–Aldebaran entry on X p.46 says
“in latitude”; its frame and measurement or reduction method remain unestablished.
It is neither an absolute latitude of Mars nor an ordinary great-circle separation.

`geometry_label`, `geometry_column` and `argument_name` identify source calculation
quantities. A diagram label alone does not supply a celestial endpoint or formula.
`Moon calculation` identifies lunar geometry parameters whose vertices have no
established body assignments. It does not identify an observed target.
`Moon lower limb` identifies an explicitly labeled lunar edge, separately from
the lower horn and from an unspecified Moon endpoint in a separation.
For the Jupiter distance instruction on XII p.432,
`source_correction_application=applied_to_following_distances` and
`source_correction_operation=add` preserve the reported application and direction.
For the instrumental note on XIII p.176,
`source_correction_application=not_yet_added_as_stated` retains the explicitly
unapplied 2′30″ addition to the associated Jupiter distances. The source calls
this an instrumental parallax; it supplies no celestial Mars-parallax measurement
or permission to adjust unrelated Mars readings.
For the Radius shortfall instruction on XIII p.111,
`source_correction_application=instruction_not_reported_applied` preserves the
required addition separately from any report that it was carried out. The stated
4′ normalizes to 240 arcseconds; affected records and application remain
unestablished. The recorded distances stay unchanged.

`source_correction_application=conditional_not_reported_applied` preserves a
counterfactual or conditional globe-consistency trial. Its positive
`separation_correction` amount and `source_correction_operation=add` belong to
the specified target set. A `source_upper_bound` flag makes the amount a limit
rather than a chosen offset. No corrected copies or uncertainty estimates are
created from the claim that the construction would coincide.

`instrument_altitude_bias` records a reported instrumental altitude error,
separately from a planetary altitude or celestial parallax. On XIII p.219,
`source_bias_direction=high` and
`source_correction_application=corrected_where_found_individual_application_unestablished`
preserve the 2′ bias and the statement that corrections were made wherever
entries could be found. Its magnitude is 120 arcseconds. The record has no
per-reading correction operation or observing group. The scope names the Benátky
sextant and revolving quadrant from August 28, with an unstated starting year;
neither original uncorrected values nor individual application are established.

`instrument_separation_bias` separately preserves the sextant shortfall reported
on XIII p.220. Its 1½′ magnitude is 90 arcseconds, with
`source_bias_direction=low` and
`source_correction_application=individual_application_unestablished`.
The two measured/expected stellar pairs retain their own values. This record
does not impose identical differences on those pairs or add 90 arcseconds to
planetary distances. It is neither a celestial parallax nor an observing event.
An explicit sextant label can accompany a recorded angular separation or stellar
calibration; it is not assigned to a historical expected value.

For the Augsburg instrument table on X pp.19–20,
`instrument_separation_bias` retains `source_bias_direction=high` with
`source_correction_operation=subtract`, or a reported shortfall as `low` with
`add`. Its application remains `individual_application_unestablished`; the
instruction does not modify any catalog reading. The instrument is not
identified as a sextant or Radius. Each angular table argument links to its
reported correction through a derivation record. Worked observed/globe examples
and the proportional table anchor remain distinct source claims.

A Mars `declination_correction` can separately retain the operation `add` or `subtract`
without the following-distances application field. It records the historical
instruction, not an adjustment executed on catalog readings or a recovered
original declination. `source_approximate` preserves a qualified amount such as
“about 2′”; its exact rational normalization describes that nominal amount,
not an exact physical correction or an uncertainty interval.

`declination_difference` can preserve a historical stellar shortfall. The reviewed
combination `source_difference_relation=deficit` and
`source_difference_reference=stellar_reference_declination_unstated` records the
positive angular amount while leaving the comparison declination unknown. It is
separate from a declination coordinate, hemisphere and applied correction.
They accompany a historical correction amount, not the preceding approximate
error estimate. Exporting these labels performs no correction and does not extend
the instruction to Mars or establish a global validity interval.
`source_difference_relation=excess` or `deficit`, together with
`source_difference_reference=limited_position_as_stated`, records the historical
author's coordinate comparison on XII p.431. The difference is an unsigned angular
amount. These labels supply neither a north/south direction nor a numerical
reference coordinate, and they do not attribute the comparison to another model.
`horizon_inclination` records the angle of the line joining its two named bodies
relative to the horizon. Its angular magnitude and approximation flag remain
separate; this is not the angular separation of the bodies or a celestial position.
`comparison_relation` and `lower_bound_inclusive` retain a stated comparison where
supported. These fields do not define an observational confidence interval.
Angular model comparisons use `coordinate_difference` or
`latitude_change_over_source_interval`. They preserve unsigned magnitudes and
source approximations without requiring the bound used for a timing comparison.
A latitude change over an interval is not a daily-motion rate.
Explicit plus/minus rows qualify their own model-difference cells. Their
`source_comparison_sign` does not turn a difference into a north/south coordinate.

An `inferred_time` is a historical reduction, distinct from a recorded clock or a
separately stated calculation epoch. Its `time_inference_basis` identifies the
source's method category without implementing that calculation. It cannot supply
an event's selected observing clock. A blank inferred-time cell remains absent.

`source_future_meridian_reduction` marks adopted separations that the author
instructs the reader to reduce later to meridian-transit times. It does not mean
that a correction has already been applied or that a transit time is known.

`source_quality_note_later_hand` identifies a later-hand attribution for a
calibration's quality note. It does not identify a new observer or attribute the
measurement itself to that hand. Its scope stays with the qualified calibration.

A sequence-scoped clock correction is an amount, distinct from a full corrected
clock value. Its `clock_runs_fast` and `clock_correction_not_applied` flags retain
the author's instruction without applying it to raw readings or later sessions.
Literal checks can compare individual raw/corrected pairs with the stated rule;
agreement does not establish clock accuracy, and disagreement supplies no
automatic emendation.

`correction_ratio_kind=separation_to_declination_refraction` identifies a historical
rule relating two correction methods. A stated half is exactly `1/2`; the rule is
not an empirical ratio between corrections evaluated at different altitudes.
`correction_ratio_kind=jupiter_to_mean_solar_parallax` identifies the published
one-third relation between Jupiter’s parallax and the Sun’s mean parallax. Its
reference is `Sun`; “mean” qualifies the parallax, rather than identifying a
fictitious mean-Sun coordinate. The ratio is dimensionless and is not itself an
applied correction or an additional numerical solar-parallax observation.

`correction_ratio_kind=copernican_prosthaphaeresis_fraction` preserves a source
instruction to add a fractional part of Copernicus's prosthaphaeresis. The phrase
“14th part” is represented as exactly `1/14`, separately from the angular
prosthaphaeresis. `model_name=Copernicus` identifies this historical input or
correction, without classifying it as an observed position or a modern prediction.
Mars calculation arguments can distinguish `simple_planetary_longitude`,
`apogee_longitude`, `prosthaphaeresis` and `commutation_correction`; their angular
units and source roles remain explicit. An unlabeled intermediate need not
receive an inferred argument name.

`source_fraction` preserves an exact fraction in its stated native reference,
including cases whose reference whole remains unstated. Its normalized unit is `source_fraction`, with
`least_component_unit=fraction`; it is neither an angle nor a dimensionless
multiplicative correction. For `source_fraction_kind=latitude_reconciliation`,
`comparison_relation` retains `greater_than_computed` or `less_than_computed`.
No corrected coordinate or numerical uncertainty follows from that statement.

Native visual comparisons use `source_fraction_kind` values `visual_palm`,
`visual_digit_breadth`, `visual_lunar_diameter`,
`visual_lunar_semidiameter`, `visual_lunar_reference_unstated` and
`visual_reference_separation`. A source that says only “one moon” retains
the unspecified lunar reference rather than being assigned a diameter. The exact number counts the stated reference
unit; it supplies no degree value, signed angle or modern angular calibration.
The subject and reference identify the compared objects or source-described line;
the linked context identifies the comparison geometry and reference separation.

An unresolved native number such as `[?]` or `[?]/[?]` retains its
`source_fraction_kind` and `source_fraction` unit, with
`source_notation_unresolved`, status `unsupported`, and no scalar or angular
value. This records which reference scale the source used without choosing the
missing numeral or treating the reading as zero.

`comparison_relation=separation_as_stated` preserves the source estimate.
`greater_than_reference_fraction` and `less_than_reference_fraction` retain
strict bounds; `at_least_reference_fraction` and `at_most_reference_fraction`
retain inclusive bounds. Bounds also carry the corresponding lower/upper-bound
flag. Visual-estimate and unresolved-geometry flags remain attached. A hypothetical
numerical illustration has role `historical_input` and
`not_an_additional_raw_reading`; it is not another observation. For example,
“four digits or a little beyond” preserves a lower bound of four native digits,
while “not beyond the breadth of a digit” preserves an inclusive upper bound of
one. Neither becomes an angle by assuming a hand-to-eye distance.

For `source_fraction_kind=calibration_difference_unit_unstated`, the relation
`less_than_both_as_stated` preserves the fraction in a stellar calibration
comparison whose reference unit is unstated. On X p.29, the written ⅙ normalizes
to `1/6` in `source_fraction` units, with no angular magnitude. It supplies
neither a ten-arcminute correction nor a fractional multiplier to apply to the
recorded separations.

For `source_fraction_kind=comparative_line_proximity`, `comparison_relation`
retains `nearer_by_fraction_as_stated`. This is a recorded visual comparison,
with `source_visual_estimate` and `geometry_interpretation_unestablished`.
The literal fraction can normalize to `1/3` while its geometric denominator
remains unknown. Its degree value stays null; no calibrated distance ratio or
along-arc interpolation formula is supplied.

For `source_fraction_kind=lunar_diameter`, the relation
`limb_separation_as_stated` preserves the February 22 gap on X p.42 from
`Moon lower horn` to `Mars`. Its one-sixth threshold remains a native
`source_fraction`, with visual-estimate, upper-bound and unresolved-geometry
flags. It is not a center-to-center separation. No angular value follows
without a separately established lunar diameter and geometry for that occasion.

Lunar comparisons distinguish `lunar_illuminated_portion`, `lunar_semidiameter`
and `lunar_reference_unstated`. These retain the source's reference whole, or its
absence, without substituting a modern lunar diameter. A latitude offset relative
to Aldebaran is not an absolute lunar latitude. `greater_than_reference_fraction`
retains a lower bound, rather than an equality. A source lunar distance labeled
`source_coordinate_state=free_of_parallax` remains a reduction; its original raw
value and the nature or amount of the correction may be unknown.

`argument_name=latitude_argument` distinguishes an argument used to calculate
latitude from the latitude itself. `latitude_argument_correction` identifies an
angular adjustment to that argument, and `apogee_to_latitude_maximum` preserves
the stated longitude offset between the apogee and the place of greatest
latitude. An explanatory editorial quantity links to its marked source value.

The date label `following_midnight`, with
`day_number_basis=completed_time_uninterpreted`, preserves “the 10th completed,
at the following midnight” without changing the named day to the 11th. A
midnight label alone supplies no numerical clock reading or accepted timestamp.

An explicit `source_angular_count_unit=sign_count` represents a count of 30°
signs in a calculation argument, distinct from sexagenae of 60° and from a
position within a named zodiac sign. Six signs therefore convert to 180°;
six sexagenae convert to 360°. No modern coordinate origin follows from either.

The lunar calculation on X p.25 establishes its 60° count through the stated
doubling relationship: twice 1 count 59°35′41″ equals 3 counts 59°11′22″.
This local evidence identifies the count unit without substituting a modern
ephemeris. The same table's proportional minutes remain dimensionless, and its
short correction rows retain angular minutes and seconds rather than an
automatic leading degree component.

Apparent and equal representations of one historical time remain separate
assertions. An explicit shared hour can bind separately printed minute values
through source fragments on the same line. Preserve a difference between the
printed result and the exact stated time correction; an unstated rounding rule
does not authorize changing either value.

For angular expressions whose component units or omitted leading components
remain unresolved, `normalized.status=unsupported` preserves numeric
`source_components` in printed order and
`normalization_issue=angular_component_units_unresolved`. The normalized
magnitude, degree value and least component unit remain null. The `arcsecond`
unit names the eventual conversion target; it does not assign arcseconds to
those literal components or establish a converted angle.

`source_scalar` preserves a complete native source number without converting it
to an angular or physical unit. Its unit is `source_scalar`, its least component unit is
`scalar`, and its degree value remains null. Exact normalization here means an
exact rational transcription of that scalar, not an angular conversion or a
physical interpretation. `source_parameter_kind` distinguishes
`eccentricity_as_stated`, `tabular_argument_unit_unstated`,
`unresolved_instruction_count`, `comparison_multiplier`, `unlabelled_table_value`
and `source_record_count`. A stated record count is the author's claim about
the material being discussed, not an independent-observation total. A bare eccentricity
of 12 or 9½ does not by itself specify a denominator, a length or the eccentricity
of a modern ellipse.

Instrument construction uses `instrument_dimension_cubits`,
`instrument_dimension_feet` and `instrument_dimension_digits` for lengths in
the source's cubits, feet and finger/digit breadths. `instrument_dimension_ratio`
retains a stated length ratio, such as a brace position at approximately one
third of a ruler's length. `instrument_component_count` records counts of parts,
`instrument_scale_divisions` for subdivision counts, and `instrument_scale_value`
for numbers engraved on the scale. These are positive native scalars with the
subject `instrument` and role `historical_input`, without an observing-event
association. Counts and scale labels are integers; native lengths and length
ratios may be fractional.
`instrument_circle_count` also permits an explicitly stated fractional circle,
such as one-and-a-half circles, without converting it to an angular span.
`instrument_scale_digit_count` counts the stated figures of a numerical scale
or canon, rather than supplying its radius or number of divisions.
The source context identifies the component or scale. No modern cubit length,
angle, or measured celestial position is inferred.
An illustrative subdivision into thousandths remains an example scale; it does
not establish the dimensions of a particular instrument or supply a missing
correction table. Source approximations and units inherited within a construction
sentence remain explicit in that sentence's review context.
An unread scale label such as `[?]00` retains `source_notation_unresolved` and
has no scalar value; neighbouring graduations do not supply its missing digit.

`calculated_chord` retains native chord lengths used in tables and calculations,
with their stated radius in `source_scalar_scale`. Roles distinguish tabular inputs,
intermediates and reductions from recorded instrument chords. The scalar is not an
angle. A printed value exceeding twice the stated radius is preserved only with
`source_quality_note_present` and its source qualification; it is not silently
replaced by a plausible value. For example, Schöner's solar table prints 217588
on a radius-100000 scale.

Trigonometric calculations also use `trigonometric_radius`, `scaled_sine` and
`arithmetic_intermediate`. With a stated whole sine of 100000, a native sine
value of 97127 stays 97127 and retains `source_scalar_scale=100000`; it does not
become 97127 arcseconds. Products and quotients keep their stated integers without
an assumed common scale power or an invented rounding convention.

`sine_increment_per_source_second` preserves native interpolation increments.
In Origanus's sine table the stated whole sine is 10000000, and the instructions
describe each paired field as whole units followed by tenths, per single source
second. With the explicit interpretation
`source_unit_notation=paired_decimal_tenths`, `48 5` and `48.5` therefore become
the exact native scalar `97/2`. Observed separators such as `48.,2` and `10: 5`
are accepted only under this declared notation. These values are neither
arcseconds nor normalized sines. The stated radius remains in
`source_scalar_scale`; table context preserves the degree and minute arguments.
Queried fields and packed increments without an established division between
whole units and tenths retain their complete literals with
`source_notation_unresolved` and no scalar. Editorial alternatives remain
separate and unapplied. Blank or dash cells do not create zero-valued records.

`scaled_tangent` likewise preserves a native tangent with its stated radius in
`source_scalar_scale`; unlike a sine, it may exceed that radius. Explicit editorial
alternatives to calculation scalars retain their own `editorial_variant` record,
link to the printed value through `variant_of_id`, and carry
`alternative_suggestion_not_applied`. They do not replace the printed numeral.

`model_length` retains geometric lengths in their stated model scale. In the
Copernican distance construction on X pp.201–203, AD is 10000: a side of 10997
remains 10997 with `source_scalar_scale=10000`, even though it exceeds the
reference length. These lengths are distinct from Earth-radius quantities.
The source's conversion to Earth radii is retained as a separate historical
reduction; no modern physical length or observational distance is inferred.
An explicitly queried model length can retain its known reference scale and
literal with empty components, `source_notation_unresolved` and no magnitude.
Knowledge of the scale does not resolve the numeral.

An Earth-radius distance written only in sixtieths retains only its
`semidiameter_minute` component: 17 sixtieths normalizes to 17/60 Earth radii.
An absent whole component is not inserted into the recorded components. This
native length is distinct from an angular arcminute.

`sine_value_scale_unstated` retains an input labeled as a sine in a historical
stellar-calibration or shared planetary table as a native scalar when its
reference scale is unestablished. The subject is `stellar calibration
calculation` or `planetary motion calculation`. The source label alone does not
establish a modern trigonometric value, a logarithmic encoding or a denominator.
No angular conversion is supplied; `source_scalar_scale` remains unset.

`angular_daily_motion` and `angular_hourly_motion` retain different normalized
units: `arcsecond_per_source_day` and `arcsecond_per_source_hour`. Neither is a
coordinate or an accepted observing interval. A source's stated daily motion
does not establish an exactly measured 24-hour baseline.

`source_parameter_kind=visual_coefficient_as_stated` instead identifies a
literal positive coefficient in a recorded Mars comparison, with role
`recorded_reading`, `source_visual_estimate` and
`geometry_interpretation_unestablished`. For example, half a diameter retains
`1/2` and twice as far retains `2`, without choosing a diameter's body, distance
baseline or interpolation formula. The full comparison can contain an additional
qualifier such as and a little more. The scalar is only the literal coefficient;
it is neither the complete measured separation nor a calibrated angle. Original
wording, qualifiers and unresolved references remain separate source context.

For a historical apogee trial, `source_adjustment_sign=plus` or `minus` preserves
the direction of the proposed angular adjustment. It does not set a latitude
hemisphere or change the unsigned normalized magnitude. A
`greatest_southern_latitude` parameter is explicitly southern and hypothetical;
it remains distinct from a recorded planetary coordinate.

An eccentricity explicitly stated as “12 of 60” or “9½ of 60” uses
`source_scale_ratio` with `source_parameter_kind=eccentricity_as_stated`.
The exact ratios are `1/5` and `19/120`; both printed operands remain available.
This is a relative historical model scale, distinct from a modern elliptical
eccentricity or an absolute distance. Common parameter definitions can be
undated while the calculations that use them have separate year claims.

`sum_modulo_360_degrees` checks a source's explicitly reviewed circular
addition. It requires angular inputs and compares their sum modulo 360° with
the printed result. Ordinary sums and differences retain their own arithmetic.
`difference_modulo_360_degrees` checks ordered subtraction of two angular inputs
with the result expressed modulo 360°. It preserves a printed right ascension
near 360° when the ordinary subtraction is negative; it does not change the
source values or convert observing clocks into angles.
Additional validation can reference an already catalogued output by its existing
`output_id`. This adds a check without duplicating a quantity or rewriting the
earlier source review. An earlier uncomputed lineage record and a later numerical
check can therefore share an output while retaining their different input sets.
Source counts can retain uncarried degree components, such as `10 30 13 31`,
without rewriting the recorded components.

`source_zodiac_candidate` and `source_zodiac_identification_uncertain` preserve a
tentative sign identification without an accepted absolute zodiac longitude.
Known degree/minute/second components remain available for the Sun, Moon and
classical planets; the candidate does not supply `zodiac_sign` or a
`zodiac_longitude_degrees` value. In particular, the queried solar signs in the
first two paired Venus collations do not become Pisces positions through their
dates or agreement with a predicted place.
`source_zodiac_candidates` preserves two or more alternative signs explicitly
present in a single source expression. For example, `13° 9′ 19″ ⟦♍/♏⟧`
retains Virgo and Scorpio as alternatives alongside the exact within-sign
components. Neither candidate establishes an absolute longitude; another
coordinate or a modern prediction cannot choose between them during ingestion.

Written degree, hour, minute and second units are bound to their numerical
components as well as symbolic marks. Prefix notation such as `hour 7 minute 12`
and mixed notation such as `81° 31′ 3⅚ seconds` retain their stated unit sequence.
The selected time or angular interpretation distinguishes bare “seconds”; the
explicit word “arcseconds” cannot become seconds of time or a native sexagesimal
length component. An exact conversion continues to describe arithmetic under the reviewed
interpretation, rather than observational accuracy.

A dot immediately following an explicit angular unit can separate components:
`22°.43′.50″` retains the literal and converts as 22 degrees, 43 arcminutes
and 50 arcseconds. It is not decimal-degree notation. Decimal numerals and
unfinished component sequences remain unsupported by this sexagesimal parser;
punctuation is not removed indiscriminately.

Native sexagesimal minutes, seconds and thirds of a day retain their day-based
scale. For example, “1½ seconds of a day” is not 1½ ordinary clock seconds.
`source_coordinate_state=parallax_adjustment_pending_as_stated` marks an input
whose source calls for a parallax adjustment but supplies no amount. The value
remains unchanged; no zero correction or corrected position is inferred.

`source_coordinate_state=parallax_possibly_insufficient_as_stated` preserves a
source's tentative claim that too little parallax has already been added.
It supplies no amount. `source_instrument_label=Radius` with
`source_instrument_qualifier=only` retains the instrument attribution on the
qualified historical summary, without asserting its dimensions or accuracy.
The same `Radius` label can identify an explicitly attributed measured angular
separation. It is not inherited by adjacent readings that omit the instrument.
`calculation_angle` with subject `equator on meridian` preserves a stated
meridian-equator calibration angle. It is neither a Mars coordinate nor a
numerical measurement of the accompanying stellar plumb-line alignment.

Source residual signs compare the printed latitude magnitudes, independently
of their northern or southern hemispheres. An earlier residual form can be an
`editorial_variant` linked to its marked comparison cell. A printed “plus” with
no number has incomplete normalization and a null magnitude; it does not mean
zero. Reported original minute components likewise do not reconstruct a full
coordinate by silently borrowing its other components.

`month_part=end` preserves “at the end of October” or another month without
supplying its last calendar day. It requires a month and an unset day and is
distinct from an explicit `last_day_of_month` rule. A source-date record with
`source_date_role=editorial_date_comment` and
`source_date_witness=editorial_comment` preserves an editor's temporal statement.
Such a comment does not automatically replace or become an epoch for a source
parameter.

`source_parameter_kind=northern_node_longitude` identifies an adopted node
longitude. `argument_name=node_before_apogee_distance` identifies the separate
angular distance by which that node precedes the apogee. Where the printed
leading sign count is editorial, `source_editorial_component_units=['sign_count']`
preserves that attribution within the full printed argument. An adopted northern
maximum can carry `parallax_included_as_stated` without supplying an original
uncorrected latitude or a numerical parallax correction.
`correction_ratio_kind=latitude_difference_weight` preserves a dimensionless
weight applied to a difference of latitudes. Its reference body is null; the
participating coordinates are identified through derivation links.

`source_unit_inherited` marks the two later distance entries whose Earth-radius
unit comes from the shared subtraction table. The unit is not printed again on
those rows. `source_horizontal_parallax` distinguishes the source’s horizon value
from the altitude-specific value and its separate approximate adoption. These
are theoretical source quantities, not observational detections.
`source_parallax_context=right_ascension_collection` and
`source_parallax_operation=add` preserve an explicitly additive parallax
instruction beside a right-ascension collection. These paired fields describe
the source context and operation, rather than a measured distance or a correction
to every coordinate. The amount remains unsigned; its derivation links identify
the adopted result. An unstated combined value before correction remains absent.
`source_upper_bound` identifies a stated maximum. A claim of at most half a minute
is 30 seconds with that qualification, distinct from a separate 28-second claim.
`clock_correction_not_applied` means the correction has not been added to readings.
Combined refraction/parallax adjustments are not isolated parallax measurements.
`source_joint_motion_unallocated` marks a source daily-motion term involving both
a planet and the Sun. Its `arcsecond_per_source_day` value is not assigned to
each body's individual rate. `simple Sun` remains a separate source label from
`mean Sun` and `Sun`. An angular motion over a stated interval retains angular
units, distinct from both the daily term and the elapsed time.
An assumed parallax in a Mercury reduction remains a historical input attributed
to Mercury. Alternative calculation versions have separate inputs, epochs and
correction paths; their adjustments must not be composed into one correction.

`separation_difference` is a change in the angular separation between its subject
and reference object, normalized in arcseconds. It is distinct from a complete
pointing, a separation correction and a rate per source day. Approximate wording
retains its flag; two named-day claims do not establish an elapsed 24-hour interval.
It can also retain a source's stated difference between two attributed versions
of a separation. Such a record uses `role=historical_comparison`, two ordered
`comparison_sources`, and `comparison_relation=second_minus_first_as_stated`.
The exact magnitude remains unsigned, with the printed `source_comparison_sign`
and `comparison_label_original` retained separately. A discrepancy between that
statement and subtraction of the two inputs is preserved, not repaired. These
comparison records have no observing-event association and do not establish
independent observations or an accuracy assessment.

An unsigned DMS difference instead uses
`comparison_relation=unsigned_difference_as_stated` and
`source_comparison_sign=not_stated`, with no `comparison_label_original`.
Every written component and unit remains bound to the complete expression;
mixed fractions remain exact. This records the source's difference magnitude,
without deriving a sign or replacing it with a subtraction of the inputs.

`model_date_relation=station_near_date` records a model's station near a named
date, with its attribution. It does not establish an observed station time or
an exact predicted instant.
`model_date_relation=station_on_named_day` instead preserves a prediction that
the body is stationary on the named day. It supplies neither an exact instant
nor an observed zero rate of motion.

`orbital_longitude` with `source_coordinate_frame=own_orbit_as_stated` retains
the source's longitude in its own orbit. It is separate from
`ecliptic_longitude`. Its `zodiac_longitude_degrees` only flattens the printed
sign and within-sign angle into nominal degrees in that source frame; it does
not convert the coordinate to the ecliptic or establish a heliocentric origin.
A `true` state preserves an explicit source label. Lunar own-orbit values can
retain the frame without an unstated truth label or a borrowed calculation epoch.

## Dates and clocks

Date records retain `year`, `month`, `day`, `daypart`, `calendar` and `day_origin`
where supported. `component_status` distinguishes complete from partial named
components. `calendar_validation` describes validation status; it does not impose
a proleptic Gregorian calendar. `day_number_basis` can retain an unresolved
completed-time convention. `day_rule=last_day_of_month` preserves a relative heading
with a null numbered day and no chosen calendar; it does not calculate February 29.
`day_rule=following_named_day` similarly retains `anchor_day` and a null numbered
day. It preserves “the following day” separately from the named observation,
without inventing a calendar conversion or absolute timestamp.
Multiple calendar labels remain separate source claims.
`source_date_role=editorial_date_comment` and
`source_date_witness=editorial_comment` retain an editor's proposed date
separately from the original heading. On X p.42, the original February 22
claim has a null year; the associated 1576 claim records Dreyer's inference
from the Moon–Mars conjunction. Neither is an accepted absolute date.
Optional `source_date_role` distinguishes an `observation_label` from a
`calculation_target`. Several observations may be reduced to one common target
date; their original labels remain separate. An absent role is unspecified.
`planned_observation_label` identifies the date context of an instruction or
observing plan. It does not establish that an observation took place or supply
an accepted observing date. Such a context can exist without numeric readings.
`observation_label_variant` retains an alternative date reported for the same
readings. `source_date_witness=printed_heading` identifies the heading, while
`manuscript_reported_by_editor` identifies a manuscript variant transmitted by an
editorial note. Linked alternatives do not duplicate the measurements or choose
an accepted date. A daypart supplied by the heading need not occur in the variant.
The role `model_prediction` instead retains an attributed historical date claim.
Its `subject`, `model_name` and `model_date_relation` identify the body, model and
claim: `retrograde_motion_begins`, `direct_motion_until_date`, `station_near_date`,
`station_on_named_day`, `station_before_named_day` or `opposition_on_named_day`.
These remain separate from observed station or opposition dates. “Direct until” does not establish an
exact station time or a boundary-inclusivity rule, and calendar validation remains
unperformed.
Named Stadius station predictions retain the same model-date role. A nearby
author's inferred stationary date or range remains a separate claim with its
own qualifications; it cannot become the model date or an observing clock.
An attributed Stadius `historical_comparison` can also retain a reported
`longitude_difference`, `comparison_relation=coordinate_difference` and its
source `plus` or `minus` sign. The comparison's date contexts remain explicit;
the type does not assert that the compared station positions share an epoch.
`accepted_observing_date` and `absolute_timestamp` are currently null.

`source_nominal_date_rejected` marks a reading or clock whose date of placement
is explicitly rejected by the source or its editor. The rejected label, witness
and scope remain supporting context; the label does not enter that record's
`source_date_claim_ids`. An unknown replacement date remains unknown. On X p.46,
the marked note rejects 20 March for two distances without supplying another day.

`source_value_restored_from_witness`, with role `editorial_addition`, preserves
a supplied number from a separately named witness. On X p.48, the bracketed
9°11′ comes from Bartholinus where the codex has a lacuna. The primary-witness
gap remains context with no invented numeric value; the supplied angle is
counted once and is marked `not_an_additional_raw_reading`.

`Moon nearer limb` preserves the lunar edge explicitly named on X p.61.
Its 11°40′ separation from Mars remains a limb distance. The same report's
29′ Radius and 25′ Sextant readings are separate `angular_diameter` values
for the Moon, each retaining its instrument. They have no assigned point clock;
only the Mars comparison carries its own 1h30 label. The Greek qualifier
`ἐν πλάτει` is retained without an invented numerical tolerance. Neither diameter
is averaged or silently used to convert the separation to the Moon's center.

The later 32′ diameter has its own 2h52 clock and a joint source instrument
label, `sextant and Radius`. It is one stated value, not two independent
measurements. The following-noon clock error is a relative calibration epoch;
it does not acquire the report's named date or correct earlier Mars readings.

On X pp.61–64, the recorded 26°45′ lunar-star distance, the marginal 27°4′ globe
value and the assumed 26°48′ remain distinct. The p.63 assumption at 1h45 and
the p.64 reduction to 1h30 preserve their different epoch roles. `vera` labels
only the first two lines of the lunar input brace; seen longitude and latitude
remain separate inputs. The eight-minute reduction instruction retains its
unresolved physical unit. Alternative Mars longitudes, adopted positions and
named table predictions are historical calculations, not additional raw readings.

On X pp.64–65, the October 23 observing-clock/altitude series precedes the
source's equatorial and ecliptic reductions. `Ex observatione` identifies a
derived position. Its half-minute values remain separate from the adjacent
integer-minute adoption. The local note expands `Merid.` and `M.` as southern
in the latitude column; this does not define `M.` throughout the books.
The parenthetical half minute beside one stellar altitude is a linked
`angle_component`, not a silently completed alternative altitude. The
following-noon clock claim carries `source_lower_bound`: 50 seconds is an
inclusive threshold, not an exact drift or an applied observing-clock correction.

The computed lunar parallax table on X p.63 distinguishes vertical parallax
in minutes/seconds from longitude and latitude corrections in degrees/minutes.
Its subtraction instruction applies to the last two columns. These are lunar
calculation inputs; they are not direct Mars parallax measurements. The 1h30
longitude correction reproduces the later seen lunar longitude exactly. Exact
latitude subtraction gives 14½′ beside the printed 14′ seen latitude. The 30″
arithmetic difference remains separate from the immutable source values; no
rounding rule or final-edition error is inferred. The rough lunar-position
table's unspecified hemispheres remain distinct from the separate, explicitly
northern mid-eclipse latitude.

The visual Saturn–Mars comparison on X p.71 is a `latitude_difference` with
an unspecified coordinate frame, not an absolute latitude or a great-circle
distance. On p.72, the twilight brace qualifies five angular comparisons;
only the first two carry point clocks. The instruction to correct those
readings supplies no numerical correction. The nearby book title's starting
year remains separate from local March date labels whose year is not explicit.

`source_lunar_semidiameter_to_add` retains an instruction to add the Moon's
semidiameter to a recorded distance. The catalog leaves the printed value
unchanged. The instruction's scope, missing correction amount and unspecified
lunar measurement endpoint remain context; no diameter is borrowed and no
center-to-center distance is manufactured.

A `recorded_clock` can retain `source_notation_unresolved` and
`absolute_time_unestablished` when its clock wording has not been converted.
It keeps the known `second_of_time` target unit, with null magnitude and
precision. This is an unresolved clock interpretation, distinct from a missing
printed figure. The half-of-ordinal-hour expressions on X p.45 remain literal
source statements; no fractional-hour scalar is chosen from their wording.

`source_day_relation=following_night` or `preceding_night` qualifies the source's
named day when its wording identifies the night following or preceding that
day. The named components remain unchanged; this field does not calculate a
new calendar date, day origin or absolute timestamp.

Clock readings, hour angles, elapsed intervals, meridian-time differences and
calculation epochs are distinct quantities. `time_reference` preserves an identified
origin or relation, such as time from noon, elapsed time from sunset or a difference
between site meridians. It does not convert the reading to UTC.
`time_reference=elapsed_before_sunrise` identifies a recorded duration.
Approximation is retained when the source states it. “Three or four hours”
retains both numerical alternatives and their
shared source context; it supplies neither a midpoint nor two observing times.
`time_reference=elapsed_before_twilight` preserves the source's distinct twilight
anchor. A stated hour normalizes to 3,600 seconds of elapsed time without
establishing a clock reading, a solar altitude or an absolute timestamp.
`time_reference=elapsed_before_meridian_transit` and
`time_reference=elapsed_after_meridian_transit` identify durations before or after
Mars's own transit, separately from any transit clock or meridian-altitude group.
`time_reference=elapsed_after_lunar_quadrature` preserves an approximate lunar
phase interval with the Moon as its subject. An approximate two days normalizes
to 172,800 seconds while retaining `source_approximate`; it does not time Mars.

`elapsed_after_prior_observations` retains an approximate duration after an
explicitly identified earlier Mars-reading group. Its
`source_time_anchor_event_id` links that group, separately from the duration's
own group. The reference cannot point to itself, a missing group or a group
with a conflicting reviewed date context. A retrospective interval without an
identified earlier group retains its numerical duration, approximation and
source relationship without this anchor field. It does not establish an earlier
named date or another observation group. `elapsed_after_stellar_meridian_transit`
instead retains the source's Hydra-transit reference, with `head of Hydra` as
the descriptive endpoint and no invented numerical transit clock.

`elapsed_after_acronychal_position` records an approximate historical phase
interval, such as the source's five days, with role `historical_input`. It is
not a new instrumental reading or an accepted opposition epoch. Named
preceding-night and following-night labels remain unchanged.
Source-corrected times retain their clock quantity with role `printed_correction`
and flag `source_clock_correction`. Where the original is stated, `variant_of_id`
links the corrected value to it. This is a complete corrected time, rather than
a numerical correction offset or an additional observing occasion. A source
group can retain its original clock while the linked correction remains available.
An unstated original stays absent; no subtraction or fixed offset fills it.
The clock's correction label does not make an adjacent declination corrected.
When a brace encloses multiple time/angle rows and an unnumbered correction mark,
`clock_association_unresolved` retains that ambiguity. A source group can keep
both recorded clock values and a null selected clock. No correction value or
preferred original/corrected assignment is supplied merely to fill the group.
`time_reference=source_midnight_label` preserves the reviewed source's explicit
identification of 12h with midnight. Its normalized value remains 43,200 seconds
of source time; it does not become civil 00h, establish a day boundary or date
conversion, or imply that the observation occurred at the calculation epoch.
`time_reference=source_after_midnight_label` preserves an explicitly stated
calculation time relative to midnight. A third of an hour becomes 1,200 seconds
of source time, with the named date retained. It does not establish a civil-date
increment, an observed transit or an absolute timestamp.
`source_completed_hour_uninterpreted` preserves a completed-hour statement on an
hour-valued calculation epoch. Its literal hour component is normalized without
choosing a modern hour origin, moving a date or accepting an observing timestamp.

## Derivations

`input_ids` and `output_id` identify the participating quantities. `operation`
states the represented relation. `computed_magnitude`, `unit` and
`arithmetic_agrees` describe supported arithmetic checks. An unspecified historical
procedure remains uncomputed. Literal subtraction alone cannot reconcile different
longitude origins, hemispheres or epochs.

`difference_modulo_360_in_zodiac_frame` checks an ordered subtraction after
including each named sign's origin, then reduces the result modulo 360°.
It retains `arithmetic_frame=zodiac_zero`. This can check a reported distance
against tabular longitudes without reconstructing a spherical separation or
altering a discrepant source result. On X p.5, Carelli's stated 18° distance
is retained alongside the 18°01′ longitude-difference check.

`zodiac_inheritance_kind=same_ephemeris_statement` identifies a sign explicitly
shared between successive bodies in a reviewed Stadius or Carelli statement.
The literal child value stays unchanged and links to the preceding sign-bearing
quantity through `zodiac_sign_inherited_from_id`. Model, source statement and
order must agree; this rule does not extend ordinary column inheritance to
unrelated bodies or tables.

A reviewed `source_coordinate_frame` context can state a zodiac sign once for
a bounded prose passage and its following table. Its value identifies the
subject, sign, exact sign-bearing `source_expression` and source-line scope.
Review assertions bind it with `zodiac_sign_basis_key`; the compiler checks the
literal glyph, subject, scope and absence of intervening headings. This also
handles a sign printed after prose alternatives without inventing table columns.
`zodiac_sign_basis_context_id` retains the public link to the source context
that establishes the sign. Private preparation keys are omitted. The link can
also qualify an unresolved numerical expression; it does not supply a scalar
where the normalization remains unresolved.

A sign declaration immediately following a table can instead use
`scope_basis=following_table_note` in that context. The reviewed scope must
contain contiguous table rows, the selected quantity must retain a physical
column, and only blank lines may separate the rows from the literal note.
This does not allow a later mention of a sign to establish an earlier prose
coordinate or cross an intervening section. The complete normalization still
retains both the within-sign value and the longitude from zodiac zero.

`source_component_order` records the literal order of explicitly reviewed
component units when prose reverses their usual order. For example, “40 above
one degree” states minutes before degrees. Both source tokens must bind exactly
to their declared components; normalization still uses degree and minute units.
This does not supply the missing degree component of a neighbouring fragment.

Named Stadius and Carelli latitude predictions retain `historical_prediction`
and their stated hemisphere, or an unsigned magnitude when no hemisphere is
given. They remain distinct from observing events and raw readings. An observed
northern latitude does not establish the hemisphere of adjacent model values.

An explicit named-sign boundary can normalize from words: “exactly at the
beginning of Virgo” gives a sign-relative magnitude of zero and a zodiac
longitude of 150°. The original expression and reviewed word-number mapping
remain preserved; this is a reported positional conclusion, not an invented
raw numeral. A neighbouring observing interval and a separate time attached to
that position retain different source roles. Interval endpoints can be
`annotated_time` bounds without a point `clock_assertion_id`.

An editorially disputed target can require a source context rather than a
change to the recorded number. The February 28 altitudes on X p.393 retain
Venus as the edition's target and `editorial_variant` as their role; the detached
note's codex-V Mars header and its affected rows remain linked context. These
are not accepted Mars altitudes. A witness-label dispute is distinct from a
translation error or a numerical correction.

`annotated_time` also preserves native time annotations whose role is uncertain,
and a table's separately labeled corresponding times. Its exact hour/minute
conversion does not establish a raw clock, corrected clock, hour angle or
absolute timestamp. The review context retains the source label, row association
and interpretation limits. A corresponding-time column and a computed stellar
transit used for calibration remain separate source records.

In a time quantity, `time_third`, `time_fourth` and `time_fifth` are respectively
1/60, 1/3,600 and 1/216,000 of a second of time. The corresponding printed marks
include `‴`, `⁗` (or `^iv^`) and `^v^`. The quantity's established dimension
distinguishes these from angular places and from subdivisions of a day. Exact
rational conversion preserves every place; it does not establish measurement
accuracy. Explicit day units, including `^d^`, cannot be relabelled as hours.

Sexagesimal subdivisions of a day use `day_minute` through `day_sixth`.
The fourth, fifth and sixth places are respectively 1/150, 1/9,000 and
1/540,000 of a second of time. Their scale comes from the stated day unit,
not the shape of the prime mark. A printed lunation expressed both in hours
and in fractions of a day retains both occurrences and their stated
relationship; normalization does not force the two expressions to agree.

`source_scalar` with `source_parameter_kind=source_year_count` retains a stated
number of historical years, including approximate intervals used in secular
motion calculations. The normalized value is a native count, not seconds or a
calendar year. No tropical, sidereal or 365¼-day year is assumed. The source
context retains the angular change or rate associated with that count.
Queried counts such as `28 [?]` and `312[fraction: ?]` preserve the complete
expression, the native count kind and an unresolved normalization. The known
digits do not become a partial scalar when another digit or fraction is unread.
Visibility durations reported for the new star or comets can use the same native
year and month counts. Their subjects identify calculation records; the
attribution, lunar-month qualification and upper or lower bounds remain in the
source context and flags. They do not establish an observing epoch.

The subject `calendar calculation` identifies native parameters used to date
ephemerides or interpret historical astronomical epochs. Its
`source_parameter_kind` distinguishes `source_year_count`, `source_month_count`,
`source_day_count`, `source_week_count` and `source_cycle_count`. Context identifies the era, year
origin, completed/current convention and whether a figure is an interval,
ordinal index, operand or stated result. These scalar counts do not imply a
fixed year or month length, an absolute timestamp, or an independently observed
event. A linked `editorial_variant` preserves a replacement separately from its
printed original; it does not apply that replacement. A complete stated
day/hour/minute duration remains a duration rather than several unrelated
calendar counts.

A queried native count retains `source_notation_unresolved`, empty components
and no scalar. For example, `2[numeral: ?]4` remains unresolved: its visible
digits are neither separate counts nor grounds for restoring a missing digit.

`source_month_count` likewise retains native month counts, including a fractional
month in an epoch-transfer interval. A three-year and 9⅓-month interval retains
both counts; no fixed month length or number of seconds is supplied.
`angular_yearly_motion` records the associated angle per source year as
`arcsecond_per_source_year`, with the source's approximate qualification retained.
These quantities remain separate from an observing clock or an absolute epoch.

`sum_modulo_360_in_zodiac_frame` explicitly checks a sum using zodiac-zero
longitudes, projecting a named-sign input or output through its separately stored
`zodiac_longitude_degrees`. Its `arithmetic_frame` is `zodiac_zero`; the computed
arcseconds use that frame while the original sign-relative magnitude stays
unchanged. Existing arithmetic operations retain their component origins. This
avoids comparing a total of 128°19′48″ directly with its Leo-relative 8°19′48″
representation or treating the 120° origin offset as a historical error.

For the January 20–24 positional calculations on XIII pp.220–221, declinations
and reused distances retain `historical_input` roles, including the three
Pafko control entries in those tables. Repeated source occurrences are not
additional independent observations. The January 20 retained-right-ascension
statement supplies lineage for the corresponding ecliptic result without a
complete reduction algorithm. The January 22 longitude difference is expressed
in arcminutes and arcseconds and checked against its two stated longitude
routes. Limited results retain their source roles without an assumed mean;
the final January 24 limitation leaves its exact input set unstated.

The [methods](observation-methods.md), [coverage guide](mars-catalog-status.md)
and [edition findings](edition-findings.md) explain the evidence and limitations.

## Quantity types and conversion conventions

Every published quantity, role and unit is defined in the [historical vocabulary](historical-data-dictionary.md) or [modern vocabulary](modern-data-dictionary.md). [Normalization conventions](normalization-conventions.md) define the conversion methods and time scales. Verification covers earlier interpretations as well as the current view. The [schema reference](database-schema.md#query-indexes) lists indexes for catalog filters and reverse relationship lookups.

Tycho source citations distinguish `original_edition` and `translation_edition` within `sources.data_json`. The historical subset version in release metadata denotes an unpublished working version, not a separate archived release.

## Complete normalization (schema 5)

`normalized_json` preserves the selected interpretation’s complete normalization object, including `longitude_origin`, `zodiac_sign`, `magnitude_degrees`, `zodiac_longitude_degrees`, `least_component_unit` and unresolved details when present. The existing degree decimal retains its original coordinate origin; it is not silently replaced by longitude from zodiac zero.

A zodiac decan retains `within_sign_range_degrees` and
`zodiac_longitude_range_degrees`, with
`range_bounds=lower_inclusive_upper_exclusive`. The first decan of Taurus spans
0–10 degrees within Taurus and 30–40 degrees from zodiac zero. These bounds
express the named sector, not a measurement confidence interval. Scalar fields
remain null, with `normalization_issue=coordinate_sector_not_scalar` and
`status=unsupported` for scalar conversion. The sector interpretation itself is
established; it is distinct from unread or unresolved source notation. Both
SQLite and CSV retain the complete normalization object.

Native paces use `distance_in_paces` and `source_pace`. Miles without an
identified convention use `distance_in_unspecified_miles` and
`source_unspecified_mile`. Neither supplies a physical length conversion. When
a source adds paces to miles, preserve the separate quantities and stated sum;
do not infer the pace-to-mile ratio.
