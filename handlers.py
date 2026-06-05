from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from config import CURRENCIES
import api
import db
import formatting
from keyboards import currency_keyboard, result_keyboard, tips_back_keyboard, main_keyboard

router = Router()

_user_amounts: dict[int, float] = {}

START_TEXT = (
    "💱 <b>Конвертер валют</b>\n\n"
    "Быстрая конвертация между BYN, PLN, USD и EUR.\n"
    "Нажмите кнопку ниже, чтобы начать."
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


def amount_currency_keyboard() -> InlineKeyboardMarkup:
    rows = currency_keyboard().inline_keyboard
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.init_db()
    kb = await main_keyboard(message.from_user.id)
    await message.answer(START_TEXT, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "new")
async def cb_new(callback: CallbackQuery):
    await callback.message.edit_text(
        "📝 Введите сумму для конвертации:\n\n"
        "<i>Например: 100 или 99,50</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "sub_on")
async def cb_sub_on(callback: CallbackQuery):
    await db.subscribe(callback.from_user.id, callback.message.chat.id)
    kb = await main_keyboard(callback.from_user.id)
    await callback.message.edit_text(
        START_TEXT + "\n\n✅ Утренняя сводка <b>включена</b>!",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer("Утренняя сводка включена!")


@router.callback_query(F.data == "sub_off")
async def cb_sub_off(callback: CallbackQuery):
    await db.unsubscribe(callback.from_user.id)
    kb = await main_keyboard(callback.from_user.id)
    await callback.message.edit_text(
        START_TEXT + "\n\n❌ Утренняя сводка <b>выключена</b>.",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer("Утренняя сводка выключена")


@router.message(F.text)
async def msg_amount(message: Message):
    if not _looks_like_number(message.text):
        return

    amount = parse_amount(message.text)
    if amount is None:
        await message.answer(
            "Введите сумму больше нуля, например: 100 или 99,50",
            reply_markup=await main_keyboard(message.from_user.id),
        )
        return

    _user_amounts[message.from_user.id] = amount
    kb = amount_currency_keyboard()
    await message.answer(
        f"💰 Сумма: <b>{formatting.format_amount(amount)}</b>\n\n"
        "Выберите исходную валюту:",
        reply_markup=kb,
        parse_mode="HTML",
    )


async def _do_convert(callback: CallbackQuery, amount: float, from_currency: str):
    rates = api.get_rates()
    if not rates:
        await callback.answer("⚠️ Курсы недоступны. Попробуйте позже.", show_alert=True)
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


@router.callback_query(F.data.startswith("cur:"))
async def cb_currency(callback: CallbackQuery):
    from_currency = callback.data.split(":")[1]
    amount = _user_amounts.get(callback.from_user.id)
    if amount is None:
        await callback.answer("⚠️ Сумма не найдена. Начните заново.", show_alert=True)
        return
    await _do_convert(callback, amount, from_currency)


@router.callback_query(F.data.startswith("tips:"))
async def cb_tips(callback: CallbackQuery):
    parts = callback.data.split(":")
    amount = float(parts[1])
    from_currency = parts[2]

    rates = api.get_rates()
    if not rates:
        await callback.answer("⚠️ Курсы недоступны.", show_alert=True)
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


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery):
    kb = await main_keyboard(callback.from_user.id)
    await callback.message.edit_text(START_TEXT, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
