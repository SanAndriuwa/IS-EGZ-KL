# Pasiruošimas gynimui

Kodo funkcijų ir lankstumo paaiškinimas: [Kodo dokumentacija ir lankstumas](KODO_DOKUMENTACIJA.md).

## Paaiškinimas savo žodžiais

Programa vienai sesijai priskiria pirkimo tikimybę. Ji mokosi iš ankstesnių mėnesių, parametrus ir sprendimo slenkstį parenka kitais mėnesiais, o vertinama dar vėlesniais. Taip būsimo testo atsakymai nepadeda mokyti modelio. RF susideda iš 200 medžių. Kiekvienas medis pateikia pasiekto lapo pirkimų dalį; galutinė tikimybė yra šių dalių vidurkis. Parodykite `src/models.py::forest_probability_by_formula` ir atitinkamą formulę plane.

Pirkimų dažnio baseline visoms sesijoms grąžina 0,1106. Jis nesugeba jų suranguoti. Logistinė regresija susumuoja transformuotus požymius su svoriais ir pritaiko sigmoidę. Miškas gali mokytis sudėtingesnių sąlygų, tačiau šiame teste jo papildoma nauda nedidelė.

## Galutinio testo statusas

Lapkričio–gruodžio imtis buvo validus nepriklausomas galutinis testas pirmojo vertinimo metu: modeliai, hiperparametrai ir slenksčiai buvo nustatyti prieš jį atveriant. Vėliau ši imtis naudota klaidų, pogrupių, kalibracijos ir slenksčio elgsenos analizei, todėl dabar tyrėjui ji jau žinoma. Dėl to jokio vėlesnio modelio pakeitimo negalima pateikti kaip naujai ir nepriklausomai patvirtinto tame pačiame teste; reikia naujo būsimo laikotarpio arba kitos iki tol neliestos *holdout* imties. Fiksuota `PageValues` abliacija taip pat yra tiriamoji analizė po testo peržiūros, ne naujas pagrindinės hipotezės patvirtinimas.

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

Trumpi atsakymai yra atmintinė kalbėjimui, ne visas metodikos aprašas.

### Duomenys ir modeliai

1. **Kas yra X ir y?** X – sesijos įvesties požymiai; y – `Revenue`, ar sesija baigėsi pirkimu (1), ar ne (0). `Revenue` nėra X dalis.
2. **Kiek pradinių požymių?** Pagrindiniame variante 15: 9 skaitiniai ir 6 kategoriniai. *One-hot* kiekvieną kategoriją paverčia atskirais stulpeliais, todėl paruoštame X jų daugiau.
3. **Ar logistinė regresija turi paslėptų sluoksnių?** Ne. Ji skaičiuoja svertinę požymių sumą, tada sigmoidę ir tikimybę.
4. **Kas yra sigmoidė?** Funkcija, paverčianti bet kokį realų skaičių reikšme tarp 0 ir 1.
5. **Ką reiškia `C=1`?** Tai atvirkštinis regularizacijos stiprumas. Mažesnis C stipriau ribotų koeficientus; `C=1` pasirinkta pagal validacijos AP, ne kaip universalus optimumas.
6. **Kaip vienas RF medis gauna tikimybę?** Sesija patenka į lapą, o medis grąžina tame lape buvusių mokymo pirkimų dalį. Miškas vidurkina medžių tikimybes.
7. **Kodėl 200 RF medžių?** Skaičius iš anksto fiksuotas pagal ribotą skaičiavimo biudžetą; neteigiama, kad 200 optimalu.
8. **Ką reiškia `min_samples_leaf=20`?** Kiekviename galutiniame medžio lape turi būti bent 20 mokymo pavyzdžių; tai riboja labai smulkius skaidymus.
9. **Kodėl boosting turi 150 iteracijų, o RF 200 medžių?** RF medžiai mokomi atskirai, boosting medžiai nuosekliai taiso ankstesnį modelį. Skaičiai iš anksto fiksuoti ir tiesiogiai nelyginami.
10. **Ką reiškia `learning_rate=0.05`?** Kiekvieno naujo boosting medžio indėlis pridedamas su 0,05 žingsniu.
11. **Ką reiškia `max_leaf_nodes=7`?** Vienam boosting medžiui leidžiama daugiausia 7 galutiniai lapai, todėl vienas medis lieka paprastas.
12. **Kam iš pradžių tikimybė, o tada klasė?** Tikimybė leidžia rikiuoti sesijas ir pasirinkti veiksmui tinkamą slenkstį; 0/1 klasė gaunama tik palyginus ją su slenksčiu.

