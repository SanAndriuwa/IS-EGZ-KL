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
        (6.8, 2.5, 2.2, 1.0, "Modelių parinkimas\ntik pagal validacijos AP"),
        (3.9, 2.5, 2.2, 1.0, "Galutinis testas\nAP, Brier, F2 ir klaidos"),
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

    fig, axes = plt.subplots(4, 1, figsize=(9.2, 6.8))
    rows = [
        ("Paprasta atskaita", ["Mokymo etiketės", "731 / 6608", "Visiems p = 0,1106"], "#7c8fa2"),
        ("Logistinė regresija", ["15 požymių → kodavimas", "Svoriai + poslinkis", "Sigmoidė → p"], "#4e83b2"),
        ("Atsitiktinis miškas", ["Požymiai", "200 medžių lygiagrečiai", "Lapų tikimybių vidurkis"], "#1d517f"),
        ("Gradientinis stiprinimas", ["Požymiai + F₀", "150 medžių paeiliui", "Suma → sigmoidė → p"], "#338f84"),
    ]
    for ax, (label, steps, color) in zip(axes, rows):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 1.2)
        ax.axis("off")
        ax.text(0, 0.6, label, ha="left", va="center", weight="bold", fontsize=10, color=color)
        for i, step in enumerate(steps):
            x = 2.55 + 2.4 * i
            box = FancyBboxPatch((x, 0.22), 2.05, 0.7, boxstyle="round,pad=0.07",
                                 facecolor="#f1f5f9", edgecolor=color, linewidth=1.1)
            ax.add_patch(box)
            ax.text(x + 1.025, 0.57, step, ha="center", va="center", fontsize=9)
            if i < 2:
                ax.add_patch(FancyArrowPatch((x + 2.06, 0.57), (x + 2.37, 0.57),
                                             arrowstyle="-|>", mutation_scale=12, color=color))
    fig.suptitle("Keturi tikimybės skaičiavimo principai", fontsize=13, weight="bold")
    fig.text(0.5, 0.02, "Supaprastinta schema: medžių vidaus šakų ir visų užkoduotų požymių ji nerodo.",
             ha="center", fontsize=9, color="#555")
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    fig.savefig(ASSETS / "exam_model_mechanisms.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


FORMULAS = [
    r"\hat p_0=\frac{1}{N}\sum_{i=1}^{N}y_i",
    r"\hat p_{\mathrm{LR}}(x)=\frac{1}{1+\exp[-(w^{\mathsf T}z+a)]}",
    r"\hat p_{\mathrm{RF}}(x)=\frac{1}{T}\sum_{t=1}^{T}p_t(z)",
    r"\hat p_{\mathrm{GB}}(x)=\sigma\!\left(F_0+\eta\sum_{m=1}^{M}h_m(z)\right)",
    r"AP=\sum_{k}(R_k-R_{k-1})P_k",
    r"Brier=\frac{1}{n}\sum_{i=1}^{n}(\hat{p}_i-y_i)^2",
    r"F_2=\frac{5\,\mathrm{Precision}\,\mathrm{Recall}}{4\,\mathrm{Precision}+\mathrm{Recall}}",
    r"F_1=\frac{2\,\mathrm{Precision}\,\mathrm{Recall}}{\mathrm{Precision}+\mathrm{Recall}}",
    r"\Delta AP=AP_{RF}-AP_{LR}=0.3411-0.3336=0.0076",
]


def math_nodes():
    source = "\n\n".join("$$\n" + f + "\n$$" for f in FORMULAS)
    converted = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "docx", "-o", "-"],
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
        self.md.insert(len(self.md) - 2, f"$$ {FORMULAS[self.eq_no - 1]} \\tag{{{self.eq_no}}} $$")
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
            table.rows[i]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
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
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(path), width=Mm(width))
        cap = self.doc.add_paragraph(f"{self.figure_no} pav. {caption}", style="Caption")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.keep_with_next = False
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
    r.p("Šioje ataskaitoje aprašomas elektroninės parduotuvės sesijos pirkimo ketinimo tyrimas: duomenų gavimas ir paruošimas, modelių mokymas, parinkimas, galutinis vertinimas, klaidų analizė ir praktinio naudojimo ribos. Tyrimo tikslas – pagal užbaigtų sesijų suvestines apskaičiuoti pirkimo tikimybės įvertį ir palyginti, ar atsitiktinis miškas suteikia praktiškai pastebimą pranašumą prieš paprastesnes atskaitas. Šio bandymo požymių prieinamumas dar vykstant naršymui nepatvirtintas. Ataskaitoje pateikiami jau įvykdyto eksperimento rezultatai; visas programos kodas nekartojamas.")
    r.p("Praktinė vertė – galimybė rikiuoti sesijas pagal tikėtiną pirkimą ir nukreipti ribotus veiksmus, pavyzdžiui, konsultanto dėmesį ar priminimą. Prognozė pati savaime nenusako, kokį veiksmą taikyti: tam dar reikia žinoti klaidingo teigiamo sprendimo, praleisto pirkėjo ir intervencijos kainą.")
    r.heading("1.1. Tyrimo klausimas ir hipotezė", 2)
    r.p("Pagrindinis klausimas: ar modelis, gebantis aprašyti netiesines požymių sąveikas, vėlesnių mėnesių sesijas surikiuoja geriau už logistinę regresiją? Iš anksto nustatyta H1 hipotezė: nenaudojant neaiškaus prieinamumo požymio PageValues, atsitiktinio miško galutinio testo AP turi būti bent 0,02, t. y. 2 procentiniais punktais, didesnė už logistinės regresijos AP.")
    r.p("0,02 buvo iš anksto pasirinkta mokomojo darbo praktiškai pastebimos persvaros riba, kad, pavyzdžiui, 0,002 AP (0,2 procentinio punkto) nebūtų laikoma pakankamu pagrindu rinktis sudėtingesnį mišką. Tai nėra statistinio reikšmingumo slenkstis, universali literatūros norma ar pinigais pagrįsta verslo riba. Jei būtų žinomos FP, FN ir intervencijos kainos, ribą reikėtų sieti su jomis. Todėl išvada vertinama ir pagal porinio bootstrap AP skirtumo intervalą.")

    r.heading("2. Duomenys ir jų paruošimas")
    r.p("Naudotas UCI Online Shoppers Purchasing Intention duomenų rinkinys (Sakar ir Kastro, 2018). Viena eilutė yra anoniminė internetinės parduotuvės sesijos suvestinė, o tikslas Revenue nurodo, ar sesija baigėsi pirkimu. Rinkinyje yra 12 330 sesijų ir 1 908 pirkimai. Lankytojo identifikatoriaus bei tikslių laiko žymų nėra, todėl mėnuo taikomas tik apytiksliam laikiniam atskyrimui.")
    r.table("Laikinis duomenų skaidymas", ["Imtis", "Mėnesiai", "Sesijos", "Pirkimai", "Pirkimų dalis"], [
        ["Mokymas", "Vasaris–rugpjūtis", "6 608", "731", "11,06 %"],
        ["Validacija", "Rugsėjis–spalis", "997", "201", "20,16 %"],
        ["Galutinis testas", "Lapkritis–gruodis", "4 725", "976", "20,66 %"],
    ], [1.2, 1.7, 1, 1, 1.2])
    r.p("Skaidymas sąmoningai imituoja mokymą iš ankstesnių mėnesių ir vertinimą vėlesniu laikotarpiu. Mokymo imties medianos, kategorijų žodynas ir kitos transformacijos apskaičiuojamos tik iš mokymo dalies. Skaitinės tuščios reikšmės pakeičiamos mokymo mediana, kategorinės – mokyme dažniausia reikšme, o kategorijos koduojamos vienkartiniu kodavimu (angl. one-hot encoding). Nežinomos vėlesnių imčių kategorijos priimamos be klaidos.")
    r.p("Mokymo imtyje modeliai išmoksta parametrus, validacijoje parenkami hiperparametrai ir sprendimo slenkstis, o testas naudojamas jau užfiksuotam sprendimui įvertinti. Validacija nėra papildoma mokymo imtis: pasirinktas modelis po jos nepermokomas sujungus mokymą ir validaciją.")
    r.p("Lapkričio–gruodžio imtis buvo validus nepriklausomas galutinis testas pirmojo vertinimo metu, nes modeliai, hiperparametrai ir slenksčiai buvo užfiksuoti prieš jį atveriant. Po klaidų, pogrupių, kalibracijos ir slenksčio elgsenos analizės ši imtis tyrėjui jau žinoma. Todėl vėlesni modelio pakeitimai negali būti laikomi nepriklausomai patvirtintais tame pačiame teste; jiems reikia naujo būsimo laikotarpio arba kitos iki tol neliestos holdout imties.")
    r.p("Pagrindiniame variante naudojama 15 pradinių požymių. PageValues pašalintas, nes jo apskaičiavimo momentas duomenų apraše nėra pakankamai aiškus realaus laiko prognozei. Šis požymis grąžinamas tik atskirame jautrumo bandyme. Dabartinis eksperimentas yra užbaigtų sesijų suvestinių offline/post-session klasifikavimas, o ne patvirtintas tarpinės sesijos realaus laiko prognozavimas. Visiškai sutampančios 125 eilutės paliktos, nes suvestinės sutapimas neįrodo, kad tai tas pats lankytojas; jos dėl mėnesio negali kirsti pasirinkto skaidymo ribų.")

    r.heading("3. Metodai ir eksperimento protokolas")
    r.table("Lyginti metodai", ["Metodas", "Paskirtis", "Parinkti nustatymai"], [
        ["Pastovus mokymo dažnis", "Paprasta atskaita; visoms sesijoms ta pati tikimybė", "p = 0,1106"],
        ["Logistinė regresija", "Stipresnė interpretuojama tiesinė atskaita", "C = 1"],
        ["Atsitiktinis miškas", "Netiesinės sąveikos ir kelių medžių vidurkis", "200 medžių; min. lapas 20"],
        ["Gradientinis stiprinimas", "Nuosekliai taisomos ankstesnių medžių klaidos", "150 iteracijų; 7 lapai"],
    ], [1.3, 2.5, 1.7])
    r.p("Iš viso validacijoje išbandyti 9 iš anksto apibrėžti kandidatai: viena pastovi atskaita, dvi logistinės regresijos (C ∈ {0,1; 1,0}), dvi atsitiktinio miško (min_samples_leaf ∈ {5; 20}), dvi gradientinio stiprinimo (max_leaf_nodes ∈ {7; 15}) ir dvi atsitiktinio miško su PageValues versijos. Tai ribotas hiperparametrų palyginimas validacijos imtyje, o ne išsami optimizacija. Kiekvienoje metodų šeimoje laimėtojas parinktas tik pagal validacijos AP. Galutinis testas iki pasirinkimų užfiksavimo nenaudotas.")
    r.p("Miško 200 medžių ir stiprinimo 150 iteracijų bei mokymosi žingsnis 0,05 buvo nustatyti iš anksto pagal ribotą skaičiavimo biudžetą; optimalumas neįrodytas. Miško medžiai mokomi atskirai, o stiprinimo medžiai kuriami nuosekliai, todėl jų skaičių tiesiogiai lyginti negalima. Atsitiktinių skaičių pradžios reikšmė 42 pasirinkta tik atkuriamumui, ne kokybei gerinti.")
    r.figure(ASSETS / "exam_workflow.png", "Eksperimento eiga ir duomenų atskyrimo principas", width=135)
    r.heading("3.1. Kaip kiekvienas metodas apskaičiuoja tikimybę", 2)
    r.p("Visi keturi metodai grąžina įvertį intervale [0; 1], bet skiriasi būdu, kuriuo jį gauna. x žymi vienos sesijos pradinius požymius, o z – tą pačią sesiją po mokymo imtyje nustatyto paruošimo. Šios formulės aprašo prognozavimą jau išmokytu modeliu, o ne visą jo mokymo procedūrą.")
    r.p("Toliau pateiktos AI sukurtos principinės iliustracijos paaiškina metodų veikimą; jose esančios skaidymo ribos, lapų reikšmės ir tikimybės yra sąlyginiai pavyzdžiai, ne išmokytų modelių ar eksperimento rezultatai. Paveiksluose X reiškia modeliui perduodamus jau paruoštus požymius; formulėse jie žymimi z.")
    r.p("Pastovus mokymo pirkimų dažnis (angl. baseline) ignoruoja z ir visoms sesijoms priskiria vienodą mokymo pirkimų dalį (scikit-learn developers, n.d.-b):")
    r.formula("N = 6 608 – mokymo sesijų skaičius, o yᵢ yra i-osios mokymo sesijos Revenue (1 – pirkta, 0 – nepirkta). Šiame bandyme p₀ = 731 / 6 608 ≈ 0,1106 yra mokymo pirkimų dalis: ją modelis grąžina kaip tikimybę kiekvienai sesijai. Visoms eilutėms skiriamas tas pats balas, todėl baseline jų neranguoja. Jo testo AP = 0,2066 yra testo pirkimų dalis. Baseline AP nėra 0,1106, nes AP skaičiuojama testo imtyje, o pastovaus balo AP lygi vertinamos imties teigiamos klasės daliai.")
    r.p("Logistinė regresija sudeda išmoktų požymių svorių poveikį ir rezultatą paverčia tikimybe sigmoidės funkcija:")
    r.formula("w yra iš mokymo duomenų išmoktas požymių svorių vektorius, a – poslinkis; skliaustuose esantis wᵀz + a yra pradinis įvertis. Didesnis C reiškia silpnesnį koeficientų apribojimą; validacija pasirinko C = 1. Tai dvejetainio LogisticRegression predict_proba taisyklė (scikit-learn developers, n.d.-c).")
    r.p("Paslėptų sluoksnių nėra. Naudojami 9 skaitiniai ir 6 kategoriniai pradiniai požymiai; po kodavimo komponentų daugiau. Logistinės regresijos paveiksle z žymi vieną svertinės sumos skaičių, o (2) formulėje z yra paruoštų požymių vektorius. Tai skirtingi to paties simbolio žymėjimai.")
    r.figure(ASSETS / "logistic_regression.png", "Logistinės regresijos principas: svertinė suma, sigmoidė ir sprendimo slenkstis", width=155)
    r.p("Atsitiktinis miškas kiekvieną paruoštą sesiją nuveda į kiekvieno medžio lapą; iš ten gautos teigiamos klasės tikimybės suvidurkinamos:")
    r.formula("T = 200 – medžių skaičius, pₜ(z) – t-ojo medžio pasiekto lapo mokymo pavyzdžių pirkimų dalis. Tai tikimybių vidurkis, ne balsavimas pagal kiekvieno medžio 0/1 klasę (scikit-learn developers, n.d.-d).")
    r.figure(ASSETS / "random_forest.png", "Atsitiktinio miško principas: atskirų medžių lapų tikimybių vidurkis; skaičiai iliustraciniai", width=155)
    r.p("Schemoje parodyti tik keli iš 200 medžių ir sąlyginiai jų lapai. Ji nevaizduoja tikrų šio darbo medžių skaidymų. Mokant su pavyzdžių ar klasių svoriais, lapo klasės dalis skaičiuojama atsižvelgiant į tuos svorius.")
    r.p("Histograminis gradientinis stiprinimas (angl. histogram-based gradient boosting) iš pradinio įverčio nuosekliai prideda medžių taisymus logaritminių šansų skalėje. Tikimybė gaunama pritaikius sigmoidę:")
    r.formula("F₀ yra mokyme nustatytas pradinis įvertis, hₘ(z) – m-ojo medžio indėlis prieš žingsnio koeficientą, M = 150 – iteracijų skaičius, η = 0,05 – mokymosi žingsnis, σ(u) = 1 / (1 + exp(−u)). Tai skaičiavimo principo užrašas: tikslų lapų reikšmių ir jų taisymų mokymą įgyvendina scikit-learn. Šio modelio medžių tikimybės tiesiogiai nevidurkinamos (scikit-learn developers, n.d.-e).")
    r.p("Skirtingą medžių skaičių lemia jų vaidmuo: miško 200 medžių išmokstami atskirai ir jų prognozės vidurkinamos, o stiprinimo 150 medžių kuriami paeiliui, po vieną mažą taisymą su η = 0,05. Skaičiai 200 ir 150 buvo iš anksto pasirinkti ribotam skaičiavimo biudžetui, o ne kaip vienodo sudėtingumo ar įrodyto optimalaus tikslumo reikšmės. Todėl vien medžių skaičius neleidžia spręsti, kuris modelis geresnis; tai parodo tik atskirtos imties metrikos.")
    r.p("Visiems metodams dvejetainė išvestis gaunama palyginus jų grąžintą pirkimo tikimybę su tos metodų šeimos validacijoje parinktu slenksčiu τ: jei p ≥ τ, prognozė yra 1, kitu atveju – 0. Pastovus modelis slenksčio tinklelyje visus testo įrašus priskyrė teigiamai klasei.")
    r.figure(ASSETS / "gradient_boosting.png", "Gradientinio stiprinimo mokymo ir prognozavimo principas; skaičiai iliustraciniai", width=155)
    r.p("Stiprinimo paveiksle fₘ(x) žymi jau mokymosi žingsniu sumažintą medžio indėlį: fₘ(x) = ηhₘ(z). Todėl paveikslo sumoje η nebekartojamas. Pavaizduota 0,73 tikimybė yra tik sąlyginis pavyzdys; ji nėra konkrečios mūsų duomenų sesijos prognozė. Visų modelių tikimybė į 0/1 klasę paverčiama pagal validacijoje parinktą slenkstį.")
    r.heading("3.2. Vertinimo rodikliai", 2)
    r.p("Pagrindinė metrika yra AP (angl. average precision). Ji apibendrina teigiamų prognozių tikslumo (angl. precision) ir jautrumo (angl. recall) ryšį per visus unikalius slenksčius ir gerai tinka retai teigiamai klasei. Jei TP yra teisingai aptikti pirkimai, FP – klaidingai pirkimais pavadintos sesijos, o FN – praleisti pirkimai, tai precision = TP / (TP + FP) ir recall = TP / (TP + FN). Pirmasis atsako, kokia teigiamų prognozių dalis teisinga, antrasis – kokia tikrų pirkimų dalis aptikta.")
    r.formula("Rₖ ir Pₖ yra recall bei precision k-ajame prognozės slenkstyje. Didesnė AP reikšmė reiškia geresnį sesijų surikiavimą.")
    r.p("AP atsako, kaip gerai modelis surikiuoja sesijas pagal pirkimo tikimybę. Pagal validacijos AP pasirenkamas kandidatas; ši metrika nepriklauso nuo vieno fiksuoto sprendimo slenksčio. F2 naudojamas tik parinkti slenkstį jau pasirinktam kandidatui. Užfiksavus slenkstį, precision, recall, F1 ir F2 apibūdina konkrečius dvejetainius sprendimus.")
    r.formula("Čia n – vertintų sesijų skaičius, pᵢ – prognozuota tikimybė, yᵢ ∈ {0,1} – tikras pirkimo faktas. Kai p = 0,9 ir pirkimas įvyksta, kvadratinė klaida maža; kai pirkimo nėra, ji didelė. Brier yra šių klaidų vidurkis, todėl mažesnis geresnis. Jis vertina tikimybines prognozes apskritai; kalibracijos kreivė atskirai lygina prognozes su stebėtais dažniais.")
    r.p("Log loss taip pat vertina tikimybes, bet ypač stipriai baudžia už labai užtikrintas klaidingas prognozes. Mažesnis log loss geresnis; šiame darbe jis yra papildomas rodiklis, ne modelio parinkimo kriterijus.")
    r.p("AP ir trapecinis PR-AUC apibūdina precision–recall kreivę, bet skaičiuojami skirtingai. Pastoviam modeliui trapecinis plotas čia yra 0,6033 dėl kreivės galinio taško, nors modelis sesijų neranguoja. Todėl pagrindiniam palyginimui naudojama AP, o trapecinis PR-AUC pateikiamas tik papildomai.")
    r.p("Veiksmo slenkstis parenkamas validacijoje maksimizuojant F2. Šiame mokomajame scenarijuje potencialaus pirkėjo praleidimas laikomas mažiau pageidaujamu nei papildomas klaidingas signalas. Tai tinka pigiam veiksmui, pavyzdžiui, priminimui; brangiai nuolaidai ar konsultanto skambučiui toks prioritetas gali netikti. Tikrųjų FP, FN ir intervencijos kainų nėra, todėl F2 nėra įrodytas verslo optimumas.")
    r.formula("F2 teikia pirmenybę recall: išreikštos per klaidų skaičius formulės vardiklyje FN koeficientas yra 4, o FP – 1 (scikit-learn developers, n.d.-f). Tai projekto taisyklė, o ne universali klaidų kainų proporcija.")
    r.p("Palyginimui F1 vienoje reikšmėje vienodai derina precision ir recall:")
    r.formula("Pakeitus tik skaičiavimo rodiklį iš F2 į F1, to paties modelio prognozės ir TP, FP, FN nepasikeičia; pasikeičia skaitinė vertinimo reikšmė. Jei pagal naują rodiklį iš naujo parenkamas slenkstis validacijoje, gali pasikeisti ir sprendimai, precision bei recall.")
    r.table("Rodiklių paskirtis ir interpretacija", ["Rodiklis", "Kam naudojamas", "Geriau", "Svarbiausia interpretacija"], [
        ["AP", "Modelių rangavimo palyginimas", "Didesnis", "Ne accuracy; nepriklauso nuo vieno slenksčio"],
        ["Precision", "Teigiamų sprendimų vertinimas", "Didesnis", "Kokia prognozuotų pirkimų dalis tikra"],
        ["Recall", "Aptiktų pirkimų vertinimas", "Didesnis", "Kokia tikrų pirkimų dalis rasta"],
        ["F1", "Papildomas sprendimų rodiklis", "Didesnis", "Vienodai derina precision ir recall"],
        ["F2", "Validacijos slenksčio parinkimas", "Didesnis", "Teikia pirmenybę recall; ne finansinis optimumas"],
        ["Brier", "Tikimybių klaida", "Mažesnis", "Vidutinė kvadratinė tikimybės klaida"],
        ["Log loss", "Papildoma tikimybių klaida", "Mažesnis", "Stipriai baudžia už užtikrintas klaidas"],
        ["Trapecinis PR-AUC", "Papildoma PR kreivės charakteristika", "Didesnis", "Pastovaus modelio reikšmė gali klaidinti"],
        ["Bootstrap 95 % intervalas", "RF ir LR AP skirtumo neapibrėžtumas", "—", "Jei apima 0, RF persvara neįrodyta"],
    ], [1.25, 2.0, 0.8, 2.2])
    r.heading("3.3. Naujausi literatūroje taikomi metodai", 2)
    r.p("Abdullah-All-Tanvir ir kt. (2023) artimai pirkimo ketinimo užduočiai taikė XGBoost, požymių atranką ir balansavimą. Satu ir Islam (2023) tam pačiam UCI rinkiniui tyrė RF su transformacijomis, SMOTE ir atranka. Setyawan ir Himawan (2026) palygino XGBoost, LightGBM ir CatBoost su platesne optimizacija. Tai pagrindas svarstyti metodus, bet ne įrodymas, kad jų skelbti kitų skaidymų accuracy ar ROC-AUC persikeltų į mūsų temporal AP.")
    r.p("Pasirinktas vienas papildomas CPU XGBoost bandymas: nuoseklūs medžiai tinka lenteliniams sesijų požymiams, o train pirkimų disbalansą galima tikrinti teigiamos klasės svoriu. Šis metodas sudėtingesnis už LR, bet paaiškinamas ir telpa į mažą tinklą. SMOTE su požymių atranka atmestas, nes keistų kelias grandis ir reikalautų atsargiai tvarkyti kategorijas; stacking atmestas dėl papildomo meta-modelio skaidymo ir gynimo sudėtingumo. Tai supaprastintas literatūra motyvuotas bandymas, ne straipsnių metodikos reprodukcija. Išsamus šaltinių palyginimas pateiktas docs/NAUJA_LITERATURA.md.")

    r.heading("4. Programos realizacija ir prieinamumas")
    r.p("Programa išskaidyta į atskirus modulius: duomenų gavimą, paruošimą, modelius, mokymą, vertinimą, analizę, grafikų kūrimą ir rezultatų įrašymą. Visą eksperimentą paleidžia viena komanda:")
    r.code("python -m src.experiment")
    r.p("Ataskaitoje nekartojamas visas kodas. Svarbiausia vieno išmokyto klasifikatoriaus išvesties eilutė yra:")
    r.code("probabilities = model.predict_proba(X)[:, 1]")
    r.p("Ji paima teigiamos klasės, t. y. pirkimo, tikimybę kiekvienai sesijai. Toliau tos tikimybės naudojamos AP, Brier, precision, recall ir klaidų analizei.")
    r.heading("4.1. GitHub repozitorija", 2)
    r.link_paragraph("Programos kodas, konfigūracija, testai, rezultatai ir atkūrimo instrukcijos pateikti repozitorijoje: ", "SanAndriuwa/IS-EGZ-KL", GITHUB, ".")
    r.p("Atkuriamumui užfiksuota Python ir bibliotekų aplinka, atsitiktinių skaičių pradžios reikšmė 42, vienas skaičiavimo srautas, duomenų SHA256 bei pradinio pagrindinio paleidimo programos failų kontrolinės sumos. Vykdymo aprašas saugomas results/manifest.json; po papildomos abliacijos kodo pakeitimo jo kodo sumos nėra dabartinių src/ failų sumos.")

    r.heading("5. Pagrindiniai rezultatai")
    r.table("Pagrindinių modelių galutinio testo rezultatai", ["Modelis", "AP", "Precision", "Recall", "Brier"], [
        ["Pastovus mokymo dažnis", "0,2066", "0,2066", "1,0000", "0,1731"],
        ["Logistinė regresija", "0,3336", "0,2438", "0,9693", "0,1582"],
        ["Atsitiktinis miškas", "0,3411", "0,2414", "0,9795", "0,1555"],
        ["Gradientinis stiprinimas", "0,3392", "0,2311", "0,9877", "0,1572"],
    ], [2.2, 1, 1, 1, 1])
    r.heading("Kaip skaityti pagrindinius rezultatus", 2)
    r.bullets([
        "Pastovaus modelio AP = 0,2066 atitinka testo pirkimų dalį; jis sesijų neranguoja.",
        "Logistinės regresijos AP = 0,3336 rodo geresnį pirkimų rangavimą už pastovų modelį.",
        "RF turi didžiausią stebėtą pagrindinių modelių AP = 0,3411; gradientinio stiprinimo AP = 0,3392 yra labai artima.",
        "RF ir logistinės regresijos skirtumas 0,0076 yra mažesnis už iš anksto pasirinktą 0,02 ribą.",
        "Porinio bootstrap intervalas apima 0, todėl tvirto RF pranašumo ši imtis neparodo.",
    ])
    r.p("AP yra rodiklis nuo maždaug 0 iki 1: didesnis reiškia geresnį rangavimą, tačiau 0,3411 nereiškia 34,11 % teisingų atsakymų. RF AP viršija pastovaus modelio AP apie 0,1346 (skirtumas skaičiuotas iš neapvalintų reikšmių), o logistinę regresiją – tik 0,0076.")
    r.figure(ASSETS / "exam_model_comparison.png", "Pagrindinių modelių AP ir Brier palyginimas")
    r.formula("RF turi didžiausią stebėtą AP šiame teste, tačiau jo persvara prieš logistinę regresiją tėra 0,0076, t. y. 0,76 procentinio punkto. Tai neįrodo bendro metodo pranašumo.")
    r.p("Porinis bootstrap 500 kartų su grąžinimu perrenka testo eilutes ir kiekvieną kartą abiejų modelių AP skaičiuoja toms pačioms eilutėms. Iš AP_RF − AP_LR skirtumų gautas centrinis 95 % intervalas [−0,0113; 0,0284]. Jis apima 0, todėl šiame bandyme negalima tvirtai teigti, kad RF geresnis; stebėta persvara taip pat nesiekia 0,02, todėl H1 nepatvirtinama. Intervalas nereiškia 95 % tikimybės, kad tikrasis skirtumas būtinai yra jo viduje, ir neapima kitų parduotuvių, sezonų ar naujų mokymo pradžios reikšmių. 500 pakartojimų yra pasirinktas skaičiavimo biudžetas: daugiau pakartojimų galėtų stabilizuoti intervalo ribas, bet 500 nėra privalomas standartas.")
    r.heading("5.1. Slenkstis ir sumaišties matrica", 2)
    r.p("Atsitiktinio miško 0,03 slenkstis nebuvo ranka parinktas peržiūrėjus testą. Kode tikrintas tinklelis nuo 0,01 iki 0,99 kas 0,01; kiekvienam slenksčiui validacijoje apskaičiuotas F2. Pasirinkto RF didžiausią validacijos F2 davė 0,03. Šis slenkstis užfiksuotas prieš galutinį testą.")
    r.p("Teste gauta TN=745, FP=3 004, FN=20 ir TP=956. Modelis aptiko 956 iš 976 pirkimų, tačiau klaidingai pažymėjo 3 004 nepirkusias sesijas. Jis beveik nepraleidžia pirkėjų, bet teigiamą signalą duoda labai dažnai: recall = 0,9795, o precision = 0,2414. Didelis recall nėra bendras tikslumas.")
    r.p("Prie šio užfiksuoto slenksčio precision = 956 / (956 + 3 004) = 0,2414, recall = 956 / (956 + 20) = 0,9795, F1 = 0,3874, o F2 = 0,6078. Didesnis F2 šiuo atveju nereiškia, kad modelis pagerėjo: abu balai apskaičiuoti iš tų pačių prognozių, tik F2 labiau vertina didelį recall.")
    r.table("To paties miško testo prognozės esant dviem iliustraciniams slenksčiams", ["Slenkstis", "TP", "FP", "FN", "Precision", "Recall", "F1", "F2"], [
        ["0,03", "956", "3 004", "20", "0,2414", "0,9795", "0,3874", "0,6078"],
        ["0,10", "857", "2 142", "119", "0,2858", "0,8781", "0,4312", "0,6207"],
    ], [1.15, 0.7, 0.9, 0.7, 1.2, 1.0, 0.8, 0.8])
    r.p("0,10 eilutė yra tik iliustracija, perskaičiuota pagal jau turimas testo tikimybes: keliant slenkstį sumažėja teigiamų prognozių, praleidžiama daugiau pirkimų, bet sumažėja nereikalingų kontaktų. Teste abiejų F reikšmių padidėjimas nesuteikia teisės pakeisti validacijoje nustatyto 0,03 slenksčio. Norint sąžiningai palyginti F1 ir F2 parenkamus slenksčius, juos reikia atskirai nustatyti išsaugotose validacijos prognozėse arba pakartotinai vykdant mokymą, o tada vieną kartą vertinti tame pačiame teste. Mūsų galutinė AP = 0,3411 nuo šių fiksuotų slenksčių nepriklauso.")
    r.heading("5.2. Kalibracija", 2)
    r.figure(ROOT / "results" / "evaluation.png", "Precision–recall ir tikimybių kalibracijos kreivės")
    r.p("Atsitiktinis miškas dažniausiai nuvertina pirkimo tikimybę. Pavyzdžiui, vienoje tikimybių grupėje vidutinė prognozė yra 0,183, o tikroji pirkimų dalis – 0,325; aukščiausioje grupėje atitinkamai 0,300 ir 0,379. Tai dera su tuo, kad testiniu laikotarpiu pirkimų dalis buvo didesnė negu mokymo laikotarpiu, tačiau vien šis sutapimas neįrodo priežasties.")

    r.heading("6. Papildomi bandymai")
    r.heading("6.1. PageValues jautrumas", 2)
    r.p("Validacijoje parinkto RF testo AP be PageValues buvo 0,3411, o su juo – 0,6715; Brier sumažėjo iki 0,1158. Pirmajame palyginime kartu keitėsi požymis ir validacijoje parinktas lapo dydis: be PageValues jis buvo 20, su juo – 5.")
    r.table("Fiksuotų RF parametrų PageValues abliacija", ["Lapo dydis", "PageValues", "Validacijos AP", "Testo AP"], [
        ["5", "Ne", "0,3063", "0,3345"],
        ["5", "Taip", "0,7070", "0,6715"],
        ["20", "Ne", "0,3070", "0,3411"],
        ["20", "Taip", "0,6904", "0,6611"],
    ], [1.1, 1.4, 1.4, 1.2])
    r.p("Fiksuojant lapo dydį 20, testo AP padidėja nuo 0,3411 iki 0,6611; fiksuojant 5 – nuo 0,3345 iki 0,6715. Taigi stiprus signalas išlieka ir nekeičiant šio parametro. Testas nenaudotas variantui pasirinkti. Abliacija atlikta po pirminės testo analizės, todėl yra tiriamoji, o ne naujas nepriklausomas patvirtinimas. Rezultatas neįrodo nei nutekėjimo, nei PageValues prieinamumo realiu laiku; būtina patikrinti jo skaičiavimo langą. Pagrindinė išvada lieka paremta variantu be šio požymio.")
    r.heading("6.2. Trūkstamų reikšmių atsparumas", 2)
    r.table("AP pokytis atsitiktinai paslėpus 9,87 % skaitinių langelių", ["Modelis", "Pradinė AP", "AP su trūkumais", "Pokytis"], [
        ["Logistinė regresija", "0,3336", "0,3298", "−0,0038"],
        ["Atsitiktinis miškas", "0,3411", "0,3386", "−0,0025"],
        ["Gradientinis stiprinimas", "0,3392", "0,3360", "−0,0032"],
    ], [2, 1.2, 1.4, 1.1])
    r.p("Iš anksto pasirinktas 10 % skaitinių langelių paslėpimas yra kontroliuojamas atsparumo scenarijus, ne realaus diegimo trūkumo dažnio įvertis. Ta pati atsitiktinė kaukė taikyta visiems pagrindiniams modeliams; dėl atsitiktinės atrankos faktiškai paslėpta 4 197 iš 42 525 langelių, arba 9,87 %. Tikslas – patikrinti vidutinio masto atsitiktinių trūkumų poveikį. Bandymas neapima viso stulpelio dingimo, sisteminio trūkumo ar trūkumo, priklausančio nuo pirkimo klasės.")
    r.heading("6.3. Pogrupiai ir klaidų pavyzdžiai", 2)
    r.p("Lapkričio atsitiktinio miško AP buvo 0,3868, gruodžio – 0,2900; tuo pat metu pirkimų dalys buvo 25,35 % ir 12,51 %. Kadangi AP priklauso nuo klasės dažnio, šis skirtumas nėra grynas modelio kokybės pablogėjimo matas. Naujiems lankytojams žemas slenkstis visas 754 sesijas priskyrė teigiamai klasei, todėl prieš realų naudojimą būtinas atskiras slenksčio auditas.")
    r.table("Tipiniai atsitiktinio miško klaidų pavyzdžiai", ["Šaltinio eilutė", "Klaida", "Tikimybė", "Interpretacija"], [
        ["10064", "FP", "0,4595", "Intensyvus naršymas, bet nepirkta"],
        ["11145", "FP", "0,4551", "Naujas lankytojas, bet nepirkta"],
        ["10615", "FN", "0,0011", "Trumpa sesija, tačiau pirkta"],
        ["7600", "FN", "0,0052", "Nulinė trukmė, tačiau pirkta"],
    ], [1.3, 0.8, 1, 2.8])
    r.p("Klaidos rodo, kad naršymo intensyvumas nėra pirkimo garantija, o trumpa sesija nėra patikimas nesusidomėjimo įrodymas. Nulinė trukmė kartu su pirkimu taip pat kelia duomenų matavimo taisyklių klausimą.")
    r.heading("6.4. Tiriamasis rezultato gerinimas po pradinio testo", 2)
    r.p("Pradinė seka: pastovios atskaitos AP = 0,2066, LR = 0,3336, RF = 0,3411, GB = 0,3392. RF persvara prieš LR tėra 0,0076, todėl po šio rezultato atskirai tikrinta, ar mažas RF parametrų pakeitimas arba literatūroje taikomas XGBoost pagerintų rangavimą. Tai post-test exploratory improvement experiment, ne pradinės H1 dalis. Visuose variantuose PageValues nenaudotas, paruošimas ir modelis mokyti tik train, kandidatas parinktas pagal validation AP, slenkstis pagal validation F2; tik tada vieną kartą įvertintas pasirinktas kiekvienos šeimos variantas teste.")
    r.p("RF iš anksto apibrėžtame papildomame tinkle min_samples_leaf = 20, max_depth ∈ {be ribos; 8}, max_features ∈ {sqrt; 0,5}. XGBoost tinkle 150 medžių, learning_rate = 0,05, max_depth ∈ {3; 5}, scale_pos_weight ∈ {1; 8,04}; 8,04 yra tik train neigiamų ir teigiamų sesijų santykis. Šie maži tinklai riboja skaičiavimą; optimalumo neįrodo. Visi kandidatai išsaugoti results/improvement_experiments.csv.")
    r.table("Papildomų variantų validacijos AP", ["Metodas ir parametrai", "Validacijos AP", "Parinktas", "Testo AP"], [
        ["RF: gylis ∞, pož. sqrt", "0,3070", "Ne", "—"],
        ["RF: gylis ∞, pož. 0,5", "0,3073", "Taip", "0,3297"],
        ["RF: gylis 8, pož. sqrt", "0,3034", "Ne", "—"],
        ["RF: gylis 8, pož. 0,5", "0,3041", "Ne", "—"],
        ["XGB: gylis 3, svoris 1", "0,2760", "Ne", "—"],
        ["XGB: gylis 3, svoris 8,04", "0,2817", "Ne", "—"],
        ["XGB: gylis 5, svoris 1", "0,2801", "Ne", "—"],
        ["XGB: gylis 5, svoris 8,04", "0,2830", "Taip", "0,3324"],
    ], [2.5, 1.2, 0.8, 0.9])
    r.p("Brūkšnys reiškia, kad papildomame palyginime neparinkto kandidato testas neskaičiuotas; pradinio RF rezultatas jau buvo žinomas iš pagrindinio eksperimento. Kiekvienos šeimos validacijos laimėtojui slenkstis nustatytas validacijoje, ne teste.")
    r.table("Parinktų tiriamųjų variantų testinės metrikos", ["Variantas", "AP", "Brier", "Precision", "Recall", "F2", "Log loss"], [
        ["RF variantas", "0,3297", "0,1586", "0,2428", "0,9764", "0,6086", "0,4972"],
        ["XGBoost", "0,3324", "0,2185", "0,2329", "0,9826", "0,5977", "0,6147"],
    ], [1.6, 0.8, 0.9, 1, 0.9, 0.8, 1])
    r.figure(ROOT / "results" / "improvement_comparison.png", "Pagrindinių ir tiriamųjų variantų testo AP; nauji variantai nėra nepriklausomai patvirtinti", width=145)
    r.p("Pagal validaciją parinktas RF variantas teste neviršijo pradinio RF (0,3297 prieš 0,3411). XGBoost taip pat neviršijo jo (0,3324), o jo Brier ir log loss buvo blogesni. RF variantas šiek tiek pakeitė precision, recall ir F2 kompromisą, bet aiškaus rangavimo pagerėjimo nėra. Skirtingų šeimų negalima paskelbti laimėtojais renkantis pagal jau žinomą testą. Net jei naujas skaičius būtų didesnis, tai būtų tiriamoji, o ne nauja nepriklausoma generalizacijos patikra; jai reikia būsimo arba iki tol neliesto holdout laikotarpio.")
    r.heading("6.5. Išplėstinis hiperparametrų tyrimas", 2)
    r.p("Po pirminio eksperimento ir mažo literatūra grįsto bandymo ta pati komanda atliko platesnę post-test exploratory paiešką. Pagrindinis RF–LR rezultatas nepakeistas. Keturiuose didėjančiuose laiko folduose iki rugsėjo kiekvieno foldo paruošimas mokytas tik ankstesnių mėnesių train dalyje; Revenue, Month ir PageValues į modelių įvestį nepateko. Patikrintos 722 unikalios konfigūracijos: 22 LR, 250 RF, 200 histograminių GB ir 250 XGBoost; iš viso 3372 modelių mokymai. Kandidatai lyginti pagal vidutinę foldų AP. Dešimt geriausių kiekvienos šeimos variantų patikrinti dėl stabilumo; vienas šeimos variantas mokytas visu vasario–rugpjūčio rinkiniu ir vertintas rugsėjo–spalio validacijoje.")
    r.table("Išplėstinio tyrimo šeimų rezultatai", ["Šeima", "Temporal AP ± SD", "Sep–Oct AP", "Nov–Dec AP*"], [
        ["Logistinė regresija", "0,2397 ± 0,0623", "0,2464", "0,3360"],
        ["Atsitiktinis miškas", "0,2852 ± 0,0326", "0,3052", "0,3325"],
        ["Histograminis GB", "0,2876 ± 0,0216", "0,2920", "0,3380"],
        ["XGBoost", "0,2892 ± 0,0149", "0,2863", "0,3407"],
    ], [1.8, 1.5, 1.1, 1.1])
    r.p("Pastaba. Nov–Dec reikšmės apskaičiuotos tik po to, kai rugsėjo–spalio AP parinko bendrą laimėtoją. Kitų šeimų test rezultatai pateikti palyginimui, ne naujam pasirinkimui. Visos konfigūracijos ir stabilumo rodikliai išsaugoti results/tuning/ kataloge.")
    r.figure(ROOT / "results" / "tuning" / "family_comparison.png", "Išplėstinio tyrimo AP pagal vertinimo laikotarpį; Nov–Dec rodikliai tiriamieji", width=145)
    r.p("Rugsėjo–spalio validacija pasirinko RF (AP 0,3052): 200 medžių, entropy kriterijus, min_samples_leaf = 2, min_samples_split = 20, max_features = sqrt, be gylio ribos ir klasės svorių. Toje pačioje validacijoje pagal F2 parinktas 0,01 slenkstis. Užfiksuoto RF Nov–Dec AP = 0,3325, Brier = 0,1563, precision = 0,2303, recall = 0,9908, F1 = 0,3737, F2 = 0,5967, log loss = 0,4838. Jis aptiko 967 iš 976 pirkimų, bet klaidingai pažymėjo 3232 nepirkusias sesijas.")
    r.p("Pradinis RF turėjo AP 0,3411; naujai parinkto RF skirtumas −0,0087. Plati paieška šiame duomenų skaidyme neatskleidė paslėpto AP pagerėjimo, bet neįrodo, kad parametrai apskritai nesvarbūs. XGBoost Nov–Dec AP 0,3407 buvo didesnė už naujo RF 0,3325, tačiau Sep–Oct AP 0,2863 buvo mažesnė; perrinkimas pagal testą būtų neteisingas. XGBoost Brier 0,2196 taip pat blogesnis už pradinio RF 0,1555. Kadangi Nov–Dec jau buvo analizuotas ankstesniuose etapuose, ši plati paieška nėra naujas nepriklausomas patvirtinimas net ir parinkus modelį be testo rezultatų.")

    r.heading("7. Klaidų ir nuoseklumo patikra")
    r.p("Prieš rengiant šią ataskaitą rezultatai patikrinti nepriklausomai nuo suvestinio teksto. Visų keturių pagrindinių modelių sumaišties matricų elementai sudaro po 4 725 testines sesijas, o teigiamų klasių suma yra 976. Iš matricų perskaičiuoti precision ir recall sutampa su metrics.csv. Skaidymo lentelėje sesijų suma yra 12 330, o pirkimų – 1 908. Dubliuotų modelio ir scenarijaus rezultatų eilučių nėra.")
    r.p("Paleista 14 automatinių testų; visi baigėsi sėkmingai. Ankstesni aštuoni tikrina pirminio eksperimento skaidymą, požymius, paruošimą, RF formulę, AP, slenkstį ir rezultatų įrašymą. Šeši nauji tikrina didėjančius laiko foldus, paruošimą tik foldo train dalyje, 722 unikalių konfigūracijų atkuriamumą, draudžiamų požymių pašalinimą ir modelio pasirinkimo nepriklausomumą nuo pakeistų test balų. Pilnas naujas žurnalas yra results/test_log.txt. Istorinio pirminio eksperimento manifeste įrašytas 6,45 s laikas neapima 3372 vėlesnių mokymų.")
    r.p("Duomenų SHA256 sutampa su naudotu CSV. manifest.json programos kontrolinės sumos aprašo pradinį pagrindinį paleidimą, o ne dabartinius src/ failus po papildomos abliacijos; atskirame pakartotiniame paleidime visi pagrindinių variantų AP tiksliai sutapo su išsaugotais rezultatais. Atsitiktinio miško medžių tikimybių vidurkio bei bibliotekos predict_proba išvesties didžiausias absoliutus skirtumas teste yra 0. Skaitinių prieštaravimų tarp manifest.json, metrics.csv, split_summary.csv ir šioje ataskaitoje pateiktų pagrindinių rezultatų nerasta.")

    r.heading("8. Diskusija ir ribotumai")
    r.p("UCI aprašymas nurodo, kad puslapių skaičius ir trukmė gali būti atnaujinami naršant, tačiau pateiktas CSV neturi tarpinių momentinių kopijų. Todėl galutinių sesijos suvestinės reikšmių prieinamumas konkrečiu realaus laiko prognozės momentu nėra įrodytas.")
    r.table("Požymių prieinamumas prognozės momentu", ["Požymis", "Ką reiškia", "Kada atsiranda", "Tarpiniu momentu", "Pabaigos rizika"], [
        ["Administrative", "Administracinių puslapių skaičius", "Kaupiasi naršant", "Galutinė reikšmė negarantuota", "Vidutinė"],
        ["Administrative_Duration", "Laikas administraciniuose puslapiuose", "Kaupiasi naršant", "Galutinė reikšmė negarantuota", "Vidutinė"],
        ["Informational", "Informacinių puslapių skaičius", "Kaupiasi naršant", "Galutinė reikšmė negarantuota", "Vidutinė"],
        ["Informational_Duration", "Laikas informaciniuose puslapiuose", "Kaupiasi naršant", "Galutinė reikšmė negarantuota", "Vidutinė"],
        ["ProductRelated", "Produktų puslapių skaičius", "Kaupiasi naršant", "Galutinė reikšmė negarantuota", "Vidutinė"],
        ["ProductRelated_Duration", "Laikas produktų puslapiuose", "Kaupiasi per sesiją", "Galutinė reikšmė negarantuota", "Didelė"],
        ["BounceRates", "Puslapių atmetimo rodiklių agregatas", "Analitikos sistemoje", "CSV neįrodo prieinamumo", "Didelė"],
        ["ExitRates", "Puslapių išėjimo rodiklių agregatas", "Analitikos sistemoje", "CSV neįrodo prieinamumo", "Didelė"],
        ["SpecialDay", "Datos artumas specialiai dienai", "Žinomas iš kalendoriaus", "Taip", "Maža"],
        ["PageValues", "Puslapių komercinės vertės agregatas", "Analitikos sistemoje", "CSV neįrodo prieinamumo", "Labai didelė"],
    ], [1.4, 2.2, 1.45, 1.7, 0.9])
    r.p("Revenue nepatenka į įvestį, o PageValues pašalintas iš pagrindinio varianto, tačiau vien tai neįrodo, kad temporalinis informacijos nutekėjimas visiškai pašalintas. Galutinės trukmės, BounceRates ir ExitRates taip pat reikalauja kilmės ir prieinamumo audito.")
    r.bullets([
        "Duomenys apima vieną anoniminę parduotuvę ir vienų metų laikotarpį, todėl išvados automatiškai neperkeliamos kitoms parduotuvėms ar sezonams.",
        "Mėnuo suteikia tik apytikslę laiko tvarką; nėra tikslių laiko žymų ir lankytojo identifikatoriaus.",
        "Pirkimų dalis mokyme ir teste skiriasi beveik du kartus, todėl tikimybės vėlesniais mėnesiais yra prasčiau kalibruotos.",
        "Pirminis mažas parametrų tinklas buvo vėliau papildytas 722 konfigūracijų tyrimu; nei vienas neįrodo, kad rasta geriausia įmanoma kiekvieno metodo versija.",
        "PageValues, sesijos trukmės, BounceRates ir ExitRates prieinamumas prognozės momentu turi būti audituojamas prieš realaus laiko naudojimą.",
        "Bootstrap intervalas aprašo šio testo ir jau išmokytų modelių neapibrėžtumą; jis neapima kitų mokymo pradžios reikšmių ar būsimų laikotarpių.",
    ])

    r.heading("9. Išvados")
    r.bullets([
        "Mokomi modeliai rikiavo pirkimus geriau už pastovų modelį (AP = 0,2066). RF turėjo didžiausią stebėtą pagrindinių modelių AP – 0,3411 – ir mažiausią Brier nuostolį – 0,1555.",
        "Jo AP persvara prieš logistinę regresiją buvo 0,0076, o 95 % bootstrap intervalas [−0,0113; 0,0284], todėl iš anksto nustatyta bent 0,02 persvaros hipotezė nepatvirtinta.",
        "Validacijoje parinktas 0,03 slenkstis aptiko 956 iš 976 pirkimų, bet sukūrė 3 004 klaidingus teigiamus atvejus. Aukštas recall gautas mažo precision kaina; prieš naudojimą reikia žinoti klaidų kainas arba veiksmų biudžetą.",
        "PageValues suteikė stiprų prognozavimo signalą ir esant vienodam RF lapo dydžiui, tačiau jo laikinė kilmė nepatvirtinta, todėl jis neįtrauktas į pagrindinę išvadą.",
        "Po pradinio testo atlikti RF parametrų ir literatūra motyvuoto XGBoost bandymai neparodė aiškaus AP pagerėjimo: parinktų variantų testo AP buvo 0,3297 ir 0,3324. Tai tiriamieji, o ne naujas nepriklausomas patvirtinimas.",
        "Vėlesniame 722 konfigūracijų tyrime Sep–Oct validacija pasirinko RF, kurio tiriamasis Nov–Dec AP 0,3325 nesiekė pradinio RF 0,3411. Plati paieška neatskleidė papildomo AP rezervo šiame skaidyme.",
        "Programa patikrinta 14 automatinių testų. Rezultatai pagrindžia offline/post-session tyrimą; realaus laiko taikymui reikia požymių prieinamumo audito ir naujo būsimo laikotarpio testo.",
    ])

    r.heading("10. AI naudojimo auditas")
    r.p("Darbas parengtas su ChatGPT Codex pagalba. AI padėjo rengti eksperimento kodą, dokumentaciją ir rezultatų patikras. Studentas pats paleido išplėstinį eksperimentą savo kompiuteryje; AI vėliau patikrino išsaugotus rezultatus. Gyvas gynimas ir dėstytojo nematytas bandymas dar neatlikti. Šiame skyriuje pateikiama audito santrauka, o pilna užklausų ir pakeitimų istorija saugoma docs/AI_ZURNALAS.md.")
    r.heading("10.1. Svarbiausios užklausos ir sprendimai", 2)
    r.p("Pagrindinės užklausos buvo įgyvendinti užduotį ir įkelti kodą bei dokumentaciją į GitHub; patikrinti testų įrodymus ir požymių prieinamumą laike; pridėti fiksuotų parametrų PageValues abliaciją; pagal dėstytojo pastabas atlikti papildomą metodų ir hiperparametrų tyrimą; prieš pateikimą sutikrinti rezultatus ir ataskaitą.")
    r.p("Priimti AI pasiūlymai: laikinis skaidymas pagal mėnesius, mokymo imtyje išmokstamas Pipeline, pirkimų dažnio baseline, RF ir gradientinis stiprinimas. PageValues pagrindiniame variante pašalintas, nes jo saugus prieinamumas prognozės momentu nepatvirtintas. Papildomas CPU XGBoost bandymas pasirinktas kaip literatūra motyvuotas palyginimas.")
    r.p("Atmesti pasiūlymai ar prielaidos: skelbti sudėtingesnį modelį savaime geresniu, rinktis slenkstį pagal testą ir vadinti rezultatą įrodyta realaus laiko sistema. SMOTE su požymių atranka ir stacking netaikyti, nes keistų daugiau eksperimento grandžių ir apsunkintų paaiškinimą. RF pranašumo teiginį pakeitė faktinė išvada: AP skirtumas tik 0,0076, o bootstrap intervalas apima 0.")
    r.heading("10.2. Aptiktos AI klaidos ir nepatikrintos prielaidos", 2)
    r.bullets([
        "Pradžioje AI nepatikrinęs nurodė scipy==1.16.3. Faktinės aplinkos scipy.__version__ patikra parodė 1.17.0; requirements.txt pataisytas. Tai priklausomybių aprašo klaida, ne rezultatų pasikeitimas.",
        "Buvo rizika sutapatinti AP su trapeciniu PR-AUC. Pastovaus modelio trapecinis plotas 0,6033 atrodė didelis, nors modelis sesijų neranguoja. Perskaičiavus AP gauta 0,2066; metrikos atskirtos, o test_constant_score_ap_equals_prevalence tikrina šią savybę.",
        "PageValues laikyti saugiu arba tikru nutekėjimu vien pagal jo pavadinimą būtų nepatikrinta prielaida. Tikrintas UCI aprašymas ir fiksuotų parametrų abliacija. Stiprus signalas išliko, tačiau CSV neturi tarpinių laiko kopijų, todėl saugus prieinamumas ir faktinis nutekėjimas neįrodyti.",
    ])
    r.heading("10.3. Patikros ir atsakomybės ribos", 2)
    r.p("Vartotojui paprašius vaizdinių paaiškinimų, AI vaizdų generavimo įrankiu sukurtos trys modelių principo iliustracijos. Priimtas jų naudojimas mokymosi ir gynimo paaiškinimui. Formulės, tikimybių vidurkinimas ir stiprinimo indėlių suma sutikrinti su modelių kodu; iliustraciniai skaičiai aiškiai atskirti nuo eksperimento rezultatų. Paveikslai nepakeičia tikro modelio patikros.")
    r.p("AI pasiūlymai tikrinti vykdant kodą: 14 unit testų baigėsi OK, RF formulės ir bibliotekos tikimybių skirtumas buvo 0. Metrikos ir porinis bootstrap perskaičiuoti iš išsaugotų prognozių, sutikrintos duomenų SHA256 ir skaidymo eilutės. Konfigūracijų pasirinkimas tikrintas pakeičiant dirbtinius test balus; validacijos pasirinkimas nesikeitė. Ataskaitos MD, DOCX ir PDF sutikrinti su rezultatų failais. Šios patikros nepakeičia studento pareigos suprasti kodą, paaiškinti sprendimus ir savarankiškai atlikti gyvą bandymą.")

    r.heading("11. Šaltiniai")
    sources = [
        "Abdullah-All-Tanvir, Khandokar, I. A., Islam, A. K. M. M., Islam, S., Shatabda, S. (2023). A gradient boosting classifier for purchase intention prediction of online shoppers. Heliyon, 9(4), e15163. https://doi.org/10.1016/j.heliyon.2023.e15163",
        "Breiman, L. (2001). Random Forests. Machine Learning, 45, 5–32. https://doi.org/10.1023/A:1010933404324",
        "Cawley, G. C., Talbot, N. L. C. (2010). On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation. Journal of Machine Learning Research, 11, 2079–2107. https://www.jmlr.org/papers/v11/cawley10a.html",
        "Friedman, J. H. (2001). Greedy Function Approximation: A Gradient Boosting Machine. The Annals of Statistics, 29(5), 1189–1232. https://doi.org/10.1214/aos/1013203451",
        "Kapoor, S., Narayanan, A. (2022). Leakage and the Reproducibility Crisis in ML-based Science. arXiv. https://doi.org/10.48550/arXiv.2207.07048",
        "Niculescu-Mizil, A., Caruana, R. (2005). Predicting Good Probabilities with Supervised Learning. ICML. https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf",
        "Pedregosa, F. ir kt. (2011). Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 12, 2825–2830. https://www.jmlr.org/papers/v12/pedregosa11a.html",
        "Saito, T., Rehmsmeier, M. (2015). The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets. PLOS ONE, 10(3), e0118432. https://doi.org/10.1371/journal.pone.0118432",
        "Satu, M. S., Islam, S. F. (2023). Modeling online customer purchase intention behavior applying different feature engineering and classification techniques. Discover Artificial Intelligence, 3, 36. https://doi.org/10.1007/s44163-023-00086-0",
        "Setyawan, I. B., Himawan, H. (2026). Optimasi Bayesian pada Gradient Boosting untuk Prediksi Niat Beli E-Commerce pada Dataset dengan Ketidakseimbangan Kelas. Building of Informatics, Technology and Science, 8(1), 51–61. https://doi.org/10.47065/bits.v8i1.9710",
        "Sakar, C. O., Kastro, Y. (2018). Online Shoppers Purchasing Intention Dataset. UCI Machine Learning Repository. https://doi.org/10.24432/C5F88Q",
        "Sakar, C. O. ir kt. (2019). Real-time prediction of online shoppers’ purchasing intention using multilayer perceptron and LSTM recurrent neural networks. Neural Computing and Applications, 31, 6893–6908. https://doi.org/10.1007/s00521-018-3523-0",
        "scikit-learn developers (n.d.-a). average_precision_score documentation (version 1.8). https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.average_precision_score.html",
        "scikit-learn developers (n.d.-b). DummyClassifier (version 1.8). https://scikit-learn.org/1.8/modules/generated/sklearn.dummy.DummyClassifier.html",
        "scikit-learn developers (n.d.-c). Logistic Regression (version 1.8). https://scikit-learn.org/1.8/modules/linear_model.html#logistic-regression",
        "scikit-learn developers (n.d.-d). RandomForestClassifier (version 1.8). https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.RandomForestClassifier.html",
        "scikit-learn developers (n.d.-e). HistGradientBoostingClassifier (version 1.8). https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html",
        "scikit-learn developers (n.d.-f). fbeta_score documentation (version 1.8). https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.fbeta_score.html",
    ]
    for i, source in enumerate(sources, 1):
        p = r.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Mm(8)
        p.paragraph_format.first_line_indent = Mm(-8)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(6)
        p.add_run(f"{i}. {source}").font.size = Pt(11)
        r.md.append(f"{i}. {source}")
    r.md.append("")
    r.save()


if __name__ == "__main__":
    build()
