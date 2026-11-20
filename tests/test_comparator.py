import unittest

from helpers import ROOT  # noqa: F401
from repcheck.comparator import ResultsFormatError, compare, load_results_csv, stars_from
from repcheck.exporter import report_to_markdown
from repcheck.schemas import PaperTable, ResultRow, TableCell, TableColumn


def cell(var, coef, stars=3):
    return TableCell(var, f"{coef}{'*' * stars}", None, coef, None, stars, True)


PAPER = PaperTable("Table 1", "test", [TableColumn("(1)", "Y", "se", "1,000", 1000, True, [
    cell("A", 0.50), cell("B", -0.20), cell("C", 0.03), cell("D", 1.00), cell("E", 0.10), cell("F", 0.40)])])


def kinds(report):
    return {(d.variable, d.kind) for d in report.discrepancies}


class ComparatorTest(unittest.TestCase):
    def test_exact_replication_matches(self):
        rows = [ResultRow("(1)", v, c, pvalue=0.001, n=1000)
                for v, c in [("A", .5), ("B", -.2), ("C", .03), ("D", 1.0), ("E", .1), ("F", .4)]]
        r = compare(PAPER, rows)
        self.assertEqual(r.overall, "match")
        self.assertEqual((r.matched_cells, r.total_cells), (6, 6))

    def test_each_discrepancy_type(self):
        rows = [ResultRow("(1)", "A", 0.51, pvalue=0.001, n=900),   # N differs
                ResultRow("(1)", "B", 0.20, pvalue=0.001, n=900),   # sign flip
                ResultRow("(1)", "C", 3.0, pvalue=0.001, n=900),    # x100 scale
                ResultRow("(1)", "D", 0.70, pvalue=0.001, n=900),   # 30% magnitude
                ResultRow("(1)", "E", 0.10, pvalue=0.04, n=900)]    # ** instead of ***; F missing
        k = kinds(compare(PAPER, rows))
        self.assertEqual(k, {(None, "n_mismatch"), ("B", "sign_flip"), ("C", "scale"),
                             ("D", "magnitude"), ("E", "significance"), ("F", "variable_missing")})

    def test_stars_from_t_when_no_pvalue(self):
        self.assertEqual(stars_from(None, 2.0), 2)
        self.assertEqual(stars_from(None, -3.0), 3)
        self.assertEqual(stars_from(0.2, None), 0)
        self.assertIsNone(stars_from(None, None))

    def test_missing_column(self):
        r = compare(PAPER, [ResultRow("(2)", "A", 0.5)])
        self.assertEqual(r.discrepancies[0].kind, "column_missing")

    def test_csv_loading_and_errors(self):
        rows = load_results_csv("column,variable,coef,se,n\n1,A,0.5,0.1,1000\n(2),B,-1,,\n")
        self.assertEqual([r.column for r in rows], ["(1)", "(2)"])
        self.assertIsNone(rows[1].se)
        with self.assertRaises(ResultsFormatError):
            load_results_csv("model,var\n1,A\n")
        with self.assertRaises(ResultsFormatError):
            load_results_csv("column,variable,coef\n1,A,abc\n")

    def test_se_mismatch_with_matching_coefficient(self):
        entry = TableCell("COVERAGE", "0.50***", "(0.10)", 0.50, 0.10, 3, True)
        column = TableColumn("(1)", "Y", "se", "1000", 1000, True, [entry])
        paper = PaperTable("Table 1", "test", [column])
        row = ResultRow("(1)", "COVERAGE", 0.50, se=0.14, n=1000)

        report = compare(paper, [row])
        self.assertIn(("COVERAGE", "se_mismatch"), kinds(report))

    def test_cross_column_scale_summarizes_the_variable_once(self):
        paper = PaperTable("Table 1", "test", [
            TableColumn("(1)", "Y", "none", None, None, False, [cell("CASH", 0.02)]),
            TableColumn("(2)", "Y", "none", None, None, False, [cell("SIZE", 1.0)]),
            TableColumn("(3)", "Y", "none", None, None, False, [cell("cash", -0.05)]),
        ])
        for factor in (100, 0.01, 2):
            with self.subTest(factor=factor):
                rows = [ResultRow("(3)", "Cash", -0.05 * factor),
                        ResultRow("(2)", "SIZE", 1.0),
                        ResultRow("(1)", "cash", 0.02 * factor)]
                report = compare(paper, rows)
                summaries = [d for d in report.discrepancies if d.kind == "cross_column_scale"]
                self.assertEqual(len(summaries), 1)
                summary = summaries[0]
                self.assertEqual((summary.variable, summary.column), ("CASH", "(1), (3)"))
                self.assertIn(f"{factor:g} times", summary.message)
                self.assertIn("units", summary.message.lower())
                self.assertIn("controls", summary.suspects)
                self.assertEqual((report.matched_cells, report.total_cells), (1, 3))
                self.assertEqual(len(report.discrepancies), 3)  # two individual findings plus the summary
                self.assertIn("**Consistent scaling across models**", report_to_markdown(report))

    def test_cross_column_scale_requires_consistent_evidence_in_every_model(self):
        paper = PaperTable("Table 1", "test", [
            TableColumn(label, "Y", "none", None, None, False, [cell("CASH", 1.0)])
            for label in ("(1)", "(2)", "(3)")
        ])
        for factors, expected in [
            ((100, 103, 105), True),       # largest factor is within 5% of the smallest
            ((100, 103, 106), False),
            ((100, 100, 1), False),        # one column already matches
            ((100, 100, -100), False),     # sign reversal
            ((100, 100, 0), False),
            ((100, 100), False),           # missing model
            ((1.05, 1.05, 1.05), False),   # within the ordinary matching tolerance
        ]:
            with self.subTest(factors=factors):
                rows = [ResultRow(col.label, "CASH", value) for col, value in zip(paper.columns, factors)]
                self.assertEqual(("CASH", "cross_column_scale") in kinds(compare(paper, rows)), expected)

        rows = [ResultRow(col.label, "CASH", 100) for col in paper.columns]
        paper.columns[-1].cells[0].verified = False
        self.assertNotIn(("CASH", "cross_column_scale"), kinds(compare(paper, rows)))

if __name__ == "__main__":
    unittest.main()
