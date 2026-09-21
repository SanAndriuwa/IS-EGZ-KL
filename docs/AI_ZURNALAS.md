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

## 2026-09-18 — kolokviumo plano peržiūra ir PDF

Vartotojas pateikė 10 vertinimo kriterijų (10 balų suma), paprašė įvertinti
aiškumą, sutvarkyti dokumentą maksimaliam įvertinimui ir įkelti PDF į GitHub.
Patikslino, kad reikalingas įgyvendinimo planas, o ne kodas ar galutiniai rezultatai.

AI perskaitė esamą planą, protokolą, konfigūraciją ir reikalavimus. Ankstesnio
teksto preliminarus turinio įvertis - 7,50/10; stipriausiai papildytas pagrindinio
metodo palyginimas su alternatyvomis, formulių paaiškinimas ir uždavinių praktinė
prasmė. Vertinimo pagrindas išsaugotas KOLIOKVIUMO_VERTINIMAS.md. Pažymėta, kad
AI peržiūra negarantuoja dėstytojo pažymio.

Sukurtas savarankiškas 9 skyrių planas: problema, etapai ir schema, trys mokomi
metodai bei baseline, RF pasirinkimas ir hipotezė, eksperimento eiga, formulės,
vertinimas ir biudžetas, rizikos ir AI naudojimas, šaltiniai ir kriterijų žemėlapis.
Galutinių modelių rezultatų plane nėra. Pradinis PROTOKOLAS.md nekeistas;
patikslinta redakcija nevadinama nauja išankstine registracija.

Šaltinių patikra: atvertas UCI puslapis, Breiman autoriaus PDF ir oficialios
sklearn 1.8 regresijos, ansamblių, RandomForestClassifier bei AP dokumentacijos.
Friedman DOI nukreipė į leidėją, tačiau pilnas tekstas neprieinamas; mechanizmo
paaiškinimas remtas oficialia bibliotekos dokumentacija. Ši riba nurodyta plane.

Markdown ir PDF generuojami iš vieno turinio scripts/build_colloquium_pdf.py.
PDF patikra: 9 A4 puslapiai, lietuviški šriftai, puslapių numeriai, formulės,
lentelės, aktyvios šaltinių nuorodos. Puslapiai renderinti ir vizualiai peržiūrėti;
papildomai patikrintos teksto ribos. Tai dokumentacijos pakeitimas: modeliai
nepermokyti ir rezultatų skaičiai nekeisti.


## 2026-09-18 — formulės ir VILNIUS TECH šablono patikra

Vartotojo prašymu iš plano pašalintas 9.1 atitikties žemėlapis. Formulės
surinktos LaTeX, su tikromis trupmenomis, sumų ribomis, indeksais ir dalinėmis
taisyklėmis. PDF įterptas vektorinis turinys, ne mažos raiškos paveikslėliai.
14 formulių numeruojamos tęstinai (1)-(14), numeriai dešinėje; tekste pateiktos
nuorodos į formules. Matematinė sprendimo logika nekeista.

Rastas oficialus VILNIUS TECH įrašas „Rašto darbo maketavimo šablonas (LT)“:
https://etalpykla.vilniustech.lt/handle/123456789/156359 . Bibliotekos puslapis
https://vilniustech.lt/biblioteka/moksline-komunikacija/vilnius-tech-baigiamieji-darbai-elaba-etd/
nurodo universiteto prisijungimo ir suteiktų prieigos teisių poreikį.
Šablono turinio gauti nepavyko; kai kurios rastos senesnės metodinių nurodymų
PDF nuorodos grąžino 404. Todėl dabartinis šriftas, paraštės ir intervalai
NEPRISTATOMI kaip patikrinta atitiktis konkrečiai VILNIUS TECH katedros tvarkai.
Tiksliai adaptacijai reikalingas vartotojo pateiktas šablonas arba gairės.

