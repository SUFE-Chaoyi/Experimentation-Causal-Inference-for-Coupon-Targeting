from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression

from config import PROCESSED_DIR, RESULTS_DIR, RANDOM_SEED
from utils import save_json


def aipw_ate(df: pd.DataFrame) -> float:
    x_cols = ['pre_orders', 'pre_revenue', 'pre_recency_days', 'is_uk', 'high_value_user']
    x = df[x_cols]
    t = df['coupon_targeted_obs']
    y = df['gmv_30d_obs']

    ps_model = LogisticRegression(max_iter=2000, random_state=RANDOM_SEED)
    ps_model.fit(x, t)
    ps = pd.Series(ps_model.predict_proba(x)[:, 1]).clip(0.02, 0.98)

    mu1_model = RandomForestRegressor(n_estimators=300, min_samples_leaf=50, random_state=RANDOM_SEED)
    mu0_model = RandomForestRegressor(n_estimators=300, min_samples_leaf=50, random_state=RANDOM_SEED + 1)
    mu1_model.fit(x[t == 1], y[t == 1])
    mu0_model.fit(x[t == 0], y[t == 0])

    mu1 = pd.Series(mu1_model.predict(x), index=df.index)
    mu0 = pd.Series(mu0_model.predict(x), index=df.index)

    pseudo = mu1 - mu0 + t * (y - mu1) / ps - (1 - t) * (y - mu0) / (1 - ps)
    return float(pseudo.mean())


def naive_diff(df: pd.DataFrame) -> float:
    return float(df.loc[df['coupon_targeted_obs'] == 1, 'gmv_30d_obs'].mean() - df.loc[df['coupon_targeted_obs'] == 0, 'gmv_30d_obs'].mean())


def main() -> None:
    df = pd.read_csv(PROCESSED_DIR / 'customer_experiment_table.csv')
    results = {
        'naive_observational_difference': naive_diff(df),
        'aipw_ate': aipw_ate(df),
        'note': 'Naive difference is biased because treatment is policy-targeted, not randomized.'
    }
    save_json(results, RESULTS_DIR / 'observational_results.json')
    print(results)


if __name__ == '__main__':
    main()
