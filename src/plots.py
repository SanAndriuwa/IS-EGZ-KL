"""Grafikų braižymas iš jau apskaičiuotų prognozių; modelių nemoko."""
import argparse
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.metrics import precision_recall_curve

def save_plots(y_test, predictions, output, model_names):
    """Iš jau apskaičiuotų tikimybių įrašo PR ir kalibracijos grafikus.

    Čia modeliai nemokomi ir nekalibruojami. Skaitome tik galutinio testo išvestį.
    """
    # axes[0] – kairysis grafikas, axes[1] – dešinysis.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout='constrained')
    for name in model_names:
        probability = predictions[name]
        precision, recall, _ = precision_recall_curve(y_test, probability)
        axes[0].step(recall, precision, where='post', label=name)
        # Suskirstome tikimybes į 8 grupes ir palyginame vidurkį su pirkimų dalimi.
        observed, predicted = calibration_curve(y_test, probability, n_bins=8, strategy='quantile')
        axes[1].plot(predicted, observed, marker='o', label=name)
    axes[0].axhline(y_test.mean(), linestyle=':', color='gray', label='test prevalence')
    axes[0].set(xlabel='Recall', ylabel='Precision', title='Final test', xlim=(0, 1), ylim=(0, 1))
    axes[1].plot([0, 1], [0, 1], '--', color='gray')
    axes[1].set(xlabel='Mean predicted probability', ylabel='Observed purchase rate', title='Calibration (quantile bins)', xlim=(0, 1), ylim=(0, 1))
    for ax in axes:
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)
    fig.savefig(output / 'evaluation.svg')
    fig.savefig(output / 'evaluation.png', dpi=160)
    plt.close(fig)



# Grafikus galima perkurti atskirai, nekartojant mokymo.
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', type=Path, default=Path('results'))
    args = parser.parse_args()
    saved = pd.read_csv(args.results / 'test_predictions.csv')
    scores = pd.read_csv(args.results / 'metrics.csv')
    # Atsparumo bandyme yra tik pagrindiniai modeliai, be PageValues bandymo.
    names = scores.loc[scores['scenario'] != 'clean', 'model'].unique().tolist()
    probabilities = {}
    for name in names:
        probabilities[name] = saved[name].to_numpy()
    save_plots(saved['revenue'].to_numpy(), probabilities, args.results, names)
