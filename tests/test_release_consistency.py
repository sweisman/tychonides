from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from src import catalog_release, release_validation, vocabulary
from src.catalog_enrichment import load_registry


ROOT = Path(__file__).resolve().parents[1]


class ReleaseConsistencyTests(unittest.TestCase):
    def test_generated_references_match_all_three_committed_pages(self):
        for kind, filename in (
            ("historical", "historical-data-dictionary.md"),
            ("modern", "modern-data-dictionary.md"),
            ("normalization", "normalization-conventions.md"),
        ):
            with self.subTest(kind=kind):
                self.assertEqual(
                    (ROOT / "docs" / filename).read_text(encoding="utf-8"),
                    vocabulary.render_vocabulary(kind),
                )

    def test_generated_reference_drift_is_rejected_even_when_terms_remain(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            for name in (
                "historical-data-dictionary.md",
                "modern-data-dictionary.md",
                "normalization-conventions.md",
            ):
                shutil.copyfile(ROOT / "docs" / name, root / "docs" / name)
            vocabulary.validate_reference_pages(root)
            with (root / "docs/modern-data-dictionary.md").open("a", encoding="utf-8") as stream:
                stream.write("\nUnregistered change.\n")
            with self.assertRaisesRegex(ValueError, "Stale generated reference.*modern"):
                vocabulary.validate_reference_pages(root)

    def test_release_references_reject_each_partial_version_update(self):
        names = (
            "pyproject.toml",
            "CITATION.cff",
            "resources/catalog/manifest.json",
            "resources/catalog/README.md",
            "docs/data-workflow.md",
        )
        manifest = json.loads((ROOT / names[2]).read_text(encoding="utf-8"))
        version = manifest["release_id"].removeprefix("tychonides-")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in names:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            release_validation.validate_release_references(root)
            for name in names:
                with self.subTest(file=name):
                    target = root / name
                    original = target.read_text(encoding="utf-8")
                    target.write_text(original.replace(version, "99.0.0", 1), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "[Rr]elease"):
                        release_validation.validate_release_references(root)
                    target.write_text(original, encoding="utf-8")

    def test_installed_catalogue_command_stops_before_accessing_workspace(self):
        error = io.StringIO()
        with (
            patch("src.checkout.__file__", "/missing/site-packages/tychonides/checkout.py"),
            patch("sys.argv", ["catalog_release", "--interpretations", "input.json"]),
            patch.object(catalog_release, "build_release", return_value={}) as build,
            redirect_stderr(error),
        ):
            with self.assertRaises(SystemExit) as caught:
                catalog_release.main()
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("source checkout", error.getvalue())
        build.assert_not_called()

    def test_tycho_flat_date_identifies_original_edition(self):
        for source, record in load_registry().items():
            if source.startswith("tycho-"):
                with self.subTest(source=source):
                    self.assertEqual(record["date_kind"], "original_publication_year")
                    self.assertEqual(
                        int(record["date"]), record["original_edition"]["publication_year"]
                    )
