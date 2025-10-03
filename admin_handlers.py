from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import datetime, date
import logging

from database import db
from config import TIMEZONE, POINTS_TO_MONEY_RATE, ADMIN_IDS
from utils import format_points, get_user_display_name, MonthNames

logger = logging.getLogger(__name__)
router = Router()

async def is_admin(user_id: int) -> bool:
    """Check if user is admin (from config or database)"""
    return user_id in ADMIN_IDS or await db.is_admin(user_id)

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin panel main menu"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_users"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton(text="📈 Отправить отчеты", callback_data="admin_reports"),
                InlineKeyboardButton(text="⚙️ Управление", callback_data="admin_manage")
            ]
        ]
    )
    
    await message.answer(
        "🔧 Панель администратора\\n\\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "admin_users")
async def admin_show_users(callback: CallbackQuery):
    """Show all users"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа!", show_alert=True)
        return
    
    try:
        users = await db.get_all_users()
        now = datetime.now(TIMEZONE)
        
        if not users:
            await callback.message.edit_text("👥 Пользователей пока нет.")
            return
        
        text = f"👥 Всего пользователей: {len(users)}\\n\\n"
        
        for user_id in users[:20]:  # Limit to first 20
            try:
                user_info = await callback.bot.get_chat(user_id)
                name = get_user_display_name(user_info)
            except:
                name = f"User{user_id}"
            
            points = await db.get_user_points_for_month(user_id, now.year, now.month)
            text += f"👤 {name} (ID: {user_id})\\n"
            text += f"   💎 {format_points(points)} баллов за месяц\\n\\n"
        
        if len(users) > 20:
            text += f"... и еще {len(users) - 20} пользователей"
        
        back_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
            ]]
        )
        
        await callback.message.edit_text(text, reply_markup=back_keyboard)
        
    except Exception as e:
        logger.error(f"Error in admin_show_users: {e}")
        await callback.answer("❌ Ошибка при загрузке пользователей!", show_alert=True)

@router.callback_query(F.data == "admin_stats")
async def admin_show_stats(callback: CallbackQuery):
    """Show system statistics"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа!", show_alert=True)
        return
    
    try:
        now = datetime.now(TIMEZONE)
        users = await db.get_all_users()
        leaderboard = await db.get_leaderboard(now.year, now.month, limit=100)
        
        total_users = len(users)
        active_users = len(leaderboard)
        
        # Calculate total points for current month
        total_points = sum(float(entry['total_points']) for entry in leaderboard)
        total_money = total_points * POINTS_TO_MONEY_RATE
        
        # Get modules info
        modules = await db.get_modules()
        
        text = (
            f"📊 Статистика системы\\n\\n"
            f"📅 Период: {MonthNames.get_full_month_name(now.month)} {now.year}\\n\\n"
            f"👥 Всего пользователей: {total_users}\\n"
            f"🔥 Активных в месяце: {active_users}\\n"
            f"📚 Доступно модулей: {len(modules)}\\n\\n"
            f"💎 Общий баланс баллов: {format_points(total_points)}\\n"
            f"💰 Общий денежный эквивалент: {format_points(total_money)} ₽\\n\\n"
            f"📈 Средние баллы на активного пользователя: "
            f"{format_points(total_points / active_users) if active_users > 0 else 0}"
        )
        
        back_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
            ]]
        )
        
        await callback.message.edit_text(text, reply_markup=back_keyboard)
        
    except Exception as e:
        logger.error(f"Error in admin_show_stats: {e}")
        await callback.answer("❌ Ошибка при загрузке статистики!", show_alert=True)

