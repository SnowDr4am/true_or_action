from typing import List, Optional, Dict
from uuid import uuid4

from sqlalchemy import select, and_, update
from ..models import AsyncSessionLocal, Room, RoomStatus, User


class RoomService:
    @classmethod
    async def get_rooms(
        cls,
        *,
        room_id: int | None = None,
        owner_id: int | None = None,
        status: RoomStatus | str | None = None,
        invite_code: str | None = None,

        with_players: bool = False,

        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
    ) -> List[Room]:
        conditions = []

        if room_id is not None:
            conditions.append(Room.id == room_id)
        if owner_id is not None:
            conditions.append(Room.owner_id == owner_id)
        if status is not None:
            status_val = status.value if isinstance(status, RoomStatus) else status
            conditions.append(Room.status == status_val)
        if invite_code is not None:
            conditions.append(Room.invite_code == invite_code)

        stmt = select(Room)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        if order_by:
            desc = order_by.startswith("-")
            field = order_by[1:] if desc else order_by
            if hasattr(Room, field):
                col = getattr(Room, field)
                stmt = stmt.order_by(col.desc() if desc else col.asc())
            else:
                stmt = stmt.order_by(Room.id.asc())
        else:
            stmt = stmt.order_by(Room.id.asc())

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        async with AsyncSessionLocal() as session:
            res = await session.execute(stmt)
            rooms = list(res.scalars().unique().all())

            if not with_players or not rooms:
                return rooms

            room_ids = [r.id for r in rooms]

            players_res = await session.execute(
                select(User)
                .where(User.room_id.in_(room_ids))
                .order_by(User.room_id.asc(), User.order_index.asc().nulls_last(), User.telegram_id.asc())
            )
            players = list(players_res.scalars().unique().all())

            grouped: Dict[int, List[User]] = {}
            for p in players:
                if p.room_id is None:
                    continue
                grouped.setdefault(p.room_id, []).append(p)

            for r in rooms:
                setattr(r, "players", grouped.get(r.id, []))

            return rooms

    @classmethod
    async def get_room(cls, **kwargs) -> Room | None:
        rows = await cls.get_rooms(limit=1, **kwargs)
        return rows[0] if rows else None

    @classmethod
    async def create_room(cls, *, owner_id: int) -> Room:
        async with AsyncSessionLocal() as session:
            entity = Room(
                owner_id=owner_id,
                status=RoomStatus.WAITING,
                current_truth_number=1,
                current_action_number=1,
                players_count=0,
                invite_code=uuid4().hex[:16]
            )
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    @classmethod
    async def join_room(cls, *, room_id: int, telegram_id: int) -> int:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                room_res = await session.execute(
                    select(Room).where(Room.id == room_id).with_for_update()
                )
                room = room_res.scalars().first()
                if not room:
                    raise ValueError("Room not found")

                if room.status != RoomStatus.WAITING:
                    raise ValueError("Room is not joinable (not WAITING)")

                user_res = await session.execute(
                    select(User).where(User.telegram_id == telegram_id).with_for_update()
                )
                user = user_res.scalars().first()
                if not user:
                    raise ValueError("User not found (create user first)")

                if user.room_id is not None and user.room_id != room_id:
                    raise ValueError(f"User already in room {user.room_id}")

                if user.room_id == room_id:
                    return user.order_index if user.order_index is not None else 0

                order_index = room.players_count

                user.room_id = room_id
                user.order_index = order_index
                room.players_count = room.players_count + 1

            await session.commit()
            return room.players_count

    @classmethod
    async def leave_room(cls, *, telegram_id: int) -> Optional[int]:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                user_res = await session.execute(
                    select(User).where(User.telegram_id == telegram_id).with_for_update()
                )
                user = user_res.scalars().first()
                if not user or user.room_id is None:
                    return None

                room_id = user.room_id

                room_res = await session.execute(
                    select(Room).where(Room.id == room_id).with_for_update()
                )
                room = room_res.scalars().first()

                if room and room.players_count and room.players_count > 0:
                    room.players_count = room.players_count - 1

                user.room_id = None
                user.order_index = None

            await session.commit()
            return room_id

    @classmethod
    async def start_game(cls, *, room_id: int, by_user_id: int) -> List[int]:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                room_res = await session.execute(
                    select(Room).where(Room.id == room_id).with_for_update()
                )
                room = room_res.scalars().first()
                if not room:
                    raise ValueError("Room not found")

                if room.owner_id != by_user_id:
                    raise PermissionError("Only owner can start the game")

                if room.status != RoomStatus.WAITING:
                    raise ValueError("Room is not in WAITING")

                players_res = await session.execute(
                    select(User)
                    .where(User.room_id == room_id)
                    .order_by(User.order_index.asc().nulls_last(), User.telegram_id.asc())
                    .with_for_update()
                )
                players = list(players_res.scalars().unique().all())

                for p in players:
                    if p.order_index is None:
                        raise ValueError("Some player has no order_index")

                room.status = RoomStatus.PLAYING

            await session.commit()
            return [p.telegram_id for p in players]

    @classmethod
    async def bump_truth(cls, *, room_id: int) -> int:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                room_res = await session.execute(
                    select(Room).where(Room.id == room_id).with_for_update()
                )
                room = room_res.scalars().first()
                if not room:
                    raise ValueError("Room not found")
                room.current_truth_number += 1
                new_val = room.current_truth_number

            await session.commit()
            return new_val

    @classmethod
    async def bump_action(cls, *, room_id: int) -> int:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                room_res = await session.execute(
                    select(Room).where(Room.id == room_id).with_for_update()
                )
                room = room_res.scalars().first()
                if not room:
                    raise ValueError("Room not found")
                room.current_action_number += 1
                new_val = room.current_action_number

            await session.commit()
            return new_val

    @classmethod
    async def bump_turn(cls, *, room_id: int) -> int:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                room_res = await session.execute(
                    select(Room).where(Room.id == room_id).with_for_update()
                )
                room = room_res.scalars().first()
                if not room:
                    raise ValueError("Room not found")

                room.current_turn_number += 1
                new_val = room.current_turn_number

            await session.commit()
            return new_val

    # ---------- FINISH ----------
    @classmethod
    async def finish_game(cls, *, room_id: int, by_user_id: int) -> None:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                room_res = await session.execute(
                    select(Room).where(Room.id == room_id).with_for_update()
                )
                room = room_res.scalars().first()
                if not room:
                    raise ValueError("Room not found")

                if room.owner_id != by_user_id:
                    raise PermissionError("Only owner can finish the game")

                room.status = RoomStatus.FINISHED
                room.players_count = 0

                await session.execute(
                    update(User)
                    .where(User.room_id == room_id)
                    .values(room_id=None, order_index=None)
                )

            await session.commit()