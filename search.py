import browsing
import bs4

async def get_html(query: str):
    url = f"https://html.duckduckgo.com/html/?q={query}"
    return await browsing.get_as_str_async(url)

def html_to_links(html: str, max_results: int):
    page = bs4.BeautifulSoup(html, "html.parser")
    links_div = page.find(id='links')
    divs = links_div.find_all("div", attrs={"class": "result"}, limit=max_results)

    links = []
    for div in divs:
        a_title = div.find("a", attrs={"class": "result__a"})
        a_link = div.find("a", attrs={"class": "result__url"})

        links.append({"title": a_title.text.strip(), "href": a_link.text.strip()})
    return links

async def search(query: str):
    html = await get_html(query)
    json = html_to_links(html, 5)
    
    result = []
    for item in json:
        result.append(f"<li>\n\t<title>{item['title']}</title>\n\t<href>{item['href']}</href>\n</li>\n")

    return f'<ul>{("".join(result))}</ul>'

async def main():
    print(await search("Серега"))

import asyncio

if __name__ == "__main__":
    asyncio.run(main())