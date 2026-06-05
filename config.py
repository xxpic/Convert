import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")
WEB_PORT = int(os.getenv("PORT", "10000"))
DB_PATH = os.getenv("DB_PATH", "bot.db")
RATE_UPDATE_INTERVAL_MINUTES = int(os.getenv("RATE_UPDATE_INTERVAL", "60"))
KEEPALIVE_INTERVAL_MINUTES = int(os.getenv("KEEPALIVE_INTERVAL", "5"))
DIGEST_HOUR_CET = int(os.getenv("DIGEST_HOUR", "9"))

CURRENCIES = ["BYN", "PLN", "USD", "EUR", "RUB"]
CURRENCY_FLAGS = {
    "BYN": "🇧🇾",
    "PLN": "🇵🇱",
    "USD": "🇺🇸",
    "EUR": "🇪🇺",
    "RUB": "🇷🇺",
}
CURRENCY_NAMES = {
    "BYN": "BYN",
    "PLN": "PLN",
    "USD": "USD",
    "EUR": "EUR",
    "RUB": "RUB",
}
