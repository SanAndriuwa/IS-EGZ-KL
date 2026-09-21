"""Sukuria egzamino ataskaitos Markdown, DOCX ir dvi iliustracijas.

Paleisti projekto šaknyje:
    python scripts/build_exam_report.py

PDF generuojamas iš DOCX atskiru render_docx.py žingsniu, kad DOCX ir PDF
turinys bei puslapių maketas sutaptų. Formulės DOCX faile yra redaguojami
Microsoft Office Math (OMML) objektai ir numeruojamos dešinėje.
"""
from __future__ import annotations

from copy import deepcopy
from io import BytesIO
import os
from pathlib import Path
import subprocess
from zipfile import ZipFile

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from lxml import etree
from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Mm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

GITHUB = "https://github.com/SanAndriuwa/IS-EGZ-KL"
ENGLISH_TERMS = ("one-hot encoding", "average precision", "precision", "recall")


def make_figures() -> None:
    """Sukuria proceso schemą ir rezultatų palyginimo diagramą."""
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

    fig, ax = plt.subplots(figsize=(8.8, 5.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")
    nodes = [
        (1.0, 5.6, 2.2, 1.0, "UCI duomenys\n12 330 sesijų"),
        (3.9, 5.6, 2.2, 1.0, "Laikinis skaidymas\nmokymas / validacija / testas"),
        (6.8, 5.6, 2.2, 1.0, "Paruošimas\nmedianos ir kodavimas"),
        (6.8, 2.5, 2.2, 1.0, "Galutinis testas\nAP, Brier, F2 ir klaidos"),
        (3.9, 2.5, 2.2, 1.0, "Modelių parinkimas\ntik pagal validacijos AP"),
        (1.0, 2.5, 2.2, 1.0, "Naudojimas\ntikimybė ir slenkstis"),
    ]
    for x, y, w, h, label in nodes:
        box = FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.12", linewidth=1.2,
            edgecolor="#234a76", facecolor="#edf4fb"
        )
        ax.add_patch(box)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", color="#142d4c")
    arrows = [
        ((3.2, 6.1), (3.9, 6.1)), ((6.1, 6.1), (6.8, 6.1)),
        ((7.9, 5.6), (7.9, 3.5)), ((6.8, 3.0), (6.1, 3.0)),
        ((3.9, 3.0), (3.2, 3.0)),
    ]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=14,
                                     linewidth=1.2, color="#234a76"))
    ax.text(5, 7.35, "Eksperimento eiga ir informacijos srautas", ha="center",
            fontsize=13, weight="bold", color="#142d4c")
    ax.text(5, 1.15, "Galutinis testas modelių ar slenksčių parinkimui nenaudojamas",
            ha="center", fontsize=10, color="#7a2e2e")
    fig.tight_layout()
    fig.savefig(ASSETS / "exam_workflow.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    labels = ["Pastovus\ndažnis", "Logistinė\nregresija", "Atsitiktinis\nmiškas", "Gradientinis\nstiprinimas"]
    ap = [0.2066, 0.3336, 0.3411, 0.3392]
    brier = [0.1731, 0.1582, 0.1555, 0.1572]
    colors = ["#9aa5b1", "#5b8db8", "#174a7e", "#7ba6c9"]
    fig, axes = plt.subplots(1, 2, figsize=(9.3, 4.4))
    for ax, values, title, better in [
        (axes[0], ap, "AP: didesnė reikšmė geresnė", "↑"),
        (axes[1], brier, "Brier nuostolis: mažesnė reikšmė geresnė", "↓"),
    ]:
        bars = ax.bar(range(4), values, color=colors, width=0.68)
        ax.set_xticks(range(4), labels)
        ax.set_title(f"{title}  {better}", fontsize=11, weight="bold")
        ax.grid(axis="y", alpha=0.22)
        ax.set_axisbelow(True)
        top = max(values) * 1.18
        ax.set_ylim(0, top)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + top * 0.018,
                    f"{value:.4f}", ha="center", va="bottom", fontsize=9)
    fig.suptitle("Pagrindinių modelių rezultatai galutiniame teste", fontsize=13, weight="bold")
    fig.tight_layout()
    fig.savefig(ASSETS / "exam_model_comparison.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


FORMULAS = [
    r"\hat{p}_{RF}(x)=\frac{1}{T}\sum_{t=1}^{T}\hat{p}_{t}(x)",
    r"AP=\sum_{k}(R_k-R_{k-1})P_k",
    r"Brier=\frac{1}{n}\sum_{i=1}^{n}(\hat{p}_i-y_i)^2",
    r"F_2=\frac{5\,\mathrm{Precision}\,\mathrm{Recall}}{4\,\mathrm{Precision}+\mathrm{Recall}}",
    r"\Delta AP=AP_{RF}-AP_{LR}=0.3411-0.3336=0.0076",
]


def math_nodes():
    source = "\n\n".join("$$\n" + f + "\n$$" for f in FORMULAS)
    converted = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "docx"],
        input=source.encode(), capture_output=True, check=True,
    )
    with ZipFile(BytesIO(converted.stdout)) as archive:
        tree = etree.fromstring(archive.read("word/document.xml"))
    nodes = tree.findall(".//" + qn("m:oMathPara"))
    if len(nodes) != len(FORMULAS):
        raise RuntimeError("Nepavyko konvertuoti visų formulių į OMML.")
    return nodes


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def add_hyperlink(paragraph, text: str, url: str) -> None:
    relation = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), relation)
    run = OxmlElement("w:r")
    props = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    props.extend([color, underline])
    run.append(props)
    text_node = OxmlElement("w:t")
    text_node.text = text
    run.append(text_node)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def add_page_number(section) -> None:
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    p._p.append(field)


