import asyncio

import g4f.models
from g4f.client import AsyncClient, Client
from g4f import Provider

import config
from loader import database
from time import time
import datetime

import utils

client = AsyncClient(
    provider=Provider.PollinationsAI
)

def push_image(user_id: int, role: str, img: bytes, img_name: str):
    database.create("images", {"user_id": user_id, "image": img, "filename": img_name})

def push_reaction(user_id: int, role: str, emoji: str):
    content = f"<tg-reaction>{emoji}</tg-reaction>"
    push_message(user_id, role, content)

def push_website_response(user_id: int, role: str, response: str):
    content = f"<website-response>{response}</website-response>"
    push_message(user_id, role, content)

def push_search_response(user_id: int, role: str, response: str):
    content = f"<search-response>{response}</search-response>"
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

def clear_history(user_id: int):
    database.delete("messages", filters={"user_id": user_id})
    database.delete("images", filters={"user_id": user_id})

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

def get_system_prompt():
    prompt = f"""

You are a language model (LLM), specifically model {config.MODEL}, designed to assist users in a messaging platform called Telegram. Your main goal is to help users with their tasks effectively.
Today is \'{datetime.datetime.today().strftime("%d/%m/%Y")}\' (day, month, year).

**Tg-Reactions**: 
Telegram allows users to express emotions through tg-reactions. For instance, if a user shares a picture of their cat, another user might send a tg-reaction to show your affection. 
To send a tg-reaction, use the format: `<tg-reaction>🔥</tg-reaction>`.

- **Usage**: 
  - Tg-reactions can replace full messages. For example, if a user says "Thank you," you can respond with a heart emoji instead of a full message.
  - You can combine tg-reactions with text messages.

- **Allowed Reactions**: 
  You can use the following emojis for tg-reactions: <allowed-reactions>{config.ALLOWED_REACTIONS}</allowed-reactions>. Using any other emoji will be automatically replaced by `<tg-reaction>❤</tg-reaction>`.

**Code**
- If you want to send code use the usual markdown format (```code```).

**Table Generation**: 
To create a table, use Markdown format within `<table></table>`.

**Website Requests**: 
You can request the server to load a website for fact-checking or to obtain updated information. Use the format: `<website-request>URL</website-request>`. The server will return the content in `<website-response></website-response>` tags.
If the loaded page didn't provide the required information, you can request to load a different website, using same format.

**Website Searching**:
Before accessing a requesting a website it's recommended to first search for them. You can do this through `<search-query>Query</search-query>` tags. The server will return a list of links to websites in `<search-response></search-response>` tags.
"""
    return prompt

