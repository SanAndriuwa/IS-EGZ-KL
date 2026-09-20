# Kolokviumo plano peržiūra pagal vertinimo kriterijus

2026-09-18. Vertintas `KOLIOKVIUMO_PLANAS.md` tekstas prieš šios dienos papildymą.
Tai AI atlikta dokumento peržiūra, ne dėstytojo pažymys. Pradinio teksto
orientacinis įvertis - **7,50 / 10**. Didžiausia spraga buvo išsamus pagrindinio
metodo palyginimas su kiekviena alternatyva (3.2), o ne kodo trūkumas:
kolokviumui kodo ir galutinių rezultatų nereikalaujama.

| Kriterijus | Maks. | Ankstesnio teksto įvertis | Kodėl sumažinta / kas jau buvo gerai | Papildyta redakcija |
|---|---:|---:|---|---|
| 1.1. Problemos supratimas | 0,25 | 0,25 | Įvardyta praktinė vertė, PageValues ir prognozės momento ribos | 1 ir 8 sk.: aiški neaiškumų lentelė |
| 1.2. Išskaidymas | 0,25 | 0,25 | Etapai ir moduliai buvo pateikti | 2.1 ir 5.2: etapai bei jų baigimo požymiai |
| 1.3. Suprantamos formuluotės | 0,50 | 0,30 | Per daug techninių terminų, mažai praktinės uždavinių prasmės | 1.1 ir 2.1: paaiškinimas įvairių sričių skaitytojams |
| 2.1. Alternatyvos | 0,50 | 0,50 | Metodai ir baseline įvardyti | 3 sk.: trys mokomi metodai ir paprasta atskaita |
| 2.2. Tinkamumo argumentai | 1,50 | 1,20 | Šaltiniai pateikti, ryšys su konkrečia užduotimi trumpas | 3 ir 9 sk.: kiekvieno metodo tinkamumas šiai schemai ir šaltinių ribos |
| 3.1. Pasirinkimas | 0,50 | 0,50 | RF pasirinktas aiškiai | 4.1: aiškūs projektavimo prioritetai |
| 3.2. Išskirtiniai privalumai | 2,50 | 1,30 | Nepakankamas tiesioginis palyginimas su alternatyvomis | 4.2-4.4: atskiri palyginimai, trūkumai, sąlygos, hipotezė ir sprendimo taisyklė |
| 4.1. Įvestis / išvestis | 0,50 | 0,50 | Schema ir tikimybės interpretacija pateiktos | 2.2-2.3: mokymo ir naudojimo įvestys atskirtos, pateiktas pavyzdys |
| 4.2. Veiksmų seka | 1,00 | 0,85 | Eiga buvo trumpa, dalis taisyklių tik kitame faile | 5 ir 7 sk.: savarankiškas planas su tinklu ir biudžetu |
| 4.3. Formulės | 2,50 | 1,85 | RF formulė gera, bet trūko pilno kelio nuo žalių duomenų bei rankinio pavyzdžio | 6-7 sk.: paruošimas, medžio kelias, lapo tikimybė, vidurkis, slenkstis ir metrikos |
| Iš viso | 10,00 | 7,50 | Preliminarus turinio įvertis | Visiems kriterijams dabar yra konkretus turinys |

## Galutinės redakcijos patikra

- Dokumentas yra įgyvendinimo planas, jame nėra pateikiamų galutinio eksperimento rezultatų.
- Apima visus 10 lentelės kriterijų bei papildomus užduoties punktus:
  abliaciją, klaidų analizę, skaičiavimo biudžetą, grėsmes ir AI naudojimą.
- 3.2 punkte neteigiama, kad RF visais atvejais geresnis. Aiškiai nurodyta,
  kada pranašumas tikėtinas, o kada tiktų paprastesnė alternatyva.
- 4.3 punkte paaiškinta kintamųjų kilmė ir numatomi moduliai, todėl formulės
  nėra vien nepaaiškintos matematinės išraiškos.
- Metodų teiginiams naudoti pirminiai šaltiniai ir oficiali bibliotekos
  dokumentacija. Friedman pilno teksto prieigos apribojimas atskleistas.
- Originali hipotezė ir pradinis `PROTOKOLAS.md` neperrašyti pagal jau žinomą
  rezultatą. Naujoji dokumento redakcija aiškiai pažymėta kaip patikslinimas.

**Išvada:** naujojoje redakcijoje dokumentiniu lygmeniu padengti visi maksimaliam
balui numatyti punktai. Tai nėra garantuotas 10/10: dėstytojas gali kitaip
vertinti argumentų stiprumą ir pareikalauti paaiškinti darbą žodžiu.

## Ką studentui mokėti paaiškinti

1. Kodėl sesijos suvestinė dar neįrodo prognozės iki pirkimo?
2. Kodėl RF pasirinktas, bet nėra iš anksto paskelbtas laimėtoju?
3. Ką grąžina vienas medis ir kaip iš jo gaunama miško tikimybė?
4. Kuo skiriasi AP ir tikslumas bei modelio pasirinkimas ir slenksčio pasirinkimas?
5. Kodėl transformacijų negalima mokyti iš viso rinkinio?
6. Ką darysime, jei numatyta hipotezė nepasitvirtins?

Pateikimui: [kolokviumo planas PDF](KOLIOKVIUMO_PLANAS.pdf).
Redagavimui: [tas pats tekstas Markdown](KOLIOKVIUMO_PLANAS.md).
