"""Build a two-sided A4 answer map covering every W7-W10 lesson and website quiz."""

from pathlib import Path
import html
import importlib.util
import json
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).parent
SITE = ROOT / "quiz2_visual_website"
OUT = ROOT / "output" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)
OUTPUT = OUT / "COMP5339_Quiz2_Complete_W7-W10_Double_Sided_Answer_Map.pdf"
ALIAS = OUT / "COMP5339_Quiz2_W7-W10_A4_Double_Sided_Cheatsheet.pdf"
RAPID = OUT / "COMP5339_Quiz2_Complete_Rapid_Review.pdf"

pdfmetrics.registerFont(TTFont("YaHei", r"C:\Windows\Fonts\msyh.ttc"))
pdfmetrics.registerFont(TTFont("YaHeiBold", r"C:\Windows\Fonts\msyhbd.ttc"))
pdfmetrics.registerFont(TTFont("Consolas", r"C:\Windows\Fonts\consola.ttf"))

PAGE = landscape(A4)
INK = colors.HexColor("#17222B")
BLUE = colors.HexColor("#2359A8")
PALE = colors.HexColor("#F8FAFC")
LINE = colors.HexColor("#D8E0E7")
MUTED = colors.HexColor("#46545E")
TRAP = colors.HexColor("#8A3415")


