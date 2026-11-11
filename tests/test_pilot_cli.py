import argparse
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.__main__ import compare, write_json
from src.core import digest


def workbook_fixture(out):
    raw = out / "raw" / "mars.xls"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_bytes(b"immutable workbook fixture")
    write_json(out / "workbook.json", dict(sha256=digest(raw)))


class PilotCliTests(unittest.TestCase):
    def test_full_mode_keeps_unmatched_rows_across_volumes(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            out, source = base / "results", base / "source"
            source.mkdir()
            workbook_fixture(out)
            p = dict(
                id="Sheet1:7",
                volume=10,
                page=44,
                date="1582-03-04",
                time_key=None,
                time_original="",
                quote="9 26",
                quote_magnitude_arcsec="33960",
                arcsec="33960",
            )
            r = dict(
                id="s",
                volume=10,
                page=44,
                date="1582-03-04",
                time_key=None,
                time_original="",
                source="batch.md",
                line=1,
                pdf_page=86,
                value_original="9°26′",
                arcsec=None,
                magnitude_arcsec="33960",
                flags=["hemisphere_unresolved"],
            )
            for name, data in [
                ("pafko.json", [p, dict(p, id="Sheet1:8", volume=13)]),
                ("observations.json", [r]),
                ("source_hashes.json", {}),
            ]:
                write_json(out / name, data)
            args = argparse.Namespace(
                output=str(out), source_root=str(source), count=50, resample=False, all=True
            )
            with (
                contextlib.redirect_stdout(io.StringIO()),
                patch("src.__main__.__file__", str(base / "installed/tychonides/__main__.py")),
            ):
                compare(args)
            results = json.loads((out / "record_outcomes.json").read_text())
            self.assertEqual(len(results), 2)
            self.assertEqual(results[1]["status"], "unmatched")
            self.assertEqual(
                json.loads((out / "full_manifest.json").read_text())["selection_mode"],
                "all_workbook_rows",
            )

    def test_fixed_selection_and_persistent_review(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            out = base / "results"
            source = base / "source"
            source.mkdir()
            workbook_fixture(out)
            p = dict(
                id="Sheet1:7",
                volume=12,
                page=44,
                date="1590-03-04",
                time_key="25500",
                time_original="",
                quote="9 26",
                quote_magnitude_arcsec="33960",
                arcsec="33960",
            )
            r = dict(
                id="s",
                page=44,
                date="1590-03-04",
                time_key="25500",
                time_original="",
                source="batch.md",
                line=1,
                pdf_page=58,
                value_original="9°26′",
                arcsec=None,
                magnitude_arcsec="33960",
                flags=["hemisphere_unresolved", "column_role_unresolved"],
            )
            review = dict(
                pafko_id=p["id"],
                status="magnitude_agreement_scan_verified",
                evidence="Printed header spans both columns",
                source_record_id="s",
                resolved_flags=["column_role_unresolved"],
            )
            for name, data in [
                ("pafko.json", [dict(p, id="Sheet1:8", page=45), p]),
                ("observations.json", [r]),
                ("source_hashes.json", {}),
                ("adjudications.json", [review]),
                ("sample_manifest.json", dict(rule="fixed", records=[p])),
            ]:
                write_json(out / name, data)
            args = argparse.Namespace(
                output=str(out), source_root=str(source), count=1, resample=False
            )
            with contextlib.redirect_stdout(io.StringIO()):
                compare(args)
            result = json.loads((out / "comparison.json").read_text())[0]
            self.assertEqual(result["pafko_id"], "Sheet1:7")
            self.assertEqual(result["status"], "magnitude_agreement")
            self.assertEqual(result["source_check"], "magnitude_agreement_scan_verified")
            self.assertEqual(json.loads((out / "adjudications.json").read_text()), [review])


if __name__ == "__main__":
    unittest.main()
