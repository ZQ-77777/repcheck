import unittest

from helpers import ROOT  # noqa: F401
from repcheck.comparator import ResultsFormatError, compare, load_results_csv, stars_from
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


if __name__ == "__main__":
    unittest.main()
