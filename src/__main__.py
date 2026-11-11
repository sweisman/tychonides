import argparse
import json
import os
import shutil
from collections import Counter
from fractions import Fraction
from pathlib import Path

from .core import digest, sample_records, compare_records, quote_angle, recorded_clock
from .io import guard, write_json, write_csv


def import_pafko(args):
    import xlrd

    src, out = Path(args.workbook).resolve(), Path(args.output).resolve()
    guard(out, Path(args.source_root))
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "raw" / "mars.xls"
    raw.parent.mkdir(exist_ok=True)
    if src != raw:
        shutil.copyfile(src, raw)
    book = xlrd.open_workbook(str(raw))
    sheets, records = [], []
    for sheet in book.sheets():
        cells = [
            [dict(value=c.value, type=c.ctype) for c in sheet.row(i)] for i in range(sheet.nrows)
        ]
        sheets.append(dict(name=sheet.name, nrows=sheet.nrows, ncols=sheet.ncols, cells=cells))
        if not sheet.nrows:
            continue
        if (
            sheet.ncols != 21
            or sheet.cell_value(5, 1) != "Year"
            or sheet.cell_value(5, 4) != "Quote"
        ):
            raise ValueError(f"Unrecognized workbook layout: {sheet.name}")
        for i in range(6, sheet.nrows):
            r = sheet.row_values(i)
            if not isinstance(r[5], (float, int)):
                continue
            date = f"{int(r[8]):04}-{int(r[9]):02}-{int(r[10]):02}"
            # Derive exact sexagesimal magnitude from Pafko's numeric cells, not the float result.
            magnitude = sum(
                (
                    Fraction(str(r[j])) * scale if r[j] != "" else Fraction()
                    for j, scale in [(17, 3600), (18, 60), (19, 1)]
                ),
                Fraction(),
            )
            converted = Fraction(str(r[20])) * 3600 if r[20] != "" else None
            sign = (-1 if converted < 0 else 1) if converted is not None else None
            value = str(magnitude * sign) if sign else None
            raw_time = str(r[3])
            key = recorded_clock(raw_time)
            quoted = quote_angle(str(r[4]))
            records.append(
                dict(
                    id=f"{sheet.name}:{i + 1}",
                    sheet=sheet.name,
                    row=i + 1,
                    volume=int(r[5]),
                    page=int(r[6]) if r[6] != "" else None,
                    date=date,
                    date_original=r[2],
                    time_original=raw_time,
                    time_key=key,
                    quote=r[4],
                    arcsec=value,
                    converted_degrees=r[20],
                    numeric_components=r[17:20],
                    quote_magnitude_arcsec=str(quoted) if quoted is not None else None,
                    quote_components_agree=(quoted == magnitude) if quoted is not None else None,
                    component_conversion_consistent=(
                        abs(converted - Fraction(value)) < Fraction(1, 1000000)
                    )
                    if value
                    else None,
                    cells=r,
                )
            )
    write_json(out / "workbook.json", dict(url=args.url, sha256=digest(raw), sheets=sheets))
    write_json(out / "pafko.json", records)
    write_csv(out / "pafko.csv", records)
    print(
        json.dumps(
            dict(records=len(records), by_volume=dict(Counter(r["volume"] for r in records)))
        )
    )


def extract(args):
    root, out = Path(args.source_root).resolve(), Path(args.output).resolve()
    guard(out, root)
    from .publication import extract_publications

    volumes = getattr(args, "volumes", [12])
    ledger_path = out / "adjudications.json"
    decisions = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
    include_ids = {
        d["identity"]["source_record_id"]
        for d in decisions
        if d.get("identity", {}).get("source_record_id")
    }
    records, hashes = extract_publications(root, volumes, include_ids)
    if hashes != {p: digest(root / p) for p in hashes}:
        raise RuntimeError("Source changed during extraction")
    write_json(out / "source_hashes.json", hashes)
    write_json(out / "observations.json", records)
    write_csv(out / "observations.csv", records)
    print(
        json.dumps(
            dict(
                records=len(records),
                sources=len(hashes),
                by_volume=dict(Counter(r["volume"] for r in records)),
                flags=dict(Counter(f for r in records for f in r["flags"])),
            )
        )
    )