@router.callback_query(F.data == "admin_reports")
async def admin_send_reports(callback: CallbackQuery):
    """Send monthly reports to all users"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа!", show_alert=True)
        return
    
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
                points = await db.get_user_points_for_month(user_id, prev_year, prev_month)
                
                if points > 0:  # Send report only to users with activity
                    money = points * POINTS_TO_MONEY_RATE
                    
                    try:
                        user_info = await callback.bot.get_chat(user_id)
                        name = get_user_display_name(user_info)
                    except:
                        name = "Пользователь"
                    
                    report_text = (
                        f"📊 Отчет за {MonthNames.get_full_month_name(prev_month)} {prev_year}\\n\\n"
                        f"👤 {name}\\n"
                        f"💎 Набрано баллов: {format_points(points)}\\n"
                        f"💰 Денежный эквивалент: {format_points(money)} ₽\\n\\n"
                        f"Спасибо за активность! 🎉"
                    )
                    
                    await callback.bot.send_message(user_id, report_text)
                    sent_count += 1
                    
            except Exception as e:
                logger.error(f"Error sending report to user {user_id}: {e}")
                error_count += 1
        
        result_text = (
            f"📧 Отчеты отправлены!\\n\\n"
            f"✅ Успешно: {sent_count}\\n"
            f"❌ Ошибок: {error_count}"
        )
        
        back_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
            ]]
        )
        
        await callback.message.edit_text(result_text, reply_markup=back_keyboard)
        
    except Exception as e:
        logger.error(f"Error in admin_send_reports: {e}")
        await callback.answer("❌ Ошибка при отправке отчетов!", show_alert=True)

@router.callback_query(F.data == "admin_manage")
async def admin_manage(callback: CallbackQuery):
    """Admin management menu"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа!", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add_admin"),
                InlineKeyboardButton(text="📚 Управление модулями", callback_data="admin_modules")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
            ]
        ]
    )
    
    await callback.message.edit_text(
        "⚙️ Управление системой\\n\\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "admin_modules")
async def admin_show_modules(callback: CallbackQuery):
    """Show modules management"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа!", show_alert=True)
        return
    
    try:
        modules = await db.get_modules()
        
        text = f"📚 Управление модулями ({len(modules)} шт.)\\n\\n"
        
        for module in modules:
            text += f"• {module['name']} - {format_points(module['points'])} баллов\\n"
        
        text += "\\n💡 Для добавления/изменения модулей используйте прямые SQL-запросы к базе данных."
        
        back_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_manage")
            ]]
        )
        
        await callback.message.edit_text(text, reply_markup=back_keyboard)
        
    except Exception as e:
        logger.error(f"Error in admin_show_modules: {e}")
        await callback.answer("❌ Ошибка при загрузке модулей!", show_alert=True)

@router.callback_query(F.data == "admin_back")
async def admin_back_to_main(callback: CallbackQuery):
    """Go back to main admin menu"""
    await cmd_admin(callback.message)
    await callback.answer()

@router.message(Command("admin_user"))
async def cmd_admin_user(message: Message):
    """Get specific user statistics: /admin_user <user_id>"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    try:
        args = message.text.split()[1:]
        if not args:
            await message.answer("📝 Использование: /admin_user <user_id>")
            return
        
        user_id = int(args[0])
        now = datetime.now(TIMEZONE)
        
        # Get user info
        try:
            user_info = await message.bot.get_chat(user_id)
            name = get_user_display_name(user_info)
        except:
            name = f"User{user_id}"
        
        # Get current month stats
        current_points = await db.get_user_points_for_month(user_id, now.year, now.month)
        daily_stats = await db.get_user_daily_stats(user_id, now.year, now.month)
        
        # Get previous month stats
        prev_month = now.month - 1 if now.month > 1 else 12
        prev_year = now.year if now.month > 1 else now.year - 1
        prev_points = await db.get_user_points_for_month(user_id, prev_year, prev_month)
        
        active_days = len(daily_stats)
        money = current_points * POINTS_TO_MONEY_RATE
        
        text = (
            f"👤 Статистика пользователя\\n\\n"
            f"Имя: {name}\\n"
            f"ID: {user_id}\\n\\n"
            f"📅 {MonthNames.get_full_month_name(now.month)} {now.year}:\\n"
            f"💎 Баллы: {format_points(current_points)}\\n"
            f"💰 Деньги: {format_points(money)} ₽\\n"
            f"📈 Активных дней: {active_days}\\n\\n"
            f"📅 {MonthNames.get_full_month_name(prev_month)} {prev_year}:\\n"
            f"💎 Баллы: {format_points(prev_points)}\\n\\n"
        )
        
        if prev_points > 0:
            change = current_points - prev_points
            change_percent = (change / prev_points) * 100
            text += f"📊 Изменение: {'+' if change > 0 else ''}{format_points(change)} баллов ({change_percent:+.1f}%)"
        
        await message.answer(text)
        
    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя.")
    except Exception as e:
        logger.error(f"Error in cmd_admin_user: {e}")
        await message.answer("❌ Произошла ошибка при получении статистики пользователя.")
