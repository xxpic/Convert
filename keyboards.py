from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from config import CURRENCIES, CURRENCY_FLAGS, CURRENCY_NAMES


def reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💱 Конвертировать")],
            [KeyboardButton(text="📊 Узнать курсы")],
            [KeyboardButton(text="🌅 Утренняя сводка")],
        ],
        resize_keyboard=False,
        persistent=True,
    )


def _inline_currency_row(prefix: str) -> list[list[InlineKeyboardButton]]:
    buttons = []
    for currency in CURRENCIES:
        flag = CURRENCY_FLAGS[currency]
        name = CURRENCY_NAMES[currency]
        buttons.append(
            InlineKeyboardButton(text=f"{flag} {name}", callback_data=f"{prefix}:{currency}")
        )
    return [buttons[i:i + 2] for i in range(0, len(buttons), 2)]


def convert_currency_keyboard() -> InlineKeyboardMarkup:
    rows = _inline_currency_row("cur")
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def rate_currency_keyboard() -> InlineKeyboardMarkup:
    rows = _inline_currency_row("rate")
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _fmt_amt(amount: float) -> str:
    return f"{amount:.2f}"


def result_keyboard(amount: float, from_currency: str) -> InlineKeyboardMarkup:
    a = _fmt_amt(amount)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Чаевые", callback_data=f"tips:{a}:{from_currency}"),
        ],
        [
            InlineKeyboardButton(text="🔄 Ещё раз", callback_data="new"),
        ],
    ])


def tips_back_keyboard(amount: float, from_currency: str) -> InlineKeyboardMarkup:
    a = _fmt_amt(amount)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data=f"back:{a}:{from_currency}"),
        ],
        [
            InlineKeyboardButton(text="🔄 Ещё раз", callback_data="new"),
        ],
    ])
