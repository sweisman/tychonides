"""Exercise durable workflow boundaries without the external source library."""

from contextlib import ExitStack, redirect_stdout, redirect_stderr
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from src import review_workflow as workflow
from src.core import digest
from src.recovery import write_json_atomic


class WorkflowRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.work, self.public, self.source, self.benchmark = (
            self.root / name for name in ("work", "public", "source", "benchmark")
        )
        for path in (self.work, self.public, self.source, self.benchmark):
            path.mkdir()
        self.stack.enter_context(patch.object(workflow, "PUBLIC", self.public))
        self.stack.enter_context(patch.object(workflow, "REPO", self.root))
        original_counts, original_hashes = workflow.current_counts, workflow.fingerprints
        self.stack.enter_context(
            patch.object(
                workflow, "current_counts", side_effect=lambda w: original_counts(w, self.public)
            )
        )
        self.stack.enter_context(
            patch.object(
                workflow, "fingerprints", side_effect=lambda w: original_hashes(w, self.public)
            )
        )
        self.stack.enter_context(redirect_stdout(io.StringIO()))
        self.save("recovery_checkpoint.json", {"in_progress": {"review_ids": ["r1"]}})

    def save(self, name, value):
        write_json_atomic(self.work / name, value)

    def checkpoint(self):
        return workflow.read(self.work / "recovery_checkpoint.json")

    def stages(self, fail=None):
        calls = []
        targets = (
            "src.catalog.build_workspace",
            "src.coordinate_staging.build_staging",
            "src.assembly.build_assembly",
            "src.provenance.build_provenance",
            "src.public_checkpoint.build_checkpoint",
        )

        def action(name, *_):
            calls.append(name)
            if name == fail:
                raise RuntimeError("interrupted")
            base = self.public if name == "public" else self.work
            output = base / (name + ".json")
            write_json_atomic(output, {"stage": name})
            manifest = base / ("manifest.json" if name == "public" else name + "_manifest.json")
            write_json_atomic(manifest, {"output_hashes": {output.name: digest(output)}})

        for name, target in zip(workflow.STAGES, targets, strict=True):
            self.stack.enter_context(
                patch(target, side_effect=lambda *args, name=name: action(name, *args))
            )
        return calls

    def test_build_resumes_after_interruption_and_rechecks_completed_hashes(self):
        calls = self.stages(fail="assembly")
        with self.assertRaisesRegex(RuntimeError, "interrupted"):
            workflow.build(self.work, self.source, self.benchmark)
        self.assertEqual(
            self.checkpoint()["in_progress"]["completed_build_stages"],
            ["catalogue", "coordinate_staging"],
        )
        self.assertEqual(self.checkpoint()["in_progress"]["stage"], "building_assembly")
        resumed = self.stages()
        workflow.build(self.work, self.source, self.benchmark)
        self.assertEqual(resumed, ["assembly", "provenance", "public"])
        (self.work / "catalogue.json").write_text("corrupt", encoding="utf-8")
        resumed.clear()
        workflow.build(self.work, self.source, self.benchmark)
        self.assertEqual(resumed, ["catalogue"])
        self.assertEqual(calls, ["catalogue", "coordinate_staging", "assembly"])

    def test_repeat_build_runs_every_stage_and_prepared_repair_blocks_build(self):
        calls = self.stages()
        workflow.build(self.work, self.source, self.benchmark)
        calls.clear()
        workflow.build(self.work, self.source, self.benchmark, repeat=True)
        self.assertEqual(calls, list(workflow.STAGES))
        checkpoint = self.checkpoint()
        checkpoint["in_progress"]["column_repair_plan"] = {"status": "prepared"}
        self.save("recovery_checkpoint.json", checkpoint)
        calls.clear()
        with self.assertRaisesRegex(ValueError, "Resume the prepared column repair"):
            workflow.build(self.work, self.source, self.benchmark)
        self.assertEqual(calls, [])

    def verification_fixture(self):
        self.save("review_batches.json", [{"id": "r1"}])
        self.save("recovery/prior-ledger.json", [])
        self.save("recovery/prior-hashes.json", {})
        self.save("work_state.json", {"next_actions": ["Review remaining records"]})
        (self.benchmark / "raw").mkdir()
        (self.benchmark / "raw/mars.xls").write_bytes(b"fixture")
        write_json_atomic(
            self.benchmark / "workbook.json", {"sha256": digest(self.benchmark / "raw/mars.xls")}
        )
        for name in (
            "prior.jsonl",
            "staged_coordinates.jsonl",
            "derivations.jsonl",
            "contexts.jsonl",
        ):
            (self.work / name).write_text("", encoding="utf-8")
        (self.work / "inventory_spans.jsonl").write_text('{"id":"s1"}\n', encoding="utf-8")
        (self.work / "assertions.jsonl").write_text(
            '{"id":"a1","review_id":"r1"}\n', encoding="utf-8"
        )
        (self.public / "reviewed_assertions.jsonl").write_text('{"id":"a1"}\n', encoding="utf-8")
        summary = {
            "reviewed_subset": {
                "assertions": 1,
                "event_groups": 1,
                "assertions_linked_to_workbook_controls": 0,
                "assertions_without_workbook_control_links": 1,
                "unlinked_recorded_mars_declinations": {
                    "assertion_count": 1,
                    "assertion_ids": ["a1"],
                },
                "derivations": 0,
                "arithmetic_agreements": 0,
                "arithmetic_disagreements": 0,
                "quantities": {"declination": 1},
            },
            "inspection": {"inspected_candidate_spans": 1, "inspected_source_lines": 1},
            "temporal_claims": dict.fromkeys(
                (
                    "date_claims",
                    "assertions_with_source_date_claims",
                    "events_with_source_date_claims",
                    "assertions_with_multiple_source_date_claims",
                ),
                0,
            ),
        }
        write_json_atomic(self.public / "summary.json", summary)
        for name in workflow.MANIFESTS:
            self.save(name + "_manifest.json", {})
        self.save("inventory_manifest.json", {"source_hashes": {}, "benchmark_artifact_sha256": {}})
        self.save(
            "catalogue_manifest.json",
            {"summary": {"review_batches": 1, "normalization_statuses": {"exact": 1}}},
        )
        self.save(
            "assembly_manifest.json",
            {
                "summary": {
                    "catalogue_views": 1,
                    "source_contexts": 0,
                    "location_links": 1,
                    "source_anchor_statuses": {"ambiguous_literal_occurrences": 0},
                    "views_linked_to_edition_issues": 0,
                }
            },
        )
        self.save(
            "coordinate_staging_manifest.json",
            {
                "summary": dict.fromkeys(
                    (
                        "reviewed_assertion_overlaps",
                        "reviewed_coordinate_roles",
                        "coordinate_classifications",
                        "nonexcluded_coordinates_without_workbook_control",
                    ),
                    0,
                )
            },
        )
        self.refresh_public_manifest()
        checkpoint = self.checkpoint()
        checkpoint["in_progress"].update(
            review_ledger_sha256=digest(self.work / "review_batches.json"),
            prior_review_ledger_backup="recovery/prior-ledger.json",
            prior_verified_snapshot="recovery/prior-hashes.json",
            prior_public_snapshot="prior.jsonl",
        )
        self.save("recovery_checkpoint.json", checkpoint)
        before, _ = workflow.fingerprints(self.work)
        self.save("recovery/prior-hashes.json", before)

    def refresh_public_manifest(self):
        write_json_atomic(
            self.public / "manifest.json",
            {
                "output_hashes": {
                    name: digest(self.public / name)
                    for name in ("reviewed_assertions.jsonl", "summary.json")
                }
            },
        )

    def test_verified_finish_persists_counts_and_can_resume_after_completion(self):
        self.verification_fixture()
        report = workflow.check(self.work, self.source, self.benchmark, "batch")
        self.assertEqual(report["status"], "verified")
        counts = workflow.finish(self.work, "batch", tracker_sequence=7)
        self.assertEqual(counts["assertions"], 1)
        checkpoint = self.checkpoint()
        self.assertNotIn("in_progress", checkpoint)
        self.assertEqual(checkpoint["tracker_sequence"], 7)
        self.assertEqual(checkpoint["last_verified"]["assertions"], 1)
        self.assertEqual(workflow.finish(self.work, "batch", tracker_sequence=7), counts)
        self.assertIn("1 quantities", (self.work / "status.md").read_text(encoding="utf-8"))

    def test_check_rejects_changed_ledger_upstream_and_private_public_fields(self):
        self.verification_fixture()
        self.save("review_batches.json", [{"id": "different"}])
        with self.assertRaisesRegex(ValueError, "Review ledger changed"):
            workflow.check(self.work, self.source, self.benchmark, "batch")
        self.save("review_batches.json", [{"id": "r1"}])
        self.save("table_staging_manifest.json", {"changed": True})
        with self.assertRaisesRegex(ValueError, "Upstream inventory artifacts changed"):
            workflow.check(self.work, self.source, self.benchmark, "batch")
        self.save("table_staging_manifest.json", {})
        (self.public / "reviewed_assertions.jsonl").write_text(
            '{"id":"a1","private_source":"hidden"}\n', encoding="utf-8"
        )
        self.refresh_public_manifest()
        with self.assertRaisesRegex(ValueError, "Private source fields"):
            workflow.check(self.work, self.source, self.benchmark, "batch")
        self.assertFalse((self.work / "batch_workflow_verification.json").exists())

    def test_repeat_difference_and_failed_tests_cannot_mark_verified(self):
        self.verification_fixture()

        def change_output(*args, **kwargs):
            (self.public / "reviewed_assertions.jsonl").write_text(
                '{"id":"changed"}\n', encoding="utf-8"
            )

        with patch.object(workflow, "build", side_effect=change_output):
            with self.assertRaisesRegex(ValueError, "Repeated outputs differ"):
                workflow.check(self.work, self.source, self.benchmark, "batch", repeat=True)
        (self.public / "reviewed_assertions.jsonl").write_text('{"id":"a1"}\n', encoding="utf-8")
        for result, message in (
            (SimpleNamespace(returncode=1, stdout="", stderr="Failed"), "Software checks failed"),
            (SimpleNamespace(returncode=0, stdout="", stderr=""), "Missing software-check result"),
        ):
            with patch.object(workflow.subprocess, "run", return_value=result):
                with self.assertRaisesRegex(ValueError, message):
                    workflow.check(self.work, self.source, self.benchmark, "batch", tests=True)
        self.assertFalse((self.work / "batch_workflow_verification.json").exists())

    def test_repeat_and_test_evidence_are_retained_only_for_same_outputs(self):
        self.verification_fixture()
        result = SimpleNamespace(returncode=0, stdout="", stderr="Ran 3 tests\nOK")
        with (
            patch.object(workflow, "build"),
            patch.object(workflow.subprocess, "run", return_value=result),
        ):
            report = workflow.check(
                self.work, self.source, self.benchmark, "batch", repeat=True, tests=True
            )
        self.assertEqual(report["tests"]["tests_passed"], 3)
        repeated = workflow.check(self.work, self.source, self.benchmark, "batch")
        self.assertEqual(repeated["tests"], report["tests"])
        self.assertEqual(
            repeated["repeat_artifacts_identical"], report["repeat_artifacts_identical"]
        )
        self.save(
            "catalogue_manifest.json",
            {"summary": {"review_batches": 2, "normalization_statuses": {"exact": 1}}},
        )
        changed = workflow.check(self.work, self.source, self.benchmark, "batch")
        self.assertIsNone(changed["tests"])
        self.assertIsNone(changed["repeat_artifacts_identical"])

    def test_finish_rejects_post_verification_changes(self):
        self.verification_fixture()
        workflow.check(self.work, self.source, self.benchmark, "batch")
        original = (self.work / "work_state.json").read_bytes()
        self.save("catalogue_manifest.json", {"changed": True})
        with self.assertRaisesRegex(ValueError, "hash|changed|fingerprint"):
            workflow.finish(self.work, "batch")
        self.assertEqual((self.work / "work_state.json").read_bytes(), original)

    def test_cli_rejects_missing_arguments_and_inspection_path_escape(self):
        for args in (
            ["run"],
            ["append"],
            ["inspect"],
            ["refresh-source"],
            ["build", "--label", "x"],
        ):
            with (
                self.subTest(args=args),
                patch.dict("os.environ", {}, clear=True),
                patch("sys.argv", ["review", *args]),
                redirect_stderr(io.StringIO()),
            ):
                with self.assertRaises(SystemExit) as caught:
                    workflow.main()
                self.assertEqual(caught.exception.code, 2)
        args = [
            "review",
            "inspect",
            "--workspace",
            str(self.work),
            "--source-root",
            str(self.source),
            "--volume",
            "10",
            "--start",
            "1",
            "--end",
            "2",
            "--output",
            "../escape.json",
        ]
        with (
            patch("sys.argv", args),
            patch.object(workflow, "inspect_range", return_value={}),
            redirect_stderr(io.StringIO()),
        ):
            with self.assertRaises(SystemExit) as caught:
                workflow.main()
        self.assertEqual(caught.exception.code, 2)
        self.assertFalse((self.root / "escape.json").exists())
