import re
import pdfplumber
from collections import defaultdict

from src.configs.config import INSTITUTES

TIME_ICONS = {
    "09:00": "🕘",
    "10:55": "🕥",
    "13:00": "🕐",
    "14:55": "🕔",
    "16:50": "🕔",
    "18:30": "🕕",
    "20:15": "🕗",
}
PAIR_TIMES = {
    "09:00": "1 пара",
    "10:55": "2 пара",
    "13:00": "3 пара",
    "14:55": "4 пара",
    "16:50": "5 пара",
    "18:30": "6 пара",
    "20:15": "7 пара",
}


def _get_default_pdf_path() -> str:
    for institute in INSTITUTES.values():
        for pdf_path in institute["courses"].values():
            return pdf_path
    return ""


def split_lessons(cell: str) -> list[str]:
    lines = [l.strip() for l in cell.strip().split("\n") if l.strip()]
    blocks, current = [], []
    for line in lines:
        if re.match(r'^(лек|пр|сем)\.', line) and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def parse_schedule(pdf_path: str = "") -> list[dict]:
    if not pdf_path:
        pdf_path = _get_default_pdf_path()
    schedule = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in (page.extract_tables() or []):
                if not table or len(table[0]) < 3:
                    continue
                groups = table[0][2:]
                current_day = current_time = ""
                for row in table[1:]:
                    if not row or len(row) < 3:
                        continue
                    day_cell = (row[0] or "").replace("\n", "").strip()
                    if day_cell in ("ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА",
                                    "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА"):
                        current_day = day_cell
                    time_cell = (row[1] or "").replace("\n", " ").strip()
                    if time_cell:
                        current_time = time_cell
                    if not current_day or not current_time:
                        continue
                    for i, cell in enumerate(row[2:]):
                        if not cell or not cell.strip() or i >= len(groups):
                            continue
                        group = (groups[i] or "").strip()
                        if not group:
                            continue
                        if len(re.findall(r'(?<!\w)([А-ЯA-Z])(?!\w)', cell)) > 8:
                            continue
                        for lesson in split_lessons(cell):
                            schedule.append({
                                "day": current_day,
                                "time": current_time,
                                "group": group,
                                "lesson": lesson,
                            })
    return schedule


def get_all_groups(schedule: list[dict]) -> list[str]:
    return sorted(set(e["group"] for e in schedule))


def get_schedule(schedule: list[dict], group: str, day: str | None = None) -> list[dict]:
    return [
        e for e in schedule
        if e["group"] == group and (day is None or e["day"] == day)
    ]


def _parse_lesson(lesson: str) -> dict:
    lines = [l.strip() for l in lesson.strip().split("\n") if l.strip()]

    type_map = {"лек": "лек", "пр": "пр", "сем": "сем"}
    lesson_type = ""
    subject = ""

    first = lines[0] if lines else ""
    for prefix, name in type_map.items():
        if first.startswith(f"{prefix}."):
            lesson_type = name
            subject = first[len(prefix) + 1:].strip()
            break
    else:
        subject = first

    teacher = ""
    room = ""

    if len(lines) > 1:
        rest = " ".join(lines[1:])
        parts = rest.rsplit(" ", 1)
        if len(parts) == 2 and re.match(r'^\d+[-–][\w]+$', parts[1]):
            teacher = parts[0].strip()
            room = parts[1].strip()
        else:
            teacher = rest

    return {
        "type": lesson_type,
        "subject": subject,
        "teacher": teacher,
        "room": room,
    }


def format_schedule(entries: list[dict]) -> str:
    if not entries:
        return "Занятий нет."

    type_icon = {"лек": "📘", "пр": "✏️", "сем": "📋"}
    type_short = {"лек": "л", "пр": "пр", "сем": "сем"}

    by_time = defaultdict(list)
    for e in entries:
        time = e["time"].strip()
        time = re.sub(r'(\d{2})\.(\d{2})', r'\1:\2', time)
        time = re.sub(r'\s*-\s*', '–', time)
        by_time[time].append(e)

    blocks = []
    for time, slot_entries in by_time.items():
        start = time.split("–")[0].strip()
        clock = TIME_ICONS.get(start, "🕐")
        pair_label = PAIR_TIMES.get(start, "")
        header = f"{clock} {time}"
        if pair_label:
            header += f"  ({pair_label})"
        lines = [header]
        for e in slot_entries:
            p = _parse_lesson(e["lesson"])
            icon = type_icon.get(p["type"], "📘")
            t = type_short.get(p["type"], p["type"])
            subject = p["subject"]
            if t:
                subject += f" ({t})"
            part = f" {icon} {subject}"
            if p["teacher"]:
                part += f" - {p['teacher']}"
            if p["room"]:
                part += f" | {p['room']}"
            lines.append(part)
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def get_course(group: str) -> int:
    match = re.search(r'-(\d{2})$', group)
    if match:
        year = int(match.group(1))
        course_map = {25: 1, 24: 2, 23: 3, 22: 4}
        return course_map.get(year, 0)
    return 0


def group_by_course(groups: list[str]) -> dict[int, list[str]]:
    result: dict[int, list[str]] = {}
    for g in groups:
        course = get_course(g)
        result.setdefault(course, []).append(g)
    return dict(sorted(result.items()))


def normalize_group(text: str) -> str | None:
    text = text.upper().strip()

    match = re.match(r'^([А-ЯA-Z]+)-?([А-ЯA-Z]+)\s*-?\s*(\d{3})$', text)
    if match:
        return f"{match.group(1)}-{match.group(2)} {match.group(3)}"

    match = re.match(r'^([А-ЯA-Z]+)\s*-?\s*(\d{2})\s*-?\s*(\d{2})$', text)
    if match:
        return f"{match.group(1)} {match.group(2)}-{match.group(3)}"

    return None
