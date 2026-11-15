import unittest

from helpers import E1
from repcheck.checklist_templates import REGRESSION_TEMPLATE, get_template
from repcheck.pdf_parser import parse_pdf
from repcheck.retriever import build_context
from repcheck.schemas import Context, Evidence, ExtractionStatus, TableTarget
from repcheck.table_locator import locate_table
from repcheck.verifier import build_item, verify_evidence

SPEC = {f.key: f for f in REGRESSION_TEMPLATE}
PAGES = {1: "Intro text about investment.",
         2: "Our sample covers fiscal years 2003 to 2019. We obtain data from Compustat.",
         3: "Standard errors are clustered at the firm level."}
CTX = Context(TableTarget("Table 3", 3, [3], "Table 3", ""), [],
              {"winsorization": [], "standard_errors": [3]})


class RetrieverTest(unittest.TestCase):
    def test_context_keeps_table_and_appendix_within_budget(self):
        pages = parse_pdf(E1)
        target = locate_table(pages, "Table 3")
        ctx = build_context(pages, target, REGRESSION_TEMPLATE, max_pages=3)
        nums = [n for n, _ in ctx.chunks]
        self.assertEqual(len(nums), 3)
        self.assertIn(4, nums)     # table page always included
        self.assertIn(5, nums)     # variable-definition appendix ranks high
        self.assertEqual(ctx.keyword_hits["winsorization"], [2])

    def test_unknown_template(self):
        with self.assertRaises(ValueError):
            get_template("nope")


class VerifierTest(unittest.TestCase):
    def test_quote_on_stated_page_is_verified(self):
        e = verify_evidence(Evidence(2, "Our sample covers fiscal years 2003 to 2019."), PAGES)
        self.assertTrue(e.verified)
        self.assertFalse(e.page_corrected)

    def test_quote_on_other_page_is_page_corrected(self):
        e = verify_evidence(Evidence(1, "Standard errors are clustered at the firm level."), PAGES)
        self.assertTrue(e.verified and e.page_corrected)
        self.assertEqual(e.page, 3)

    def test_invented_quote_is_unverified(self):
        item = build_item(SPEC["standard_errors"], {"found": True, "value": "robust",
                          "evidence": [{"page": 3, "quote": "We use White robust standard errors."}]}, PAGES, CTX)
        self.assertEqual(item.extraction_status, ExtractionStatus.UNVERIFIED)
        self.assertIn("could not be found", item.hint)

    def test_value_without_quote_is_unverified(self):
        item = build_item(SPEC["model"], {"found": True, "value": "OLS", "evidence": []}, PAGES, CTX)
        self.assertEqual(item.extraction_status, ExtractionStatus.UNVERIFIED)

    def test_missing_field_gets_hint_from_keywords_not_model(self):
        item = build_item(SPEC["standard_errors"], {"found": False}, PAGES, CTX)
        self.assertEqual(item.extraction_status, ExtractionStatus.MISSING)
        self.assertIn("p.3", item.hint)
        item = build_item(SPEC["winsorization"], {"found": True, "value": None}, PAGES, CTX)
        self.assertEqual(item.extraction_status, ExtractionStatus.MISSING)
        self.assertIn("genuinely unreported", item.hint)

    def test_list_fields_are_normalised(self):
        item = build_item(SPEC["data_sources"], {"found": True, "value": "Compustat",
                          "evidence": [{"page": 2, "quote": "We obtain data from Compustat."}]}, PAGES, CTX)
        self.assertEqual(item.value, ["Compustat"])


if __name__ == "__main__":
    unittest.main()
