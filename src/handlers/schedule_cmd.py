import os
from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.configs.config import INSTITUTES
from src.db.db_operations import get_user_info
from src.utils.pdf_parser import (
    parse_schedule,
    get_all_groups,
    get_schedule,
    format_schedule,
    normalize_group,
)

router = Router()

DAYS = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА"]
DAY_SHORT = {
    "ПОНЕДЕЛЬНИК": "Пн",
    "ВТОРНИК": "Вт",
    "СРЕДА": "Ср",
    "ЧЕТВЕРГ": "Чт",
    "ПЯТНИЦА": "Пт",
    "СУББОТА": "Сб",
}

_schedule_cache: dict[str, list[dict]] = {}
_group_to_pdf: dict[str, str] = {}


def build_cache() -> None:
    for institute in INSTITUTES.values():
        for pdf_path in institute["courses"].values():
            if not os.path.exists(pdf_path):
                continue
            try:
                schedule = parse_schedule(pdf_path)
                _schedule_cache[pdf_path] = schedule
                for group in get_all_groups(schedule):
                    _group_to_pdf[group] = pdf_path
                print(f"[cache] Загружен: {pdf_path}")
            except Exception as e:
                print(f"[cache] Ошибка при парсинге {pdf_path}: {e}")


def _find_pdf_for_group(group: str) -> str | None:
    return _group_to_pdf.get(group)


def _get_schedule_cached(pdf_path: str) -> list[dict]:
    return _schedule_cache.get(pdf_path, [])


class ScheduleStates(StatesGroup):
    choosing_institute = State()
    choosing_course = State()
    waiting_for_group = State()


def institutes_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, data in INSTITUTES.items():
        builder.button(text=data["name"], callback_data=f"institute:{key}")
    builder.adjust(1)
    return builder.as_markup()


