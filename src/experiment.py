"""Pagrindinė eiga: python -m src.experiment. Skaitykite run() nuo viršaus.

Modelių mokymas → training.py; papildomi bandymai → analysis.py;
grafikai → plots.py; rezultatų failai → reporting.py.
"""
import argparse
import json
from pathlib import Path
from time import perf_counter
import joblib
from threadpoolctl import threadpool_limits
from .data import load_and_split, prepare_features
from .training import train_and_select
from .evaluation import metrics
from .analysis import evaluate_missing, analyze_forest
from .plots import save_plots
from .reporting import save_splits, save_tables, save_manifest, save_summary

ROOT = Path(__file__).resolve().parents[1]
# KEITIMO VIETA: vienas sąrašas mokymui, atsparumui ir grafikams.
# RF ir logistic palikite: jie reikalingi iš anksto numatytai hipotezei.
PRIMARY_MODELS = ['purchase_rate', 'logistic', 'random_forest', 'gradient_boosting']


def run(config_path=ROOT / 'config.json', output=ROOT / 'results'):
    """Nuosekliai atlieka 10 eksperimento etapų ir išsaugo rezultatus.

    config_path – JSON kelias; output – lentelių bei grafikų katalogas.
    Modeliai visada rašomi į ROOT/models, net jei pakeistas output.
    """
    # 1. Nustatymai ir katalogai. perf_counter matuoja trukmę sekundėmis.
    started = perf_counter()
    config = json.loads(Path(config_path).read_text())
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    model_dir = ROOT / 'models'
    model_dir.mkdir(exist_ok=True)
    # 2. Duomenų skaidymas. Revenue yra atsakymas; į požymius jis nepateks.
    data, parts = load_and_split(ROOT / 'data/online_shoppers_intention.csv', config)
    train = parts['train']
    validation = parts['validation']
    test = parts['test']
    y_train = train['Revenue'].to_numpy()
    y_validation = validation['Revenue'].to_numpy()
    y_test = test['Revenue'].to_numpy()

    save_splits(parts, config, output)

    # 3. Pagrindiniai modeliai ir atskiras PageValues jautrumo bandymas.
    selection = []       # Visų kandidatų validacijos AP ir parametrai.
    table = []           # Viena metrikų eilutė kiekvienam modeliui ir scenarijui.
    predictions = {}     # Bandymo vardas → testo tikimybių masyvas.
    fitted = {}          # Bandymo vardas → pasirinktas modelis ir jo slenkstis.

    specifications = []
    for name in PRIMARY_MODELS:
        specifications.append({
            'label': name, 'name': name, 'include_page_values': False,
        })
    specifications.append({
        'label': 'random_forest_with_page_values',
        'name': 'random_forest',
        'include_page_values': True,
    })

    # 4. Kiekvieną metodą mokome atskirai. Pagrindinių metodų imtys vienodos.
    for specification in specifications:
        label = specification['label']
        name = specification['name']
        page_values = specification['include_page_values']
        x_train = prepare_features(train, page_values)
        x_validation = prepare_features(validation, page_values)
        x_test = prepare_features(test, page_values)

        selected, candidate_results = train_and_select(
            name, label, x_train, y_train, x_validation, y_validation,
            config['seed'], page_values,
        )
        selection.extend(candidate_results)
        best_model = selected['model']
        threshold = selected['threshold']

        # Tik DABAR naudojame testą: pasirinkimas ir slenkstis jau užfiksuoti.
        probability = best_model.predict_proba(x_test)[:, 1]
        predictions[label] = probability
        fitted[label] = selected

        row = metrics(y_test, probability, threshold)
        row['model'] = label
        row['scenario'] = 'clean'
        row['validation_ap'] = selected['validation_ap']
        row['selection_seconds'] = selected['selection_seconds']
        table.append(row)

        # Išsaugome visą grandinę, kad predict.py nereikėtų mokyti iš naujo.
        artifact = {
            'model': best_model,
            'threshold': threshold,
            'include_page_values': page_values,
            'features': list(x_train.columns),
            'parameters': selected['parameters'],
            'seed': config['seed'],
        }
        joblib.dump(artifact, model_dir / f'{label}.joblib')
        print(label, 'validation AP:', round(selected['validation_ap'], 4),
              'test AP:', round(row['average_precision'], 4), flush=True)

    # 5. Atskirame modulyje sugadiname testo kopiją ir pamatuojame atsparumą.
    missing_rows, missing_mask = evaluate_missing(
        test, fitted, PRIMARY_MODELS, config['missing_fraction'], config['seed'],
    )
    table.extend(missing_rows)

    # 6. Išsaugome jau apskaičiuotus skaičius.
    result = save_tables(table, selection, test, predictions, output)

    # 7. RF formulės patikra, klaidos, pogrupiai ir palyginimo intervalas.
    formula_error, interval = analyze_forest(
        test, fitted, predictions, config['bootstrap_repetitions'],
        config['seed'], output,
    )

    # 8. PR kreivė rodo precision ir recall kompromisą, kalibracija – tikimybių kokybę.
    save_plots(y_test, predictions, output, PRIMARY_MODELS)
    clean = result.loc[result.scenario == 'clean'].set_index('model')
    forest_ap = clean.loc['random_forest', 'average_precision']
    logistic_ap = clean.loc['logistic', 'average_precision']
    delta = float(forest_ap - logistic_ap)
    # 9. Išsaugome, kokiu kodu ir kokiomis sąlygomis gauti rezultatai.
    save_manifest(ROOT, config, data, formula_error, delta, interval,
                  missing_mask, started, output)
    # 10. Iš tų pačių skaičių sukuriame žmogui skaitomą Markdown lentelę.
    save_summary(table, delta, interval, formula_error, output)
    print('Experiment complete:', output, flush=True)


# Šis blokas vykdomas paleidus failą kaip modulį, bet ne jį importavus.
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, default=ROOT / 'config.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'results')
    args = parser.parse_args()
    # Vienas skaičiavimo srautas mažina vykdymo skirtumus tarp paleidimų.
    with threadpool_limits(limits=1):
        run(args.config, args.output)
