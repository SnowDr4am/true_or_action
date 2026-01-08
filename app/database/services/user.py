from typing import List, Optional

from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload
from ..models import AsyncSessionLocal, User


class UserService:
    @classmethod
    async def get_users(
            cls,
            *,
            telegram_id: int | None = None,
            username: str | None = None,
            room_id: int | None = None,
            order_index: int | None = None,

            with_room: bool = False,

            limit: int | None = None,
            offset: int | None = None,
            order_by: str | None = None,
    ) -> List[User]:
        conditions = []

        if telegram_id is not None:
            conditions.append(User.telegram_id == telegram_id)
        if username is not None:
            conditions.append(User.username == username)
        if room_id is not None:
            conditions.append(User.room_id == room_id)
        if order_index is not None:
            conditions.append(User.order_index == order_index)

        stmt = select(User)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        if with_room:
            stmt = stmt.options(selectinload(User.room))

        if order_by:
            desc = order_by.startswith("-")
            field = order_by[1:] if desc else order_by
            if hasattr(User, field):
                col = getattr(User, field)
                stmt = stmt.order_by(col.desc() if desc else col.asc())
            else:
                stmt = stmt.order_by(User.telegram_id.asc())
        else:
            stmt = stmt.order_by(User.telegram_id.asc())

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        async with AsyncSessionLocal() as session:
            res = await session.execute(stmt)
            return list(res.scalars().unique().all())

    @classmethod
    async def get_user(cls, **kwargs) -> User | None:
        rows = await cls.get_users(limit=1, **kwargs)
        return rows[0] if rows else None

    @classmethod
    async def save_or_update(
        cls,
        telegram_id: int,
        *,
        username: str | None = None,
        room_id: int | None = None,
        order_index: int | None = None,
        meta_data: dict | None = None,
    ) -> Optional[User]:
        async with AsyncSessionLocal() as session:
            current = await session.execute(
                select(User).where(User.telegram_id == telegram_id).limit(1)
            )
            entity = current.scalars().first()

            if entity:
                if username is not None:
                    entity.username = username
                if room_id is not None:
                    entity.room_id = room_id
                if order_index is not None:
                    entity.order_index = order_index
                if meta_data is not None:
                    entity.meta_data = meta_data

                await session.commit()
                await session.refresh(entity)
                return entity

            entity = User(
                telegram_id=telegram_id,
                username=username,
                room_id=room_id,
                order_index=order_index,
                meta_data=meta_data or {},
            )
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    @classmethod
    async def set_room(
        cls,
        telegram_id: int,
        *,
        room_id: int | None,
        order_index: int | None,
    ) -> None:
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(room_id=room_id, order_index=order_index)
            )
            await session.commit()
