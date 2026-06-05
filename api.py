import aiohttp
import logging
import db as _db
from config import CURRENCIES

logger = logging.getLogger(__name__)

_cached_rates: dict | None = None
_cached_base: str = "USD"
_last_update: str = ""


async def fetch_rates() -> dict | None:
    global _cached_rates, _cached_base, _last_update
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://open.er-api.com/v6/latest/USD"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    logger.error(f"Rate API returned status {resp.status}")
                    return _cached_rates
                data = await resp.json()
                if data.get("result") != "success":
                    logger.error(f"Rate API error: {data}")
                    return _cached_rates
                rates = data.get("rates", {})
                missing = [c for c in CURRENCIES if c not in rates and c != "USD"]
                if missing:
                    logger.warning(f"Missing currencies in API response: {missing}")
                _cached_rates = rates
                _cached_base = "USD"
                _last_update = data.get("time_last_update_utc", "")
                logger.info(f"Rates updated successfully. {len(rates)} currencies.")
                return rates
    except Exception as e:
        logger.error(f"Failed to fetch rates: {e}")
        return _cached_rates


async def fetch_fresh_rates() -> dict | None:
    rates = await fetch_rates()
    if rates:
        await _db.save_rate_snapshot(rates)
        logger.info("Fresh rates fetched and snapshot saved")
    return rates


def get_rates() -> dict | None:
    return _cached_rates


def get_last_update() -> str:
    return _last_update


def convert(amount: float, from_currency: str, rates: dict) -> dict:
    result = {}
    if from_currency == "USD":
        usd_amount = amount
    else:
        usd_amount = amount / rates[from_currency]

    for currency in CURRENCIES:
        if currency == from_currency:
            continue
        if currency == "USD":
            result[currency] = usd_amount
        else:
            result[currency] = usd_amount * rates[currency]
    return result


def calculate_change(current_rates: dict, previous_rates: dict | None, from_currency: str, to_currency: str) -> float | None:
    if not previous_rates:
        return None
    if from_currency not in current_rates and from_currency != "USD":
        return None
    if to_currency not in current_rates and to_currency != "USD":
        return None
    if from_currency not in previous_rates and from_currency != "USD":
        return None
    if to_currency not in previous_rates and to_currency != "USD":
        return None

    def cross_rate(rates, base_cur, target_cur):
        if base_cur == "USD":
            base_to_usd = 1.0
        else:
            base_to_usd = 1.0 / rates[base_cur]
        if target_cur == "USD":
            return base_to_usd
        return base_to_usd * rates[target_cur]

    current_cross = cross_rate(current_rates, from_currency, to_currency)
    previous_cross = cross_rate(previous_rates, from_currency, to_currency)

    if previous_cross == 0:
        return None

    change_pct = ((current_cross - previous_cross) / previous_cross) * 100
    return round(change_pct, 2)
