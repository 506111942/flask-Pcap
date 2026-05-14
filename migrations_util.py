"""SQLite 轻量迁移：为已有 packets.db 增加列并同步超级用户规则。"""

from sqlalchemy import text


def _table_columns(conn, table: str):
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return [r[1] for r in rows]


def apply_sqlite_migrations(engine):
    """在 create_all 之后调用，仅补充缺失列。"""
    with engine.begin() as conn:
        cols = _table_columns(conn, "user")
        if "is_superuser" not in cols:
            conn.execute(text("ALTER TABLE user ADD COLUMN is_superuser INTEGER NOT NULL DEFAULT 0"))
        cols = _table_columns(conn, "capture_file")
        if "user_id" not in cols:
            conn.execute(text("ALTER TABLE capture_file ADD COLUMN user_id INTEGER"))
