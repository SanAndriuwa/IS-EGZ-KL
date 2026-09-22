"""Atkuria kolokviumo Markdown ir PDF iš vieno turinio šaltinio.
Paleidimas projekto kataloge: python scripts/build_colloquium_pdf.py
PDF generavimui reikia reportlab, PyMuPDF ir pdflatex (standalone, amsmath,
amssymb); tai dokumento, ne ML eksperimento priklausomybės.
"""
from pathlib import Path
import matplotlib
import subprocess
import hashlib
import fitz
import re
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONT = Path(matplotlib.get_data_path()) / 'fonts' / 'ttf'
for name, file in [('TNR','DejaVuSerif.ttf'),
                   ('TNRB','DejaVuSerif-Bold.ttf'),
                   ('TNRI','DejaVuSerif-Italic.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
pdfmetrics.registerFontFamily('TNR',normal='TNR',bold='TNRB',italic='TNRI',boldItalic='TNRB')
styles = {
 'title': ParagraphStyle('title',fontName='TNRB',fontSize=14,leading=18,textColor=colors.black,spaceBefore=14,spaceAfter=10,keepWithNext=True),
 'h': ParagraphStyle('h',fontName='TNRB',fontSize=12,leading=16,spaceBefore=11,spaceAfter=6,textColor=colors.black,keepWithNext=True),
 'p': ParagraphStyle('p',fontName='TNR',fontSize=10.5,leading=15.75,spaceAfter=7,alignment=4),
 'small': ParagraphStyle('small',fontName='TNR',fontSize=8.5,leading=11.5,spaceAfter=4),
 'eq': ParagraphStyle('eq',fontName='TNR',fontSize=11,leading=17,spaceBefore=5,spaceAfter=7,leftIndent=12,textColor=colors.black),
 'caption': ParagraphStyle('caption',fontName='TNRB',fontSize=10,leading=13,spaceBefore=4,spaceAfter=8,alignment=1),
}
pages=[]
def page(title):
    pages.append([('title',title)])
def p(t): pages[-1].append(('p',t))
def h(t): pages[-1].append(('h',t))
def eq(latex):
    # LaTeX šaltinis bendras PDF ir GitHub Markdown formulėms.
    pages[-1].append(('eq', latex))
def diagram(title):
    pages[-1].append(('diagram', title))
def table(headers,rows,widths): pages[-1].append(('table',(headers,rows,widths)))

page('1. Problema ir sprendimo paskirtis')
p('<b>Elektroninės parduotuvės pirkimo ketinimo tyrimo įgyvendinimo planas</b><br/>Andrej Kondratjev | DISfm-26 | Intelektualiosios sistemos | 2026-09-18')
h('Įžanga')
p('Šiame darbe pateikiamas elektroninės parduotuvės lankytojų pirkimo ketinimo tyrimo įgyvendinimo planas. Pirmiausia apibrėžiama problema, praktinė sprendimo vertė ir naudojami naršymo sesijų duomenys. Toliau palyginami galimi klasifikavimo metodai, pagrindžiamas atsitiktinio miško pasirinkimas ir suformuluojama tikrinama hipotezė. Aprašomi duomenų paruošimo, modelių mokymo, vertinimo ir naudojimo etapai, pagrindinės formulės bei planuojami programos moduliai. Taip pat aptariami tyrimo apribojimai ir AI naudojimo bei jo pasiūlymų tikrinimo tvarka. Dokumente pateikiamas darbų planas, o ne galutiniai eksperimento rezultatai.')
h('1.1. Problema, techninis uždavinys ir vertė')
p('Elektroninė parduotuvė kaupia duomenis apie lankytojų naršymo sesijas, tačiau vien aplankytų puslapių skaičiaus ar naršymo trukmės nepakanka pirkimo tikimybei įvertinti. Pagal ankstesnių sesijų duomenis siekiama nustatyti, kokie lankytojų elgsenos požymių deriniai yra susiję su pirkimu, ir sukurti modelį šiai tikimybei įvertinti.')
p('<b>Techninis uždavinys:</b> dvejetainis klasifikavimas (angl. <i>binary classification</i>), taikant prižiūrimąjį mokymąsi (angl. <i>supervised learning</i>). Iš vienos sesijos požymių x apskaičiuoti pirkimo tikimybės įvertį p(x) ir klasę: 1 – sesija priskiriama pirkimo klasei, 0 – nepirkimo klasei. Mokymui pateikiamas žinomas atsakymas Revenue; prognozuojant jo nereikia. Kadangi naudojamos užbaigtų sesijų suvestinės, tai nėra patvirtinta prognozė dar vykstant naršymui.')
p('<b>Praktinė vertė:</b> sesijų rangavimas galėtų padėti planuoti konsultantų dėmesį ir analizuoti pirkimo elgseną. Projektų vadovui rezultatas būtų patikrinamas prototipas; finansininkui - klaidingų signalų ir praleistų pirkėjų skaičiai; vadybininkui - prioritetų sąrašas; personalo vadybininkui - informacija galimam konsultantų apkrovos planavimui. Darbuotojų vertinimas nėra šio modelio paskirtis.')
h('1.2. Neakivaizdžios problemos dalys')
table(['Neaiškumas','Sprendimas plane'],[
['Kada žinomi požymiai?','CSV yra sesijos suvestinė. Tiriamas klasifikavimas pagal sukauptus duomenis (angl. <i>offline classification</i>); realaus laiko prognozė neįrodoma. PageValues pagrindiniame modelyje nenaudojamas.'],
['Kuris metodas tinkamiausias?','Tiesinį modelį ir du medžių ansamblius lyginti tomis pačiomis imtimis bei metrikomis.'],
['Mažuma sesijų baigiasi pirkimu','Vien bendro klasifikavimo tikslumo (angl. <i>accuracy</i>) nepakanka. Vertinti AP, teigiamų prognozių tikslumą, jautrumą ir klaidų skaičius (7.1 skyrius).'],
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
p('Naudojamas UCI Online Shoppers Purchasing Intention Dataset: 12 330 sesijų, 17 pradinių požymių ir tikslas Revenue (Sakar &amp; Kastro, 2018). Modeliui atrenkama 15 požymių. Viena CSV eilutė - viena sesija; į modelį siunčiama požymių lentelė, o ne svetainės vaizdas ar tekstas.')
p('Su rinkiniu susijusiame Sakar ir kt. (2019) tyrime pirkimo ketinimas vertinamas pagal apibendrintus puslapių peržiūrų, sesijos ir lankytojo duomenis. Leidėjo pateiktoje santraukoje aprašytas RF, SVM ir daugiasluoksnio perceptrono palyginimas; tame eksperimente perceptronas pasiekė geresnius accuracy ir F1 rezultatus. Šaltinis pagrindžia uždavinio aktualumą ir RF taikymo galimybę, bet ne RF pranašumą. Šio plano požymiai, skaidymas ir vertinimas skiriasi, todėl paskelbtų rezultatų tiesiogiai neperkeliame. Tikrinta santrauka, o ne visas straipsnis.')
p('<b>9 skaitiniai:</b> Administrative, Administrative_Duration, Informational, Informational_Duration, ProductRelated, ProductRelated_Duration, BounceRates, ExitRates, SpecialDay. Pirmieji trys pavadinimų tipai žymi puslapių kiekius, jų Duration - trukmes sekundėmis; paskutiniai trys rodikliai yra intervale [0; 1].')
p('<b>6 kategoriniai:</b> OperatingSystems, Browser, Region, TrafficType, VisitorType, Weekend. Skaitiniai kategorijų kodai laikomi pavadinimais, ne dydžiais. Month naudojamas tik skaidymui. PageValues naudojamas tik atskirame požymio įtakos bandyme. Revenue: False → 0, True → 1.')
h('2.3. Įvesties ir išvesties sutartis')
p('Mokymo CSV turi požymius, Month ir Revenue. Naujam prognozių CSV reikia visų pasirinkto modelio požymių stulpelių; Revenue ir Month nereikalingi. Papildomi stulpeliai ignoruojami. Tuščias langelis užpildomas, bet visai nesantis privalomas stulpelis yra klaida. Neigiami ar begaliniai skaitiniai dydžiai bei dažniai virš 1 atmetami.')
p('Išvestis: row - įvesties eilutės numeris nuo 0; purchase_probability - modelio įvertis [0; 1]; prediction - 0 arba 1 pagal slenkstį τ. Pavyzdžiui, p = 0,30 ir τ = 0,20 duoda klasę 1. Tai iliustracija, ne tyrimo rezultatas; 0,30 nėra pirkimo garantija.')

page('3. Metodų alternatyvos ir šaltiniai')
p('Intelektualieji metodai taikomi pirkimo klasifikavimo uždaviniui. CSV gavimui ar failų įrašymui dirbtinio intelekto nereikia. Nagrinėjami <b>trys mokomi metodai ir viena paprasta atskaita</b>.')
h('3.1. Paprasta atskaita: mokymo imties pirkimų dažnis')
p('Paprasta atskaita (angl. <i>baseline</i>) kiekvienai sesijai grąžina tą pačią mokymo imties pirkimų dalį. Ji leidžia patikrinti, ar modelis panaudoja sesijos požymius geriau negu vien bendrą pirkimų dažnį. Šis metodas sesijų neranguoja; formulė pateikta 6 skyriuje. Tai aritmetinė atskaita, ne pagrindinis intelektualusis metodas.')
h('3.2. Logistinė regresija - stipresnė atskaita')
p('Logistinė regresija (angl. <i>logistic regression</i>) nustato skaitinių ir užkoduotų kategorinių požymių svorius, o sigmoidės funkcija paverčia jų svertinę sumą pirkimo tikimybės įverčiu (scikit-learn developers, n.d.-d). Metodas tinka dvejetainiam tikslui ir lenteliniams duomenims. Šiame plane jis naudojamas kaip palyginti lengvai paaiškinama atskaita, padedanti patikrinti, ar sudėtingesnio modelio apskritai reikia.')
p('Riba: be papildomų sąveikų požymių logaritminis šansų santykis yra tiesinis. Pavyzdžiui, tas pats naršymo laikas skirtingai produktų peržiūrų grupei gali turėti kitą reikšmę; ši sąveika automatiškai neįtraukiama. Šaltinis pagrindžia algoritmo formą, bet ne jo būsimą tikslumą šiame rinkinyje.')
h('3.3. Atsitiktinis miškas - pagrindinis metodas')
p('Atsitiktinis miškas (angl. <i>random forest</i>, RF) sujungia daugelio sprendimų medžių prognozes. Medžių sąlygų deriniai leidžia aprašyti netiesinius ryšius ir požymių sąveikas. Mokymo eilučių atranka su grąžinimu (angl. <i>bootstrap sampling</i>) ir atsitiktiniai požymių poaibiai padeda sudaryti skirtingus medžius (Breiman, 2001). Tai prasminga sesijų lentelei, kur puslapių skaičiaus, naršymo trukmės ir lankytojo tipo sąveikos iš anksto nežinomos.')
p('Breiman (2001) pagrindžia miško konstrukciją; konkreti scikit-learn realizacija tikimybes skaičiuoja kaip medžių lapų tikimybių vidurkį (scikit-learn developers, n.d.-f). Ansamblį sunkiau paaiškinti negu regresijos svorius, o pasikeitusi lankytojų elgsena gali sumažinti išmoktų taisyklių naudą.')
h('3.4. Histograminis gradientinis stiprinimas')
p('Histograminis gradientinis stiprinimas (angl. <i>histogram-based gradient boosting</i>) nuosekliai prideda medžius, siekdamas mažinti nuostolio funkcijos reikšmę. Jis leidžia aprašyti netiesinius ryšius ir yra alternatyva tam pačiam dvejetainio klasifikavimo uždaviniui (scikit-learn developers, n.d.-b).')
p('Friedman (2001) yra bendro gradientinio stiprinimo metodo pirminis šaltinis. Jo pilnas tekstas šios patikros metu nebuvo prieinamas, todėl konkretaus mechanizmo paaiškinimas ir histograminės realizacijos savybės šiame plane remiami oficialia bibliotekos dokumentacija (scikit-learn developers, n.d.-b, n.d.-c). Reikia atsižvelgti į mokymosi žingsnio, iteracijų skaičiaus ir medžių sudėtingumo sąveiką; tai savaime nereiškia, kad metodas blogesnis už mišką.')
h('3.5. Pagrindimo ribos')
p('Duomenų šaltinis (Sakar &amp; Kastro, 2018) patvirtina klasifikavimo uždavinį ir įvesčių pobūdį. Pirminiai straipsniai ir bibliotekos dokumentacija pagrindžia mechanizmus, o jų pritaikymas šiai schemai yra argumentuota projektavimo išvada. Nei pirminis straipsnis, nei algoritmo populiarumas negarantuoja pranašumo šiame eksperimente.')

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
eq('\\Delta\\mathrm{AP}=\\mathrm{AP}_{\\mathrm{RF}}-\\mathrm{AP}_{\\mathrm{LR}},\\qquad \\Delta\\mathrm{AP}\\geq 0{,}02.')
p('(1) formulėje 0,02 reiškia absoliutų AP skirtumą, arba 2 procentinius punktus. Ši riba pasirinkta tam, kad labai maži skirtumai, pavyzdžiui, 0,001–0,003, nebūtų laikomi praktiškai svarbiu modelio pranašumu, nes jie gali atsirasti dėl konkrečios testavimo imties atsitiktinumo. Tai iš anksto nustatytas preliminarus praktinio pagerėjimo kriterijus, o ne iš literatūros gautas universalus dydis ar garantuotas efektas. Jei būtų žinomos klaidingo signalo ir praleisto pirkimo kainos, ribą reikėtų grįsti jomis; šiame plane tokios piniginės informacijos nėra. Todėl papildomai vertinamas 95 % porinis bootstrap intervalas ir galima jautrumo analizė su 0,01 bei 0,05 ribomis. Abu modeliai gauna tas pačias imtis ir tą patį parinkimo kriterijų; kiekvienam skiriami du kandidatų mokymai.')
h('4.4. Kaip bus daroma išvada?')
p('Jei ΔAP &lt; 0,02, numatytas pagerėjimas šiame teste nepasitvirtins. Jei ΔAP ≥ 0,02, kriterijus bus pasiektas tik šiame teste; papildomai vertinamas 95 % porinio bootstrap intervalas. Jei intervalas apima nulį, tvirto teiginio apie persvarą nedarysime. Nepasiekus prasmingos persvaros, paprastesnė regresija liks pagrįsta praktinė alternatyva. Testo rezultatu nebus perrašomas pradinis parinkimo planas.')

page('5. Algoritmo eiga ir eksperimento taisyklės')
h('5.1. Skaidymas ir duomenų paruošimas')
p('Mokymo imčiai (angl. <i>training set</i>; kode train) priskiriami Feb, Mar, May, June, Jul, Aug mėnesiai; parinkimo imčiai (angl. <i>validation set</i>; kode validation) – Sep ir Oct; galutinei testavimo imčiai (angl. <i>test set</i>; kode test) – Nov ir Dec. Jan ir Apr įrašų rinkinyje nėra. Month nėra modelio požymis. Imtys turi nesikirsti, apimti visas eilutes ir turėti abi klases. Skaidoma pagal mėnesio numerį, nes tikslių laiko žymų nėra.')
p('Atsitiktinių skaičių generatoriaus pradinė reikšmė (angl. <i>random seed</i>) nustatoma lygi 42. Ji naudojama atsitiktinėms operacijoms, pavyzdžiui, miško mokymo eilučių atrankai ir trūkstamų reikšmių bandymui. Ta pati pradinė reikšmė padeda pakartoti šias operacijas toje pačioje aplinkoje, su tais pačiais duomenimis ir kodu. Skaičius 42 pasirinktas sutartinai, o ne siekiant geresnės prognozės. Skaidymas pagal mėnesius nėra atsitiktinis ir nuo šios reikšmės nepriklauso.')
p('Duomenų paruošimo (angl. <i>preprocessing</i>) parametrai nustatomi tik mokymo imtyje: skaitinių požymių medianos, vidurkiai ir skalės, kategorinių požymių modos bei kategorijų aibė. Kategorijos paverčiamos atskirais 0 ir 1 indikatoriais (angl. <i>one-hot encoding</i>). Parinkimo, testavimo ir naujos sesijos tik transformuojamos. Nežinoma kategorija koduojama nuliais savo indikatorių grupėje. Standartizavimas naudingas regresijai; medžiams nebūtinas, bet paruošimo veiksmai visiems modeliams vienodi. Sintetiniai mažumos klasės pavyzdžiai nekuriami, klasių svoriai nenaudojami.')
p('Mokymo ir testavimo duomenys turi išlikti atskirti ir paruošimo metu. Kapoor ir Narayanan (2022, preprintas, 2.4 skyrius, L1.2) visos imties naudojimą transformacijoms nustatyti išskiria kaip informacijos nutekėjimo (angl. <i>data leakage</i>) atvejį. Todėl medianos ir standartizavimo parametrai šiame plane neskaičiuojami iš visos lentelės. Šaltinis pagrindžia šį principą, bet nenustato konkretaus mūsų skaidymo pagal mėnesius.')
h('5.2. Veiksmų seka programuotojui')
p('Įgyvendinimui naudojama Python biblioteka scikit-learn. Pedregosa ir kt. (2011) aprašo jos bendrą paskirtį, vienodą programavimo sąsają ir dėmesį dokumentacijai bei kodo kokybei. Tai pagrindžia bendros bibliotekos pasirinkimą aiškiam modelių palyginimui. Dabartinės 1.8 versijos parametrų reikšmės tikrinamos atskiruose dokumentacijos puslapiuose, nes 2011 m. straipsnis jų neaprašo.')
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
diagram('Sprendimo eiga')
h('5.3. Modelių parametrų variantai ir jų pasirinkimo pagrindimas')
p('Kandidatu vadinamas modelis su konkrečiu parametrų rinkiniu. Iš anksto nustatytas variantų sąrašas (angl. <i>hyperparameter grid</i>) riboja bandymų skaičių ir leidžia atkurti palyginimą. Toliau paaiškinama, kodėl pasirinktos būtent šios reikšmės. Tai riboto mokomojo eksperimento nustatymai, o ne literatūroje įrodytos optimalios reikšmės šiam duomenų rinkiniui.')
p('<b>Paprasta atskaita – 1 kandidatas.</b> Pirkimų dažnis apskaičiuojamas iš mokymo duomenų, todėl papildomų derinamų parametrų nėra.')
p('<b>Logistinė regresija – 2 kandidatai.</b> C = 0,1 ir C = 1,0 leidžia palyginti dešimt kartų besiskiriantį reguliavimo stiprumą: mažesnis C labiau riboja svorius. Taip tikrinama, ar naudingesnis stipriau apribotas modelis. max_iter = 2000 yra optimizavimo iteracijų viršutinė riba, paliekanti vietos konvergencijai, o ne reikalavimas visada vykdyti 2000 iteracijų. Jei gaunamas įspėjimas apie nekonvergavimą, jis registruojamas (scikit-learn developers, n.d.-e).')
p('<b>Atsitiktinis miškas – 2 kandidatai.</b> Abiem parenkama po 200 medžių: tai praktinis kompromisas tarp prognozių vidurkinimo ir skaičiavimo biudžeto, kurio pakankamumas dar neįrodytas. min_samples_leaf = 5 ir 20 leidžia palyginti smulkesnes ir stambesnes sesijų grupes lapuose; didesnė reikšmė riboja pernelyg detalias taisykles. max_features = sqrt nustato viename skaidyme svarstomų požymių skaičių pagal transformuotų požymių skaičiaus kvadratinę šaknį, kad medžiai būtų įvairesni. n_jobs = 1 išjungia miško darbų lygiagretinimą. Kiti nustatymai – scikit-learn 1.8 numatytieji, įskaitant atranką su grąžinimu ir Gini kriterijų (scikit-learn developers, n.d.-f).')
p('<b>Histograminis gradientinis stiprinimas – 2 kandidatai.</b> max_leaf_nodes = 7 ir 15 leidžia palyginti du medžių sudėtingumo lygius. max_iter = 150 ir learning_rate = 0,05 parenkami kaip bendras riboto biudžeto nustatymas: mažesnės kiekvieno medžio pataisos derinamos su fiksuotu iteracijų skaičiumi. Tai nėra šių reikšmių optimalumo įrodymas. early_stopping = False išjungia ankstyvą stabdymą, kad nebūtų automatiškai kuriama papildoma vidinė parinkimo imtis ir visi kandidatai būtų mokomi pagal tą pačią taisyklę (scikit-learn developers, n.d.-c).')
p('Kiekvienam mokomam metodui skiriami du kandidatų mokymai. Tai vienodas bandymų skaičius, bet nebūtinai vienodas vykdymo laikas ar išsami geriausių parametrų paieška. Parametrų paskirtį pagrindžia dokumentacija; konkrečių skaičių pasirinkimas yra šio plano projektinis sprendimas. Pagal testavimo rezultatus šie nustatymai nekeičiami.')

page('6. Formulės: nuo įvesties iki sprendimo')
p('Pasirinkto RF prognozės kelias: sesijos x reikšmės → paruoštas vektorius z → kiekvieno medžio lapas → lapo pirkimų dalis → medžių vidurkis → sprendimas pagal slenkstį. Indeksas i žymi sesiją, j - skaitinį požymį, b - medį.')
h('6.1. Skaitinių duomenų paruošimas')
eq("x'_{ij}=\\begin{cases}x_{ij},&\\text{jei reikšmė žinoma},\\\\ m_j,&\\text{jei reikšmės trūksta}.\\end{cases}")
eq("z_{ij}=\\frac{x'_{ij}-\\mu_j}{s_j}.")
p('(2)-(3) formulėse mⱼ - j požymio žinomų train reikšmių mediana; μⱼ ir sⱼ - jau užpildyto train stulpelio vidurkis ir standartinis nuokrypis. Jei stulpelis pastovus, StandardScaler naudoja skalę 1. Validation ir test reikšmės nekeičia šių parametrų. Kategorijai c kuriamas indikatorius I(x = c), lygus 1 sutapus kategorijai ir 0 nesutapus. Gautos skiltys sujungiamos į z. Modulis: preprocessing.py.')
h('6.2. Vieno medžio taisyklė ir tikimybė')
eq('\\text{kitas mazgas}=\\begin{cases}\\text{kairysis vaikas},&z_j\\leq t,\\\\ \\text{dešinysis vaikas},&z_j>t.\\end{cases}')
eq('p_b(z)=\\frac{n_{b,1}\\!\\left(L_b(z)\\right)}{n_b\\!\\left(L_b(z)\\right)}.')
p('(4)-(5) formulėse j ir t - mokymo metu parinkto mazgo požymio indeksas ir slenkstis. Kartojame sąlygą iki lapo L<sub>b</sub>(z). n<sub>b,1</sub> - pirkusių mokymo pavyzdžių svoris tame lape; n<sub>b</sub> - visų mokymo pavyzdžių svoris tame lape. Bootstrap pasikartojimai skaičiuojami su jų kartotinumu. Tai mokymo lapo statistika, ne naujos sesijos Revenue. Naujos sesijos tikras atsakymas prognozei nežinomas.')
h('6.3. Miško išvestis ir dvejetainis sprendimas')
eq('\\hat p_{\\mathrm{RF}}(x)=\\frac{1}{B}\\sum_{b=1}^{B}p_b(z),\\qquad B=200.')
eq('\\hat y=\\begin{cases}1,&\\hat p_{\\mathrm{RF}}(x)\\geq\\tau,\\\\ 0,&\\hat p_{\\mathrm{RF}}(x)<\\tau.\\end{cases}')
p('(6)-(7) formulėse B – medžių skaičius; τ – tik parinkimo imtyje parinktas sprendimo slenkstis (angl. <i>decision threshold</i>). scikit-learn RF vidurkina tikimybes, ne vien medžių 0/1 balsus (scikit-learn developers, n.d.-f). models.py funkcija forest_probability_by_formula apskaičiuoja atskirų medžių predict_proba rezultatų vidurkį; analysis.py jį palygina su viso miško predict_proba. Ši patikra tikrina vidurkinimą, bet nepriklausomai neatkuria bibliotekos medžio apėjimo. Leistina absoliuti skaitinė paklaida: 10⁻¹², be santykinės tolerancijos.')
p('<b>Rankinis pavyzdys, ne rezultatas:</b> jei trijų medžių lapų tikimybės yra 0,2; 0,6; 0,4, jų vidurkis yra 0,4. Su τ = 0,3 prognozė lygi 1. Net jei tik vienas medis viršytų 0,5, sprendimas priklauso nuo tikimybių vidurkio ir pasirinkto τ.')
h('6.4. Atskaitų ir gradientinio stiprinimo išvestys')
eq('\\hat p_0=\\frac{1}{N}\\sum_{i=1}^{N}y_i.')
eq('\\hat p_{\\mathrm{LR}}(z)=\\frac{1}{1+\\exp\\!\\left[-(w^{\\mathsf T}z+a)\\right]}.')
p('(8)-(9) formulėse N - train sesijų skaičius; yᵢ - jų Revenue (0/1); p₀ - pastovi pirkimų dalis. w - regresijos išmokti svoriai, a - jos poslinkis; abu gaunami tik iš train. Modulis: models.py. Mokymo optimizavimo išvedimai neprivalomi: mokymą atliks biblioteka, o šiame plane tiksliai aprašyta prognozės taisyklė.')
eq('\\hat p_{\\mathrm{GB}}(x)=\\sigma\\!\\left(F_0+\\eta\\sum_{m=1}^{M}h_m(z)\\right).')
p('(10) formulėje F₀ – mokymo metu nustatytas pradinis įvertis logaritminių šansų skalėje, hₘ(z) – m-ojo medžio indėlis prieš žingsnio koeficientą, M = 150 – iteracijų skaičius, η = 0,05 – mokymosi žingsnis, o σ(u) = 1 / (1 + exp(−u)). Tai dvejetainio histograminio gradientinio stiprinimo prognozės principas, ne rankinis bibliotekos mokymo algoritmo perrašymas: medžiai paeiliui taiso bendrą įvertį, jų tikimybės nevidurkinamos. Bibliotekos numatytasis log_loss naudoja sigmoidę (scikit-learn developers, n.d.-b, n.d.-c). Išvestį apskaičiuoja models.py sukurto HistGradientBoostingClassifier predict_proba.')
h('6.5. Simbolių ir programos realizacijos atitiktis')
table(['Formulės simbolis','Reikšmė plane','Kur realizuojama'],[
['xᵢⱼ, yᵢ','i-osios sesijos požymis ir Revenue tikslas.','data.py: duomenų skaitymas ir tikrinimas'],
['mⱼ, μⱼ, sⱼ','Tik train duomenyse išmokta mediana, vidurkis ir skalė.','preprocessing.py: `SimpleImputer`, `StandardScaler`'],
['z','Po paruošimo gautas skaitinių ir one-hot požymių vektorius.','preprocessing.py: `ColumnTransformer`'],
['Lᵦ(z), nᵦ,₁, nᵦ','b-ojo medžio pasiektas lapas ir mokymo pavyzdžių svoriai.','scikit-learn medžio predict_proba; models.py vidurkina medžių tikimybes'],
['B, p̂RF, τ','200 medžių, vidutinė tikimybė ir validation parinktas slenkstis.','models.py, training.py, evaluation.py'],
['F₀, hₘ, η, M, p̂GB','Gradientinio stiprinimo pradinis įvertis, medžių indėliai, žingsnis ir tikimybė.','models.py: HistGradientBoostingClassifier; predict_proba'],
['P, R, F₂, AP, Brier','Testo metrikos iš `TP`, `FP`, `FN` ir tikimybių.','evaluation.py: `metrics`'],
],[126,220,175])
p('Lentelė nurodo, kuri programos dalis atlieka formulėje aprašytą veiksmą. Formulės raidė nebūtinai sutampa su kintamojo vardu kode. Tikrinama, iš kur gaunami duomenys, kaip jie transformuojami ir kaip apskaičiuojamas rezultatas. Pavyzdžiui, medžių tikimybių vidurkis turi sutapti su viso miško grąžinama tikimybe. Keičiant skaičiavimo logiką atnaujinamas aprašas ir AI žurnalas.')

page('7. Vertinimas, papildomi bandymai ir biudžetas')
h('7.1. Metrikos ir jų interpretacija')
eq('P=\\frac{\\mathrm{TP}}{\\mathrm{TP}+\\mathrm{FP}}.')
eq('R=\\frac{\\mathrm{TP}}{\\mathrm{TP}+\\mathrm{FN}}.')
eq('F_2=\\frac{5PR}{4P+R}.')
p('(11)-(13) formulėse TP – teisingai aptikti pirkimai; FP – prognozuoti pirkimai, kurių nebuvo; FN – praleisti pirkimai; TN – teisingai atmesti nepirkimai. P – teigiamų prognozių tikslumas (angl. <i>precision</i>), R – jautrumas (angl. <i>recall</i>), rodantis aptiktų pirkimų dalį. Kai vardiklis nulis, atitinkama metrika lygi 0. F2 daugiau svarbos teikia jautrumui; tai pasirinktas mokomasis prioritetas, ne finansinis optimumas.')
eq('\\mathrm{AP}=\\sum_{k}(R_k-R_{k-1})P_k.')
eq('\\mathrm{Brier}=\\frac{1}{n}\\sum_{i=1}^{n}(p_i-y_i)^2.')
p('(14) formulėje AP (angl. <i>average precision</i>) apskaičiuojamas mažinant sprendimo slenkstį ir didėjant jautrumui; k žymi kreivės tašką, R₀ = 0. Naudojama scikit-learn average_precision_score realizacija (scikit-learn developers, n.d.-a), o ne trapecinis plotas po precision–recall kreive. (15) formulėje n – vertinamos imties dydis, pᵢ – modelio tikimybė, yᵢ – tikras atsakymas. Didesnė AP ir mažesnis Brier rodiklis yra geriau. AP nėra procentinis klasifikavimo tikslumas.')
p('Papildomai pateikti trapecinį PR-AUC, log loss, painiavos matricą, PR kreivę ir kalibracijos kreivę su 8 vienodo dažnio grupėmis. Kalibracijos grafikas tik vertins tikimybes; papildomas kalibratorius nebus mokomas. Modulis: evaluation.py; grafikai: plots.py.')
p('Saito ir Rehmsmeier (2015) parodo, kodėl nesubalansuotoms klasėms svarbu vertinti teigiamų prognozių tikslumo ir jautrumo santykį: vien accuracy ar ROC vaizdas gali nuslėpti silpną teigiamų prognozių patikimumą. Tai pagrindžia PR kreivės įtraukimą į šį planą. Straipsnis nepagrindžia mūsų hipotezės 0,02 ribos, o konkreti AP skaičiavimo taisyklė remiama scikit-learn dokumentacija.')
p('Geras klasių atskyrimas dar nereiškia, kad modelio tikimybės gerai kalibruotos (Niculescu-Mizil &amp; Caruana, 2005). Todėl kartu su AP vertinamas Brier rodiklis ir kalibracijos kreivė (angl. <i>reliability diagram</i>), lyginanti prognozuotas tikimybes su stebimu pirkimų dažniu. Šaltinis pagrindžia atskiro tikimybių vertinimo poreikį; pasirinktos 8 vienodo dažnio grupės yra šio plano nustatymas, o ne straipsnio taisyklė.')
h('7.2. Iš anksto numatyta analizė')
table(['Bandymas','Tiksli taisyklė ir tikslas'],[
['Požymio įtaka (angl. <i>ablation study</i>)','Pakartoti RF su PageValues, paliekant tas pačias imtis ir du lapo dydžio kandidatus. Palyginti su pagrindiniu RF be šio požymio. Pagerėjimas neįrodys prieinamumo iki pirkimo.'],
['Atsparumas','Generatoriaus pradinė reikšmė – 42; nepriklausomai paslėpti apie 10 % testo skaitinių langelių reikšmių. Keturiems pagrindiniams metodams tos pačios paslėptos reikšmės. Modelių, medianų ir slenksčių nekeisti.'],
['Klaidų analizė','RF: 5 didžiausios tikimybės FP ir 5 mažiausios tikimybės FN (arba visi, jei mažiau). Papildomos suvestinės pagal Month ir VisitorType.'],
['Neapibrėžtumas','500 porinio stratifikuoto bootstrap kartojimų: su grąžinimu rinkti pirkimų ir nepirkimų eilutes, abiem modeliams tas pačias. ΔAP 2,5 ir 97,5 procentiliai sudaro sąlyginį 95 % intervalą.']],[104,391])
h('7.3. Skaičiavimo ir rezultatų planas')
p('Iš viso 9 kandidatų mokymai: 1 + 2 + 2 + 2 pagrindiniams metodams ir 2 RF su PageValues. CPU, vienas srautas, orientacinis biudžetas - 10 min. ir 4 GB RAM. Vykdymo laikas bus matuojamas, RAM - tik planavimo įvertis, ne išmatuotas ar priverstinai ribojamas dydis. Viršijus biudžetą tai pažymėti; slaptai keisti tinklelį pagal testą negalima.')
p('Numatomos išvestys: imčių sudėtis, kandidatų AP parinkimo imtyje, testavimo metrikos ir sesijų tikimybės, klaidų bei pogrupių lentelės ir grafikai. Taip pat išsaugoma duomenų paruošimo ir klasifikavimo veiksmų seka (angl. <i>pipeline</i>), kad ją būtų galima taikyti naujiems duomenims. Eksperimento vykdymo apraše (angl. <i>run manifest</i>; failas manifest.json) įrašomos bibliotekų versijos, atsitiktinių skaičių generatoriaus pradinė reikšmė ir kodo failų SHA256 kontrolinės sumos. Ši informacija padeda nustatyti, kokiu kodu ir kokioje aplinkoje atliktas bandymas.')

page('8. Rizikos, AI naudojimas ir priėmimo patikros')
h('8.1. Grėsmės išvadų galiojimui')
p('Per didelis prisitaikymas galimas ne tik mokant modelį, bet ir renkantis jo parametrus: parinkimo kriterijus apskaičiuojamas iš baigtinės imties ir pats turi atsitiktinę paklaidą (Cawley &amp; Talbot, 2010). Dėl to šiame plane ribojamas kandidatų skaičius, o galutinė testavimo imtis nenaudojama jų parinkimui. Šaltinis pagrindžia riziką ir nepriklausomo vertinimo poreikį, bet negarantuoja, kad du kandidatai ją visiškai pašalina.')
table(['Grėsmė','Valdymas ir liekanti riba'],[
['Informacijos nutekėjimas','Revenue ir Month nepatenka į modelį; PageValues tik atskiras bandymas. Vis tiek neįmanoma iš suvestinės įrodyti visų rodiklių prieinamumo iki pirkimo.'],
['Laiko ir parduotuvės poslinkis','Chronologinis skaidymas sumažina atsitiktinio sumaišymo optimizmą. Vieni metai ir viena parduotuvė neleidžia išvados perkelti visur.'],
['Nežinomas sesijų ryšys','UCI aprašo skirtingus naudotojus, bet CSV nėra ID. Teiginio nepriklausomai patikrinti ir grupuoti pagal lankytoją negalėsime.'],
['Validacijos perkrovimas','Ribotas kandidatų tinklas, bet ta pati validation imtis parenka ir modelį, ir slenkstį. Tai likusi optimizmo rizika.'],
['Testo peržiūra','Tai patikslinta projekto plano redakcija, ne nauja išankstinė registracija. Pradinis protokolas išsaugomas. Po testo peržiūros pakeistas variantas būtų tiriamoji analizė; patvirtinimui reikėtų naujo neliečiamo testo.'],
['Klaidos kaina ir kalibracija','F2 nėra finansinio pelno kriterijus. Prieš diegimą reikėtų klaidų kainų, prognozės momento audito ir atskiros tikimybių patikros.']],[122,373])
p('Bootstrap intervalas apibūdina šios testo imties ir šių išmokytų modelių neapibrėžtumą. Jis neapima viso mokymo proceso kintamumo, būsimų sezonų ar kitų parduotuvių. Trūkstamų reikšmių maskavimas neimituoja visų realių gedimų.')
h('8.2. AI naudojimo ir tikrinimo planas')
p('AI bus naudojamas dokumento struktūrai, pradiniam aiškiam kodui, komentarams ir testų idėjoms. AI nepakeis šaltinių skaitymo ar programos vykdymo. AI gali pasiūlyti citatą ar DOI, tačiau autorius privalo atverti pirminį arba oficialų šaltinį, patikrinti metaduomenis ir teiginio atitiktį bei pats patvirtinti galutinę citatą. Kiekvieną reikšmingą pakeitimą, atmestą pasiūlymą ir aptiktą klaidą registruoti AI_ZURNALAS.md.')
table(['Tikrinamas dalykas','Patikros veiksmas'],[
['Citatos','AI parenka kandidatą; autorius atveria autoriaus, leidėjo ar oficialios bibliotekos puslapį ir patikrina autorių, metus, DOI bei teiginio atitiktį. Neprieinamo pilno teksto neskelbti perskaitytu.'],
['Formulės','Autorius patikrina, ar programoje naudojami tie patys dydžiai ir veiksmai kaip formulėse. Vienos sesijos pavyzdį apskaičiuoja ranka; medžių tikimybių vidurkį palygina su miško predict_proba.'],
['Kodas','Testuoti nesikertančias imtis, draudžiamus požymius, tik train išmoktas transformacijas, nežinomas kategorijas ir netinkamą schemą.'],
['Rezultatai','Autorius vykdo eksperimentą ir skaičius ima iš CSV. Tikrina pakartojamumą su ta pačia generatoriaus pradine reikšme, tais pačiais duomenimis, kodu ir aplinka; išsaugo versijas bei kodo sumas.']],[99,396])
p('Kodo autorystė: AI parengė pradinį kodą pagal darbo autoriaus nurodymus ir užduoties reikalavimus, remdamasis bibliotekų dokumentacija. Autorius turi perskaityti modulius, paleisti testus, patikrinti rezultatus, gebėti paaiškinti sprendimus ir pats patvirtinti galutinę redakciją. Tai autoriaus numatyti tikrinimo veiksmai, o ne teiginys, kad jie jau atlikti. AI sugeneruotas tekstas ar kodas negali būti pateikiamas kaip vien autoriaus savarankiškai parašytas darbas.')
p('Priėmimo sąlyga: kitas programuotojas pagal 2, 5-7 skyrius gali įgyvendinti grandinę ir gauti visus numatytus išvesties failus. Teigiamas hipotezės rezultatas nėra darbo priėmimo sąlyga. Studentas turi gebėti paaiškinti įvestį, miško formulę, slenkstį ir skaidymą.')

page('9. Šaltiniai')
refs=[
('Breiman, L. (2001). Random forests. <i>Machine Learning, 45</i>, 5–32. https://doi.org/10.1023/A:1010933404324','https://doi.org/10.1023/A:1010933404324'),
('Cawley, G. C., &amp; Talbot, N. L. C. (2010). On over-fitting in model selection and subsequent selection bias in performance evaluation. <i>Journal of Machine Learning Research, 11</i>, 2079–2107.','https://www.jmlr.org/papers/v11/cawley10a.html'),
('Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. <i>Annals of Statistics, 29</i>(5), 1189–1232. https://doi.org/10.1214/aos/1013203451','https://doi.org/10.1214/aos/1013203451'),
('Kapoor, S., &amp; Narayanan, A. (2022). <i>Leakage and the reproducibility crisis in ML-based science</i> [Preprint, v1]. arXiv. https://doi.org/10.48550/arXiv.2207.07048','https://arxiv.org/abs/2207.07048v1'),
('Niculescu-Mizil, A., &amp; Caruana, R. (2005). Predicting good probabilities with supervised learning. <i>Proceedings of the 22nd International Conference on Machine Learning</i>.','https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf'),
('Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., &amp; Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. <i>Journal of Machine Learning Research, 12</i>, 2825–2830.','https://www.jmlr.org/papers/v12/pedregosa11a.html'),
('Saito, T., &amp; Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. <i>PLOS ONE, 10</i>(3), e0118432. https://doi.org/10.1371/journal.pone.0118432','https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432'),
('Sakar, C., &amp; Kastro, Y. (2018). <i>Online Shoppers Purchasing Intention Dataset</i> [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5F88Q','https://doi.org/10.24432/C5F88Q'),
('Sakar, C. O., Polat, S. O., Katircioglu, M., &amp; Kastro, Y. (2019). Real-time prediction of online shoppers’ purchasing intention using multilayer perceptron and LSTM recurrent neural networks. <i>Neural Computing and Applications, 31</i>, 6893–6908. https://doi.org/10.1007/s00521-018-3523-0','https://link.springer.com/article/10.1007/s00521-018-3523-0'),
('scikit-learn developers. (n.d.-a). <i>average_precision_score</i> (Version 1.8) [Documentation].','https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.average_precision_score.html'),
('scikit-learn developers. (n.d.-b). <i>Ensembles: Histogram-based gradient boosting</i> (Version 1.8) [Documentation].','https://scikit-learn.org/1.8/modules/ensemble.html#histogram-based-gradient-boosting'),
('scikit-learn developers. (n.d.-c). <i>HistGradientBoostingClassifier</i> (Version 1.8) [Documentation].','https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html'),
('scikit-learn developers. (n.d.-d). <i>Linear models: Logistic regression</i> (Version 1.8) [Documentation].','https://scikit-learn.org/1.8/modules/linear_model.html#logistic-regression'),
('scikit-learn developers. (n.d.-e). <i>LogisticRegression</i> (Version 1.8) [Documentation].','https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html'),
('scikit-learn developers. (n.d.-f). <i>RandomForestClassifier</i> (Version 1.8) [Documentation].','https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.RandomForestClassifier.html'),
]
for title,url in refs:
    pages[-1].append(('small',title+' <link href="'+url+'" color="#16706b">Atverti šaltinį</link>'))

# ReportLab rezervuoja vietą ir įrašo numerį. PyMuPDF įterpia LaTeX PDF
# vektorinį turinį į tą vietą, todėl trupmenos ir indeksai neišsilieja priartinus.
EQUATION_POSITIONS = []
class Equation(Flowable):
    def __init__(self, latex, number):
        super().__init__()
        cache = ROOT / 'tmp' / 'equations'
        cache.mkdir(parents=True, exist_ok=True)
        stem = hashlib.sha256(latex.encode()).hexdigest()[:16]
        tex = cache / (stem + '.tex')
        self.pdf = cache / (stem + '.pdf')
        if not self.pdf.exists():
            tex.write_text(r'\documentclass[12pt,border=2pt]{standalone}' + '\n' +
                r'\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}' + '\n' +
                r'\usepackage{amsmath,amssymb}' + '\n' +
                r'\begin{document}$\displaystyle '+latex+r'$\end{document}')
            done = subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',
                '-output-directory',str(cache),str(tex)],capture_output=True,text=True)
            if done.returncode:
                raise RuntimeError(done.stdout[-3000:])
        with fitz.open(self.pdf) as pdf:
            self.natural_width = pdf[0].rect.width
            self.natural_height = pdf[0].rect.height
        self.width = 495
        self.scale = min(1.0, 433 / self.natural_width)
        self.height = self.natural_height*self.scale + 10
        self.number = number
        self.keepWithNext = True
        self.spaceBefore = 2
        self.spaceAfter = 2
    def draw(self):
        w = self.natural_width*self.scale
        h = self.natural_height*self.scale
        x = (self.width-w)/2
        px,py = self.canv.absolutePosition(x,5)
        pageheight = self.canv._pagesize[1]
        EQUATION_POSITIONS.append((self.canv.getPageNumber()-1, str(self.pdf),
            (px,pageheight-py-h,px+w,pageheight-py)))
        self.canv.setFont('TNR',9.5)
        self.canv.setFillColor(colors.black)
        self.canv.drawRightString(self.width,self.height/2-3,'('+str(self.number)+')')

class FlowDiagram(Flowable):
    """Nedidelė vektorinė schema, paaiškinanti 5.2 skyriaus veiksmų seką."""
    def __init__(self, caption):
        super().__init__()
        self.width = 495
        self.height = 94
        self.caption = caption
    def draw(self):
        c = self.canv
        labels = [
            ('1. CSV', 'schema + SHA256'),
            ('2. Paruošimas', 'train / val / test'),
            ('3. Mokymas', 'baseline + modeliai'),
            ('4. Parinkimas', 'AP + slenkstis τ'),
            ('5. Vertinimas', 'testas + prognozė'),
        ]
        box_w, box_h, gap = 88, 42, 12
        y = 37
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.white)
        c.setLineWidth(0.7)
        for i, (head, sub) in enumerate(labels):
            x = i * (box_w + gap)
            c.roundRect(x, y, box_w, box_h, 3, stroke=1, fill=1)
            c.setFillColor(colors.black)
            c.setFont('TNRB', 8.2)
            c.drawCentredString(x + box_w / 2, y + 25, head)
            c.setFont('TNR', 7.2)
            c.drawCentredString(x + box_w / 2, y + 13, sub)
            if i < len(labels) - 1:
                ax = x + box_w + 2
                c.line(ax, y + box_h / 2, ax + gap - 4, y + box_h / 2)
                c.line(ax + gap - 4, y + box_h / 2, ax + gap - 8, y + box_h / 2 + 3)
                c.line(ax + gap - 4, y + box_h / 2, ax + gap - 8, y + box_h / 2 - 3)
            c.setFillColor(colors.white)
        c.setFont('TNRB', 9.5)
        c.setFillColor(colors.black)
        c.drawCentredString(self.width / 2, 16, '1 pav. Sprendimo eiga (parengta su AI pagalba pagal projekto planą)')

# Tas pats turinys išsaugomas kaip redaguojamas Markdown.
def plain(t):
    t=t.replace('<br/>','\n\n').replace('<b>','**').replace('</b>','**')
    t=t.replace('<i>','*').replace('</i>','*')
    t=re.sub(r'<link href="([^"]+)" color="[^"]+">([^<]+)</link>',r'[\2](\1)',t)
    return t.replace('&lt;','<').replace('&gt;','>').replace('&amp;','&')
md=['# Kolokviumo įgyvendinimo planas','']
flow=[]
equation_number=0
for i,blocks in enumerate(pages):
    # Turinys teka nuosekliai; antraštės ir formulės laikomos su paaiškinimais.
    for kind,val in blocks:
        if kind=='table':
            headers,rows,widths=val
            data=[[Paragraph(x,styles['small']) for x in headers]]
            data += [[Paragraph(x,styles['small']) for x in row] for row in rows]
            t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3efef')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),0.6,colors.HexColor('#16706b')),('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#d9e0e5')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            flow.extend([t,Spacer(1,8)])
            md += ['| '+' | '.join(plain(x) for x in headers)+' |','|'+'|'.join(['---']*len(headers))+'|']
            md += ['| '+' | '.join(plain(x) for x in row)+' |' for row in rows];md.append('')
        elif kind=='eq':
            equation_number += 1
            flow.append(Equation(val,equation_number))
            md.extend(['$$',val + r' \tag{' + str(equation_number) + '}', '$$', ''])
        elif kind=='diagram':
            flow.extend([FlowDiagram(val), Spacer(1, 6)])
            md.extend(['```mermaid', 'flowchart LR',
                       'A[CSV schema] --> B[Preprocessing]',
                       'B --> C[Train candidates]',
                       'C --> D[Validation AP and threshold]',
                       'D --> E[Test and prediction]', '```', '',
                       '_1 pav. Sprendimo eiga. Parengta su AI pagalba pagal projekto planą._', ''])
        else:
            flow.append(Paragraph(val,styles[kind]));md.extend([('## ' if kind=='title' else '### ' if kind=='h' else '')+plain(val),''])
(ROOT/'docs/KOLIOKVIUMO_PLANAS.md').write_text('\n'.join(md))
def footer(c,doc):
    c.setFont('TNR',8);c.setFillColor(colors.HexColor('#536477'))
    c.drawString(50,28,'Andrej Kondratjev · DISfm-26 · 2026-09-18')
    c.drawRightString(545,28,str(doc.page))
path=ROOT/'docs/KOLIOKVIUMO_PLANAS.pdf'
SimpleDocTemplate(str(path),pagesize=(595.28,841.89),rightMargin=50,leftMargin=50,topMargin=54,bottomMargin=48,title='Kolokviumo įgyvendinimo planas - pirkimo ketinimo tyrimas',author='Andrej Kondratjev').build(flow,onFirstPage=footer,onLaterPages=footer)
pdf=fitz.open(path)
for page_number,source,rect in EQUATION_POSITIONS:
    with fitz.open(source) as equation_pdf:
        pdf[page_number].show_pdf_page(fitz.Rect(rect),equation_pdf,0)
rendered = path.with_suffix('.rendered.pdf')
pdf.save(rendered,garbage=4,deflate=True)
pdf.close()
rendered.replace(path)
print(path)
