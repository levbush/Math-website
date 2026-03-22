from aiogram import Bot, Dispatcher
from handlers import router
from db import init_dbs
from config import TOKEN
import asyncio


async def main():
    init_dbs()
    if TOKEN is None:
        raise ValueError('TOKEN not found')
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
