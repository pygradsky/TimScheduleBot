import os
import aiosqlite

from src.configs.config import DataConfig

data_config = DataConfig()

db_file = os.path.join(data_config.db_dir, 'users.db')
dirs_to_create = [
    data_config.data_dir,
    data_config.downloads_dir,
    data_config.db_dir,
]


async def _create_dirs() -> None:
    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)


async def _create_table() -> None:
    async with aiosqlite.connect(db_file) as conn:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            group_id INTEGER NOT NULL,
            faculty TEXT NOT NULL,
            join_date DEFAULT CURRENT_TIMESTAMP NOT NULL
            )"""
        )


async def setup() -> None:
    await _create_dirs()
    await _create_table()
