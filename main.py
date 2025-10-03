import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, ADMIN_IDS
from database import db
from middleware import TimeRestrictionMiddleware
from scheduler import Scheduler

# Import all handlers
import handlers
import advanced_handlers
import admin_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to start the bot"""
    
    # Validate configuration
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set in environment variables")
        sys.exit(1)
    
    # Initialize bot
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Initialize dispatcher
    dp = Dispatcher()
    
    # Add middleware
    dp.message.middleware(TimeRestrictionMiddleware())
    dp.callback_query.middleware(TimeRestrictionMiddleware())
    
    # Register routers
    dp.include_router(handlers.router)
    dp.include_router(advanced_handlers.router)
    dp.include_router(admin_handlers.router)
    
    # Initialize database
    try:
        await db.init()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    # Initialize scheduler
    scheduler = Scheduler(bot)
    
    # Add admin IDs from config to database
    try:
        for admin_id in ADMIN_IDS:
            await db.add_admin(admin_id)
        logger.info(f"Added {len(ADMIN_IDS)} admin IDs to database")
    except Exception as e:
        logger.error(f"Failed to add admin IDs: {e}")
    
    try:
        # Start scheduler
        await scheduler.start()
        
        # Send startup notification to admins
        startup_message = (
            "🤖 Бот запущен успешно!\\n\\n"
            f"⏰ Время: {asyncio.get_event_loop().time()}\\n"
            "✅ База данных подключена\\n"
            "📅 Планировщик активен\\n"
            "🔧 Все системы работают"
        )
        
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, startup_message)
            except Exception as e:
                logger.error(f"Failed to send startup notification to admin {admin_id}: {e}")
        
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Cleanup
        await scheduler.stop()
        await db.close()
        await bot.session.close()
        logger.info("Bot stopped and cleaned up")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by KeyboardInterrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
