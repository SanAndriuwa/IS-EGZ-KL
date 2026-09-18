"""Atkuria kolokviumo Markdown ir PDF iš vieno turinio šaltinio.
Paleidimas projekto kataloge: python scripts/build_colloquium_pdf.py
PDF generavimui reikia reportlab; tai dokumento, ne ML eksperimento priklausomybė.
"""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONT = Path('/usr/share/fonts/truetype/dejavu')
for name, file in [('D','DejaVuSans.ttf'),('DB','DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
pdfmetrics.registerFontFamily('D',normal='D',bold='DB',italic='D',boldItalic='DB')
styles = {
 'title': ParagraphStyle('title',fontName='DB',fontSize=21,leading=26,textColor=colors.HexColor('#16324f'),spaceAfter=15),
 'h': ParagraphStyle('h',fontName='DB',fontSize=12,leading=16,spaceBefore=12,spaceAfter=6,textColor=colors.HexColor('#16706b'),keepWithNext=True),
 'p': ParagraphStyle('p',fontName='D',fontSize=9.5,leading=14,spaceAfter=7),
 'small': ParagraphStyle('small',fontName='D',fontSize=8.3,leading=11.7,spaceAfter=4),
 'eq': ParagraphStyle('eq',fontName='D',fontSize=11,leading=17,spaceBefore=5,spaceAfter=7,leftIndent=12,textColor=colors.HexColor('#16324f')),
}
pages=[]
def page(title):
    pages.append([('title',title)])
def p(t): pages[-1].append(('p',t))
def h(t): pages[-1].append(('h',t))
def eq(t): pages[-1].append(('eq',t))
def table(headers,rows,widths): pages[-1].append(('table',(headers,rows,widths)))

page('1. Problema ir sprendimo paskirtis')
p('<b>Elektroninės parduotuvės pirkimo ketinimo tyrimo įgyvendinimo planas</b><br/>Andrej Kondratjev | DISfm-26 | Intelektualiosios sistemos | 2026-09-18')
p('Dokumento paskirtis - apibrėžti įgyvendinimą prieš naujo bandymo vykdymą: duomenis, metodus, sprendimo taisykles ir vertinimą. Čia nepateikiami galutinio eksperimento rezultatai. Tai patikslinta projekto plano redakcija; pradinio protokolo istorija išsaugoma atskirai, todėl ši redakcija nėra nauja išankstinė registracija.')
h('1.1. Problema, techninis uždavinys ir vertė')
p('Elektroninė parduotuvė turi naršymo sesijų duomenų, tačiau vien puslapių ar praleisto laiko skaičius nepasako, kuri sesija labiau tikėtina baigsis pirkimu. Reikia išmokti ryšį tarp kelių sesijos požymių ir pirkimo fakto.')
p('<b>Techninis uždavinys:</b> prižiūrimo mokymosi dvejetainė klasifikacija. Iš vienos sesijos požymių x apskaičiuoti pirkimo tikimybės įvertį p(x) ir klasę: 1 - pirks, 0 - nepirks. Mokymui pateikiamas žinomas atsakymas Revenue; prognozuojant jo nereikia.')
p('<b>Praktinė vertė:</b> sesijų rangavimas galėtų padėti planuoti konsultantų dėmesį ir analizuoti pirkimo elgseną. Projektų vadovui rezultatas būtų patikrinamas prototipas; finansininkui - klaidingų signalų ir praleistų pirkėjų skaičiai; vadybininkui - prioritetų sąrašas; personalo vadybininkui - informacija galimam konsultantų apkrovos planavimui. Darbuotojų vertinimas nėra šio modelio paskirtis.')
h('1.2. Neakivaizdžios problemos dalys')
table(['Neaiškumas','Sprendimas plane'],[
['Kada žinomi požymiai?','CSV yra sesijos suvestinė. Tiriamas neprisijungęs klasifikavimas; realaus laiko prognozė neįrodoma. PageValues pagrindiniame modelyje nenaudojamas.'],
['Kuris metodas tinkamiausias?','Tiesinį modelį ir du medžių ansamblius lyginti tomis pačiomis imtimis bei metrikomis.'],
['Mažuma sesijų baigiasi pirkimu','Bendro accuracy nepakanka. Vertinti AP, precision, recall ir klaidų skaičius.'],
['Ar ryšiai išliks vėliau?','Mokyti ankstesniais mėnesiais, vertinti vėlesniais; aprašyti sezoninio poslinkio ribą.'],
['Kiek kainuoja klaida?','FP - bereikalingas kontaktas, FN - praleistas pirkėjas. Eurais kainos nežinomos; jų neišgalvoti.']],[130,365])
p('Prognozė neįrodo, kad nuolaida ar konsultanto kontaktas pakeistų pirkėjo elgesį. Tam reikėtų atskiro intervencijos eksperimento. Konkretaus komercinio įrankio veikimas neaudituojamas, todėl jam nepriskiriami nepatikrinti gebėjimai.')

page('2. Užduotys, duomenys ir išvestis')
h('2.1. Etapai, suprantami skirtingų sričių specialistams')
table(['Etapas','Ką darome ir kodėl','Baigimo požymis'],[
['Duomenų gavimas','Gauname patikimos kilmės sesijų lentelę, kad išvada remtųsi tikrais duomenimis.','Patikrintas originalus CSV ir jo SHA256.'],
['Paruošimas','Suvienodiname reikšmes ir atskiriame senesnes bei naujesnes sesijas, kad palyginimas būtų sąžiningas.','Trys nesikertančios imtys; schema ir tušti langeliai patikrinti.'],
['Mokymas','Modeliams pateikiame ankstesnius pavyzdžius, kad jie išmoktų ryšį su pirkimu.','Kiekvieno kandidato modelis.'],
['Parinkimas','Su atskirais pavyzdžiais pasirenkame parametrus ir jautrumą klaidoms.','Vienas kandidatas ir slenkstis kiekvienam metodui.'],
['Vertinimas','Pamatuojame naudą naujesniu laikotarpiu ir paaiškiname klaidas.','Metrikos, palyginimas, klaidų pavyzdžiai.'],
['Naudojimas','Naujai sesijai pateikiame įvertį, nekartodami mokymo.','CSV: eilutės numeris, tikimybė, prognozė.']],[86,251,158])
h('2.2. Duomenų šaltinis ir tiksli schema')
p('Naudojamas UCI Online Shoppers Purchasing Intention Dataset: 12 330 sesijų, 17 pradinių požymių ir tikslas Revenue [1]. Modeliui atrenkama 15 požymių. Viena CSV eilutė - viena sesija; į modelį siunčiama požymių lentelė, o ne svetainės vaizdas ar tekstas.')
p('<b>9 skaitiniai:</b> Administrative, Administrative_Duration, Informational, Informational_Duration, ProductRelated, ProductRelated_Duration, BounceRates, ExitRates, SpecialDay. Pirmieji trys pavadinimų tipai žymi puslapių kiekius, jų Duration - trukmes sekundėmis; paskutiniai trys rodikliai yra intervale [0; 1].')
p('<b>6 kategoriniai:</b> OperatingSystems, Browser, Region, TrafficType, VisitorType, Weekend. Skaitiniai kategorijų kodai laikomi pavadinimais, ne dydžiais. Month naudojamas tik skaidymui. PageValues naudojamas tik atskirame požymio įtakos bandyme. Revenue: False → 0, True → 1.')
h('2.3. Įvesties ir išvesties sutartis')
p('Mokymo CSV turi požymius, Month ir Revenue. Naujam prognozių CSV reikia visų pasirinkto modelio požymių stulpelių; Revenue ir Month nereikalingi. Papildomi stulpeliai ignoruojami. Tuščias langelis užpildomas, bet visai nesantis privalomas stulpelis yra klaida. Neigiami ar begaliniai skaitiniai dydžiai bei dažniai virš 1 atmetami.')
p('Išvestis: row - įvesties eilutės numeris nuo 0; purchase_probability - modelio įvertis [0; 1]; prediction - 0 arba 1 pagal slenkstį τ. Pavyzdžiui, p = 0,30 ir τ = 0,20 duoda klasę 1. Tai iliustracija, ne tyrimo rezultatas; 0,30 nėra pirkimo garantija.')

page('3. Metodų alternatyvos ir šaltiniai')
p('Intelektualieji metodai taikomi pirkimo klasifikavimo uždaviniui. CSV gavimui ar failų įrašymui dirbtinio intelekto nereikia. Nagrinėjami <b>trys mokomi metodai ir viena paprasta atskaita</b>.')
h('3.1. Paprastas baseline: mokymo pirkimų dažnis')
p('Kiekvienai sesijai grąžinama ta pati mokymo imties pirkimų dalis. Tai patikrina, ar modelis iš požymių išmoksta daugiau negu vien bendrą klasės dažnį. Šis metodas sesijų neranguoja; formulė pateikta 6 skyriuje. Tai aritmetinė atskaita, ne pagrindinis intelektualusis metodas.')
h('3.2. Logistinė regresija - stipresnė atskaita')
p('Modelis mokosi skaitinių ir užkoduotų kategorinių požymių svorių, o sigmoidė duoda pirkimo tikimybės įvertį [2]. Tinka dvejetainiam tikslui ir nedidelės ar vidutinės dimensijos lenteliniams duomenims. Šiame plane tai interpretuojamas palyginimas, padedantis patikrinti, ar sudėtingesnio modelio apskritai reikia.')
p('Riba: be papildomų sąveikų požymių logaritminis šansų santykis yra tiesinis. Pavyzdžiui, tas pats naršymo laikas skirtingai produktų peržiūrų grupei gali turėti kitą reikšmę; ši sąveika automatiškai neįtraukiama. Šaltinis pagrindžia algoritmo formą, bet ne jo būsimą tikslumą šiame rinkinyje.')
h('3.3. Atsitiktinis miškas - pagrindinis metodas')
p('Atskirų medžių sąlygų deriniai leidžia mokytis netiesinių ryšių ir požymių sąveikų. Bootstrap imtys ir atsitiktiniai požymių poaibiai sukuria skirtingus medžius, kurių rezultatai sujungiami [3]. Tai prasminga sesijų lentelei, kur kiekių, trukmių ir lankytojo tipo sąveikos iš anksto nežinomos.')
p('Breiman (2001), DOI 10.1023/A:1010933404324, pagrindžia miško konstrukciją; konkreti sklearn realizacija tikimybes skaičiuoja kaip medžių lapų tikimybių vidurkį [4]. Riba: ansamblis mažiau skaidrus negu svorių modelis, o laiko poslinkis gali panaikinti išmoktų taisyklių naudą.')
h('3.4. Histograminis gradientinis stiprinimas')
p('Medžiai pridedami nuosekliai, kad mažintų pasirinkto nuostolio likusią paklaidą. Metodas gali atkurti sudėtingus lentelinių požymių ryšius [5, 6], todėl yra prasminga kita netiesinė alternatyva tam pačiam dvejetainiam uždaviniui.')
p('Friedman (2001), DOI 10.1214/aos/1013203451, yra bendro metodo pirminis šaltinis; histograminės realizacijos ir parametrų elgsena remiama bibliotekos autorių dokumentacija [6]. Reikia derinti žingsnio, iteracijų ir medžių sudėtingumo sąveiką. Tai savaime nereiškia, kad metodas blogesnis už mišką.')
h('3.5. Pagrindimo ribos')
p('Duomenų šaltinis [1] patvirtina klasifikavimo uždavinį ir įvesčių pobūdį. Šaltiniai [2-6] pagrindžia mechanizmus, o jų pritaikymas šiai schemai yra argumentuota projektavimo išvada. Nei pirminis straipsnis, nei algoritmo populiarumas negarantuoja pranašumo šiame eksperimente.')

page('4. Pagrindinis sprendimas ir hipotezė')
h('4.1. Pasirinkimas')
p('<b>Pagrindiniam tyrimui pasirenkamas atsitiktinis miškas.</b> Projektavimo prioritetai: automatiškai aprašyti netiesines sąveikas, turėti aiškią prognozės skaičiavimo taisyklę ir tilpti į nedidelį CPU eksperimentą. Tai pasirinkimas patikrinti, o ne teiginys apie jau įrodytą globalų optimumą.')
h('4.2. Kodėl jis pasirenkamas prieš kiekvieną alternatyvą?')
table(['Alternatyva','Miško privalumas šiame plane','Kada alternatyva tinkamesnė?'],[
['Pastovus dažnis','Naudoja konkrečios sesijos požymius, todėl gali atskirti pirkėjus ir nepirkėjus. Pastovus įvertis visiems vienodas.','Kai požymiai neturi patikimo signalo; paprasčiausias dažnis gali būti pakankama tikimybinė atskaita.'],
['Logistinė regresija','Sąlygų sekos medžiuose automatiškai aprašo sąveikas ir slenksčius, kuriuos regresijai tektų projektuoti atskirai.','Kai ryšys beveik tiesinis, svarbiausia paaiškinti svorius arba kokybės skirtumas mažas.'],
['Gradientinis stiprinimas','Medžiai mokomi nepriklausomai, todėl prognozės vidurkį paprasta paaiškinti. Šiame plane parenkamas vienas lapo dydžio parametras, neforsuojant žingsnio ir iteracijų derinimo.','Kai nuoseklus klaidų taisymas duoda geresnę patikimą kokybę ir yra biudžeto papildomam derinimui.']],[94,226,175])
p('Netiesiškumas yra privalumas prieš tiesinę regresiją, bet ne išskirtinis privalumas prieš gradientinį stiprinimą: abu medžių metodai aprašo sąveikas. Miškas taip pat nėra lengviau interpretuojamas už logistinę regresiją. RF parametrų paprastumas čia yra konkretaus riboto eksperimento pasirinkimas, ne universalus metodų reitingas.')
h('4.3. Patikrinama hipotezė ir sąlygos')
p('<b>H1:</b> nenaudojant PageValues, RF galutinio testo AP bus bent 0,02 didesnė už logistinės regresijos AP, jeigu netiesinės naršymo intensyvumo ir išėjimo rodiklių sąveikos išlieka vėlesniais mėnesiais. Logistinė regresija yra stipresnė atskaita; papildomai pateikiamas palyginimas su pastoviu dažniu.')
eq('ΔAP = AP(RF) - AP(logistinė regresija); tikslas: ΔAP ≥ 0,02.')
p('0,02 yra iš anksto pasirinktas praktinio pagerėjimo kriterijus, ne iš literatūros gautas garantuotas efektas. Abu modeliai gauna tas pačias imtis ir tą patį parinkimo kriterijų; kiekvienam skiriami du kandidatų mokymai.')
h('4.4. Kaip bus daroma išvada?')
p('Jei ΔAP &lt; 0,02, numatytas pagerėjimas šiame teste nepasitvirtins. Jei ΔAP ≥ 0,02, kriterijus bus pasiektas tik šiame teste; papildomai vertinamas 95 % porinio bootstrap intervalas. Jei intervalas apima nulį, tvirto teiginio apie persvarą nedarysime. Nepasiekus prasmingos persvaros, paprastesnė regresija liks pagrįsta praktinė alternatyva. Testo rezultatu nebus perrašomas pradinis parinkimo planas.')

page('5. Algoritmo eiga ir eksperimento taisyklės')
h('5.1. Skaidymas ir duomenų paruošimas')
p('Sėkla - 42. Train: Feb, Mar, May, June, Jul, Aug; validation: Sep, Oct; test: Nov, Dec. Jan ir Apr įrašų rinkinyje nėra. Month nėra modelio požymis. Imtys turi nesikirsti, apimti visas eilutes ir turėti abi klases. Chronologija tikrinama pagal mėnesio numerį; tikslių laiko žymų nėra.')
p('Tik train imtyje išmokstama skaitinių medianų, standartizavimo ir kategorinių modų bei one-hot kategorijų aibė. Validation, test ir naujos sesijos tik transformuojamos. Nežinoma kategorija koduojama nuliais savo kategorijos indikatorių grupėje. Standartizavimas naudingas regresijai; medžiams nebūtinas, bet grandinė visiems vienoda. SMOTE ir klasių svoriai nenaudojami.')
h('5.2. Veiksmų seka programuotojui')
table(['Nr.','Veiksmas','Planuojamas modulis'],[
['1','Gauti CSV; patikrinti SHA256, schemą, reikšmes ir Revenue kodavimą.','data.py'],
['2','Skaidyti pagal Month; išsaugoti originalių eilučių priklausomybę imtims.','data.py, reporting.py'],
['3','Kiekvienam kandidatui sukurti naują paruošimo ir klasifikatoriaus grandinę.','preprocessing.py, models.py'],
['4','Išmokyti tik su train; apskaičiuoti validation tikimybes ir AP.','training.py'],
['5','Pasirinkti didžiausią validation AP; lygybės atveju pirmą kandidatą.','training.py'],
['6','Jo validation tikimybėmis parinkti F2 slenkstį. Užfiksuoti modelį ir slenkstį.','evaluation.py, training.py'],
['7','Vieną kartą vertinti švarų testą; atlikti suplanuotus papildomus bandymus.','experiment.py, analysis.py'],
['8','Įrašyti metrikas, prognozes, grafikus, kodų sumas ir visą modelio grandinę.','reporting.py, plots.py'],
['9','Naują CSV tikrinti ir transformuoti išsaugota grandine; pateikti tikimybes.','predict.py']],[26,322,147])
p('Po pasirinkimo modelis nepermokomas su validation duomenimis. Slenkstis parenkamas iš 0,01; 0,02; ...; 0,99 pagal didžiausią F2; lygybės atveju mažesnis. Testas neperduodamas kandidatų ar slenksčio parinkimo funkcijai.')
h('5.3. Fiksuotas kandidatų tinklas')
p('Pastovus dažnis: 1 kandidatas. Regresija: C = 0,1 arba 1,0; max_iter = 2000. RF: 200 medžių, max_features = sqrt, min_samples_leaf = 5 arba 20, n_jobs = 1; kiti numatyti sklearn 1.8 nustatymai, įskaitant bootstrap ir Gini. Stiprinimas: max_iter = 150, learning_rate = 0,05, max_leaf_nodes = 7 arba 15, early_stopping = False. Mažesnis C reiškia stipresnį reguliavimą.')

page('6. Formulės: nuo įvesties iki sprendimo')
p('Pasirinkto RF prognozės kelias: sesijos x reikšmės → paruoštas vektorius z → kiekvieno medžio lapas → lapo pirkimų dalis → medžių vidurkis → sprendimas pagal slenkstį. Indeksas i žymi sesiją, j - skaitinį požymį, b - medį.')
h('6.1. Skaitinių duomenų paruošimas')
eq('x′ᵢⱼ = xᵢⱼ, jei reikšmė žinoma; kitu atveju x′ᵢⱼ = mⱼ.')
eq('zᵢⱼ = (x′ᵢⱼ - μⱼ) / sⱼ.')
p('mⱼ - j požymio žinomų train reikšmių mediana; μⱼ ir sⱼ - jau užpildyto train stulpelio vidurkis ir standartinis nuokrypis. Jei stulpelis pastovus, StandardScaler naudoja skalę 1. Validation ir test reikšmės nekeičia šių parametrų. Kategorijai c kuriamas indikatorius I(x = c), lygus 1 sutapus kategorijai ir 0 nesutapus. Gautos skiltys sujungiamos į z. Modulis: preprocessing.py.')
h('6.2. Vieno medžio taisyklė ir tikimybė')
eq('Jei zⱼ ≤ t, eiti į kairį vaiką; kitu atveju - į dešinį.')
eq('p<sub>b</sub>(z) = n<sub>b,1</sub>(L<sub>b</sub>(z)) / n<sub>b</sub>(L<sub>b</sub>(z)).')
p('j ir t - mokymo metu parinkto mazgo požymio indeksas ir slenkstis. Kartojame sąlygą iki lapo Lᵦ(z). nᵦ,₁ - pirkusių mokymo pavyzdžių svoris tame lape; nᵦ - visų mokymo pavyzdžių svoris tame lape. Bootstrap pasikartojimai skaičiuojami su jų kartotinumu. Tai mokymo lapo statistika, ne naujos sesijos Revenue. Naujos sesijos tikras atsakymas prognozei nežinomas.')
h('6.3. Miško išvestis ir dvejetainis sprendimas')
eq('pRF(x) = (1 / B) ∑<sub>b=1</sub><super>B</super> p<sub>b</sub>(z),   B = 200.')
eq('ŷ = 1, kai pRF(x) ≥ τ; kitu atveju ŷ = 0.')
p('B - medžių skaičius; τ - tik validation imtyje parinktas slenkstis. sklearn RF vidurkina tikimybes, ne vien medžių 0/1 balsus [4]. models.py sukurs mišką ir turės forest_probability_by_formula; analysis.py palygins formulę su predict_proba. Leistina skaitinė paklaida: 10⁻¹² (absoliuti, be santykinės tolerancijos).')
p('<b>Rankinis pavyzdys, ne rezultatas:</b> jei trijų medžių lapų tikimybės yra 0,2; 0,6; 0,4, jų vidurkis yra 0,4. Su τ = 0,3 prognozė lygi 1. Net jei tik vienas medis viršytų 0,5, sprendimas priklauso nuo tikimybių vidurkio ir pasirinkto τ.')
h('6.4. Atskaitų formulės')
eq('p₀ = (1 / N) ∑<sub>i=1</sub><super>N</super> yᵢ;     pLR(z) = 1 / (1 + exp(-(wᵀz + a))).')
p('N - train sesijų skaičius; yᵢ - jų Revenue (0/1); p₀ - pastovi pirkimų dalis. w - regresijos išmokti svoriai, a - jos poslinkis; abu gaunami tik iš train. Modulis: models.py. Mokymo optimizavimo išvedimai neprivalomi: mokymą atliks biblioteka, o šiame plane tiksliai aprašyta prognozės taisyklė.')

page('7. Vertinimas, papildomi bandymai ir biudžetas')
h('7.1. Metrikos ir jų interpretacija')
eq('P = TP / (TP + FP);   R = TP / (TP + FN);   F₂ = 5PR / (4P + R).')
p('TP - teisingai aptikti pirkimai; FP - prognozuoti pirkimai, kurių nebuvo; FN - praleisti pirkimai; TN - teisingai atmesti nepirkimai. P (precision) rodo teigiamų prognozių patikimumą, R (recall) - aptiktų pirkimų dalį. Kai vardiklis nulis, atitinkama metrika lygi 0. F2 daugiau svarbos teikia recall; tai pasirinktas mokomasis prioritetas, ne piniginis optimumas.')
eq('AP = ∑ₖ (Rₖ - Rₖ₋₁) Pₖ;    Brier = (1 / M) ∑<sub>i=1</sub><super>M</super> (pᵢ - yᵢ)².')
p('AP sumuojama slenksčius atlaisvinant nuo mažesnio iki didesnio recall; k žymi tašką, R₀ = 0. Naudojama sklearn average_precision_score realizacija [7], o ne trapecinis PR plotas. M - vertinamos imties dydis, pᵢ - modelio tikimybė, yᵢ - tikras atsakymas. Didesnė AP ir mažesnis Brier yra geriau. AP nėra procentinis klasifikavimo tikslumas.')
p('Papildomai pateikti trapecinį PR-AUC, log loss, painiavos matricą, PR kreivę ir kalibracijos kreivę su 8 vienodo dažnio grupėmis. Kalibracijos grafikas tik vertins tikimybes; papildomas kalibratorius nebus mokomas. Modulis: evaluation.py; grafikai: plots.py.')
h('7.2. Iš anksto numatyta analizė')
table(['Bandymas','Tiksli taisyklė ir tikslas'],[
['Požymio įtaka','Pakartoti RF su PageValues, paliekant tas pačias imtis ir du lapo dydžio kandidatus. Palyginti su pagrindiniu RF be šio požymio. Pagerėjimas neįrodys prieinamumo iki pirkimo.'],
['Atsparumas','Sėkla 42; nepriklausomai maskuoti apie 10 % testo skaitinių langelių. Keturiems pagrindiniams metodams ta pati kaukė. Modelių, medianų ir slenksčių nekeisti.'],
['Klaidų analizė','RF: 5 didžiausios tikimybės FP ir 5 mažiausios tikimybės FN (arba visi, jei mažiau). Papildomos suvestinės pagal Month ir VisitorType.'],
['Neapibrėžtumas','500 porinio stratifikuoto bootstrap kartojimų: su grąžinimu rinkti pirkimų ir nepirkimų eilutes, abiem modeliams tas pačias. ΔAP 2,5 ir 97,5 procentiliai sudaro sąlyginį 95 % intervalą.']],[104,391])
h('7.3. Skaičiavimo ir rezultatų planas')
p('Iš viso 9 kandidatų mokymai: 1 + 2 + 2 + 2 pagrindiniams metodams ir 2 RF su PageValues. CPU, vienas srautas, orientacinis biudžetas - 10 min. ir 4 GB RAM. Vykdymo laikas bus matuojamas, RAM - tik planavimo įvertis, ne išmatuotas ar priverstinai ribojamas dydis. Viršijus biudžetą tai pažymėti; slaptai keisti tinklelį pagal testą negalima.')
p('Numatomos išvestys: imčių sudėtis, kandidatų validation AP, testo metrikos ir sesijų tikimybės, klaidų bei pogrupių lentelės, grafikai, modelio grandinė ir manifestas su versijomis, sėkla bei kodo kontrolinėmis sumomis.')

page('8. Rizikos, AI naudojimas ir priėmimo patikros')
h('8.1. Grėsmės išvadų galiojimui')
table(['Grėsmė','Valdymas ir liekanti riba'],[
['Informacijos nutekėjimas','Revenue ir Month nepatenka į modelį; PageValues tik atskiras bandymas. Vis tiek neįmanoma iš suvestinės įrodyti visų rodiklių prieinamumo iki pirkimo.'],
['Laiko ir parduotuvės poslinkis','Chronologinis skaidymas sumažina atsitiktinio sumaišymo optimizmą. Vieni metai ir viena parduotuvė neleidžia išvados perkelti visur.'],
['Nežinomas sesijų ryšys','UCI aprašo skirtingus naudotojus, bet CSV nėra ID. Teiginio nepriklausomai patikrinti ir grupuoti pagal lankytoją negalėsime.'],
['Validacijos perkrovimas','Ribotas kandidatų tinklas, bet ta pati validation imtis parenka ir modelį, ir slenkstį. Tai likusi optimizmo rizika.'],
['Testo peržiūra','Pradinis protokolas išsaugomas. Naujas variantas po testo peržiūros būtų tiriamoji analizė; naujam patvirtinimui reikėtų naujo neliečiamo testo.'],
['Klaidos kaina ir kalibracija','F2 nėra finansinio pelno kriterijus. Prieš diegimą reikėtų klaidų kainų, prognozės momento audito ir atskiros tikimybių patikros.']],[122,373])
p('Bootstrap intervalas apibūdina šios testo imties ir šių išmokytų modelių neapibrėžtumą. Jis neapima viso mokymo proceso kintamumo, būsimų sezonų ar kitų parduotuvių. Trūkstamų reikšmių maskavimas neimituoja visų realių gedimų.')
h('8.2. AI naudojimo ir tikrinimo planas')
p('AI bus naudojamas dokumento struktūrai, pradiniam paprastam kodui, komentarams ir testų idėjoms. AI nepakeis šaltinių skaitymo ar programos vykdymo. Kiekvieną reikšmingą pakeitimą, atmestą pasiūlymą ir aptiktą klaidą registruoti AI_ZURNALAS.md.')
table(['Tikrinamas dalykas','Patikros veiksmas'],[
['Citatos','Atverti autoriaus, leidėjo ar oficialios bibliotekos puslapį; patikrinti autorių, metus, DOI ir teiginio atitiktį. Neprieinamo pilno teksto neskelbti perskaitytu.'],
['Formulės','Sutikrinti simbolius su realizacija; vienos sesijos skaičiavimą patikrinti ranka, RF medžių vidurkį - prieš predict_proba.'],
['Kodas','Testuoti nesikertančias imtis, draudžiamus požymius, tik train išmoktas transformacijas, nežinomas kategorijas ir netinkamą schemą.'],
['Rezultatai','Vykdyti eksperimentą; skaičius imti iš CSV. Patikrinti pakartojamumą su ta pačia sėkla, įrašyti versijas ir kodo sumas.']],[99,396])
p('Priėmimo sąlyga: kitas programuotojas pagal 2, 5-7 skyrius gali įgyvendinti grandinę ir gauti visus numatytus išvesties failus. Teigiamas hipotezės rezultatas nėra darbo priėmimo sąlyga. Studentas turi gebėti paaiškinti įvestį, miško formulę, slenkstį ir skaidymą.')

page('9. Šaltiniai ir vertinimo kriterijų atitiktis')
p('Pirminiai šaltiniai ir bibliotekos autorių dokumentacija patikrinti 2026-09-18. Šaltinių numeriai naudojami 2-7 skyriuose. DOI nuoroda pati savaime nėra pilno straipsnio perskaitymo įrodymas.')
refs=[
('[1] Sakar, C.; Kastro, Y. (2018). Online Shoppers Purchasing Intention Dataset. UCI. DOI: 10.24432/C5F88Q.','https://doi.org/10.24432/C5F88Q'),
('[2] scikit-learn autoriai. Linear Models: Logistic regression. Versija 1.8.','https://scikit-learn.org/1.8/modules/linear_model.html#logistic-regression'),
('[3] Breiman, L. (2001). Random Forests. Machine Learning, 45, 5-32. DOI: 10.1023/A:1010933404324.','https://doi.org/10.1023/A:1010933404324'),
('Breiman straipsnio autoriaus PDF (peržiūrėtas).','https://www.stat.berkeley.edu/~breiman/randomforest2001.pdf'),
('[4] scikit-learn autoriai. RandomForestClassifier, predict_proba. Versija 1.8.','https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.RandomForestClassifier.html'),
('[5] Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. Annals of Statistics, 29(5), 1189-1232. DOI: 10.1214/aos/1013203451.','https://doi.org/10.1214/aos/1013203451'),
('[6] scikit-learn autoriai. Ensembles: Histogram-Based Gradient Boosting. Versija 1.8.','https://scikit-learn.org/1.8/modules/ensemble.html#histogram-based-gradient-boosting'),
('[7] scikit-learn autoriai. average_precision_score. Versija 1.8.','https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.average_precision_score.html'),
]
for title,url in refs:
    pages[-1].append(('small',escape(title)+' <link href="'+url+'" color="#16706b">Atverti šaltinį</link>'))
p('Friedman DOI nukreipia į leidėjo puslapį, tačiau pilnas tekstas šioje prieigoje neperskaitytas. Algoritmo paaiškinimas tikrintas oficialiame šaltinyje [6]; straipsniui nepriskiriamos nepatikrintos pažodinės citatos.')
h('9.1. Atitikties žemėlapis')
table(['Kriterijus','Maks.','Kur įgyvendinta šiame plane'],[
['1.1. Problemos supratimas','0,25','1 ir 8 sk.: neaiškumai, ribos, klaidų kaina.'],
['1.2. Išskaidymas','0,25','2.1 ir 5.2: etapai, išvestys, modulių atsakomybės.'],
['1.3. Suprantamos formuluotės','0,50','1.1 ir 2.1: praktinė prasmė įvairioms rolėms.'],
['2.1. Metodų alternatyvos','0,50','3 sk.: trys mokomi metodai ir paprastas baseline.'],
['2.2. Tinkamumo pagrindimas','1,50','3 ir 9 sk.: ryšys su uždaviniu, pirminiai šaltiniai.'],
['3.1. Pagrindinis pasirinkimas','0,50','4.1: RF ir jo pasirinkimo prioritetai.'],
['3.2. Privalumai prieš alternatyvas','2,50','4.2-4.4: tiesioginis palyginimas, sąlygos, hipotezė.'],
['4.1. Įvestis ir išvestis','0,50','2.2-2.3: visi stulpeliai, tipai ir interpretacija.'],
['4.2. Veiksmų eiliškumas','1,00','5 sk.: devyni žingsniai, skaidymas, parametrai.'],
['4.3. Formulės ir kintamieji','2,50','6-7 sk.: simbolių kilmė, pavyzdys, ryšys su moduliais.'],
['Iš viso','10,00','Atitikties žemėlapis, ne pažadėtas dėstytojo balas.']],[198,42,255])

# Tas pats turinys išsaugomas kaip redaguojamas Markdown.
def plain(t):
    t=t.replace('<br/>','\n\n').replace('<b>','**').replace('</b>','**')
    t=re.sub(r'<link href="([^"]+)" color="[^"]+">([^<]+)</link>',r'[\2](\1)',t)
    return t.replace('&lt;','<').replace('&gt;','>').replace('&amp;','&')
md=['# Kolokviumo įgyvendinimo planas','']
flow=[]
for i,blocks in enumerate(pages):
    if i: flow.append(PageBreak())
    for kind,val in blocks:
        if kind=='table':
            headers,rows,widths=val
            data=[[Paragraph(escape(x),styles['small']) for x in headers]]
            data += [[Paragraph(escape(x),styles['small']) for x in row] for row in rows]
            t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3efef')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),0.6,colors.HexColor('#16706b')),('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#d9e0e5')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            flow.extend([t,Spacer(1,8)])
            md += ['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']
            md += ['| '+' | '.join(row)+' |' for row in rows];md.append('')
        else:
            flow.append(Paragraph(val,styles[kind]));md.extend([('## ' if kind=='title' else '### ' if kind=='h' else '')+plain(val),''])
(ROOT/'docs/KOLOKVIUMO_PLANAS.md').write_text('\n'.join(md))
def footer(c,doc):
    c.setStrokeColor(colors.HexColor('#16706b'));c.line(50,802,545,802)
    c.setFont('D',8);c.setFillColor(colors.HexColor('#536477'))
    c.drawString(50,813,'IS-EGZ-KL  /  KOLOKVIUMO PLANAS')
    c.drawString(50,28,'Andrej Kondratjev · DISfm-26 · 2026-09-18')
    c.drawRightString(545,28,str(doc.page))
path=ROOT/'docs/KOLOKVIUMO_PLANAS.pdf'
SimpleDocTemplate(str(path),pagesize=(595.28,841.89),rightMargin=50,leftMargin=50,topMargin=54,bottomMargin=48,title='Kolokviumo įgyvendinimo planas - pirkimo ketinimo tyrimas',author='Andrej Kondratjev').build(flow,onFirstPage=footer,onLaterPages=footer)
print(path)
