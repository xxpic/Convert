from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CURRENCIES, CURRENCY_FLAGS, CURRENCY_NAMES
from db import is_subscribed


def currency_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for currency in CURRENCIES:
        flag = CURRENCY_FLAGS[currency]
        name = CURRENCY_NAMES[currency]
        buttons.append(
            InlineKeyboardButton(text=f"{flag} {name}", callback_data=f"cur:{currency}")
        )
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)])


def _fmt_amt(amount: float) -> str:
    return f"{amount:.2f}"


def result_keyboard(amount: float, from_currency: str) -> InlineKeyboardMarkup:
    a = _fmt_amt(amount)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Чаевые", callback_data=f"tips:{a}:{from_currency}"),
        ],
        [
            InlineKeyboardButton(text="🔄 Новая конвертация", callback_data="new"),
        ],
    ])


def tips_back_keyboard(amount: float, from_currency: str) -> InlineKeyboardMarkup:
    a = _fmt_amt(amount)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data=f"back:{a}:{from_currency}"),
        ],
        [
            InlineKeyboardButton(text="🔄 Новая конвертация", callback_data="new"),
        ],
    ])


async def main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    sub = await is_subscribed(user_id)
    sub_text = "🌅 Утренняя сводка: ВЫКЛ" if not sub else "🌅 Утренняя сводка: ВКЛ"
    sub_data = "sub_on" if not sub else "sub_off"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💱 Конвертировать", callback_data="new")],
        [InlineKeyboardButton(text=sub_text, callback_data=sub_data)],
    ])
