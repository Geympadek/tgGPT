import loader
from loader import dp, bot, database

import config

from aiogram import types, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter

from aiogram.exceptions import TelegramBadRequest

import chatgpt
import utils

from time import time

@dp.message(Command("start"))
async def on_start(msg: types.Message, state: FSMContext):
    await msg.answer(
        text="Привет!\n"
             "Этот бот предоставляет бесплатный доступ к ChatGPT.\n\n"
             "Введите текст, чтобы начать.")

    database.setdefault("prefs", {"user_id": msg.from_user.id})

async def handle_photo(msg: Message):
    user_id = msg.from_user.id

    file_id = attached_image_id(msg)

    img = await bot.get_file(file_id)
    url = f"https://api.telegram.org/file/bot{config.TG_TOKEN}/{img.file_path}"
    await chatgpt.push_image(user_id, "user", url)

@dp.message()
async def on_message(msg: Message, state: FSMContext):
    user_id = msg.from_user.id

    text = None

    if msg.photo:
        await handle_photo(msg)
        text = msg.caption
    elif msg.text:
        text = msg.text
    
    if text:
        chatgpt.push_message(user_id, "user", text)
        await gen_response(msg)


async def gen_response(last_msg: Message):
    user_id = last_msg.from_user.id

    response = await chatgpt.get_response(user_id)
    
    text = utils.tag_content(response, "message")
    reaction = utils.tag_content(response, "tg-reaction")
    chatgpt.push_message(user_id, "assistant", response)

    if reaction and reaction != '':
        try:
            await last_msg.react([types.ReactionTypeEmoji(emoji=reaction)])
        except TelegramBadRequest:
            print("Unable to send reaction")
    if text and text.strip() != "":
        await last_msg.answer(text)

def attached_image_id(msg: Message):
    if msg.photo is None:
        return None

    best_photo = max(msg.photo, key=lambda info : info.width)
    return best_photo.file_id
    
@dp.callback_query()
async def on_query(query: CallbackQuery, state: FSMContext):
    pass

async def main():
    await loader.launch()
    pass

import asyncio

if __name__ == "__main__":
    asyncio.run(main(), debug=True)