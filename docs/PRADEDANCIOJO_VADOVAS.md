# Kodas kaip laboratorinis darbas

Tikslas – skaityti veiksmus iš eilės ir suprasti, kur ką keisti. Panašiai kaip
`testing4H.m` atskiria parametrus, mokymą ir testavimą, šiame projekte atskirtos
atsakomybės. Naudojame paprastas funkcijas, `for` ciklus ir `if/elif`.
Sklearn vis dar atlieka pačių klasifikatorių mokymą: šis projektas neperrašo
atsitiktinio miško ar logistinės regresijos algoritmo nuo nulio.

## 1. Failas ir funkcija – skirtingi dalykai

`.py` failas gali turėti kelias susijusias funkcijas. `from .training import
train_and_select` reiškia „iš šalia esančio training.py paimti funkciją“.
Importas modelio nemoko. Mokymas prasideda tik iškvietus funkciją ir jos `fit()`.
Funkcijoms perduodame duomenis argumentais: jos nesiremia ankstesnio skripto
paliktais kintamaisiais. Taip lengviau patikrinti, iš kur atsirado rezultatas.

| Failas | Viena pagrindinė atsakomybė | Ką čia keisti |
|---|---|---|
| `config.json` | Eksperimento nustatymai | Sėkla, mėnesiai, trūkumo dalis, bootstrap kartojimai |
| `data.py` | CSV patikra, požymiai ir imtys | Stulpeliai ir skaidymo taisyklės |
| `preprocessing.py` | Požymių pavertimas skaitine matrica | Užpildymas, mastelis, kategorijų kodavimas |
| `models.py` | Klasifikatoriaus sukūrimas | Modelio parametrai ir jų variantai |
| `training.py` | Kandidatų mokymas ir pasirinkimas | Validacijos kriterijus |
| `evaluation.py` | Metrikų ir slenksčio skaičiavimas | F2, slenksčių tinklas, metrikos |
| `experiment.py` | Visa eiga nuo pradžios iki pabaigos | Pagrindinių modelių sąrašas ir etapų tvarka |
| `analysis.py` | Papildomi bandymai ir RF analizė | Trūkstamos reikšmės, klaidų pavyzdžiai, pogrupiai |
| `plots.py` | Grafikų braižymas | Spalvos, pavadinimai, dydžiai |
| `reporting.py` | Skaičių išsaugojimas | CSV ir Markdown išvesties formatas |
| `predict.py` | Išmokyto modelio taikymas | Naujo CSV prognozavimas |

## 2. Kaip paleisti

Komandas vykdykite projekto kataloge, kuriame yra `config.json` ir `src`.
Pirmiausia įdiekite priklausomybes pagal README.

```bash
# Visas darbas: mokymas, testas, analizė, lentelės ir grafikai.
python -m src.experiment

# Tik grafikai iš jau turimų rezultatų; mokymo nekartoja.
python -m src.plots --results results

# Tik naujų sesijų prognozė; modelis turi būti jau išmokytas.
python -m src.predict --input examples/unseen_sessions.csv
```

`-m src.experiment` nurodo Python paleisti modulį pakete `src`. Nenaudokite
`python src/experiment.py`, nes santykiniai importai skirti modulio paleidimui.
`training.py`, `analysis.py`, `models.py`, `preprocessing.py`, `reporting.py`
yra importuojami pagalbiniai moduliai, o ne atskiros komandinės programos.
Vien failo paleidimas jų funkcijų automatiškai neiškviečia.

## 3. Kas vyksta experiment.run() viduje

1. Perskaitomi nustatymai ir sukuriami išvesties katalogai.
2. CSV padalijamas į `train`, `validation`, `test`; `Revenue` tampa atsakymu.
3. Sudaromas pagrindinių modelių ir atskiro PageValues bandymo sąrašas.
4. Ciklas ima vieną modelį, paruošia požymius, kviečia `train_and_select`,
   prognozuoja testą ir išsaugo visą modelį su transformacijomis.
5. `evaluate_missing` sugadina testo kopijos skaitinius langelius ir vertina
   tuos pačius modelius. Modeliai nepermokomi.
6. `save_tables` išsaugo metrikas, kandidatų palyginimą ir testo prognozes.
7. `analyze_forest` tikrina medžių tikimybių vidurkį, nagrinėja klaidas,
   pogrupius ir apskaičiuoja RF bei logistinės regresijos AP skirtumo intervalą.
8. `save_plots` nubraižo PR ir kalibracijos grafikus.
9. `save_manifest` išsaugo vykdymo sąlygas bei kodo kontrolines sumas.
10. `save_summary` tuos pačius rezultatus surašo į Markdown lentelę.

## 4. Kintamieji paprastai

| Kintamasis | Kas jame yra |
|---|---|
| `x_train` | Požymių lentelė; viena eilutė – viena sesija |
| `y_train` | Atsakymai toms pačioms eilutėms: 0 nepirko, 1 pirko |
| `parameters` | Vieno kandidato nustatymai, pvz. `{'min_samples_leaf': 5}` |
| `model` | Požymių paruošimo ir klasifikatoriaus Pipeline |
| `probability` | Po vieną P(pirks) kiekvienai testo sesijai |
| `threshold` | Slenkstis: tikimybė ≥ slenkstis reiškia prognozę 1 |
| `selected` | Pasirinktas modelis, parametrai, validacijos AP, slenkstis ir trukmė |
| `fitted` | Visų išmokytų bandymų `selected` žodynai pagal vardą |
| `predictions` | Testo tikimybių masyvai pagal bandymo vardą |
| `table` | Metrikų žodynų sąrašas; vėliau tampa CSV lentele |

