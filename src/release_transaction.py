"""Recoverable, manifest-last publication of a set of files.

A pending transaction makes the directory unverified until recovery finishes.
Readers should validate the manifest and reject pending transactions.
"""

import os
from pathlib import Path
import shutil
import tempfile
import json

from .core import digest
from .recovery import write_json_atomic, sync_directory


def install_file(source, destination):
    descriptor, temporary = tempfile.mkstemp(dir=destination.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream, source.open("rb") as incoming:
            shutil.copyfileobj(incoming, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)


def recover(output):
    output = Path(output)
    pending = output / ".pending-release"
    if not pending.exists():
        return
    manifest = json.loads((pending / "manifest.json").read_text(encoding="utf-8"))
    for name, checksum in manifest["output_hashes"].items():
        if Path(name).name != name or name in (".", "..", "manifest.json"):
            raise ValueError("Invalid transaction filename")
        if digest(pending / name) != checksum:
            raise ValueError("Pending release payload differs from manifest")
    for name in manifest["output_hashes"]:
        install_file(pending / name, output / name)
    write_json_atomic(output / "manifest.json", manifest)
    shutil.rmtree(pending)
    sync_directory(output)


def publish(staging, output, manifest):
    staging, output = Path(staging), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    recover(output)
    with tempfile.TemporaryDirectory(prefix=".prepare-release-", dir=output) as directory:
        prepared = Path(directory) / "payload"
        prepared.mkdir()
        for name, checksum in manifest["output_hashes"].items():
            if Path(name).name != name or name in (".", "..", "manifest.json"):
                raise ValueError("Invalid transaction filename")
            if digest(staging / name) != checksum:
                raise ValueError("Release payload differs from manifest")
            install_file(staging / name, prepared / name)
        write_json_atomic(prepared / "manifest.json", manifest)
        os.replace(prepared, output / ".pending-release")
        sync_directory(output)
    recover(output)
