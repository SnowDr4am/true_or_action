import os
from dotenv import load_dotenv
from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage
from aiogram import Bot, Dispatcher


load_dotenv()

# ──────────────────────────────────────
# PostgreSQL / Database
# ──────────────────────────────────────
ASYNC_DATABASE_URL: str | None = os.getenv("ASYNC_DATABASE_URL")

POSTGRES_USER: str | None = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD: str | None = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB: str | None = os.getenv("POSTGRES_DB")
POSTGRES_HOST: str | None = os.getenv("POSTGRES_HOST")
POSTGRES_PORT: str | None = os.getenv("POSTGRES_PORT")


# ──────────────────────────────────────
# Telegram Bot
# ──────────────────────────────────────
BOT_TOKEN: str | None = os.getenv("BOT_TOKEN")


# ──────────────────────────────────────
# Redis (FSM / rate limit / cache)
# ──────────────────────────────────────
REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD") or None
REDIS_DB: int = int(os.getenv("REDIS_DB", "1"))


# ──────────────────────────────────────
# Runtime objects (Redis, FSM storage, Bot, Dispatcher)
# ──────────────────────────────────────
# Redis client для работы с очередями (decode_responses=False для работы с интами)
redis_client: Redis = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    decode_responses=False,  # False для работы с числами
)

# Redis client для FSM (decode_responses=True)
redis_fsm_client: Redis = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    decode_responses=True,
)

storage: RedisStorage = RedisStorage(redis=redis_fsm_client)

bot: Bot = Bot(token=BOT_TOKEN)
dp: Dispatcher = Dispatcher(storage=storage)