def compare(args):
    out = Path(args.output).resolve()
    guard(out, Path(args.source_root))
    pafko = json.loads((out / "pafko.json").read_text(encoding="utf-8"))
    obs = json.loads((out / "observations.json").read_text(encoding="utf-8"))
    adjudication_path = out / "adjudications.json"
    adjudications = (
        json.loads(adjudication_path.read_text(encoding="utf-8"))
        if adjudication_path.exists()
        else []
    )
    reviews = {r["pafko_id"]: r for r in adjudications}
    structures = {
        r["source_record_id"]: r
        for r in adjudications
        if r.get("source_record_id") and r.get("resolved_flags") and r.get("evidence")
    }
    for r in obs:
        alias = (
            f"{r.get('provenance_source')}:{r.get('provenance_line')}:{r['column']}"
            if r.get("provenance_source") and r.get("provenance_line") and r.get("column")
            else None
        )
        review = structures.get(r["id"]) or structures.get(alias)
        if review:
            cleared = set(review["resolved_flags"]) & {"column_role_unresolved"}
            r["flags"] = [f for f in r["flags"] if f not in cleared]
            r["reviewed_flags"] = sorted(cleared)
    hashes = json.loads((out / "source_hashes.json").read_text(encoding="utf-8"))
    if not all(digest(Path(args.source_root) / p) == h for p, h in hashes.items()):
        raise RuntimeError("Source hashes changed; re-extract before comparing")
    from .reviews import prepare_reviews, derived_catalogue

    workbook = json.loads((out / "workbook.json").read_text(encoding="utf-8"))
    if digest(out / "raw" / "mars.xls") != workbook["sha256"]:
        raise RuntimeError("Original workbook fingerprint changed; re-import before comparing")
    obs, review_links, accepted_reviews = prepare_reviews(
        pafko, obs, adjudications, hashes, workbook["sha256"]
    )
    # Eligibility is source page/date overlap only; never select using observed values.
    full = getattr(args, "all", False)
    locations = {(r.get("volume", 12), r["page"], r["date"]) for r in obs if r["date"]}
    eligible = [r for r in pafko if (r["volume"], r["page"], r["date"]) in locations]
    manifest_path = out / ("full_manifest.json" if full else "sample_manifest.json")
    previous = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    )
    # Keep the pilot fixed while the extractor improves. Changing coverage must not
    # replace the difficult rows with easier ones.
    if full:
        selected = pafko
    elif previous and not args.resample:
        ids = {r["id"] for r in previous["records"]}
        selected = [r for r in pafko if r["id"] in ids]
    else:
        selected = sample_records(eligible, args.count)
    if not full and len(selected) != args.count:
        raise ValueError(f"Only {len(selected)} overlapping records; requested {args.count}")
    selected_ids = {r["id"] for r in selected}
    results = [
        r
        for r in compare_records(
            pafko if full else [p for p in pafko if p["volume"] == 12], obs, review_links
        )
        if r["pafko_id"] in selected_ids
    ]
    by_id = {r["id"]: r for r in obs}
    original = {r["id"]: r for r in selected}
    for result in results:
        result["pafko_quote"] = original[result["pafko_id"]]["quote"]
        result["pafko_time"] = original[result["pafko_id"]]["time_original"]
        result["pafko_numeric_components"] = original[result["pafko_id"]].get("numeric_components")
        result["pafko_decimal_degrees"] = original[result["pafko_id"]].get("converted_degrees")
        result["quote_magnitude_arcsec"] = original[result["pafko_id"]].get(
            "quote_magnitude_arcsec"
        )
        result["candidate_details"] = [
            dict(
                source=by_id[i]["source"],
                line=by_id[i]["line"],
                pdf_page=by_id[i]["pdf_page"],
                value=by_id[i]["value_original"],
                time=by_id[i]["time_original"],
                flags=by_id[i]["flags"],
                reviewed_flags=by_id[i].get("reviewed_flags", []),
                schema_basis=by_id[i].get("schema_basis"),
                hemisphere_basis=by_id[i].get("hemisphere_basis"),
            )
            for i in result["candidate_ids"]
        ]
    for result in results:
        if result["pafko_id"] in reviews:
            result["source_check"] = reviews[result["pafko_id"]]["status"]
    agreement = [r for r in results if r["status"] in ("exact", "magnitude_agreement")]
    agreement.sort(key=lambda r: r["pafko_id"])
    agreement = agreement[:: max(1, len(agreement) // 5)][:5]
    control_ids = previous.get("agreement_review_ids", []) if previous and not args.resample else []
    control_ids = control_ids or [r["pafko_id"] for r in agreement]
    manifest = dict(
        rule=previous["rule"]
        if previous and not args.resample
        else "mars-pilot-v1: page/date overlap; round-robin sorted years, SHA256(mars-pilot-v1:ID) within year; no measurement values used",
        eligible=len(eligible),
        count=len(selected),
        records=selected,
        selection_mode="all_workbook_rows" if full else "fixed_pilot",
        selection_frozen=not args.resample and previous is not None,
        agreement_review_ids=control_ids,
    )
    write_json(manifest_path, manifest)
    write_json(out / "comparison.json", results)
    write_csv(out / "comparison.csv", results)
    review = [
        dict(
            r,
            review_status=reviews.get(r["pafko_id"], {}).get("status", "pending"),
            evidence=reviews.get(r["pafko_id"], {}).get("evidence", ""),
            proposed_correction="",
        )
        for r in results
        if r["status"] != "exact"
        or r["conversion_status"] != "consistent"
        or r["pafko_id"] in manifest["agreement_review_ids"]
    ]
    write_csv(out / "review_queue.csv", review)
    # Every record gets an explicit next-review reason, including unsigned agreements.
    reasons = {
        "exact": "Text and stated hemisphere agree; scan verification is separate.",
        "magnitude_agreement": "Angular magnitude agrees; one or both quoted hemispheres are unstated.",
        "disagreement": "Quoted reading differs from the independently extracted reading; see delta and source check.",
        "unresolved": "A named extraction flag prevents a supported comparison.",
        "ambiguous": "Metadata and reading counts do not identify one source reading.",
        "unmatched": "No compatible extracted reading; review source context and clock conventions.",
    }
    for r in results:
        r["review_reason"] = reasons[r["status"]]
    write_json(out / "record_outcomes.json", results)
    write_csv(out / "record_outcomes.csv", results)
    catalogue = derived_catalogue(selected, obs, results, accepted_reviews)
    write_json(out / "derived_catalogue.json", catalogue)
    write_csv(out / "derived_catalogue.csv", catalogue)
    from .publication_export import public_records

    from .source_registry import public_sources

    registry = public_sources()
    public = public_records(catalogue, registry)
    write_json(out / "public_catalogue_draft.json", public)
    write_csv(out / "public_catalogue_draft.csv", public)
    # Human decisions are never overwritten by reruns.
    if not (out / "adjudications.json").exists():
        write_json(out / "adjudications.json", [])
    summary = dict(
        selected=len(selected),
        eligible=len(eligible),
        outcomes=dict(Counter(r["status"] for r in results)),
        by_year=dict(Counter(r["date"][:4] for r in selected)),
        by_volume={
            str(v): dict(Counter(r["status"] for r in results if r.get("volume", 12) == v))
            for v in sorted({p["volume"] for p in selected})
        },
        conversion_outcomes=dict(Counter(r["conversion_status"] for r in results)),
        numeric_source_sign_outcomes=dict(
            Counter(r["numeric_source_sign_status"] for r in results)
        ),
        source_checks=dict(Counter(r["source_check"] for r in results)),
        source_files_unchanged=all(
            digest(Path(args.source_root) / p) == h
            for p, h in json.loads((out / "source_hashes.json").read_text(encoding="utf-8")).items()
        ),
        image_review="See source_checks and adjudications.json; automated text comparisons are not scan verification",
        limitations=[
            "Contextual declination table extractor; not a complete Mars inventory.",
            "Printed-order alignments are explicit assumptions and require scan spot checks.",
            "Unsigned agreement does not validate hemisphere; no sign is imported from Pafko into the source.",
            "No rounding compatibility inferred without a documented precision policy.",
            "All workbook rows are included; no claim of complete source confirmation until unresolved checks are resolved."
            if full
            else "Sample is overlap-conditioned; no corpus-wide accuracy estimate.",
        ],
    )
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, indent=2))


