"""Read final prepub editions; use batch text solely to recover page provenance."""

import bisect
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from .core import digest, extract_text

# Acquired source-edition manifests: original printed page -> current scan image.
# Volume XIII changed from the Toronto copy to the Hannover copy.
SCAN_OFFSETS = {10: 42, 11: 14, 12: 14, 13: 17}


def line_key(line):
    if line.startswith(("[QA:", "[ed.:", "[Running header:", "<!--", "[^")):
        return None
    line = re.sub(r"\[\^ed\d+\]|\^\d+\^", "", line)
    line = re.sub(r"[¹²³⁴⁵⁶⁷⁸⁹](?![⁄/])", "", line)
    line = unicodedata.normalize("NFKC", line).replace("*", "").replace("`", "")
    return " ".join(line.split()) or None


def trailing_qa_page_nodes(text, *, batch_name, batch_sha256):
    """Bind a page's text to its closing QA note, across separator lines.

    Inline table QA is not a page boundary. A source-PDF range supplies page
    indices only when its length matches the number of explicit page closures;
    this never extrapolates a printed-page offset.
    """
    closing = list(re.finditer(r"^\[QA:\s*p\.\s*(\d+)\s+notes\b", text, re.M | re.I))
    if not closing:
        raise ValueError("Source format has no closing QA page notes")
    header = re.search(r"source-PDF pages\s+(\d+)\s*[–—-]\s*(\d+)", text)
    pdf_pages = [None] * len(closing)
    if header:
        first, last = map(int, header.groups())
        if 0 < first <= last and last - first + 1 == len(closing):
            pdf_pages = list(range(first, last + 1))
    nodes = []
    start = 0
    for index, note in enumerate(closing):
        body = text[start : note.start()]
        explicit = {int(p) for p in re.findall(r"<!--\s*PDF p\.\s*(\d+)", body)}
        pdf_page = next(iter(explicit)) if len(explicit) == 1 else pdf_pages[index]
        if len(explicit) > 1:
            pdf_page = None
        for line in body.splitlines():
            key = line_key(line)
            if not key or line.strip() == "---":
                continue
            keys = {key}
            if line.startswith("#"):
                title = re.sub(r"^#+\s*", "", line)
                keys.update(line_key("#" * level + " " + title) for level in range(1, 7))
            for alias in sorted(keys):
                nodes.append(
                    dict(
                        key=alias,
                        page=int(note[1]),
                        pdf_page=pdf_page,
                        year=None,
                        batch=batch_name,
                        batch_sha256=batch_sha256,
                    )
                )
        end = text.find("\n", note.end())
        start = len(text) if end == -1 else end + 1
    return nodes


def metadata(line, state):
    if line.startswith("#") and re.search(
        r"Observations of (?:the )?year|OBSERUATIONES ANNI|\bANNO\b", line, re.I
    ):
        year = re.search(r"\b(15\d{2}|160[01])\b", line)
        if year:
            state["year"] = int(year[1])
    anchor = re.match(r"<!--\s*PDF p\.\s*(\d+)", line)
    if anchor:
        state["pdf_page"] = int(anchor[1])
        printed = re.search(r"printed p\.\s*(\d+)", line)
        state["page"] = int(printed[1]) if printed else None
    if line.startswith("[Running header:"):
        nums = [int(x) for x in re.findall(r"\b\d+\b", line)]
        years = [n for n in nums if 1560 <= n <= 1601]
        pages = [n for n in nums if n < 1000]
        if years:
            state["year"] = years[0]
        if pages:
            state["page"] = pages[0]
    if line.startswith("[QA:") and re.search(r"running head|opening|page number", line, re.I):
        pdf = re.search(r"(?:PDF )?p\.\s*(\d+)", line)
        if pdf:
            state["pdf_page"] = int(pdf[1])
        printed = re.search(r'(?:printed (?:p\.|page)|page number)\s*["“`]*(\d+)', line)
        if not printed:
            printed = re.search(r'["“`](\d+)["”`]\s*\((?:right|left)\)', line)
        if printed:
            state["page"] = int(printed[1])
        year = re.search(r'["“`*]((?:15\d{2}|160[01]))["”`*]', line)
        if year:
            state["year"] = int(year[1])


def provenance_map(lines, nodes):
    positions = defaultdict(list)
    for i, node in enumerate(nodes):
        positions[node["key"]].append(i)
    keys = [line_key(line) for line in lines]
    unique = {
        i: positions[k][0]
        for i, k in enumerate(keys)
        if k and len(positions[k]) == 1 and len(k) > 10
    }
    anchor_lines = sorted(unique)
    result = {}
    for i, key in enumerate(keys):
        if not key:
            continue
        choices = positions.get(key, [])
        basis = "unique_text_line"
        where = bisect.bisect_left(anchor_lines, i)
        prev = unique[anchor_lines[where - 1]] if where else None
        nxt = unique[anchor_lines[where]] if where < len(anchor_lines) else None
        if len(choices) > 1 and prev is not None and nxt is not None and prev < nxt:
            choices = choices[bisect.bisect_right(choices, prev) : bisect.bisect_left(choices, nxt)]
            basis = "text_line_between_unique_anchors"
        if len(choices) == 1:
            result[i + 1] = {k: v for k, v in nodes[choices[0]].items() if k != "key"}
            result[i + 1]["provenance_basis"] = basis
        elif prev is not None and nxt is not None and prev < nxt:
            a, b = nodes[prev], nodes[nxt]
            if all(
                a.get(k) == b.get(k) and a.get(k) is not None for k in ["page", "pdf_page", "year"]
            ):
                result[i + 1] = {k: a[k] for k in ["page", "pdf_page", "year"]}
                result[i + 1]["provenance_basis"] = "same_page_between_text_anchors"
    return result


