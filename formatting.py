from config import CURRENCY_FLAGS, CURRENCY_NAMES, CURRENCIES
import api


def format_amount(value: float) -> str:
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", " ").replace(".", ",")
    return formatted


def format_conversion(amount: float, from_currency: str, converted: dict, changes: dict | None = None) -> str:
    flag_from = CURRENCY_FLAGS[from_currency]
    name_from = CURRENCY_NAMES[from_currency]
    lines = [f"💱  {format_amount(amount)} {name_from}", ""]

    for currency in CURRENCIES:
        if currency == from_currency:
            continue
        flag = CURRENCY_FLAGS[currency]
        name = CURRENCY_NAMES[currency]
        value = converted.get(currency, 0)
        line = f"{flag}  {format_amount(value)} {name}"
        if changes and currency in changes:
            change = changes[currency]
            if change is not None:
                if change > 0:
                    line += f"  ↑{abs(change)}%"
                elif change < 0:
                    line += f"  ↓{abs(change)}%"
                else:
                    line += "  —"
        lines.append(line)

    return "\n".join(lines)


def format_live_rates(from_currency: str, rates: dict, previous_rates: dict | None) -> str:
    flag_from = CURRENCY_FLAGS[from_currency]
    name_from = CURRENCY_NAMES[from_currency]
    lines = [f"📊 Курс {flag_from} {name_from} (обновлено сейчас)", ""]

    for currency in CURRENCIES:
        if currency == from_currency:
            continue
        flag = CURRENCY_FLAGS[currency]
        name = CURRENCY_NAMES[currency]
        cross = api.convert(1, from_currency, rates).get(currency, 0)
        line = f"{flag} 1 {name_from} = {format_amount(cross)} {name}"
        if previous_rates:
            change = api.calculate_change(rates, previous_rates, from_currency, currency)
            if change is not None:
                if change > 0:
                    line += f"  ↑{abs(change)}%"
                elif change < 0:
                    line += f"  ↓{abs(change)}%"
                else:
                    line += "  —"
        lines.append(line)

    return "\n".join(lines)
    from datetime import datetime
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("Europe/Warsaw"))
    date_str = now.strftime("%d.%m.%Y")

    lines = [f"🌅 Курс на {date_str}", ""]

    pairs = [
        ("PLN", "BYN"),
        ("USD", "BYN"),
        ("EUR", "BYN"),
        ("PLN", "USD"),
        ("EUR", "USD"),
    ]

    for from_c, to_c in pairs:
        flag_from = CURRENCY_FLAGS[from_c]
        flag_to = CURRENCY_FLAGS[to_c]
        cross = api.convert(1, from_c, current_rates).get(to_c, 0)
        line = f"{flag_from} 1 {CURRENCY_NAMES[from_c]} = {format_amount(cross)} {CURRENCY_NAMES[to_c]}"

        if previous_rates:
            change = api.calculate_change(current_rates, previous_rates, from_c, to_c)
            if change is not None:
                if change > 0:
                    line += f" ↑{abs(change)}%"
                elif change < 0:
                    line += f" ↓{abs(change)}%"
                else:
                    line += " —"
        lines.append(line)

    return "\n".join(lines)