def inventory(args):
    from .publication import load_publication, read_witness
    from .inventory import inventory_text, benchmark_links
    from .source_bindings import load_bindings, apply_span_bindings, rebind_extraction_inputs

    root, out, benchmark = (
        Path(args.source_root).resolve(),
        Path(args.output).resolve(),
        Path(args.benchmark).resolve(),
    )
    guard(out, root)
    if out == benchmark or out.is_relative_to(benchmark) or benchmark.is_relative_to(out):
        raise ValueError("Inventory output must be separate from the preserved benchmark")
    names = (
        "workbook.json",
        "pafko.json",
        "pafko.csv",
        "observations.json",
        "observations.csv",
        "source_hashes.json",
        "record_outcomes.json",
        "record_outcomes.csv",
        "adjudications.json",
        "derived_catalogue.json",
        "derived_catalogue.csv",
        "public_catalogue_draft.json",
        "public_catalogue_draft.csv",
        "pilot_baseline.json",
        "verification.json",
        "readiness.json",
        "coverage_notes.json",
    )
    baseline = {name: digest(benchmark / name) for name in names if (benchmark / name).is_file()}
    benchmark_hashes = json.loads((benchmark / "source_hashes.json").read_text(encoding="utf-8"))
    observations = json.loads((benchmark / "observations.json").read_text(encoding="utf-8"))
    outcomes = [
        r
        for r in json.loads((benchmark / "record_outcomes.json").read_text(encoding="utf-8"))
        if r["volume"] in args.volumes
    ]
    reference_path = out / "source_reference_reviews.json"
    reference_sha = digest(reference_path) if reference_path.is_file() else None
    reference_reviews = (
        json.loads(reference_path.read_text(encoding="utf-8")) if reference_sha else []
    )
    if not isinstance(reference_reviews, list):
        raise ValueError("Invalid source reference ledger")
    prior_witnesses = (
        {w["volume"]: w for w in json.loads((out / "witnesses.json").read_text(encoding="utf-8"))}
        if (out / "witnesses.json").exists()
        else {}
    )
    binding_path = out / "source_binding_reviews.json"
    binding_sha = digest(binding_path) if binding_path.is_file() else None
    bindings = load_bindings(out)
    spans, coverage, witnesses, hashes = [], [], [], {}
    texts = {}
    by_source = {}
    write_json(out / "inventory_manifest.json", dict(status="running", volumes=args.volumes))
    for volume in args.volumes:
        book = load_publication(root, volume)
        texts[volume] = book["text"]
        identity_sha = book["sha256"]
        prior = prior_witnesses.get(volume)
        if benchmark_hashes.get(book["source"]) != identity_sha:
            if (
                not prior
                or prior["edition_sha256"] != benchmark_hashes.get(book["source"])
                or read_witness(root, out, prior) != book["text"]
            ):
                raise ValueError("Final-edition fingerprint differs from the reconciled benchmark")
            identity_sha = prior["edition_sha256"]
        screened = inventory_text(
            book["text"],
            volume,
            identity_sha,
            book["provenance"],
            reference_reviews=[r for r in reference_reviews if r.get("volume") == volume],
        )
        spans.extend(screened["spans"])
        coverage.append(screened["coverage"])
        hashes.update(book["source_hashes"])
        witness = dict(
            id=screened["coverage"]["witness_id"],
            volume=volume,
            edition_sha256=identity_sha,
            witness_type="final_prepub",
            private_source=book["source"],
        )
        if identity_sha != book["sha256"]:
            witness.update(source_sha256=book["sha256"], source_revision=prior["source_revision"])
        witnesses.append(witness)
        by_source[book["source"]] = witness
        write_json(out / f"provenance_v{volume}.json", book["provenance"])
    spans = apply_span_bindings(spans, bindings)
    observations, _ = rebind_extraction_inputs(
        observations,
        None,
        texts,
        bindings,
        control_source_ids={i for r in outcomes for i in r["candidate_ids"]},
    )
    links = benchmark_links(spans, observations, outcomes)
    catalogue_path = benchmark / "derived_catalogue.json"
    catalogue = (
        {r["pafko_id"]: r for r in json.loads(catalogue_path.read_text(encoding="utf-8"))}
        if catalogue_path.exists()
        else {}
    )
    by_span = {s["id"]: s for s in spans}
    for link in links:
        preferred = catalogue.get(link["pafko_id"], {}).get("preferred_source_page")
        link["benchmark_preferred_page"] = preferred
        link["page_mapping_conflict"] = bool(
            link["span_id"]
            and preferred is not None
            and preferred not in by_span[link["span_id"]]["printed_pages"]
        )
    omitted = []
    if (benchmark / "coverage_notes.json").exists():
        for i, control in enumerate(
            json.loads((benchmark / "coverage_notes.json").read_text(encoding="utf-8")), 1
        ):
            sid = control["source_record_id"]
            source, line, _ = sid.rsplit(":", 2)
            if source not in by_source:
                continue
            witness = by_source[source]
            if control["source_sha256"] != witness["edition_sha256"]:
                raise ValueError("Omission-control fingerprint changed")
            linked = benchmark_links(
                spans,
                [dict(id=sid, volume=witness["volume"], line=int(line))],
                [dict(pafko_id=f"coverage-example-{i}", candidate_ids=[sid])],
            )[0]
            linked["control_id"] = linked.pop("pafko_id")
            omitted.append(linked)
    if any(digest(root / source) != sha for source, sha in hashes.items()):
        raise RuntimeError("Source changed during inventory")
    if baseline != {name: digest(benchmark / name) for name in baseline}:
        raise RuntimeError("Benchmark artifacts changed")
    if (digest(reference_path) if reference_path.is_file() else None) != reference_sha:
        raise RuntimeError("Source reference ledger changed during inventory")
    if (digest(binding_path) if binding_path.is_file() else None) != binding_sha:
        raise RuntimeError("Source binding ledger changed during inventory")
    with (out / "inventory_spans.jsonl").open("w", encoding="utf-8") as f:
        for span in spans:
            f.write(json.dumps(span, ensure_ascii=False) + "\n")
    write_json(out / "witnesses.json", witnesses)
    write_json(out / "coverage.json", coverage)
    write_json(out / "source_hashes.json", hashes)
    write_json(out / "benchmark_links.json", links)
    write_json(out / "known_omission_links.json", omitted)
    write_csv(out / "benchmark_links.csv", links)
    write_csv(
        out / "coverage_pages.csv",
        [dict(volume=c["volume"], **page) for c in coverage for page in c["pages"]],
    )
    public = dict(
        status="machine_screened_not_inspected",
        volumes=args.volumes,
        source_lines_screened=sum(c["screened_lines"] for c in coverage),
        candidate_spans=len(spans),
        reviewed_spans=0,
        measurement_count=None,
        benchmark_controls=len(links),
        benchmark_controls_covered=sum(r["coverage_status"] == "covered" for r in links),
        benchmark_page_mapping_conflicts=sum(r["page_mapping_conflict"] for r in links),
        omission_controls_covered=sum(r["coverage_status"] == "covered" for r in omitted),
        candidate_kind_counts=dict(Counter(s["block_kind"] for s in spans)),
        by_volume=[
            {
                k: c[k]
                for k in (
                    "volume",
                    "screened_lines",
                    "nonblank_lines",
                    "candidate_spans",
                    "candidate_nonblank_lines",
                    "explicit_mars_reference_lines",
                    "weekday_marker_lines",
                    "unmapped_nonblank_lines",
                )
            }
            for c in coverage
        ],
        limits=[
            "Candidate spans are source regions, not measurements or observing sessions",
            "Machine screening does not certify inspected coverage or completeness",
            "Provisional page mappings and target/quantity roles require review",
        ],
    )
    write_json(out / "public_inventory_summary.json", public)
    inventory_outputs = (
        "inventory_spans.jsonl",
        "witnesses.json",
        "coverage.json",
        "source_hashes.json",
        "benchmark_links.json",
        "known_omission_links.json",
        "benchmark_links.csv",
        "coverage_pages.csv",
        "public_inventory_summary.json",
        *(f"provenance_v{v}.json" for v in args.volumes),
    )
    write_json(
        out / "inventory_manifest.json",
        dict(
            schema_version=1,
            status="screening_complete_inventory_unreviewed",
            output_hashes={name: digest(out / name) for name in inventory_outputs},
            volumes=args.volumes,
            source_hashes=hashes,
            benchmark_artifact_sha256=baseline,
            benchmark_unchanged=True,
            source_inputs_unchanged=True,
            selection_uses_benchmark=False,
            selection_uses_measured_values=False,
            public_summary=public,
            input_hashes=({"source_binding_reviews.json": binding_sha} if binding_sha else {}),
            **(dict(source_reference_reviews_sha256=reference_sha) if reference_sha else {}),
        ),
    )
    print(json.dumps(public, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Read-only Mars transcription comparison")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ["import-pafko", "extract", "compare", "inventory"]:
        p = commands.add_parser(name)
        p.add_argument(
            "--output",
            default="work/mars-catalogue" if name == "inventory" else "work/pafko-sample-baseline",
        )
        p.add_argument("--source-root", default=os.environ.get("TYCHONIDES_SOURCE_ROOT"))
        if name == "import-pafko":
            p.add_argument("workbook")
            p.add_argument("--url", default="https://www.pafko.com/tycho/mars.xls")
        if name == "compare":
            p.add_argument(
                "--all",
                action="store_true",
                help="Compare every workbook row, including unmatched rows",
            )
            p.add_argument("--count", type=int, default=50)
            p.add_argument(
                "--resample",
                action="store_true",
                help="Explicitly replace the existing fixed pilot selection",
            )
        if name == "extract":
            p.add_argument("--volumes", nargs="+", type=int, choices=[10, 11, 12, 13], default=[12])
        if name == "inventory":
            p.add_argument(
                "--volumes", nargs="+", type=int, choices=[10, 11, 12, 13], default=[10, 11, 12, 13]
            )
            p.add_argument("--benchmark", default="work/pafko-full-reconciliation")
        p.set_defaults(
            run={
                "import-pafko": import_pafko,
                "extract": extract,
                "compare": compare,
                "inventory": inventory,
            }[name]
        )
    args = parser.parse_args()
    if not args.source_root:
        parser.error("Set TYCHONIDES_SOURCE_ROOT locally or pass --source-root")
    args.run(args)


if __name__ == "__main__":
    main()
