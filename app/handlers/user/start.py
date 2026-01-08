from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

from ..main import user_router
import app.keyboards.user.start as kb
from app.database.services import RoomService, UserService
from app.database.models import User


async def handle_start_payload(message: Message, payload: str, user: User):
    if not payload:
        return None

    async def invalid():
        return await message.answer(
            "⚠️ Эта ссылка не ведёт ни в одну комнату\n"
            "<i>Похоже, она устарела или была скопирована с ошибкой</i>",
            parse_mode="HTML",
            reply_markup=kb.delete_message_keyboard
        )

    if payload.startswith("room_"):
        invite_code = payload[5:]
        if not len(invite_code) == 16:
            return await invalid()

        room = await RoomService.get_room(invite_code=invite_code)
        if not room:
            return await invalid()

        if user.room_id == room.id:
            return await cmd_start(message)

        if user.room_id is not None and user.room_id != room.id:
            old_room_id = user.room_id
            old_room = getattr(user, "room", None)

            if old_room and old_room.owner_id == user.telegram_id:
                await RoomService.finish_game(room_id=old_room_id, by_user_id=user.telegram_id)
            else:
                await RoomService.leave_room(telegram_id=user.telegram_id)

        players_count = await RoomService.join_room(room_id=room.id, telegram_id=message.from_user.id)

        return await message.answer(
            "✅ Ты в комнате\n\n"

            f"👥 Сейчас участников: <b>{players_count}</b>\n\n"

            "⏳ Ждём, когда владелец запустит игру",
            parse_mode="HTML",
            reply_markup=kb.delete_message_keyboard,
        )
    return await invalid()



@user_router.message(CommandStart(deep_link=True))
async def start_with_payload(message: Message, command: CommandObject):
    try:
        await message.delete()
    except Exception:
        pass

    user = await UserService.get_user(telegram_id=message.from_user.id)
    if not user:
        await UserService.save_or_update(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        user = await UserService.get_user(
            telegram_id=message.from_user.id,
            with_room=True
        )
    else:
        if message.from_user.username and message.from_user.username != user.username:
            await UserService.save_or_update(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
            )

    payload = (command.args or "").strip()

    try:
        result = await handle_start_payload(message, payload, user)
        if result is not None:
            return result
    except Exception:
        return await message.answer(
            "⚠️ <b>Что-то пошло не так</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "Ссылка не сработала или возникла ошибка\n"
            "Попробуй ещё раз чуть позже\n\n"

            "━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML",
            reply_markup=kb.delete_message_keyboard
        )

    return await cmd_start(message)

@user_router.message(CommandStart())
async def cmd_start(message: Message):
    try:
        await message.delete()
    except Exception:
        pass

    user = await UserService.get_user(
        telegram_id=message.from_user.id,
        with_room=True
    )
    if not user:
        await UserService.save_or_update(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        user = await UserService.get_user(
            telegram_id=message.from_user.id,
            with_room=True
        )
    else:
        if message.from_user.username and message.from_user.username != user.username:
            await UserService.save_or_update(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
            )

    room_block = ""
    if getattr(user, "room", None):
        room = user.room
        count = room.players_count or 0

        me = await message.bot.get_me()
        invite_link = f"https://t.me/{me.username}?start=room_{room.invite_code}"

        room_block = (
            "\n━━━━━━━━━━━━━━━\n\n"

            "🏠 <b>Твоя комната</b>\n"
            f"• ID: <b>#{room.id}</b>\n"
            f"• Сейчас внутри: <b>{count}</b>\n\n"

            "🔗 <b>Ссылка-приглашение</b>\n"
            f"<code>{invite_link}</code>\n\n"
            "<i>Скинь друзьям, чтобы они залетели в игру</i>\n\n"

            "━━━━━━━━━━━━━━━"
        )

    await message.answer(
        "<b>Играем в «Правду или Действие»</b>\n\n"
        "<i>Без скуки, неловких пауз и лишних правил</i>"
        f"{room_block}",
        parse_mode="HTML",
        reply_markup=kb.generate_start_menu(user)
    )