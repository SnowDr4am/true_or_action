from aiogram import F
from aiogram.types import CallbackQuery

from ..main import user_router
from app.database.services import RoomService, UserService
import app.keyboards.user.start as kb


@user_router.callback_query(F.data == "room:create")
async def handle_create_room(callback: CallbackQuery):
    await callback.answer()

    room = await RoomService.create_room(owner_id=callback.from_user.id)
    await RoomService.join_room(
        telegram_id=callback.from_user.id,
        room_id=room.id
    )
    user = await UserService.get_user(
        telegram_id=callback.from_user.id,
        with_room=True
    )

    room_block = ""
    if getattr(user, "room", None):
        room = user.room
        count = room.players_count or 0

        me = await callback.bot.get_me()
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

    await callback.message.edit_text(
        "<b>Играем в «Правду или Действие»</b>\n\n"
        "<i>Без скуки, неловких пауз и лишних правил</i>"
        f"{room_block}",
        parse_mode="HTML",
        reply_markup=kb.generate_start_menu(user),
    )
