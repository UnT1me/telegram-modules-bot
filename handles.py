from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import datetime, date
import re
import logging

from database import db
from config import TIMEZONE, POINTS_TO_MONEY_RATE
from utils import format_points, get_user_display_name, create_modules_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Start command handler"""
    user_name = get_user_display_name(message.from_user)
    await message.answer(
        f"👋 Привет, {user_name}!\n\n"
        "🎯 Я помогу тебе отслеживать выполненные модули и подсчитывать баллы.\n\n"
        "📋 Доступные команды:\n"
        "/modules - Выбрать модуль для добавления\n"
        "/add - Добавить модуль командой\n"
        "/points - Мои баллы за месяц\n"
        "/graph - График выполнения\n"
        "/insight - ИИ-анализ прогресса\n"
        "/leaderboard - Лидерборд\n\n"
        "⏰ Добавление модулей доступно с 18:00 до 23:59"
    )

@router.message(Command("modules"))
async def cmd_modules(message: Message):
    """Show modules selection menu"""
    try:
        modules = await db.get_modules()
        if not modules:
            await message.answer("❌ Модули не найдены. Обратитесь к администратору.")
            return
        
        keyboard = create_modules_keyboard(modules)
        await message.answer(
            "📚 Выберите модуль для добавления:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in cmd_modules: {e}")
        await message.answer("❌ Произошла ошибка при загрузке модулей.")

@router.callback_query(F.data.startswith("module_"))
async def handle_module_selection(callback: CallbackQuery):
    """Handle module selection from inline keyboard"""
    try:
        module_id = int(callback.data.split("_")[1])
        user_id = callback.from_user.id
        
        # Get module info
        modules = await db.get_modules()
        module = next((m for m in modules if m['id'] == module_id), None)
        
        if not module:
            await callback.answer("❌ Модуль не найден!", show_alert=True)
            return
        
        # Add module completion
        await db.add_module_completion(user_id, module_id)
        
        # Create undo keyboard
        undo_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="↩️ Отменить последнее", callback_data="undo_last")
            ]]
        )
        
        await callback.message.edit_text(
            f"✅ Модуль '{module['name']}' добавлен!\n"
            f"💎 Получено баллов: {format_points(module['points'])}\n"
            f"💰 Деньги: {format_points(module['points'] * POINTS_TO_MONEY_RATE)} ₽",
            reply_markup=undo_keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in handle_module_selection: {e}")
        await callback.answer("❌ Произошла ошибка при добавлении модуля!", show_alert=True)

@router.callback_query(F.data == "undo_last")
async def handle_undo_last(callback: CallbackQuery):
    """Handle undo last action"""
    try:
        user_id = callback.from_user.id
        last_action = await db.get_user_last_action(user_id)
        
        if not last_action:
            await callback.answer("❌ Нет действий для отмены!", show_alert=True)
            return
        
        success = await db.undo_last_action(user_id)
        
        if success:
            await callback.message.edit_text(
                f"↩️ Действие отменено!\n"
                f"Удален модуль: '{last_action['name']}' ({format_points(last_action['points'])} баллов)"
            )
            await callback.answer("✅ Действие отменено!")
        else:
            await callback.answer("❌ Не удалось отменить действие!", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error in handle_undo_last: {e}")
        await callback.answer("❌ Произошла ошибка при отмене!", show_alert=True)

@router.message(Command("add"))
async def cmd_add(message: Message):
    """Add module by command: /add <module_name> <count>"""
    try:
        args = message.text.split()[1:]  # Remove /add
        
        if len(args) < 1:
            await message.answer(
                "📝 Использование: /add <название_модуля> [количество]\n\n"
                "Примеры:\n"
                "/add BMU 5X\n"
                "/add BMU 5X 3\n"
                "/add Практика 1"
            )
            return
        
        # Parse count if provided
        count = 1
        if args[-1].isdigit():
            count = int(args[-1])
            module_name = " ".join(args[:-1])
        else:
            module_name = " ".join(args)
        
        # Find module
        module = await db.get_module_by_name(module_name)
        if not module:
            await message.answer(f"❌ Модуль '{module_name}' не найден!")
            return
        
        # Add multiple completions
        user_id = message.from_user.id
        for _ in range(count):
            await db.add_module_completion(user_id, module['id'])
        
        total_points = module['points'] * count
        total_money = total_points * POINTS_TO_MONEY_RATE
        
        # Create undo keyboard
        undo_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="↩️ Отменить последнее", callback_data="undo_last")
            ]]
        )
        
        count_text = f" (x{count})" if count > 1 else ""
        await message.answer(
            f"✅ Модуль '{module['name']}'{count_text} добавлен!\n"
            f"💎 Получено баллов: {format_points(total_points)}\n"
            f"💰 Деньги: {format_points(total_money)} ₽",
            reply_markup=undo_keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in cmd_add: {e}")
        await message.answer("❌ Произошла ошибка при добавлении модуля.")

@router.message(Command("points"))
async def cmd_points(message: Message):
    """Show user's points for current month"""
    try:
        user_id = message.from_user.id
        now = datetime.now(TIMEZONE)
        
        points = await db.get_user_points_for_month(user_id, now.year, now.month)
        money = points * POINTS_TO_MONEY_RATE
        
        # Get previous month for comparison
        prev_month = now.month - 1 if now.month > 1 else 12
        prev_year = now.year if now.month > 1 else now.year - 1
        prev_points = await db.get_user_points_for_month(user_id, prev_year, prev_month)
        
        change = points - prev_points
        change_symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        change_text = f"{change_symbol} {'+' if change > 0 else ''}{format_points(change)} баллов к прошлому месяцу"
        
        await message.answer(
            f"💎 Ваши баллы за {now.strftime('%B %Y')}:\n\n"
            f"🎯 Баллы: {format_points(points)}\n"
            f"💰 Деньги: {format_points(money)} ₽\n\n"
            f"{change_text}"
        )
        
    except Exception as e:
        logger.error(f"Error in cmd_points: {e}")
        await message.answer("❌ Произошла ошибка при получении баллов.")
