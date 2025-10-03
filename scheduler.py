import asyncio
import logging
from datetime import datetime, time, date
from aiogram import Bot
from database import db
from config import TIMEZONE, POINTS_TO_MONEY_RATE
from utils import format_points, MonthNames

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.running = False
    
    async def start(self):
        """Start the scheduler"""
        self.running = True
        logger.info("Scheduler started")
        
        # Start background tasks
        asyncio.create_task(self.daily_reminder_task())
        asyncio.create_task(self.monthly_report_task())
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Scheduler stopped")
    
    async def daily_reminder_task(self):
        """Task for daily reminders at 18:00"""
        while self.running:
            try:
                now = datetime.now(TIMEZONE)
                target_time = time(18, 0)  # 18:00
                
                # Check if it's time for reminder
                if (now.time().hour == target_time.hour and 
                    now.time().minute == target_time.minute):
                    
                    await self.send_daily_reminder()
                    
                    # Wait until next minute to avoid duplicate sends
                    await asyncio.sleep(60)
                else:
                    # Check every minute
                    await asyncio.sleep(60)
                    
            except Exception as e:
                logger.error(f"Error in daily_reminder_task: {e}")
                await asyncio.sleep(60)
    
    async def monthly_report_task(self):
        """Task for monthly reports on 1st day at 10:00"""
        while self.running:
            try:
                now = datetime.now(TIMEZONE)
                
                # Check if it's 1st day of month at 10:00
                if (now.day == 1 and 
                    now.time().hour == 10 and 
                    now.time().minute == 0):
                    
                    await self.send_monthly_reports()
                    
                    # Wait until next hour to avoid duplicate sends
                    await asyncio.sleep(3600)
                else:
                    # Check every minute
                    await asyncio.sleep(60)
                    
            except Exception as e:
                logger.error(f"Error in monthly_report_task: {e}")
                await asyncio.sleep(60)
    
    async def send_daily_reminder(self):
        """Send daily reminder to all users at 18:00"""
        try:
            users = await db.get_all_users()
            
            reminder_text = (
                "⏰ Напоминание!\\n\\n"
                "Время добавлять модули! ⚡\\n"
                "Используйте /modules или /add для записи выполненных заданий.\\n\\n"
                "📈 Каждый балл приближает вас к цели!"
            )
            
            sent_count = 0
            error_count = 0
            
            for user_id in users:
                try:
                    await self.bot.send_message(user_id, reminder_text)
                    sent_count += 1
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error sending reminder to user {user_id}: {e}")
                    error_count += 1
            
            logger.info(f"Daily reminder sent to {sent_count} users, {error_count} errors")
            
        except Exception as e:
            logger.error(f"Error in send_daily_reminder: {e}")
    
    async def send_monthly_reports(self):
        """Send monthly reports to all users on 1st day of month"""
        try:
            users = await db.get_all_users()
            now = datetime.now(TIMEZONE)
            
            # Get previous month
            prev_month = now.month - 1 if now.month > 1 else 12
            prev_year = now.year if now.month > 1 else now.year - 1
            
            sent_count = 0
            error_count = 0
            
            for user_id in users:
                try:
                    # Get user stats for previous month
                    points = await db.get_user_points_for_month(user_id, prev_year, prev_month)
                    
                    if points > 0:  # Send report only to active users
                        money = points * POINTS_TO_MONEY_RATE
                        
                        # Save monthly summary
                        await db.save_monthly_summary(user_id, prev_year, prev_month, points)
                        
                        # Get user name (simplified)
                        try:
                            user_info = await self.bot.get_chat(user_id)
                            name = user_info.first_name or f"User{user_id}"
                        except:
                            name = f"User{user_id}"
                        
                        # Get daily stats for the month
                        daily_stats = await db.get_user_daily_stats(user_id, prev_year, prev_month)
                        active_days = len(daily_stats)
                        
                        # Calculate averages
                        daily_average = points / active_days if active_days > 0 else 0
                        
                        report_text = (
                            f"📊 Месячный отчет\\n\\n"
                            f"👤 {name}\\n"
                            f"📅 {MonthNames.get_full_month_name(prev_month)} {prev_year}\\n\\n"
                            f"🎯 Результаты:\\n"
                            f"💎 Общие баллы: {format_points(points)}\\n"
                            f"💰 Денежный эквивалент: {format_points(money)} ₽\\n"
                            f"📈 Активных дней: {active_days}\\n"
                            f"📊 Среднее в день: {format_points(daily_average)}\\n\\n"
                            f"Отличная работа! Продолжайте в том же духе! 🚀\\n\\n"
                            f"Новый месяц - новые возможности! 💪"
                        )
                        
                        await self.bot.send_message(user_id, report_text)
                        sent_count += 1
                        
                        # Small delay to avoid rate limits
                        await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error sending monthly report to user {user_id}: {e}")
                    error_count += 1
            
            logger.info(f"Monthly reports sent to {sent_count} users, {error_count} errors")
            
        except Exception as e:
            logger.error(f"Error in send_monthly_reports: {e}")
    
    async def send_test_reminder(self, user_id: int):
        """Send test reminder to specific user (for testing)"""
        try:
            reminder_text = (
                "🧪 Тестовое напоминание!\\n\\n"
                "⏰ Время добавлять модули! ⚡\\n"
                "Используйте /modules или /add для записи выполненных заданий.\\n\\n"
                "📈 Каждый балл приближает вас к цели!"
            )
            
            await self.bot.send_message(user_id, reminder_text)
            logger.info(f"Test reminder sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending test reminder to user {user_id}: {e}")
    
    async def send_test_report(self, user_id: int):
        """Send test monthly report to specific user (for testing)"""
        try:
            now = datetime.now(TIMEZONE)
            
            # Get current month stats (for testing)
            points = await db.get_user_points_for_month(user_id, now.year, now.month)
            
            if points == 0:
                await self.bot.send_message(
                    user_id, 
                    "🧪 Тестовый отчет: нет активности в текущем месяце для демонстрации отчета."
                )
                return
            
            money = points * POINTS_TO_MONEY_RATE
            daily_stats = await db.get_user_daily_stats(user_id, now.year, now.month)
            active_days = len(daily_stats)
            daily_average = points / active_days if active_days > 0 else 0
            
            try:
                user_info = await self.bot.get_chat(user_id)
                name = user_info.first_name or f"User{user_id}"
            except:
                name = f"User{user_id}"
            
            report_text = (
                f"🧪 Тестовый месячный отчет\\n\\n"
                f"👤 {name}\\n"
                f"📅 {MonthNames.get_full_month_name(now.month)} {now.year} (текущий)\\n\\n"
                f"🎯 Результаты:\\n"
                f"💎 Общие баллы: {format_points(points)}\\n"
                f"💰 Денежный эквивалент: {format_points(money)} ₽\\n"
                f"📈 Активных дней: {active_days}\\n"
                f"📊 Среднее в день: {format_points(daily_average)}\\n\\n"
                f"Это тестовый отчет на основе текущих данных! 🧪"
            )
            
            await self.bot.send_message(user_id, report_text)
            logger.info(f"Test report sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending test report to user {user_id}: {e}")
