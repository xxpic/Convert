import logging
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import RENDER_EXTERNAL_URL, KEEPALIVE_INTERVAL_MINUTES, RATE_UPDATE_INTERVAL_MINUTES, DIGEST_HOUR_CET
import api
import db
import formatting

logger = logging.getLogger(__name__)

scheduler: AsyncIOScheduler | None = None


async def update_rates_job():
    rates = await api.fetch_rates()
    if rates:
        await db.save_rate_snapshot(rates)
        logger.info("Rates updated and snapshot saved")


async def morning_digest_job(bot):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo("Europe/Warsaw"))
    current_hour = now.hour

    current_rates = api.get_rates()
    if not current_rates:
        logger.warning("No rates available for morning digest")
        return

    previous_rates = await db.get_previous_rates()
    text = formatting.format_digest(current_rates, previous_rates)

    subscribers = await db.get_all_subscribers()
    for user_id, chat_id, digest_hour in subscribers:
        if digest_hour != current_hour:
            continue
        try:
            await bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            logger.error(f"Failed to send digest to {user_id}: {e}")


async def keepalive_job():
    if not RENDER_EXTERNAL_URL:
        return
    url = f"{RENDER_EXTERNAL_URL}/health"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    logger.debug("Keep-alive ping successful")
                else:
                    logger.warning(f"Keep-alive returned status {resp.status}")
    except Exception as e:
        logger.error(f"Keep-alive ping failed: {e}")


def setup_scheduler(bot) -> AsyncIOScheduler:
    global scheduler
    scheduler = AsyncIOScheduler(timezone="Europe/Warsaw")

    scheduler.add_job(
        update_rates_job,
        "interval",
        minutes=RATE_UPDATE_INTERVAL_MINUTES,
        id="update_rates",
        replace_existing=True,
    )

    scheduler.add_job(
        morning_digest_job,
        "cron",
        hour="8,9,10,11",
        minute=0,
        id="morning_digest",
        replace_existing=True,
        args=[bot],
    )

    if RENDER_EXTERNAL_URL:
        scheduler.add_job(
            keepalive_job,
            "interval",
            minutes=KEEPALIVE_INTERVAL_MINUTES,
            id="keepalive",
            replace_existing=True,
        )

    return scheduler


async def start_scheduler(bot):
    sched = setup_scheduler(bot)
    await update_rates_job()
    sched.start()
    logger.info("Scheduler started")


def stop_scheduler():
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
