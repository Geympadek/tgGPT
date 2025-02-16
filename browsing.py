from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import TimeoutException

import config
import platform

import asyncio

def init_webdriver():
    '''
    Creates a new driver for scraping
    '''
    service = None

    service = Service(executable_path=config.DRIVER_PATH)

    options = Options()

    # run browser without opening a new window
    options.add_argument("--headless")

    driver = webdriver.Firefox(options=options, service=service)
    
    driver.set_page_load_timeout(3)

    return driver


driver = init_webdriver()

def get_as_str(url: str):
    try:
        driver.get(url)
    except TimeoutException:
        driver.execute_script("window.stop();")
    return driver.page_source

lock = asyncio.Lock()

async def get_as_str_async(url: str):
    async with lock:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, get_as_str, url)

async def main():
    await asyncio.gather(
        get_as_str_async("https://www.azlyrics.com/lyrics/jackstauber/mindsight.html"),
        get_as_str_async("https://www.azlyrics.com/lyrics/jackstauber/buttercup.html")
        )

if __name__ == "__main__":
    asyncio.run(main())