from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from config import PROCESSED_DIR, RESULTS_DIR
from utils import save_json


def fit_t_learner(df: pd.DataFrame) -> pd.DataFrame:
    features = [
        'is_uk',
        'high_value_user',
        'pre_orders',
        'pre_items',
        'pre_revenue',
        'pre_avg_basket',
        'pre_recency_days',
        'log_pre_orders',
        'log_pre_revenue',
    ]

    treat_df = df[df['treatment'] == 1].copy()
    ctrl_df = df[df['treatment'] == 0].copy()

    model_t = RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=20,
        random_state=42,
    )
    model_c = RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=20,
        random_state=42,
    )

    model_t.fit(treat_df[features], treat_df['gmv_30d'])
    model_c.fit(ctrl_df[features], ctrl_df['gmv_30d'])

    scored = df[['customer_id', 'high_value_user', 'is_uk', 'pre_recency_days']].copy()
    scored['pred_treat'] = model_t.predict(df[features])
    scored['pred_control'] = model_c.predict(df[features])
    scored['cate_hat'] = scored['pred_treat'] - scored['pred_control']

    return scored


def main() -> None:
    df = pd.read_csv(PROCESSED_DIR / 'customer_experiment_table.csv')
    scored = fit_t_learner(df)
    scored.to_csv(RESULTS_DIR / 'hte_scored_users.csv', index=False)

    segment_summary = (
        scored.assign(
            recency_segment=(scored['pre_recency_days'] > scored['pre_recency_days'].median())
            .map({True: 'dormant', False: 'active'})
        )
        .groupby(['high_value_user', 'is_uk', 'recency_segment'], as_index=False)['cate_hat']
        .mean()
        .sort_values('cate_hat', ascending=False)
    )

    top_segments = segment_summary.head(10).to_dict(orient='records')

    results = {
        'avg_cate': float(scored['cate_hat'].mean()),
        'cate_std': float(scored['cate_hat'].std(ddof=1)),
        'top_segments': top_segments,
    }

    save_json(results, RESULTS_DIR / 'hte_summary.json')
    print(results)


if __name__ == '__main__':
    main()