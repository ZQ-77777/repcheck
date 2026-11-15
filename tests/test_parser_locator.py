import tempfile
import unittest
from pathlib import Path

from helpers import E1, E2, SCANNED
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
