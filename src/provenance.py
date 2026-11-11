"""Reference-locus claims and rendering diagnostics; never guess a note's page."""

import bisect
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from .catalog import identity
from .core import digest
from .inventory import blocks


DEFINITION = re.compile(r"^\s*\[\^([^\]]+)\]:")
REFERENCE = re.compile(r"\[\^([^\]]+)\]")


def analyze_anchor(item, line):
    positions = []
    for interval in item.get("candidate_intervals", []):
        start = interval["char_start"]
        prefix = line[:start]
        layer = "bracketed" if prefix.count("[") > prefix.count("]") else "main"
        positions.append(dict(**interval, rendering_layer=layer))
    counts = dict(sorted(Counter(p["rendering_layer"] for p in positions).items()))
    if counts == {"bracketed": 1, "main": 1}:
        diagnosis = "main_and_bracketed_locations"
    elif (
        counts.get("main", 0) > 1
        and counts.get("bracketed", 0) > 1
        and re.search(r"repeated|repetita", line, re.I)
    ):
        diagnosis = "repetition_and_parallel_locations"
    elif len(positions) > 1:
        diagnosis = "multiple_locations_unresolved"
    else:
        diagnosis = "single_source_location" if positions else "source_location_missing"
    return dict(
        diagnosis=diagnosis,
        layer_counts=counts,
        positions=positions,
        selected_interval=None,
        interpretation_status="source_structure_only_not_observation_equivalence",
    )