class Report:
    def __init__(self):
        self.doc = Document()
        self.math = math_nodes()
        self.eq_no = 0
        self.table_no = 0
        self.figure_no = 0
        self.md: list[str] = []
        self._style()

    def _style(self):
        sec = self.doc.sections[0]
        sec.page_width, sec.page_height = Mm(210), Mm(297)
        sec.left_margin, sec.right_margin = Mm(30), Mm(20)
        sec.top_margin = sec.bottom_margin = Mm(20)
        sec.footer_distance = Mm(10)
        add_page_number(sec)
        for name in ("Normal", "Heading 1", "Heading 2", "Caption"):
            style = self.doc.styles[name]
            style.font.name = "Times New Roman"
            style.font.size = Pt(12)
            style.font.color.rgb = RGBColor(0, 0, 0)
            fonts = style.element.get_or_add_rPr().rFonts
            for key in ("ascii", "hAnsi", "eastAsia", "cs"):
                fonts.set(qn("w:" + key), "Times New Roman")
            style.paragraph_format.line_spacing = 1.5
            style.paragraph_format.space_after = Pt(6)
        self.doc.styles["Normal"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        self.doc.styles["Heading 1"].font.size = Pt(14)
        self.doc.styles["Heading 1"].font.bold = True
        self.doc.styles["Heading 2"].font.size = Pt(12)
        self.doc.styles["Heading 2"].font.bold = True
        for name in ("Heading 1", "Heading 2"):
            self.doc.styles[name].paragraph_format.keep_with_next = True
            self.doc.styles[name].paragraph_format.space_before = Pt(12)
        self.doc.styles["Caption"].font.italic = False
        self.doc.styles["Caption"].paragraph_format.keep_with_next = True
        self.doc.core_properties.title = "Elektroninės parduotuvės pirkimo ketinimo tyrimo egzamino ataskaita"
        self.doc.core_properties.author = "Andrej Kondratjev"

    def title_page(self):
        for _ in range(4):
            self.doc.add_paragraph()
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run("ELEKTRONINĖS PARDUOTUVĖS PIRKIMO KETINIMO TYRIMO\nEGZAMINO ATASKAITA")
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(16)
        p.paragraph_format.line_spacing = 1.5
        for _ in range(4):
            self.doc.add_paragraph()
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.add_run("Parengė: Andrej Kondratjev\nGrupė: DISfm-26\nDalykas: Intelektualiosios sistemos")
        for _ in range(7):
            self.doc.add_paragraph()
        p = self.doc.add_paragraph("Vilnius, 2026")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self.doc.add_page_break()
        self.md.extend([
            "# Elektroninės parduotuvės pirkimo ketinimo tyrimo egzamino ataskaita",
            "", "**Andrej Kondratjev · DISfm-26 · Intelektualiosios sistemos · 2026**", "",
        ])

    def heading(self, text: str, level=1):
        self.doc.add_heading(text, level=level)
        self.md.extend(["#" * (level + 1) + " " + text, ""])

    def p(self, text: str):
        p = self.doc.add_paragraph()
        pieces = [(text, False)]
        for term in ENGLISH_TERMS:
            updated = []
            for value, italic in pieces:
                if italic:
                    updated.append((value, True))
                    continue
                split = value.split(term)
                for index, part in enumerate(split):
                    if part:
                        updated.append((part, False))
                    if index < len(split) - 1:
                        updated.append((term, True))
            pieces = updated
        markdown = ""
        for value, italic in pieces:
            run = p.add_run(value)
            run.italic = italic
            markdown += f"*{value}*" if italic else value
        self.md.extend([markdown, ""])

    def bullets(self, items: list[str]):
        for item in items:
            p = self.doc.add_paragraph(style="List Bullet")
            p.add_run(item)
            self.md.append("- " + item)
        self.md.append("")

    def code(self, text: str):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Mm(8)
        p.paragraph_format.right_indent = Mm(8)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(text)
        r.font.name = "Consolas"
        r.font.size = Pt(10)
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), "F2F2F2")
        p._p.get_or_add_pPr().append(shading)
        self.md.extend(["```python", text, "```", ""])

    def link_paragraph(self, prefix: str, label: str, url: str, suffix=""):
        p = self.doc.add_paragraph()
        p.add_run(prefix)
        add_hyperlink(p, label, url)
        if suffix:
            p.add_run(suffix)
        self.md.extend([f"{prefix}[{label}]({url}){suffix}", ""])

    def formula(self, explanation: str):
        self.eq_no += 1
        table = self.doc.add_table(rows=1, cols=2)
        table.autofit = False
        table.columns[0].width = Mm(145)
        table.columns[1].width = Mm(15)
        left, right = table.rows[0].cells
        left.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        left.paragraphs[0]._p.append(deepcopy(self.math[self.eq_no - 1]))
        right.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        right.paragraphs[0].add_run(f"({self.eq_no})")
        for cell in table.rows[0].cells:
            cell.paragraphs[0].paragraph_format.line_spacing = 1.0
        self.p(explanation)
        self.md.insert(len(self.md) - 2, f"$$ {FORMULAS[self.eq_no - 1]} \tag{{{self.eq_no}}} $$")
        self.md.insert(len(self.md) - 2, "")

    def table(self, caption: str, headers: list[str], rows: list[list[str]], widths=None):
        self.table_no += 1
        cap = self.doc.add_paragraph(f"{self.table_no} lentelė. {caption}", style="Caption")
        cap.paragraph_format.keep_with_next = True
        table = self.doc.add_table(rows=len(rows) + 1, cols=len(headers))
        table.autofit = False
        if widths is None:
            widths = [1] * len(headers)
        actual = [160 * w / sum(widths) for w in widths]
        for i, row in enumerate([headers] + rows):
            for j, value in enumerate(row):
                cell = table.cell(i, j)
                cell.width = Mm(actual[j])
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                cell.paragraphs[0].add_run(value)
                cell.paragraphs[0].paragraph_format.line_spacing = 1.0
                cell.paragraphs[0].paragraph_format.space_after = Pt(4)
                cell.paragraphs[0].paragraph_format.space_before = Pt(4)
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in cell.paragraphs[0].runs:
                    run.font.size = Pt(9.5)
                    if i == 0:
                        run.bold = True
                if i == 0:
                    set_cell_shading(cell, "D9EAF7")
        table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            el = OxmlElement("w:" + edge)
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "4")
            el.set(qn("w:color"), "888888")
            borders.append(el)
        table._tbl.tblPr.append(borders)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(0)
        self.md.extend([f"**{self.table_no} lentelė. {caption}**", "",
                        "| " + " | ".join(headers) + " |",
                        "|" + "|".join(["---"] * len(headers)) + "|"])
        self.md.extend("| " + " | ".join(row) + " |" for row in rows)
        self.md.append("")

    def figure(self, path: Path, caption: str, width=155):
        self.figure_no += 1
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Mm(width))
        cap = self.doc.add_paragraph(f"{self.figure_no} pav. {caption}", style="Caption")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        relative = Path(os.path.relpath(path, DOCS)).as_posix()
        self.md.extend([f"![{caption}]({relative})", "",
                        f"*{self.figure_no} pav. {caption}*", ""])

    def save(self):
        self.doc.save(DOCS / "EGZAMINO_ATASKAITA.docx")
        (DOCS / "EGZAMINO_ATASKAITA.md").write_text("\n".join(self.md).strip() + "\n", encoding="utf-8")


