"""Fingerprint explicitly selected editions and inventory every source section.

The inventory is protected working evidence, not reviewed observations or a
public export. It never discovers additional books or assigns measurement roles.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re

from .recovery import write_json_atomic


def inventory_sources(entries, workspace):
    workspace = Path(workspace).resolve()
    identifiers = [entry["source_id"] for entry in entries]
    if not identifiers or len(set(identifiers)) != len(identifiers):
        raise ValueError("Source identities must be nonempty and unique")
    paths = [Path(entry["path"]).resolve() for entry in entries]
    if len(set(paths)) != len(paths):
        raise ValueError("One edition cannot be registered twice")
    if any(workspace == path.parent or path.is_relative_to(workspace) for path in paths):
        raise ValueError("Inventory output overlaps source storage")
    destination = workspace / "inventory.json"
    prior = json.loads(destination.read_text(encoding="utf-8")) if destination.exists() else None
    sources = []
    for entry, path in zip(entries, paths, strict=True):
        sid = entry["source_id"]
        if not re.fullmatch(r"[a-z][a-z0-9-]+", sid):
            raise ValueError("Invalid source identity")
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        sha = hashlib.sha256(raw).hexdigest()
        lines = text.splitlines()
        starts = (
            sorted({1, *(n for n, line in enumerate(lines, 1) if re.match(r"^#{1,6}\s", line))})
            if lines
            else []
        )
        sections = []
        for start, stop in zip(starts, [*starts[1:], len(lines) + 1], strict=True):
            content = "\n".join(lines[start - 1 : stop - 1])
            sections.append(
                dict(
                    id=f"section-{sid}-{sha[:16]}-{start}",
                    line_start=start,
                    line_end=stop - 1,
                    heading=lines[start - 1] if lines[start - 1].startswith("#") else None,
                    interval_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    table_lines=sum(
                        line.lstrip().startswith("|") for line in lines[start - 1 : stop - 1]
                    ),
                    decision="pending",
                )
            )
        sources.append(
            dict(
                source_id=sid,
                source_sha256=sha,
                source_path=str(path),
                lines=len(lines),
                sections=sections,
            )
        )
    result = dict(
        schema_version=1,
        status="inventory_only_not_source_review",
        sources=sources,
        section_count=sum(len(s["sections"]) for s in sources),
    )
    if prior is not None and prior != result:
        raise ValueError(
            "Source or inventory selection changed; preserve the prior inventory and review migration"
        )
    if prior is None:
        workspace.mkdir(parents=True, exist_ok=True)
        write_json_atomic(destination, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bindings", type=Path, required=True, help="Protected JSON source bindings"
    )
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    from .checkout import require_checkout

    require_checkout(parser)
    # Source-bearing inventory files must stay outside the publication tree.
    from .review_workflow import REPO

    if not args.workspace.resolve().is_relative_to(REPO / "work"):
        parser.error("Historical inventories require protected work storage")
    entries = json.loads(args.bindings.read_text(encoding="utf-8"))
    result = inventory_sources(entries, args.workspace)
    print(
        json.dumps(
            dict(
                sources=len(result["sources"]),
                sections=result["section_count"],
                reviewed_sections=0,
                status=result["status"],
            )
        )
    )


if __name__ == "__main__":
    main()
