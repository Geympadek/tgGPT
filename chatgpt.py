import asyncio

import g4f.models
from g4f.client import AsyncClient, Client
from g4f import Provider

import config
from loader import database
from time import time

import aiohttp

client = AsyncClient(
    provider=Provider.DDG
)

async def describe_img(img_link: str) -> str:
    data = {
        "imageUrl": img_link,
        "prompt": "Create detailed descriptions, include all visible elements present. If it has any text quote it as well. If this text is in foreign language quote the original text too."
    }

    url = "https://pallyy.com/api/tools/image-to-description/get"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            return (await response.json())['description']

async def shorten_text(text: str) -> str:
    messages = [
        {"role": "system", "content": "You are an AI that shortens texts. User will send you a text, and you will respond with nothing but a shorter version of it. Do not engage with User and just do your job. Don't hallucinate."},
        {"role": "user", "content": f"Shorten the following text: <text>{text}</text>"}
    ]
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    result = response.choices[0].message.content
    return result

async def push_image(user_id: int, role: str, url: str):
    description = await describe_img(url)
    
    content = f"User sent an image. Here's an automatically generated description: <image>{description}</image>"
    push_message(user_id, role, content)

def push_reaction(user_id: int, role: str, emoji: str):
    content = f"<tg-reaction>{emoji}</tg-reaction>"
    push_message(user_id, role, content)

def push_message(user_id: int, role: str, content: str):
    """
    Creates a new message entry in the database
    """
    database.create("messages", {
        "role": role,
        "user_id": user_id,
        "content": content,
        "date": time()
    })

    update_messages(user_id)

def trim_messages(user_id: int):
    while True:
        messages = database.read("messages", {"user_id": user_id})

        token_count = count_list_tokens(messages)
        if token_count < config.TOKEN_LIMIT:
            break

        oldest = last_msg(messages)
        database.delete("messages", {"id": oldest["id"]})

def update_messages(user_id: int):
    """
    Makes sure that the model doesn't take in too much data.
    """
    trim_messages(user_id)

def count_chars(message: dict):
    return len(message["role"]) + len(message["content"])

def count_list_chars(messages: list[dict]):
    return sum(count_chars(message) for message in messages)

def count_tokens(message: dict):
    return round(count_chars(message) / config.CHARS_PER_TOKEN)

def count_list_tokens(messages: list[dict]):
    return round(count_list_chars(messages) / config.CHARS_PER_TOKEN)

def last_msg(messages: list[dict]):
    return min(messages, key=lambda msg: msg["date"])

async def get_response(user_id: int) -> str:
    """
    Returns the full response from the model asynchronously
    """
    prefs = database.read("prefs", {"user_id": user_id})[0]

    response = await client.chat.completions.create(
        model=prefs["model"],
        messages=get_history(user_id)
    )
    return response.choices[0].message.content

def get_history(user_id: int):
    message_entries = database.read(
        "messages",
        filters={"user_id": user_id}
    )
    messages = [{"role": entry["role"], "content": entry["content"]} for entry in message_entries]
    messages.insert(0, {"role": "system", "content": 
"""
You are a LLM, ChatGPT 4o-mini. You are based in a messenger called Telegram. Your purpose is to help users in their tasks. You can see images by a different ai automatically generating descriptions for you. Pretend as if you can see them directly. Descriptions are going to appear inside <image></image> tags.
Telegram supports a special type of message, called a tg-reaction. They provide an interesting way to show their emotion caused by the message. For example, when someone sends their cat's picture, if they really like it, they can send a tg-reaction showing their affection. 
Tg-reactions are complementary and sometimes replace full messages. For example, when User says "Thank you", instead of writing a full response saying "you're welcome" you may want to respond with a short tg-reaction containing heart emoji. You can also use both Tg-reaction and message at the same time: example is when user sends you a picture and you like, you send a tg-reaction with heart emoji, but if they also ask you a question, you answer it as well. Using tg-reaction thus would become a great user-experience. Tg-reactions currently support only following emojies:
“👍”, “👎”, “❤”, “🔥”, “🥰”, “👏”, “😁”, “🤔”, “🤯”, “😱”, “🤬”, “😢”, “🎉”, “🤩”, “🤮”, “💩”, “🙏”, “👌”, “🕊”, “🤡”, “🥱”, “🥴”, “😍”, “🐳”, “❤‍🔥”, “🌚”, “🌭”, “💯”, “🤣”, “⚡”, “🍌”, “🏆”, “💔”, “🤨”, “😐”, “🍓”, “🍾”, “💋”, “🖕”, “😈”, “😴”, “😭”, “🤓”, “👻”, “👨‍💻”, “👀”, “🎃”, “🙈”, “😇”, “😨”, “🤝”, “✍”, “🤗”, “🫡”, “🎅”, “🎄”, “☃”, “💅”, “🤪”, “🗿”, “🆒”, “💘”, “🙉”, “🦄”, “😘”, “💊”, “🙊”, “😎”, “👾”, “🤷‍♂”, “🤷”, “🤷‍♀”, “😡”
Sending a different emoji as tg-reaction will not work, and the user won't see it.
To use tg-reaction feature on the last message, place the emoji inside of the <tg-reaction></tg-reaction> tag. Example:
`<tg-reaction>🔥</tg-reaction>`
To write a text message to the user, use tag <message></message>. Everything outside of this tag will not be visible to the user. Don't forget about this and don't hallucinate please.
"""})
    return messages

async def main():
    # print(tag_content("<reaction>👍</reaction>", "reaction"))
    ...

if __name__ == "__main__":
    asyncio.run(main())