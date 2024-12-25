from bs4 import BeautifulSoup, Comment
import aiohttp
import asyncio

async def get_as_str(url: str, *args):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, *args) as response:
            return await response.text()

def remove_commments(page: BeautifulSoup):
    for element in page(text=lambda text: isinstance(text, Comment)):
        element.extract()

def remove_attrs(page: BeautifulSoup, attrs: list[str]):
    for element in page.find_all():
        for attr in attrs:
            if attr in element.attrs:
                del element.attrs[attr]

def remove_elements(page: BeautifulSoup, elements: list[str]):
    for el in page(elements):
        el.decompose()

def unwrap_elements(page: BeautifulSoup, elements: list[str]):
    for el in page(elements):
        el.unwrap()

def remove_empty_lines(src: str):
    lines = src.splitlines()
    
    lines = [line for line in lines if line.strip() != '']

    return "\n".join(lines)

async def site_from_url(url: str):
    raw = await get_as_str(url)

    page = BeautifulSoup(raw, "html.parser")

    remove_commments(page)
    remove_attrs(page, ['class', 'style'])
    remove_elements(page, ['svg', 'style', 'script', 'link', 'meta', 'title'])

    for el in page.find_all():
        if el.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'li', 'ul', 'ol', 'br']:
            el.unwrap()

    src = str(page)
    return remove_empty_lines(src)

async def main():
    print(await site_from_url("https://www.azlyrics.com/lyrics/jackstauber/mindsight.html"))

if __name__ == "__main__":
    asyncio.run(main())