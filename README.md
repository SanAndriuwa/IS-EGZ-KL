# Elektroninės parduotuvės pirkimo ketinimas

**Andrej Kondratjev · DISfm-26 · Intelektualiosios sistemos · 2026–2027**

Atkuriamas Python tyrimas pagal individualią užduotį. Įgyvendintos abi atskaitos (pirkimų dažnis ir logistinė regresija), atsitiktinis miškas ir gradientinis stiprinimas, laikinis skaidymas, požymio jautrumo bei atsparumo bandymai. Dokumentacija lietuvių kalba, kodo komentarai anglų kalba.

**Rezultatas:** pagrindinio RF AP=0,3411, logistinės regresijos AP=0,3336. Hipotezė apie ≥0,02 RF persvarą nepasitvirtino. Tai sesijų suvestinių tyrimas; realaus laiko tinkamumas dar nepatvirtintas.

## Paleidimas

Rekomenduojama Python 3.12. Komandas vykdykite projekto šakniniame kataloge
(jame yra `requirements.txt` ir `src`). Pasirinkite savo terminalo variantą.

### Windows CMD

```bat
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m src.experiment
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.experiment
```

Jei PowerShell neleidžia aktyvavimo scenarijaus, galima vykdyti tiesiogiai,
nekeičiant vykdymo politikos:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.experiment
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.experiment
```

Jei `.venv` jau sukurta, jos kūrimo komandą praleiskite. `source` naudojama
Linux / macOS terminale, Windows CMD jos neatpažįsta.

Po priklausomybių įdiegimo ir aplinkos aktyvavimo **viena komanda** visam
pagrindiniam eksperimentui yra `python -m src.experiment`. Pirmą kartą
reikalingas internetas UCI duomenims. Modelių mokymui GPU nereikia.

Ataskaita ir vykdymo aprašas įrašomi UTF-8 koduote, o `config.json` skaitomas
UTF-8 koduote. Tai apsaugo nuo Windows `UnicodeEncodeError`, kai sistemos
numatytoji koduotė nepalaiko lietuviškų raidžių. Naudojant senesnę projekto
kopiją laikinas sprendimas: `python -X utf8 -m src.experiment`.

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

[Kolokviumo planas PDF](docs/KOLIOKVIUMO_PLANAS.pdf) - savarankiškas įgyvendinimo planas pagal visus 10 kriterijų, be galutinių rezultatų.
[Kolokviumo plano DOCX](docs/KOLIOKVIUMO_PLANAS.docx) - redaguojama dokumento versija pagal pateikto VILNIUS TECH šablono stilius.
[Vertinimas ir atlikti papildymai](docs/KOLIOKVIUMO_VERTINIMAS.md) pateikti atskirai.
[Pateiktas VILNIUS TECH šablonas](docs/KOLIOKVIUMO_PLANAS_TEMPLATE.docx) - atskiras pradinio šablono failas.
Word ir Markdown atkuriami komanda `python scripts/build_colloquium_docx.py`.
Galutinį PDF eksportuokite iš gauto DOCX naudodami Word arba LibreOffice:
taip abu pateikiami dokumentai turi tą patį turinį ir puslapių maketą.
Scenarijui reikia `python-docx`, `lxml`, `pandoc`, `reportlab`, `PyMuPDF`,
`matplotlib` ir `pdflatex` (standalone, amsmath, amssymb).
`build_colloquium_pdf.py` saugo bendrą turinį ir atkuria alternatyvaus maketo
PDF, kurį galutiniam pateikimui pakeičia Word eksportas. DOCX išlaiko
redaguojamas OMML formules su numeriais dešinėje. Jei sistemoje nėra Times
New Roman, PDF eksportuotojas gali pakeisti šį šriftą suderinamu šriftu.
Tai papildomos dokumento generavimo priklausomybės, nereikalingos modelių mokymui.

## Egzamino pateikimas

[Egzamino ataskaita PDF](docs/EGZAMINO_ATASKAITA.pdf) pateikia eksperimento metodiką,
rezultatus, keturių metodų veikimo principus, vizualizacijas, klaidų analizę,
ribotumus ir išvadas be perteklinio kodo.
[Egzamino ataskaitos DOCX](docs/EGZAMINO_ATASKAITA.docx) yra redaguojama versija,
o [Markdown šaltinis](docs/EGZAMINO_ATASKAITA.md) leidžia greitai peržiūrėti turinį
repozitorijoje. Ataskaitoje yra atskira skiltis su nuoroda į šią GitHub repozitoriją.
Dokumentai atkuriami komanda `python scripts/build_exam_report.py`; PDF eksportuojamas
iš DOCX naudojant dokumentų renderinimo scenarijų.

## Ką skaityti

| Failas | Paskirtis |
|---|---|
| [Kodo dokumentacija ir lankstumas](docs/KODO_DOKUMENTACIJA.md) | Funkcijos, konfigūracija, plėtimo pavyzdžiai ir ribos |
| [Kolokviumo planas](docs/KOLIOKVIUMO_PLANAS.md) | Problema, metodai, literatūra, formulės, moduliai ir AI planas |
| [Eksperimento protokolas](docs/PROTOKOLAS.md) | Prieš mokymą nustatytas skaidymas, hipotezė ir bandymai |
| [Galutinė ataskaita](docs/ATASKAITA.md) | Rezultatai, klaidos, interpretacija ir apribojimai |
| [Egzamino ataskaita](docs/EGZAMINO_ATASKAITA.pdf) | Pateikimui parengta DOCX/PDF ataskaita su vizualizacijomis ir patikros išvadomis |
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
