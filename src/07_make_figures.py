from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from config import RESULTS_DIR


def main() -> None:
    with open(RESULTS_DIR / 'ab_test_results.json', 'r', encoding='utf-8') as f:
        ab = json.load(f)
    with open(RESULTS_DIR / 'hte_summary.json', 'r', encoding='utf-8') as f:
        hte = json.load(f)

    seg = pd.DataFrame(hte['top_segments'])

    metrics = ['conversion_30d', 'orders_30d', 'gmv_30d']
    estimates = [ab[m]['estimate'] for m in metrics]
    labels = ['Conversion', 'Orders', 'GMV']

    plt.figure(figsize=(7, 4))
    plt.bar(labels, estimates)
    plt.axhline(0, linewidth=1)
    plt.title('Average treatment effect by metric')
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / 'ate_bar.png', dpi=180)
    plt.close()

    top = seg.head(10).copy()
    top['segment'] = (
        'HV=' + top['high_value_user'].astype(str)
        + ', UK=' + top['is_uk'].astype(str)
        + ', ' + top['recency_segment'].astype(str)
    )
    plt.figure(figsize=(8, 5))
    plt.barh(top['segment'][::-1], top['cate_hat'][::-1])
    plt.title('Top segments by predicted uplift (HTE)')
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / 'hte_top_segments.png', dpi=180)
    plt.close()

    print('Saved figures to results/')


if __name__ == '__main__':
    main()