def load_publication(root, volume):
    """Load a documented final edition and its independent page-provenance index."""
    if volume not in SCAN_OFFSETS:
        raise ValueError("Unknown observation volume")
    root = Path(root)
    work = f"thesaurus_observationum_vol{volume - 9}"
    directory = root / "brahe" / work / "translation"
    book = directory / f"brahe_{work}_prepub.md"
    if not book.is_file():
        raise ValueError(f"Missing final publication: {book}")
    source = str(book.relative_to(root))
    hashes = {source: digest(book)}
    nodes = []
    page_notes = {}
    meta = {}
    for batch in sorted(directory.glob("batch_[0-9][0-9][0-9].md")):
        rel = str(batch.relative_to(root))
        hashes[rel] = digest(batch)
        for lineno, line in enumerate(batch.read_text(encoding="utf-8").splitlines(), 1):
            metadata(line, meta)
            if (
                line.startswith("[QA:")
                and meta.get("pdf_page") is not None
                and meta.get("page") is not None
            ):
                page_notes[meta["pdf_page"]] = {k: meta.get(k) for k in ("page", "year")}
            key = line_key(line)
            if key:
                nodes.append(dict(key=key, **meta, provenance_source=rel, provenance_line=lineno))
    # Preserve the benchmark's existing provenance rules during this refactor.
    for node in nodes:
        note = page_notes.get(node.get("pdf_page"), {})
        for key in ("page", "year"):
            if node.get(key) is None and note.get(key) is not None:
                node[key] = note[key]
    text = book.read_text(encoding="utf-8")
    return dict(
        volume=volume,
        source=source,
        sha256=hashes[source],
        text=text,
        provenance=provenance_map(text.splitlines(), nodes),
        source_hashes=hashes,
    )


def read_witness(root, workspace, witness):
    """Read current canonical bytes, keeping a reviewed earlier identity namespace.

    A revision is accepted only through a retained, fingerprinted binding review.
    The original edition hash remains an identity/evidence locator; source_sha256
    identifies the actual current file and is never substituted for that hash.
    """
    root, workspace = Path(root).resolve(), Path(workspace).resolve()
    path = (root / witness["private_source"]).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Witness path outside source library")
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    expected = witness.get("source_sha256", witness["edition_sha256"])
    if actual != expected:
        raise ValueError("Canonical source fingerprint changed")
    if expected != witness["edition_sha256"]:
        revision = witness.get("source_revision", {})
        evidence = (workspace / revision.get("evidence_file", "")).resolve()
        if (
            not evidence.is_relative_to(workspace)
            or not evidence.is_file()
            or digest(evidence) != revision.get("evidence_sha256")
        ):
            raise ValueError("Missing or stale source revision evidence")
        proof = json.loads(evidence.read_text(encoding="utf-8"))
        if (
            proof.get("status") not in ("unchanged_source_bindings", "reviewed_source_bindings")
            or proof.get("volume") != witness["volume"]
            or proof.get("identity_edition_sha256") != witness["edition_sha256"]
            or proof.get("current_source_sha256") != actual
            or proof.get("private_source") != witness["private_source"]
        ):
            raise ValueError("Source revision evidence differs from witness")
        if proof["status"] == "reviewed_source_bindings":
            from .source_bindings import load_bindings, rebind_review

            binding = proof.get("binding_record")
            if binding is None or binding not in load_bindings(workspace):
                raise ValueError("Reviewed source binding ledger differs from witness evidence")
            original = (workspace / proof.get("original_review_ledger", "")).resolve()
            if not original.is_relative_to(workspace) or not original.is_file():
                raise ValueError("Missing frozen original source review")
            matches = [
                r
                for r in json.loads(original.read_text(encoding="utf-8"))
                if r["id"] == binding["review_id"]
            ]
            if len(matches) != 1:
                raise ValueError("Frozen original source review differs")
            rebind_review(matches[0], data.decode(), binding)
        for name, sha in proof["retained_artifact_hashes"].items():
            artifact = (workspace / name).resolve()
            if not artifact.is_relative_to(workspace) or digest(artifact) != sha:
                raise ValueError("Source revision baseline changed")
    return data.decode()


def extract_publications(root, volumes, include_record_ids=None):
    records, hashes = [], {}
    for volume in volumes:
        book = load_publication(root, volume)
        hashes.update(book["source_hashes"])
        state = dict(
            volume=volume,
            _line_provenance=book["provenance"],
            _include_record_ids=set(include_record_ids or []),
        )
        rows = extract_text(book["text"], book["source"], state)
        for r in rows:
            r["batch_pdf_page"] = r.get("pdf_page")
            r["pdf_page"] = r["page"] + SCAN_OFFSETS[volume] if r.get("page") is not None else None
            r["scan_page_basis"] = "source_edition_page_map"
        records.extend(rows)
    return records, hashes
