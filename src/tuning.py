"""Exploratory temporal tuning invoked only by src.experiment.

No function that selects a candidate receives the Nov-Dec test frame. The
test is evaluated only after the four family choices and overall winner are
fixed using earlier months.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from itertools import product
import json
import math
import os
from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, f1_score
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from .data import prepare_features
from .evaluation import metrics, select_threshold
from .preprocessing import build_preprocessing

MONTHS = ('Feb', 'Mar', 'May', 'June', 'Jul', 'Aug')
COUNTS = {'logistic': 22, 'random_forest': 250,
          'gradient_boosting': 200, 'xgboost': 250}
STABILITY_SEEDS = (1, 7, 42, 101, 202)
ORIGINAL_TEST_AP = {'purchase_rate': 0.20656084656084656,
                    'logistic': 0.33356794061583583,
                    'random_forest': 0.3411325147168911,
                    'gradient_boosting': 0.33921063417531777}
ORIGINAL_VALIDATION_AP = {'logistic': 0.24865106115627172,
                          'random_forest': 0.30699681466742,
                          'gradient_boosting': 0.2892483831640243}


def temporal_folds(train):
    """Four expanding, checked train/validation month pairs before Sep-Oct."""
    if not set(train.Month.unique()).issubset(MONTHS):
        raise ValueError('Temporal tuning accepts only the original Feb-Aug train.')
    folds = []
    for stop in range(2, len(MONTHS)):
        earlier, later = MONTHS[:stop], MONTHS[stop]
        fit = train.loc[train.Month.isin(earlier)].copy()
        valid = train.loc[train.Month == later].copy()
        if fit.empty or valid.empty or set(fit.index) & set(valid.index):
            raise ValueError(f'Invalid temporal fold ending in {later}.')
        if max(MONTHS.index(m) for m in fit.Month.unique()) >= MONTHS.index(later):
            raise ValueError('Validation must follow every training month.')
        if fit.Revenue.nunique() != 2 or valid.Revenue.nunique() != 2:
            raise ValueError(f'Both classes required in fold ending in {later}.')
        folds.append((fit, valid))
    return folds


def _sample_grid(space, count, seed):
    """Uniform sample of unique Cartesian indices without building the grid."""
    names = tuple(space)
    sizes = [len(space[name]) for name in names]
    total = math.prod(sizes)
    if count > total:
        raise ValueError('Requested more configurations than the grid contains.')
    rng = np.random.default_rng(seed)
    indices = rng.choice(total, size=count, replace=False)
    out = []
    for index in indices:
        values = {}
        remainder = int(index)
        for name, size in reversed(list(zip(names, sizes))):
            remainder, digit = divmod(remainder, size)
            values[name] = space[name][digit]
        out.append({name: values[name] for name in names})
    return out


def _boosting_grid(seed):
    """Guarantee ten variants for every learning-rate × iteration pair."""
    rows = []
    other = {'max_leaf_nodes': (5, 7, 15, 31),
             'min_samples_leaf': (10, 20, 40, 80),
             'l2_regularization': (0, 0.1, 1, 5, 10)}
    for pair_no, (rate, iterations) in enumerate(product(
            (0.01, 0.03, 0.05, 0.1, 0.2), (100, 200, 400, 800))):
        for extra in _sample_grid(other, 10, seed + pair_no):
            rows.append({'learning_rate': rate, 'max_iter': iterations, **extra})
    return rows


def candidate_grids(seed):
    """Fixed ranges and seeded samples; XGB weight modes use each fold's train."""
    logistic = [{'C': c, 'class_weight': weight}
                for c, weight in product(
                    (0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100),
                    (None, 'balanced'))]
    forest = _sample_grid({
        'n_estimators': (200, 400, 800),
        'max_depth': (None, 6, 10, 14, 20),
        'min_samples_leaf': (2, 5, 10, 20, 40),
        'min_samples_split': (2, 5, 10, 20),
        'max_features': ('sqrt', 'log2', 0.3, 0.5, 0.8, 1.0),
        'class_weight': (None, 'balanced', 'balanced_subsample'),
        'criterion': ('gini', 'entropy', 'log_loss'),
    }, COUNTS['random_forest'], seed + 11)
    boosting = _boosting_grid(seed + 22)
    xgboost = _sample_grid({
        'n_estimators': (100, 200, 400, 800),
        'learning_rate': (0.01, 0.03, 0.05, 0.1),
        'max_depth': (2, 3, 4, 5, 6),
        'min_child_weight': (1, 3, 5, 10),
        'subsample': (0.6, 0.8, 1.0),
        'colsample_bytree': (0.5, 0.7, 1.0),
        'reg_alpha': (0, 0.1, 1),
        'reg_lambda': (1, 3, 10),
        'scale_pos_weight': ('one', 'sqrt_train_ratio', 'train_ratio'),
    }, COUNTS['xgboost'], seed + 33)
    grids = {'logistic': logistic, 'random_forest': forest,
             'gradient_boosting': boosting, 'xgboost': xgboost}
    for name, grid in grids.items():
        keys = [json.dumps(item, sort_keys=True) for item in grid]
        if len(grid) != COUNTS[name] or len(set(keys)) != len(keys):
            raise AssertionError(f'Non-unique or incomplete {name} grid.')
    return grids


