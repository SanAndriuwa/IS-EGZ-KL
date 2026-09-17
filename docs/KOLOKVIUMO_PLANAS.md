# Elektroninės parduotuvės pirkimo ketinimo tyrimo planas

Andrej Kondratjev, DISfm-26. Intelektualiosios sistemos, 2026–2027 m.

## Problema ir praktinė vertė

Tikslas – pagal vienos naršymo sesijos požymius įvertinti tikimybę, kad sesija baigsis pirkimu. Techninis uždavinys yra dvejetainė klasifikacija su tikimybine išvestimi. Parduotuvė galėtų pagal įvertį rūšiuoti sesijas konsultanto dėmesiui ar analizuoti pirkimo elgseną. Prognozė savaime nerodo, kuriam lankytojui nuolaida padidins pirkimo tikimybę; tam reikėtų atskiro intervencijos eksperimento.

Klaidingai teigiama prognozė (FP) gali reikšti bereikalingą kontaktą ar paskatą nepirksiančiam lankytojui. Klaidingai neigiama (FN) – praleistą pirkėją. Piniginės kainos nepateiktos, todėl jų neišgalvojame. Mokomajame bandyme validacijoje maksimizuojamas F2, teikiantis daugiau svarbos recall. Tai nėra ekonomiškai optimalaus slenksčio įrodymas.

Svarbi riba: viešame CSV pateikta sesijos suvestinė. Net jei dalis požymių gali būti atnaujinama naršant, turimi duomenys neleidžia patikrinti prognozės konkrečią sekundę iki pirkimo. Rezultatas bus atkuriamas neprisijungęs tyrimas, ne patvirtinta realaus laiko sistema.

## Duomenys ir įvesties sutartis

