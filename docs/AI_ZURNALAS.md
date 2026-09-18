# AI naudojimo ir patikros žurnalas

Darbas parengtas su ChatGPT Codex pagal vartotojo užklausą: „Prašau atlikti nurodytą darbą, sukurti naują github repo ir sukelti tiek sprendima, tiek dokumentaciją“, pridėjus `DISfm-26_Andrej_Kondratjev.docx`. Tai faktinio šios sesijos darbo žurnalas, ne tariamų studento savarankiškų eksperimentų aprašymas.

## Pagrindinės užklausos ir veiksmai

Pradinė vartotojo užklausa buvo viena; vėlesni papildymai užrašyti žemiau. Iš pradžių AI ją išskaidė į dokumento perskaitymą, UCI duomenų gavimą, literatūros tikrinimą, eksperimento protokolą, programą, bandymus ir dokumentaciją. Paieškose naudotos užklausos „Breiman 2001 Random Forests doi“ ir „Friedman 2001 greedy function approximation gradient boosting machine doi“. Metodų ir metrikų realizacija tikrinta bibliotekos autorių dokumentacijoje; rezultatai gauti vykdant kodą, ne generuojant skaičius tekste.

## Priimti ir atmesti sprendimai

| Sprendimas | Statusas ir priežastis | Patikra |
|---|---|---|
| Laikinis skaidymas pagal mėnesius | Priimtas, nes tikslūs laikai ir ID nepateikti | CSV stulpeliai, mėnesių suvestinė, testas |
| Pagrindinis bandymas be PageValues | Priimtas, nes prieinamumas prognozės momentu nepatvirtintas | UCI požymio aprašymas, jautrumo bandymas |
| RF ir gradientinis stiprinimas | Priimti kaip du intelektualieji metodai | Pirminiai metodų ir realizacijų šaltiniai, realus palyginimas |
| Teigti, kad sudėtingesnis modelis būtinai laimi | Atmesta kaip nepatikrinta prielaida | RF persvara 0,0076, intervalas apima nulį |
| Teste pasirinkti patogesnį slenkstį | Atmesta dėl informacijos nutekėjimo | Kodas slenkstį gauna iš validacijos |
| Pavadinti rezultatą įrodyta realaus laiko sistema | Atmesta dėl suvestinių duomenų ribų | Nėra įvykių sekų ar prognozės laiko žymos |

## Aptiktos AI klaidos ir nepatikrintos prielaidos

1. **Neteisingai numanyta SciPy versija.** AI pradžioje įrašė `scipy==1.16.3`, nepatikrinęs faktinės aplinkos. Vėliau `scipy.__version__` parodė 1.17.0. Priklausomybės pataisytos į tikrai naudotą versiją. Tai atkuriamumo klaida, ne modelio rezultatų pasikeitimas.
2. **AP ir trapecinio PR-AUC tapatumo rizika.** Pirmas rezultatų skaitymas parodė pastovaus modelio trapecinį plotą 0,6033, nors jis neranguoja sesijų. Skaičiavimo patikra atskleidė galinio PR taško poveikį; AP yra 0,2066. Abi metrikos aiškiai atskirtos ir įtrauktas konstantinių prognozių AP testas. Aukštas trapecinis skaičius nepateikiamas kaip geras modelio rezultatas.
3. **Nepatikrinta prielaida apie PageValues.** Negalima vien iš pavadinimo patvirtinti nei saugaus prieinamumo, nei faktinio nutekėjimo. Patikrintas UCI aprašymas ir palyginti modeliai su požymiu bei be jo. Faktinis agregato laiko auditas neįmanomas iš šio CSV; prielaida lieka nepatvirtinta ir aiškiai pažymėta.
4. **Neteisingas santykinis kelias rašymo komandoje.** Vienas AI bandymas naudojo projekto katalogo vardą jau būdamas to katalogo viduje. Komanda grąžino „No such file or directory“, failai nebuvo sukurti. Kelias pataisytas prieš sėkmingą pirmą eksperimento paleidimą. Ši nesėkmė nesukūrė jokių modelio rezultatų.

## Rezultatų ir citatų tikrinimas

- Failo turinys ištrauktas iš DOCX; įgyvendinti tiek kolokviumo, tiek galutinio darbo punktai, išskyrus dar neįvykusį gyvą gynimą.
- UCI puslapis ir CSV patikrinti, atsisiųsto failo SHA256 išsaugota kode ir vykdymo apraše.
- Breiman straipsnio autoriaus PDF peržiūrėtas. Friedman DOI nuveda į leidėjo straipsnio puslapį, bet pilnas leidėjo tekstas šioje prieigoje nebuvo perskaitomas; konkrečios realizacijos veikimas papildomai tikrintas oficialioje scikit-learn dokumentacijoje. Necituojamas nepatikrintas pažodinis tekstas.
- RF tikimybės formulė palyginta su bibliotekos rezultatu, didžiausias skirtumas 0.
- Septyni testai paleisti ir praėjo. PR bei kalibracijos grafikas vizualiai peržiūrėtas.
- Dokumentacijos skaičiai sutikrinti su `results/metrics.csv` ir klaidų pavyzdžiais. Neigiamas hipotezės rezultatas paliktas.

