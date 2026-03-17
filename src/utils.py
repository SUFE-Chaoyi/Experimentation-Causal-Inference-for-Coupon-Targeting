from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
from scipy import stats


def save_json(obj: Dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def summarize_binary_rate(series: pd.Series) -> Tuple[float, int]:
    clean = series.dropna()
    return float(clean.mean()), int(clean.shape[0])


def difference_in_means(y_t: Iterable[float], y_c: Iterable[float]) -> Dict:
    y_t = pd.Series(y_t).dropna().astype(float)
    y_c = pd.Series(y_c).dropna().astype(float)
    est = float(y_t.mean() - y_c.mean())
    test = stats.ttest_ind(y_t, y_c, equal_var=False)
    se = float(np.sqrt(y_t.var(ddof=1) / len(y_t) + y_c.var(ddof=1) / len(y_c)))
    ci_low = est - 1.96 * se
    ci_high = est + 1.96 * se
    return {
        'estimate': est,
        'p_value': float(test.pvalue),
        'se': se,
        'ci_low': float(ci_low),
        'ci_high': float(ci_high),
        'n_treat': int(len(y_t)),
        'n_control': int(len(y_c)),
    }


def difference_in_proportions(y_t: Iterable[float], y_c: Iterable[float]) -> Dict:
    y_t = pd.Series(y_t).dropna().astype(float)
    y_c = pd.Series(y_c).dropna().astype(float)
    p1, n1 = y_t.mean(), len(y_t)
    p0, n0 = y_c.mean(), len(y_c)
    diff = float(p1 - p0)
    pooled = (y_t.sum() + y_c.sum()) / (n1 + n0)
    se = np.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n0))
    z = diff / se if se > 0 else 0.0
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    se_unpooled = np.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    ci_low = diff - 1.96 * se_unpooled
    ci_high = diff + 1.96 * se_unpooled
    return {
        'estimate': diff,
        'p_value': float(p_value),
        'se': float(se_unpooled),
        'ci_low': float(ci_low),
        'ci_high': float(ci_high),
        'n_treat': int(n1),
        'n_control': int(n0),
    }


def srm_p_value(n_treat: int, n_control: int, expected_treat_share: float = 0.5) -> float:
    total = n_treat + n_control
    expected = np.array([expected_treat_share * total, (1 - expected_treat_share) * total])
    observed = np.array([n_treat, n_control])
    stat = ((observed - expected) ** 2 / expected).sum()
    return float(1 - stats.chi2.cdf(stat, df=1))


def bootstrap_ci(diffs: np.ndarray, alpha: float = 0.05) -> Tuple[float, float]:
    return tuple(np.quantile(diffs, [alpha / 2, 1 - alpha / 2]).tolist())