Formulių numeracija yra pasirinktas akademinis įforminimas, o ne nepasiekiamo
šablono taisyklių citata. Microsoft Word redaguojamų OMML formulių šiame PDF
nėra; lygiavertis vizualus surinkimas atliktas LaTeX. Generavimo scenarijus ir
jo priklausomybių aprašas atnaujinti. PDF iš naujo renderintas bei patikrintas.

## 2026-09-18 — prisegto VILNIUS TECH šablono pritaikymas

Vartotojas pateikė `01-BD-ablonas.docx`. Jo stiliuose patikrinta, kad pagrindiniam
tekstui numatyta Times New Roman 12 pt ir 1,5 eilutės intervalo logika, antraštės
juodos, citavimui nurodytas APA 7, o formulės turi būti kuriamos per Word
`Insert Equation` ir numeruojamos. Šios taisyklės naudotos kaip PDF maketo
orientyras; PDF nepretenduoja atkartoti Word OMML objekto, nes jo paskirtis yra
stabilus galutinis PDF.

Numeruotos nuorodos pakeistos į APA autoriaus–metų citatas, o šaltinių sąrašas
pertvarkytas į APA 7 tipo įrašus. AI gali parinkti kandidatinį šaltinį, bet galutinę
citatą tvirtina autorius: jis turi atverti pirminį arba oficialų puslapį, sutikrinti
autorių, metus, DOI, nuorodą ir teiginio atitiktį. Jei pilnas tekstas nebuvo
perskaitytas, žurnale tai aiškiai pažymima.

Į formulų skyrių įtraukta simbolių–realizacijos lentelė. Joje `x`, `y`, `m`, `μ`,
`s`, `z`, `L_b(z)`, `B`, `τ` ir metrikų simboliai susieti su `data.py`,
`preprocessing.py`, `models.py`, `training.py` ir `evaluation.py`. Tai reiškia,
kad prieš vykdymą tikrinama ne vien graži formulė, bet ir ar kiekvienas jos
kintamasis egzistuoja programoje bei ar jo skaičiavimo tvarka sutampa.

Į planą įtraukta vektorinė 1 pav. „Sprendimo eiga“: CSV patikra → paruošimas →
kandidatų mokymas → validacijos AP ir slenksčio parinkimas → testas ir prognozė.
Paveikslas pažymėtas „sudaryta autoriaus“, todėl tai nėra nepatikrinta išorinio
šaltinio iliustracija.

Kodo autorystė dokumente patikslinta: AI parengė pradinį aiškų kodą pagal užduoties,
projekto ir bibliotekų dokumentacijos reikalavimus, tačiau autorius turi pats
perskaityti modulius, paleisti testus, patikrinti rezultatus, gebėti paaiškinti
sprendimus ir priimti galutinę redakciją. AI sugeneruotas kodas nėra automatiškai
laikomas vien autoriaus savarankiškai parašytu kodu.

## 2026-09-18 — kalbos redakcija, parametrų paaiškinimai ir šaltinių patikra

Autorius paprašė natūralesnės įžangos ir problemos formuluotės, angliškų
terminų kursyvu, 5.3 skyriaus skaičių pagrindimo ir aiškesnio „sėklos“ termino.
AI perrašė šias vietas, nekeisdamas ML modelių parametrų, imčių ar rezultatų.
Vartojama „atsitiktinių skaičių generatoriaus pradinė reikšmė (angl. random
seed)“; paaiškinta, kad 42 yra sutartinis pakartojamumo nustatymas, ne kokybės
garantija. „Manifestas“ paaiškintas kaip eksperimento vykdymo aprašas.

Parametrų reikšmių pasirinkimas aiškiai atskirtas nuo dokumentacijoje
aprašytos jų paskirties. 200 medžių, 150 iteracijų, žingsnis 0,05 bei dviejų
kandidatų poros yra riboto eksperimento projektiniai sprendimai; jų optimalumas
šiam rinkiniui neįrodytas. Eksperimentas šiame redagavimo etape nevykdytas.

