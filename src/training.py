"""Kandidatų mokymas ir pasirinkimas. Testo duomenų šis modulis negauna."""
import json
from time import perf_counter
from sklearn.metrics import average_precision_score
from .models import build_model, candidates
from .evaluation import select_threshold

def train_and_select(name, label, x_train, y_train, x_validation, y_validation,
                     seed, include_page_values):
    """Išmoko kandidatus, validacijoje parenka vieną modelį ir slenkstį.

    x_* – požymių lentelės, y_* – tikri 0/1 atsakymai.
    name – modelio tipas, label – bandymo vardas rezultatų failuose.
    Testo imties ši funkcija negauna: ji negali pagal testą pasirinkti modelio.
    Grąžina pasirinkto modelio žodyną ir visų kandidatų validacijos rezultatus.
    """
    started = perf_counter()
    best_score = -1.0  # AP negali būti mažesnė už 0; pirmas kandidatas bus priimtas.
    best_model = None
    best_parameters = None
    candidate_results = []

    for parameters in candidates(name):
        # Kiekvienam variantui kuriame NAUJĄ grandinę.
        model = build_model(name, seed, parameters, include_page_values)
        model.fit(x_train, y_train)

        # Dvejetainio modelio skiltys: P(nepirks), P(pirks). Imame antrą.
        validation_probabilities = model.predict_proba(x_validation)[:, 1]
        score = average_precision_score(y_validation, validation_probabilities)
        candidate_results.append({
            'model': label,
            'parameters': json.dumps(parameters),
            'validation_ap': float(score),
        })

        # Griežtas > reiškia, kad lygiųjų atveju lieka pirmas kandidatas.
        if score > best_score:
            best_score = score
            best_model = model
            best_parameters = parameters

    # Modelio parinkimas ir slenkstis yra skirtingi veiksmai.
    # AP vertina rangavimą, o slenkstis tikimybę paverčia atsakymu 0 arba 1.
    # select_threshold() maksimizuoja F2 tik validacijos duomenimis.
    validation_probabilities = best_model.predict_proba(x_validation)[:, 1]
    threshold = select_threshold(y_validation, validation_probabilities)

    selected = {
        'model': best_model,
        'parameters': best_parameters,
        'validation_ap': best_score,
        'threshold': threshold,
        'selection_seconds': perf_counter() - started,
    }
    return selected, candidate_results
