from __future__ import annotations

import math
import pandas as pd
from scipy.stats import norm

from config import PROCESSED_DIR, RESULTS_DIR
from utils import save_json


def proportion_mde(p: float, n_per_arm: int, alpha: float = 0.05, power: float = 0.8) -> float:
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    return float((z_alpha + z_beta) * math.sqrt(2 * p * (1 - p) / n_per_arm))


def mean_mde(std: float, n_per_arm: int, alpha: float = 0.05, power: float = 0.8) -> float:
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    return float((z_alpha + z_beta) * std * math.sqrt(2 / n_per_arm))


def main() -> None:
    df = pd.read_csv(PROCESSED_DIR / 'customer_experiment_table.csv')
    n_total = len(df)
    n_per_arm = n_total // 2
    baseline_conv = df['conversion_30d'].mean()
    baseline_gmv_std = df['gmv_30d'].std(ddof=1)

    outputs = {
        'n_total': int(n_total),
        'n_per_arm_assumed': int(n_per_arm),
        'baseline_conversion_rate': float(baseline_conv),
        'mde_conversion_absolute': proportion_mde(baseline_conv, n_per_arm),
        'baseline_gmv_std': float(baseline_gmv_std),
        'mde_gmv_absolute': mean_mde(baseline_gmv_std, n_per_arm),
        'guardrails': ['SRM p-value > 0.01', 'No extreme negative GMV inflation', 'Stable country mix'],
        'primary_metric': 'conversion_30d',
        'secondary_metrics': ['orders_30d', 'gmv_30d'],
    }
    save_json(outputs, RESULTS_DIR / 'design_power_summary.json')
    print(outputs)


if __name__ == '__main__':
    main()
