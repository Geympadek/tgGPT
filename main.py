import loader
from loader import dp, bot, database

from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter

from aiogram.exceptions import TelegramBadRequest

import chatgpt

@dp.message(Command("start"))
async def on_start(msg: types.Message, state: FSMContext):
    await msg.answer(
        text="Привет!\n"
             "Этот бот предоставляет бесплатный доступ к ChatGPT.\n\n"
             "Введите текст, чтобы начать.")

    database.setdefault("prefs", {"user_id": msg.from_user.id})

@dp.message()
async def on_message(msg: Message, state: FSMContext):
    prefs = database.read("prefs", {"user_id": msg.from_user.id})[0]
    user_id = msg.from_user.id

    chatgpt.push_message(user_id, "user", msg.text)

    response = await chatgpt.get_response(user_id)
    await msg.answer(response)

    chatgpt.push_message(user_id, "assistant", response)

@dp.callback_query()
async def on_query(query: CallbackQuery, state: FSMContext):
    pass

async def main():
    await loader.launch()
    pass

import asyncio

if __name__ == "__main__":
    asyncio.run(main())