def build() -> None:
    make_figures()
    r = Report()
    r.title_page()

    r.heading("1. Įvadas")
    r.p("Šioje ataskaitoje aprašomas elektroninės parduotuvės sesijos pirkimo ketinimo tyrimas: duomenų gavimas ir paruošimas, modelių mokymas, parinkimas, galutinis vertinimas, klaidų analizė ir praktinio naudojimo ribos. Tyrimo tikslas – pagal iki sprendimo momento turimus sesijos požymius apskaičiuoti pirkimo tikimybę ir palyginti, ar atsitiktinis miškas suteikia praktiškai pastebimą pranašumą prieš paprastesnes atskaitas. Ataskaitoje pateikiami jau įvykdyto eksperimento rezultatai; visas programos kodas nekartojamas.")
    r.p("Praktinė vertė – galimybė rikiuoti sesijas pagal tikėtiną pirkimą ir nukreipti ribotus veiksmus, pavyzdžiui, konsultanto dėmesį ar priminimą. Prognozė pati savaime nenusako, kokį veiksmą taikyti: tam dar reikia žinoti klaidingo teigiamo sprendimo, praleisto pirkėjo ir intervencijos kainą.")
    r.heading("1.1. Tyrimo klausimas ir hipotezė", 2)
    r.p("Pagrindinis klausimas: ar modelis, gebantis aprašyti netiesines požymių sąveikas, vėlesnių mėnesių sesijas surikiuoja geriau už logistinę regresiją? Iš anksto nustatyta H1 hipotezė: nenaudojant neaiškaus prieinamumo požymio PageValues, atsitiktinio miško galutinio testo AP turi būti bent 0,02, t. y. 2 procentiniais punktais, didesnė už logistinės regresijos AP. 0,02 riba yra projekto minimalus praktiškai pastebimas pagerėjimas, o ne literatūroje garantuotas efektas.")

    r.heading("2. Duomenys ir jų paruošimas")
    r.p("Naudotas UCI Online Shoppers Purchasing Intention duomenų rinkinys (Sakar ir Kastro, 2018). Viena eilutė yra anoniminė internetinės parduotuvės sesijos suvestinė, o tikslas Revenue nurodo, ar sesija baigėsi pirkimu. Rinkinyje yra 12 330 sesijų ir 1 908 pirkimai. Lankytojo identifikatoriaus bei tikslių laiko žymų nėra, todėl mėnuo taikomas tik apytiksliam laikiniam atskyrimui.")
    r.table("Laikinis duomenų skaidymas", ["Imtis", "Mėnesiai", "Sesijos", "Pirkimai", "Pirkimų dalis"], [
        ["Mokymas", "Vasaris–rugpjūtis", "6 608", "731", "11,06 %"],
        ["Validacija", "Rugsėjis–spalis", "997", "201", "20,16 %"],
        ["Galutinis testas", "Lapkritis–gruodis", "4 725", "976", "20,66 %"],
    ], [1.2, 1.7, 1, 1, 1.2])
    r.p("Skaidymas sąmoningai imituoja mokymą iš ankstesnių mėnesių ir vertinimą vėlesniu laikotarpiu. Mokymo imties medianos, kategorijų žodynas ir kitos transformacijos apskaičiuojamos tik iš mokymo dalies. Skaitinės tuščios reikšmės pakeičiamos mokymo mediana, kategorinės – atskira reikšme, o kategorijos koduojamos vienkartiniu kodavimu (angl. one-hot encoding). Nežinomos vėlesnių imčių kategorijos priimamos be klaidos.")
    r.p("Pagrindiniame variante naudojama 15 pradinių požymių. PageValues pašalintas, nes jo apskaičiavimo momentas duomenų apraše nėra pakankamai aiškus realaus laiko prognozei. Šis požymis grąžinamas tik atskirame jautrumo bandyme. Visiškai sutampančios 125 eilutės paliktos, nes suvestinės sutapimas neįrodo, kad tai tas pats lankytojas; jos dėl mėnesio negali kirsti pasirinkto skaidymo ribų.")

    r.heading("3. Metodai ir eksperimento protokolas")
    r.table("Lyginti metodai", ["Metodas", "Paskirtis", "Parinkti nustatymai"], [
        ["Pastovus mokymo dažnis", "Paprasta atskaita; visoms sesijoms ta pati tikimybė", "p = 0,1106"],
        ["Logistinė regresija", "Stipresnė interpretuojama tiesinė atskaita", "C = 1"],
        ["Atsitiktinis miškas", "Netiesinės sąveikos ir kelių medžių vidurkis", "200 medžių; min. lapas 20"],
        ["Gradientinis stiprinimas", "Nuosekliai taisomos ankstesnių medžių klaidos", "150 iteracijų; 7 lapai"],
    ], [1.3, 2.5, 1.7])
    r.p("Iš viso validacijoje išbandyti 9 iš anksto apibrėžti kandidatai: viena pastovi atskaita, dvi logistinės regresijos, dvi atsitiktinio miško, dvi gradientinio stiprinimo ir dvi atsitiktinio miško su PageValues versijos. Kiekvienoje metodų šeimoje laimėtojas parinktas tik pagal validacijos AP. Galutinis testas iki pasirinkimų užfiksavimo nenaudotas.")
    r.figure(ASSETS / "exam_workflow.png", "Eksperimento eiga ir duomenų atskyrimo principas")
    r.heading("3.1. Atsitiktinio miško prognozė", 2)
    r.formula("Čia T – medžių skaičius, x – vienos sesijos požymių vektorius, o pₜ(x) – t-ojo medžio apskaičiuota pirkimo tikimybė. Galutinė tikimybė yra medžių tikimybių vidurkis.")
    r.heading("3.2. Vertinimo rodikliai", 2)
    r.p("Pagrindinė metrika yra AP (angl. average precision). Ji apibendrina teigiamų prognozių tikslumo (angl. precision) ir jautrumo (angl. recall) ryšį per visus unikalius slenksčius ir gerai tinka retai teigiamai klasei. Precision atsako, kokia teigiamų prognozių dalis buvo teisinga, o recall – kokia tikrų pirkimų dalis aptikta.")
    r.formula("Rₖ ir Pₖ yra recall bei precision k-ajame prognozės slenkstyje. Didesnė AP reikšmė reiškia geresnį sesijų surikiavimą.")
    r.formula("Čia n – vertintų sesijų skaičius, pᵢ – prognozuota tikimybė, yᵢ ∈ {0,1} – tikras pirkimo faktas. Mažesnis Brier nuostolis reiškia tikslesnes tikimybines prognozes.")
    r.p("Veiksmo slenkstis parenkamas validacijoje maksimizuojant F2, nes šiame demonstraciniame scenarijuje recall laikomas svarbesniu už precision. Tikrame diegime slenkstis turi būti siejamas su veiksmų biudžetu ir realiomis klaidų kainomis.")
    r.formula("F2 recall suteikia keturis kartus didesnį svorį negu precision. Tai projekto taisyklė, o ne universalus verslo sprendimas.")

    r.heading("4. Programos realizacija ir prieinamumas")
    r.p("Programa išskaidyta į atskirus modulius: duomenų gavimą, paruošimą, modelius, mokymą, vertinimą, analizę, grafikų kūrimą ir rezultatų įrašymą. Visą eksperimentą paleidžia viena komanda:")
    r.code("python -m src.experiment")
    r.p("Ataskaitoje nekartojamas visas kodas. Svarbiausia vieno išmokyto klasifikatoriaus išvesties eilutė yra:")
    r.code("probabilities = model.predict_proba(X)[:, 1]")
    r.p("Ji paima teigiamos klasės, t. y. pirkimo, tikimybę kiekvienai sesijai. Toliau tos tikimybės naudojamos AP, Brier, precision, recall ir klaidų analizei.")
    r.heading("4.1. GitHub repozitorija", 2)
    r.link_paragraph("Programos kodas, konfigūracija, testai, rezultatai ir atkūrimo instrukcijos pateikti repozitorijoje: ", "SanAndriuwa/IS-EGZ-KL", GITHUB, ".")
    r.p("Atkuriamumui užfiksuota Python ir bibliotekų aplinka, atsitiktinių skaičių pradžios reikšmė 42, vienas skaičiavimo srautas, duomenų SHA256 bei programos failų kontrolinės sumos. Vykdymo aprašas saugomas results/manifest.json.")

    r.heading("5. Pagrindiniai rezultatai")
    r.table("Pagrindinių modelių galutinio testo rezultatai", ["Modelis", "AP", "Precision", "Recall", "Brier"], [
        ["Pastovus mokymo dažnis", "0,2066", "0,2066", "1,0000", "0,1731"],
        ["Logistinė regresija", "0,3336", "0,2438", "0,9693", "0,1582"],
        ["Atsitiktinis miškas", "0,3411", "0,2414", "0,9795", "0,1555"],
        ["Gradientinis stiprinimas", "0,3392", "0,2311", "0,9877", "0,1572"],
    ], [2.2, 1, 1, 1, 1])
    r.figure(ASSETS / "exam_model_comparison.png", "Pagrindinių modelių AP ir Brier palyginimas")
    r.formula("Atsitiktinis miškas skaičiais yra geriausias pagrindinis modelis, tačiau jo AP persvara prieš logistinę regresiją tėra 0,0076, t. y. 0,76 procentinio punkto.")
    r.p("Porinio bootstrap 95 % intervalas skirtumui yra [−0,0113; 0,0284]. Jis apima nulį, o stebėtas 0,0076 pagerėjimas nesiekia iš anksto nustatytos 0,02 ribos. Todėl H1 nepatvirtinama. Tai nėra eksperimento nesėkmė: neigiamas rezultatas parodo, kad sudėtingesnis modelis šioje sąžiningai atskirtoje imtyje nesuteikė numatyto praktinio pranašumo.")
    r.heading("5.1. Slenkstis ir sumaišties matrica", 2)
    r.p("Atsitiktinio miško validacijoje parinktas 0,03 slenkstis. Galutiniame teste gauta TN=745, FP=3 004, FN=20 ir TP=956. Taigi aptikta 97,95 % pirkimų, tačiau iš 3 960 teigiamų prognozių teisingos buvo tik 956. Didelis recall nėra bendras tikslumas; toks žemas slenkstis tiktų tik pigiam veiksmui, kai praleisto pirkėjo kaina yra gerokai didesnė už nereikalingo kontakto kainą.")
    r.heading("5.2. Kalibracija", 2)
    r.figure(ROOT / "results" / "evaluation.png", "Precision–recall ir tikimybių kalibracijos kreivės")
    r.p("Atsitiktinis miškas dažniausiai nuvertina pirkimo tikimybę. Pavyzdžiui, vienoje tikimybių grupėje vidutinė prognozė yra 0,183, o tikroji pirkimų dalis – 0,325; aukščiausioje grupėje atitinkamai 0,300 ir 0,379. Tai dera su tuo, kad testiniu laikotarpiu pirkimų dalis buvo didesnė negu mokymo laikotarpiu, tačiau vien šis sutapimas neįrodo priežasties.")

    r.heading("6. Papildomi bandymai")
    r.heading("6.1. PageValues jautrumas", 2)
    r.p("Pridėjus PageValues, atsitiktinio miško AP padidėjo iki 0,6715, o Brier sumažėjo iki 0,1158. Tai didelis skirtumas, bet jis neįrodo nei duomenų nutekėjimo, nei saugaus požymio naudojimo. Prieš diegimą būtina dokumentuoti, kada ir iš kokių įvykių šis rodiklis apskaičiuojamas. Dėl šio neapibrėžtumo pagrindinė išvada remiasi variantu be PageValues.")
    r.heading("6.2. Trūkstamų reikšmių atsparumas", 2)
    r.table("AP pokytis atsitiktinai paslėpus 9,87 % skaitinių langelių", ["Modelis", "Pradinė AP", "AP su trūkumais", "Pokytis"], [
        ["Logistinė regresija", "0,3336", "0,3298", "−0,0038"],
        ["Atsitiktinis miškas", "0,3411", "0,3386", "−0,0025"],
        ["Gradientinis stiprinimas", "0,3392", "0,3360", "−0,0032"],
    ], [2, 1.2, 1.4, 1.1])
    r.p("Šis bandymas rodo nedidelį jautrumą atsitiktinai išsibarsčiusioms tuščioms skaitinėms reikšmėms. Jis neapima viso stulpelio dingimo, sisteminio matavimo sutrikimo ar trūkumo, priklausančio nuo pirkimo klasės.")
    r.heading("6.3. Pogrupiai ir klaidų pavyzdžiai", 2)
    r.p("Lapkričio atsitiktinio miško AP buvo 0,3868, gruodžio – 0,2900; tuo pat metu pirkimų dalys buvo 25,35 % ir 12,51 %. Kadangi AP priklauso nuo klasės dažnio, šis skirtumas nėra grynas modelio kokybės pablogėjimo matas. Naujiems lankytojams žemas slenkstis visas 754 sesijas priskyrė teigiamai klasei, todėl prieš realų naudojimą būtinas atskiras slenksčio auditas.")
    r.table("Tipiniai atsitiktinio miško klaidų pavyzdžiai", ["Šaltinio eilutė", "Klaida", "Tikimybė", "Interpretacija"], [
        ["10064", "FP", "0,4595", "Intensyvus naršymas, bet nepirkta"],
        ["11145", "FP", "0,4551", "Naujas lankytojas, bet nepirkta"],
        ["10615", "FN", "0,0011", "Trumpa sesija, tačiau pirkta"],
        ["7600", "FN", "0,0052", "Nulinė trukmė, tačiau pirkta"],
    ], [1.3, 0.8, 1, 2.8])
    r.p("Klaidos rodo, kad naršymo intensyvumas nėra pirkimo garantija, o trumpa sesija nėra patikimas nesusidomėjimo įrodymas. Nulinė trukmė kartu su pirkimu taip pat kelia duomenų matavimo taisyklių klausimą.")

    r.heading("7. Klaidų ir nuoseklumo patikra")
    r.p("Prieš rengiant šią ataskaitą rezultatai patikrinti nepriklausomai nuo suvestinio teksto. Visų keturių pagrindinių modelių sumaišties matricų elementai sudaro po 4 725 testines sesijas, o teigiamų klasių suma yra 976. Iš matricų perskaičiuoti precision ir recall sutampa su metrics.csv. Skaidymo lentelėje sesijų suma yra 12 330, o pirkimų – 1 908. Dubliuotų modelio ir scenarijaus rezultatų eilučių nėra.")
    r.p("Paleisti 8 automatiniai testai; visi baigėsi sėkmingai. Jie tikrina laiko tvarką, imčių atskyrimą, neleistinų požymių pašalinimą, mokymo medianas, naujas kategorijas ir tuščias reikšmes, atsitiktinio miško formulę, AP savybę, slenkstį, blogą įvestį ir UTF‑8 rezultatų įrašymą. Eksperimento manifeste užfiksuotas 6,45 s vykdymo laikas autoriaus Windows aplinkoje. Ankstesniame ataskaitos juodraštyje buvo likę pasenę teiginiai apie 9,4 s ir 7 testus; šioje redakcijoje jie ištaisyti.")
    r.p("Duomenų SHA256 ir programos kontrolinės sumos sutampa su dabartiniais failais. Atsitiktinio miško medžių tikimybių vidurkio bei bibliotekos predict_proba išvesties didžiausias absoliutus skirtumas teste yra 0. Skaitinių prieštaravimų tarp manifest.json, metrics.csv, split_summary.csv ir šioje ataskaitoje pateiktų pagrindinių rezultatų nerasta.")

    r.heading("8. Diskusija ir ribotumai")
    r.bullets([
        "Duomenys apima vieną anoniminę parduotuvę ir vienų metų laikotarpį, todėl išvados automatiškai neperkeliamos kitoms parduotuvėms ar sezonams.",
        "Mėnuo suteikia tik apytikslę laiko tvarką; nėra tikslių laiko žymų ir lankytojo identifikatoriaus.",
        "Pirkimų dalis mokyme ir teste skiriasi beveik du kartus, todėl tikimybės vėlesniais mėnesiais yra prasčiau kalibruotos.",
        "Mažas iš anksto nustatytas parametrų tinklas riboja skaičiavimo sąnaudas, bet neįrodo, kad rasta geriausia įmanoma kiekvieno metodo versija.",
        "PageValues, sesijos trukmės, BounceRates ir ExitRates prieinamumas prognozės momentu turi būti audituojamas prieš realaus laiko naudojimą.",
        "Bootstrap intervalas aprašo šio testo ir jau išmokytų modelių neapibrėžtumą; jis neapima kitų mokymo pradžios reikšmių ar būsimų laikotarpių.",
    ])

    r.heading("9. Išvados")
    r.bullets([
        "Atsitiktinis miškas be PageValues pasiekė didžiausią pagrindinių modelių AP – 0,3411 – ir mažiausią Brier nuostolį – 0,1555.",
        "Jo AP persvara prieš logistinę regresiją buvo 0,0076, o 95 % bootstrap intervalas [−0,0113; 0,0284], todėl iš anksto nustatyta bent 0,02 persvaros hipotezė nepatvirtinta.",
        "0,03 slenkstis aptiko 956 iš 976 pirkimų, bet sukūrė 3 004 klaidingus teigiamus atvejus; prieš naudojimą būtinos realios klaidų kainos arba veiksmų biudžetas.",
        "PageValues smarkiai pagerino rezultatą, tačiau jo laikinė kilmė nepatvirtinta, todėl jis neįtrauktas į pagrindinę išvadą.",
        "Programa ir ataskaitos skaičiai yra tarpusavyje nuoseklūs, visi 8 automatiniai testai praeina, tačiau realaus laiko tinkamumui dar reikia požymių kilmės audito ir naujo būsimo laikotarpio bandymo.",
    ])

    r.heading("10. Šaltiniai")
    sources = [
        "Breiman, L. (2001). Random Forests. Machine Learning, 45, 5–32. https://doi.org/10.1023/A:1010933404324",
        "Cawley, G. C., Talbot, N. L. C. (2010). On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation. Journal of Machine Learning Research, 11, 2079–2107. https://www.jmlr.org/papers/v11/cawley10a.html",
        "Friedman, J. H. (2001). Greedy Function Approximation: A Gradient Boosting Machine. The Annals of Statistics, 29(5), 1189–1232. https://doi.org/10.1214/aos/1013203451",
        "Kapoor, S., Narayanan, A. (2022). Leakage and the Reproducibility Crisis in ML-based Science. arXiv. https://doi.org/10.48550/arXiv.2207.07048",
        "Niculescu-Mizil, A., Caruana, R. (2005). Predicting Good Probabilities with Supervised Learning. ICML. https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf",
        "Pedregosa, F. ir kt. (2011). Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 12, 2825–2830. https://www.jmlr.org/papers/v12/pedregosa11a.html",
        "Saito, T., Rehmsmeier, M. (2015). The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets. PLOS ONE, 10(3), e0118432. https://doi.org/10.1371/journal.pone.0118432",
        "Sakar, C. O., Kastro, Y. (2018). Online Shoppers Purchasing Intention Dataset. UCI Machine Learning Repository. https://doi.org/10.24432/C5F88Q",
        "Sakar, C. O. ir kt. (2019). Real-time prediction of online shoppers’ purchasing intention using multilayer perceptron and LSTM recurrent neural networks. Neural Computing and Applications, 31, 6893–6908. https://doi.org/10.1007/s00521-018-3523-0",
        "scikit-learn developers (n.d.). average_precision_score documentation. https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html",
    ]
    for i, source in enumerate(sources, 1):
        p = r.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Mm(8)
        p.paragraph_format.first_line_indent = Mm(-8)
        p.add_run(f"{i}. {source}")
        r.md.append(f"{i}. {source}")
    r.md.append("")
    r.save()


if __name__ == "__main__":
    build()
