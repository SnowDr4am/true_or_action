import os
import sys
import asyncio
import datetime
import shutil
import subprocess
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from dotenv import load_dotenv

# ─────────────────────────────────────────
# Подготовка окружения и sys.path
# ─────────────────────────────────────────

# гарантируем, что корень проекта в PYTHONPATH
# env.py находится в <root>/alembic/env.py → parents[1] это <root>
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv()

# теперь можно тянуть наш код
from app.database.models import Base
from app.utils.func import EKB_TZ

# ─────────────────────────────────────────
# ЛОГИ
# ─────────────────────────────────────────

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ─────────────────────────────────────────
# URL БД (ASYNC)
# ─────────────────────────────────────────

ASYNC_DB_URL = os.getenv("ASYNC_DATABASE_URL")
if not ASYNC_DB_URL:
    raise RuntimeError("ASYNC_DATABASE_URL is not set")

config.set_main_option("sqlalchemy.url", ASYNC_DB_URL)

POSTGRES_DB = os.getenv("POSTGRES_DB", "db")

# ─────────────────────────────────────────
# metadata моделей
# ─────────────────────────────────────────

target_metadata = Base.metadata

# ─────────────────────────────────────────
# Настройки бэкапа
# ─────────────────────────────────────────

BACKUP_DIR = Path("static/backup")


def ensure_backup_dir() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def to_sync_url(async_url: str) -> str:
    """
    Преобразуем postgresql+asyncpg://... -> postgresql://... для pg_dump.
    """
    return async_url.replace("postgresql+asyncpg://", "postgresql://")


def pg_dump_available() -> bool:
    """Проверяем, доступен ли pg_dump в PATH."""
    return shutil.which("pg_dump") is not None


def make_backup(async_url: str) -> None:
    """
    Создать .sql бэкап в static/backup перед миграцией.
    Имя: {POSTGRES_DB}_YYYY-MM-DD_HH-MM-SS.sql (в EKB_TZ)
    """
    if not pg_dump_available():
        print("[alembic] WARN: pg_dump not found in PATH — skipping backup.")
        return

    ensure_backup_dir()

    ts = datetime.datetime.now(EKB_TZ).strftime("%Y-%m-%d_%H-%M-%S")
    sql_path = BACKUP_DIR / f"{POSTGRES_DB}_{ts}.sql"

    sync_url = to_sync_url(async_url)

    cmd = ["pg_dump", "-f", str(sql_path), sync_url]

    print(f"[alembic] Creating backup: {sql_path}")
    try:
        subprocess.run(cmd, check=True)
        print(f"[alembic] Backup created: {sql_path}")
    except subprocess.CalledProcessError as e:
        print(f"[alembic] WARN: backup failed: {e}. Continuing without backup.")

# ─────────────────────────────────────────
# OFFLINE режим
# ─────────────────────────────────────────

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

# ─────────────────────────────────────────
# ONLINE режим
# ─────────────────────────────────────────

def _detect_cmd() -> str:
    """
    Понять, что конкретно вызвал alembic:
    upgrade / downgrade / revision / ...
    чтобы решить — делать ли бэкап.
    """
    cmd_opts = getattr(config, "cmd_opts", None)
    if cmd_opts is not None and hasattr(cmd_opts, "cmd"):
        cmd = cmd_opts.cmd
        if isinstance(cmd, (list, tuple)):
            return cmd[0] if cmd else ""
        if isinstance(cmd, str):
            return cmd

    for token in sys.argv[1:4]:
        if token in {
            "upgrade",
            "downgrade",
            "revision",
            "history",
            "current",
            "heads",
            "branches",
            "show",
            "check",
        }:
            return token
    return ""


async def run_migrations_online():
    alembic_cmd = _detect_cmd()

    # бэкапим только когда реально трогаем схему
    if alembic_cmd in {"upgrade", "downgrade"}:
        try:
            make_backup(ASYNC_DB_URL)
        except Exception as e:
            print(f"[alembic] Backup warning: {e}")

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

# ─────────────────────────────────────────
# Запуск
# ─────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())