from __future__ import annotations

import pandas as pd

from config import PROCESSED_DIR, RESULTS_DIR
from utils import difference_in_means, save_json


def cuped_adjustment(df: pd.DataFrame, outcome: str, covariate: str) -> pd.Series:
    theta = df[[outcome, covariate]].cov().iloc[0, 1] / df[covariate].var(ddof=1)
    return df[outcome] - theta * (df[covariate] - df[covariate].mean())


def main() -> None:
    df = pd.read_csv(PROCESSED_DIR / 'customer_experiment_table.csv')
    df['gmv_30d_cuped'] = cuped_adjustment(df, 'gmv_30d', 'pre_revenue')
    raw = difference_in_means(df.loc[df.treatment == 1, 'gmv_30d'], df.loc[df.treatment == 0, 'gmv_30d'])
    adj = difference_in_means(df.loc[df.treatment == 1, 'gmv_30d_cuped'], df.loc[df.treatment == 0, 'gmv_30d_cuped'])
    variance_reduction = 1 - (df['gmv_30d_cuped'].var(ddof=1) / df['gmv_30d'].var(ddof=1))

    results = {
        'raw_gmv_result': raw,
        'cuped_gmv_result': adj,
        'variance_reduction_fraction': float(variance_reduction),
    }
    save_json(results, RESULTS_DIR / 'cuped_results.json')
    print(results)


if __name__ == '__main__':
    main()