### Rodikliai ir rezultatai

13. **Kodėl pagrindinis rodiklis AP?** Pirkimų klasė retesnė, o AP vertina teigiamų sesijų rangavimą per slenksčius. Vien accuracy gali atrodyti gera net neaptikus pirkimų.
14. **Ar AP = 0,3411 yra 34,11 % accuracy?** Ne. AP apibendrina *precision–recall* rangavimą, o accuracy yra teisingų 0/1 sprendimų dalis prie vieno slenksčio.
15. **Kodėl baseline tikimybė 0,1106, o testo AP 0,2066?** 0,1106 yra mokymo pirkimų dalis, grąžinama visoms sesijoms. Visi balai vienodi, todėl testo AP lygi testo pirkimų daliai – 0,2066.
16. **Kodėl modelis parenkamas pagal AP, o slenkstis pagal F2?** AP parenka geriau ranguojantį kandidatą validacijoje; F2 tada parenka 0/1 sprendimo ribą tam kandidatui. Testas nė vieno pasirinkimo nenulemia.
17. **Kodėl F2, o ne F1?** Šiame mokomajame scenarijuje svarbiau nepraleisti pirkėjo; F2 labiau akcentuoja *recall*. Be realių klaidų kainų tai nėra verslo optimumas.
18. **Kas pasikeistų naudojant F1?** Tos pačios prognozės ir klaidų skaičiai savaime nesikeistų; pasikeistų balas. Iš naujo parenkant slenkstį validacijoje galėtų keistis ir 0/1 sprendimai.
19. **Iš kur 0,03 slenkstis?** Validacijoje patikrintas 0,01–0,99 tinklelis kas 0,01; pasirinkto RF didžiausią F2 davė 0,03, prieš atveriant testą.
20. **Kodėl *recall* ≈ 0,98, bet *precision* ≈ 0,24?** Žemas slenkstis aptiko 956 iš 976 pirkimų, bet kartu pažymėjo 3 004 nepirkusias sesijas.
21. **Kas yra Brier score?** Prognozuotos tikimybės ir tikro 0/1 atsakymo kvadratinės klaidos vidurkis; mažesnis geresnis.
22. **Kas yra kalibracija?** Palyginimas, ar tarp sesijų, kurioms duota, pavyzdžiui, apie 0,3 tikimybė, maždaug 30 % iš tiesų pirko. Ji skiriasi nuo gero rangavimo.
23. **Kodėl trapecinis PR-AUC baseline gali klaidinti?** Pastovus balas sesijų neranguoja, bet trapecinis kreivės plotas dėl galinio taško čia yra 0,6033; jo AP yra tik 0,2066.
24. **Ką reiškia bootstrap intervalas [−0,0113; 0,0284]?** Poromis perrinkus tas pačias testo eilutes abiem modeliams, toks gautas centrinis 95 % RF minus LR AP skirtumo intervalas šiai imčiai.
25. **Kodėl svarbu, kad intervalas apima 0?** Turimi duomenys neleidžia tvirtai teigti, kad RF AP pranašumas prieš LR yra teigiamas.
26. **Kodėl 500 pakartojimų?** Tai iš anksto pasirinktas skaičiavimo biudžetas, ne privalomas standartas; daugiau pakartojimų galėtų stabilizuoti intervalo galus.
27. **Kodėl ΔAP riba 0,02?** Iš anksto pasirinkta mokomojo darbo praktiškai pastebimos persvaros riba, ne statistinio reikšmingumo ar pinigais pagrįsta norma.
28. **Ką praktiškai daro `min_samples_leaf` ir `max_leaf_nodes`?** Pirmasis nustato mažiausią lapo imtį, antrasis – didžiausią lapų skaičių. Abu riboja medžio sudėtingumą.

### Sąžiningas vertinimas ir ribos

