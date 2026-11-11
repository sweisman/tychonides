# Historical Review Format

Technical reference for contributors preparing source-bound review records. Start
with the [processing workflow](data-workflow.md) and the [ingestion strategy](ingestion-strategy.md)
for the sequence and evidence requirements; use the [data dictionary](catalog-data-dictionary.md)
for exported field meanings. The [worked example](worked-example.md) demonstrates
a complete small review.

- [Source evidence and table ranges](#source-evidence-and-table-ranges)
- [Selectors and field adapters](#selectors-and-field-adapters)
- [Interpretation and source updates](#interpretation-and-source-updates)

## Source Evidence and Table Ranges

Ordinary extraction uses `basis.kind=final_edition_review`, bound to the canonical
edition and interval fingerprints. Scans resolve specific ambiguities or support
proposed corrections; they are not required to confirm every recorded number.
For a scan-based review, `basis.evidence_hashes` maps retained witness files to
their hashes; missing or changed declared evidence prevents a new append.
Historical interpretation remains explicit; a parser result does not establish
that a source passage has been inspected.

Repeated table layouts can be recorded compactly as `cell_groups`, with shared
quantity and role fields, explicit cell selections and per-cell exceptions.
An inclusive `line_range: [first, last]` replaces `cells` for a reviewed run of
rows with the same schema. Declare either a physical `column` or consecutive
`source_columns`, such as `[2, 3]` for separate degree and minute cells. The
materializer binds the complete printed cell span and uses the declared
`component_units`. Targets and signs require explicit review or the bounded
`table_fields` declarations in the selectors section below. Split the range
around headers, empty cells and exceptions, which keep their own explicit
selections. Range expansion produces the same assertions as explicit cells.
`row_events` records reviewed grouping, including blank-clock continuations.
The runner expands this data through the existing parsers; a bare annotation
cannot become a numeric reading. Supplementary edition issues and coordinate
classifications use append-only `record_updates` in the same review record.
Unpaged numerical edition notes require a literal definition and attachment,
an explicit editorial role and an `annotation_of_ref` naming the preserved
original quantity. The compiler derives `edition_note_marker` from the
validated note context; it cannot be supplied as an assertion's invented
citation. These records have no observing event and retain unapplied variants
and suggestions separately from the original value.
If an attachment falls between conflicting page scopes, a separate note review
may supply `basis.annotation_attachment_citations`, naming the original review,
note context, attachment line and reviewed printed page. This qualifies that
attachment in the named scopes; it neither assigns a page to the collected
note nor replaces other source-page claims. Keep the original review immutable.
For a quantity embedded in prose, select the line's single field as column 1
and give its exact `source_expression` and components. Assembly binds the
literal text interval without claiming a printed table cell. Repeated literal
occurrences remain ambiguous until independent source evidence distinguishes them.

## Selectors and Field Adapters

Within a declarative `cell_groups` review, a prose selection can use `line`,
`column: null` and a zero-based `expression_index` in place of a copied literal
and character offsets. The shared materializer selects the staged occurrence in
printed order and supplies its expression, position and parsed components.
Quantity, role, endpoints and context still require review. Partial numerical
continuations are rejected; a queried candidate cannot acquire a scalar through
this selector. Complete exceptional literals remain available for notation that
staging cannot represent. Table selections retain their physical column bindings.

Table groups may retain literal row labels through `row_context`, supplied in
the assertion defaults or a group. Its `key_prefix` names the row contexts;
`columns` maps descriptive field names to physical column numbers, for example
`{"native_index": 1, "reference_star_as_printed": 3}`. Values and column
references are copied from each selected row without identifying stars,
reclassifying records or inferring dates. Repeated reference numbers remain
separate source rows. Conflicting existing row contexts are rejected.

For a reviewed coordinate table, `table_fields` can expand native fields over
the same row range. `subject_column: 1` reads the source label before its
bracketed annotation; that column must also be retained in `row_context`.
It preserves the native designation without identifying a modern star.
For catalog entries, `subject_prefix: Taurus` qualifies that literal label
by its reviewed constellation scope and retains bracketed qualifications.
The same label selection works with consecutive `source_columns` and with
native `stellar_magnitude_class` cells. These descriptions identify source
entries; repeated labels do not establish a unique modern stellar identity.
`direction_suffixes: {A: south, B: north}` declares a local convention for
explicit declination or latitude suffixes. Missing labels and contradictions
with an explicitly supplied target or direction require review.
When the hemisphere has its own physical column, use
`direction_column: {column: 9, values: {A: south, B: north}}` and retain that
column in `row_context`. A missing or unknown label requires a separate
review; it does not inherit a hemisphere automatically.
An explicit empty-string entry mapping to `null` preserves a blank hemisphere
as unknown. Qualified labels such as `A [?]` do not match an unqualified `A`.
For split coordinate columns with optional trailing direction letters,
`unmarked_direction: unknown` alongside `direction_suffixes` retains an
unmarked numerical value without assigning a hemisphere. Unknown letters and
queried directions still require review.

With consecutive `source_columns`, `omit_empty_source_columns: true` skips a
value only when every selected physical cell is empty. Written zeros remain
values; partially written expressions still undergo the usual component
checks. This opt-in policy can preserve the intentionally blank domain of an
astronomical table without manufacturing zeros or silently dropping partial
readings.

For longitude, `zodiac_from_expression: true` requires exactly one literal
zodiac sign in the selected expression. `value_before: ";"` can separate an
angle from a following calendar label only when the entire source cell is
retained in `row_context`. This operation does not interpret that date or
create an observing timestamp. Multiple signs, including a printed correction,
require explicit original and alternative interpretations. Angular components
still pass the ordinary compiler and exact normalizer.

A reviewed month/day/hour/minute column can use `clock_fields` with
`separator: "·"` (or `":"`), an explicit `absent_values` list, and
`component_units: [hour, minute]`. The physical `column` must also be retained
in `row_context`. For example, `Nou. 18 · 1 · 30` supplies the literal clock
`1 · 30`; the day is preserved in context and does not become an hour.
Two-field clocks retain their own hours and minutes without inheriting a date.
Only explicitly listed date-only or nonnumeric labels are omitted; partial
numeric clocks and extra components fail validation. The review still decides
whether the value is an observing clock, a calculation epoch, or an annotated
positional time. This selector establishes no calendar or absolute timestamp.

Stellar-separation tables can declare reusable `table_relationship_rules` and
`table_authorities` in a review. A group selects a rule with
`table_relationships: rule-name`; its ordinary `line_range`, `source_columns`
and `component_units` still select and normalize the written values. Both the
label and authority columns must be retained in `row_context`.

A relationship rule specifies `label_column`, `authority_policy` and
`context_prefix`. Its `pairs` dictionary binds complete printed labels to
reviewed `subject`/`reference` names. Alternatively, a fixed `subject` uses a
`reference_labels` dictionary, or explicitly opts into `literal_references`.
Literal mode preserves numbered names and bracketed qualifications; it does
not identify a modern star. Authority policies declare a physical `column`,
exact `values` with roles and attribution `context_keys`, and explicit
`repeat` marks. Unknown labels, unknown authorities and conflicting explicit
fields fail rather than being selected by the measured angle.

When a cited heading supplies one authority for an entire run and there is no
observer column, its authority policy uses `column: null`, an empty `repeat`
list and one `values` entry keyed by the empty string. That entry declares the
role and source-bound heading contexts. The generated row evidence records no
printed authority cell; it does not manufacture repeated observer labels.

Blank pair cells and declared repetition marks inherit their preceding source
labels within a reviewed block. A non-table heading prevents that inheritance;
a new, fully explicit pair and authority can restart the rule. Generated
contexts retain the literal cells and their inheritance evidence. Split ranges
around layout exceptions and declare those rows explicitly. Missing numerical
components follow the existing unresolved-component policy. A known angular
reading with an unestablished reference association can retain
`source_reference_status: antecedent_unresolved` and the matching caution flag;
this does not authorize choosing an endpoint from expected motion or numerical
agreement.

An optional `zodiac_sign_column` binds a row's printed sign to a coordinate whose
`zodiac_sign` has already been explicitly reviewed. The compiler checks that
sign against the literal column; the operation does not choose a sign from the
number or a neighboring row. The resulting frame context is separate from
the row labels. Source expressions, numerical components and existing assertion
identities remain unchanged. A group may use `row_context: null` to opt out of
a shared default when it selects a different kind of source material.

An explicitly stated carry-down rule can supply a blank leading angular cell
or a whole proportional coefficient.
Declare `table_carry: {rule_key: carry, unit: arcsecond, column: 8}` on a
group whose consecutive `source_columns` begin at that column. The named
source context must have `record_type: source_table_carry_rule`, its inclusive
table `line_start`/`line_end`, and a literal `source_expression` anchored to one
preceding instruction line. Preparation and compilation independently find
the nearest nonblank cell in that column within the scope. A queried leader,
intervening nonnumeric cell, missing origin or broken table scope is rejected.
The printed expression stays unchanged; `source_component_carry` preserves the
origin and the qualified rule context in the public scientific metadata.
For `quantity: proportional_minutes`, the matching leading unit is
`proportional_minute`; it retains the coefficient's native scale. Angular and
proportional units cannot be exchanged. A separately marked terminal `recte`
proposal in an origin cell leaves the printed prefix as the carry origin.
The proposal remains a separate, unapplied interpretation. A query still
blocks carrying, and a missing lower component is not supplied by this rule.

Omission alone does not establish a carry rule. With
`incomplete_component_policy: unresolved` and explicit `component_units`, a
value missing one leading component remains literal, with empty interpreted
components, `source_notation_unresolved` and no scalar. Complete expressions
retain their ordinary exact interpretation. This policy does not supply zero,
borrow a degree or choose a value from expected astronomical motion.

Native eclipse-digit columns use `quantity: eclipse_extent`,
`source_extent_unit: digit` and their explicitly reviewed `digit`,
`digit_minute` and, where present, `digit_second` places. A nonempty
`unit_basis` must identify the header units for bare table columns. The same
printed conversion may have the shared subject `Sun and Moon` when the source
says it serves either luminary; this does not create two source readings.
Queried native-digit entries retain `source_eclipse_digit` as their known unit,
empty interpreted components and no scalar. They do not become angles or times.

For a compound angle whose minute or second unit is written as a word, a prose
`expression_index` selection may opt into `complete_angle_sequence: true` with
`component_units: [degree, arcminute]` (or the three angular components). This
extends that selected occurrence to the complete contiguous unit sequence,
including mixed fractions such as `25° 25½ minutes` and the printed separator
in `52° / 48′`. It preserves the source
literal and the existing staging indices. Queries, conflicting units and
unconsumed numerical continuations require an explicit unresolved review.

For an angle written wholly in words, select its first numeric `fragment_index`
and set `complete_angle_sequence: true` with the reviewed angular
`component_units`. For example, `[degree, arcminute]` selects the complete
`24 degrees 32 minutes`; `[arcminute]` selects `34 minutes`. Mixed fractions and
explicitly omitted intermediate places are retained. Completion consumes the
declared number–unit sequence and rejects queries, time units and leftover
numeric continuations. It neither changes existing staging indices nor supplies
targets, roles, hemispheres or clock conventions.

A homogeneous worked-calculation block can instead declare
`calculation_angles: true` with an inclusive `line_range`. This requires the
`calculation_angle` quantity, a calculation/input/reduction role, an explicit
source context and `not_an_additional_raw_reading`. The materializer selects
every staged angular occurrence, preserving repeated literals and their existing
identities. A reviewed `worded_component_sequences` list can additionally select
worded angles through the same complete-sequence parser. Tables, queried values,
partial expressions and editorial alternatives require explicit selections.
Keep coordinates, signs, times, native lengths and differently classified values
in their own reviewed groups; this operation neither assigns their meaning nor
completes the source block's non-angular numerical companions.

For an explicitly reviewed form such as `p. 41/35`, a source-bound literal can
declare `source_unit_notation: parts_slash_minutes`. The shared materializer
supplies its degree and minute components without retyping them. This opt-in
does not alter staging indices or reinterpret unlabeled fractions.

An explicit unsigned decimal-degree expression, such as `34.5 degrees` or
`0.5°`, can declare `source_unit_notation: decimal_degrees` without supplying
components. The materializer preserves the literal and derives its exact
rational degree value. Missing units, comma decimals, time units, queried
readings and incomplete compound expressions require separate review; a decimal
tail cannot be selected as a whole-degree value.

The corresponding `source_unit_notation: decimal_hours` accepts explicit hour
expressions such as `7.25 hours`, preserving the literal and deriving 29/4 hours
exactly. The reviewed quantity and context establish whether the hours describe
a clock, duration or calculation epoch; the numerical conversion supplies no
calendar, day origin or absolute observing timestamp.

For native scalar occurrences, a prose selection can instead use `fragment_index`:
the zero-based position among that line's staged numeric fragments. Declare one
`component_units` entry and review the quantity, role and context. The materializer
supplies the exact literal and character positions. A single explicit angular or
time unit is included and checked against the declared component. It rejects
fragments covered by an angle or clock expression, grouping or continuation
digits, partial compound quantities, signed values and uncertainty marks. Use a
complete expression review, or the explicit angular completion above, for these cases. Selecting an occurrence supplies no physical interpretation
and does not combine ratio operands.

Comma-grouped integers remain complete staged fragments. They require an explicit
`source_number_grouping=comma_thousands` review before conversion; staging alone
does not decide whether punctuation denotes an integer grouping.

Source-bound classification reviews can also add approximation, bound and quality
qualifications. These retain the original review, reading and numerical fields.
They require a fingerprint of the prior interpretation and unique evidence on the
reading's source line. Qualification reviews cannot remove flags or alter values,
units, endpoints or roles.

## Interpretation and Source Updates

An interpretation review can revise the direction of an already identified
coordinate without adding another quantity. Its `direction_reviews` bind the
earlier assertion, expected prior direction, source label and reviewed Latin
expansion. Inherited labels also bind their earlier column anchor. Original
expressions, components, unsigned magnitudes and identifiers remain fixed;
previous normalizations are retained in protected history. The verifier permits
only the reviewed direction and signed-magnitude changes and reports them
separately. Ordinary imports continue to require unchanged prior quantities.

`append --review` accepts either one reviewed JSON record or a nonempty list.
Every packet and supplementary decision is validated before the ledger changes.
Separate packets retain their own volumes and source intervals; unread gaps are
not included, and overlapping source lines or candidate regions are counted once.
Replay the same ordered list to recover an interrupted append. A list mixing
already appended and new packets is rejected rather than partly imported.
Use one subsequent `run` for the accepted list.

The screened index does not define the limits of source evidence. A clock or
other necessary context outside its regions can be bound to an independently
selected Mars passage through an append-only source-reference review. Retain the
exact block, parent line, relationship and fingerprints; refresh the inventory
and dependent stages before importing its quantities. Verify that prior candidate
records and catalog quantities remain unchanged, and retain an explicit
inventory-expansion verification and new baseline. Candidate totals can therefore
increase when a missed context is documented.

Use `refresh-references --review REFERENCES.json` for a list of these reviewed
links, followed by `run --label LABEL`. The shared workflow retains the previous
inventory, reference ledger and catalog as recovery baselines, refreshes the
inventory and staging, and checks that existing regions and quantities survive
unchanged. Replay the same reference list if interrupted before its ledger write;
resume `run` if interrupted during rebuilding. A refresh adds candidate regions,
not inspected coverage or measurements.

References to regions already selected by the source screening are still
validated and retained in the reference ledger. Their original inventory
records remain unchanged; a newly documented parent relationship does not
create another region or rewrite its earlier selection evidence.

If a reference refresh is interrupted by changes to provenance batches while
the canonical edition is unchanged, `refresh-source --volume VOLUME` can rebind
those inputs only after reproducing every selected source region and its
existing provenance. The compatibility evidence retains the old and new input
fingerprints and any changes outside the selected regions. Changed selected
bindings, canonical readings or input membership are rejected. Resume the same
`run --label LABEL` after this check; the earlier review records remain fixed.


Changes follow the [proportional verification policy](ingestion-strategy.md#verification-proportional-to-the-change). Preserve earlier readings and review decisions; an interpretation update is not permission to overwrite them.
