import tempfile
import unittest

from helpers import CACHE, E1, E2
from repcheck.extractor import ResponseFormatError, parse_json_response
from repcheck.llm.base import LLMError, LLMProvider
from repcheck.llm.cache import CachingProvider, MockProvider
from repcheck.pipeline import load_paper, run_compare, run_spec
from repcheck.schemas import ExtractionStatus

INPUTS = E1.parent


class FakeProvider(LLMProvider):
    name = "fake"

    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def complete(self, system, user, cache_key=None):
        self.calls += 1
        return self.replies.pop(0)


class ProviderTest(unittest.TestCase):
    def test_parse_json_with_fences(self):
        self.assertEqual(parse_json_response('```json\n{"a": 1}\n```'), {"a": 1})
        with self.assertRaises(ResponseFormatError):
            parse_json_response("sorry, I cannot help")

    def test_mock_without_cache_entry_fails_clearly(self):
        with self.assertRaises(LLMError) as ctx:
            MockProvider(CACHE).complete("s", "u", "no_such_key")
        self.assertIn("no saved response", str(ctx.exception))

    def test_caching_provider_saves_and_reuses(self):
        with tempfile.TemporaryDirectory() as d:
            fake = FakeProvider(['{"x": 1}'])
            cp = CachingProvider(fake, d)
            self.assertEqual(cp.complete("s", "u", "k1"), '{"x": 1}')
            self.assertEqual(cp.complete("s", "u", "k1"), '{"x": 1}')
            self.assertEqual(fake.calls, 1)
            self.assertEqual(MockProvider(d).complete("s", "u", "k1"), '{"x": 1}')

    def test_bad_json_is_retried_once(self):
        fake = FakeProvider(["not json", '{"fields": {}}'])
        c = run_spec(load_paper(E1), "Table 3", fake)
        self.assertEqual(fake.calls, 2)
        self.assertTrue(all(i.extraction_status == ExtractionStatus.MISSING for i in c.items))


class PipelineMockTest(unittest.TestCase):
    def test_e1_end_to_end(self):
        prov = MockProvider(CACHE)
        paper = load_paper(E1)
        c = run_spec(paper, "Table 3", prov)
        status = {i.key: i.extraction_status for i in c.items}
        self.assertEqual(status["winsorization"], ExtractionStatus.UNVERIFIED)   # paraphrased quote
        self.assertTrue(c.get("unit_of_observation").evidence[0].page_corrected)  # wrong page fixed
        table, report = run_compare(paper, "Table 3", INPUTS / "e1_replication_results.csv", prov, c)
        self.assertEqual(table.unverified_numbers(), ["(2) LEV=-0.0452***"])      # misread SE caught
        kinds = {d.kind for d in report.discrepancies}
        self.assertEqual(kinds, {"n_mismatch", "significance", "magnitude", "scale", "variable_missing", "se_mismatch"})
        self.assertEqual([(d.column, d.variable) for d in report.discrepancies if d.kind == "se_mismatch"],
                         [("(2)", "MTB")])

    def test_e2_matches_and_reports_unreported_fields(self):
        prov = MockProvider(CACHE)
        paper = load_paper(E2)
        c = run_spec(paper, "TABLE II", prov)
        missing = {i.key for i in c.items if i.extraction_status == ExtractionStatus.MISSING}
        # "subsamples" was added to the template after these fixtures were recorded
        self.assertEqual(missing, {"standard_errors", "winsorization", "subsamples"})
        table, report = run_compare(paper, "II", INPUTS / "e2_replication_results.csv", prov, c)
        self.assertEqual(table.columns[0].paren_kind, "t")
        self.assertEqual(report.overall, "match")


if __name__ == "__main__":
    unittest.main()
