from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties

import sys

from config import TG_TOKEN
from database import FileDatabase

bot = Bot(
    token=TG_TOKEN,
    default=DefaultBotProperties(
        parse_mode="markdown"
    )
)
dp = Dispatcher()
database = FileDatabase('database.db')

async def launch():
    await dp.start_polling(bot)