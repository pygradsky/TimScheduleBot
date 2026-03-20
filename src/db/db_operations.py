import aiosqlite

db: aiosqlite.Connection | None = None


async def init_db(db_file: str) -> None:
    global db
    db = await aiosqlite.connect(db_file)
    db.row_factory = aiosqlite.Row


async def close_db():
    if db:
        await db.close()


async def create_table() -> None:
    await db.execute(
        """CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        group_id INTEGER NOT NULL,
        faculty TEXT NOT NULL,
        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
        """
    )
    await db.commit()


async def save_user_info(user_id: int, username: str) -> None:
    await db.execute(
        "INSERT OR IGNORE INTO users (user_id, username, group_id, faculty) VALUES (?, ?, ?, ?)",
        (user_id, username, 0, '')
    )
    await db.commit()


async def get_user_info(user_id: int) -> dict | None:
    cur = await db.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = await cur.fetchone()

    if row:
        return dict(row)
    return None


async def update_user_info(user_id: int, new_group_id: int, new_faculty: str) -> None:
    await db.execute(
        "UPDATE users SET group_id = ?, faculty = ? WHERE user_id = ?",
        (new_group_id, new_faculty, user_id)
    )
    await db.commit()
