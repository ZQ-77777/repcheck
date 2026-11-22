import unittest

from helpers import ROOT  # noqa: F401  (sets sys.path)
from repcheck.text_utils import (clean_text, normalize_for_match, number_in_text,
                                 partial_ratio, quote_context)


class QuoteContextTest(unittest.TestCase):
    PAGE = ("Sample selection.  To mitigate outliers, all continuous variables are winsorized\n"
            "at the 1st and 99th percentiles. Firms are ranked on continu-\nous closing spreads.")

    def test_marks_the_matched_span(self):
        out = quote_context(self.PAGE, "variables are winsorized at the 1st")
        self.assertIsNotNone(out)
        self.assertIn("[[", out) and self.assertIn("]]", out)
        matched = out.split("[[", 1)[1].split("]]", 1)[0]
        self.assertEqual(normalize_for_match(matched), normalize_for_match("variables are winsorized at the 1st"))

    def test_window_is_about_200_characters(self):
        long_page = " ".join(f"word{i}" for i in range(200))
        out = quote_context(long_page, "word100 word101 word102", width=200)
        self.assertLessEqual(len(out.replace("[[", "").replace("]]", "")), 320)

    def test_matches_quotes_with_ligatures_and_curly_quotes(self):
        page = "The ﬁrm’s leverage is measured as total debt over assets."
        self.assertIsNotNone(quote_context(page, "firm's leverage is measured"))

    def test_matches_quote_across_a_hyphenated_line_break(self):
        out = quote_context(self.PAGE, "continuous closing spreads")
        self.assertIsNotNone(out)
        self.assertIn("continu-", out)          # the page text is shown as printed
        self.assertIn("]]", out)

    def test_matches_tightly_spaced_text(self):
        page = "Thedependentvariableiscapexadjustments(CAPEX_ADJ)definedasthepercentagedeviation"
        out = quote_context(page, "dependent variable is capex adjustments")
        self.assertIsNotNone(out)

    def test_returns_none_for_an_absent_quote(self):
        self.assertIsNone(quote_context(self.PAGE, "the CEO is paid in bitcoin"))


class TextUtilsTest(unittest.TestCase):
    def test_clean_text_replaces_ligatures_quotes_and_minus(self):
        self.assertEqual(clean_text("ﬁrm’s \u22120.5"), "firm's -0.5")

    def test_normalize_joins_hyphenated_line_breaks(self):
        self.assertEqual(normalize_for_match("continu-\nous   variables"), "continuous variables")

    def test_partial_ratio_exact_and_paraphrase(self):
        page = "To mitigate outliers, all continuous variables are winsorized at the 1st and 99th percentiles."
        self.assertEqual(partial_ratio("variables are winsorized at the 1st and 99th", page), 100.0)
        self.assertLess(partial_ratio("variables are trimmed at 5% to remove outliers", page), 90)

    def test_partial_ratio_ignores_lost_word_spaces(self):
        page = "Thedependentvariableiscapexadjustments(CAPEX_ADJ)definedasthepercentagedeviation"
        self.assertEqual(partial_ratio("The dependent variable is capex adjustments (CAPEX_ADJ)", page), 100.0)
        self.assertLess(partial_ratio("The dependent variable is investment growth", page), 90)

    def test_number_in_text_respects_sign_and_tokens(self):
        text = "LEV -0.0452*** -0.0398***\n(0.0087) (0.0085)\nObservations 24,318"
        self.assertTrue(number_in_text("-0.0452***", text))
        self.assertFalse(number_in_text("0.0452", text))        # sign dropped by the model
        self.assertTrue(number_in_text("(0.0087)", text))
        self.assertFalse(number_in_text("(0.0078)", text))      # transposed digits
        self.assertTrue(number_in_text("24318", text))          # thousands separator dropped
        self.assertFalse(number_in_text("0.045", text))         # prefix of a longer number


if __name__ == "__main__":
    unittest.main()
