"""Download, validate and split the public UCI session data."""
import hashlib
import io
from pathlib import Path
import urllib.request
import zipfile
import numpy as np
import pandas as pd

URL = 'https://archive.ics.uci.edu/static/public/468/online+shoppers+purchasing+intention+dataset.zip'
SHA256 = 'b3055ee355f59134d851d32641183cb4a8b45def7124d2f50442a042f358e0d9'
CATEGORICAL = ['OperatingSystems', 'Browser', 'Region', 'TrafficType', 'VisitorType', 'Weekend']
NUMERIC = ['Administrative', 'Administrative_Duration', 'Informational',
           'Informational_Duration', 'ProductRelated', 'ProductRelated_Duration',
           'BounceRates', 'ExitRates', 'SpecialDay']


def download(path):
    """Read only the intended CSV member; verify a known file digest."""
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(URL, timeout=60) as response:
            archive = zipfile.ZipFile(io.BytesIO(response.read()))
        content = archive.read('online_shoppers_intention.csv')
        if hashlib.sha256(content).hexdigest() != SHA256:
            raise ValueError('UCI file changed: review source before updating SHA256.')
        path.write_bytes(content)
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256:
        raise ValueError('Unexpected dataset SHA256. Use the original UCI CSV.')
    return path


def prepare_features(frame, include_page_values=False):
    """Validate schema and normalize categories identically in training/inference."""
    numeric = NUMERIC + (['PageValues'] if include_page_values else [])
    columns = numeric + CATEGORICAL
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    out = frame[columns].copy()
    for col in numeric:
        out[col] = pd.to_numeric(out[col], errors='raise')
        observed = out[col].dropna()
        if not np.isfinite(observed).all() or (observed < 0).any():
            raise ValueError(f'{col} must contain finite nonnegative values or blanks.')
    for col in ['BounceRates', 'ExitRates', 'SpecialDay']:
        if (out[col].dropna() > 1).any():
            raise ValueError(f'{col} must be in [0, 1].')
    for col in CATEGORICAL:
        # Numeric codes are nominal categories, not ordered measurements.
        if col in ['OperatingSystems', 'Browser', 'Region', 'TrafficType']:
            out[col] = pd.to_numeric(out[col], errors='raise').map(
                lambda value: str(int(value)) if pd.notna(value) and float(value).is_integer()
                else (np.nan if pd.isna(value) else str(value)))
        else:
            out[col] = out[col].map(lambda value: str(value) if pd.notna(value) else np.nan)
    return out


def load_and_split(path, config):
    frame = pd.read_csv(download(path))
    # Preserve the source row number for reproducible error inspection.
    frame.index.name = 'source_row'
    labels = frame['Revenue'].astype(str).str.lower().map({'true': 1, 'false': 0})
    if labels.isna().any():
        raise ValueError('Revenue must be True or False.')
    frame['Revenue'] = labels.astype(int)
    parts = {}
    for name in ['train', 'validation', 'test']:
        parts[name] = frame.loc[frame.Month.isin(config[f'{name}_months'])].copy()
        if parts[name].Revenue.nunique() != 2:
            raise ValueError(f'{name} needs both classes.')
    indices = [set(part.index) for part in parts.values()]
    if any(indices[i] & indices[j] for i in range(3) for j in range(i + 1, 3)):
        raise ValueError('Split overlap.')
    if sum(map(len, parts.values())) != len(frame):
        raise ValueError('Some months were omitted from the split.')
    return frame, parts