def enrich(items, texts, provenance, *, edition_hashes=None):
    editions = {
        v: ((edition_hashes or {}).get(v, hashlib.sha256(t.encode()).hexdigest()), t.splitlines())
        for v, t in texts.items()
    }
    definitions = []
    references = []
    by_key = defaultdict(list)
    incoming = defaultdict(list)
    indexes = {}
    for volume, (sha, lines) in sorted(editions.items()):
        group = []
        attachments = {}
        previous = None
        for start, end, kind, body in blocks(lines):
            marker = bool(re.fullmatch(r"(?:\[\^[^\]]+\]\s*)+", body.strip()))
            if (
                marker
                and previous
                and previous[2] in ("paragraph", "list", "table", "diagram")
                and not DEFINITION.match(previous[3])
            ):
                a, b, block_kind, _ = previous
                pages = sorted(
                    {
                        provenance.get(volume, {}).get(n, {}).get("page")
                        for n in range(a, b + 1)
                        if isinstance(provenance.get(volume, {}).get(n, {}).get("page"), int)
                        and provenance[volume][n]["page"] > 0
                    }
                )
                for n in range(start, end + 1):
                    attachments[n] = dict(
                        relation="standalone_reference_after_block",
                        block_start=a,
                        block_end=b,
                        block_kind=block_kind,
                        provisional_context_pages=pages,
                        interpretation_status="structural_context_not_reference_or_note_printed_page",
                    )
            previous = (start, end, kind, body)
        for i, line in enumerate(lines):
            match = DEFINITION.match(line)
            if not match:
                continue
            end = i + 1
            while (
                end < len(lines)
                and lines[end].strip()
                and not DEFINITION.match(lines[end])
                and not lines[end].startswith(("#", "|", "<!--"))
            ):
                end += 1
            record = dict(
                id=identity("note-definition", volume, sha, i + 1, match[1]),
                volume=volume,
                edition_sha256=sha,
                note_key=match[1],
                line_start=i + 1,
                line_end=end,
                text_original="\n".join(lines[i:end]),
            )
            definitions.append(record)
            group.append(record)
            by_key[(volume, match[1])].append(record)
        starts = [d["line_start"] for d in group]
        indexes[volume] = (starts, group)
        for i, line in enumerate(lines):
            definition = DEFINITION.match(line)
            pos = bisect.bisect_right(starts, i + 1) - 1
            owner = group[pos] if pos >= 0 and i + 1 <= group[pos]["line_end"] else None
            for match in REFERENCE.finditer(line):
                if definition and match.start() == definition.start() + len(line) - len(
                    line.lstrip()
                ):
                    continue
                page = provenance.get(volume, {}).get(i + 1, {}).get("page")
                ref = dict(
                    id=identity("note-reference", volume, sha, i + 1, str(match.start())),
                    volume=volume,
                    edition_sha256=sha,
                    line=i + 1,
                    char_start=match.start(),
                    char_end=match.end(),
                    note_key=match[1],
                    owner_note_key=owner["note_key"] if owner else None,
                    provisional_reference_page=page if isinstance(page, int) and page > 0 else None,
                    attachment=attachments.get(i + 1),
                    page_basis="source_line_provenance_not_scan_review",
                )
                references.append(ref)
                incoming[(volume, match[1])].append(ref)
    memo = {}

    def resolve(volume, key, trail=()):
        token = (volume, key)
        if token in trail:
            return dict(
                reference_pages=[],
                reference_context_pages=[],
                root_reference_ids=[],
                used_nested_reference=True,
                flags=["reference_cycle"],
            )
        if not trail and token in memo:
            return memo[token]
        count = len(by_key[token])
        if count != 1:
            return dict(
                reference_pages=[],
                reference_context_pages=[],
                root_reference_ids=[],
                used_nested_reference=False,
                flags=["duplicate_definition_key" if count > 1 else "definition_missing"],
            )
        pages = set()
        context_pages = set()
        roots = set()
        flags = set()
        nested = False
        for ref in incoming[token]:
            if ref["owner_note_key"] is None:
                roots.add(ref["id"])
                if ref["provisional_reference_page"] is not None:
                    pages.add(ref["provisional_reference_page"])
                else:
                    flags.add("reference_page_unmapped")
                if ref["attachment"]:
                    context_pages.update(ref["attachment"]["provisional_context_pages"])
                    flags.add("reference_attachment_unreviewed")
            else:
                parent = resolve(volume, ref["owner_note_key"], (*trail, token))
                nested = True
                pages.update(parent["reference_pages"])
                roots.update(parent["root_reference_ids"])
                flags.update(parent["flags"])
                context_pages.update(parent["reference_context_pages"])
        if not incoming[token]:
            flags.add("no_reference_occurrence")
        result = dict(
            reference_pages=sorted(pages),
            reference_context_pages=sorted(context_pages),
            root_reference_ids=sorted(roots),
            used_nested_reference=nested,
            flags=sorted(flags),
        )
        if not trail:
            memo[token] = result
        return result

    output = []
    for item in items:
        volume, line = item["volume"], item["line"]
        sha, lines = editions[volume]
        if item["edition_sha256"] != sha:
            raise ValueError("Provenance source fingerprint mismatch")
        starts, group = indexes[volume]
        position = bisect.bisect_right(starts, line) - 1
        definition = (
            group[position] if position >= 0 and line <= group[position]["line_end"] else None
        )
        resolution = resolve(volume, definition["note_key"]) if definition else None
        direct = provenance.get(volume, {}).get(line, {}).get("page")
        direct = direct if isinstance(direct, int) and direct > 0 else None
        pages = resolution["reference_pages"] if resolution else []
        context_pages = resolution["reference_context_pages"] if resolution else []
        encoded = re.fullmatch(r"p(\d+)[-_.].*", definition["note_key"]) if definition else None
        status = (
            "upstream_page_claim"
            if item["bibliographic_pages"]
            else "source_line_provenance_claim"
            if direct
            else "note_reference_locus_only"
            if pages
            else "reference_context_only"
            if context_pages
            else "encoded_note_key_only"
            if encoded
            else "unresolved_locus"
        )
        output.append(
            dict(
                item_id=item["id"],
                volume=volume,
                edition_sha256=sha,
                line=line,
                upstream_bibliographic_pages=item["bibliographic_pages"],
                source_line_page_claim=direct,
                note_definition_id=definition["id"] if definition else None,
                note_key=definition["note_key"] if definition else None,
                note_reference_pages=pages,
                note_reference_context_pages=context_pages,
                note_resolution=resolution,
                encoded_note_page_claim=int(encoded[1]) if encoded else None,
                accepted_note_printed_page=None,
                citation_status=status,
                anchor_diagnostic=analyze_anchor(item, lines[line - 1]),
            )
        )
    return dict(provenance=output, definitions=definitions, references=references)


