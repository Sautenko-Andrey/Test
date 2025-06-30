import os                             
import asyncio                        
from datetime import datetime         
from urllib.parse import urljoin     
import aiohttp
from bs4 import BeautifulSoup  


# Basic url
START_URL = os.getenv("START_URL")

async def fetch_html(session: aiohttp.ClientSession, url: str) -> str:
    """
        Method sends a get-request using url argument,
        then checks resonse status and if it's not 200
        it raises exception.
        If everything is ok, it returns string (html) and
        this string is ready for parsing.
    """
    async with session.get(url) as resp:

        resp.raise_for_status()

        return await resp.text()
    


def parse_links(html: str) -> list[str]:
    """
        Method parses and saves all links on cards
        and returns as list of strings.
    """
    bs = BeautifulSoup(html, "lxml")
    
    # Find all div.hide, which have data-link-to-view
    all_cards = bs.find_all("div", class_="hide",
                          attrs={"data-link-to-view": True})
    
    # Here we will store all references to cards
    all_links = []

    for card in all_cards:
        # 2) Читаем относительный путь из атрибута
        current_path = card["data-link-to-view"]

        # Skip if there is no path to card
        if not current_path:
            continue
        
        # Make URL
        url = urljoin(START_URL, current_path)

        # Add to the list
        all_links.append(url)
    
    return all_links


async def main():

    # Create a session and execute fetch_html
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, START_URL)
    
    # Get all available links
    links = parse_links(html)
    
    # Print it
    for url in links:
        print(url)

if __name__ == "__main__":
    asyncio.run(main())