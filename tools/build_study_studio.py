"""Build source-grounded data for the W7-W10 multi-mode study studio."""

from pathlib import Path
from html import unescape
import importlib.util
import json
import re


ROOT = Path(__file__).parent
DIST = ROOT / "dist"


def clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()


def load_cheats():
    path = ROOT / "quiz2_cheat_data.py"
    spec = importlib.util.spec_from_file_location("quiz2_cheat_data", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CHEATS


def extract_quizzes(fragment: str):
    quizzes = []
    starts = list(re.finditer(r'<div class="quiz-box[^"]*"[^>]*>', fragment))
    for start in starts:
        depth, end = 1, start.end()
        for token in re.finditer(r'<div\b[^>]*>|</div>', fragment[start.end():], re.I):
            depth += -1 if token.group(0).lower() == "</div>" else 1
            if depth == 0:
                end = start.end() + token.start()
                break
        block = fragment[start.end():end]
        question_match = re.search(r"<h3>(.*?)</h3>", block, re.S)
        if not question_match:
            continue
        choices = []
        for correct, label in re.findall(
            r'<button[^>]*data-correct="(true|false)"[^>]*>(.*?)</button>', block, re.S
        ):
            choices.append({"text": clean(label), "correct": correct == "true"})
        explanation_match = re.search(r'<div class="quiz-explain">(.*?)</div>', block, re.S)
        quizzes.append({
            "question": clean(question_match.group(1)),
            "choices": choices,
            "explanation": clean(explanation_match.group(1)) if explanation_match else "",
        })
    return quizzes


raw = (DIST / "content.js").read_text(encoding="utf-8").strip()
course = json.loads(raw[len("const COURSE=") : -1])
cheats = load_cheats()

week_meta = {
    "w7": {
        "title": "Temporal Data · 时间数据",
        "question": "一个事实何时成立、何时被记录，以及怎样按时间查询？",
        "route": ["时间语义", "时间建模", "时间 SQL", "数组与时间序列"],
    },
    "w8": {
        "title": "Unstructured Data · 非结构化数据",
        "question": "怎样把文本、图像和元数据转换成可计算特征？",
        "route": ["数据类型", "文本特征", "图像特征", "元数据与工程"],
    },
    "w9": {
        "title": "Stream Processing · 流处理",
        "question": "事件怎样持续进入系统，并在乱序、迟到和故障下正确处理？",
        "route": ["流与消息", "窗口与状态", "时间与水位线", "Join 与框架"],
    },
    "w10": {
        "title": "Scalable Engineering · 可扩展数据工程",
        "question": "数据与负载增长时，系统怎样保持性能、正确性和可靠性？",
        "route": ["扩展指标", "分区复制", "分布式存储", "Spark/Flink"],
    },
}

result = {"weeks": [], "stats": {"lessons": 0, "quizzes": 0}}
for week in course["weeks"]:
    week_id = week["id"]
    output_week = {"id": week_id, **week_meta[week_id], "lessons": []}
    for lesson in week["lessons"]:
        item = cheats[lesson["id"]]
        quizzes = extract_quizzes(lesson["html"])
        output_week["lessons"].append({
            "id": lesson["id"],
            "title": lesson["title"],
            "summary": lesson["summary"],
            "trigger": item["trigger"],
            "decision": item["decision"],
            "facts": item.get("facts", []),
            "code": item.get("code", ""),
            "trap": item.get("trap", ""),
            "quizzes": quizzes,
        })
        result["stats"]["lessons"] += 1
        result["stats"]["quizzes"] += len(quizzes)
    result["weeks"].append(output_week)

(DIST / "study-data.js").write_text(
    "const STUDY_DATA=" + json.dumps(result, ensure_ascii=False, separators=(",", ":")) + ";\n",
    encoding="utf-8",
)
print(result["stats"])