AI parengtas kodas ir tekstas nėra savaiminis teisingumo įrodymas. Studentas turi peržiūrėti medžiagą, pakartoti eksperimentą savo aplinkoje ir gebėti paaiškinti formulę bei atlikti pakeitimą gynimo metu. Šis žurnalas nepriskiria studentui veiksmų, kurių jis dar neatliko.


## 2026-09-18 — aiškesnis kodas ir atskiri moduliai

### Vartotojo užklausos

- Supaprastinti kodą panašiai kaip laboratoriniuose IS-Lab darbuose: aiškumas ir galimybė koreguoti svarbesni už optimizavimą.
- Skirtingos paskirties funkcijas rašyti atskiruose failuose ir išsamiai paaiškinti jų veikimą.
- Nepamiršti pildyti AI naudojimo žurnalo.

### AI atlikti veiksmai ir sprendimų priežastys

Peržiūrėtas dabartinis projektas ir `SanAndriuwa/IS-Lab2/testing4H.m`.
Laboratoriniame pavyzdyje matomi atskiri parametrų, mokymo ir testavimo etapai;
šį nuoseklumo principą pritaikėme Python projektui. Kiti laboratoriniai darbai
šiame etape nebuvo išsamiai peržiūrėti.

| Pakeitimas | Kodėl |
|---|---|
| `training.py` gauna `train_and_select` | Kandidatų mokymas ir pasirinkimas matomi vienoje vietoje, be grafikų kodo |
| `preprocessing.py` atskirtas nuo `models.py` | Duomenų paruošimas nesusimaišo su klasifikatorių parametrais |
| `analysis.py` | Atsparumas, RF formulė, klaidos ir pogrupiai atskirti nuo pagrindinės eigos |
| `plots.py` su atskira komanda | Grafikų korekcijoms nereikia kartoti mokymo |
| `reporting.py` | CSV, Markdown ir vykdymo aprašas atskirti nuo skaičiavimo |
| `experiment.py` palikta nuosekli eiga | Galima skaityti etapus nuo viršaus žemyn |
| Lietuviški komentarai ir pradedančiojo vadovas | Paaiškintos įvestys, išvestys, kintamieji ir korekcijų vietos |

Išlaikyti sklearn klasifikatoriai, parametrų variantai, sėkla, imtys ir
validacijos taisyklės. Neįgyvendintas naujas mokymo algoritmas. Pagalbiniai
moduliai importuojami; atskiras komandinis paleidimas numatytas eksperimentui,
prognozei ir grafikams. Sąmoningai nekurta universali įskiepių ar klasių sistema.

### Aptiktos klaidos ir dokumentacijos neatitikimai

- Pirmas pilno eksperimento paleidimas po išskaidymo aptiko trūkstamą
  `metrics` importą `experiment.py` (`NameError`). Importas pridėtas. Septyni
  esami vienetiniai testai šios visos programos sujungimo klaidos neaptiko,
  todėl patikrintas ir pilnas paleidimas.
- Senesnė dokumentacija teigė, kad modeliai parenkami `estimators` žodyne ir
  jų sąrašai kartojami keliose vietose. Pataisyta pagal faktinį `if/elif`
  kodą ir bendrą `PRIMARY_MODELS` sąrašą.
- Pašalintas fiksuotas grafiko mėnesių pavadinimas: jis klaidintų pakeitus
  skaidymo nustatymus. Konkretūs mėnesiai lieka `split_summary.csv`.

### Ribos

Modelių mokymas ir toliau vykdomas sklearn viduje. Kitam mokymo duomenų
rinkiniui reikia pritaikyti `data.py`. RF ir logistinės regresijos analizė
susieta su jų vardais. `--output` nepakeičia bendro `models/` katalogo.
Notion turinys šiuo kodo pakeitimu automatiškai neatsinaujina.

### Patikros rezultatai

- Visi 7 automatiniai testai praėjo; Python moduliai sėkmingai sukompiliuoti.
- Pilnas eksperimentas po importo pataisymo sėkmingai baigtas.
- `metrics.csv` (be vykdymo trukmės), `test_predictions.csv`,
  `model_selection.csv`, `split_summary.csv`, `split_membership.csv`,
  `subgroups.csv`, `error_examples.csv` tiksliai sutampa su ankstesniais
  rezultatais, naudojant `pandas.testing.assert_frame_equal(check_exact=True)`.
- Atskirai paleistas grafikų atkūrimas iš CSV ir naujų sesijų prognozavimas.
- Ankstesni `results/` eksperimento įrodymai išsaugoti; struktūros patikra
  atlikta atskirame laikiname rezultatų kataloge. Modelių failai permokyti
  su tais pačiais parametrais. Prognozės nepasikeitė.

Šiuos pakeitimus ir patikras atliko AI pagal vartotojo nurodymus; jie nėra
studento savarankiško kodo paaiškinimo ar gynimo įrodymas.
