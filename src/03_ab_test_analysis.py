from __future__ import annotations

import numpy as np
import pandas as pd

from config import PROCESSED_DIR, RESULTS_DIR, RANDOM_SEED
from utils import difference_in_means, difference_in_proportions, save_json, srm_p_value, bootstrap_ci

rng = np.random.default_rng(RANDOM_SEED)


def bootstrap_diff(df: pd.DataFrame, metric: str, n_boot: int = 2000) -> tuple[float, float]:
    treat = df[df['treatment'] == 1][metric].to_numpy()
    control = df[df['treatment'] == 0][metric].to_numpy()
    diffs = []
    for _ in range(n_boot):
        t = rng.choice(treat, size=len(treat), replace=True)
        c = rng.choice(control, size=len(control), replace=True)
        diffs.append(t.mean() - c.mean())
    return bootstrap_ci(np.array(diffs))


def main() -> None:
    df = pd.read_csv(PROCESSED_DIR / 'customer_experiment_table.csv')
    n_t = int(df['treatment'].sum())
    n_c = int((1 - df['treatment']).sum())

    conversion = difference_in_proportions(
        df.loc[df['treatment'] == 1, 'conversion_30d'],
        df.loc[df['treatment'] == 0, 'conversion_30d'],
    )
    orders = difference_in_means(
        df.loc[df['treatment'] == 1, 'orders_30d'],
        df.loc[df['treatment'] == 0, 'orders_30d'],
    )
    gmv = difference_in_means(
        df.loc[df['treatment'] == 1, 'gmv_30d'],
        df.loc[df['treatment'] == 0, 'gmv_30d'],
    )
    gmv['bootstrap_ci_low'], gmv['bootstrap_ci_high'] = bootstrap_diff(df, 'gmv_30d')

    results = {
        'sample_ratio_mismatch_p_value': srm_p_value(n_t, n_c),
        'arm_sizes': {'treatment': n_t, 'control': n_c},
        'conversion_30d': conversion,
        'orders_30d': orders,
        'gmv_30d': gmv,
    }
    save_json(results, RESULTS_DIR / 'ab_test_results.json')
    print(results)


if __name__ == '__main__':
    main()
