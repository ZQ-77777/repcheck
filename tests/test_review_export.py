import ast
import unittest

from helpers import CACHE, E1, E2
from repcheck.exporter import checklist_to_markdown, render_skeleton
from repcheck.llm.cache import MockProvider
from repcheck.pipeline import load_paper, run_spec
from repcheck.review import ExportBlockedError, apply_review, parse_user_value, progress
from repcheck.schemas import Checklist, ReviewStatus


def fresh(pdf=E1, table="Table 3"):
    return run_spec(load_paper(pdf), table, MockProvider(CACHE))


def confirm_all(c, status="confirmed"):
    for i in c.items:
        apply_review(c, i.key, status)


class ReviewTest(unittest.TestCase):
    def test_export_gate(self):
        c = fresh()
        self.assertEqual(progress(c), (0, 10))
        with self.assertRaises(ExportBlockedError):
            render_skeleton(c)
        confirm_all(c)
        self.assertTrue(c.ready_to_export())

    def test_optional_items_do_not_block(self):
        c = fresh()
        for i in c.items:
            if i.required:
                apply_review(c, i.key, "confirmed")
        self.assertTrue(c.ready_to_export())

    def test_edit_requires_value_and_overrides(self):
        c = fresh()
        with self.assertRaises(ValueError):
            apply_review(c, "model", "edited", "")
        apply_review(c, "model", "edited", "Logit")
        self.assertEqual(c.get("model").final_value(), "Logit")
        apply_review(c, "model", "confirmed")
        self.assertEqual(c.get("model").final_value(), "OLS")

    def test_parse_user_value(self):
        self.assertEqual(parse_user_value("- a\n\n• b\n", True), ["a", "b"])
        self.assertIsNone(parse_user_value("  ", False))

    def test_json_round_trip(self):
        c = fresh()
        apply_review(c, "model", "edited", "OLS with firm FE", note="checked p.3")
        c2 = Checklist.from_dict(c.to_dict())
        self.assertEqual(c2.get("model").review_status, ReviewStatus.EDITED)
        self.assertEqual(c2.get("model").user_note, "checked p.3")
        self.assertEqual(c2.items[0].evidence[0].page, c.items[0].evidence[0].page)


class ExportTest(unittest.TestCase):
    def test_skeleton_is_valid_python_and_uses_confirmed_items(self):
        c = fresh()
        confirm_all(c)
        code = render_skeleton(c)
        ast.parse(code)
        self.assertIn('"INVEST ~ COVERAGE + SIZE + LEV + MTB + CASH + ROA | firm + year"', code)
        self.assertIn("{'CRV1': 'firm'}", code)
        self.assertIn("SAMPLE_START, SAMPLE_END = 2003, 2019", code)

    def test_year_quarter_fixed_effect_is_one_term(self):
        c = fresh()
        confirm_all(c)
        apply_review(c, "fixed_effects", "edited", "firm and year-quarter fixed effects")
        self.assertIn("| firm + year_quarter", render_skeleton(c))

    def test_rejected_items_never_reach_the_skeleton(self):
        c = fresh()
        confirm_all(c)
        apply_review(c, "standard_errors", "rejected")
        apply_review(c, "controls", "rejected")
        code = render_skeleton(c)
        ast.parse(code)
        self.assertIn("TODO: standard errors not confirmed", code)
        self.assertNotIn("MTB", code)

    def test_not_in_paper_items_are_noted(self):
        c = fresh(E2, "Table 2")
        for i in c.items:
            apply_review(c, i.key, "not_in_paper" if i.value is None else "confirmed")
        code = render_skeleton(c)
        ast.parse(code)
        self.assertIn("Standard errors — not reported in the paper", code)
        self.assertIn("| year + industry", code)

    def test_markdown_marks_pending_review(self):
        md = checklist_to_markdown(fresh())
        self.assertIn("NO — pending items remain", md)
        self.assertIn("⚠️ unverified", md)


if __name__ == "__main__":
    unittest.main()
