"""Metrics, validation-only decision thresholds, and paired uncertainty."""
import numpy as np
from sklearn.metrics import (average_precision_score, auc, brier_score_loss,
                             confusion_matrix, log_loss, precision_recall_curve,
                             precision_score, recall_score, fbeta_score)


def select_threshold(labels, probabilities):
    # A fixed grid avoids selecting a threshold on the final test set.
    grid = np.linspace(0.01, 0.99, 99)
    scores = [fbeta_score(labels, probabilities >= value, beta=2, zero_division=0) for value in grid]
    return float(grid[int(np.argmax(scores))])


def metrics(labels, probabilities, threshold):
    predictions = probabilities >= threshold
    precision, recall, _ = precision_recall_curve(labels, probabilities)
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    return {
        'average_precision': float(average_precision_score(labels, probabilities)),
        'pr_auc_trapezoid': float(auc(recall, precision)),
        'precision': float(precision_score(labels, predictions, zero_division=0)),
        'recall': float(recall_score(labels, predictions, zero_division=0)),
        'f2': float(fbeta_score(labels, predictions, beta=2, zero_division=0)),
        'brier': float(brier_score_loss(labels, probabilities)),
        'log_loss': float(log_loss(labels, probabilities, labels=[0, 1])),
        'threshold': threshold, 'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)
    }


def paired_ap_interval(labels, first, second, repetitions, seed):
    """Stratified paired bootstrap, conditional on this test period and fitted models."""
    rng = np.random.default_rng(seed)
    labels = np.asarray(labels)
    negative, positive = np.flatnonzero(labels == 0), np.flatnonzero(labels == 1)
    differences = []
    for _ in range(repetitions):
        rows = np.concatenate([rng.choice(negative, len(negative), replace=True),
                               rng.choice(positive, len(positive), replace=True)])
        differences.append(average_precision_score(labels[rows], first[rows]) -
                           average_precision_score(labels[rows], second[rows]))
    return np.quantile(differences, [0.025, 0.975]).tolist()
