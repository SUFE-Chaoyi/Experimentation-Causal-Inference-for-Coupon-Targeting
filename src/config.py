from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / 'data' / 'raw'
PROCESSED_DIR = ROOT / 'data' / 'processed'
RESULTS_DIR = ROOT / 'results'

RANDOM_SEED = 42
PRE_PERIOD_DAYS = 60
EXPERIMENT_DAYS = 30
TREAT_SHARE = 0.50
TARGET_SAMPLE_SIZE = 1600

for path in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)