AI atvėrė UCI rinkinio puslapį, Breiman autoriaus rankraštį ir oficialią
scikit-learn 1.8 metodų bei AP dokumentaciją. Tikrintos konkrečios dalys,
ne deklaruotas visų straipsnių perskaitymas. Friedman DOI nukreipė į leidėją,
bet pilnas tekstas liko neprieinamas; metaduomenys taip pat sutikrinti su
oficialios scikit-learn ansamblių dokumentacijos References įrašu.
Darbo citatos yra perfrazavimai, ne pažodiniai straipsnių vertimai.
Dokumentacijos prieigos metai nebepateikiami kaip publikavimo metai:
vartojama n.d.-a–n.d.-f. Breiman rankraštis nebeskaičiuojamas kaip atskiras
tyrimas. Galutinė šaltinių, formulių, kodo ir rezultatų validacija palikta
autoriui; nėra teigiama, kad jis jau atliko šiuos veiksmus.

Patikslinta formulių ir kodo lentelė: formulės simbolis neprivalo būti
pažodinis kodo kintamojo vardas; forest_probability_by_formula tikrina medžių
predict_proba vidurkinimą, bet nepriklausomai neatkuria medžio apėjimo.

Ankstesnio DOCX renderinime aptiktos lentelių ir schemos konvertavimo klaidos.
Sukurtas pakartojamas build_colloquium_docx.py scenarijus: tikros lentelės,
iliustracija vietoj Mermaid teksto, kursyvas ir 14 redaguojamų OMML formulių.
DOCX nustatyta A4, 30 mm kairė ir 20 mm kitos paraštės, Times New Roman 12 pt,
1,5 pagrindinio teksto intervalas. Ši aplinka Times New Roman neturi, todėl
PDF eksportuotojas naudoja pakaitinį šriftą; absoliuti šablono atitiktis
neteigiama. Galutinis PDF eksportuojamas iš DOCX, kad failų maketai sutaptų.
Dokumento įgūdžių renderinimo patikra paskatino šias maketo pataisas.

Pradinis protokolas ir ankstesni žurnalo įrašai palikti kaip istorija.
Naujos formuluotės nėra nauja išankstinė registracija. Šiame etape pakeitimai
į GitHub nesiunčiami, nes dabartinis prašymas yra teksto ir šaltinių peržiūra.

Galutinė techninė patikra: 14 A4 puslapių renderinti ir peržiūrėti; išliko 14
OMML formulių bei 8 tikros lentelės. LibreOffice eksportuotojo klaidingi
dešinieji skliaustai pašalinti pakeitus delimiter objektus aiškiais OMML
matematiniais simboliais. PDF eksportuotas iš pataisyto DOCX. `git diff --check`
klaidų nerodė. Tai dokumento patikra, ne autoriaus atlikta mokslinė validacija.

## 2026-09-18 — literatūros papildymas ir puslapinės antraštės pašalinimas

Autorius paprašė papildyti literatūros sąrašą. Dabartinėje redakcijoje buvo
9 bibliografiniai įrašai, iš jų 6 scikit-learn dokumentacijos puslapiai.
AI pridėjo 6 skirtingus mokslinius šaltinius ir susiejo juos su konkrečiais
teiginiais 2.2, 5.1, 5.2, 7.1 bei 8.1 skyriuose. Sąraše dabar 15 įrašų:
7 straipsniai (įskaitant konferencijos straipsnį), 1 aiškiai pažymėtas
preprintas, 1 duomenų rinkinys ir 6 oficialios dokumentacijos puslapiai.

Patikros ribos ir vietos:
- Sakar ir kt. (2019), DOI 10.1007/s00521-018-3523-0: patikrinti Springer
  metaduomenys ir santrauka. Visas tekstas neprieinamas. Aiškiai pažymėta,
  kad santraukoje MLP rezultatai geresni už RF ir SVM; šaltinis nepateikiamas
  kaip įrodymas, kad RF geriausias. 2019 m. yra žurnalo tomo metai;
  pirmą kartą internete straipsnis paskelbtas 2018 m.