29. **Kodėl paruošimas mokomas tik iš train?** Kad validacijos ir testo mediana, kategorijos ar kitos reikšmės nepatektų į mokymą iš ateities.
30. **Kas yra data leakage?** Kai modelis mokydamasis gauna informaciją, kurios tikros prognozės momentu dar neturėtų.
31. **Kodėl `PageValues` įtartinas, bet neįrodytas leakage?** Jo skaičiavimo ir prieinamumo laikas CSV neaiškus. Didelis AP šuolis kelia klausimą, bet pats savaime neįrodo nutekėjimo.
32. **Kam RF pipeline `StandardScaler`?** Medžiams mastelio keitimas nebūtinas. Bendras paruošimo žingsnis paliktas vienodai grandinei; scaler pritaikomas tik train ir RF skaidymų esmės nekeičia.
33. **Kodėl train pirkimų dalis 11,06 %, o test 20,66 %?** Tai skirtingų mėnesių stebėti dažniai. Vėlesnė imtis turi kitą klasės dalį, todėl tikimybių kalibracija ir baseline AP gali skirtis.
34. **Kas yra distribution shift?** Kai vėlesnių duomenų požymių ar atsakymų pasiskirstymas skiriasi nuo mokymo duomenų.
35. **Kas yra *unseen test*?** Iki modelio ir slenksčio pasirinkimų neliesta imtis, skirta vienkartiniam galutiniam įvertinimui.
36. **Kodėl tas pats testas po analizės nebėra naujas nepriklausomas įrodymas?** Tyrėjas jau matė jo klaidas, pogrupius ir rezultatus; vėlesni pakeitimai gali būti sąmoningai ar netyčia prie jo priderinti. Reikia naujos neliestos imties.
37. **Kodėl modelis nepermokomas su train+validation?** Šiame eksperimente vertinama tiksliai ta grandinė, kurios parametrai išmokti train ir pasirinkimai padaryti validation; jungimas pakeistų modelį prieš testą.
38. **Ką parodė 10 % trūkstamų reikšmių bandymas?** Atsitiktinai paslėpus 9,87 % skaitinių testo langelių, AP sumažėjo nedaug. Tai neįrodo atsparumo sisteminiam ar viso stulpelio trūkumui.
39. **Kodėl seed = 42?** Atkuriamumui. Skaičius nepasirinktas modeliui pagerinti.
40. **Ką iš tikrųjų parodėme?** Modeliai išmoko signalą: jų AP aukštesnė už pastovią atskaitą. RF turėjo didžiausią stebėtą AP, bet nepasiekė iš anksto reikalauto ≥0,02 pranašumo prieš LR, o bootstrap intervalas apima 0. Aukštas *recall* gautas mažo *precision* kaina. `PageValues` turi stiprų prognozavimo signalą, bet saugus prieinamumas neįrodytas. Tai *offline/post-session* tyrimas, ne patvirtintas realaus laiko sprendimas.

### Išplėstinio tyrimo klausimai po jo paleidimo

41. **Kodėl naujas tyrimas atskiras nuo H1?** Jis sumanytas jau pamačius pradinio Nov–Dec testo rezultatus; negalima jo pavadinti iš anksto registruota RF–LR hipoteze.
42. **Kodėl keturi didėjantys laiko foldai?** Kiekviename modelis mokomas tik ankstesniais mėnesiais ir tikrinamas vėlesniu; atsitiktinis maišymas šį laiko santykį sugriautų.
43. **Kaip parenkami parametrai ir šeima?** Konfigūracijos lyginamos pagal vidutinę keturių foldų AP; artimi top variantai tikrinami dėl stabilumo. Po to vienas kiekvienos šeimos kandidatas įvertinamas Sep–Oct, ir didžiausia šios validacijos AP parenka bendrą laimėtoją.
44. **Ar Nov–Dec parenka laimėtoją?** Ne. Kode laimėtojas ir F2 slenkstis užfiksuojami prieš Nov–Dec prognozes; pakeitus dirbtinius test balus pasirinkimas nesikeičia.
45. **Kodėl ir tada rezultatas tik tiriamasis?** Tyrėjas jau analizavo tą patį testą ankstesniuose etapuose. Naujam nepriklausomam patvirtinimui reikia iki tol neliesto būsimo laikotarpio.

Konkretaus naujo laimėtojo ir jo skaičių šioje atmintinėje dar nėra: vartotojas pats paleis tyrimą. Atsakymus papildyti tik pagal `results/tuning/SUMMARY.md`, ne spėjimu.
