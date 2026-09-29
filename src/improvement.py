"""Post-test exploratory improvements; never changes the preregistered models."""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from .data import load_and_split, prepare_features
from .evaluation import metrics, select_threshold
from .models import build_model
from .preprocessing import build_preprocessing

ROOT = Path(__file__).resolve().parents[1]


def run_improvements(train, validation, test, seed, main_results, output):
    """Select each small, fixed grid on validation; test selected variants once."""
    from xgboost import XGBClassifier

    y_train = train['Revenue'].to_numpy()
    y_validation = validation['Revenue'].to_numpy()
    y_test = test['Revenue'].to_numpy()
    x_train = prepare_features(train)
    x_validation = prepare_features(validation)
    x_test = prepare_features(test)
    imbalance_ratio = float((y_train == 0).sum() / (y_train == 1).sum())

    # RF: original setting plus three controlled depth/feature-subset changes.
    rf_grid = [
        {'min_samples_leaf': 20, 'max_depth': depth, 'max_features': features}
        for depth in [None, 8] for features in ['sqrt', 0.5]
    ]
    # Literature-motivated XGBoost: two depths and no/weighted minority class.
    xgb_grid = [
        {'max_depth': depth, 'scale_pos_weight': weight}
        for depth in [3, 5] for weight in [1.0, imbalance_ratio]
    ]
    rows = []
    selected_results = {}
    for experiment_name, model_name, grid in [
        ('rf_parameter_improvement', 'random_forest', rf_grid),
        ('literature_xgboost', 'xgboost', xgb_grid),
    ]:
        best_ap = -1.0
        best_model = None
        best_row = None
        for parameters in grid:
            if model_name == 'random_forest':
                model = build_model(model_name, seed, parameters)
            else:
                classifier = XGBClassifier(
                    n_estimators=150, learning_rate=0.05,
                    objective='binary:logistic', eval_metric='logloss',
                    tree_method='hist', n_jobs=1, random_state=seed,
                    **parameters,
                )
                model = Pipeline([
                    ('preprocessing', build_preprocessing(False)),
                    ('classifier', classifier),
                ])
            model.fit(x_train, y_train)
            validation_probability = model.predict_proba(x_validation)[:, 1]
            validation_ap = float(average_precision_score(
                y_validation, validation_probability,
            ))
            row = {
                'experiment_name': experiment_name,
                'model': model_name,
                'parameters': json.dumps(parameters, sort_keys=True),
                'validation_ap': validation_ap,
                'selected': False,
                'test_ap': None,
                'brier': None,
                'precision': None,
                'recall': None,
                'f2': None,
                'log_loss': None,
                'threshold': None,
                'notes': 'Post-test exploratory; no PageValues; train-only fit.',
            }
            rows.append(row)
            if validation_ap > best_ap:
                best_ap = validation_ap
                best_model = model
                best_row = row

        # Only now is the test opened for this selected family variant.
        validation_probability = best_model.predict_proba(x_validation)[:, 1]
        threshold = select_threshold(y_validation, validation_probability)
        test_probability = best_model.predict_proba(x_test)[:, 1]
        test_metrics = metrics(y_test, test_probability, threshold)
        best_row['selected'] = True
        for key in ['brier', 'precision', 'recall', 'f2', 'log_loss', 'threshold']:
            best_row[key] = test_metrics[key]
        best_row['test_ap'] = test_metrics['average_precision']
        selected_results[experiment_name] = test_metrics

    output = Path(output)
    pd.DataFrame(rows).to_csv(output / 'improvement_experiments.csv', index=False)

    clean = main_results.loc[main_results.scenario == 'clean'].set_index('model')
    labels = ['Baseline', 'LR', 'RF', 'GB', 'XGBoost', 'RF variantas']
    values = [
        clean.loc[name, 'average_precision']
        for name in ['purchase_rate', 'logistic', 'random_forest', 'gradient_boosting']
    ] + [
        selected_results['literature_xgboost']['average_precision'],
        selected_results['rf_parameter_improvement']['average_precision'],
    ]
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(labels, values, color=['#9aa5b1'] * 4 + ['#467ba5', '#204b78'])
    ax.set_ylabel('Testo AP')
    ax.set_ylim(0, max(values) * 1.18)
    ax.set_title('Pagrindiniai modeliai ir tiriamieji pagerinimai')
    ax.grid(axis='y', alpha=0.2)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.008,
                f'{value:.4f}', ha='center', fontsize=9)
    fig.tight_layout()
    fig.savefig(output / 'improvement_comparison.png', dpi=180)
    plt.close(fig)
    return pd.DataFrame(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'results')
    args = parser.parse_args()
    config = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
    _, parts = load_and_split(ROOT / 'data/online_shoppers_intention.csv', config)
    main_results = pd.read_csv(ROOT / 'results/metrics.csv')
    args.output.mkdir(parents=True, exist_ok=True)
    with threadpool_limits(limits=1):
        run_improvements(parts['train'], parts['validation'], parts['test'],
                         config['seed'], main_results, args.output)