- Saito ir Rehmsmeier (2015), DOI 10.1371/journal.pone.0118432: PLOS
  pirminis tekstas, Theoretical Background / PRC poskyriai; klasių disbalansas
  ir metrikų interpretacija, ne pasirinkto 0,02 efekto pagrindimas.
- Cawley ir Talbot (2010): oficialus JMLR tekstas, 2079–2080 psl.;
  parametrų parinkimo persimokymas ir vertinimo šališkumas.
- Niculescu-Mizil ir Caruana (2005): Cornell autoriaus PDF, 1 ir 3 psl.;
  tikimybių kalibracija ir reliability diagrams. Stabilus autoriaus URL
  pateiktas vietoj per šią patikrą nepatvirtinto DOI. 8 grupės lieka mūsų
  projekto nustatymas, nepriskiriamas straipsniui.
- Pedregosa ir kt. (2011): oficialus JMLR tekstas, 2825 ir 2827 psl.;
  bibliotekos paskirtis ir Project Vision. 1.8 parametrų elgsena remiasi
  dabartine dokumentacija, o ne istoriniu bibliotekos straipsniu.
- Kapoor ir Narayanan (2022): arXiv v1 preprintas, PDF 5 psl., 2.4 skyriaus
  L1.2; transformacijų nustatymas visoje imtyje kaip informacijos nutekėjimas.
  Žurnalo DOI prieigos patvirtinti nepavyko, todėl cituojama faktiškai
  patikrinta preprinto versija, DOI 10.48550/arXiv.2207.07048.

Tyrimo parametrai, modeliai ir rezultatai nekeisti. Citatas parinko ir
nurodytas šaltinių dalis patikrino AI; galutinis autoriaus patvirtinimas
neimituojamas. Užklausos papildyme autorius paprašė pašalinti puslapinį
užrašą „IS-EGZ-KL / KOLIOKVIUMO PLANAS“. Jis pašalintas ir iš alternatyvaus
PDF generavimo scenarijaus; galutinis Word eksportas šio užrašo neturi.

Patikra: atnaujinto DOCX eksportas sudaro 16 A4 puslapių; visi puslapiai
renderinti ir vizualiai peržiūrėti. Išlaikytos 14 formulių ir 8 lentelės.
Šeši nauji įrašai turi nuorodas pagrindiniame tekste; bibliografija turi
15 unikalių įrašų. `git diff --check` klaidų nerodė.

## 2026-09-18 — 9 skyriaus sutrumpinimas ir šablono nuoroda

Autoriaus prašymu 9 skyriuje paliktas tik literatūros sąrašas. Pašalinti
šaltinių tikrinimo paaiškinimai, prieigos datos komentarai ir papildomos
pastabos apie Breiman bei Friedman šaltinius. Bibliografiniai įrašai ir
nuorodos į šaltinius išsaugoti.

Pridėta aiški nuoroda į atskirą pateiktą VILNIUS TECH failą
`KOLIOKVIUMO_PLANAS_TEMPLATE.docx`. Šablonas nėra įterpiamas į galutinį
planą, nes jis yra pradinė dokumento rengimo forma; planas sukurtas pagal jo
paraščių, šrifto ir formulių įforminimo nuostatas. Atlikus pakeitimą dokumentas
renderintas iš naujo; 14 formulių išliko OMML formatu, o literatūros sąrašas
užima paskutinį dokumento puslapį.

## 2026-09-18 — hipotezės ribos 0,02 paaiškinimas

Autorius paprašė paaiškinti, kodėl hipotezėje pasirinkta būtent 0,02 riba.
Plane įrašyta, kad tai yra absoliutus AP skirtumas, lygus 2 procentiniams
punktams. Jis pasirinktas kaip preliminari minimalaus praktiškai pastebimo
pagerėjimo riba, kad 0,001–0,003 skirtumai nebūtų automatiškai laikomi
reikšmingu pranašumu. Pažymėta, kad 0,02 nėra universalus literatūros dydis,
nes nėra pateiktos klaidų kainos ar ankstesnio piloto, iš kurio jį būtų galima
apskaičiuoti. Įrašyta papildoma jautrumo analizė su 0,01 ir 0,05 ribomis bei
95 % bootstrap intervalu. Modeliai ir rezultatai nebuvo vykdyti ar pakeisti.

