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

        # Rise the exception if fail
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
        # Read a path from the attribute
        current_path = card["data-link-to-view"]

        # Skip if there is no path to card
        if not current_path:
            continue
        
        # Make URL
        url = urljoin(START_URL, current_path)

        # Add to the list
        all_links.append(url)
    
    return all_links


def get_reference_on_next_page(html:str) ->str | None:
    """
    Method finds <a class="page-link active">.
    Use its next selcetor<a class="page-link"> and
    returns its href. 
    Otherwise return None.
    """

    soup = BeautifulSoup(html, "html.parser")

    # Find the <nav> element that contains pagination
    #  links (has class "pager")
    nav = soup.select_one("nav.pager")
    if not nav:
        return None

    # Inside the nav find the active page <a> tag (class="page-link active")
    active_a = nav.find("a", class_="page-link active")
    if not active_a:
        return None

    # Find its parent container
    page_item = active_a.find_parent("span")
    if not page_item:
        return None

    # Find the next sibling <span> element (the link to the next page)
    next_item = page_item.find_next_sibling("span")
    if not next_item:
        return None

    # Inside that <span>, find the <a class="page-link"> tag
    next_a = next_item.find("a", class_="page-link")
    
    if not next_a or not next_a.has_attr("href"):
        return None

    href = next_a["href"].strip()
    # Ignore"javascript:void(0)"
    if not href or href.startswith("javascript"):
        return None

    return urljoin(START_URL, href)


# Fields parsers
def parse_title(bs: BeautifulSoup) -> str | None:
    """
        Method parses a title of the car page
        and returns it as a string. If it fails,
        then method returns None.
    """

    # Title uses h1.head selector
    title = bs.select_one("h1.head")

    return title.get_text(strip=True) if title else None


async def main():

    # Create a session and execute fetch_html
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, START_URL)
    
    # Get all available links
    links = parse_links(html)
    
    # Print it
    for url in links:
        print(url)

    # Is here a reference on the next page?
    next_page = get_reference_on_next_page(html)
    if next_page:
        print(next_page)
    else:
        print("Couldn't fimd a reference on the next page.")

    # Test fields parsers**********************************************

    # Title parser
    car_url = "https://auto.ria.com/uk/auto_mazda_cx_30_38402227.html"
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, car_url)
    
    bs = BeautifulSoup(html, "lxml")
    title = parse_title(bs)
    if title:
        print(title)
    else:
        print("Couldn't parse a title of the car page")

        

if __name__ == "__main__":
    asyncio.run(main())