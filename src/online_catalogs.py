"""Import public terrestrial meridian tables through shared catalog writers.

Downloads are separate inputs. Native lines, field boundaries, catalog identifiers,
time scales and published reductions remain distinct from exact unit conversions.
"""

import argparse
from collections import Counter
from contextlib import closing
from fractions import Fraction
import gzip
import json
from pathlib import Path
import re
import sqlite3

from .catalog_release import adapt_source_quantities, write_catalogue
from .checkout import require_checkout
from .core import digest
from .import_collection import merge_catalogues
from .numeric_integrity import recompute_conversion, validate_conversion
from .recovery import write_json_atomic, write_text_atomic
from .release_validation import validate_release


JPL_FILES = {
    "wash6a": "trnstswash6a.txt",
    "wash6b": "trnstswash6b.txt",
    "wash6c": "trnstswash6c.txt",
    "wash9": "trnstswash9.txt",
    "herst": "trnstsherst.txt",
    "lapalma": "trnstslplma.txt",
    "tokyo": "trnststokyo.txt",
    "bordeaux": "trnstsbordx.txt",
}
PLANETS = {
    "001": "Mercury",
    "100": "Mercury",
    "002": "Venus",
    "200": "Venus",
    "004": "Mars",
    "400": "Mars",
    "005": "Jupiter",
    "500": "Jupiter",
    "006": "Saturn",
    "600": "Saturn",
    "007": "Uranus",
    "700": "Uranus",
    "008": "Neptune",
    "800": "Neptune",
    "009": "Pluto",
    "900": "Pluto",
    "010": "Sun",
}
SATELLITES = {
    "503": "Ganymede",
    "504": "Callisto",
    "605": "Rhea",
    "606": "Titan",
    "607": "Hyperion",
    "608": "Iapetus",
    "704": "Oberon",
}
STATIONS = {
    "wash6a": "7866",
    "wash6b": "7866",
    "wash6c": "7866",
    "wash9": "7869",
    "herst": "0011",
    "lapalma": "9501",
    "tokyo": "388",
    "bordeaux": "999",
}
ORIGINS = {"1": "geocentric", "3": "geocentric", "4": "topocentric", "6": "topocentric"}

# All bounds below are zero-based, half-open, from the publishers' ReadMe files.
JPL_FIELDS = (
    ("right_ascension", 33, 42, "hhmmss_millisecond"),
    ("declination", 50, 59, "signed_ddmmss_centisecond"),
    ("recorded_epoch", 4, 16, "JPL_D12.5_UT"),
)
USNO_FIELDS = {
    "w1": (
        ("right_ascension", 8, 20, "sexagesimal_hour"),
        ("declination", 28, 40, "sexagesimal_degree"),
        ("recorded_epoch", 47, 60, "julian_day"),
        ("absolute_minus_HIP_ra", 21, 27, "second_of_time"),
        ("absolute_minus_HIP_dec", 41, 46, "arcsecond"),
    ),
    "w2": (
        ("right_ascension", 11, 23, "sexagesimal_hour"),
        ("declination", 24, 36, "sexagesimal_degree"),
        ("recorded_epoch", 37, 50, "julian_day"),
    ),
}
CDS_FIELDS = {
    "carlsberg": (
        ("recorded_epoch", 32, 46, "julian_day"),
        ("right_ascension", 50, 62, "sexagesimal_hour"),
        ("declination", 64, 76, "sexagesimal_degree"),
        ("observed_magnitude", 78, 83, "magnitude"),
    ),
    "tokyo": (
        ("recorded_epoch", 18, 32, "julian_day"),
        ("right_ascension", 48, 60, "sexagesimal_hour"),
        ("declination", 78, 90, "sexagesimal_degree"),
        ("observed_minus_computed_ra", 62, 68, "second_of_time"),
        ("phase_correction_ra", 69, 75, "second_of_time"),
        ("observed_minus_computed_dec", 92, 97, "arcsecond"),
        ("phase_correction_dec", 98, 103, "arcsecond"),
        ("observed_magnitude", 107, 112, "magnitude"),
        ("observed_minus_computed_magnitude", 114, 119, "magnitude"),
    ),
}
SCALAR_UNITS = {"julian_day", "second_of_time", "arcsecond", "magnitude"}


def text_file(path):
    path = Path(path)
    content = path.read_bytes()
    return (gzip.decompress(content) if path.suffix == ".gz" else content).decode("ascii")


