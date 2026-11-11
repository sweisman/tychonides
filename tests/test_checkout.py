import argparse
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.checkout import require_checkout


class CheckoutTests(unittest.TestCase):
    def test_installed_processing_command_reports_checkout_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            error = io.StringIO()
            with (
                patch("src.checkout.__file__", str(Path(directory) / "tychonides/checkout.py")),
                contextlib.redirect_stderr(error),
            ):
                with self.assertRaises(SystemExit) as caught:
                    require_checkout(argparse.ArgumentParser())
            self.assertEqual(caught.exception.code, 2)
            self.assertIn("source checkout", error.getvalue())
            self.assertNotIn("Traceback", error.getvalue())

    def test_source_checkout_remains_usable(self):
        self.assertEqual(
            require_checkout(argparse.ArgumentParser()), Path(__file__).resolve().parents[1]
        )
