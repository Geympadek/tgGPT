import asyncio

import g4f.models
from g4f.client import AsyncClient, Client
from aiolimiter import AsyncLimiter
from g4f import Provider

import config
from loader import database
from time import time

import utils

import aiohttp

client = AsyncClient(
    provider=Provider.Blackbox
)

rate_limit = AsyncLimiter(max_rate=1, time_period=1)  # 10 requests per second

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

def push_website_response(user_id: int, role: str, response: str):
    content = f"<website-response>{response}</website-response>"
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
        print(token_count)
        if token_count < config.TOKEN_LIMIT:
            break

        oldest = last_msg(messages)
        database.delete("messages", {"id": oldest["id"]})

def update_messages(user_id: int):
    """
    Makes sure that the model doesn't take in too much data.
    """
    trim_messages(user_id)

def count_tokens(message: dict):
    return utils.count_tokens(message["content"]) + 2

def count_list_tokens(messages: list[dict]):
    return sum(count_tokens(message) for message in messages)

def last_msg(messages: list[dict]):
    return min(messages, key=lambda msg: msg["date"])

def get_system_prompt(prefs: dict):
    prompt = f"""
You are a LLM, model {prefs["model"]}. You are based in a messenger called Telegram. Your purpose is to help users in their tasks. You can see images by a different ai automatically generating descriptions for you. Pretend as if you can see them directly. Descriptions are going to appear inside <image></image> tags.
Telegram supports a special type of message, called a tg-reaction. They provide an interesting way to show their emotion caused by the message. For example, when someone sends their cat's picture, if they really like it, they can send a tg-reaction showing their affection. 
Tg-reactions are complementary and sometimes replace full messages. For example, when User says "Thank you", instead of writing a full response saying "you're welcome" you may want to respond with a short tg-reaction containing heart emoji. You can also use both Tg-reaction and message at the same time: example is when user sends you a picture and you like it, you send a tg-reaction with heart emoji, but if they also ask you a question, you answer it as well. Using tg-reaction thus would become a great user-experience. Tg-reactions currently support only following emojies:
“👍”, “👎”, “❤”, “🔥”, “🥰”, “👏”, “😁”, “🤔”, “🤯”, “😱”, “🤬”, “😢”, “🎉”, “🤩”, “🤮”, “💩”, “🙏”, “👌”, “🕊”, “🤡”, “🥱”, “🥴”, “😍”, “🐳”, “❤‍🔥”, “🌚”, “🌭”, “💯”, “🤣”, “⚡”, “🍌”, “🏆”, “💔”, “🤨”, “😐”, “🍓”, “🍾”, “💋”, “🖕”, “😈”, “😴”, “😭”, “🤓”, “👻”, “👨‍💻”, “👀”, “🎃”, “🙈”, “😇”, “😨”, “🤝”, “✍”, “🤗”, “🫡”, “🎅”, “🎄”, “☃”, “💅”, “🤪”, “🗿”, “🆒”, “💘”, “🙉”, “🦄”, “😘”, “💊”, “🙊”, “😎”, “👾”, “🤷‍♂”, “🤷”, “🤷‍♀”, “😡”
Sending a different emoji as tg-reaction will not work, and the user won't see it.
To use tg-reaction feature on the last message, place the emoji inside of the <tg-reaction></tg-reaction> tag. Example:
`<tg-reaction>🔥</tg-reaction>`
To write a text message to the user, use tag <message></message>. Everything outside of this tag will not be visible to the user.
If you choose not to respond to the user, you can leave <message></message> tag empty. This can be useful for example, when user sends incomplete info, and you are 100 percent sure, that they are going to send more complete info soon.

Another thing you can do is request the server to load a website. This is especially useful when the job requeres you to fact-check something, or to get info that was released after you training.
Use tags <website-request></website-request> and put a URL in between this tags. The server is going to respond to you by loading this website's source code and returing it partialy. It's going to remove most of the tags except headers, paragraphs and so on.
You will receive the website's source code in tags <website-response></website-response>.

It is recommended to create a plan of your actions. List all the actions required for the task in a list. You can use html to make it easier to read. You can do it inside <reasoning></reasoning> tags.
"""
    if prefs.get("system_prompt") is not None:
        prompt += f"""
The user also stated their own communication preferences: 
<user_prompt>
{prefs["system_prompt"]}
</user_prompt>
"""
    return prompt

async def get_response(user_id: int) -> str:
    """
    Returns the full response from the model asynchronously
    """
    prefs = database.read("prefs", {"user_id": user_id})[0]

    history = [{"role": "system", "content": get_system_prompt(prefs)}]
    history.extend(get_history(user_id))

    for retry in range(10):
        async with rate_limit:
            response = await client.chat.completions.create(
                model=prefs["model"],
                messages=history
            )
            content: str = response.choices[0].message.content
            if content.strip() != "":
                break
            print(f"Unable to get response from the model. Retry {retry + 1}")
        
    return content

def get_history(user_id: int):
    message_entries = database.read(
        "messages",
        filters={"user_id": user_id}
    )
    messages = [{"role": entry["role"], "content": entry["content"]} for entry in message_entries]

    return messages

async def main():
    # print(tag_content("<reaction>👍</reaction>", "reaction"))
    print(await get_response(1565642212))
    ...

if __name__ == "__main__":
    asyncio.run(main())