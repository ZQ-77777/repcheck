import tempfile
import unittest
from pathlib import Path

from helpers import E1, E2, ROOT, SCANNED
from repcheck.pdf_parser import InvalidPDFError, ScannedPDFError, parse_pdf
from repcheck.schemas import Page
from repcheck.table_locator import TableNotFoundError, list_tables, locate_table, parse_label


class ParserTest(unittest.TestCase):
    def test_text_pdf_pages_are_numbered_from_one(self):
        pages = parse_pdf(E1)
        self.assertEqual([p.number for p in pages], [1, 2, 3, 4, 5])
        self.assertIn("Our sample covers fiscal years 2003 to 2019", pages[1].text)

    def test_scanned_pdf_is_rejected(self):
        with self.assertRaises(ScannedPDFError):
            parse_pdf(SCANNED)

    def test_non_pdf_is_rejected(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"this is not a pdf")
        with self.assertRaises(InvalidPDFError):
            parse_pdf(f.name)
        Path(f.name).unlink()


class LocatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e1, cls.e2 = parse_pdf(E1), parse_pdf(E2)

    def test_label_formats(self):
        for label in ("Table 3", "3", "table III", "iii", " TABLE 3 "):
            self.assertEqual(parse_label(label), 3)
        with self.assertRaises(ValueError):
            parse_label("third table")

    def test_caption_beats_prose_mention(self):
        # p.3 has a line starting "Table 3 presents ..."; the caption is on p.4
        t = locate_table(self.e1, "Table 3")
        self.assertEqual(t.pages, [4])
        self.assertIn("Analyst Coverage", t.caption)
        self.assertIn("clustered by firm", t.notes)

    def test_roman_numeral_caption(self):
        t = locate_table(self.e2, "2")
        self.assertEqual(t.pages, [3])
        self.assertTrue(t.caption.startswith("TABLE II"))

    def test_missing_table_lists_alternatives(self):
        with self.assertRaises(TableNotFoundError) as ctx:
            locate_table(self.e1, "Table 9")
        self.assertEqual(ctx.exception.available, ["Table 2", "Table 3"])

    def test_caption_spacing_variants(self):
        for caption in ("Table3", "T able 3", "T A B L E 3", "TABLE 3."):
            pages = [Page(1, f"{caption}\nResults\nA 0.1 0.2 0.3 1 2 3\nThis table reports x.")]
            self.assertEqual(locate_table(pages, "3").pages, [1], caption)

    def test_continued_table_spans_pages(self):
        pages = [Page(1, "Table 4\nResults\nA 0.1 0.2 0.3 1 2 3 4 5 6\nThis table reports x."),
                 Page(2, "Table 4 (continued)\nB 0.4 0.5 0.6 7 8 9\nNotes: more")]
        self.assertEqual(locate_table(pages, "4").pages, [1, 2])
        self.assertEqual(list_tables(pages), ["Table 4"])


if __name__ == "__main__":
    unittest.main()


class TightSpacingTest(unittest.TestCase):
    """Tables typeset without space characters between words (seen in a real RFS article)."""

    def test_words_are_separated_and_table_is_found(self):
        from helpers import ROOT
        from repcheck.verifier import verify_evidence
        from repcheck.schemas import Evidence
        pages = parse_pdf(ROOT / "tests" / "fixtures" / "tight_spacing.pdf")
        text = pages[0].text
        self.assertIn("The dependent variable is capex adjustments", text)
        self.assertIn("Normal body text with ordinary word spacing", text)   # body text unchanged
        self.assertEqual(locate_table(pages, "3").pages, [1])
        ev = verify_evidence(Evidence(1, "Robust standard errors clustered by industry."), {1: text})
        self.assertTrue(ev.verified)


class RotatedTablePageTest(unittest.TestCase):
    """Wide tables printed sideways: the reader turns the page, pdfplumber returns one word per line.

    Real RFS articles print some regression tables this way. Before the re-flow in `pdf_parser.py`,
    the caption "TABLE 4" came out as "4\\nELBAT" (or one word per line), so the table was invisible.
    Fixture: `scripts/make_fixtures.py` (p.1 content rotated 90° plus an upright banner and a 270°
    sidebar, p.2 /Rotate 90, p.3 upright). The mixed angles on p.1 are what a real RFS page has.
    """

    @classmethod
    def setUpClass(cls):
        cls.pages = parse_pdf(ROOT / "tests" / "fixtures" / "rotated_tables.pdf")

    def test_caption_in_rotated_block_is_found(self):
        target = locate_table(self.pages, "4")
        self.assertEqual(target.pages, [1])
        self.assertTrue(target.caption.startswith("TABLE 4"))
        self.assertIn("OLS", target.notes)

    def test_page_rotation_attribute_is_found(self):
        # Same failure, produced with /Rotate 90 instead of a rotated text block.
        self.assertEqual(locate_table(self.pages, "5").pages, [2])

    def test_upright_control_page_is_unchanged(self):
        self.assertEqual(locate_table(self.pages, "6").pages, [3])
        self.assertIn("The dependent variable is CAR", self.pages[2].text)
        self.assertEqual(list_tables(self.pages), ["Table 4", "Table 5", "Table 6"])

    def test_rotated_text_is_reflowed_in_reading_order(self):
        text = self.pages[0].text
        self.assertIn("4. Results", text)
        self.assertIn("Notes: This table reports OLS estimates.", text)
        self.assertNotIn("ELBAT", text)
        # The upright banner is re-flowed on its own axes, not projected onto the table's.
        self.assertIn("Page: 3870", text)
        self.assertTrue(text.rstrip().endswith("Page: 3870 3854-3888"))

    def test_missing_caption_points_to_the_prose_mention(self):
        pages = [Page(1, "1. Introduction\nWe study peers."),
                 Page(2, "Table 4 reports the robustness checks.\nA 0.1 0.2 0.3 4 5 6")]
        with self.assertRaises(TableNotFoundError) as ctx:
            locate_table(pages, "4")
        self.assertEqual(ctx.exception.mentions, [2])
        self.assertIn("image", str(ctx.exception))
