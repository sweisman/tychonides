"""Shared text output and read-only source guards."""

import csv
import json
import os
import io
from pathlib import Path
from .recovery import write_json_atomic, write_text_atomic


def write_json(path, data):
    write_json_atomic(path, data)


def write_csv(path, rows):
    if not rows:
        write_text_atomic(path, "")
        return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with io.StringIO(newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                    for k, v in row.items()
                }
            )
        write_text_atomic(path, f.getvalue())


def guard(output, source_root):
    roots = [source_root]
    if os.environ.get("TYCHONIDES_SOURCE_ROOT"):
        roots.append(Path(os.environ["TYCHONIDES_SOURCE_ROOT"]))
    if any(output.resolve().is_relative_to(root.resolve()) for root in roots):
        raise ValueError("Output must be outside the read-only source repository")
