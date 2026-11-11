"""Pagination labels close their own page, including after a separator."""

import unittest

from src.publication import line_key, trailing_qa_page_nodes


class TrailingQAPageTests(unittest.TestCase):
    def nodes(self, text):
        return trailing_qa_page_nodes(text, batch_name="batch_001.md", batch_sha256="a" * 64)

    def test_closing_notes_do_not_label_the_next_page(self):
        nodes = self.nodes(
            "<!-- Batch 1 — global source-PDF pages 20–22 -->\n"
            "First page unique source sentence.\n---\n"
            "[QA: p. 7 notes. End of first page.]\n"
            "Second page unique source sentence.\n---\n"
            "[QA: p. 8 notes. End of second page.]\n"
            "Third page unique source sentence.\n---\n"
            "[QA: p. 9 notes. End of third page.]\n"
        )
        claims = {n["key"]: (n["page"], n["pdf_page"]) for n in nodes}
        self.assertEqual(claims[line_key("First page unique source sentence.")], (7, 20))
        self.assertEqual(claims[line_key("Second page unique source sentence.")], (8, 21))
        self.assertEqual(claims[line_key("Third page unique source sentence.")], (9, 22))

    def test_inline_table_qa_does_not_end_a_page(self):
        nodes = self.nodes(
            "A sentence before the source table.\n"
            "[QA: p. 17 table. Layout description.]\n"
            "A sentence after the source table.\n---\n"
            "[QA: p. 17 notes. End of page.]\n"
        )
        self.assertEqual({n["page"] for n in nodes}, {17})
        self.assertIn(line_key("A sentence after the source table."), {n["key"] for n in nodes})
        self.assertTrue(all(n["pdf_page"] is None for n in nodes))

    def test_pdf_header_requires_the_matching_number_of_pages(self):
        nodes = self.nodes(
            "<!-- Batch 1 — global source-PDF pages 20–22 -->\n"
            "Only one closed source page here.\n---\n"
            "[QA: p. 7 notes. End of page.]\n"
        )
        self.assertTrue(all(n["pdf_page"] is None for n in nodes))

    def test_explicit_page_marker_and_heading_aliases(self):
        nodes = self.nodes(
            "<!-- PDF p. 40 -->\n### A unique chapter heading\n[QA: p. 12 notes. End of page.]\n"
        )
        self.assertIn(line_key("## A unique chapter heading"), {n["key"] for n in nodes})
        self.assertEqual({n["pdf_page"] for n in nodes}, {40})

    def test_unclosed_format_is_not_guessed(self):
        with self.assertRaisesRegex(ValueError, "closing QA"):
            self.nodes("A source sentence.\n[QA: p. 12 table. Layout only.]\n")
