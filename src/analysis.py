"""Papildomi bandymai: trūkstamos reikšmės, RF klaidos ir AP skirtumo intervalas."""
import numpy as np
import pandas as pd
from .data import prepare_features, NUMERIC
from .evaluation import metrics, paired_ap_interval
from .models import forest_probability_by_formula

def evaluate_missing(test, fitted, model_names, missing_fraction, seed):
    """Grąžina metrikų eilutes ir kaukę. Išmokytų modelių nekeičia."""
    y_test = test['Revenue'].to_numpy()
    rows = []
    # 5. Atsparumas trūkstamiems duomenims. Visus modelius vertiname ta pačia kauke.
    # rng.random grąžina [0; 1) skaičius. Palyginimas su 0.10 apytiksliai
    # 10 % langelių pažymi True; mask() juos pakeičia NaN (trūkstama reikšmė).
    # Niekas nepermokoma: medianos ir slenksčiai lieka iš ankstesnių etapų.
    damaged = prepare_features(test)
    rng = np.random.default_rng(seed)
    missing_mask = rng.random((len(damaged), len(NUMERIC))) < missing_fraction
    damaged[NUMERIC] = damaged[NUMERIC].mask(missing_mask)
    for label in model_names:
        model = fitted[label]['model']
        threshold = fitted[label]['threshold']
        probability = model.predict_proba(damaged)[:, 1]
        row = metrics(y_test, probability, threshold)
        row['model'] = label
        missing_percent = 100 * missing_fraction
        row['scenario'] = f'missing_numeric_{missing_percent:g}pct'
        rows.append(row)

    return rows, missing_mask

def analyze_forest(test, fitted, predictions, repetitions, seed, output):
    """Įrašo RF klaidas ir pogrupius; grąžina formulės paklaidą ir AP intervalą."""
    y_test = test['Revenue'].to_numpy()
    # 7. Pagrindinio RF analizė. Ši dalis sąmoningai susieta su RF, ne su
    # geriausią testo skaičių gavusiu modeliu. Hipotezė pasirinkta prieš bandymą.
    rf_model = fitted['random_forest']['model']
    rf_threshold = fitted['random_forest']['threshold']
    # Patikriname, ar medžių tikimybių vidurkis sutampa su bibliotekos išvestimi.
    formula = forest_probability_by_formula(rf_model, prepare_features(test))
    formula_error = float(np.max(np.abs(formula - predictions['random_forest'])))
    if not np.allclose(formula, predictions['random_forest'], atol=1e-12):
        raise AssertionError('Forest equation does not match sklearn probabilities.')
    # FP – nepirko, nors prognozė teigiama. FN – pirko, nors prognozė neigiama.
    # Paimame 5 aukščiausios tikimybės FP ir 5 žemiausios tikimybės FN.
    errors = test.copy()
    errors['probability'] = predictions['random_forest']
    errors['prediction'] = (errors.probability >= rf_threshold).astype(int)
    false_positive_rows = (errors['Revenue'] == 0) & (errors['prediction'] == 1)
    false_negative_rows = (errors['Revenue'] == 1) & (errors['prediction'] == 0)
    fp = errors.loc[false_positive_rows].nlargest(5, 'probability')
    fn = errors.loc[false_negative_rows].nsmallest(5, 'probability')
    pd.concat([fp.assign(error='FP'), fn.assign(error='FN')]).to_csv(output / 'error_examples.csv')
    # Atskirai vertiname mėnesius ir lankytojų tipus. Tai ne naujas mokymas.
    subgroup = []
    for column in ['Month', 'VisitorType']:
        for group, subset in test.groupby(column):
            # Originalūs eilučių indeksai nebūtinai 0, 1, 2...; randame jų
            # pozicijas bendrame testo masyve, kad sutaptų sesijos ir tikimybės.
            positions = test.index.get_indexer(subset.index)
            if subset.Revenue.nunique() == 2:
                group_probabilities = predictions['random_forest'][positions]
                row = {
                    'column': column,
                    'group': group,
                    'rows': len(subset),
                    'purchase_rate': float(subset.Revenue.mean()),
                }
                # update() į tą patį žodyną prideda visas apskaičiuotas metrikas.
                row.update(metrics(subset.Revenue, group_probabilities, rf_threshold))
                subgroup.append(row)
    pd.DataFrame(subgroup).to_csv(output / 'subgroups.csv', index=False)
    # Porinis bootstrap: abu modelius lyginame tose pačiose perrinktose eilutėse.
    interval = paired_ap_interval(y_test, predictions['random_forest'], predictions['logistic'],
                                  repetitions, seed)
    return formula_error, interval
