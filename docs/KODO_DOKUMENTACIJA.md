# Kodo dokumentacija ir lankstumas

Šis dokumentas paaiškina programos veikimą, pagrindinių funkcijų sutartis ir konkrečias plėtimo vietas. Dabartinė realizacija yra modulinis, konkrečiam UCI rinkiniui skirtas mokomasis eksperimentas. Ji leidžia keisti dalį bandymo sąlygų per konfigūraciją, tačiau nėra universali bet kokių duomenų ir modelių platforma.

## Nuo ko pradėti naujokui

Pirmiausia skaitykite [nuoseklų failų ir kintamųjų vadovą](PRADEDANCIOJO_VADOVAS.md).
`experiment.py` yra pagrindinė eiga. Skirtingos atsakomybės perkeltos į atskirus
failus: `preprocessing.py`, `training.py`, `analysis.py`, `plots.py`, `reporting.py`.

| Papildoma funkcija | Įvestis | Išvestis / poveikis |
|---|---|---|
| `preprocessing.build_preprocessing(page_values)` | Ar reikia PageValues | Neišmokytas stulpelių paruošimas |
| `training.train_and_select(...)` | Train ir validation, modelio vardas, sėkla | Pasirinkto modelio žodynas ir kandidatų rezultatų sąrašas |
| `analysis.evaluate_missing(...)` | Test, išmokyti modeliai, vardai, trūkumo dalis, sėkla | Metrikų sąrašas ir trūkstamų langelių kaukė |
| `analysis.analyze_forest(...)` | Test, išmokyti modeliai, prognozės, kartojimai, sėkla, katalogas | Formulės paklaida ir AP intervalas; įrašo klaidas bei pogrupius |
| `plots.save_plots(...)` | Testo atsakymai, tikimybės, katalogas, modelių vardai | SVG ir PNG, modelių nemoko |
| `reporting.save_splits(...)` | Imtys, konfigūracija, katalogas | Imčių dydžių ir eilučių priklausomybės CSV |
| `reporting.save_tables(...)` | Metrikų eilutės, kandidatai, test, prognozės, katalogas | CSV ir metrikų DataFrame |
| `reporting.save_manifest(...)` | Vykdymo sąlygos ir patikros skaičiai | `manifest.json` su versijomis ir kontrolinėmis sumomis |
| `reporting.save_summary(...)` | Metrikos, AP skirtumas, intervalas, paklaida, katalogas | `RESULTS.md` |

## Kaip vyksta skaičiavimas

Paleidus `python -m src.experiment`, programa perskaito konfigūraciją ir originalų CSV. Sesijos padalijamos pagal mėnesius. Kiekvienas modelio kandidatas gauna tik mokymo imtį; šiame etape išmokomi ir trūkstamų reikšmių užpildymo bei kodavimo parametrai. Validacijos AP parenka kandidatą, o validacijos F2 – sprendimo slenkstį. Užfiksuotu modeliu prognozuojamas galutinis testas. Tada atliekami papildomi bandymai ir rašomi rezultatai.

Paleidus `python -m src.predict`, mokymas nebevyksta. Įkeliamas išsaugotas modelis su savo preprocessing grandine, paruošiamas naujas CSV ir grąžinama tikimybė bei sprendimas kiekvienai eilutei.

## Failai ir funkcijų sutartys

| Funkcija | Įvestis | Grąžinama reikšmė arba poveikis |
|---|---|---|
| `data.download(path)` | Kelias originaliam CSV | Patikrintas `Path`; jei failo nėra, atsisiunčia; neatitikus SHA256, klaida |
| `data.prepare_features(frame, include_page_values=False)` | `pandas.DataFrame` su reikiamais stulpeliais | Naujas DataFrame su pasirinktais ir normalizuotais požymiais; nemoko imputavimo |
| `data.load_and_split(path, config)` | Originalus CSV ir konfigūracijos žodynas | Visa lentelė ir žodynas su `train`, `validation`, `test` lentelėmis |
| `models.build_model(name, seed, params=None, include_page_values=False)` | Modelio vardas, sėkla, parametrų žodynas | Dar neišmokyta `Pipeline`: `preprocessing` ir `classifier` |
| `models.candidates(name)` | Modelio vardas | Išbandomų parametrų žodynų sąrašas |
| `models.forest_probability_by_formula(model, features)` | Išmokytas RF ir paruošti požymiai | Teigiamos klasės tikimybių masyvas, apskaičiuotas iš medžių |
| `evaluation.select_threshold(labels, probabilities)` | Validacijos atsakymai ir tikimybės | Vienas slenkstis iš 0,01–0,99 tinklelio pagal F2 |
| `evaluation.metrics(labels, probabilities, threshold)` | Atsakymai, tikimybės, slenkstis | Žodynas su AP, trapeciniu PR-AUC, precision, recall, F2, Brier, log loss ir TN/FP/FN/TP |
| `evaluation.paired_ap_interval(...)` | Atsakymai, dviejų modelių tikimybės, kartojimai, sėkla | AP skirtumo 2,5 ir 97,5 procentiliai |
| `experiment.run(config_path, output)` | Konfigūracijos ir rezultatų keliai | Rašo CSV, grafiką, vykdymo aprašą ir modelius; reikšmės negrąžina |
| `predict.predict(input_path, model_path, output_path)` | Naujas CSV, modelio ir išvesties keliai | Prognozių DataFrame; tą pačią lentelę išsaugo CSV |