def build_provenance(source_root, workspace):
    from .io import guard, write_json, write_csv

    root = Path(source_root).resolve()
    work = Path(workspace).resolve()
    guard(work, root)
    if (work / "pafko.json").exists() or (work / "raw" / "mars.xls").exists():
        raise ValueError("Protected benchmark workspace")
    witnesses = json.loads((work / "witnesses.json").read_text(encoding="utf-8"))
    names = [
        "assembly_manifest.json",
        "catalogue_items.jsonl",
        "inventory_manifest.json",
        "witnesses.json",
        *[f"provenance_v{w['volume']}.json" for w in witnesses],
    ]
    inputs = {n: digest(work / n) for n in names}
    assembly = json.loads((work / "assembly_manifest.json").read_text(encoding="utf-8"))
    upstream = {**assembly.get("output_hashes", {}), **assembly.get("input_hashes", {})}
    for name, sha in upstream.items():
        path = (work / name).resolve()
        if not path.is_relative_to(work) or digest(path) != sha:
            raise ValueError("Assembly input/output fingerprint mismatch")
    texts = {}
    maps = {}
    from .publication import read_witness

    for witness in witnesses:
        v = witness["volume"] - 9
        relative = f"brahe/thesaurus_observationum_vol{v}/translation/brahe_thesaurus_observationum_vol{v}_prepub.md"
        if witness["private_source"] != relative:
            raise ValueError("Unexpected canonical source path")
        texts[witness["volume"]] = read_witness(root, work, witness)
        maps[witness["volume"]] = {
            int(k): v
            for k, v in json.loads(
                (work / f"provenance_v{witness['volume']}.json").read_text(encoding="utf-8")
            ).items()
        }
    items = [
        json.loads(s)
        for s in (work / "catalogue_items.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    result = enrich(
        items, texts, maps, edition_hashes={w["volume"]: w["edition_sha256"] for w in witnesses}
    )
    claims = result["provenance"]
    inventory = json.loads((work / "inventory_manifest.json").read_text(encoding="utf-8"))
    for relative, sha in inventory["source_hashes"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or digest(path) != sha:
            raise ValueError("Source fingerprint changed")
    if any(digest(work / n) != sha for n, sha in {**upstream, **inputs}.items()):
        raise ValueError("Provenance input fingerprint changed")
    keys = Counter((d["volume"], d["note_key"]) for d in result["definitions"])
    summary = dict(
        status="reference_locus_claims_not_guessed_note_pages",
        catalogue_views=len(claims),
        note_definitions=len(result["definitions"]),
        note_references=len(result["references"]),
        duplicate_definition_keys=sum(count > 1 for count in keys.values()),
        citation_statuses=dict(sorted(Counter(c["citation_status"] for c in claims).items())),
        views_without_upstream_pages_with_reference_loci=sum(
            not c["upstream_bibliographic_pages"] and bool(c["note_reference_pages"])
            for c in claims
        ),
        views_with_reference_context_only=sum(
            c["citation_status"] == "reference_context_only" for c in claims
        ),
        anchor_diagnoses=dict(
            sorted(Counter(c["anchor_diagnostic"]["diagnosis"] for c in claims).items())
        ),
        accepted_inferred_note_pages=0,
        inspected_spans_added=0,
        measurement_count=None,
        limits=[
            "Reference-locus pages are provisional source claims, not verified physical note pages",
            "Parallel locations are preserved without selecting or merging observations",
            "Duplicate definition keys and unresolved reference paths remain explicit",
        ],
    )
    outputs = {}
    for name, rows in [
        ("catalogue_provenance", claims),
        ("note_definitions", result["definitions"]),
        ("note_references", result["references"]),
    ]:
        path = work / (name + ".jsonl")
        path.write_text(
            "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows),
            encoding="utf-8",
        )
        outputs[path.name] = digest(path)
        path = work / (name + ".csv")
        write_csv(path, rows)
        outputs[path.name] = digest(path)
    write_json(work / "public_provenance_summary.json", summary)
    outputs["public_provenance_summary.json"] = digest(work / "public_provenance_summary.json")
    write_json(
        work / "provenance_manifest.json",
        dict(
            schema_version=1,
            input_hashes=inputs,
            upstream_hashes=upstream,
            source_hashes=inventory["source_hashes"],
            output_hashes=outputs,
            source_inputs_unchanged=True,
            summary=summary,
        ),
    )
    return summary


if __name__ == "__main__":
    import argparse
    import os

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--source-root",
        default=os.environ.get("TYCHONIDES_SOURCE_ROOT"),
        required=not os.environ.get("TYCHONIDES_SOURCE_ROOT"),
    )
    p.add_argument("--workspace", default="work/mars-catalogue")
    args = p.parse_args()
    print(json.dumps(build_provenance(args.source_root, args.workspace)))
