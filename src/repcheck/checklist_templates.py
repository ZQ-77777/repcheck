"""Checklist templates: which fields a replication of one table needs.

Extension point: add a new template (e.g. "ml_experiment": dataset, preprocessing,
model, hyper-parameters, metrics) to TEMPLATES. Retriever, extractor, verifier and UI
read the template, so no other module has to change.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    required: bool
    description: str            # sent to the model
    where: str                  # where papers usually report it (used in hints)
    is_list: bool = False
    keywords: tuple = field(default_factory=tuple)   # used by the retriever and hints


REGRESSION_TEMPLATE: list[FieldSpec] = [
    FieldSpec("sample_period", "Sample period", True,
              "Years (or dates) covered by the sample used in this table.",
              "the Data/Sample section",
              keywords=("sample period", "sample covers", "sample spans", "fiscal years", "sample consists")),
    FieldSpec("data_sources", "Data sources", True,
              "Databases used (e.g. Compustat, CRSP, I/B/E/S, BoardEx).",
              "the Data/Sample section", is_list=True,
              keywords=("compustat", "crsp", "i/b/e/s", "ibes", "boardex", "execucomp", "audit analytics", "we obtain", "database")),
    FieldSpec("sample_filters", "Sample filters", True,
              "Each sample selection step, e.g. excluded industries, required non-missing data, minimum size.",
              "the Data/Sample section or a sample-selection table", is_list=True,
              keywords=("exclude", "we require", "non-missing", "financial firms", "utilities", "sic", "drop", "final sample")),
    FieldSpec("unit_of_observation", "Unit of observation", True,
              "Level of one observation, e.g. firm-year, firm-quarter, deal.",
              "the Data section or the table notes",
              keywords=("firm-year", "firm-quarter", "observations", "observation")),
    FieldSpec("dependent_var", "Dependent variable", True,
              "Dependent variable of this table, formatted 'NAME: definition'.",
              "the research design section and the variable-definition appendix",
              keywords=("dependent variable", "is defined as", "measured as", "appendix")),
    FieldSpec("key_independent_vars", "Key independent variable(s)", True,
              "Variables of interest, each formatted 'NAME: definition'.",
              "the hypothesis/research design section and the appendix", is_list=True,
              keywords=("variable of interest", "independent variable", "is defined as", "measured as")),
    FieldSpec("controls", "Control variables", True,
              "Every control variable in this table, each formatted 'NAME: definition'.",
              "the variable-definition appendix and the table itself", is_list=True,
              keywords=("control", "controls", "variable definitions", "appendix")),
    FieldSpec("fixed_effects", "Fixed effects", True,
              "Fixed effects included in this table (e.g. firm and year).",
              "the research design section or the bottom rows of the table",
              keywords=("fixed effect", "fixed-effect", " fe")),
    FieldSpec("standard_errors", "Standard errors", True,
              "How standard errors are computed or clustered.",
              "the table notes or the research design section",
              keywords=("cluster", "robust", "heteroskedastic", "heteroscedastic", "newey", "standard errors")),
    FieldSpec("model", "Estimation method", True,
              "Estimator, e.g. OLS, logit, probit, Tobit.",
              "the research design section",
              keywords=("ols", "logit", "probit", "tobit", "we estimate", "regression")),
    FieldSpec("subsamples", "Subsamples / column structure", False,
              "How the table's columns differ: for subsample splits, the splitting variable, the cut-off "
              "(e.g. median) and when it is measured; otherwise the change in specification across columns.",
              "the table notes, the table header and the text describing the table",
              keywords=("subsample", "split", "median", "partition", "tercile", "quartile", "above", "below")),
    FieldSpec("winsorization", "Winsorization / outliers", False,
              "Winsorizing or trimming of variables, including the percentiles.",
              "the Data/Sample section or the appendix",
              keywords=("winsoriz", "winsoris", "truncat", "trimm", "outlier")),
    FieldSpec("sample_size", "Reported sample size", False,
              "Number of observations reported for this table or the final sample.",
              "the Data section or the N row of the table",
              keywords=("observations", "final sample", " n ")),
]

TEMPLATES: dict[str, list[FieldSpec]] = {"regression": REGRESSION_TEMPLATE}


def get_template(name: str) -> list[FieldSpec]:
    try:
        return TEMPLATES[name]
    except KeyError:
        raise ValueError(f"Unknown template '{name}'. Available: {', '.join(TEMPLATES)}") from None