Funkcijų pavadinimai čia pateikti su modulio vardu, pavyzdžiui, `data` reiškia `src/data.py`. Pagrindinės eigos, mokymo, modelių, analizės ir išvesties moduliuose yra lietuviški komentarai; išsamesnis metodų pagrindimas bei formulės – [kolokviumo plane](KOLIOKVIUMO_PLANAS.md).

## Ką galima pakeisti be Python kodo redagavimo

| Nustatymas | Kur keisti | Poveikis ir sąlygos |
|---|---|---|
| Atsitiktinė sėkla | `config.json`: `seed` | Modelių atsitiktinumas, trūkstamų reikšmių kaukė ir bootstrap |
| Mokymo, validacijos ir testo mėnesiai | `train_months`, `validation_months`, `test_months` | Imčių sudėtis; turi apimti visus turimus mėnesius be persidengimo, kiekvienoje imtyje turi būti abi klasės |
| Prarastų reikšmių dalis | `missing_fraction` | Tik atsparumo bandymo skaitinių langelių maskavimo tikimybė; naudoti [0; 1] |
| Bootstrap kartojimų skaičius | `bootstrap_repetitions` | AP skirtumo intervalo skaičiavimo trukmė ir Monte Carlo tikslumas; teigiamas sveikasis skaičius |
| Konfigūracijos failas | `experiment --config` | Atskiros eksperimento sąlygos |
| Rezultatų katalogas | `experiment --output` | Kur įrašomos lentelės ir grafikai |
| Prognozuojamų sesijų failas | `predict --input` | Naujos sesijos su ta pačia požymių schema |
| Išmokytas modelis prognozavimui | `predict --model` | Galima pasirinkti kitą iš eksperimento sugeneruotų modelių |
| Prognozių išvestis | `predict --output` | Naujo CSV vieta |

Konfigūracija neturi pilnos tipų ir intervalų validacijos. Pavyzdžiui, `missing_fraction=2` būtų klaidinga sąlyga, bet nebūtų aiškiai atmesta kaip netinkama tikimybė. `load_and_split` tikrina imčių persidengimą, padengimą ir abi klases, tačiau pati funkcija netikrina chronologinės tvarkos. Dabartinę konfigūraciją dėl tvarkos tikrina `test_chronological_disjoint_split`; pakeitus mėnesius šį testą reikia paleisti.

### Atskiras atsparumo variantas

Nukopijuokite `config.json` į `config_missing20.json`, pakeiskite tik `missing_fraction` į `0.20` ir paleiskite:

```bash
python -m src.experiment --config config_missing20.json --output results/missing20
```

Kitiems palyginimo parametrams nesikeičiant, pagrindinis švaraus testo rezultatas turėtų išlikti toks pats, o atsparumo eilutės bus pažymėtos `missing_numeric_20pct`.

**Katalogų ribojimas:** `--output` atskiria rezultatų failus, tačiau modeliai vis tiek perrašomi bendrame `models/` kataloge. Prieš kelis variantus išsisaugokite norimus modelius arba kode pridėkite atskirą modelių katalogo argumentą. Kelių eksperimento paleidimų vienu metu dabartinė realizacija neizoliuoja.

### Kitas išmokytas modelis

Po pagrindinio eksperimento galima naudoti logistinę regresiją:

```bash
python -m src.predict --input examples/unseen_sessions.csv --model models/logistic.joblib --output results/logistic_new.csv
```