`[]` su vardu paima žodyno lauką: `selected['model']` yra pats modelis.
`append(row)` prideda vieną eilutę, `extend(rows)` – kelias eilutes.
Tai duomenų laikymas, ne papildomas mokymas.

## 5. Vieno modelio mokymas, eilutė po eilutės

```python
from src.data import load_and_split, prepare_features
from src.models import build_model
import json

config = json.load(open('config.json'))
data, parts = load_and_split('data/online_shoppers_intention.csv', config)
x_train = prepare_features(parts['train'])
y_train = parts['train']['Revenue']
x_validation = prepare_features(parts['validation'])

# Sukuriamas tuščias, dar neišmokytas modelis.
parameters = {'n_estimators': 100, 'min_samples_leaf': 10}
model = build_model('random_forest', seed=42, params=parameters)
# Išmokstamos medianos, masteliai, kategorijos ir medžiai tik iš train.
model.fit(x_train, y_train)
# Taikome išmoktas taisykles; naujo mokymo čia nėra.
two_columns = model.predict_proba(x_validation)
probabilities = two_columns[:, 1]
```

`two_columns` turi P(nepirks) ir P(pirks). `[:, 1]` paima visas eilutes ir
antrą stulpelį, nes Python numeruoja nuo 0. Tai teisinga šiam dvejetainiam
uždaviniui su klasėmis `[0, 1]`. Pavyzdys moko vieną kandidatą; pilnas
`training.py` ciklas palygina visus `candidates(name)` variantus.

`train_and_select()` pradeda su `best_score = -1`. Kiekvienam kandidatui
sukuria naują modelį, išmoko jį su train, apskaičiuoja validacijos AP ir
įsimena geriausią. Lygybės atveju lieka pirmas kandidatas. Tada tik iš
validacijos parenka F2 slenkstį. Testo ši funkcija apskritai negauna.

## 6. Kur daryti korekcijas

**Medžių skaičius:** `models.py`, RandomForestClassifier `n_estimators=200`
pakeiskite, pavyzdžiui, į `100`. Tai mažiau medžių, bet nebūtinai geresnė kokybė.

**Išbandomi variantai:** `candidates('random_forest')` šakoje galite naudoti:

```python
return [
    {'min_samples_leaf': 5},
    {'min_samples_leaf': 10},
    {'min_samples_leaf': 20},
]
```

Kiekvienas žodynas yra vienas mokymas. Jei norite tik vieno bandymo, palikite
vieną žodyną. Žodyno reikšmės pakeičia modelio numatytus parametrus per
`set_params(**params)`; `**` perduoda žodyno laukus kaip vardinius argumentus.

**Naujas modelis:** pridėkite importą, `elif` šaką `build_model`, variantus
`candidates` ir vardą `experiment.PRIMARY_MODELS`. Grafikų ir atsparumo
sąrašuose jo kartoti nereikia. Klasifikatorius turi palaikyti `predict_proba`.
RF ir logistic palikite sąraše: jų reikia dabartinei hipotezei ir analizei.

**Slenkstis:** keiskite `evaluation.select_threshold`. Slenkstis parenkamas
validacijoje. Jis keičia 0/1 sprendimus, precision ir recall, bet nekeičia
jau apskaičiuotų tikimybių ar jų AP.

**Grafikai:** keiskite tik `plots.py`, tada vykdykite `python -m src.plots`.
`--results` turi rodyti katalogą su to paties eksperimento
`test_predictions.csv` ir `metrics.csv`.

**Naujas požymis:** keiskite `data.NUMERIC` arba `data.CATEGORICAL`, tikrinkite
`prepare_features` ir permokykite. Revenue neturi patekti į požymius.
Kitas mokymo CSV reikalauja pritaikyto įkėlimo: dabar tikrinamas originalaus
UCI failo SHA256. Naujas prognozių CSV palaikomas per `predict` be šios sumos.

## 7. Ką išsaugome ir kaip tikrinti

`results/` gauna CSV, SVG, PNG, RESULTS.md ir manifest.json. `models/` gauna
joblib failus su modeliu, slenksčiu ir nustatymais. `--output` pakeičia tik
rezultatų katalogą; modeliai vis dar perrašomi `models/`. Rankinė ATASKAITA.md
po parametrų keitimo automatiškai neperskaičiuojama.

```bash
python -m unittest discover -s tests -v
python -m src.experiment --output results/changed_variant
python -m src.predict --input examples/unseen_sessions.csv
```

Po struktūros pakeitimo lyginkite prognozes ir metrikas. Trukmė, kodo sumos
ir aplinkos informacija gali skirtis. Po parametrų pakeitimo rezultatai gali
pasikeisti; tada reikia juos paaiškinti ir atnaujinti ataskaitą.

Paprastesnė struktūra nekeičia taisyklės: mokome su train, pasirenkame su
validation, galutinį vertinimą atliekame su test. Sąmoningai peržiūrėto testo
pagrindu taisyti modelį ir vėl vadinti tą testą nepriklausomu būtų klaida.
