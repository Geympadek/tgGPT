from bs4 import BeautifulSoup, Comment
import aiohttp
import asyncio

async def get_as_str(url: str, *args):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, *args) as response:
            return await response.text(encoding="UTF-8")

async def site_from_url(url: str):
    raw = await get_as_str(url)

    page = BeautifulSoup(raw, "html.parser")
    new_page = BeautifulSoup(features='html.parser')

    for element in page.find_all():
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']:
            new_page.append(element)
    
    for element in new_page(text=lambda text: isinstance(text, Comment)):
        element.extract()

    for element in new_page.find_all():
        if 'class' in element.attrs:
            del element.attrs['class']
    
    for el in new_page(["svg", "nav"]):
        el.decompose()

    for span in new_page(["span", "b", "i", "u", "strong"]):
        span.unwrap()

    return str(new_page)

async def main():
    print

if __name__ == "__main__":
    asyncio.run(site_from_url("https://genius.com/search?q=jack+stauber+mindsight"))