def fields(line, number, common, schema):
    """Preserve literal fields and recompute only supported mechanical conversions."""
    for quantity, start, end, unit in schema:
        literal = line[start:end]
        if not literal.strip():
            continue
        row = dict(
            common,
            id=f"line:{number}:{quantity}",
            quantity=quantity,
            literal=literal,
            unit=unit,
            event_id=f"line:{number}",
            locator=f"line {number}",
            raw_line=line,
            flags=list(common.get("flags", [])),
            source_field_bounds=[start, end],
        )
        if unit in {"sexagesimal_hour", "sexagesimal_degree"}:
            parts = re.sub(r"^([+-])\s+(?=\d)", r"\1", literal.strip()).split()
            if len(parts) != 3:
                row["flags"].append("incomplete_coordinate")
        if quantity.startswith("phase_correction"):
            row["correction_status"] = "applied_as_published"
        row["normalized"] = dict(
            magnitude=str(Fraction(literal)) if unit in SCALAR_UNITS else None, unit=unit
        )
        converted = recompute_conversion(row)
        if converted is not None:
            row["derived_normalization"] = converted
        validate_conversion(row)
        yield row


def jpl_records(text, series):
    if series not in STATIONS:
        raise ValueError("Unknown JPL series")
    for number, line in enumerate(text.splitlines(), 1):
        if not line.startswith("P"):
            if line.strip() and not line.startswith(("#", "Meridian Circle")):
                raise ValueError(f"Unexpected non-record on JPL line {number}")
            continue
        target = line[1:4]
        if target not in PLANETS | SATELLITES or len(line) < 60:
            raise ValueError(f"Unrecognized JPL target or truncated line {number}")
        if line[21:25].strip() != STATIONS[series] or line[28] not in ORIGINS:
            raise ValueError(f"Unrecognized terrestrial station/type on line {number}")
        common = dict(
            subject=(PLANETS | SATELLITES)[target],
            original_target_code=target,
            platform="ground",
            technique="optical",
            role="reduction",
            coordinate_origin=ORIGINS[line[28]],
            observation_type=line[28],
            observatory_telescope_code=line[21:25],
            catalogue_code=line[25:28],
            observer_code=line[29:30],
            clamp_code=line[30:31],
            circle_code=line[31:32],
            ra_limb=line[32:33],
            dec_limb=line[49:50],
            time_scale="UT_as_documented",
            correction_history_status="requires_programme_documentation",
            flags=["reduced_position_not_original_reading", "possible_cross_publication_overlap"],
            adapter_version="meridian-tables-1",
            ra_equinox_code=line[42],
            dec_equinox_code=line[59],
            source_year=line[72:76],
            source_code=line[76:80],
        )
        yield from fields(line, number, common, JPL_FIELDS)


def usno_records(text, programme):
    schema = USNO_FIELDS[programme]
    w1 = programme == "w1"
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        subject = line[: 7 if w1 else 10].strip()
        telescope = '6"' if w1 else line[61:63]
        if not subject or telescope not in {'6"', '7"'} or len(line) < (60 if w1 else 63):
            raise ValueError(f"Malformed USNO row {number}")
        common = dict(
            subject=subject,
            original_target_identifier=subject,
            platform="ground",
            technique="optical",
            role="reduction",
            coordinate_origin="geocentric",
            coordinate_frame="true_equator_equinox_of_date",
            reduction_system="Hipparcos",
            site="Washington" if telescope == '6"' else "Black Birch",
            telescope=telescope,
            observer=line[61:63] if w1 else line[51:54],
            clamp_code=line[64:65] if w1 else line[55:56],
            ra_limb=line[66:67] if w1 else line[57:58],
            dec_limb=line[68:69] if w1 else line[59:60],
            time_scale="UT1",
            adapter_version="meridian-tables-1",
            position_endpoint="published_geocentric_position",
            corrections=[
                dict(
                    kind="horizontal_parallax_declination",
                    status="applied",
                    reference="https://arxiv.org/abs/1605.09780",
                    printed_page=42 if w1 else 83,
                )
            ],
            flags=["reduced_not_raw", "possible_cross_publication_overlap"],
        )
        yield from fields(line, number, common, schema)