def _classifier(family, parameters, seed, y_train):
    params = parameters.copy()
    if family == 'logistic':
        return LogisticRegression(max_iter=2000, penalty='l2', random_state=seed,
                                  **params)
    if family == 'random_forest':
        return RandomForestClassifier(n_jobs=1, random_state=seed, **params)
    if family == 'gradient_boosting':
        return HistGradientBoostingClassifier(early_stopping=False,
                                               random_state=seed, **params)
    if family == 'xgboost':
        mode = params.pop('scale_pos_weight')
        ratio = float(np.count_nonzero(y_train == 0) / np.count_nonzero(y_train == 1))
        weight = {'one': 1.0, 'sqrt_train_ratio': math.sqrt(ratio),
                  'train_ratio': ratio}[mode]
        return XGBClassifier(objective='binary:logistic', eval_metric='logloss',
                             tree_method='hist', n_jobs=1, random_state=seed,
                             scale_pos_weight=weight, **params)
    raise ValueError(f'Unknown tuning family: {family}')


def _encoded_folds(train):
    """Fit one preprocessing object per fold TRAIN; reuse immutable arrays."""
    encoded = []
    for fit, valid in temporal_folds(train):
        prep = build_preprocessing(False)
        x_fit = prep.fit_transform(prepare_features(fit))
        x_valid = prep.transform(prepare_features(valid))
        encoded.append((x_fit, fit.Revenue.to_numpy(), x_valid,
                        valid.Revenue.to_numpy()))
    return encoded


def _fold_scores(family, parameters, seed, folds):
    started = perf_counter()
    scores = []
    for x_fit, y_fit, x_valid, y_valid in folds:
        model = _classifier(family, parameters, seed, y_fit)
        model.fit(x_fit, y_fit)
        scores.append(float(average_precision_score(
            y_valid, model.predict_proba(x_valid)[:, 1])))
    return scores, perf_counter() - started


def _complexity(family, params):
    """Fixed last-resort preference only among practically tied AP variants."""
    if family == 'logistic':
        return (params['class_weight'] is not None, -params['C'])
    if family == 'random_forest':
        return (params['n_estimators'], params['max_depth'] or 1000,
                -params['min_samples_leaf'])
    if family == 'gradient_boosting':
        return (params['max_iter'], params['max_leaf_nodes'])
    return (params['n_estimators'], params['max_depth'],
            params['subsample'] != 1.0)


def choose_stable_family(family, rows):
    """Within 0.001 of top mean AP: lower std, then simpler settings."""
    best_mean = max(row['stability_mean_ap'] for row in rows)
    tied = [row for row in rows if best_mean - row['stability_mean_ap'] < 0.001]
    return min(tied, key=lambda row: (row['stability_std_ap'],
                                      _complexity(family, json.loads(row['parameters']))))


def choose_overall(family_rows):
    """Outer Sep-Oct AP only; never accepts or reads test scores."""
    return max(family_rows, key=lambda row: row['validation_ap'])


