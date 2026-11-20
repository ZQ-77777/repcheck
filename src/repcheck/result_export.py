"""Write fitted regression models to the results CSV that the result check reads.

Dependency-free: copy this single file into any replication project, or import it from here.

    from result_export import write_results_csv
    write_results_csv({"(1)": fit1, "(2)": fit2}, "table3_results.csv",
                      rename={"capex_rev": "CAPEX_REV"})   # your names -> the paper's row labels

Works with statsmodels (params/bse/pvalues/nobs), linearmodels (params/std_errors/pvalues/nobs)
and pyfixest (coef()/se()/pvalue()/_N). Intercepts are dropped by default.
"""
from __future__ import annotations

import csv
from pathlib import Path

INTERCEPTS = {"const", "intercept", "(intercept)", "_cons"}


def _mapping(fit, *names) -> dict:
    for name in names:
        value = getattr(fit, name, None)
        if value is None:
            continue
        if callable(value):
            value = value()
        return dict(value.items()) if hasattr(value, "items") else dict(value)
    return {}


def _nobs(fit) -> int | None:
    for name in ("nobs", "_N", "n_obs"):
        value = getattr(fit, name, None)
        if value is not None:
            value = value() if callable(value) else value
            return int(round(float(value)))
    return None


def rows_from_model(fit, column: str, rename: dict | None = None, drop_intercept: bool = True) -> list[dict]:
    coef = _mapping(fit, "params", "coef")
    if not coef:
        raise ValueError(f"Cannot read coefficients from a {type(fit).__name__} object.")
    se = _mapping(fit, "bse", "std_errors", "se")
    pvalues = _mapping(fit, "pvalues", "pvalue")
    n = _nobs(fit)
    rename = rename or {}
    rows = []
    for var, b in coef.items():
        if drop_intercept and str(var).strip().lower() in INTERCEPTS:
            continue
        rows.append({"column": column, "variable": rename.get(var, var), "coef": float(b),
                     "se": "" if se.get(var) is None else float(se[var]),
                     "pvalue": "" if pvalues.get(var) is None else float(pvalues[var]),
                     "n": "" if n is None else n})
    return rows


def write_results_csv(models: dict, path: str | Path, rename: dict | None = None,
                      drop_intercept: bool = True) -> Path:
    """`models` maps the paper's column label ("(1)", "(2)", ...) to a fitted model."""
    rows = [r for column, fit in models.items() for r in rows_from_model(fit, column, rename, drop_intercept)]
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["column", "variable", "coef", "se", "pvalue", "n"])
        writer.writeheader()
        writer.writerows(rows)
    return path

def convert_esttab_csv(source: str | Path, output: str | Path) -> Path:
    """Convert a numbered esttab CSV with standard errors in parentheses."""
    with Path(source).open(encoding="utf-8-sig", newline="") as file:
        # esttab may wrap spreadsheet cells as ="value".
        reader = csv.reader(line.removeprefix("=").replace(',="', ',"') for line in file)
        rows = ([cell.strip() for cell in row] for row in reader)
        models = next((row[1:] for row in rows if row[1:2] == ["(1)"]), None)
        body = [row for row in rows if any(row)]
    if not models:
        raise ValueError("Expected numbered model columns such as (1), (2).")

    sizes = [""] * len(models)
    for row in body:
        label = row[0].lower().replace("-", " ")
        if label in {"n", "observations"}:
            sizes = row[1:]
        if label.startswith(("t statistics", "z statistics", "p values")):
            raise ValueError("Export standard errors with the esttab se option.")

    results = []
    for coefs, errors in zip(body, body[1:]):
        variable = coefs[0]
        if not variable or errors[0] or not any(s.startswith("(") for s in errors[1:]):
            continue
        for model, coef, se, n in zip(models, coefs[1:], errors[1:], sizes, strict=True):
            if coef in ("", "."):
                continue
            value = float(coef.rstrip("*").replace(",", ""))
            se = se.strip("()").replace(",", "")
            error = "" if se in ("", ".") else float(se)
            results.append((model, variable, value, error, "", n.replace(",", "")))

    if not results:
        raise ValueError("No coefficient and standard-error pairs found.")
    output = Path(output)
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["column", "variable", "coef", "se", "pvalue", "n"])
        writer.writerows(results)
    return output