def cds_records(text, catalogue):
    schema = CDS_FIELDS[catalogue]
    carlsberg = catalogue == "carlsberg"
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        name = line[18:30].strip() if carlsberg else line[:12].strip()
        if not name or len(line) < (76 if carlsberg else 103):
            raise ValueError(f"Malformed CDS row {number}")
        mp = line[12:16].strip() if carlsberg else None
        subject = f"({int(mp)}) {name}" if mp else name
        if not carlsberg:
            subject = name.title() if name.isupper() else name
        common = dict(
            subject=subject,
            original_target_identifier=name,
            platform="ground",
            technique="photoelectric",
            role="reduction",
            site="La Palma" if carlsberg else "Tokyo",
            coordinate_origin="topocentric" if name == "Geographos" else "geocentric",
            coordinate_frame="true_equator_equinox_of_date",
            reduction_system="IAU_1976" if carlsberg else "FK5",
            time_scale="TT" if carlsberg else "UT1",
            adapter_version="meridian-tables-1",
            flags=["reduced_not_raw", "possible_cross_publication_overlap"],
            correction_history_status="published_reductions",
        )
        if carlsberg:
            common.update(
                camc_object_code=line[1:8],
                minor_planet_number=mp or None,
                source_quality_flag=line[46:47],
            )
            if line[46:47] == "*":
                common["flags"].append("source_internal_error_above_0.75_arcsecond")
            common["corrections"] = [
                dict(
                    kind="parallax_declination",
                    status="not_applied" if name == "Geographos" else "applied",
                    reference="https://cdsarc.cds.unistra.fr/viz-bin/cat/I/256",
                )
            ]
        else:
            common.update(source_sequence_number=line[12:16], source_calendar_date=line[34:44])
        yield from fields(line, number, common, schema)


def input_tables(raw):
    for series, filename in JPL_FILES.items():
        yield (
            f"jpl-{series}",
            raw / f"jpl-{series}.txt",
            jpl_records,
            series,
            ("https://ssd.jpl.nasa.gov/dat/planets/" + filename),
        )
    for programme in ("w1", "w2"):
        yield (
            f"usno-{programme}",
            raw / f"usno-{programme}.txt",
            usno_records,
            programme,
            (f"https://vizier.cfa.harvard.edu/ftp/cats/I/334/{programme}j00sol.dat"),
        )
    for catalogue, code, filename in (
        ("carlsberg", "256", "planet.dat"),
        ("tokyo", "188", "planets"),
    ):
        yield (
            f"cds-{catalogue}-planets",
            raw / f"cds-{catalogue}-planets.gz",
            cds_records,
            catalogue,
            (f"https://vizier.cfa.harvard.edu/ftp/cats/I/{code}/{filename}.gz"),
        )


