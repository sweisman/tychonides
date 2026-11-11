import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.inventory import inventory_text
from src import publication, review_workflow


class SourceRevisionTests(unittest.TestCase):
    def fixture(self, base):
        root, work, public = (base / n for n in ("source", "work", "public"))
        for p in (root, work, public):
            p.mkdir()
        relative = "brahe/thesaurus_observationum_vol1/translation/brahe_thesaurus_observationum_vol1_prepub.md"
        path = root / relative
        path.parent.mkdir(parents=True)
        old = "# Book\n\nMars: 17° 20′.\n\n# Appendix\n\nLayout marker.\n"
        sha = hashlib.sha256(old.encode()).hexdigest()
        path.write_text(old)
        spans = inventory_text(old, 10, sha)["spans"]
        witness = dict(
            volume=10,
            private_source=relative,
            edition_sha256=sha,
            id=f"tycho-oo-10-prepub-{sha[:12]}",
            witness_type="final_prepub",
        )
        for name, value in {
            "witnesses.json": [witness],
            "review_batches.json": [],
            "source_reference_reviews.json": [],
            "inventory_manifest.json": dict(volumes=[10], source_hashes={relative: sha}),
            "recovery_checkpoint.json": dict(
                checkpoint_status="verified_resume_ready", last_verified={}
            ),
        }.items():
            (work / name).write_text(json.dumps(value))
        (work / "inventory_spans.jsonl").write_text("".join(json.dumps(s) + "\n" for s in spans))
        (public / "reviewed_assertions.jsonl").write_text("")
        return root, work, public, path, old, witness

    def test_layout_revision_keeps_identity_and_requires_exact_current_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root, work, public, path, old, witness = self.fixture(Path(d))
            current = old.replace("Layout marker.", "Layout marker corrected.")
            path.write_text(current)
            try:
                review_workflow.begin_source_refresh(work, root, public, 10)
            except (AttributeError, ValueError) as error:
                self.fail(f"An unchanged Mars selection must retain its identities: {error}")
            revised = json.loads((work / "witnesses.json").read_text())[0]
            self.assertEqual(revised["edition_sha256"], witness["edition_sha256"])
            self.assertEqual(revised["id"], witness["id"])
            self.assertEqual(revised["source_sha256"], hashlib.sha256(current.encode()).hexdigest())
            self.assertEqual(publication.read_witness(root, work, revised), current)
            self.assertEqual(
                review_workflow.begin_source_refresh(work, root, public, 10)["status"],
                "source_refresh_resumed",
            )
            self.assertEqual(json.loads((work / "witnesses.json").read_text())[0], revised)
            cp = json.loads((work / "recovery_checkpoint.json").read_text())
            self.assertEqual(cp["in_progress"]["operation"], "reference_inventory_refresh")
            self.assertEqual(cp["in_progress"]["review_ids"], [])
            self.assertEqual(json.loads((work / "review_batches.json").read_text()), [])
            path.write_text(current.replace("17°", "18°"))
            with self.assertRaises(ValueError):
                publication.read_witness(root, work, revised)

    def test_current_bytes_without_revision_evidence_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root, work, _public, path, old, witness = self.fixture(Path(d))
            current = old.replace("Layout marker.", "Layout marker corrected.")
            path.write_text(current)
            witness["source_sha256"] = hashlib.sha256(current.encode()).hexdigest()
            with self.assertRaises(ValueError):
                publication.read_witness(root, work, witness)

    def test_changed_reading_shifted_lines_and_new_mars_regions_cannot_rebind(self):
        for change in (
            lambda s: s.replace("17°", "18°"),
            lambda s: "\n" + s,
            lambda s: s.replace("Layout marker.", "Mars: 18° 10′."),
        ):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as d:
                root, work, public, path, old, _witness = self.fixture(Path(d))
                before = (work / "witnesses.json").read_bytes()
                path.write_text(change(old))
                with self.assertRaises(ValueError):
                    review_workflow.begin_source_refresh(work, root, public, 10)
                self.assertEqual((work / "witnesses.json").read_bytes(), before)
                self.assertEqual(
                    json.loads((work / "recovery_checkpoint.json").read_text())[
                        "checkpoint_status"
                    ],
                    "verified_resume_ready",
                )

    def test_reviewed_supporting_interval_outside_selection_must_also_match(self):
        with tempfile.TemporaryDirectory() as d:
            root, work, public, path, old, witness = self.fixture(Path(d))
            review = dict(
                id="support",
                volume=10,
                edition_sha256=witness["edition_sha256"],
                line_start=7,
                line_end=7,
                interval_sha256=hashlib.sha256(b"Layout marker.").hexdigest(),
            )
            (work / "review_batches.json").write_text(json.dumps([review]))
            path.write_text(old.replace("Layout marker.", "Changed supporting context."))
            with self.assertRaises(ValueError):
                review_workflow.begin_source_refresh(work, root, public, 10)

    def test_context_lines_outside_review_interval_cannot_change(self):
        with tempfile.TemporaryDirectory() as d:
            root, work, public, path, old, _witness = self.fixture(Path(d))
            context = dict(volume=10, lines=[7], text_original="Layout marker.")
            (work / "contexts.jsonl").write_text(json.dumps(context) + "\n")
            path.write_text(old.replace("Layout marker.", "Changed date qualification."))
            with self.assertRaises(ValueError):
                review_workflow.begin_source_refresh(work, root, public, 10)


if __name__ == "__main__":
    unittest.main()
