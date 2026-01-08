from aiogram import Router


user_router = Router()

async def setup_routers():
    all_routers = [
        user_router
    ]

    return all_routers