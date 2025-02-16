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
    chatgpt.push_message(user_id, "assistant", response)

    actions = utils.separate_string(response)

    for action in actions:
        await perform_action(action, last_msg, state)

async def perform_action(action: str | dict[str, str], last_msg: Message, state: FSMContext):
    user_id = last_msg.from_user.id
    if type(action) is str:
        print("Responding with a text")
        msg = await last_msg.answer(action)
        await state.update_data(last_msg_id = msg.message_id)
        return

    act_content = action['content'].strip()
    if act_content == '':
        return

    tag = action['tag']
    if tag == 'tg-reaction':
        print("Using tg-reactions")
        emoji = act_content if act_content in config.ALLOWED_REACTIONS else '❤'
        react = types.ReactionTypeEmoji(emoji=emoji)
        await last_msg.react([react])
        return

    TEMP_FILE = 'table.png'

    if tag == 'table':
        print("Generating a table")
        tb.render_table(act_content, TEMP_FILE)
        await last_msg.answer_photo(types.FSInputFile(TEMP_FILE))
        return
    
    if tag == 'website-request':
        print("Performing a web request")

        await last_msg.answer(f"_Загрузка сайта_ [по ссылке]({act_content})...")
        website = await parse.site_from_url(act_content)

        if utils.count_tokens(website) > 0.6 * config.TOKEN_LIMIT:
            website = "Unfortunately, page's size exceeds the limit."

        chatgpt.push_website_response(user_id, "user", website)
        await gen_response(last_msg, state)

    if tag == 'search-query':
        print("Googling.")

        await last_msg.answer(f"_Поиск по запросу:_ **\"{act_content}\"**...")

        search_response = await search.search(act_content)
        chatgpt.push_search_response(user_id, "user", search_response)
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