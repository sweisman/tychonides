from pathlib import Path
import tempfile
import unittest

from src.release_validation import heading_anchors, validate_documentation, validate_links


class DocumentationLinkTests(unittest.TestCase):
    def test_heading_anchors_follow_the_site_generator(self):
        text = (
            "# Title\n\n## Model-comparison protocol\n\n## Done to date\n\n"
            "## Done to date\n\n### The *printed* [tables](x.md)\n\n"
            '```\n# not a heading\n```\n\n<a id="fixed"></a>\n'
        )
        self.assertEqual(
            heading_anchors(text),
            {
                "title",
                "model-comparison-protocol",
                "done-to-date",
                "done-to-date-1",
                "the-printed-tables",
                "fixed",
            },
        )

    def test_repository_links_and_anchors_resolve(self):
        validate_documentation(Path(__file__).resolve().parents[1])

    def test_missing_files_and_anchors_are_reported(self):
        with tempfile.TemporaryDirectory() as scratch:
            first, second = Path(scratch) / "a.md", Path(scratch) / "b.md"
            second.write_text("## Real heading\n", encoding="utf-8")
            first.write_text("# Top\n\n[there](b.md#real-heading) [here](#top)\n", encoding="utf-8")
            validate_links([first, second])
            first.write_text("[gone](b.md#no-such-heading)\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Broken documentation anchor"):
                validate_links([first])
            first.write_text("[gone](c.md)\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Broken local documentation link"):
                validate_links([first])


if __name__ == "__main__":
    unittest.main()
