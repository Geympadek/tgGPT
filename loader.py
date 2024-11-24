from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties

from config import TG_TOKEN
from database import Database

bot = Bot(
    token=TG_TOKEN,
    default=DefaultBotProperties(
        parse_mode="markdown"
    )
)
dp = Dispatcher()
database = Database("database.db")

async def launch():
    await dp.start_polling(bot)