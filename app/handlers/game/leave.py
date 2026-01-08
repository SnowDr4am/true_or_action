from aiogram import F
from aiogram.types import CallbackQuery

from ..main import user_router
from app.database.services import RoomService, UserService
import app.keyboards.user.start as kb


@user_router.callback_query(F.data.startswith("room:leave"))
async def handle_create_room(callback: CallbackQuery):
    await callback.answer()

    await RoomService.leave_room(telegram_id=callback.from_user.id)

    user = await UserService.get_user(
        telegram_id=callback.from_user.id,
        with_room=True
    )
    await callback.message.edit_text(
        "<b>Играем в «Правду или Действие»</b>\n\n"
        "<i>Без скуки, неловких пауз и лишних правил</i>",
        parse_mode="HTML",
        reply_markup=kb.generate_start_menu(user),
    )
