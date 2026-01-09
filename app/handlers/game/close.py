from aiogram import F
from aiogram.types import CallbackQuery

from ..main import user_router
from app.database.services import RoomService, UserService
import app.keyboards.user.start as kb


@user_router.callback_query(F.data.startswith("room:close:"))
async def handle_close_room(callback: CallbackQuery):
    await callback.answer()

    room_id = int(callback.data.split(":")[-1])

    room = await RoomService.get_room(room_id=room_id, with_players=True)
    if not room:
        return

    owner_id = room.owner_id
    caller_id = callback.from_user.id

    if caller_id != owner_id:
        return await callback.answer("Только создатель комнаты может закрыть игру", show_alert=True)

    players = getattr(room, "players", []) or []
    recipients = [p.telegram_id for p in players if p.telegram_id != owner_id]

    await RoomService.finish_game(room_id=room_id, by_user_id=caller_id)

    user = await UserService.get_user(telegram_id=caller_id, with_room=True)
    await callback.message.edit_text(
        "<b>Играем в «Правду или Действие»</b>\n\n"
        "<i>Без скуки, неловких пауз и лишних правил</i>",
        parse_mode="HTML",
        reply_markup=kb.generate_start_menu(user),
    )

    for chat_id in recipients:
        try:
            await callback.bot.send_message(
                chat_id=chat_id,
                text="⛔️ Создатель комнаты завершил игру. Возвращаемся в меню.",
                parse_mode="HTML",
                reply_markup=kb.generate_simple_keyboard("🏠 В главное меню", "cmd_start"),
            )
        except Exception:
            pass