def courses_keyboard(institute_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    courses = INSTITUTES[institute_key]["courses"]
    for course_num in sorted(courses.keys()):
        builder.button(text=f"{course_num} курс", callback_data=f"course:{course_num}")
    builder.button(text="← Назад", callback_data="back:institutes")
    builder.adjust(2)
    return builder.as_markup()


def days_keyboard(group: str, active_day: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for day in DAYS:
        label = f"• {DAY_SHORT[day]} •" if day == active_day else DAY_SHORT[day]
        builder.button(text=label, callback_data=f"day:{group}:{day}")
    builder.adjust(3)
    return builder.as_markup()


def _get_group_examples(pdf_path: str) -> str:
    try:
        schedule = _get_schedule_cached(pdf_path)
        groups = get_all_groups(schedule)
        return ", ".join(groups[:2]) if groups else "ДЭ 15-25"
    except Exception:
        return "ДЭ 15-25"


def _format_day(schedule: list[dict], group: str, day: str) -> str:
    entries = get_schedule(schedule, group=group, day=day)
    if not entries:
        return f"📆 <b>{day}</b>\n\nЗанятий нет."
    text = f"📆 <b>{day.capitalize()}</b>\n\n"
    text += format_schedule(entries)
    text += "\n\n⚠️ Верхняя / нижняя неделя."
    return text


@router.message(Command("cancel"))
async def handle_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активного режима.")
        return
    await state.clear()
    await message.answer("Действие отменено. Для просмотра расписания введите /schedule")


@router.message(Command("schedule"))
async def handle_schedule(message: Message, state: FSMContext):
    user_info = await get_user_info(message.from_user.id)
    if not user_info:
        await message.answer(
            "⚠️ <b>Не удалось обработать ваши данные</b>\n\n"
            "Пожалуйста, перезапустите бота и попробуйте ещё раз.",
            parse_mode=ParseMode.HTML,
        )
        return
    await state.set_state(ScheduleStates.choosing_institute)
    await message.answer(
        "Выберите институт:",
        reply_markup=institutes_keyboard()
    )


@router.callback_query(ScheduleStates.choosing_institute, F.data.startswith("institute:"))
async def on_institute_selected(call: CallbackQuery, state: FSMContext):
    institute_key = call.data.split(":")[1]
    if institute_key not in INSTITUTES:
        await call.answer("Институт не найден.", show_alert=True)
        return
    await state.update_data(institute=institute_key)
    await state.set_state(ScheduleStates.choosing_course)
    institute_name = INSTITUTES[institute_key]["name"]
    await call.message.edit_text(
        f"<b>🏛️ {institute_name}</b>\n\nВыберите курс:",
        parse_mode=ParseMode.HTML,
        reply_markup=courses_keyboard(institute_key)
    )


@router.callback_query(ScheduleStates.choosing_course, F.data.startswith("course:"))
async def on_course_selected(call: CallbackQuery, state: FSMContext):
    course_num = int(call.data.split(":")[1])
    data = await state.get_data()
    institute_key = data.get("institute")
    if not institute_key or institute_key not in INSTITUTES:
        await call.answer("⚠️ Что-то пошло не так. Начните заново.", show_alert=True)
        await state.clear()
        return
    courses = INSTITUTES[institute_key]["courses"]
    if course_num not in courses:
        await call.answer("❌ Курс не найден.", show_alert=True)
        return
    pdf_path = courses[course_num]
    if not os.path.exists(pdf_path):
        await call.answer(
            f"⚠️ Файл расписания для {course_num} курса ещё не загружен.",
            show_alert=True
        )
        return
    await state.update_data(course=course_num, pdf_path=pdf_path)
    await state.set_state(ScheduleStates.waiting_for_group)
    examples = _get_group_examples(pdf_path)
    await call.message.edit_text(
        f"<b>{course_num} курс</b>\n\n"
        f"Введите номер своей группы.\n"
        f"<i>Примеры: {examples}</i>",
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(ScheduleStates.choosing_course, F.data == "back:institutes")
async def on_back_to_institutes(call: CallbackQuery, state: FSMContext):
    await state.set_state(ScheduleStates.choosing_institute)
    await call.message.edit_text(
        "Выберите институт:",
        reply_markup=institutes_keyboard()
    )


@router.message(ScheduleStates.waiting_for_group)
async def handle_group_input(message: Message, state: FSMContext):
    data = await state.get_data()
    pdf_path = data.get("pdf_path")
    course_num = data.get("course")
    if not pdf_path:
        await message.answer("⚠️ Что-то пошло не так. Начните заново — /schedule")
        await state.clear()
        return
    group = normalize_group(message.text or "")
    if not group:
        examples = _get_group_examples(pdf_path)
        await message.answer(
            f"⚠️ Не удалось распознать группу.\n\n"
            f"Попробуйте ещё раз, например: <code>{examples.split(',')[0]}</code>",
            parse_mode=ParseMode.HTML,
        )
        return
    schedule = _get_schedule_cached(pdf_path)
    all_groups = get_all_groups(schedule)
    if group not in all_groups:
        examples = _get_group_examples(pdf_path)
        await message.answer(
            f"⚠️ Группа <b>{group}</b> не найдена в расписании {course_num} курса. Проверьте номер и попробуйте ещё раз.\n\n"
            f"<i>Примеры групп: {examples}</i>",
            parse_mode=ParseMode.HTML,
        )
        return
    await state.clear()
    text = _format_day(schedule, group, "ПОНЕДЕЛЬНИК")
    await message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=days_keyboard(group, "ПОНЕДЕЛЬНИК")
    )


@router.callback_query(F.data.startswith("day:"))
async def on_day_selected(call: CallbackQuery):
    parts = call.data.split(":", 2)
    group = parts[1]
    day = parts[2]
    pdf_path = _find_pdf_for_group(group)
    if not pdf_path:
        await call.answer("❌ Не удалось найти расписание.", show_alert=True)
        return
    schedule = _get_schedule_cached(pdf_path)
    text = _format_day(schedule, group, day)
    await call.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=days_keyboard(group, day)
    )
