from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from config import CURRENCIES
import api
import db
import formatting
from keyboards import (
    reply_keyboard,
    convert_currency_keyboard,
    rate_currency_keyboard,
    result_keyboard,
    tips_back_keyboard,
    digest_time_keyboard,
    digest_off_keyboard,
)

router = Router()

_user_amounts: dict[int, float] = {}

REPLY_CONVERT = "💱 Конвертировать"
REPLY_RATES = "📊 Узнать курсы"
REPLY_DIGEST = "🌅 Утренняя сводка"

START_TEXT = (
    "💱 <b>Конвертер валют</b>\n\n"
    "Быстрая конвертация между BYN, PLN, USD и EUR.\n"
    "Используйте кнопки ниже."
)


def _looks_like_number(text: str) -> bool:
    cleaned = text.strip().replace(" ", "").replace(",", "").replace(".", "")
    return cleaned.isdigit() and len(cleaned) > 0


def parse_amount(text: str) -> float | None:
    if not _looks_like_number(text):
        return None
    cleaned = text.strip().replace(" ", "")
    cleaned = cleaned.replace(",", ".")
    try:
        value = float(cleaned)
        if value <= 0:
            return None
        return value
    except ValueError:
        return None


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.init_db()
    await message.answer(START_TEXT, reply_markup=reply_keyboard(), parse_mode="HTML")


@router.message(F.text == REPLY_CONVERT)
async def msg_convert(message: Message):
    await message.answer(
        "📝 Введите сумму для конвертации:\n\n"
        "<i>Например: 100 или 99,50</i>",
        parse_mode="HTML",
    )


@router.message(F.text == REPLY_RATES)
async def msg_rates(message: Message):
    kb = rate_currency_keyboard()
    await message.answer("Выберите базовую валюту:", reply_markup=kb)


@router.message(F.text == REPLY_DIGEST)
async def msg_digest_toggle(message: Message):
    user_id = message.from_user.id
    if await db.is_subscribed(user_id):
        hour = await db.get_digest_hour(user_id)
        await message.answer(
            f"✅ Утренняя сводка <b>включена</b> на {hour}:00\n\nВыберите другое время или выключите:",
            reply_markup=digest_off_keyboard(),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "🌅 Выберите время утренней сводки:",
            reply_markup=digest_time_keyboard(),
        )


@router.message(F.text)
async def msg_amount(message: Message):
    if not _looks_like_number(message.text):
        return

    amount = parse_amount(message.text)
    if amount is None:
        await message.answer("Введите сумму больше нуля, например: 100 или 99,50")
        return

    _user_amounts[message.from_user.id] = amount
    kb = convert_currency_keyboard()
    await message.answer(
        f"💰 Сумма: <b>{formatting.format_amount(amount)}</b>\n\n"
        "Выберите исходную валюту:",
        reply_markup=kb,
        parse_mode="HTML",
    )


async def _do_convert(callback: CallbackQuery, amount: float, from_currency: str):
    rates = api.get_rates()
    if not rates:
        await callback.answer("Курсы недоступны. Попробуйте позже.", show_alert=True)
        return

    converted = api.convert(amount, from_currency, rates)
    previous_rates = await db.get_previous_rates()

    changes = {}
    if previous_rates:
        for currency in CURRENCIES:
            if currency == from_currency:
                continue
            ch = api.calculate_change(rates, previous_rates, from_currency, currency)
            if ch is not None:
                changes[currency] = ch

    result_text = formatting.format_conversion(amount, from_currency, converted, changes if changes else None)
    kb = result_keyboard(amount, from_currency)
    await callback.message.edit_text(result_text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "new")
async def cb_new(callback: CallbackQuery):
    await callback.message.edit_text(
        "📝 Введите сумму для конвертации:\n\n"
        "<i>Например: 100 или 99,50</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cur:"))
async def cb_currency(callback: CallbackQuery):
    from_currency = callback.data.split(":")[1]
    amount = _user_amounts.get(callback.from_user.id)
    if amount is None:
        await callback.answer("Сумма не найдена. Начните заново.", show_alert=True)
        return
    await _do_convert(callback, amount, from_currency)


@router.callback_query(F.data.startswith("rate:"))
async def cb_rate(callback: CallbackQuery):
    from_currency = callback.data.split(":")[1]

    rates = await api.fetch_fresh_rates()
    if not rates:
        await callback.answer("Не удалось получить курсы. Попробуйте позже.", show_alert=True)
        return

    previous_rates = await db.get_previous_rates()
    text = formatting.format_live_rates(from_currency, rates, previous_rates)
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data.startswith("tips:"))
async def cb_tips(callback: CallbackQuery):
    parts = callback.data.split(":")
    amount = float(parts[1])
    from_currency = parts[2]

    rates = api.get_rates()
    if not rates:
        await callback.answer("Курсы недоступны.", show_alert=True)
        return

    converted = api.convert(amount, from_currency, rates)
    tips_text = formatting.format_tips(amount, from_currency, converted)
    kb = tips_back_keyboard(amount, from_currency)
    await callback.message.edit_text(tips_text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("back:"))
async def cb_back(callback: CallbackQuery):
    parts = callback.data.split(":")
    amount = float(parts[1])
    from_currency = parts[2]
    await _do_convert(callback, amount, from_currency)


@router.callback_query(F.data.startswith("dtime:"))
async def cb_digest_time(callback: CallbackQuery):
    hour = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    await db.subscribe(user_id, callback.message.chat.id, digest_hour=hour)
    await callback.message.edit_text(
        f"✅ Утренняя сводка <b>включена</b> на {hour}:00!\n\nКаждый день в {hour}:00 будете получать актуальные курсы.",
        parse_mode="HTML",
    )
    await callback.answer(f"Сводка включена на {hour}:00")


@router.callback_query(F.data == "doff")
async def cb_digest_off(callback: CallbackQuery):
    await db.unsubscribe(callback.from_user.id)
    await callback.message.edit_text("❌ Утренняя сводка <b>выключена</b>.", parse_mode="HTML")
    await callback.answer("Сводка выключена")


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery):
    await callback.message.edit_text("Отменено. Выберите действие 👇")
    await callback.answer()
