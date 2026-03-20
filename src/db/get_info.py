import os
import aiosqlite

from src.configs.config import DataConfig

data_config = DataConfig()
db_file = os.path.join(data_config.db_dir, 'users.db')
users_cache = {}


async def get_db_info(user_id: int) -> dict | None:
    async with aiosqlite.connect(db_file) as conn:
        cur = await conn.execute(
            "SELECT user_id, username, group_id, faculty, join_date FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cur.fetchone()
        
        if row:
            return {
                'user_id': row[0],
                'username': row[1],
                'group_id': row[2],
                'faculty': row[3],
                'join_date': row[4]
            }
        return None


async def get_cached_info(user_id: int) -> dict:
    if user_id not in users_cache:
        user_data = await get_db_info(user_id)
        users_cache[user_id] = user_data
    
    return users_cache[user_id]
