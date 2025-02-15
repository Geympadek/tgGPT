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
import search

import tables as tb

@dp.message(Command("start"), StateFilter(None))
async def on_start(msg: types.Message, state: FSMContext):
    await msg.answer(
        text="Привет!\n"
             "Этот бот предоставляет бесплатный доступ к ChatGPT и другим языковым моделям.\n\n"
             "Введите текст, чтобы начать.")

    database.setdefault("prefs", {"user_id": msg.from_user.id})

@dp.message(Command("clear"), StateFilter(None))
async def on_clear(msg: types.Message, state: FSMContext):
    print(f"/clear on user {msg.from_user.first_name}")

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
    print(f"Photo received from {msg.from_user.first_name}")
    user_id = msg.from_user.id

    file_id = attached_image_id(msg)

    img = await bot.get_file(file_id)
    url = f"https://api.telegram.org/file/bot{config.TG_TOKEN}/{img.file_path}"
    await chatgpt.push_image(user_id, "user", url)

@dp.message_reaction()
async def on_reaction(arg: types.MessageReactionUpdated, state: FSMContext):
    print(f"Reaction received from {arg.from_user.first_name}")
    last_msg_id = await state.get_value("last_msg_id")

    if not last_msg_id or last_msg_id != arg.message_id:
        return

    for react in arg.new_reaction:
        chatgpt.push_reaction(arg.user.id, role="user", emoji=react.emoji)

@dp.message()
async def on_message(msg: Message, state: FSMContext):
    print(f"Message received from {msg.from_user.first_name}")
    user_id = msg.from_user.id

    text = None

    if msg.photo:
        await handle_photo(msg)
        text = msg.caption
    elif msg.text:
        text = msg.text
    
    if text:
        chatgpt.push_message(user_id, "user", f"{text}")
        await gen_response(msg, state)

async def gen_response(last_msg: Message, state: FSMContext):
    print(f"Generating a response.")
    user_id = last_msg.from_user.id

    await bot.send_chat_action(last_msg.from_user.id, "typing")
    response = await chatgpt.get_response(user_id)

    data, text = utils.separate_string(response)

    reaction_emojies = data["tg-reaction"]
    tables = data['table']
    requests = data["website-request"]
    queries = data["search-query"]

    chatgpt.push_message(user_id, "assistant", response)

    reactions = []
    for reaction in reaction_emojies:
        emoji = reaction if reaction in config.ALLOWED_REACTIONS else '❤'
        reactions.append(types.ReactionTypeEmoji(emoji=emoji))

    if len(reactions):
        print("Using tg-reactions")
        await last_msg.react([reactions[0]])
    
    TEMP_FILE = 'table.png'

    for table in tables:
        print("Generating a table")
        table = table.strip()
        tb.render_table(table, TEMP_FILE)
        await last_msg.answer_photo(types.FSInputFile(TEMP_FILE))
    
    if text != '':
        print("Responding with a text")
        msg = await last_msg.answer(
            text
        )
        await state.update_data(last_msg_id = msg.message_id)
    
    for request in requests:
        print("Performing a web request")
        if request.strip() == "":
            continue

        website = await parse.site_from_url(request)

        if utils.count_tokens(website) > 0.6 * config.TOKEN_LIMIT:
            website = "Unfortunately, page's size exceeds the limit."

        chatgpt.push_website_response(user_id, "user", website)

    for query in queries:
        print("Googling.")
        if query.strip() == "":
            continue

        search_response = await search.search(query)
        chatgpt.push_search_response(user_id, "user", search_response)

    if len(requests) or len(queries):
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