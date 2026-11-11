# Processing and Verification Workflow

For downloads and an introductory query, start with the
[catalog guide](../resources/catalog/README.md). This page explains verification
and the contributor workflow. Detailed review syntax is in the
[historical review reference](review-reference.md).

## Installation and Verification

Python 3.11 or newer is required. From a source checkout:

```sh
python -m pip install .
./scripts/download-catalog downloads
```

The download helper retrieves the files pinned by the checkout, verifies them and
decompresses `tychonides.sqlite`. To verify files obtained separately:

```sh
tychonides-verify resources/catalog --assets-dir downloads --docs-root .
```

Alternatively, place the matching manifest beside the files and run
`tychonides-verify downloads`. The installed package is `tychonides`;
`tychonides --help` and `python -m tychonides --help` expose its commands.
From a checkout, `python -m src` provides the same entry point.

## What Verification Checks

For schema 5 releases, the verifier checks:

| Check | Guarantee within this contract |
| --- | --- |
| File identity | Downloaded bytes and the decompressed database match manifest SHA-256 values. |
| Database structure | SQLite integrity, foreign keys and declared indexes pass their checks. |
| Representation consistency | Every CSV field agrees with the canonical database projection. JSON is compared structurally; decimal conveniences come from exact values. Row identities and all declared counts, including per-source totals, agree. |
| Mechanical conversion | Supported modern conversions are recomputed from preserved native fields; displayed derived columns agree. No new astrometric correction is applied. |
| Documentation contracts | With `--docs-root`, CSV and schema fields, vocabulary coverage, generated references, local links and release identifiers are checked. |

The historical compiler separately checks literal components, explicit units and
reviewed source bindings. The download verifier does not repeat that compilation
or inspect source images. Earlier schemas have their own verification contracts.

Verification establishes the enumerated checks, not measurement accuracy,
observational independence, an accepted historical epoch or eligibility for an
astronomical analysis. See [terminology](catalog-terms.md) and
[numerical integrity](catalog-integrity-audit.md).

## Processing Stages

| Stage | Inputs | Outputs |
| --- | --- | --- |
| Independent controls | Original Pafko workbook, editions and reviewed identity matches | Preserved workbook entries and reconciliation controls |
| Inventory | Selected editions and bibliographic references | Candidate regions and source fingerprints |
| Staging | Inventory and canonical text | Parsed table, coordinate and prose candidates |
| Review and assembly | Declarative reviews, candidates and source bindings | Quantities, groups, context and relationships |
| Working export | Assembled records and source evidence | Verified SQLite, CSV and manifest |
| Consolidation | Compatible verified working catalogs | One catalog preserving every input record and relationship |
| Public packaging | Verified consolidated catalog and publication policy | Compressed SQLite, CSV and public manifest |

Staging proposes occurrences; source review establishes their interpretation.
Processing commands require a source checkout and the corresponding workspace.
The [ingestion strategy](ingestion-strategy.md) defines selection, batching,
unresolved interpretations and checks proportional to the change.

## Historical Source Reviews

Use each work’s final edition as the content authority. Configure its location
through `TYCHONIDES_SOURCE_ROOT` or `--source-root`; source files remain read-only.
Scans resolve a particular ambiguity or support a correction rather than serving
as a routine second transcription of every number.

For a prepared historical-book bundle:

```sh
python -m src.review_workflow run --workspace WORKSPACE --review REVIEW.json
```

This command validates and durably appends the review, then exports from the same
compilation. Source bindings, duplicate occurrences, prior-record preservation,
numerical interpretation and export parity are checked. If export is interrupted
after the ledger is saved, resume with `run --workspace WORKSPACE`; do not append
the accepted bundle again. Standalone `append --review` is available when export
is intentionally deferred.

Use `inspect` with the registered `--source-id` or `--volume`, the workspace and
source interval to examine staged candidates. Inspection alone adds no accepted
quantities. `status` distinguishes pending reviews from the last verified export.
Use `--help` for command-specific arguments.

The [review reference](review-reference.md) documents table ranges, prose selectors,
inherited components, source evidence and additive interpretation reviews. The
[casebook](observation-methods.md) records source-specific applications.

## Importing Additional Collections

### Public Meridian Tables

The shared adapter supports the eight selected JPL series, USNO W1J00/W2J00
Solar System tables, Carlsberg `planet.dat` and Tokyo `planets`:

