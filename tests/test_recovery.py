import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.__main__ import write_json


class RecoveryWriteTests(unittest.TestCase):
    def test_interruption_before_replace_preserves_the_previous_checkpoint(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "checkpoint.json"
            target.write_text('{"stage":"verified"}\n')
            with patch("os.replace", side_effect=OSError("interrupted")):
                with self.assertRaises(OSError):
                    write_json(target, dict(stage="new"))
            self.assertEqual(json.loads(target.read_text()), dict(stage="verified"))
            self.assertEqual(list(Path(root).iterdir()), [target])

    def test_invalid_payload_does_not_damage_an_existing_checkpoint(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "checkpoint.json"
            target.write_text("{}\n")
            with self.assertRaises(TypeError):
                write_json(target, dict(stage=object()))
            self.assertEqual(target.read_text(), "{}\n")

    def test_successful_atomic_write_preserves_the_existing_json_format(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "nested" / "checkpoint.json"
            payload = dict(stage="verified", fraction="⅓")
            write_json(target, payload)
            self.assertEqual(
                target.read_text(), json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
            )
