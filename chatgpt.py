import asyncio

import g4f.models
from g4f.client import AsyncClient, Client
from g4f import Provider

import config
from loader import database
from time import time

from requests import get

import typing

client = AsyncClient(
    provider=Provider.DDG
)

imgClient = AsyncClient(
    provider=Provider.You
)

async def describe_img(img_link: str) -> str:
    img = open("cat.jpg", "b+r")

    response = await imgClient.chat.completions.create(
        model=g4f.models.default,
        messages=[{"role":"system", "content": "Give a full description of the given image."}],
        image=img
    )
    return response.choices[0].message.content

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

def update_messages(user_id: int):
    """
    Checks the message history, trims messages if there are too many tokens
    """
    while True:
        messages = database.read("messages", {"user_id": user_id})

        token_count = count_tokens(messages)
        print(token_count)
        if token_count < config.TOKEN_LIMIT:
            break

        oldest = last_msg(messages)
        database.delete("messages", {"id": oldest["id"]})

def count_tokens(messages: list[dict]):
    char_count = sum(len(message["role"]) + len(message["content"]) for message in messages)
    return round(char_count / config.CHARS_PER_TOKEN)

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
    return messages

async def main():
    print(await describe_img("https://img.freepik.com/free-photo/view-adorable-kitten-with-simple-background_23-2150758088.jpg"))

if __name__ == "__main__":
    asyncio.run(main())

