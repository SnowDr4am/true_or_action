from aiogram import F
from aiogram.types import CallbackQuery

from ..main import user_router
from app.database.services import RoomService
import app.keyboards.game.game_service as kb
from .game_service import GameService, pick_truth, pick_action



@user_router.callback_query(F.data.startswith("room:start_game:"))
async def handle_create_room(callback: CallbackQuery):
    await callback.answer()

    room_id = int(callback.data.split(":")[-1])

    await callback.message.edit_text(
        "🎮 <b>Правда или действие — правила игры</b>\n\n"
        "Перед началом выберите <b>ведущего</b>. Ведущий следит за атмосферой и управляет игрой\n\n"

        "🔥 <b>Внимание и фокус</b>\n"
        "Во время вопроса или действия всё внимание должно быть направлено только на двух людей:\n"
        "— того, кто задаёт вопрос\n"
        "— того, кто отвечает или выполняет действие\n\n"
        "Ведущий имеет право останавливать игру, если кто-то отвлекается, смеётся, комментирует не в тему "
        "или ломает вайб\n\n"

        "💋 <b>Атмосфера</b>\n"
        "Это не игра на смех. Здесь важно создавать сексуальный вайб:\n"
        "— меньше шума\n"
        "— больше контакта\n"
        "— взгляды, паузы, интонации\n\n"

        "🔞 <b>Правда</b>\n"
        "Каждый 10-й вопрос раскрывает отдельную сексуальную тему\n"
        "Отвечать нужно честно, без ухода от темы и без шуток\n\n"

        "🔥 <b>Действие — особые правила</b>\n"
        "10, 20, 30, 40, 50 — <b>Жизнь за 5 минут</b>\n"
        "60 — <b>Уединение в отдельной комнате</b>\n"
        "70 — <b>Свет в комнате</b>\n"
        "80 — <b>Поцелуй в губы</b>\n"
        "90 — <b>Поцелуй в живот</b>\n"
        "95 — <b>БДСМ-сессия</b>\n"
        "100 — <b>Снятие трусов зубами</b>\n\n"

        "⚠️ <b>Важно</b>\n"
        "Если кто-то чувствует дискомфорт — он может сказать об этом ведущему\n"
        "Ведущий решает, как адаптировать действие, не ломая атмосферу\n\n"

        "Готовы? Тогда выбирайте — <b>Правда</b> или <b>Действие</b>",
        parse_mode="HTML",
        reply_markup=kb.confirm_rules(room_id)
    )

@user_router.callback_query(F.data.startswith("room:confirm_start:"))
async def handle_confirm_start(callback: CallbackQuery):
    await callback.answer()

    try:
        await callback.message.delete()
    except Exception:
        pass

    room_id = int(callback.data.split(":")[-1])

    await RoomService.start_game(room_id=room_id, by_user_id=callback.from_user.id)

    await GameService.broadcast(
        callback.bot,
        room_id,
        "🚀 <b>Игра стартовала</b>\n\n"
        
        "Первый игрок уже выбирает: правда или действие"
    )

    await GameService.send_turn_prompt(callback.bot, room_id)


@user_router.callback_query(F.data.startswith("room:choice:"))
async def handle_choice(callback: CallbackQuery):
    await callback.answer()

    _, _, room_id, player_id, turn, kind = callback.data.split(":")
    room_id = int(room_id)
    player_id = int(player_id)
    turn = int(turn)

    if callback.from_user.id != player_id:
        return

    room = await RoomService.get_room(room_id=room_id, with_players=False)
    if not room or (room.current_turn_number or 1) != turn:
        return

    allow_truth, allow_action = GameService.availability(room)

    if not allow_truth and not allow_action:
        try:
            await callback.message.delete()
        except Exception:
            pass
        return await GameService.end_game(callback.bot, room_id)

    if (kind == "truth" and not allow_truth) or (kind == "action" and not allow_action):
        try:
            await callback.message.delete()
        except Exception:
            pass
        return await GameService.send_turn_prompt(callback.bot, room_id)

    kind_ru = "Правда" if kind == "truth" else "Действие"

    if kind == "truth":
        task = pick_truth(room)
        await RoomService.bump_truth(room_id=room_id)
    else:
        task = pick_action(room)
        await RoomService.bump_action(room_id=room_id)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await GameService.broadcast(
        callback.bot,
        room_id,
        (
            f"👤 <b>{callback.from_user.full_name}</b> сделал выбор — <b>{kind_ru}</b>\n\n"
            
            f"🎯 Его задание: <b>{task}</b>"
        ),
        exclude_ids={callback.from_user.id},
    )

    await callback.message.answer(
        f"✅ Твой выбор — <b>{kind_ru}</b>\n\n"
        
        f"🎯 Твоё задание:\n<b>{task}</b>\n\n"
        
        "Как закончишь, жми кнопку ниже",
        parse_mode="HTML",
        reply_markup=kb.done_keyboard(room_id, player_id, turn),
    )


@user_router.callback_query(F.data.startswith("room:done:"))
async def handle_done(callback: CallbackQuery):
    await callback.answer()

    _, _, room_id, player_id, turn = callback.data.split(":")
    room_id = int(room_id)
    player_id = int(player_id)
    turn = int(turn)

    if callback.from_user.id != player_id:
        return

    room = await RoomService.get_room(room_id=room_id, with_players=False)
    if not room or (room.current_turn_number or 1) != turn:
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await GameService.broadcast(
        callback.bot,
        room_id,
        f"✅ <b>{callback.from_user.full_name}</b> закончил свой ход\n\n"
        
        "Передаём очередь дальше",
        exclude_ids={callback.from_user.id},
    )

    await RoomService.bump_turn(room_id=room_id)

    room2 = await RoomService.get_room(room_id=room_id, with_players=False)
    if room2:
        allow_truth, allow_action = GameService.availability(room2)
        if not allow_truth and not allow_action:
            await GameService.end_game(callback.bot, room_id)
            return

    await GameService.send_turn_prompt(callback.bot, room_id)