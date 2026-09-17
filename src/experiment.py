"""Run the predefined experiment: python -m src.experiment."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import calibration_curve
from sklearn.metrics import average_precision_score, precision_recall_curve
from threadpoolctl import threadpool_limits
from .data import load_and_split, prepare_features, NUMERIC, SHA256
from .evaluation import metrics, select_threshold, paired_ap_interval
from .models import build_model, candidates, forest_probability_by_formula

ROOT = Path(__file__).resolve().parents[1]


def run(config_path=ROOT / 'config.json', output=ROOT / 'results'):
    started = perf_counter()
    config = json.loads(Path(config_path).read_text())
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    model_dir = ROOT / 'models'
    model_dir.mkdir(exist_ok=True)
    data, parts = load_and_split(ROOT / 'data/online_shoppers_intention.csv', config)
    train, validation, test = [parts[name] for name in ['train', 'validation', 'test']]
    y_train, y_validation, y_test = [part.Revenue.to_numpy() for part in [train, validation, test]]
    split_rows = []
    for name, part in parts.items():
        split_rows.append({'split': name, 'rows': len(part), 'positives': int(part.Revenue.sum()),
                           'purchase_rate': float(part.Revenue.mean()),
                           'months': ', '.join(config[f'{name}_months'])})
    pd.DataFrame(split_rows).to_csv(output / 'split_summary.csv', index=False)
    pd.concat([pd.DataFrame({'source_row': part.index, 'split': name})
               for name, part in parts.items()]).to_csv(output / 'split_membership.csv', index=False)
    selection, table, predictions, fitted = [], [], {}, {}
    specifications = [(name, name, False) for name in ['purchase_rate', 'logistic', 'random_forest', 'gradient_boosting']]
    specifications.append(('random_forest_with_page_values', 'random_forest', True))
    for label, name, page_values in specifications:
        x_train, x_validation, x_test = [prepare_features(part, page_values) for part in [train, validation, test]]
        best_score, best_model, best_parameters = -1.0, None, None
        fitting_started = perf_counter()
        for params in candidates(name):
            model = build_model(name, config['seed'], params, page_values)
            model.fit(x_train, y_train)
            probability = model.predict_proba(x_validation)[:, 1]
            score = average_precision_score(y_validation, probability)
            selection.append({'model': label, 'parameters': json.dumps(params), 'validation_ap': float(score)})
            if score > best_score:
                best_score, best_model, best_parameters = score, model, params
        # Freeze model and validation threshold before test prediction.
        threshold = select_threshold(y_validation, best_model.predict_proba(x_validation)[:, 1])
        elapsed = perf_counter() - fitting_started
        probability = best_model.predict_proba(x_test)[:, 1]
        predictions[label] = probability
        fitted[label] = (best_model, threshold, page_values)
        table.append({'model': label, 'scenario': 'clean', 'validation_ap': best_score,
                      'selection_seconds': elapsed, **metrics(y_test, probability, threshold)})
        joblib.dump({'model': best_model, 'threshold': threshold, 'include_page_values': page_values,
                     'features': list(x_train.columns), 'parameters': best_parameters,
                     'seed': config['seed']}, model_dir / f'{label}.joblib')
        print(label, 'validation AP:', round(best_score, 4), 'test AP:', round(table[-1]['average_precision'], 4), flush=True)
    # Same missingness mask; no retraining or threshold adjustment.
    damaged = prepare_features(test)
    rng = np.random.default_rng(config['seed'])
    missing_mask = rng.random((len(damaged), len(NUMERIC))) < config['missing_fraction']
    damaged[NUMERIC] = damaged[NUMERIC].mask(missing_mask)
    for label in ['purchase_rate', 'logistic', 'random_forest', 'gradient_boosting']:
        model, threshold, _ = fitted[label]
        probability = model.predict_proba(damaged)[:, 1]
        table.append({'model': label, 'scenario': f"missing_numeric_{100 * config['missing_fraction']:g}pct", **metrics(y_test, probability, threshold)})
    result = pd.DataFrame(table)
    result.to_csv(output / 'metrics.csv', index=False)
    pd.DataFrame(selection).to_csv(output / 'model_selection.csv', index=False)
    pd.DataFrame({'source_row': test.index, 'month': test.Month, 'revenue': y_test,
                  **predictions}).to_csv(output / 'test_predictions.csv', index=False)
    rf_model, rf_threshold, _ = fitted['random_forest']
    formula = forest_probability_by_formula(rf_model, prepare_features(test))
    formula_error = float(np.max(np.abs(formula - predictions['random_forest'])))
    if not np.allclose(formula, predictions['random_forest'], atol=1e-12):
        raise AssertionError('Forest equation does not match sklearn probabilities.')
    errors = test.copy()
    errors['probability'] = predictions['random_forest']
    errors['prediction'] = (errors.probability >= rf_threshold).astype(int)
    fp = errors.loc[(errors.Revenue == 0) & (errors.prediction == 1)].nlargest(5, 'probability')
    fn = errors.loc[(errors.Revenue == 1) & (errors.prediction == 0)].nsmallest(5, 'probability')
    pd.concat([fp.assign(error='FP'), fn.assign(error='FN')]).to_csv(output / 'error_examples.csv')
    subgroup = []
    for column in ['Month', 'VisitorType']:
        for group, subset in test.groupby(column):
            positions = test.index.get_indexer(subset.index)
            if subset.Revenue.nunique() == 2:
                subgroup.append({'column': column, 'group': group, 'rows': len(subset),
                                 'purchase_rate': float(subset.Revenue.mean()),
                                 **metrics(subset.Revenue, predictions['random_forest'][positions], rf_threshold)})
    pd.DataFrame(subgroup).to_csv(output / 'subgroups.csv', index=False)
    interval = paired_ap_interval(y_test, predictions['random_forest'], predictions['logistic'],
                                  config['bootstrap_repetitions'], config['seed'])
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout='constrained')
    for name in ['purchase_rate', 'logistic', 'random_forest', 'gradient_boosting']:
        probability = predictions[name]
        precision, recall, _ = precision_recall_curve(y_test, probability)
        axes[0].step(recall, precision, where='post', label=name)
        observed, predicted = calibration_curve(y_test, probability, n_bins=8, strategy='quantile')
        axes[1].plot(predicted, observed, marker='o', label=name)
    axes[0].axhline(y_test.mean(), linestyle=':', color='gray', label='test prevalence')
    axes[0].set(xlabel='Recall', ylabel='Precision', title='Final test: November and December', xlim=(0, 1), ylim=(0, 1))
    axes[1].plot([0, 1], [0, 1], '--', color='gray')
    axes[1].set(xlabel='Mean predicted probability', ylabel='Observed purchase rate', title='Calibration (quantile bins)', xlim=(0, 1), ylim=(0, 1))
    for ax in axes:
        ax.legend(fontsize=8); ax.grid(alpha=0.2)
    fig.savefig(output / 'evaluation.svg')
    fig.savefig(output / 'evaluation.png', dpi=160)
    plt.close(fig)
    clean = result.loc[result.scenario == 'clean'].set_index('model')
    delta = float(clean.loc['random_forest', 'average_precision'] - clean.loc['logistic', 'average_precision'])
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
        'source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sorted((ROOT / 'src').glob('*.py'))}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
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
    print('Experiment complete:', output, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, default=ROOT / 'config.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'results')
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        run(args.config, args.output)
