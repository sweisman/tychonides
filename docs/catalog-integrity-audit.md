# Numerical Integrity and Verification

The current release uses schema 5. Verification covers the complete downloaded
catalog, including its historical and modern records. The
[catalog guide](../resources/catalog/README.md) identifies the release and totals;
the [verification contract](data-workflow.md#what-verification-checks) enumerates
the checks.

## Safeguards

| Layer | Safeguard |
| --- | --- |
| Historical source compilation | Literal components and their explicit units are checked against reviewed source spans. Inherited units or signs need their own scoped evidence. |
| Modern conversions | Supported conversions are recomputed from native notation. Supplied derived values and timestamps cannot replace the preserved source meaning unchecked. |
| Normalization | Exact rational values remain separate from decimal conveniences. Zodiac-relative values retain their origin and separate full longitude in `normalized_json`. |
| Export | CSV is generated from the database. Every exported field is checked, including parsed JSON, flags, qualifications and numerical conveniences. |
| Release manifest | File hashes, database integrity, relationships, indexes, row identities and declared counts are checked. |
| Independent controls | Pafko’s separately entered records test defined source identifications and numerical properties; they do not create independent observations. |

Regression cases cover contradictory units, altered conversions, missing coordinate
components, fractional notation, changed qualifications and inconsistent exports.
The historical compiler and downloadable-release verifier have different inputs
and responsibilities. Download verification does not repeat source compilation.

## Documented Interpretation Limits

One clock in *Opera Omnia* X, p.245, is written `H. 10′ 38′ 12″`. The first prime
conflicts with the hour prefix. Its retained 10-hour interpretation rests on the
explicit adjacent `H.` and clock context; the prime remains preserved. A bare
`10′ 38′ 12″` does not independently establish hours. This is an interpretation
qualification, not a confirmed error in the edition. See the
[published volume](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-primus/).

The non-control expression `17° 23¾′ [17 23⁸⁄₄]` contains disagreeing fractional
forms and remains unresolved. An exact conversion must not silently choose
between them.

Source fingerprints bind decisions to the evidence actually reviewed. Changed
editions require explicit source bindings before earlier identity decisions can
be reused. Numerical agreement alone does not authorize transferring an identity
or interpretation.

## Scientific Limits

Passing these checks establishes the declared numerical and representation
contracts. It does not establish measurement accuracy, an independent image audit,
an accepted historical observing epoch, an orbital fit or a parallax detection.
Source ambiguity and correction dependencies remain visible.

Use the [Pafko reconciliation](pafko-validation-status.md),
[historical coverage](mars-catalog-status.md),
[supplementary-book coverage](historical-books-ingestion.md) and
[edition findings](edition-findings.md) for source-specific evidence and limits.
Eligibility for a scientific result follows the [research protocol](research-plan.md#model-comparison-protocol).