def run(workspace, base, *, repeat=False):
    """Stage whole tables, skip preserved entries and merge one substantial bundle."""
    from .import_collection import WORK_ROOT

    workspace, base = Path(workspace).resolve(), Path(base).resolve()
    if not workspace.is_relative_to(WORK_ROOT.resolve()):
        raise ValueError("Online acquisition requires protected working storage")
    workspace.mkdir(parents=True, exist_ok=True)
    checkpoint_path = workspace / "recovery_checkpoint.json"
    checkpoint = (
        json.loads(checkpoint_path.read_text(encoding="utf-8")) if checkpoint_path.exists() else {}
    )
    base_manifest_hash = digest(base / "manifest.json")
    signature = dict(
        base_manifest_sha256=base_manifest_hash,
        raw_hashes={p.name: digest(p) for _, p, _, _, _ in input_tables(workspace / "raw")},
        engine_hashes={
            name: digest(Path(__file__).with_name(name))
            for name in (
                "online_catalogs.py",
                "numeric_integrity.py",
                "catalog_release.py",
                "csv_projection.py",
                "import_collection.py",
            )
        },
    )
    reusable = checkpoint.get("input_signature") == signature
    if reusable and checkpoint.get("stage") in {"merged_verified", "complete"}:
        validate_release(Path(checkpoint.get("catalogue_path", workspace / "combined")))
        return checkpoint
    if reusable and checkpoint.get("stage") == "additional_verified":
        return finish_merge(workspace, base, checkpoint)
    previous_tables = checkpoint.get("tables", {}) if reusable else {}
    checkpoint.update(
        stage="preparing", base_manifest_sha256=base_manifest_hash, input_signature=signature
    )
    write_json_atomic(checkpoint_path, checkpoint)
    all_rows, source_records, artifacts = [], [], []
    inventory = {}
    with closing(
        sqlite3.connect((base / "tychonides.sqlite").as_uri() + "?mode=ro", uri=True)
    ) as db:
        prior = {
            (sid, artifact, local): expression
            for sid, artifact, local, expression in db.execute(
                "SELECT source_id,artifact_sha256,source_entry_id,expression FROM quantities "
                "WHERE artifact_sha256 IS NOT NULL"
            )
        }
        for sid, path, parser, argument, url in input_tables(workspace / "raw"):
            checksum = digest(path)
            staged = workspace / "prepared" / (sid + ".jsonl")
            saved = previous_tables.get(sid)
            if saved and staged.exists() and digest(staged) == saved["prepared_sha256"]:
                records = [
                    json.loads(line) for line in staged.read_text(encoding="utf-8").splitlines()
                ]
                inventory[sid] = saved
            else:
                native = list(parser(text_file(path), argument))
                records, preserved = [], 0
                for row in native:
                    key = (sid, checksum, row["id"])
                    if key in prior:
                        if prior[key] != row["literal"]:
                            raise ValueError(
                                "Previously imported native expression changed: " + str(key)
                            )
                        preserved += 1
                        continue
                    records.append(dict(row, source_id=sid, artifact_sha256=checksum))
                write_text_atomic(
                    staged,
                    "".join(
                        json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records
                    ),
                )
                inventory[sid] = dict(
                    source_url=url,
                    artifact_sha256=checksum,
                    source_records=len({r["event_id"] for r in native}),
                    source_quantities=len(native),
                    preserved_quantities=preserved,
                    added_quantities=len(records),
                    targets=dict(
                        Counter(r["subject"] for r in native if r["quantity"] == "recorded_epoch")
                    ),
                    prepared_sha256=digest(staged),
                )
                del native
            existing_source = db.execute(
                "SELECT data_json FROM sources WHERE id=?", (sid,)
            ).fetchone()
            source_records.append(
                json.loads(existing_source[0]) if existing_source else dict(id=sid, url=url)
            )
            existing_artifact = db.execute(
                "SELECT metadata_json,content FROM artifacts WHERE source_id=? AND sha256=?",
                (sid, checksum),
            ).fetchone()
            if existing_artifact:
                artifacts.append(
                    dict(json.loads(existing_artifact[0]), content=existing_artifact[1])
                )
            else:
                artifacts.append(
                    dict(
                        source_id=sid,
                        sha256=checksum,
                        media_type="application/gzip" if path.suffix == ".gz" else "text/plain",
                        redistribution_status="source_terms_apply_reference_only",
                        content=path.read_bytes(),
                    )
                )
            all_rows.extend(records)
            checkpoint.update(
                stage="preparing",
                tables=inventory,
                next_action="prepare remaining tables, then export bundle",
            )
            write_json_atomic(checkpoint_path, checkpoint)
    source, public, groups = adapt_source_quantities(all_rows)
    del all_rows
    checkpoint.update(
        stage="prepared",
        added_quantities=len(source),
        added_groups=len(groups),
        next_action="write additional catalog, then merge with preserved baseline",
    )
    write_json_atomic(checkpoint_path, checkpoint)
    additional = workspace / "catalogue"

    def build(output):
        result = write_catalogue(
            output,
            source,
            public,
            [],
            groups,
            [],
            [],
            [],
            source_records,
            [],
            {},
            artifacts=artifacts,
        )
        validate_release(output)
        return result

    manifest = build(additional)
    if repeat:
        import tempfile

        with tempfile.TemporaryDirectory(prefix="repeat-", dir=workspace) as temporary:
            if build(Path(temporary))["output_hashes"] != manifest["output_hashes"]:
                raise ValueError("Repeated additional catalog exports differ")
    checkpoint.update(
        stage="additional_verified",
        repeated_outputs_identical=repeat,
        next_action="merge additional catalog into combined catalog",
    )
    write_json_atomic(checkpoint_path, checkpoint)
    return finish_merge(workspace, base, checkpoint)


def finish_merge(workspace, base, checkpoint):
    combined = workspace / "combined"
    merged = merge_catalogues(base, workspace / "catalogue", combined)
    checkpoint.update(
        stage="merged_verified",
        combined_quantities=merged["quantities"],
        combined_groups=merged["groups"],
        combined_manifest_sha256=digest(combined / "manifest.json"),
        next_action="prepare public projection and update coverage documentation",
    )
    write_json_atomic(workspace / "recovery_checkpoint.json", checkpoint)
    return checkpoint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path("work/online-catalogues"))
    parser.add_argument("--base", type=Path, default=Path("work/combined-catalogue/expanded"))
    parser.add_argument("--repeat", action="store_true")
    args = parser.parse_args()
    require_checkout(parser)
    print(json.dumps(run(args.workspace, args.base, repeat=args.repeat), indent=2))


if __name__ == "__main__":
    main()