```sh
python -m src.online_catalogs --workspace WORKSPACE --base EXISTING_CATALOG
```

Choose a workspace beneath the checkout’s `work/` directory. Supply downloads in
its `raw/` directory: `jpl-SERIES.txt` for the series in `src/online_catalogs.py`,
`usno-w1.txt`, `usno-w2.txt`, `cds-carlsberg-planets.gz` and
`cds-tokyo-planets.gz`. Public URLs and table coverage are in the
[source directory](data-sources.md).

The adapter checks target and terrestrial instrument codes, preserves native
lines and field bounds, retains incomplete coordinates, and uses the checked
exact-conversion routines. Existing source/artifact/entry identities are skipped
only when the literal agrees. Fingerprinted prepared tables and a checkpoint
support recovery. Mean stellar and environmental companions are separate selections.

### Compatible Working Catalogs

```sh
python -m src.import_collection --base EXISTING_CATALOG \
  --catalogue ADDITIONAL_CATALOG --output COMBINED_WORKSPACE
```

The merger requires compatible working schemas, rejects conflicting identities,
preserves complete record graphs, and regenerates CSV from SQLite. Inputs remain
unchanged. Keep the existing baseline until the successor passes verification.

### Source Stores and Full-Fidelity Exports

```sh
python -m src.import_collection --database INPUT.sqlite \
  --quantities quantities.jsonl --overlaps overlap-candidates.json
```

Omit `--overlaps` when no candidate file exists. The source store is opened
read-only. Artifact hashes, native payloads, original scalars and supported
conversions are checked before import. Candidate overlaps remain linked source
occurrences rather than instructions to merge observations. Image pixels remain
external; working artifact bytes and local locators require public projection.

## Public Release

The current release is [tychonides-1.0.0](../resources/catalog/README.md).
To prepare its public files from a verified working catalog:

```sh
python -m src.publish_collection --source WORKING_CATALOG \
  --output PUBLIC_DIRECTORY --release-id tychonides-1.0.0
```

Packaging adds citations and derived-value columns, removes source-document bytes
and local image paths, checks for private material, and verifies the public
database and CSV. The manifest identifies the compressed download and the
decompressed database separately. The SQLite database includes the relationships;
the CSV provides one row per quantity for spreadsheet use.

Large files are GitHub Release assets. The repository retains the manifest and
download documentation. Upload the matching compressed database, CSV and manifest
to the named release; CI verifies those assets against the repository manifest.
Local packaging does not upload files or deploy a website.

## Recovery and Working-Data Retention

Use the acquisition checkpoint and validated stage manifests to resume processing.
Retain authoritative reviews, source and correction bindings, fingerprints,
original inputs, unique evidence, the current preservation baseline and final
verification records. An interrupted append is recovered from its ledger state;
it is not a reason to restart a completed source interval.

After consolidation, retain one current working catalog and one current public
release. Verified repeat exports, superseded drafts and preparation packets whose
evidence is already preserved can be removed after dependency checks. A unique
source image or correction decision remains evidence regardless of its directory.

Promotion is recoverable and replaces the manifest last. The verifier rejects a
directory containing `.pending-release`; rerunning packaging recovers the pending
transaction. Only one writer may promote to a destination at a time. Individual
files are replaced atomically; the file set is not one filesystem transaction.

## Reproducibility Boundary

Downloads can be verified independently. The [public worked example](worked-example.md)
reproduces a cited reading through review, normalization and export using supplied
inputs. A complete historical extraction rebuild additionally requires the
unpublished source bindings and review inputs. Working-manifest hashes do not
substitute for those inputs. Published editions and bibliographic citations support
independent extraction and source checking.

## Development

Install tools with `python -m pip install ".[dev]"`. The project metadata is the
dependency authority. From a checkout:

```sh
python -m unittest discover -s tests
ruff check src tests
ruff format --check src tests
```

Tests use self-contained fixtures. Source selection, extraction, normalization,
public projection and release verification retain their separate responsibilities.
For the checks required by a particular change, follow the
[proportional verification policy](ingestion-strategy.md#verification-proportional-to-the-change).
Routine data additions do not require a full regression suite or repeat export;
semantic changes require the relevant regressions and deterministic export checks.

Code is AGPL-3.0-or-later; project data contributions are CC0-1.0. Third-party
sources retain their terms; see [data licensing](../DATA_LICENSE.md).
