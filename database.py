import asyncpg
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from config import DATABASE_URL, DEFAULT_MODULES

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None
    
    async def init(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL)
            await self.create_tables()
            await self.populate_default_modules()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def create_tables(self):
        """Create all necessary tables"""
        async with self.pool.acquire() as conn:
            # Modules table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS modules (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    points NUMERIC NOT NULL
                )
            """)
            
            # User module logs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_module_logs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    module_id INT NOT NULL REFERENCES modules(id),
                    date DATE NOT NULL DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Admins table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id BIGINT PRIMARY KEY
                )
            """)
            
            # Monthly summary table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS monthly_summary (
                    user_id BIGINT,
                    year INT,
                    month INT,
                    total_points NUMERIC,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, year, month)
                )
            """)
            
            # Create indexes for better performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_module_logs_user_date 
                ON user_module_logs(user_id, date)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_monthly_summary_user_year_month 
                ON monthly_summary(user_id, year, month)
            """)
    
    async def populate_default_modules(self):
        """Populate database with default modules if empty"""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM modules")
            if count == 0:
                for name, points in DEFAULT_MODULES:
                    await conn.execute(
                        "INSERT INTO modules (name, points) VALUES ($1, $2)",
                        name, points
                    )
                logger.info("Default modules populated")
    
    async def get_modules(self) -> List[Dict]:
        """Get all available modules"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, name, points FROM modules ORDER BY name")
            return [dict(row) for row in rows]
    
    async def get_module_by_name(self, name: str) -> Optional[Dict]:
        """Get module by name"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, points FROM modules WHERE LOWER(name) = LOWER($1)",
                name
            )
            return dict(row) if row else None
    
    async def add_module_completion(self, user_id: int, module_id: int, date_completed: date = None):
        """Add a module completion for a user"""
        if date_completed is None:
            date_completed = date.today()
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO user_module_logs (user_id, module_id, date) VALUES ($1, $2, $3)",
                user_id, module_id, date_completed
            )
    
    async def get_user_points_for_month(self, user_id: int, year: int, month: int) -> float:
        """Get total points for user in specific month"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT COALESCE(SUM(m.points), 0)
                FROM user_module_logs uml
                JOIN modules m ON uml.module_id = m.id
                WHERE uml.user_id = $1 
                AND EXTRACT(YEAR FROM uml.date) = $2 
                AND EXTRACT(MONTH FROM uml.date) = $3
            """, user_id, year, month)
            return float(result) if result else 0.0
    
    async def get_user_daily_stats(self, user_id: int, year: int, month: int) -> Dict[int, float]:
        """Get daily points breakdown for user in specific month"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT EXTRACT(DAY FROM uml.date)::INT as day, SUM(m.points) as points
                FROM user_module_logs uml
                JOIN modules m ON uml.module_id = m.id
                WHERE uml.user_id = $1 
                AND EXTRACT(YEAR FROM uml.date) = $2 
                AND EXTRACT(MONTH FROM uml.date) = $3
                GROUP BY EXTRACT(DAY FROM uml.date)
                ORDER BY day
            """, user_id, year, month)
            return {row['day']: float(row['points']) for row in rows}
    
    async def get_leaderboard(self, year: int, month: int, limit: int = 20) -> List[Dict]:
        """Get leaderboard for specific month"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    uml.user_id,
                    SUM(m.points) as total_points,
                    COUNT(*) as completions
                FROM user_module_logs uml
                JOIN modules m ON uml.module_id = m.id
                WHERE EXTRACT(YEAR FROM uml.date) = $1 
                AND EXTRACT(MONTH FROM uml.date) = $2
                GROUP BY uml.user_id
                ORDER BY total_points DESC
                LIMIT $3
            """, year, month, limit)
            return [dict(row) for row in rows]
    
    async def get_user_last_action(self, user_id: int) -> Optional[Dict]:
        """Get user's last module completion for undo functionality"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT uml.id, uml.module_id, m.name, m.points, uml.date
                FROM user_module_logs uml
                JOIN modules m ON uml.module_id = m.id
                WHERE uml.user_id = $1
                ORDER BY uml.created_at DESC
                LIMIT 1
            """, user_id)
            return dict(row) if row else None
    
    async def undo_last_action(self, user_id: int) -> bool:
        """Undo user's last module completion"""
        async with self.pool.acquire() as conn:
            last_action = await self.get_user_last_action(user_id)
            if not last_action:
                return False
            
            await conn.execute(
                "DELETE FROM user_module_logs WHERE id = $1",
                last_action['id']
            )
            return True
    
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT 1 FROM admins WHERE user_id = $1",
                user_id
            )
            return result is not None
    
    async def add_admin(self, user_id: int):
        """Add user as admin"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO admins (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
                user_id
            )
    
    async def get_all_users(self) -> List[int]:
        """Get all users who have logged modules"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT DISTINCT user_id FROM user_module_logs")
            return [row['user_id'] for row in rows]
    
    async def save_monthly_summary(self, user_id: int, year: int, month: int, total_points: float):
        """Save monthly summary for user"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO monthly_summary (user_id, year, month, total_points) 
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, year, month) 
                DO UPDATE SET total_points = $4
            """, user_id, year, month, total_points)

# Global database instance
db = Database()
