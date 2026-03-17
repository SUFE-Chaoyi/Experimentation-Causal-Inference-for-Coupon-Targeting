"""Prepare a customer-level dataset for the A/B + causal inference project.

Preferred behavior:
1. If data/raw/Online Retail.xlsx exists, read it locally.
2. Otherwise, try fetching UCI Online Retail (id=352) via ucimlrepo.

This script creates a realistic user-level experiment table with:
- pre-period outcomes
- randomized treatment assignment (A/B test)
- post-period outcomes
- a policy-driven observational treatment flag for causal inference
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from config import PROCESSED_DIR, RANDOM_SEED, RAW_DIR, TARGET_SAMPLE_SIZE

rng = np.random.default_rng(RANDOM_SEED)
LOCAL_RAW_CANDIDATES = [
    RAW_DIR / 'Online Retail.xlsx',
    RAW_DIR / 'online_retail.xlsx',
    RAW_DIR / 'Online_Retail.xlsx',
    RAW_DIR / 'online_retail.csv',
    RAW_DIR / 'Online Retail.csv',
]
REQUIRED_COLUMNS = [
    'InvoiceNo', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country'
]


def _standardize_transaction_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    rename_map = {
        'Customer ID': 'CustomerID',
        'Invoice No': 'InvoiceNo',
        'Invoice Date': 'InvoiceDate',
        'Unit Price': 'UnitPrice',
    }
    df = df.rename(columns=rename_map)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f'Missing required columns: {missing}. Available columns: {df.columns.tolist()}'
        )

    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
    df = df.dropna(subset=['InvoiceDate', 'CustomerID'])

    df = df[~df['InvoiceNo'].astype(str).str.lower().str.startswith('c')]
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)].copy()

    df = df.rename(columns={'CustomerID': 'customer_id'})
    df['customer_id'] = df['customer_id'].astype('Int64').astype(str)
    df['revenue'] = df['Quantity'] * df['UnitPrice']
    return df


def _load_local_online_retail() -> pd.DataFrame | None:
    for path in LOCAL_RAW_CANDIDATES:
        if path.exists():
            if path.suffix.lower() == '.csv':
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            print(f'Loaded local raw file: {path}')
            return _standardize_transaction_columns(df)
    return None


def _load_remote_online_retail() -> pd.DataFrame:
    try:
        from ucimlrepo import fetch_ucirepo
    except Exception as exc:
        raise RuntimeError(
            'No local raw file found in data/raw, and ucimlrepo is unavailable. '
            'Place Online Retail.xlsx into data/raw or install ucimlrepo.'
        ) from exc

    ds = fetch_ucirepo(id=352)
    source_df = None
    if getattr(ds.data, 'original', None) is not None:
        source_df = ds.data.original.copy()
    elif getattr(ds.data, 'features', None) is not None:
        source_df = ds.data.features.copy()

    if source_df is None:
        raise RuntimeError('Failed to load Online Retail from UCI.')

    print('Loaded Online Retail from UCI via ucimlrepo.')
    return _standardize_transaction_columns(source_df)


def load_online_retail() -> pd.DataFrame:
    local_df = _load_local_online_retail()
    if local_df is not None:
        return local_df
    return _load_remote_online_retail()


def build_customer_table(df: pd.DataFrame) -> pd.DataFrame:
    split_date = df['InvoiceDate'].quantile(0.75)
    pre = df[df['InvoiceDate'] < split_date].copy()
    post = df[df['InvoiceDate'] >= split_date].copy()

    pre_agg = pre.groupby('customer_id').agg(
        pre_orders=('InvoiceNo', 'nunique'),
        pre_items=('Quantity', 'sum'),
        pre_revenue=('revenue', 'sum'),
        pre_avg_basket=('revenue', 'mean'),
        pre_last_date=('InvoiceDate', 'max'),
        country=('Country', lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]),
    )
    post_agg = post.groupby('customer_id').agg(
        post_orders_base=('InvoiceNo', 'nunique'),
        post_items_base=('Quantity', 'sum'),
        post_revenue_base=('revenue', 'sum'),
        post_avg_basket_base=('revenue', 'mean'),
        post_last_date=('InvoiceDate', 'max'),
    )
    user_df = pre_agg.join(post_agg, how='inner').reset_index()
    user_df = user_df[user_df['pre_orders'] >= 1].copy()

    max_pre_date = user_df['pre_last_date'].max()
    user_df['pre_recency_days'] = (max_pre_date - user_df['pre_last_date']).dt.days.clip(lower=0)
    user_df['log_pre_revenue'] = np.log1p(user_df['pre_revenue'])
    user_df['log_pre_orders'] = np.log1p(user_df['pre_orders'])
    user_df['high_value_user'] = (user_df['pre_revenue'] >= user_df['pre_revenue'].median()).astype(int)
    user_df['is_uk'] = (user_df['country'] == 'United Kingdom').astype(int)

    if len(user_df) > TARGET_SAMPLE_SIZE:
        user_df = user_df.sample(TARGET_SAMPLE_SIZE, random_state=RANDOM_SEED).reset_index(drop=True)
    else:
        user_df = user_df.reset_index(drop=True)
        warnings.warn(
            f'Available customers ({len(user_df)}) are below TARGET_SAMPLE_SIZE={TARGET_SAMPLE_SIZE}. '
            'Using all eligible customers.',
            stacklevel=2,
        )

    user_df['treatment'] = rng.binomial(1, 0.5, size=len(user_df))

    tau = (
        0.02
        + 0.015 * user_df['high_value_user']
        + 0.010 * (user_df['pre_recency_days'] > user_df['pre_recency_days'].median()).astype(int)
        + 0.008 * (1 - user_df['is_uk'])
    )

    base_conv_prob = 1 / (1 + np.exp(-(
        -1.2
        + 0.55 * user_df['log_pre_orders']
        + 0.35 * user_df['log_pre_revenue']
        - 0.002 * user_df['pre_recency_days']
    )))
    treat_conv_prob = np.clip(base_conv_prob + tau * user_df['treatment'], 0.001, 0.999)

    user_df['conversion_30d'] = rng.binomial(1, treat_conv_prob)
    user_df['orders_30d'] = np.where(
        user_df['conversion_30d'] == 1,
        rng.poisson(
            1.2 + 0.12 * user_df['pre_orders'] + 0.35 * user_df['treatment'] * (1 + 0.3 * user_df['high_value_user'])
        ),
        0,
    )
    user_df['orders_30d'] = np.maximum(user_df['orders_30d'], user_df['conversion_30d'])
    user_df['gmv_30d'] = np.where(
        user_df['orders_30d'] > 0,
        user_df['orders_30d']
        * (12 + 1.8 * user_df['pre_avg_basket'].fillna(user_df['pre_avg_basket'].median()))
        * (1 + 0.05 * user_df['treatment'] + 0.03 * user_df['treatment'] * user_df['high_value_user'])
        + rng.normal(0, 10, size=len(user_df)),
        0,
    )
    user_df['gmv_30d'] = user_df['gmv_30d'].clip(lower=0)

    logits = (
        -1.0
        + 0.8 * user_df['high_value_user']
        + 0.4 * user_df['is_uk']
        - 0.002 * user_df['pre_recency_days']
        + 0.45 * user_df['log_pre_revenue']
    )
    obs_p = 1 / (1 + np.exp(-logits))
    user_df['coupon_targeted_obs'] = rng.binomial(1, np.clip(obs_p, 0.02, 0.95))

    confounding_bonus = 6 * user_df['high_value_user'] + 2 * user_df['is_uk']
    user_df['gmv_30d_obs'] = (
        user_df['gmv_30d'] + 8 * user_df['coupon_targeted_obs'] + confounding_bonus + rng.normal(0, 6, size=len(user_df))
    ).clip(lower=0)

    keep_cols = [
        'customer_id', 'country', 'is_uk', 'high_value_user',
        'pre_orders', 'pre_items', 'pre_revenue', 'pre_avg_basket',
        'pre_recency_days', 'log_pre_orders', 'log_pre_revenue',
        'treatment', 'conversion_30d', 'orders_30d', 'gmv_30d',
        'coupon_targeted_obs', 'gmv_30d_obs'
    ]
    return user_df[keep_cols].copy()


def main() -> None:
    tx = load_online_retail()
    user_df = build_customer_table(tx)
    out_path = PROCESSED_DIR / 'customer_experiment_table.csv'
    user_df.to_csv(out_path, index=False)
    print(f'Saved {len(user_df):,} rows to {out_path}')


if __name__ == '__main__':
    main()
