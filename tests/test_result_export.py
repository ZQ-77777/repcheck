import tempfile
import unittest
from pathlib import Path

from helpers import ROOT  # noqa: F401  (sets sys.path)
from repcheck.comparator import load_results_csv
from repcheck.result_export import rows_from_model, write_results_csv


class StatsmodelsLike:          # attributes, like statsmodels / linearmodels results
    params = {"const": 0.5, "COVERAGE": 0.0209}
    bse = {"const": 0.1, "COVERAGE": 0.0043}
    pvalues = {"const": 0.0, "COVERAGE": 0.00001}
    nobs = 23104.0


class PyfixestLike:             # methods, like pyfixest Feols
    _N = 23104

    def coef(self):
        return {"cov": 0.0163, "SIZE": -0.003}

    def se(self):
        return {"cov": 0.004, "SIZE": 0.0014}

    def pvalue(self):
        return {"cov": 0.0001, "SIZE": 0.03}


class ResultExportTest(unittest.TestCase):
    def test_statsmodels_style_drops_intercept(self):
        rows = rows_from_model(StatsmodelsLike(), "(1)")
        self.assertEqual([r["variable"] for r in rows], ["COVERAGE"])
        self.assertEqual(rows[0]["n"], 23104)

    def test_pyfixest_style_with_rename_round_trips_through_comparator(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_results_csv({"(1)": StatsmodelsLike(), "(2)": PyfixestLike()}, Path(d) / "r.csv",
                                     rename={"cov": "COVERAGE"})
            rows = load_results_csv(path)
        self.assertEqual([(r.column, r.variable) for r in rows],
                         [("(1)", "COVERAGE"), ("(2)", "COVERAGE"), ("(2)", "SIZE")])
        self.assertAlmostEqual(rows[2].se, 0.0014)

    def test_unknown_object(self):
        with self.assertRaises(ValueError):
            rows_from_model(object(), "(1)")


    def test_esttab_csv_keeps_models_separate(self):
        from repcheck.result_export import convert_esttab_csv

        source = ROOT / "examples" / "inputs" / "f_esttab_sample.csv"
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "results.csv"
            convert_esttab_csv(source, output)
            rows = load_results_csv(output)

        actual = [
            (row.column, row.variable, row.coef, row.se, row.pvalue, row.n)
            for row in rows
        ]
        self.assertCountEqual(actual, [
            ("(1)", "COVERAGE", 0.0209, 0.0043, None, 120),
            ("(2)", "COVERAGE", -0.0163, 0.0054, None, 95),
        ])

if __name__ == "__main__":
    unittest.main()
