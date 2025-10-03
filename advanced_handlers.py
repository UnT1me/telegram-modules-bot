from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from datetime import datetime, date
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import calendar
import logging

from database import db
from config import TIMEZONE, POINTS_TO_MONEY_RATE, ADMIN_IDS
from utils import (
    format_points, get_user_display_name, get_rank_emoji,
    generate_progress_insights, MonthNames
)

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message):
    """Show leaderboard for current month"""
    try:
        now = datetime.now(TIMEZONE)
        leaderboard = await db.get_leaderboard(now.year, now.month)
        
        if not leaderboard:
            await message.answer("📊 Пока нет данных для лидерборда за этот месяц.")
            return
        
        text = f"🏆 Лидерборд за {MonthNames.get_full_month_name(now.month)} {now.year}\\n\\n"
        
        for i, entry in enumerate(leaderboard, 1):
            user_id = entry['user_id']
            points = float(entry['total_points'])
            money = points * POINTS_TO_MONEY_RATE
            
            # Try to get user info (this is simplified - in real bot you'd cache this)
            try:
                user_info = await message.bot.get_chat(user_id)
                name = get_user_display_name(user_info)
            except:
                name = f"User{user_id}"
            
            rank_emoji = get_rank_emoji(i)
            text += f"{rank_emoji} {name}\\n"
            text += f"   💎 {format_points(points)} баллов\\n"
            text += f"   💰 {format_points(money)} ₽\\n\\n"
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Error in cmd_leaderboard: {e}")
        await message.answer("❌ Произошла ошибка при загрузке лидерборда.")

@router.message(Command("graph"))
async def cmd_graph(message: Message):
    """Generate and send user's progress graph"""
    try:
        user_id = message.from_user.id
        now = datetime.now(TIMEZONE)
        
        # Get daily stats for current month
        daily_stats = await db.get_user_daily_stats(user_id, now.year, now.month)
        
        if not daily_stats:
            await message.answer("📈 Пока нет данных для построения графика.")
            return
        
        # Generate graph
        graph_buffer = await generate_progress_graph(daily_stats, now.year, now.month)
        
        # Send graph
        graph_file = BufferedInputFile(
            graph_buffer.getvalue(),
            filename=f"progress_{user_id}_{now.year}_{now.month}.png"
        )
        
        user_name = get_user_display_name(message.from_user)
        caption = f"📈 График выполнения модулей\\n👤 {user_name}\\n📅 {MonthNames.get_full_month_name(now.month)} {now.year}"
        
        await message.answer_photo(graph_file, caption=caption)
        
    except Exception as e:
        logger.error(f"Error in cmd_graph: {e}")
        await message.answer("❌ Произошла ошибка при создании графика.")

async def generate_progress_graph(daily_stats: dict, year: int, month: int) -> BytesIO:
    """Generate progress graph for user"""
    
    # Set up Russian font (if available) and style
    plt.style.use('default')
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Get days in month
    days_in_month = calendar.monthrange(year, month)[1]
    
    # Prepare data
    days = list(range(1, days_in_month + 1))
    points = [daily_stats.get(day, 0) for day in days]
    
    # Create bar chart
    bars = ax.bar(days, points, color='#4CAF50', alpha=0.8, edgecolor='#2E7D32', linewidth=1)
    
    # Customize appearance
    ax.set_xlabel('День месяца', fontsize=12)
    ax.set_ylabel('Баллы', fontsize=12)
    ax.set_title(f'График выполнения модулей - {MonthNames.get_full_month_name(month)} {year}', 
                fontsize=14, fontweight='bold')
    
    # Set x-axis ticks
    ax.set_xticks(range(1, days_in_month + 1, max(1, days_in_month // 10)))
    ax.set_xlim(0.5, days_in_month + 0.5)
    
    # Add grid
    ax.grid(True, axis='y', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Add value labels on bars (only for non-zero values)
    for bar, point in zip(bars, points):
        if point > 0:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{format_points(point)}',
                   ha='center', va='bottom', fontsize=8)
    
    # Add statistics
    total_points = sum(points)
    active_days = len([p for p in points if p > 0])
    avg_points = total_points / active_days if active_days > 0 else 0
    
    stats_text = f'Всего баллов: {format_points(total_points)} | Активных дней: {active_days} | Среднее: {format_points(avg_points)}'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    
    # Save to buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    return buffer

@router.message(Command("insight"))
async def cmd_insight(message: Message):
    """Provide AI-generated insights about user's progress"""
    try:
        user_id = message.from_user.id
        now = datetime.now(TIMEZONE)
        current_day = now.day
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        
        # Get current month stats
        current_points = await db.get_user_points_for_month(user_id, now.year, now.month)
        daily_stats = await db.get_user_daily_stats(user_id, now.year, now.month)
        
        # Get previous month stats
        prev_month = now.month - 1 if now.month > 1 else 12
        prev_year = now.year if now.month > 1 else now.year - 1
        prev_points = await db.get_user_points_for_month(user_id, prev_year, prev_month)
        
        if current_points == 0 and len(daily_stats) == 0:
            await message.answer(
                "🤖 Анализ прогресса\\n\\n"
                "📊 Пока нет данных для анализа. Начните выполнять модули, "
                "и я смогу предоставить подробную аналитику вашего прогресса!"
            )
            return
        
        # Generate insights
        insights = generate_progress_insights(
            user_id, current_points, prev_points, daily_stats, days_in_month, current_day
        )
        
        user_name = get_user_display_name(message.from_user)
        month_name = MonthNames.get_full_month_name(now.month)
        
        response = f"🤖 ИИ-анализ прогресса\\n👤 {user_name}\\n📅 {month_name} {now.year}\\n\\n{insights}"
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error in cmd_insight: {e}")
        await message.answer("❌ Произошла ошибка при генерации анализа.")

# Pagination handler for modules keyboard
@router.callback_query(F.data.startswith("modules_page_"))
async def handle_modules_pagination(callback: CallbackQuery):
    """Handle pagination for modules keyboard"""
    try:
        page = int(callback.data.split("_")[2])
        modules = await db.get_modules()
        
        from utils import create_modules_keyboard
        keyboard = create_modules_keyboard(modules, page)
        
        await callback.message.edit_text(
            "📚 Выберите модуль для добавления:",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in handle_modules_pagination: {e}")
        await callback.answer("❌ Ошибка при переключении страницы!", show_alert=True)
