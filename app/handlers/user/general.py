from aiogram import F
from aiogram.types import CallbackQuery

from ..main import user_router


@user_router.callback_query(F.data == "delete-message")
async def handle_delete_message(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        await callback.answer("⚠️ Возникла ошибка", show_alert=True)