Naudojamas [UCI rinkinys](https://doi.org/10.24432/C5F88Q). CSV turi 17 pradinių požymių ir tikslą `Revenue`. Pagrindinis modelis naudoja devynis skaitinius ir šešis kategorinius požymius, išvardytus `src/data.py`. `Month` naudojamas tik skaidymui; `PageValues` tik abliacijai. Įvestis – CSV su viena sesija eilutėje. Išvestis – `purchase_probability` intervale [0; 1] ir dvejetainė prognozė pagal validacijoje nustatytą slenkstį.

Skaitiniai požymiai: puslapių kiekių ir trukmių poros `Administrative`, `Informational`, `ProductRelated`, jų `_Duration`, taip pat `BounceRates`, `ExitRates`, `SpecialDay`. Kategoriniai: `OperatingSystems`, `Browser`, `Region`, `TrafficType`, `VisitorType`, `Weekend`. Tušti langeliai užpildomi tik iš mokymo imties nustatytomis reikšmėmis. Nežinomos kategorijos priimamos, trūkstamas stulpelis laikomas klaida. Neigiami ar begaliniai skaitiniai dydžiai atmetami.

## Metodai ir literatūros pagrindimas

| Metodas | Kodėl pasirinktas | Ribos ir pirminis šaltinis |
|---|---|---|
| Mokymo pirkimų dažnis | Paprasčiausia tikimybės atskaita, nereikalaujanti požymių | Neatskiria sesijų; formulė žemiau |
| Logistinė regresija | Aiški tiesinė logaritminio šansų santykio atskaita ir tiesioginė tikimybinė išvestis | Neaprašo netiesinių sąveikų be papildomų požymių; [bibliotekos autorių dokumentacija](https://scikit-learn.org/1.8/modules/linear_model.html#logistic-regression) |
| Atsitiktinis miškas | Aprašo netiesines sąveikas; medžių vidurkinimas mažina atskirų medžių kintamumą | Gali blogai ekstrapoliuoti pasikeitus laikotarpiui; [Breiman, 2001](https://doi.org/10.1023/A:1010933404324) ir [autoriaus tekstas](https://www.stat.berkeley.edu/~breiman/randomforest2001.pdf) |
| Gradientinis stiprinimas | Nuosekliai pridedami medžiai gali atkurti ankstesnio modelio neaprašytus ryšius | Jautrus sudėtingumui ir poslinkiui; [Friedman, 2001](https://doi.org/10.1214/aos/1013203451), konkrečiai realizacijai – [HistGradientBoostingClassifier](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html) |

Taigi nagrinėjami du intelektualieji metodai ir abi privalomos atskaitos. Šaltiniai pagrindžia metodų mechanizmą; jų pranašumas šiame rinkinyje bus tikrinamas eksperimentu. Pagrindinis metodas – atsitiktinis miškas. Patikrinama hipotezė ir visos bandymų taisyklės yra [išankstiniame protokole](PROTOKOLAS.md).

## Formulės ir jų realizavimas

Kai $y_i=1$ reiškia pirkimą, mokymo imtyje iš $N$ sesijų pastovus įvertis yra

$$\hat p_0=\frac{1}{N}\sum_{i=1}^{N} y_i.$$

`src/models.py::build_model` jį realizuoja `DummyClassifier(strategy='prior')`.

Logistinė regresija naudoja transformuotą požymių vektorių $z$, išmoktus svorius $w$ ir poslinkį $b$:

$$\hat p(y=1\mid z)=\frac{1}{1+e^{-(w^Tz+b)}}.$$

`LogisticRegression` minimizuoja reguliuotą logaritminį nuostolį. Parametras `C` yra atvirkštinis reguliavimo stiprumas.

Miško medis padalija požymių erdvę sąlygomis, pavyzdžiui, $z_j\le t$. Mazgo Gini priemaiša yra

$$G=1-\sum_{k\in\{0,1\}}p_k^2,$$

kur $p_k$ – svertinė klasės dalis mazge. Pasirenkamas skaidymas, mažinantis vaikų priemaišų svertinį vidurkį. Kiekvienas iš $B$ medžių mokomas bootstrap imtyje ir skaidymui svarsto atsitiktinį požymių poaibį.

Šioje scikit-learn realizacijoje tikimybė yra medžių lapų tikimybių vidurkis:

$$\hat p_{RF}(x)=\frac{1}{B}\sum_{b=1}^{B}\frac{n_{b,1}(L_b(x))}{n_b(L_b(x))}.$$

$L_b(x)$ – lapas, į kurį patenka transformuota sesija; $n_{b,1}$ – teigiamų mokymo pavyzdžių svoris lape; $n_b$ – visas lapo svoris, įskaitant bootstrap pasikartojimus; $B=200$. Tai ne vien dvejetainių medžių balsų vidurkis. Funkcija `src/models.py::forest_probability_by_formula` tiesiogiai apskaičiuoja šią išraišką, o `src/experiment.py` palygina ją su `predict_proba`.

Sprendimo taisyklė: $\hat y=\mathbf{1}[\hat p\ge\tau]$. Slenkstis $\tau$ nustatomas `src/evaluation.py::select_threshold` tik validacijos imtyje. $F_2=5PR/(4P+R)$, kur $P$ yra precision, $R$ – recall.

## Etapai ir moduliai

| Etapas | Įvestis | Veiksmas ir failas | Išvestis |
|---|---|---|---|
| Gavimas | UCI ZIP | `data.py::download`, SHA256 patikra | Originalus CSV |
| Skaidymas | CSV ir konfigūracija | `data.py::load_and_split` | Trys nesikertančios imtys |
| Paruošimas | Viena imtis | `prepare_features`, `build_model` | Skaitinė matrica |
| Mokymas | Tik mokymo imtis | `experiment.py`, `models.py` | Kandidatų modeliai |
| Parinkimas | Validacija | AP palyginimas ir F2 slenkstis | Užfiksuotas modelis |
| Vertinimas | Neliečiamas testas | `evaluation.py`, `experiment.py` | Lentelės, kreivės, klaidos |
| Naudojimas | Naujas CSV | `predict.py` | Tikimybė kiekvienai eilutei |

## Eksperimentas ir rizikos

Tikslus skaidymas, kandidatų tinklai, biudžetas, abliacija ir atsparumo bandymas aprašyti [protokole](PROTOKOLAS.md). Pagrindinė rangavimo metrika – average precision (AP); atskirai pateikiamas trapecinis PR-AUC. Tikimybių kokybė vertinama Brier ir log loss bei kalibracijos kreive. Testas nenaudojamas nei modelio parametrams, nei slenksčiui, nei kalibravimui mokyti. Papildomas kalibratorius šiame minimaliame tyrime nemokomas.

UCI nurodo skirtingus naudotojus sesijoms, tačiau CSV nėra jų identifikatorių, todėl nepriklausomai patikrinti šio teiginio negalima. `Returning_Visitor` yra lankytojo tipas, o ne ID. Vienodi požymiai savaime nereiškia to paties asmens. Galimas sezoninis poslinkis, vienos parduotuvės specifika, neaiškus analitinių rodiklių apskaičiavimo laikas ir validacijos perkrovimas bendru hiperparametrų bei slenksčio parinkimu. Rezultatai nebus apibendrinami visoms parduotuvėms.

## AI naudojimo planas

AI naudojamas pradiniam kodui, teksto struktūrai ir bandymų idėjoms. Citatos tikrinamos šaltinio puslapyje, formulė lyginama su bibliotekos aprašu ir skaitine realizacija, kodas vykdomas, o skaičiai imami tik iš sugeneruotų failų. Nepatikrinta prielaida aiškiai atskiriama nuo fakto. Faktiniai patikrinimai ir aptiktos klaidos pateikiami [AI žurnale](AI_ZURNALAS.md). Studentas turi savarankiškai suprasti ir apginti pateiktą darbą.
