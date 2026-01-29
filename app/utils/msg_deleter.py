from aiogram.fsm.context import FSMContext

from config import bot


class MessageDeleter:
    @classmethod
    async def delete_messages(
            cls,
            state: FSMContext,
            user_telegram_id: int,
            only_media: bool = False
    ):
        """
        use: await MessageDeleter.delete_messages(state, message.from_user.id)
        """
        data = await state.get_data()

        action_message_ids = data.get("action_message_ids", [])
        media_message_ids = data.get("media_message_ids", [])

        try:
            for msg_id in media_message_ids:
                try:
                    await bot.delete_message(message_id=msg_id, chat_id=user_telegram_id)
                except Exception:
                    continue
                data.pop("media_message_ids", None)

            if not only_media:
                for msg_id in action_message_ids:
                    try:
                        await bot.delete_message(chat_id=user_telegram_id, message_id=msg_id)
                    except Exception:
                        continue

                    data.pop("action_message_ids", None)

            await state.set_data(data)
        except Exception:
            pass

    @classmethod
    async def add_messages(
            cls,
            state: FSMContext,
            message_id: int,
            message_type: str = "action_message_ids",
    ):
        """
        use: await MessageDeleter.add_messages(state, message.message_id)
        """
        data = await state.get_data()

        match message_type:
            case "action_message_ids":
                action_ids = data.get("action_message_ids") or []
                action_ids.append(message_id)
                await state.update_data(action_message_ids=action_ids)

            case "media_message_ids":
                media_ids = data.get("media_message_ids") or []
                media_ids.append(message_id)
                await state.update_data(media_message_ids=media_ids)