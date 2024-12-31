import loader
from loader import dp, bot, database

import parse

import config

from aiogram import types, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter

from aiogram.exceptions import TelegramBadRequest

import chatgpt
import utils

from time import time
from tables import create_table

@dp.message(Command("start"), StateFilter(None))
async def on_start(msg: types.Message, state: FSMContext):
    await msg.answer(
        text="Привет!\n"
             "Этот бот предоставляет бесплатный доступ к ChatGPT.\n\n"
             "Введите текст, чтобы начать.")

    database.setdefault("prefs", {"user_id": msg.from_user.id})

@dp.message(Command("clear"), StateFilter(None))
async def on_clear(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    
    await msg.answer("История очищена.")
    
    chatgpt.clear_history(user_id)

@dp.message(Command("prompt"), StateFilter(None))
async def on_prompt_command(msg: types.Message, state: FSMContext):
    await msg.answer("Введите дополнительные инструкции к нейросети: ")
    await state.set_state("prompt")

@dp.message(StateFilter("prompt"))
async def on_prompt(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id

    database.update('prefs', {"system_prompt": msg.text}, {"user_id": user_id})
    await state.set_state(None)
    await msg.answer("Промпт успешно изменен.")
    
    chatgpt.clear_history(user_id)

@dp.message(Command("prompt_reset"))
async def on_prompt_reset(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id

    database.update('prefs', {"system_prompt": None}, {"user_id": user_id})

    await state.set_state(None)
    await msg.answer("Промпт сброшен.")
    
    chatgpt.clear_history(user_id)

async def handle_photo(msg: Message):
    user_id = msg.from_user.id

    file_id = attached_image_id(msg)

    img = await bot.get_file(file_id)
    url = f"https://api.telegram.org/file/bot{config.TG_TOKEN}/{img.file_path}"
    await chatgpt.push_image(user_id, "user", url)

@dp.message_reaction()
async def on_reaction(arg: types.MessageReactionUpdated, state: FSMContext):
    last_msg_id = await state.get_value("last_msg_id")

    if not last_msg_id or last_msg_id != arg.message_id:
        return

    for react in arg.new_reaction:
        chatgpt.push_reaction(arg.user.id, role="user", emoji=react.emoji)

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
        await gen_response(msg, state)

async def gen_response(last_msg: Message, state: FSMContext):
    user_id = last_msg.from_user.id

    await bot.send_chat_action(last_msg.from_user.id, "typing")
    response = await chatgpt.get_response(user_id)

    data = utils.parse_string(response)

    texts = data["message"]
    reaction_emojies = data["tg-reaction"]
    requests = data["website-request"]
    tables = data['table']
    chatgpt.push_message(user_id, "assistant", response)

    reactions = []
    for reaction in reaction_emojies:
        emoji = reaction if reaction in config.ALLOWED_REACTIONS else '❤'
        reactions.append(types.ReactionTypeEmoji(emoji=emoji))

    if len(reactions):
        await last_msg.react([reactions[0]])
    
    for table in tables:
        create_table(user_id, table)

    for text in texts:
        if text.strip() == '':
            continue
        msg = await last_msg.answer(text)
        await state.update_data(last_msg_id = msg.message_id)
    
    for request in requests:
        if request.strip() == "":
            continue

        website = await parse.site_from_url(request)

        if utils.count_tokens(website) > 0.6 * config.TOKEN_LIMIT:
            website = "Unfortunately, page's size exceeded the limit."

        chatgpt.push_website_response(user_id, "user", website)

    if len(requests):
        await gen_response(last_msg, state)

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
    asyncio.run(main())