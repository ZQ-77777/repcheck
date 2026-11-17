"""Threshold-experiment data sets keep the properties the 90 threshold relies on."""
import unittest

from helpers import ROOT
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from repcheck.pipeline import load_paper                      # noqa: E402
from repcheck.schemas import Evidence                         # noqa: E402
from repcheck.verifier import verify_evidence                 # noqa: E402
from threshold_experiment import INVENTED, PARAPHRASED, collect_true  # noqa: E402


def _pages(pdf):
    return {p.number: p.text for p in load_paper(pdf).pages}


class ThresholdSetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pdfs = {q[0] for q in collect_true() + PARAPHRASED + INVENTED}
        cls.papers = {pdf: _pages(pdf) for pdf in pdfs}

    def test_true_quotes_are_all_accepted_at_90(self):
        quotes = collect_true()
        self.assertGreater(len(quotes), 20)
        for pdf, page, quote in quotes:
            e = verify_evidence(Evidence(page, quote), self.papers[pdf], 90.0)
            self.assertTrue(e.verified, quote)

    def test_invented_quotes_are_all_rejected_at_90(self):
        for pdf, page, quote in INVENTED:
            e = verify_evidence(Evidence(page, quote), self.papers[pdf], 90.0)
            self.assertFalse(e.verified, quote)

    def test_most_paraphrases_are_rejected_at_90(self):
        accepted = [q for pdf, page, q in PARAPHRASED
                    if verify_evidence(Evidence(page, q), self.papers[pdf], 90.0).verified]
        self.assertLessEqual(len(accepted), 2, accepted)


if __name__ == "__main__":
    unittest.main()
