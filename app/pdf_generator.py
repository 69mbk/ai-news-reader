from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

FONT, BOLD = "Helvetica", "Helvetica-Bold"
try:
    d = "/usr/share/fonts/truetype/dejavu/"
    pdfmetrics.registerFont(TTFont("DejaVu", d + "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", d + "DejaVuSans-Bold.ttf"))
    FONT, BOLD = "DejaVu", "DejaVu-Bold"
except Exception:
    pass

IMG_DIR = Path("/opt/ai-news-reader/storage/img")
MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
          "août", "septembre", "octobre", "novembre", "décembre"]
DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
CAT_COLORS = {"Maroc": "#b3202a", "Sciences & Espace": "#1d4e89", "IA & Technologie": "#6a2c91",
              "Cybersécurité & Réseaux": "#0b6e4f", "Monde & Économie": "#8a5a00", "Sport": "#c25400", "Tendances Reddit": "#d9480f"}
READ_LEAD = "Lire l'article original"
ACCENT = colors.HexColor("#8b1a1a")
INK = colors.HexColor("#1a1a1a")
GREY = colors.HexColor("#666666")
PAPER = colors.HexColor("#f4f1ec")

W, H = A4
M = 1.6 * cm
GAP = 0.6 * cm
FULL = W - 2 * M
COL = (FULL - GAP) / 2


def st(name, **kw):
    base = dict(fontName=FONT, fontSize=9.5, leading=13.5, textColor=INK)
    base.update(kw)
    return ParagraphStyle(name, **base)


S_BRAND = st("brand", fontName=BOLD, fontSize=34, leading=38, textColor=colors.white, alignment=1)
S_DATE = st("date", fontSize=11, textColor=colors.white, alignment=1)
S_BOXH = st("boxh", fontName=BOLD, fontSize=11, textColor=ACCENT, spaceAfter=4)
S_BOX = st("box", fontSize=10, leading=14, spaceAfter=3)
S_KICK = st("kick", fontName=BOLD, fontSize=8, textColor=ACCENT, spaceBefore=6)
S_LEAD_T = st("leadt", fontName=BOLD, fontSize=19, leading=23, spaceBefore=2, spaceAfter=4)
S_LEAD_B = st("leadb", fontSize=10.5, leading=15)
S_SEC = st("sec", fontName=BOLD, fontSize=12, textColor=colors.white)
S_H = st("h", fontName=BOLD, fontSize=11.5, leading=14.5, spaceBefore=2, spaceAfter=2)
S_B = st("b", fontSize=9.2, leading=13)
S_META = st("meta", fontSize=7.5, leading=10, textColor=GREY, spaceBefore=2, spaceAfter=10)
S_BRIEF = st("brief", fontSize=8.6, leading=12, spaceAfter=5)
S_SUB = st("sub", fontName=BOLD, fontSize=8, textColor=GREY, spaceBefore=6, spaceAfter=4)


def pic(name, width, max_h):
    if not name:
        return None
    p = IMG_DIR / name
    if not p.exists():
        return None
    try:
        iw, ih = ImageReader(str(p)).getSize()
    except Exception:
        return None
    h = width * ih / iw
    if h > max_h:
        width, h = width * max_h / h, max_h
    return Image(str(p), width=width, height=h)


def link(a, label, color="#8b1a1a"):
    url = escape(a["url"], {'"': "&quot;"})
    return f'<a href="{url}" color="{color}">{label}</a>'


def sec_header(name):
    t = Table([[Paragraph(escape(name).upper(), S_SEC)]], colWidths=[COL])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(CAT_COLORS.get(name, "#333333"))),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
    return t


def box(flow, width, bg=PAPER):
    t = Table([[flow]], colWidths=[width])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(GREY)
    canvas.drawCentredString(W / 2, 0.9 * cm, f"AI Daily News · page {doc.page}")
    canvas.restoreState()


def generate_pdf(data, path):
    now = datetime.now()
    date_txt = f"{DAYS[now.weekday()].capitalize()} {now.day} {MONTHS[now.month - 1]} {now.year}"
    arts = data["articles"]
    lead = next((a for a in arts if a["tier"] == "lead"), None)

    story = []
    banner = Table([[[Paragraph("AI DAILY NEWS", S_BRAND), Paragraph(date_txt, S_DATE)]]], colWidths=[FULL])
    banner.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT),
                                ("TOPPADDING", (0, 0), (-1, -1), 14), ("BOTTOMPADDING", (0, 0), (-1, -1), 14)]))
    story += [banner, Spacer(1, 10)]

    if data.get("top5"):
        items = [Paragraph("L'ESSENTIEL EN 5 POINTS", S_BOXH)]
        items += [Paragraph(f"<b>{i}.</b> {escape(t)}", S_BOX) for i, t in enumerate(data["top5"], 1)]
        story += [box(items, FULL), Spacer(1, 10)]

    if lead:
        p = pic(lead.get("image"), FULL, 7.5 * cm)
        if p:
            story.append(p)
        story += [Paragraph(f"À LA UNE · {escape(lead['category']).upper()}", S_KICK),
                  Paragraph(escape(lead["title"]), S_LEAD_T),
                  Paragraph(escape(lead["summary"]), S_LEAD_B),
                  Paragraph(f'{escape(lead["source"])} · {lead["published"][:10]} · '
                            f'{link(lead, READ_LEAD)}', S_META)]

    story += [NextPageTemplate("cols"), PageBreak()]

    cats = [c for c in CAT_COLORS if any(a["category"] == c and a is not lead for a in arts)]
    for cat in cats:
        story += [sec_header(cat), Spacer(1, 6)]
        rows = [a for a in arts if a["category"] == cat and a is not lead]
        for a in [r for r in rows if r["tier"] == "story"]:
            block = []
            p = pic(a.get("image"), COL, 5 * cm)
            if p:
                block += [p, Spacer(1, 3)]
            block += [Paragraph(escape(a["title"]), S_H), Paragraph(escape(a["summary"]), S_B),
                      Paragraph(f'{escape(a["source"])} · {a["published"][:10]} · {link(a, "Lire la suite")}', S_META)]
            story.append(KeepTogether(block))
        briefs = [r for r in rows if r["tier"] == "brief"]
        if briefs:
            story.append(Paragraph("EN BREF", S_SUB))
            for a in briefs:
                story.append(Paragraph(
                    f'▪ <b>{link(a, escape(a["title"]), "#1a1a1a")}</b> — {escape(a["summary"])} '
                    f'<font color="#666666">({escape(a["source"])})</font>', S_BRIEF))
        story.append(Spacer(1, 10))

    if data.get("fact"):
        f = data["fact"]
        story.append(KeepTogether([box([
            Paragraph("LE SAVIEZ-VOUS ?", S_BOXH),
            Paragraph(escape(f["text"]), S_B),
            Paragraph(f'{escape(f["source"])} · {link(f, "source")}', S_META)], COL, colors.HexColor("#fff4d6"))]))

    doc = BaseDocTemplate(path, pagesize=A4, title="AI Daily News", author="AI Daily News")
    cover = Frame(M, M, FULL, H - 2 * M, id="cover", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    cols = [Frame(M + i * (COL + GAP), M, COL, H - M - 1.6 * cm, id=f"c{i}",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0) for i in range(2)]
    doc.addPageTemplates([PageTemplate(id="cover", frames=[cover], onPage=footer),
                          PageTemplate(id="cols", frames=cols, onPage=footer)])
    doc.build(story)
    return doc.page
