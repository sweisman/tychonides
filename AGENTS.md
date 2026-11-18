# Tychonides project guidance

Tychonides is an [Ars Astronomica](https://arsastronomica.com/) project that makes
historical and modern astronomical records usable for research. Tycho’s logs
anchor the catalog. It also includes other historical works and modern optical
observations. The [source inventory](docs/data-sources.md) defines coverage and
eligibility. The [research plan](docs/research-plan.md) defines future work.

## Working in this repository

- Keep to the requested sources, celestial bodies, and task. Ingestion, research,
  and publication have separate scopes. Completed work stays complete unless
  its inputs change or evidence shows a defect.
- Use the Python version declared in `pyproject.toml`. The implementation lives
  in `src/`. Run shell steps separately and use the cheapest sufficient checks.
- Automated contributors need maintainer approval for Git operations, including
  staging, committing, pushing, tagging, and changing history. Publishing or
  replacing release assets also requires approval. Bundle approved related work
  into one logical commit.
- Treat protected source inputs as read-only. Extract from the final edition and
  consult earlier production material only to recover missing page provenance.
- Keep source-bearing intermediates, authoritative reviews, fingerprints, and
  recovery state under excluded working storage. Public exports use reviewed
  fields and public citations. Keep private paths, credentials, copied source
  material, and operational notes out of public files.

## Ingestion and verification

- Resume at the first incomplete step in the active acquisition’s checkpoint.
  Check existing coverage before reading or preparing a source block. Reuse
  accepted reviews, staged data, and verification tied to unchanged inputs.
  Save review and checkpoint updates atomically.
- Prepare substantial, coherent blocks with shared parsers and declarative
  table or prose schemas. Set routine units, roles, and context once per block.
  Save individual review decisions as you go and export the accumulated work.
  Skip repeated preflights, per-number transcription, and per-batch scripts.
- Prefer an existing representation. When interpretation is uncertain, retain
  the complete expression, known context, and explicit limit. Extend the engine
  only when needed to preserve required evidence. Finish ingestion once scoped
  material is captured and required checks pass. Leave model reconstruction and
  unresolved scientific questions for research.
- Treat final-edition numerals as reliable. Consult a scan for a specific
  ambiguity or proposed correction. Use the best available witness, verify its
  printed-page alignment, and cache the evidence. Record edition issues
  separately from extraction or interpretation problems.
- Preserve original readings, identities, exact fractions, and provenance.
  Require evidence for inherited units, signs, dates, and context. Keep readings,
  reductions, predictions, and corrections distinct. Never choose a source
  match by numerical agreement or infer a reading from expected motion.
- Follow the [ingestion strategy](docs/ingestion-strategy.md) and its proportional
  verification rules. Use focused checks for changed logic and the shared release
  checks for exports. Report verified totals from manifests and checkpoints.
  Keep source-specific selectors and examples in the [review reference](docs/review-reference.md)
  and [casebook](docs/observation-methods.md).

## Public catalog and website

- Serve one self-contained SQLite catalog and a matching CSV. Follow the
  [workflow](docs/data-workflow.md) for verification and versioned releases.
  Keep the current working bundle and release assets, plus unique evidence and
  authoritative ledgers. Prune superseded intermediates only after checking
  dependencies and preservation.
- Use American English in project prose. Preserve source titles, readings,
  citations, and established data identifiers. Prefer Ars Astronomica editions
  and PDFs where available. Identify original printed witnesses when needed.
- The root README is the website homepage. Keep it reader-facing and brief.
  Explain the name Tychonides there only. Put coverage and planned acquisitions
  in the source inventory and scientific milestones in the research plan.
  State verification scope and interpretation limits plainly.
- Code is AGPL-3.0-or-later. Project data contributions are CC0-1.0. Third-party
  source terms remain separate.
