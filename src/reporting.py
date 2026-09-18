"""CSV, Markdown ir vykdymo aprašo įrašymas. Čia modeliai nemokomi."""
import hashlib
import json
import platform
from time import perf_counter
import numpy as np
import pandas as pd
import sklearn
from .data import SHA256

def save_summary(table, delta, interval, formula_error, output):
    """Sukuria RESULTS.md iš rezultatų; tai ne papildomas eksperimentas.

    table – metrikų eilučių sąrašas; delta – RF ir logistinės regresijos AP skirtumas;
    interval – to skirtumo bootstrap ribos; formula_error – RF formulės patikra.
    """
    lines = ['# Eksperimento rezultatai', '',
             'Automatiškai sukurta paleidus `python -m src.experiment`.', '',
             'AP yra pagrindinė PR kreivės suvestinė; trapecinis PR-AUC pateiktas atskirai. Mažesnis Brier yra geriau.', '',
             '| Modelis | Scenarijus | AP | PR-AUC | Precision | Recall | Brier | Slenkstis |',
             '|---|---|---:|---:|---:|---:|---:|---:|']
    for row in table:
        lines.append(f"| {row['model']} | {row['scenario']} | {row['average_precision']:.4f} | {row['pr_auc_trapezoid']:.4f} | {row['precision']:.4f} | {row['recall']:.4f} | {row['brier']:.4f} | {row['threshold']:.2f} |")
    lines += ['', f'RF ir logistinės regresijos AP skirtumas: **{delta:.4f}**. Sąlyginis 95 % porinio bootstrap intervalas: **[{interval[0]:.4f}; {interval[1]:.4f}]**.',
              '', f'Hipotezė AP skirtumas ≥ 0,02: **{"pasitvirtino šiame teste" if delta >= 0.02 else "nepasitvirtino šiame teste"}**.',
              '', f'Formulės ir bibliotekos prognozių didžiausias skirtumas: `{formula_error:.3g}`.',
              '', '![PR ir kalibracija](evaluation.svg)', '',
              'Interpretacija, ribos ir klaidų analizė: [ataskaita](../docs/ATASKAITA.md).']
    (output / 'RESULTS.md').write_text('\n'.join(lines) + '\n')


def save_splits(parts, config, output):
    """Gauna imčių lenteles ir įrašo dydžius bei eilučių priklausomybę imtims."""
    # Išsaugome imčių dydžius ir originalių eilučių numerius patikrai.
    split_rows = []
    for name, part in parts.items():
        split_rows.append({'split': name, 'rows': len(part), 'positives': int(part.Revenue.sum()),
                           'purchase_rate': float(part.Revenue.mean()),
                           'months': ', '.join(config[f'{name}_months'])})
    pd.DataFrame(split_rows).to_csv(output / 'split_summary.csv', index=False)
    membership_tables = []
    for split_name, part in parts.items():
        membership = pd.DataFrame({'source_row': part.index, 'split': split_name})
        membership_tables.append(membership)
    pd.concat(membership_tables).to_csv(output / 'split_membership.csv', index=False)


def save_tables(table, selection, test, predictions, output):
    """Gauna metrikas ir prognozes; įrašo tris CSV ir grąžina metrikų lentelę."""
    y_test = test['Revenue'].to_numpy()
    # 6. Užrašome lenteles ir kiekvienos testo sesijos prognozes.
    result = pd.DataFrame(table)
    result.to_csv(output / 'metrics.csv', index=False)
    pd.DataFrame(selection).to_csv(output / 'model_selection.csv', index=False)
    prediction_table = pd.DataFrame({
        'source_row': test.index, 'month': test.Month, 'revenue': y_test,
    })
    for label, probability in predictions.items():
        prediction_table[label] = probability
    prediction_table.to_csv(output / 'test_predictions.csv', index=False)
    return result

def save_manifest(root, config, data, formula_error, delta, interval,
                  missing_mask, started, output):
    """Įrašo aplinką, duomenų ir kodo kontrolines sumas bei patikros rezultatus."""
    source_checksums = {}
    for path in sorted((root / 'src').glob('*.py')):
        relative_path = str(path.relative_to(root))
        source_checksums[relative_path] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        'config': config, 'dataset_sha256': SHA256, 'dataset_rows': len(data),
        'exact_duplicate_rows': int(data.duplicated().sum()),
        'split_source': 'Month only; no exact timestamps or visitor IDs',
        'python': platform.python_version(), 'platform': platform.platform(),
        'sklearn': sklearn.__version__, 'numpy': np.__version__, 'pandas': pd.__version__,
        'formula_max_absolute_error': formula_error,
        'rf_minus_logistic_ap': delta, 'paired_bootstrap_95pct': interval,
        'hypothesis_delta_at_least_0_02': bool(delta >= 0.02),
        'missing_numeric_cells': int(missing_mask.sum()), 'elapsed_seconds': perf_counter() - started,
        'source_sha256': source_checksums,
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
