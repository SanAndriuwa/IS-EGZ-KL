# Eksperimento protokolas prieš rezultatų skaičiavimą

Protokolas užrašytas prieš pirmą modelių paleidimą šiame projekte. Tai vietinis darbo planas, ne išorinė preregistracija. Prieš jį peržiūrėta duomenų schema, mėnesių pasiskirstymas ir klasių dažniai, bet ne modelių rezultatai.

- Pagrindinis modelis: atsitiktinis miškas (RF). Hipotezė: be `PageValues` RF galutinio testo AP bus bent 0,02 didesnis už logistinės regresijos AP, jeigu netiesinės naršymo intensyvumo ir išėjimo rodiklių sąveikos išlieka vėlesniais mėnesiais.
- Mokymas: vasaris–rugpjūtis iš turimų mėnesių; validacija: rugsėjis–spalis; galutinis testas: lapkritis–gruodis. Sausio ir balandžio įrašų nėra. Datos tik mėnesio tikslumo, remiamasi UCI nurodytu vienų metų laikotarpiu.
- `Month` skirtas skaidymui, modelio įvestimi netampa. `Revenue` yra tik tikslas. `PageValues` iš pagrindinio eksperimento pašalintas dėl neaiškaus prieinamumo prognozės momentu.
- Modeliai: pastovus mokymo pirkimų dažnis, logistinė regresija C ∈ {0,1; 1}, RF su 200 medžių ir minimaliu lapo dydžiu {5; 20}, histograminis gradientinis stiprinimas su 150 iteracijų, mokymosi žingsniu 0,05 ir lapų skaičiumi {7; 15}.
- Parinkimas: didžiausias validacijos AP; lygiųjų atveju pirmas kandidatas. Po parinkimo modelis nepermokomas su validacijos eilutėmis. Slenkstis: didžiausias validacijos F2 fiksuotame 0,01–0,99 tinkle; lygiųjų atveju mažesnis slenkstis.
- Transformacijos mokomos tik mokymo imtyje: skaitinių reikšmių mediana ir standartizavimas; kategorijų moda ir one-hot kodavimas, nežinomos kategorijos ignoruojamos.
- Metrikos: AP, trapecinis PR-AUC, precision, recall, F2, Brier, log loss, painiavos matricos skaičiai, PR ir kalibracijos kreivės. Nenaudojamas SMOTE ar klasių svoriai. Retai klasei skiriamas dėmesys metrikomis ir slenksčiu.
- Abliacija: tas pats RF eksperimentas papildomai su `PageValues`, tuo pačiu skaidymu ir kandidatų tinklu. Papildomas modelis nekeičia iš anksto pasirinkto pagrindinio modelio.
- Atsparumas: 10 % testo skaitinių langelių atsitiktinai užmaskuoti; keturiems modeliams ta pati kaukė; be permokymo ir slenksčio pakeitimo.
- RF klaidos: penki aukščiausios tikimybės FP ir penki žemiausios tikimybės FN. Suvestinės pagal mėnesį ir lankytojo tipą.
- Neapibrėžtumas: 500 porinio stratifikuoto bootstrap kartojimų RF–logistinės regresijos AP skirtumui. Tai nėra ateities mėnesių ar kitų parduotuvių generalizacijos intervalas.
- Biudžetas: CPU, vienas skaičiavimo srautas, devyni kandidatų mokymai įskaitant abliaciją; orientacinė riba 10 min. ir 4 GB RAM. Laikas bus išmatuotas; RAM nebus matuojama ar priverstinai ribojama.
- Sėkla: 42. Teigiamas hipotezės rezultatas nėra būtinas; testo pamatymas negali pakeisti parametrų tinklelio.
