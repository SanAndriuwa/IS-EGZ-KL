# Elektroninės parduotuvės pirkimo ketinimas

**Andrej Kondratjev · DISfm-26 · Intelektualiosios sistemos · 2026–2027**

Atkuriamas Python tyrimas pagal individualią užduotį. Įgyvendintos abi atskaitos (pirkimų dažnis ir logistinė regresija), atsitiktinis miškas ir gradientinis stiprinimas, laikinis skaidymas, požymio jautrumo bei atsparumo bandymai. Dokumentacija lietuvių kalba, kodo komentarai anglų kalba.

**Rezultatas:** pagrindinio RF AP=0,3411, logistinės regresijos AP=0,3336. Hipotezė apie ≥0,02 RF persvarą nepasitvirtino. Tai sesijų suvestinių tyrimas; realaus laiko tinkamumas dar nepatvirtintas.

## Paleidimas

Rekomenduojama Python 3.12. Iš projekto šakninio katalogo:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.experiment
```

Windows PowerShell aktyvavimas: `.venv\Scripts\Activate.ps1`. Po priklausomybių įdiegimo **viena komanda** visam pagrindiniam eksperimentui yra `python -m src.experiment`. Pirmą kartą reikalingas internetas UCI duomenims. Modelių mokymui GPU nereikia.

Duomenys automatiškai atsisiunčiami į `data/online_shoppers_intention.csv`, patikrinama SHA256. Jei atsisiuntimas neprieinamas, iš [UCI puslapio](https://archive.ics.uci.edu/dataset/468/online+shoppers+purchasing+intention+dataset) atsisiųskite ZIP ir originalų CSV įdėkite į minėtą kelią. Duomenų ir modelių kopijų Git repozitorijoje nėra; modeliai atkuriami komanda. Jei kontrolinė suma neatitinka, patikrinkite failo kilmę ir nekeiskite sumos vien tam, kad apeitumėte patikrą.

```bash
python -m unittest discover -s tests -v
python -m src.predict --input examples/unseen_sessions.csv
```

Antra komanda veikia po eksperimento ir grąžina tikimybes naujoms sesijoms. Dėstytojo failui pakeiskite `--input`. Pavyzdinės eilutės yra sintetinės, tik techninei patikrai.

## Aiškus kodas kaip laboratoriniame darbe

Pradėkite nuo [pradedančiojo vadovo](docs/PRADEDANCIOJO_VADOVAS.md): failų paskirtis,
kintamieji, mokymo pavyzdys ir konkrečios korekcijų vietos.
Grafikus atkurkite be mokymo: `python -m src.plots --results results`.

## Kolokviumo pateikimas

[Kolokviumo planas PDF](docs/KOLOKVIUMO_PLANAS.pdf) - savarankiškas įgyvendinimo planas pagal visus 10 kriterijų, be galutinių rezultatų.
[Vertinimas ir atlikti papildymai](docs/KOLOKVIUMO_VERTINIMAS.md) pateikti atskirai.
PDF ir Markdown atkuriami komanda `python scripts/build_colloquium_pdf.py`;
dokumentui generuoti reikia `reportlab` ir Linux DejaVu Sans šriftų.
Tai papildomos dokumento generavimo priklausomybės, nereikalingos modelių mokymui.

## Ką skaityti

| Failas | Paskirtis |
|---|---|
| [Kodo dokumentacija ir lankstumas](docs/KODO_DOKUMENTACIJA.md) | Funkcijos, konfigūracija, plėtimo pavyzdžiai ir ribos |
| [Kolokviumo planas](docs/KOLOKVIUMO_PLANAS.md) | Problema, metodai, literatūra, formulės, moduliai ir AI planas |
| [Eksperimento protokolas](docs/PROTOKOLAS.md) | Prieš mokymą nustatytas skaidymas, hipotezė ir bandymai |
| [Galutinė ataskaita](docs/ATASKAITA.md) | Rezultatai, klaidos, interpretacija ir apribojimai |
| [Automatinė rezultatų lentelė](results/RESULTS.md) | Visų metodų ir bandymų metrikos |
| [AI žurnalas](docs/AI_ZURNALAS.md) | Priimti sprendimai, aptiktos klaidos ir patikros |
| [Gynimo instrukcija](docs/GYNIMAS.md) | Formulės paaiškinimas, nematytas CSV ir kodo pakeitimas |
| [Reikalavimų atitiktis](docs/REIKALAVIMAI.md) | Užduoties punktai ir jų įrodymai |

## Projekto struktūra

- `src/data.py` – gavimas, schema, požymiai, skaidymas.
- `src/preprocessing.py` – skaitinių ir kategorinių požymių paruošimas.
- `src/models.py` – keturi klasifikatoriai, parametrų variantai ir RF formulė.
- `src/training.py` – kandidatų mokymas ir pasirinkimas validacijoje.
- `src/analysis.py` – atsparumas, RF klaidos, pogrupiai ir AP intervalas.
- `src/plots.py` – grafikai; galima paleisti atskirai iš rezultatų CSV.
- `src/reporting.py` – lentelių, santraukos ir vykdymo aprašo įrašymas.
- `src/evaluation.py` – AP, PR-AUC, precision, recall, kalibracijos nuostoliai, slenkstis ir bootstrap.
- `src/experiment.py` – nuosekli eiga, iškviečianti atskirų modulių funkcijas.
- `src/predict.py` – naujų sesijų prognozė.
- `config.json` – mėnesiai, sėkla, atsparumo kaukė ir bootstrap kiekis.
- `results/` – tikrai įvykdyto eksperimento lentelės, prognozės, grafikai ir vykdymo aprašas.

Testas niekur nenaudojamas hiperparametrams parinkti. Visiems pagrindiniams modeliams taikomos tos pačios imtys ir metrikos. AP ir trapecinis PR-AUC dokumentacijoje atskirti: pastoviam prognozuotojui trapecinis plotas gali klaidinti. Aukštas recall prie žemo slenksčio nėra aukštas bendras tikslumas.

## Duomenų šaltinis

C. Sakar ir Y. Kastro (2018), *Online Shoppers Purchasing Intention Dataset*, UCI, [DOI 10.24432/C5F88Q](https://doi.org/10.24432/C5F88Q), CC BY 4.0. Rezultatuose pateikiami iš šių duomenų gauti skaičiai ir nedidelė klaidų įrašų ištrauka. Modelių metodiniai šaltiniai ir patikros ribos nurodyti plane bei AI žurnale.

Darbas parengtas su AI pagalba. Gyvas gynimas ir dėstytojo nematytas bandymas dar turi būti atlikti studento.
