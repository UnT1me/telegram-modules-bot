import os
from dotenv import load_dotenv
import pytz

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Europe/Moscow"))
ADMIN_IDS = [int(id_) for id_ in os.getenv("ADMIN_IDS", "").split(",") if id_.strip()]

# Time restrictions
ALLOWED_HOUR_START = 18
ALLOWED_HOUR_END = 23

# Points to money conversion
POINTS_TO_MONEY_RATE = 220  # ₽ per point

# Default modules with points
DEFAULT_MODULES = [
    ("BMU 5X", 14.5),
    ("BMU 10X", 29.0),
    ("Практика 1", 10.0),
    ("Практика 2", 15.0),
    ("Теория", 8.0),
    ("Дополнительный модуль", 12.5),
]
