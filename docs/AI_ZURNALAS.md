# AI naudojimo ir patikros žurnalas

Darbas parengtas su ChatGPT Codex pagal vartotojo užklausą: „Prašau atlikti nurodytą darbą, sukurti naują github repo ir sukelti tiek sprendima, tiek dokumentaciją“, pridėjus `DISfm-26_Andrej_Kondratjev.docx`. Tai faktinio šios sesijos darbo žurnalas, ne tariamų studento savarankiškų eksperimentų aprašymas.

## Pagrindinės užklausos ir veiksmai

Vartotojo užklausa buvo viena. Toliau AI ją išskaidė į dokumento perskaitymą, UCI duomenų gavimą, literatūros tikrinimą, eksperimento protokolą, programą, bandymus ir dokumentaciją. Paieškose naudotos užklausos „Breiman 2001 Random Forests doi“ ir „Friedman 2001 greedy function approximation gradient boosting machine doi“. Metodų ir metrikų realizacija tikrinta bibliotekos autorių dokumentacijoje; rezultatai gauti vykdant kodą, ne generuojant skaičius tekste.

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