async def get_response(user_id: int) -> str:
    """
    Returns the full response from the model asynchronously
    """
    history = [{"role": "system", "content": get_system_prompt()}]
    history.extend(get_sample_history())
    history.extend(get_history(user_id))

    images = get_images(user_id)

    last_error = None
    for retry in range(3):
        response = ""
        try:
            response = await client.chat.completions.create(
                model=config.MODEL,
                messages=history,
                images=images
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            print(f"Unable to get response from the model. Retry {retry + 1}")
    raise last_error

def get_sample_history():
    return [{"role": "user", "content": "Привет!"},
            {"role": "assistant", "content": "Привет! Как я могу помочь тебе сегодня?"},
            {"role": "user", "content": "Можешь сгенерировать таблицу где в первой колонке будет \"ЯП\", а во второй \"Применение\"?"},
            {"role": "assistant", "content": """<tg-reaction>🤝</tg-reaction>
Конечно!
<table>
| ЯП         | Применение                     |
|------------|--------------------------------|
| Python     | Веб-разработка, анализ данных  |
| Java       | Разработка приложений, Android |
| JavaScript | Веб-разработка, интерактивные элементы |
| C++        | Системное программирование, игры |
| Ruby       | Веб-разработка, автоматизация   |
</table>"""},
            {"role": "user", "content": """Можешь найти слова песни "Smells like teen spirit" группы "Nirvana"?"""},
            {"role": "assistant", "content": "Сейчас!<search-query>Smells like teen spirit lyrics Nirvana</search-query>"},
            {"role": "user", "content": """
<search-response><ul><li>
	<title>Nirvana - Smells Like Teen Spirit Lyrics - Genius</title>
	<href>genius.com/Nirvana-smells-like-teen-spirit-lyrics</href>
</li>
<li>
	<title>Nirvana - Smells Like Teen Spirit Lyrics | AZLyrics.com</title>
	<href>www.azlyrics.com/lyrics/nirvana/smellsliketeenspirit.html</href>
</li>
<li>
	<title>Smells Like Teen Spirit - Lyrics.com</title>
	<href>www.lyrics.com/lyric/24156833/Nirvana/Smells+Like+Teen+Spirit</href>
</li>
<li>
	<title>Smells Like Teen Spirit Lyrics - Lyrics On Demand</title>
	<href>www.lyricsondemand.com/nirvana/smells_like_teen_spirit</href>
</li>
<li>
	<title>Nirvana - Smells Like Teen Spirit (2021 Remaster) Lyrics - Genius</title>
	<href>genius.com/Nirvana-smells-like-teen-spirit-2021-remaster-lyrics</href>
</li>
</ul></search-response>
"""},
            {"role": "assistant", "content": """Ищу слова, немного подождите!<website-request>https://www.azlyrics.com/lyrics/nirvana/smellsliketeenspirit.html</website-request>"""},
            {"role": "user", "content": 
"""
<website-response>
<h1>"Smells Like Teen Spirit" lyrics</h1>
<h2><a href="//www.azlyrics.com/n/nirvana.html">Nirvana Lyrics</a></h2>
                     Follow Nirvana                     on Bandsintown                  
"Smells Like Teen Spirit"<br/>
<br/>
Load up on guns, bring your friends<br/>
It's fun to lose and to pretend<br/>
She's over-bored and self-assured<br/>
Oh no, I know a dirty word<br/>
<br/>
Hello, hello, hello, how low<br/>
Hello, hello, hello, how low<br/>
Hello, hello, hello, how low<br/>
Hello, hello, hello<br/>
<br/>
With the lights out, it's less dangerous<br/>
Here we are now, entertain us<br/>
I feel stupid and contagious<br/>
Here we are now, entertain us<br/>
A mulatto, an albino<br/>
A mosquito, my libido<br/>
<br/>
Yeah, hey, yay<br/>
<br/>
I'm worse at what I do best<br/>
And for this gift, I feel blessed<br/>
Our little group has always been<br/>
And always will until the end<br/>
<br/>
Hello, hello, hello, how low<br/>
Hello, hello, hello, how low<br/>
Hello, hello, hello, how low<br/>
Hello, hello, hello<br/>
<br/>
With the lights out, it's less dangerous<br/>
Here we are now, entertain us<br/>
I feel stupid and contagious<br/>
Here we are now, entertain us<br/>
A mulatto, an albino<br/>
A mosquito, my libido<br/>
<br/>
Yeah, hey, yay<br/>
<br/>
And I forget just why I taste<br/>
Oh yeah, I guess it makes me smile<br/>
I found it hard, it's hard to find<br/>
Oh well, whatever, never mind<br/>
<br/>
Hello, hello, hello, how low<br/>
Hello, hello, hello, how low<br/>
Hello, hello, hello, how low<br/>
Hello, hello, hello<br/>
<br/>
With the lights out, it's less dangerous<br/>
Here we are now, entertain us<br/>
I feel stupid and contagious<br/>
Here we are now, entertain us<br/>
A mulatto, an albino<br/>
A mosquito, my libido<br/>
<br/>
A denial, a denial<br/>
A denial, a denial<br/>
A denial, a denial<br/>
A denial, a denial<br/>
A denial
<br/><br/>
<br/><br/>
</website-response>"""},
            {"role": "assistant", "content": """
Вот слова песни "Smells Like Teen Spirit" группы "Nirvana":

Load up on guns, bring your friends
It's fun to lose and to pretend
She's over-bored and self-assured
Oh no, I know a dirty word

Hello, hello, hello, how low
Hello, hello, hello, how low
Hello, hello, hello, how low
Hello, hello, hello

With the lights out, it's less dangerous
Here we are now, entertain us
I feel stupid and contagious
Here we are now, entertain us
A mulatto, an albino
A mosquito, my libido

Yeah, hey, yay

I'm worse at what I do best
And for this gift, I feel blessed
Our little group has always been
And always will until the end

Hello, hello, hello, how low
Hello, hello, hello, how low
Hello, hello, hello, how low
Hello, hello, hello

With the lights out, it's less dangerous
Here we are now, entertain us
I feel stupid and contagious
Here we are now, entertain us
A mulatto, an albino
A mosquito, my libido

Yeah, hey, yay

And I forget just why I taste
Oh yeah, I guess it makes me smile
I found it hard, it's hard to find
Oh well, whatever, never mind

Hello, hello, hello, how low
Hello, hello, hello, how low
Hello, hello, hello, how low
Hello, hello, hello

With the lights out, it's less dangerous
Here we are now, entertain us
I feel stupid and contagious
Here we are now, entertain us
A mulatto, an albino
A mosquito, my libido

A denial, a denial
A denial, a denial
A denial, a denial
A denial, a denial
A denial
     
Надеюсь, это поможет!
"""},
            {"role": "user", "content": "<tg-reaction>❤</tg-reaction>"},
            {"role": "user", "content": "Большое спасибо!"},
            {"role": "assistant", "content": "<tg-reaction>😇</tg-reaction>Не за что!"},
            {"role": "user", "content": "можешь написать скрипт в Python который будет принимать два числа и выводить в консоль их произведение?"},
            {"role": "assistant", "content": """<tg-reaction>👍</tg-reaction>
Конечно! Вот простой скрипт на Python, который принимает два числа и выводит их произведение:
```python
# Функция для умножения двух чисел
def multiply_numbers(num1, num2):
    return num1 * num2

# Ввод чисел от пользователя
number1 = float(input("Введите первое число: "))
number2 = float(input("Введите второе число: "))

# Вывод произведения
result = multiply_numbers(number1, number2)
print(f"Произведение {number1} и {number2} равно {result}.")
```
Скопируй и запусти этот код в своем Python окружении!
"""},
            {"role": "user", "content": "<tg-reaction>❤</tg-reaction>"}
    ]

def get_history(user_id: int):
    message_entries = database.read(
        "messages",
        filters={"user_id": user_id}
    )
    messages = [{"role": entry["role"], "content": entry["content"]} for entry in message_entries]

    return messages

def get_images(user_id: int):
    image_entries = database.read(
        "images", 
        filters={"user_id": user_id}
    )
    images = [(entry["image"], entry["filename"]) for entry in image_entries]
    return images

async def main():
    # print(tag_content("<reaction>👍</reaction>", "reaction"))
    # print(await get_response(1565642212))
    push_message(23, "user", "fu")
    ...

if __name__ == "__main__":
    asyncio.run(main())