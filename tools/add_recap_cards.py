from pathlib import Path
from html import escape
import json
import re
from quiz2_cheat_data import CHEATS


ROOT = Path(__file__).parents[1]
CONTENT = ROOT / "content.js"
raw = CONTENT.read_text(encoding="utf-8").strip()
course = json.loads(raw[len("const COURSE=") : -1])


def recap(item: dict) -> str:
    title = escape(item["title"])
    lesson_id = item.get("id")
    cheat = CHEATS.get(lesson_id)
    if not cheat:
        summary = escape(item["summary"])
        goals = [escape(goal) for goal in item.get("goals", [])]
        return f'''<section class="lesson-section recap-card" data-recap="true">
<div class="recap-label">📌 EXAM CHEATSHEET · 考场速查</div>
<h2>{title}</h2>
<div class="recap-prompt"><b>直接结论：</b>{summary}</div>
<button class="recap-toggle" type="button" aria-expanded="false">展开本节考点</button>
<div class="recap-answer" hidden><ul>{''.join(f'<li>{g}</li>' for g in goals)}</ul></div>
</section>'''

    trigger = escape(cheat["trigger"])
    decision = escape(cheat["decision"])
    facts = "".join(f"<li>{escape(fact)}</li>" for fact in cheat["facts"])
    code = cheat.get("code")
    code_html = f'<div class="exam-code"><b>可抄写代码 / 公式</b><pre>{escape(code)}</pre></div>' if code else ""
    trap = escape(cheat["trap"])
    return f'''<section class="lesson-section recap-card" data-recap="true">
<div class="recap-label">📌 EXAM CHEATSHEET · 考场速查</div>
<h2>{title}</h2>
<div class="exam-trigger"><b>题干出现：</b>{trigger}</div>
<div class="recap-prompt"><b>直接结论：</b>{decision}</div>
<button class="recap-toggle" type="button" aria-expanded="false">展开完整考场答案</button>
<div class="recap-answer" hidden>
<div class="exam-grid">
<div class="exam-must"><b>必背规则</b><ul>{facts}</ul></div>
{code_html}
</div>
<div class="exam-trap"><b>⚠ 常见陷阱：</b>{trap}</div>
</div>
</section>'''


pattern = re.compile(
    r'<section class="lesson-section recap-card" data-recap="true">.*?</section>',
    re.S,
)
items = [lesson for week in course["weeks"] for lesson in week["lessons"]]

for item in items:
    item["html"] = pattern.sub("", item["html"]).rstrip() + recap(item)

CONTENT.write_text(
    "const COURSE=" + json.dumps(course, ensure_ascii=False, separators=(",", ":")) + ";\n",
    encoding="utf-8",
)
print(f"Added {len(items)} recap cards")
