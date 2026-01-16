import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from database import init_db
from handlers import common, admin
from scheduler import setup_scheduler, start_scheduler, stop_scheduler


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def main():
    # Validate config
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN is not set! Please set it in .env file")
        sys.exit(1)
    
    if not config.SUPERUSER_ID:
        logger.warning("SUPERUSER_ID is not set! Admin commands will be disabled.")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()
    
    # Register routers
    dp.include_router(common.router)
    dp.include_router(admin.router)
    
    # Setup scheduler
    setup_scheduler(bot)
    start_scheduler()
    logger.info("Scheduler started")
    
    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    finally:
        stop_scheduler()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
