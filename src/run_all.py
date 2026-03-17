from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

scripts = [
    '01_prepare_data.py',
    '02_design_and_power.py',
    '03_ab_test_analysis.py',
    '04_cuped.py',
    '05_hte.py',
    '06_observational.py',
    '07_make_figures.py',
]

for script in scripts:
    print(f'>>> Running {script}')
    subprocess.run([sys.executable, str(SRC / script)], check=True)
