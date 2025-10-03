from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, User
from typing import List, Dict
import math

def format_points(points: float) -> str:
    """Format points with proper decimal display"""
    if points == int(points):
        return str(int(points))
    return f"{points:.1f}"

def get_user_display_name(user: User) -> str:
    """Get user display name (first name or username)"""
    if user.first_name:
        return user.first_name
    elif user.username:
        return f"@{user.username}"
    else:
        return f"User{user.id}"

def create_modules_keyboard(modules: List[Dict], page: int = 0, per_page: int = 8) -> InlineKeyboardMarkup:
    """Create inline keyboard for module selection with pagination"""
    keyboard = []
    
    # Calculate pagination
    total_pages = math.ceil(len(modules) / per_page)
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(modules))
    
    # Add module buttons (2 per row)
    for i in range(start_idx, end_idx, 2):
        row = []
        
        # First module in row
        module = modules[i]
        button_text = f"{module['name']} ({format_points(module['points'])})"
        row.append(InlineKeyboardButton(
            text=button_text, 
            callback_data=f"module_{module['id']}"
        ))
        
        # Second module in row (if exists)
        if i + 1 < end_idx:
            module = modules[i + 1]
            button_text = f"{module['name']} ({format_points(module['points'])})"
            row.append(InlineKeyboardButton(
                text=button_text, 
                callback_data=f"module_{module['id']}"
            ))
        
        keyboard.append(row)
    
    # Add pagination buttons if needed
    if total_pages > 1:
        pagination_row = []
        
        if page > 0:
            pagination_row.append(InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"modules_page_{page-1}"
            ))
        
        pagination_row.append(InlineKeyboardButton(
            text=f"{page+1}/{total_pages}", 
            callback_data="noop"
        ))
        
        if page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(
                text="Вперед ➡️", 
                callback_data=f"modules_page_{page+1}"
            ))
        
        keyboard.append(pagination_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_rank_emoji(position: int) -> str:
    """Get emoji for leaderboard position"""
    if position == 1:
        return "🥇"
    elif position == 2:
        return "🥈"
    elif position == 3:
        return "🥉"
    else:
        return f"{position}."

def calculate_monthly_progress_score(current_points: float, previous_points: float, days_in_month: int, current_day: int) -> int:
    """Calculate progress score from 1 to 10 based on various factors"""
    
    # Base score calculation
    if previous_points == 0:
        # New user - judge by current performance
        daily_average = current_points / current_day if current_day > 0 else 0
        projected_monthly = daily_average * days_in_month
        
        # Score based on projected monthly performance
        if projected_monthly >= 300:
            base_score = 10
        elif projected_monthly >= 200:
            base_score = 8
        elif projected_monthly >= 100:
            base_score = 6
        elif projected_monthly >= 50:
            base_score = 4
        else:
            base_score = 2
    else:
        # Existing user - compare with previous month
        progress_ratio = current_points / previous_points if previous_points > 0 else 1
        
        if progress_ratio >= 1.5:  # 50% improvement
            base_score = 10
        elif progress_ratio >= 1.2:  # 20% improvement
            base_score = 8
        elif progress_ratio >= 1.0:  # Maintaining level
            base_score = 6
        elif progress_ratio >= 0.8:  # Slight decline
            base_score = 4
        else:  # Significant decline
            base_score = 2
    
    # Consistency bonus (check if user is actively participating)
    consistency_bonus = 1 if current_points > 0 else -1
    
    # Final score (1-10 range)
    final_score = max(1, min(10, base_score + consistency_bonus))
    
    return final_score

def generate_progress_insights(user_id: int, current_points: float, previous_points: float, 
                             daily_stats: Dict[int, float], days_in_month: int, current_day: int) -> str:
    """Generate AI-like insights based on user statistics"""
    
    score = calculate_monthly_progress_score(current_points, previous_points, days_in_month, current_day)
    
    # Calculate some stats
    daily_average = current_points / current_day if current_day > 0 else 0
    projected_monthly = daily_average * days_in_month
    active_days = len(daily_stats)
    activity_rate = (active_days / current_day * 100) if current_day > 0 else 0
    
    insights = []
    
    # Performance assessment
    if score >= 8:
        insights.append("🔥 Отличная работа! Ваш прогресс впечатляет!")
    elif score >= 6:
        insights.append("👍 Хорошие результаты! Продолжайте в том же духе.")
    elif score >= 4:
        insights.append("📈 Есть потенциал для улучшения. Попробуйте быть более активными.")
    else:
        insights.append("💪 Время взяться за дело! Увеличьте активность.")
    
    # Activity insights
    if activity_rate >= 80:
        insights.append(f"📅 Отличная регулярность! Активны {active_days} из {current_day} дней ({activity_rate:.0f}%).")
    elif activity_rate >= 50:
        insights.append(f"📅 Неплохая регулярность: {active_days} из {current_day} дней ({activity_rate:.0f}%). Можно чаще!")
    else:
        insights.append(f"📅 Стоит быть активнее: только {active_days} из {current_day} дней ({activity_rate:.0f}%).")
    
    # Progress comparison
    if previous_points > 0:
        change_percent = ((current_points - previous_points) / previous_points) * 100
        if change_percent > 20:
            insights.append(f"📊 Прогресс к прошлому месяцу: +{change_percent:.0f}%! Впечатляющий рост!")
        elif change_percent > 0:
            insights.append(f"📊 Прогресс к прошлому месяцу: +{change_percent:.0f}%. Движемся вперед!")
        elif change_percent > -20:
            insights.append(f"📊 Небольшое снижение: {change_percent:.0f}%. Время вернуться к активности!")
        else:
            insights.append(f"📊 Значительное снижение: {change_percent:.0f}%. Нужно срочно активизироваться!")
    
    # Projection
    insights.append(f"🎯 Прогноз на месяц: {format_points(projected_monthly)} баллов.")
    
    # Recommendations
    if daily_average < 5:
        insights.append("💡 Совет: попробуйте выполнять хотя бы один модуль в день.")
    elif daily_average < 10:
        insights.append("💡 Совет: увеличьте сложность модулей или их количество.")
    else:
        insights.append("💡 Вы на правильном пути! Поддерживайте темп.")
    
    return "\n\n".join(insights)

class MonthNames:
    """Russian month names"""
    NAMES = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    
    FULL_NAMES = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    
    @classmethod
    def get_month_name(cls, month: int) -> str:
        return cls.NAMES.get(month, str(month))
    
    @classmethod
    def get_full_month_name(cls, month: int) -> str:
        return cls.FULL_NAMES.get(month, str(month))
