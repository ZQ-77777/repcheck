import unittest

from helpers import ROOT  # noqa: F401  (sets sys.path)
from repcheck.text_utils import clean_text, normalize_for_match, number_in_text, partial_ratio


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
