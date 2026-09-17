# Pasiruošimas gynimui

## Paaiškinimas savo žodžiais

Programa vienai sesijai priskiria pirkimo tikimybę. Ji mokosi iš ankstesnių mėnesių, parametrus ir sprendimo slenkstį parenka kitais mėnesiais, o vertinama dar vėlesniais. Taip būsimo testo atsakymai nepadeda mokyti modelio. RF susideda iš 200 medžių. Kiekvienas medis pateikia pasiekto lapo pirkimų dalį; galutinė tikimybė yra šių dalių vidurkis. Parodykite `src/models.py::forest_probability_by_formula` ir atitinkamą formulę plane.

Pirkimų dažnio baseline visoms sesijoms grąžina 0,1106. Jis nesugeba jų suranguoti. Logistinė regresija susumuoja transformuotus požymius su svoriais ir pritaiko sigmoidę. Miškas gali mokytis sudėtingesnių sąlygų, tačiau šiame teste jo papildoma nauda nedidelė.

## Nematytos sesijos

Po pagrindinio eksperimento dėstytojo pateiktą CSV su reikiamais požymiais paleiskite taip:

```bash
python -m src.predict --input destytojo_sesijos.csv --output results/destytojo_prognozes.csv
```

`Revenue`, `Month` ir `PageValues` pagrindiniam modeliui nebūtini ir ignoruojami, jei yra. `examples/unseen_sessions.csv` yra rankiniu būdu sukurtas techninis pavyzdys, ne tikras dėstytojo testas ir ne vertinimo duomenys. Jame yra nežinoma lankytojo kategorija bei tuščia skaitinė reikšmė.

```bash
python -m src.predict --input examples/unseen_sessions.csv
```

Modelį reikia pirmiausia sugeneruoti `python -m src.experiment`. `joblib` failus įkelkite tik iš patikimo šaltinio – jie yra Python objektų serializacija. Jei CSV trūksta stulpelio, parodykite aiškią klaidą ir duomenų sutartį, o ne tyliai kurkite neegzistuojantį požymį.

## Nedidelis pakeitimas

Dėstytojui paprašius pakeisti recall ir precision kompromisą, `src/evaluation.py::select_threshold` funkcijoje `beta=2` pakeiskite į `beta=1` ir pakartokite eksperimentą su atskiru rezultatų katalogu:

```bash
python -m src.experiment --output results/f1_variant
```

Slenkstis ir toliau parenkamas tik validacijoje; testas nenaudojamas pasirinkti, kuris variantas patogesnis. Šis paleidimas perrašo vietinius modelių failus. Originalius rezultatus palikite palyginimui, tačiau papildomas bandymas jau yra tiriamoji analizė po testo peržiūros. Jos nepateikite kaip naujo nepriklausomo hipotezės patvirtinimo.

Kitas paprastas pakeitimas – `config.json` pakeisti `missing_fraction` iš 0.10 į 0.20 ir patikrinti atsparumą. Grafikai pagrindiniam švariam testui nuo šio pakeitimo nesikeičia; atsparumo eilutės pasikeičia.

## Klausimai, kuriuos reikia gebėti atsakyti

1. Kodėl vien accuracy nepakanka? Retą pirkimą visada atmetantis modelis gali atrodyti tikslus, bet neaptiks nė vieno pirkimo.
2. Kodėl nėra atsitiktinio skaidymo? Turime mėnesį ir norime įvertinti vėlesnį laikotarpį.
3. Kodėl be PageValues? Jo prieinamumas iki prognozės nėra patvirtintas; jautrumas jam didelis.
4. Ar RF laimėjo? Skaitinė persvara maža, išankstinė hipotezė nepasitvirtino, intervalas apima nulį.
5. Kodėl recall aukštas, bet precision žemas? Validacijos F2 taisyklė pasirinko žemą slenkstį, todėl daug sesijų pažymimos teigiamai.
6. Ar tikimybės kalibruotos? Kalibracija įvertinta, RF dažnai nuvertina pirkimų dažnį. Papildomas kalibratorius nemokytas.
7. Ko trūksta realiam laikui? Įvykių sekų, prieinamumo prognozės momentu audito ir būsimo laikotarpio bandymo.
