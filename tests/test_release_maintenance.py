import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src import release_transaction


class ReleaseTransactionTests(unittest.TestCase):
    def test_unicode_helpers_and_source_guard(self):
        from src.io import guard, write_csv, write_json

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text = "♂ 12° 3′ 4″ ſ"
            write_csv(root / "values.csv", [{"value": text}])
            write_json(root / "values.json", {"value": text})
            self.assertIn(text, (root / "values.csv").read_text(encoding="utf-8"))
            self.assertEqual(
                json.loads((root / "values.json").read_text(encoding="utf-8"))["value"], text
            )
            with self.assertRaises(ValueError):
                guard(root / "source" / "output", root / "source")

    def test_release_validator_rejects_corruption_and_pending_transaction(self):
        from test_catalog_release import CatalogueReleaseTests
        from src.catalog_release import write_catalogue
        from src.release_validation import validate_release

        source, published, contexts = CatalogueReleaseTests().fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_catalogue(root, source, published, contexts, [], [], [], [], [], [], {})
            self.assertEqual(validate_release(root)["quantities"], 2)
            (root / ".pending-release").mkdir()
            with self.assertRaisesRegex(ValueError, "incomplete"):
                validate_release(root)
            (root / ".pending-release").rmdir()
            (root / "tychonides.csv").write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError, "checksum"):
                validate_release(root)

    def test_interruption_is_detected_and_resumable(self):
        from src.core import digest

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "stage"
            output = root / "output"
            stage.mkdir()
            for name in ("tychonides.csv", "tychonides.sqlite"):
                (stage / name).write_bytes("♂ 12° ſ".encode())
            manifest = {
                "output_hashes": {
                    n: digest(stage / n) for n in ("tychonides.csv", "tychonides.sqlite")
                }
            }
            original = release_transaction.install_file

            def interrupt(source, destination):
                if destination.parent == output:
                    raise OSError("interrupted")
                original(source, destination)

            with patch.object(release_transaction, "install_file", side_effect=interrupt):
                with self.assertRaises(OSError):
                    release_transaction.publish(stage, output, manifest)
            self.assertTrue((output / ".pending-release").exists())
            release_transaction.recover(output)
            self.assertFalse((output / ".pending-release").exists())
            self.assertEqual(
                json.loads((output / "manifest.json").read_text(encoding="utf-8")), manifest
            )
            for name, checksum in manifest["output_hashes"].items():
                self.assertEqual(digest(output / name), checksum)

    def test_corrupt_pending_payload_cannot_be_promoted(self):
        from src.core import digest

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "stage"
            output = root / "output"
            stage.mkdir()
            (stage / "tychonides.csv").write_bytes(b"original")
            manifest = {"output_hashes": {"tychonides.csv": digest(stage / "tychonides.csv")}}
            original = release_transaction.install_file

            def interrupt(source, destination):
                if destination.parent == output:
                    raise OSError("interrupted")
                original(source, destination)

            with patch.object(release_transaction, "install_file", side_effect=interrupt):
                with self.assertRaises(OSError):
                    release_transaction.publish(stage, output, manifest)
            (output / ".pending-release" / "tychonides.csv").write_bytes(b"corrupt")
            with self.assertRaises(ValueError):
                release_transaction.recover(output)
