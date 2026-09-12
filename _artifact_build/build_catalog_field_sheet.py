from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


OUTPUT = Path("C:/Users/Professional/Desktop/ASOTIA/asotia/outputs/pdf/asotia_field_catalog_sheet.pdf")
FONT_DIR = Path("C:/Windows/Fonts")

pdfmetrics.registerFont(TTFont("Arial", str(FONT_DIR / "arial.ttf")))
pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_DIR / "arialbd.ttf")))

ink = colors.HexColor("#172019")
gold = colors.HexColor("#E0B36B")
line = colors.HexColor("#9AA69C")
paper = colors.HexColor("#FFFDF8")

styles = {
    "title": ParagraphStyle("title", fontName="Arial-Bold", fontSize=17, leading=20, textColor=ink),
    "sub": ParagraphStyle("sub", fontName="Arial", fontSize=8.5, leading=11, textColor=colors.HexColor("#4E5B50")),
    "head": ParagraphStyle("head", fontName="Arial-Bold", fontSize=7.2, leading=8.5, textColor=colors.white, alignment=1),
    "cell": ParagraphStyle("cell", fontName="Arial", fontSize=7.6, leading=9, textColor=ink),
    "footer": ParagraphStyle("footer", fontName="Arial", fontSize=7.2, leading=9, textColor=colors.HexColor("#4E5B50")),
}


def p(text, style):
    return Paragraph(text, styles[style])


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=9 * mm,
        bottomMargin=8 * mm,
        title="Asotia Food Shop - первичный полевой лист каталога",
    )

    story = [
        p("Asotia Food Shop - первичный полевой лист каталога", "title"),
        Spacer(1, 2 * mm),
    ]

    meta = Table(
        [[p("Дата: ____________________", "cell"), p("Цех / зона: ______________________________", "cell"), p("Заполнил: ____________________", "cell")]],
        colWidths=[55 * mm, 105 * mm, 75 * mm],
    )
    meta.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, line),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([meta, Spacer(1, 3 * mm)])

    story.append(p(
        "Заполняйте по одной строке на товар или вариант. Статус: обведите нужное - новый / есть / снять. "
        "Если данные неизвестны, ставьте вопросительный знак: это лучше, чем оставить незамеченным.",
        "sub",
    ))
    story.append(Spacer(1, 3 * mm))

    headers = [
        "№", "Статус", "Товар / вариант", "Категория", "Цена", "Остаток", "Вес / объем / шт.",
        "Вид продукции", "Состав / осн. ингредиент", "Упаковка", "Фото", "Что уточнить / комментарий",
    ]
    data = [[p(h, "head") for h in headers]]
    for number in range(1, 9):
        data.append([
            p(str(number), "cell"), p("новый<br/>есть<br/>снять", "cell"), p("", "cell"), p("", "cell"), p("", "cell"),
            p("", "cell"), p("", "cell"), p("", "cell"), p("", "cell"), p("", "cell"), p("снято<br/>нет", "cell"), p("", "cell"),
        ])

    widths = [7 * mm, 16 * mm, 37 * mm, 23 * mm, 17 * mm, 16 * mm, 25 * mm, 25 * mm, 38 * mm, 23 * mm, 15 * mm, 35 * mm]
    grid = Table(data, colWidths=widths, rowHeights=[11 * mm] + [17.2 * mm] * 8, repeatRows=1)
    grid.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ink),
        ("GRID", (0, 0), (-1, -1), 0.45, line),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 1), (1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 2),
        ("BACKGROUND", (0, 1), (-1, -1), paper),
        ("BACKGROUND", (0, 1), (0, -1), gold),
    ]))
    story.extend([grid, Spacer(1, 3 * mm)])

    footer = Table(
        [[p("После обхода: перенести строки в таблицу ревизии. Характеристики берём из факта, а не из названия товара. Фото фиксируем отдельно для каждого нового или изменённого товара.", "footer")]],
        colWidths=[277 * mm],
    )
    footer.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), 0.6, gold),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(footer)
    doc.build(story)


if __name__ == "__main__":
    main()