## 2026-09-20 — dokumentų commitų ir GitHub sinchronizavimo patikra

Autoriaus prašymu patikrinta vietinė ir GitHub istorija. Naujausi dokumentai
buvo vietiniame commite `9656a0f`, o GitHub `main` dar buvo `4495f61`.
Dokumentų atnaujinimas parengtas nuo dabartinio GitHub `main`, išsaugant jo
programos kodą ir eksperimento rezultatus. Perkelti atnaujinti DOCX, PDF,
Markdown, atskiras šablonas, generavimo scenarijai ir pataisytos nuorodos.
Failų pavadinimai pakeisti į autoriaus prašytą `KOLIOKVIUMO_` formą;
ankstesnės versijos išlieka Git istorijoje. Dokumentai iš naujo negeneruoti,
kad būtų išsaugotas anksčiau patikrintas maketas. Mokymas nevykdytas.

## 2026-09-20 — Windows paleidimas ir UTF-8 koduotė

Autorius pranešė, kad Windows CMD neatpažino `source`, o ataskaitos įrašymas
nutrūko su `UnicodeEncodeError`: numatytoji `cp1251` koduotė nepalaikė `š`.
Vėliau autorius patvirtino, kad paleidimas veikia, ir paprašė atnaujinti GitHub
bei README. AI pridėjo aiškią UTF-8 koduotę ataskaitos ir vykdymo aprašo
įrašymui bei konfigūracijos skaitymui. README išskirtos CMD, PowerShell ir
Linux/macOS instrukcijos; pateiktas paleidimas be PowerShell aktyvavimo ir
laikinas `-X utf8` sprendimas senoms kopijoms.

Pridėtas regresinis testas, imituojantis `cp1251` kaip numatytąją koduotę.
Jis patikrino, kad ataskaita išsaugoma UTF-8 ir išlaiko lietuviškas raides
bei `≥` simbolį. Testas praėjo Linux aplinkoje; tikras Windows paleidimas
šiame etape nebuvo atliktas. `git diff --check` klaidų nerodė. Išsaugoti
autoriaus commite `200560e` įkelti rezultatai; modeliai nepermokyti.

## 2026-09-21 — egzamino ataskaita ir galutinė rezultatų patikra

Autorius paprašė parengti egzamino ataskaitą be pilno programos kodo, paliekant
tik svarbiausias eilutes, įvertinti galimas klaidas ir vienoje skiltyje pateikti
nuorodą į GitHub. AI parengė atskiras DOCX, PDF ir Markdown versijas. Ataskaitoje
palikta eksperimento paleidimo komanda ir viena `predict_proba` eilutė; pridėtos
proceso, modelių palyginimo, precision–recall ir kalibracijos vizualizacijos.

Prieš rašant išvadas perskaičiuotos sumaišties matricų sumos, precision ir recall,
duomenų skaidymo sumos, kandidatų ir pogrupių eilučių skaičiai. Patikrinta, kad
manifeste įrašytos šaltinio failų kontrolinės sumos sutampa su dabartiniais failais.
Paleisti 8 automatiniai testai; visi praėjo. Ankstesniame `ATASKAITA.md` buvę
pasenę skaičiai pataisyti: autoriaus Windows vykdymas truko 6,45 s, o dabartiniame
rinkinyje yra 8, ne 7, automatiniai testai. Modeliai nepermokyti ir rezultatai
neperrašyti.

DOCX formulės sukurtos redaguojamu Microsoft Office Math (OMML) formatu ir
sunumeruotos. Naudotas tas pats A4, Times New Roman 12 pt, 1,5 intervalo ir
30/20/20/20 mm paraščių principas kaip ankstesniame pateikimo dokumente. PDF
eksportuotas iš DOCX, o visi 10 puslapių renderinti ir vizualiai peržiūrėti.
