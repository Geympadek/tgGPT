from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException

import config
import platform

import asyncio

def init_webdriver():
    '''
    Creates a new driver for scraping
    '''
    service = None

    service = Service(executable_path=config.CHROMEDRIVER_PATH)

    options = Options()

    # run browser without opening a new window
    options.add_argument("--headless")
        
    # fixes a gpu error without fully disabling gpu
    options.add_argument("--disable-gpu-compositing")
    # suppresses SSL errors 
    options.add_argument('--ignore-certificate-errors')
    options.set_capability('acceptInsecureCerts', True)
    # disable console output
    options.add_argument("--log-level=OFF")

    # prevents browser from playing audio
    options.add_argument("--mute-audio")

    driver = webdriver.Chrome(options=options, service=service)

    stealth(driver,
            platform="Win32",
            vendor="Google Inc.",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine")
    
    driver.set_page_load_timeout(3)

    return driver

def enable_cdp_blocking():
    """
    Starts blocking all the resources to speed up loading
    """
    # Enable Chrome DevTools Protocol (CDP) for blocking resources
    driver.execute_cdp_cmd("Network.enable", {})
    
    # Set request interception patterns for types you want to block
    driver.execute_cdp_cmd(
        "Network.setBlockedURLs", {
            "urls": [
                "*.jpg", "*.jpeg", "*.png", "*.gif", "*.svg", "*.webp",  # Images
                "*.css",  # Stylesheets
                "*.mp4", "*.webm", "*.avi", "*.mov",  # Media
                "*.ttf", "*.woff", "*.woff2", "*.otf"  # Fonts
            ]
        }
    )

driver = init_webdriver()

def get_as_str(url: str):
    enable_cdp_blocking()
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
    print(await asyncio.gather(
        get_as_str_async("https://www.azlyrics.com/lyrics/jackstauber/mindsight.html"),
        get_as_str_async("https://www.azlyrics.com/lyrics/jackstauber/buttercup.html")
        ))

if __name__ == "__main__":
    asyncio.run(main())