def _write_plots(all_rows, top_rows, family_rows, test_rows, output):
    top = sorted(top_rows, key=lambda row: row['stability_mean_ap'],
                 reverse=True)[:20][::-1]
    fig, ax = plt.subplots(figsize=(9, 7))
    names = [f"{row['family']} #{row['candidate_id']}" for row in top]
    ax.barh(names, [row['stability_mean_ap'] for row in top],
            xerr=[row['stability_std_ap'] for row in top], color='#467ba5')
    ax.set_xlabel('Temporal AP (mean ± std)')
    fig.tight_layout()
    fig.savefig(output / 'top_candidates.png', dpi=180)
    plt.close(fig)

    families = [row['family'] for row in family_rows]
    tests = {row['family']: row for row in test_rows}
    x = np.arange(len(families))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for offset, label, values in [
        (-0.25, 'Temporal folds', [row['temporal_mean_ap'] for row in family_rows]),
        (0, 'Sep-Oct', [row['validation_ap'] for row in family_rows]),
        (0.25, 'Nov-Dec exploratory', [tests[name]['average_precision'] for name in families]),
    ]:
        ax.bar(x + offset, values, width=0.24, label=label)
    ax.set_xticks(x, ['LR', 'RF', 'HGB', 'XGB'])
    ax.set_ylabel('AP')
    ax.legend()
    ax.grid(axis='y', alpha=0.2)
    fig.tight_layout()
    fig.savefig(output / 'family_comparison.png', dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, family, parameter in [
        (axes[0], 'random_forest', 'min_samples_leaf'),
        (axes[1], 'xgboost', 'max_depth'),
    ]:
        frame = pd.DataFrame([{'value': str(json.loads(row['parameters'])[parameter]),
                               'ap': row['mean_ap']}
                              for row in all_rows if row['family'] == family])
        grouped = frame.groupby('value').ap.agg(['mean', 'std']).sort_index()
        ax.bar(grouped.index, grouped['mean'], yerr=grouped['std'], capsize=3)
        ax.set_title(f'{family}: {parameter}')
        ax.set_ylabel('Mean temporal AP across sampled settings')
    fig.tight_layout()
    fig.savefig(output / 'parameter_effects.png', dpi=180)
    plt.close(fig)


def _summary(grids, fits, family_rows, test_rows, overall, output):
    tests = {row['family']: row for row in test_rows}
    selected = tests[overall['family']]
    delta = selected['average_precision'] - ORIGINAL_TEST_AP['random_forest']
    if delta >= 0.02:
        conclusion = 'Expanded tuning found additional performance beyond the original small grid.'
    elif delta > 0:
        conclusion = 'Expanded tuning produced only a small improvement; the original grid was not the main bottleneck.'
    else:
        conclusion = 'Broad tuning did not reveal a hidden performance reserve; features/data may be a larger limitation.'
    lines = ['# EXTENDED HYPERPARAMETER STUDY', '',
             'Post-test exploratory: Nov-Dec was inspected in earlier project stages, '
             'although no Nov-Dec result selected these parameters, thresholds or model family.', '',
             'Tested configurations: ' + ', '.join(f'{name} {len(grid)}' for name, grid in grids.items()),
             f'Total unique configurations: {sum(map(len, grids.values()))}; total model fits: {fits}.',
             'Temporal folds: Feb-Mar → May; Feb-Mar-May → June; +June → Jul; +Jul → Aug.', '',
             '| Family | Parameters | Temporal AP mean ± std | Sep-Oct AP | Nov-Dec AP |',
             '|---|---|---:|---:|---:|']
    for row in family_rows:
        family = row['family']
        lines.append(f"| {family} | `{row['parameters']}` | "
                     f"{row['temporal_mean_ap']:.4f} ± {row['temporal_std_ap']:.4f} | "
                     f"{row['validation_ap']:.4f} | {tests[family]['average_precision']:.4f} |")
    lines += ['', 'Comparison with the original Sep-Oct validation AP:']
    for row in family_rows:
        if row['family'] in ORIGINAL_VALIDATION_AP:
            old = ORIGINAL_VALIDATION_AP[row['family']]
            lines.append(f"- {row['family']}: original {old:.4f}, tuned "
                         f"{row['validation_ap']:.4f}, delta {row['validation_ap'] - old:+.4f}.")
    lines += ['', f"Overall Sep-Oct validation winner: **{overall['family']}**; "
              f"threshold {overall['threshold']:.2f}; Sep-Oct AP {overall['validation_ap']:.4f}.",
              f"Exploratory Nov-Dec: AP {selected['average_precision']:.4f}, "
              f"Brier {selected['brier']:.4f}, precision {selected['precision']:.4f}, "
              f"recall {selected['recall']:.4f}, F2 {selected['f2']:.4f}.",
              'Original Nov-Dec AP: baseline 0.2066, LR 0.3336, RF 0.3411, HGB 0.3392.',
              f'Delta versus original RF: {delta:+.4f}.', conclusion, '',
              'Hyperparameters and family were chosen without Nov-Dec results; because that '
              'period was already inspected, this is not independent confirmation.']
    body = '\n'.join(lines) + '\n'
    (output / 'SUMMARY.md').write_text(body, encoding='utf-8')
    print('\n' + '=' * 37 + '\nEXTENDED HYPERPARAMETER STUDY\n' + '=' * 37)
    print('\n'.join(lines[4:]))
    print('=' * 37, flush=True)
    return body


def run_extended_tuning(train, validation, test, seed, output, jobs=None):
    """Run broad search after primary analysis; keep all outputs in tuning/."""
    output = Path(output) / 'tuning'
    output.mkdir(parents=True, exist_ok=True)
    jobs = jobs or min(4, os.cpu_count() or 1)
    grids = candidate_grids(seed)
    folds = _encoded_folds(train)
    all_rows = []
    top_rows = []
    fits = 0
    for family, grid in grids.items():
        print(f'{family}: 0/{len(grid)}', flush=True)
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = [pool.submit(_fold_scores, family, params, seed, folds)
                       for params in grid]
            for index, (params, future) in enumerate(zip(grid, futures), 1):
                scores, seconds = future.result()
                row = {'family': family, 'candidate_id': index,
                       'parameters': json.dumps(params, sort_keys=True),
                       **{f'fold_{number}_ap': score for number, score in enumerate(scores, 1)},
                       'mean_ap': float(np.mean(scores)),
                       'median_ap': float(np.median(scores)),
                       'std_ap': float(np.std(scores)),
                       'min_ap': min(scores), 'max_ap': max(scores),
                       'training_seconds': seconds}
                all_rows.append(row)
                fits += len(folds)
                if index % 10 == 0 or index == len(grid):
                    print(f'{family}: {index}/{len(grid)}', flush=True)
        pd.DataFrame(all_rows).to_csv(output / 'all_candidates.csv', index=False)
        top = sorted((row for row in all_rows if row['family'] == family),
                     key=lambda row: row['mean_ap'], reverse=True)[:10]
        for row in top:
            params = json.loads(row['parameters'])
            seeds = STABILITY_SEEDS if family in ('random_forest', 'xgboost') else (seed,)
            repeated = []
            for repeat_seed in seeds:
                scores, _ = _fold_scores(family, params, repeat_seed, folds)
                repeated.extend(scores)
                fits += len(folds)
            top_rows.append({**row, 'stability_seeds': json.dumps(seeds),
                             'stability_mean_ap': float(np.mean(repeated)),
                             'stability_std_ap': float(np.std(repeated)),
                             'stability_min_ap': min(repeated),
                             'stability_max_ap': max(repeated)})
        pd.DataFrame(top_rows).to_csv(output / 'top_candidates.csv', index=False)
    pd.DataFrame([{key: value for key, value in row.items()
                   if key in ('family', 'candidate_id', 'parameters', 'stability_seeds',
                              'stability_mean_ap', 'stability_std_ap',
                              'stability_min_ap', 'stability_max_ap')}
                  for row in top_rows]).to_csv(output / 'stability_results.csv', index=False)

    # The outer validation sees one fixed candidate from each family, not test.
    x_train = prepare_features(train)
    x_validation = prepare_features(validation)
    y_train = train.Revenue.to_numpy()
    y_validation = validation.Revenue.to_numpy()
    family_rows = []
    fitted = {}
    for family in grids:
        winner = choose_stable_family(family,
                    [row for row in top_rows if row['family'] == family])
        params = json.loads(winner['parameters'])
        model = Pipeline([('preprocessing', build_preprocessing(False)),
                          ('classifier', _classifier(family, params, seed, y_train))])
        model.fit(x_train, y_train)
        fits += 1
        probability = model.predict_proba(x_validation)[:, 1]
        threshold = select_threshold(y_validation, probability)
        row = {'family': family, 'parameters': winner['parameters'],
               'temporal_mean_ap': winner['stability_mean_ap'],
               'temporal_std_ap': winner['stability_std_ap'],
               'validation_ap': float(average_precision_score(y_validation, probability)),
               'validation_brier': float(brier_score_loss(y_validation, probability)),
               'validation_log_loss': float(log_loss(y_validation, probability)),
               'threshold': threshold}
        family_rows.append(row)
        fitted[family] = model
    overall = choose_overall(family_rows)
    pd.DataFrame(family_rows).to_csv(output / 'family_winners.csv', index=False)
    (output / 'best_configuration.json').write_text(json.dumps({
        'selection_rule': 'highest Sep-Oct validation AP after temporal stability tie rule',
        'family': overall['family'], 'parameters': json.loads(overall['parameters']),
        'validation_ap': overall['validation_ap'], 'threshold': overall['threshold'],
        'test_used_for_selection': False, 'post_test_exploratory': True,
    }, indent=2) + '\n', encoding='utf-8')

    # Only now inspect Nov-Dec, once per fixed family choice; never reselect.
    x_test = prepare_features(test)
    y_test = test.Revenue.to_numpy()
    test_rows = []
    for row in family_rows:
        family = row['family']
        probability = fitted[family].predict_proba(x_test)[:, 1]
        result = metrics(y_test, probability, row['threshold'])
        result.update({'family': family, 'parameters': row['parameters'],
                       'overall_validation_winner': family == overall['family'],
                       'f1': float(f1_score(y_test, probability >= row['threshold'],
                                            zero_division=0)),
                       'post_test_exploratory': True})
        test_rows.append(result)
    pd.DataFrame(test_rows).to_csv(output / 'final_test_results.csv', index=False)
    _write_plots(all_rows, top_rows, family_rows, test_rows, output)
    summary = _summary(grids, fits, family_rows, test_rows, overall, output)
    return {'winner': overall, 'test_results': test_rows, 'summary': summary,
            'total_fits': fits}
