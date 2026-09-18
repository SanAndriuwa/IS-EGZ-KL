"""Modelių sukūrimas ir jų parametrų variantai.

Skaitymo tvarka naujokui:
1. build_model() paruošia duomenų apdorojimo grandinę ir klasifikatorių.
2. candidates() nurodo, kokius parametrus bandys experiment.py.
3. forest_probability_by_formula() parodo RF tikimybės skaičiavimą.

Šiame faile modeliai dar NEMOKOMI. Mokymas prasideda iškvietus model.fit(X, y).
X – požymiai (viena sesija eilutėje), y – teisingi atsakymai (0 arba 1).
"""
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from .preprocessing import build_preprocessing
from sklearn.pipeline import Pipeline


def build_model(name, seed, params=None, include_page_values=False):
    """Grąžina neišmokytą grandinę: požymių paruošimas → klasifikatorius.

    name: 'purchase_rate', 'logistic', 'random_forest' arba 'gradient_boosting'.
    seed: atsitiktinė sėkla, kad bandymą galėtume pakartoti.
    params: vienas parametrų variantas, pvz., {'min_samples_leaf': 20}.
    include_page_values: ar įtraukti papildomai tiriamą PageValues požymį.

    Pavyzdys: model = build_model('random_forest', 42)
              model.fit(x_train, y_train)
    """
    # 1. Bendras stulpelių paruošimas aprašytas preprocessing.py.
    preprocessing = build_preprocessing(include_page_values)

    # 2. Paprastas if/elif leidžia aiškiai matyti, kurį modelį kuriame.
    if name == 'purchase_rate':
        # Visoms sesijoms prognozuos vienodą mokymo imties pirkimų dalį.
        classifier = DummyClassifier(strategy='prior')

    elif name == 'logistic':
        # Mokosi požymių svorių; svorių sumą sigmoidė paverčia tikimybe.
        # max_iter – didžiausias optimizavimo iteracijų skaičius, ne sesijų skaičius.
        classifier = LogisticRegression(max_iter=2000, random_state=seed)

    elif name == 'random_forest':
        # KEITIMO VIETA: n_estimators – medžių skaičius.
        # max_features='sqrt' – kiekvienam skaidymui svarstomas atsitiktinis
        # maždaug sqrt(transformuotų požymių skaičius) požymių poaibis.
        classifier = RandomForestClassifier(
            n_estimators=200,
            max_features='sqrt',
            n_jobs=1,
            random_state=seed,
        )

    elif name == 'gradient_boosting':
        # Medžiai pridedami paeiliui, mažinant ankstesnio modelio nuostolį.
        # KEITIMO VIETA: max_iter – stiprinimo iteracijos; learning_rate – žingsnis.
        # early_stopping=False: iš anksto naudojame visas 150 iteracijų,
        # o parametrus lyginame mūsų atskiroje validacijos imtyje.
        classifier = HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.05,
            early_stopping=False,
            random_state=seed,
        )

    else:
        raise ValueError(f'Nežinomas modelis: {name}')

    # 3. Kandidato parametrai pakeičia aukščiau nurodytas numatytas reikšmes.
    # Pavyzdžiui, params={'min_samples_leaf': 20} nustato RF lapo dydį.
    if params is not None:
        classifier.set_params(**params)

    # 4. fit() išmoks ir transformacijas, ir modelį tik pateiktoje mokymo imtyje.
    # predict_proba() naudos tas pačias išmoktas transformacijas jų nekeisdamas.
    model = Pipeline([
        ('preprocessing', preprocessing),
        ('classifier', classifier),
    ])
    return model


def candidates(name):
    """Grąžina atskirai išbandomus parametrų variantus; čia nieko nemokome.

    Kiekvienas sąrašo žodynas reiškia VIENĄ mokymą. Dvi reikšmės viename
    žodyne būtų vieno modelio nustatymai, o ne du atskiri bandymai.
    """
    # KEITIMO VIETA: naują bandymą pridėkite kaip papildomą žodyną sąraše.
    if name == 'purchase_rate':
        return [{}]  # Vienas bandymas be papildomų parametrų.
    elif name == 'logistic':
        # Mažesnis C reiškia stipresnį svorių reguliavimą.
        return [{'C': 0.1}, {'C': 1.0}]
    elif name == 'random_forest':
        # Mažesni lapai leidžia smulkesnes taisykles, bet gali labiau persimokyti.
        return [{'min_samples_leaf': 5}, {'min_samples_leaf': 20}]
    elif name == 'gradient_boosting':
        # Didžiausias lapų skaičius viename medyje riboja jo sudėtingumą.
        return [{'max_leaf_nodes': 7}, {'max_leaf_nodes': 15}]
    else:
        raise ValueError(f'Nežinomas modelis: {name}')


def forest_probability_by_formula(model, features):
    """Patikrina formulę p(x) = visų medžių pirkimo tikimybių vidurkis.

    model – jau išmokyta RF Pipeline; features – sesijų požymių lentelė.
    Grąžinamas masyvas: viena pirkimo tikimybė kiekvienai sesijai.
    """
    # transform(), o ne fit_transform(): testo duomenimis nieko nepermokome.
    preprocessing = model.named_steps['preprocessing']
    encoded_features = preprocessing.transform(features)
    forest = model.named_steps['classifier']

    probabilities_from_trees = []
    for tree in forest.estimators_:
        # Kiekvieno medžio išvestis turi dvi skiltis: P(0) ir P(1).
        # [:, 1] reiškia „visos eilutės, antra skiltis“, t. y. pirkimo tikimybė.
        # Medžio tikimybė gaunama iš pasiekto lapo mokymo klasių dažnių.
        two_class_probabilities = tree.predict_proba(encoded_features)
        purchase_probabilities = two_class_probabilities[:, 1]
        probabilities_from_trees.append(purchase_probabilities)

    # Sąrašo forma: medžiai × sesijos. axis=0 vidurkina medžius,
    # todėl po vidurkinimo lieka viena reikšmė kiekvienai sesijai.
    mean_probabilities = np.mean(probabilities_from_trees, axis=0)
    return mean_probabilities
