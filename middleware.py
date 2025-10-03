from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from datetime import datetime
from config import TIMEZONE, ALLOWED_HOUR_START, ALLOWED_HOUR_END
import logging

logger = logging.getLogger(__name__)

class TimeRestrictionMiddleware(BaseMiddleware):
    """Middleware to restrict bot usage to specific hours (18:00-23:59)"""
    
    def __init__(self):
        super().__init__()
        self.restricted_commands = ['/modules', '/add']
        self.restricted_callbacks = ['module_', 'add_', 'undo']
    
    async def __call__(self, handler, event, data):
        # Allow admin commands and non-restricted commands always
        if isinstance(event, Message):
            if event.text and any(event.text.startswith(cmd) for cmd in ['/admin', '/start', '/help', '/points', '/leaderboard', '/graph', '/insight']):
                return await handler(event, data)
            
            # Check time restriction for module-related commands
            if event.text and any(event.text.startswith(cmd) for cmd in self.restricted_commands):
                if not self._is_allowed_time():
                    await event.answer(
                        "⏰ Добавление модулей доступно только с 18:00 до 23:59!\n"
                        f"Текущее время: {datetime.now(TIMEZONE).strftime('%H:%M')}"
                    )
                    return
        
        elif isinstance(event, CallbackQuery):
            # Check time restriction for module-related callbacks
            if event.data and any(event.data.startswith(cb) for cb in self.restricted_callbacks):
                if not self._is_allowed_time():
                    await event.answer(
                        "⏰ Добавление модулей доступно только с 18:00 до 23:59!",
                        show_alert=True
                    )
                    return
        
        return await handler(event, data)
    
    def _is_allowed_time(self) -> bool:
        """Check if current time is within allowed hours"""
        now = datetime.now(TIMEZONE)
        current_hour = now.hour
        return ALLOWED_HOUR_START <= current_hour <= ALLOWED_HOUR_END