Prognozei naudojamas pasirinkto modelio išsaugotas slenkstis. `predict` neturi atskiro slenksčio argumento. `random_forest_with_page_values.joblib` papildomai reikalauja `PageValues` stulpelio, kurio šiame sintetiniame pavyzdyje nėra.

## Ką reikia keisti kode

| Pakeitimas | Konkreti vieta | Ar reikia naujo mokymo |
|---|---|---|
| RF medžių skaičius | `models.build_model`: `n_estimators=200` | Taip |
| Hiperparametrų paieškos tinklas | `models.candidates` | Taip, kandidatai parenkami iš naujo validacijoje |
| Imputavimo ar standartizavimo būdas | `preprocessing.build_preprocessing` | Taip |
| Pagrindiniai požymiai | `data.NUMERIC`, `data.CATEGORICAL`, `prepare_features` | Taip |
| Slenksčio kriterijus F2 → F1 | `evaluation.select_threshold`, `beta=2` → `beta=1` | Reikia iš naujo parinkti slenkstį validacijoje; dabartinė eksperimento komanda kartu permoko modelius |
| Nauja vertinimo metrika | `evaluation.metrics` | Jau išsaugotoms prognozėms mokymas nebūtinas; pilna komanda jį pakartoja |
| Kandidato parinkimo metrika AP → kita | `training.train_and_select`, `score = average_precision_score(...)` | Taip; taip pat keisti žymėjimus `validation_ap` ir interpretaciją |
| Naujas modelis | `models.py` ir keli sąrašai `experiment.py` | Taip |
| Kitas mokymo rinkinys | `data.py`, `experiment.py`, požymių bei skaidymo taisyklės | Taip |

Pakeitus tik slenksčio parinkimą į F1, `metrics()` ir toliau skaičiuos F2. Jei norima papildomai rodyti F1, jį reikia įtraukti į `metrics()` kaip atskirą lauką. Visas `metrics()` žodynas patenka į `metrics.csv`, bet Markdown lentelės stulpeliai `reporting.save_summary` parenkami atskirai; naują metriką ten reikia pridėti atskirai.

## Kaip pridėti penktą modelį

Pavyzdžiui, norint pridėti kitą scikit-learn suderinamą klasifikatorių:

1. `src/models.py` importuoti klasifikatorių ir pridėti `elif` šaką `build_model` funkcijoje, suteikiant unikalų vardą.
2. `candidates()` tuo pačiu vardu pridėti parametrų variantų sąrašą. Parametrai perduodami tiesiai klasifikatoriaus `set_params`, todėl čia nereikia `classifier__` prefikso.
3. `src/experiment.py` modelio vardą pridėti į `PRIMARY_MODELS` sąrašą. Tai įtrauks mokymą, parinkimą, švaraus testo metrikas ir išsaugojimą.
4. Atsparumo bandymas ir grafikai gauna tą patį `PRIMARY_MODELS` sąrašą: jo kitur kartoti nereikia.
5. Nuspręsti, ar naujas metodas keičia pagrindinę hipotezę. RF formulės patikra, klaidų pavyzdžiai, pogrupių analizė ir RF–logistinės regresijos bootstrap kode susieti su konkrečiais vardais. Jie automatiškai nepersijungs į naują modelį.
6. Papildyti metodo literatūros pagrindimą, protokolą ir dokumentaciją, tada vykdyti bandymus.

Klasifikatorius turi palaikyti `fit` ir `predict_proba`. Dabartinis kodas teigiamai klasei ima `predict_proba(... )[:, 1]`, todėl remiasi dvejetaine klasifikacija ir klasių tvarka `[0, 1]`. Vien `decision_function` nepakanka. Negalima tiesiog pridėti regresoriaus ar daugiaklasio uždavinio nepakeitus metrikų, klaidų analizės ir tikimybių interpretacijos.

## Nauji duomenys ir požymių sutartis

**Naujų sesijų prognozė palaikoma.** `src.predict` priima kitą CSV be originalaus rinkinio SHA256 patikros, nes prognozuojami nauji duomenys. Turi būti visi pasirinkto modelio reikalaujami požymiai. Stulpelių tvarka nesvarbi, nes `prepare_features` juos atrenka pagal vardus; papildomi stulpeliai ignoruojami.