def load_cheats():
    path = SITE / "quiz2_cheat_data.py"
    spec = importlib.util.spec_from_file_location("quiz2_cheat_data", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CHEATS


def clean(value):
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def load_course_and_quizzes():
    raw = (SITE / "dist" / "content.js").read_text(encoding="utf-8").strip()
    course = json.loads(raw[len("const COURSE=") : -1])
    titles, answers = {}, {}
    for week in course["weeks"]:
        for lesson in week["lessons"]:
            lesson_id = lesson["id"]
            titles[lesson_id] = lesson["title"]
            chunks = re.split(r'<div class="quiz-box[^>]*>', lesson["html"])[1:]
            lesson_answers = []
            for chunk in chunks:
                correct = [
                    clean(value)
                    for value in re.findall(
                        r'<button[^>]*data-correct="true"[^>]*>(.*?)</button>',
                        chunk,
                        re.S,
                    )
                ]
                if correct:
                    lesson_answers.append(" / ".join(correct))
            answers[lesson_id] = lesson_answers
    return titles, answers


def esc(value):
    return html.escape(str(value), quote=False).replace("\n", "<br/>")


def split_week(ids):
    middle = (len(ids) + 1) // 2
    return ids[:middle], ids[middle:]


def styles(font_size):
    return {
        "body": ParagraphStyle(
            "body", fontName="YaHei", fontSize=font_size,
            leading=font_size * 1.16, textColor=INK,
        ),
        "title": ParagraphStyle(
            "title", fontName="YaHeiBold", fontSize=font_size + 0.65,
            leading=(font_size + 0.65) * 1.10, textColor=colors.white,
            leftIndent=3,
        ),
    }


def card_html(lesson_id, title, cheat, quiz_answers):
    number = lesson_id.replace("w", "W").replace("-", ".")
    parts = [f"<b>题干:</b> {esc(cheat['trigger'])}", f"<b>结论:</b> {esc(cheat['decision'])}"]
    parts.append("<b>规则:</b> " + esc("；".join(cheat.get("facts", []))))
    if quiz_answers:
        labelled = "；".join(f"Q{i+1}={answer}" for i, answer in enumerate(quiz_answers))
        parts.append(f"<font color='#1D6B45'><b>网站题答案:</b> {esc(labelled)}</font>")
    if cheat.get("code"):
        parts.append(f"<font name='Consolas' color='#174D37'><b>式/码:</b> {esc(cheat['code'])}</font>")
    if cheat.get("trap"):
        parts.append(f"<font color='#8A3415'><b>⚠</b> {esc(cheat['trap'])}</font>")
    return f"{number} {title}", "<br/>".join(parts)


def card_height(body_html, width, sty):
    paragraph = Paragraph(body_html, sty["body"])
    _, body_h = paragraph.wrap(width - 8, 1000)
    return 13 + body_h + 5


def draw_card(canvas, x, top, width, title, body_html, sty):
    height = card_height(body_html, width, sty)
    canvas.setFillColor(PALE)
    canvas.setStrokeColor(LINE)
    canvas.roundRect(x, top - height, width, height, 3, fill=1, stroke=1)
    canvas.setFillColor(BLUE)
    canvas.roundRect(x, top - 13, width, 13, 3, fill=1, stroke=0)
    title_p = Paragraph(esc(title), sty["title"])
    title_p.wrap(width - 6, 12)
    title_p.drawOn(canvas, x + 2, top - 11)
    body_p = Paragraph(body_html, sty["body"])
    _, body_h = body_p.wrap(width - 8, 1000)
    body_p.drawOn(canvas, x + 4, top - 16 - body_h)
    return height


def plan_columns(cheats):
    weeks = {}
    for week in ("w7", "w8", "w9", "w10"):
        ids = sorted(
            (lesson_id for lesson_id in cheats if lesson_id.startswith(week + "-")),
            key=lambda value: int(value.split("-")[1]),
        )
        weeks[week] = split_week(ids)
    return [
        [("W7", weeks["w7"][0]), ("W7", weeks["w7"][1]), ("W8", weeks["w8"][0]), ("W8", weeks["w8"][1])],
        [("W9", weeks["w9"][0]), ("W9", weeks["w9"][1]), ("W10", weeks["w10"][0]), ("W10", weeks["w10"][1])],
    ]


def build(path):
    cheats = load_cheats()
    titles, answers = load_course_and_quizzes()
    page_columns = plan_columns(cheats)
    canvas = Canvas(str(path), pagesize=PAGE)
    width, height = PAGE
    margin, gap, header, footer = 11, 5, 31, 10
    column_width = (width - margin * 2 - gap * 3) / 4

    chosen = None
    for size in (6.2, 6.0, 5.8, 5.6, 5.4, 5.2):
        sty = styles(size)
        fits = True
        for columns in page_columns:
            for _, lesson_ids in columns:
                used = 0
                for lesson_id in lesson_ids:
                    title, body = card_html(lesson_id, titles[lesson_id], cheats[lesson_id], answers[lesson_id])
                    used += card_height(body, column_width, sty) + 3
                if used > height - header - footer:
                    fits = False
        if fits:
            chosen = (size, sty)
            break
    if chosen is None:
        raise RuntimeError("Complete answer map does not fit two pages")
    font_size, sty = chosen

    for page_no, columns in enumerate(page_columns, 1):
        canvas.setFillColor(colors.HexColor("#F3F0E8"))
        canvas.rect(0, 0, width, height, fill=1, stroke=0)
        canvas.setFillColor(INK)
        canvas.setFont("YaHeiBold", 13)
        canvas.drawString(margin, height - 18, "COMP5339 Quiz 2 完整速答图")
        canvas.setFillColor(MUTED)
        canvas.setFont("YaHei", 6.3)
        canvas.drawRightString(width - margin, height - 17, "W7-W10 每节规则 + 71 道网站自测正确答案 + 代码/陷阱")
        for column_index, (week_label, lesson_ids) in enumerate(columns):
            x = margin + column_index * (column_width + gap)
            top = height - header
            for lesson_id in lesson_ids:
                title, body = card_html(lesson_id, titles[lesson_id], cheats[lesson_id], answers[lesson_id])
                used = draw_card(canvas, x, top, column_width, title, body, sty)
                top -= used + 3
            canvas.setFillColor(MUTED)
            canvas.setFont("YaHei", 5.4)
            canvas.drawCentredString(x + column_width / 2, 4, f"{week_label} · 字号 {font_size:.1f}pt")
        canvas.setFillColor(MUTED)
        canvas.setFont("YaHei", 5.7)
        canvas.drawRightString(width - margin, 4, f"第 {page_no}/2 页 · A4横向 · 实际大小 · 双面短边翻转 · 2026-10-22")
        canvas.showPage()
    canvas.save()

    # Make the complete map the default Quiz 2 A4 download as requested.
    ALIAS.write_bytes(path.read_bytes())
    print(path)
    print(ALIAS)


def build_rapid_review(path):
    """Create a readable companion with the same complete coverage as the two-page map."""
    cheats = load_cheats()
    titles, answers = load_course_and_quizzes()
    doc = SimpleDocTemplate(
        str(path), pagesize=A4, rightMargin=28, leftMargin=28,
        topMargin=32, bottomMargin=30,
        title="COMP5339 Quiz 2 Complete Rapid Review",
        author="COMP5339 study materials",
    )
    usable_width = A4[0] - 56
    styles = {
        "cover": ParagraphStyle("cover", fontName="YaHeiBold", fontSize=24, leading=30, textColor=INK, spaceAfter=12),
        "week": ParagraphStyle("week", fontName="YaHeiBold", fontSize=18, leading=22, textColor=BLUE, spaceAfter=8),
        "lesson": ParagraphStyle("lesson", fontName="YaHeiBold", fontSize=12.5, leading=16, textColor=colors.white),
        "body": ParagraphStyle("rapidbody", fontName="YaHei", fontSize=9.2, leading=13.2, textColor=INK),
        "small": ParagraphStyle("rapidsmall", fontName="YaHei", fontSize=8.3, leading=11.5, textColor=MUTED),
        "code": ParagraphStyle("rapidcode", fontName="Consolas", fontSize=8, leading=10.5, textColor=colors.HexColor("#123C2B")),
        "footer": ParagraphStyle("rapidfooter", fontName="YaHei", fontSize=7, leading=9, textColor=MUTED),
    }
    story = [
        Paragraph("COMP5339 Quiz 2<br/>W7–W10 完整速答版", styles["cover"]),
        Paragraph(
            "用途：先用本版理解与复习，再把双面 A4 速答图带进考场。覆盖网站全部 48 节、71 道自测题的正确答案、关键公式、代码和常见陷阱。每节按“看到什么题 → 选什么结论 → 为什么”组织。",
            styles["body"],
        ),
        Spacer(1, 10),
        Table(
            [["题型", "最快判断法"],
             ["定义/选择题", "先找题干触发词，再对应本节“结论”和“规则”。"],
             ["代码题", "先确定输入/输出粒度，再逐句套用“式/码”。"],
             ["多选题", "逐项验证；不要因为一句正确就忽略其他正确项。"],
             ["情境题", "先判断题目关心正确性、速度、扩展、时间还是容错。"]],
            colWidths=[95, usable_width - 95],
            style=TableStyle([
                ("FONTNAME", (0,0), (-1,0), "YaHeiBold"),
                ("FONTNAME", (0,1), (-1,-1), "YaHei"),
                ("FONTSIZE", (0,0), (-1,-1), 9),
                ("LEADING", (0,0), (-1,-1), 12),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#DCE9FA")),
                ("GRID", (0,0), (-1,-1), .5, LINE),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING", (0,0), (-1,-1), 6),
                ("RIGHTPADDING", (0,0), (-1,-1), 6),
                ("TOPPADDING", (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ]),
        ),
        PageBreak(),
    ]

    week_names = {
        "w7": "W7 · Temporal Data 时间数据",
        "w8": "W8 · Unstructured Data 非结构化数据",
        "w9": "W9 · Stream Processing 流处理",
        "w10": "W10 · Scalable Data Engineering 可扩展数据工程",
    }
    for week_index, week in enumerate(("w7", "w8", "w9", "w10")):
        if week_index:
            story.append(PageBreak())
        story.append(Paragraph(week_names[week], styles["week"]))
        lesson_ids = sorted(
            (lesson_id for lesson_id in cheats if lesson_id.startswith(week + "-")),
            key=lambda value: int(value.split("-")[1]),
        )
        for lesson_id in lesson_ids:
            cheat = cheats[lesson_id]
            number = lesson_id.replace("w", "W").replace("-", ".")
            labelled = "；".join(f"Q{i+1}={answer}" for i, answer in enumerate(answers[lesson_id]))
            header = Table(
                [[Paragraph(f"{number} {esc(titles[lesson_id])}", styles["lesson"])]],
                colWidths=[usable_width],
                style=TableStyle([
                    ("BACKGROUND", (0,0), (-1,-1), BLUE),
                    ("LEFTPADDING", (0,0), (-1,-1), 7),
                    ("RIGHTPADDING", (0,0), (-1,-1), 7),
                    ("TOPPADDING", (0,0), (-1,-1), 5),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
                ]),
            )
            rows = [
                [Paragraph("题干触发词", styles["small"]), Paragraph(esc(cheat["trigger"]), styles["body"])],
                [Paragraph("直接结论", styles["small"]), Paragraph(esc(cheat["decision"]), styles["body"])],
                [Paragraph("作答规则", styles["small"]), Paragraph(esc("；".join(cheat.get("facts", []))), styles["body"])],
            ]
            if labelled:
                rows.append([Paragraph("网站题答案", styles["small"]), Paragraph(f"<font color='#1D6B45'><b>{esc(labelled)}</b></font>", styles["body"])])
            if cheat.get("code"):
                rows.append([Paragraph("公式/代码", styles["small"]), Paragraph(esc(cheat["code"]), styles["code"])])
            if cheat.get("trap"):
                rows.append([Paragraph("常见陷阱", styles["small"]), Paragraph(f"<font color='#8A3415'>{esc(cheat['trap'])}</font>", styles["body"])])
            detail = Table(
                rows, colWidths=[78, usable_width - 78],
                style=TableStyle([
                    ("GRID", (0,0), (-1,-1), .4, LINE),
                    ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#EEF3F7")),
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("LEFTPADDING", (0,0), (-1,-1), 6),
                    ("RIGHTPADDING", (0,0), (-1,-1), 6),
                    ("TOPPADDING", (0,0), (-1,-1), 4),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ]),
            )
            story.extend([KeepTogether([header, detail]), Spacer(1, 9)])

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("YaHei", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(28, 17, "COMP5339 Quiz 2 · 完整速答版 · 2026-10-22")
        canvas.drawRightString(A4[0] - 28, 17, f"第 {document.page} 页")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(path)


if __name__ == "__main__":
    build(OUTPUT)
    build_rapid_review(RAPID)