Tuščias langelis ir neegzistuojantis stulpelis nėra tas pats. Tuščios reikšmės užpildomos mokymo metu išmoktomis medianomis ar modomis. Trūkstant viso privalomo stulpelio pateikiama klaida. Nežinomos kategorijos koduojamos kaip tos kategorinės savybės nulinių one-hot indikatorių grupė: programa veiks, bet nežinomos kategorijos poveikio modelis nėra išmokęs. `Weekend` rekomenduojama pateikti kaip `True` arba `False`, kaip mokymo rinkinyje; kitų tekstinių formų semantinio suvienodinimo nėra.

**Naujo mokymo rinkinio pakeitimas vien CSV failu nepalaikomas.** `download()` sąmoningai tikrina konkretaus UCI failo SHA256, o `experiment.run` naudoja fiksuotą mokymo failo kelią. Norint mokyti savo parduotuvės duomenimis, reikia sukurti atskirą jų įkėlimo ir tikrinimo kelią, suderinti požymius bei tikslą ir pakeisti skaidymą. Jei yra tikri lankytojų ID ar laiko žymos, reikia jais remtis. Vien kontrolinės sumos pakeitimas nebūtų pakankamas pritaikymas.

Išsaugotame `joblib` objekte yra `model`, `threshold`, `include_page_values`, `features`, `parameters`, `seed`. `model` apima ir transformacijas. Vis dėlto `predict` požymius paruošia pagal tuo metu esančius `data.py` sąrašus, o ne vien pagal artefakto `features`. Pakeitus požymių kodą senų modelių suderinamumas negarantuotas: reikia išsaugoti atitinkamą kodo versiją arba permokyti modelį. Atgalinio suderinamumo ir automatinio schemos versijavimo nėra.

## Dabartinės lankstumo ribos

- Eksperimentas skirtas dvejetainiam pirkimo tikslui ir konkrečiai sesijų schemai.
- AP, F2, RF pagrindinis modelis ir modelių sąrašai nėra visiškai valdomi JSON konfigūracija.
- Grafiko pavadinimas yra bendras „Final test“. Rankinė ataskaita ir jos skaičiai neatsinaujina automatiškai; konkrečius mėnesius rasite `split_summary.csv`.
- Sintetinės trūkstamos reikšmės generuojamos tik skaitiniams požymiams. Visų stulpelių praradimas, kategorijų sugadinimas ir nuo klasės priklausantis trūkumas automatiškai netiriami.
- Numatyti vietiniai CSV ir paketinis paleidimas. HTTP API, srautinis mokymas, automatinis permokymas, modelių registras ir gamybinė stebėsena neįgyvendinti.
- `run()` tiesiogiai importuojant kaip Python funkciją nenumato `threadpool_limits` konteksto; vieno srauto ribojimas taikomas standartiniame `python -m src.experiment` paleidime.

Šios ribos padeda aiškiai atskirti jau veikiančias galimybes nuo būsimos plėtros. Esama struktūra palengvina pakeitimus, bet nepanaikina poreikio juos patikrinti.

## Patikrinimas po pakeitimo

Pakeitus programos veikimą paleiskite:

```bash
python -m unittest discover -s tests -v
python -m src.experiment --output results/changed_variant
python -m src.predict --input examples/unseen_sessions.csv --output results/changed_predictions.csv
```

Pasirinkite tik aktualius bandymus: vien teksto dokumentacijos pakeitimui modelių permokyti nereikia. Keičiant schemą, sintetiniame CSV taip pat reikia atnaujinti stulpelius. Naujas modelis turi būti palygintas tomis pačiomis imtimis, o jo parametrų ir slenksčio parinkimui negalima naudoti galutinio testo.

Jau peržiūrėto testo pagrindu sugalvotas variantas laikomas papildoma tiriamąja analize. Naujam nepriklausomam teiginiui apie pagerėjimą reikia naujo neliečiamo testo. Pradinę [ataskaitą](ATASKAITA.md) ir [protokolą](PROTOKOLAS.md) išsaugokite kaip atlikto eksperimento įrodymą.

## Trumpas paaiškinimas gynimui

„Kodą suskaidžiau į duomenų paruošimo, modelių, vertinimo, eksperimento ir prognozavimo modulius. Sėklą, mėnesių imtis ir duomenų praradimo lygį galiu keisti JSON faile. Modelių hiperparametrus ar naują metodą pridedu modelių modulyje ir eksperimento sąrašuose. Naujoms tos pačios schemos sesijoms prognozuoti permokyti nereikia. Kitam mokymo rinkiniui ar kitai požymių schemai reikia keisti duomenų grandinę ir permokyti. Taigi sprendimas pritaikomas, tačiau jo lankstumas turi aiškias ribas.“
